#!/usr/bin/env python3
"""High-resolution pipeline for the coloring pages.

The raws are only ~1408x768. Upscaling to A4 300DPI (2480x3508) means inventing
pixels. For pure line art the right answer is to TRACE to real vector paths and
rasterise those at any size - no invented pixels, exact edges.

potrace/potracer emits a phantom full-bitmap curve whose fill semantics are
awkward, so rather than trusting any single interpretation we render the
candidates, SCORE each against the original artwork, and keep the winner.
If no vector interpretation is trustworthy we fall back to the source pixels,
so the delivered page is always correct.

Outputs per page:
  vector-svg/<name>.svg   true vector, infinitely scalable (only when verified)
  <name>.png              A4 @ 300DPI, from vector when verified, else source
"""
import os, glob
import numpy as np
import potrace
from PIL import Image, ImageDraw, ImageOps

ROOT = "/home/user/Arena.ai/etsy-shop"
A4 = (2480, 3508)
DPI = (300, 300)
MARGIN = 150
HI_SCALE = 3          # rasterise vectors at 3x source width
MIN_SCORE = 0.965     # similarity to the original art required to trust a vector

# ---------------------------------------------------------------- geometry
def _flat_between(p0, c1, c2, p1, steps):
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt**3*p0[0] + 3*mt*mt*t*c1[0] + 3*mt*t*t*c2[0] + t**3*p1[0]
        y = mt**3*p0[1] + 3*mt*mt*t*c1[1] + 3*mt*t*t*c2[1] + t**3*p1[1]
        out.append((x, y))
    return out

def curve_to_polygon(curve, scale):
    P = lambda pt: (pt.x, pt.y)
    pts = []
    cur = P(curve.start_point)
    for seg in curve.segments:
        end = P(seg.end_point)
        if getattr(seg, "is_corner", False):
            pts.append((cur[0]*scale, cur[1]*scale))
        else:
            c1 = P(seg.c1); c2 = P(seg.c2)
            span = (abs(end[0]-cur[0]) + abs(end[1]-cur[1])) * scale
            steps = max(6, min(48, int(span / 1.5) + 4))
            pts.extend(_flat_between((cur[0]*scale, cur[1]*scale),
                                     (c1[0]*scale, c1[1]*scale),
                                     (c2[0]*scale, c2[1]*scale),
                                     (end[0]*scale, end[1]*scale), steps))
        cur = end
    return pts

def flatten_all(path):
    curves = []
    def rec(c):
        curves.append(c)
        for ch in (getattr(c, "children", None) or []):
            rec(ch)
    for c in path.curves:
        rec(c)
    return curves

def curve_bbox(curve):
    pts = list(getattr(curve, "decomposition_points", []) or []) or [curve.start_point]
    xs = [q.x for q in pts]; ys = [q.y for q in pts]
    if not xs:
        return 0, 0, 0, 0
    return min(xs), min(ys), max(xs), max(ys)

# ---------------------------------------------------------------- rasterise
def render_curves(curves, out_size, src_size, xor=True):
    """Even-odd (XOR) accumulation is how SVG defines fill, so raster == vector."""
    ow, oh = out_size
    sw, sh = src_size
    scale = max(ow / sw, oh / sh)
    acc = np.zeros((oh, ow), dtype=bool)
    for curve in curves:
        poly = curve_to_polygon(curve, scale)
        if len(poly) < 3:
            continue
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        x0 = max(0, int(min(xs)) - 1); x1 = min(ow, int(max(xs)) + 2)
        y0 = max(0, int(min(ys)) - 1); y1 = min(oh, int(max(ys)) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        tmp = Image.new("1", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(tmp).polygon([(p[0]-x0, p[1]-y0) for p in poly], fill=1)
        tile = np.array(tmp, dtype=bool)
        acc[y0:y1, x0:x1] = (acc[y0:y1, x0:x1] ^ tile) if xor else (acc[y0:y1, x0:x1] | tile)
    return acc

def score(mask, target):
    """Similarity: 1.0 = identical."""
    diff = np.logical_xor(mask, target).sum()
    return 1.0 - diff / float(target.size)

# ---------------------------------------------------------------- per page
def trace_page(img_path):
    g = ImageOps.autocontrast(Image.open(img_path).convert("L"), cutoff=1)
    target = np.array(g) < 150                    # True = ink
    sh, sw = target.shape
    path = potrace.Bitmap(target).trace(turdsize=2, alphamax=1.0, opttolerance=0.2)

    all_curves = flatten_all(path)
    cands = {"all": all_curves}

    # the phantom curve = largest bbox covering (nearly) the whole bitmap
    if path.curves:
        biggest = max(path.curves, key=lambda c: (curve_bbox(c)[2]-curve_bbox(c)[0]) *
                                             (curve_bbox(c)[3]-curve_bbox(c)[1]))
        bx0, by0, bx1, by1 = curve_bbox(biggest)
        if (bx1-bx0) >= sw*0.99 and (by1-by0) >= sh*0.99:
            dropped = set(id(c) for c in flatten_all(type("P", (), {"curves": [biggest]})()))
            cands["minus_phantom"] = [c for c in all_curves if id(c) not in dropped]

    results = {}
    for tag, curves in cands.items():
        m = render_curves(curves, (sw, sh), (sw, sh))
        results[tag] = (score(m, target), curves)

    best_tag, (best_score, best_curves) = max(results.items(), key=lambda kv: kv[1][0])
    detail = ", ".join(f"{t}={s:.3f}" for t, (s, _) in results.items())
    return target, best_curves, best_score, detail, (sw, sh)

def write_svg(curves, src_size, out_path, precision=2):
    sw, sh = src_size
    fmt = lambda v: f"{v:.{precision}f}".rstrip("0").rstrip(".")
    def emit(c):
        d = [f"M{fmt(c.start_point.x)} {fmt(c.start_point.y)}"]
        for seg in c.segments:
            if getattr(seg, "is_corner", False):
                d.append(f"L{fmt(seg.end_point.x)} {fmt(seg.end_point.y)}")
            else:
                d.append(f"C{fmt(seg.c1.x)} {fmt(seg.c1.y)} {fmt(seg.c2.x)} {fmt(seg.c2.y)} "
                         f"{fmt(seg.end_point.x)} {fmt(seg.end_point.y)}")
        d.append("Z")
        return "".join(d)
    body = "".join(emit(c) for c in curves)
    open(out_path, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {sw} {sh}" '
        f'width="{sw}" height="{sh}"><path fill="#000000" fill-rule="evenodd" d="{body}"/></svg>')

def content_bbox(im, tol=250, pad=10):
    g = im.convert("L").point(lambda v: 255 if v < tol else 0)
    bb = g.getbbox()
    if not bb:
        return (0, 0, im.width, im.height)
    l, t, r, b = bb
    return (max(0, l-pad), max(0, t-pad), min(im.width, r+pad), min(im.height, b+pad))

def place_a4(art_l, out_path):
    art = art_l.convert("RGB").crop(content_bbox(art_l))
    avail = (A4[0] - MARGIN*2, A4[1] - MARGIN*2)
    r = min(avail[0]/art.width, avail[1]/art.height)
    art = art.resize((max(1, int(art.width*r)), max(1, int(art.height*r))), Image.LANCZOS)
    page = Image.new("RGB", A4, (255, 255, 255))
    page.paste(art, ((A4[0]-art.width)//2, (A4[1]-art.height)//2))
    page.save(out_path, dpi=DPI, optimize=True)
    return page

if __name__ == "__main__":
    SRC = f"{ROOT}/coloring/raw"
    OUT = f"{ROOT}/set-01-coloring-pages"
    VEC = f"{OUT}/vector-svg"
    os.makedirs(VEC, exist_ok=True)

    pages, fallbacks = [], []
    for f in sorted(glob.glob(f"{SRC}/c*.png")):
        name = os.path.splitext(os.path.basename(f))[0]
        target, curves, sc, detail, (sw, sh) = trace_page(f)

        if sc >= MIN_SCORE:
            hi = render_curves(curves, (sw*HI_SCALE, sh*HI_SCALE), (sw, sh))
            art = Image.fromarray(np.where(hi, 0, 255).astype(np.uint8), "L")
            art = art.resize((sw*HI_SCALE, sh*HI_SCALE), Image.LANCZOS)
            write_svg(curves, (sw, sh), f"{VEC}/{name}.svg")
            mode = "VECTOR"
        else:
            art = ImageOps.autocontrast(Image.open(f).convert("L"), cutoff=1)
            art = art.resize((sw*HI_SCALE, sh*HI_SCALE), Image.LANCZOS)
            mode = "FALLBACK-source"
            fallbacks.append(name)

        pages.append(place_a4(art, f"{OUT}/{name}.png"))
        print(f"{name:16} {mode:16} score={sc:.3f}  [{detail}]")

    pdf = f"{OUT}/TwinkleTotsClub_Coloring_Pages_A4.pdf"
    pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=300.0)
    print(f"\npdf -> {os.path.basename(pdf)} ({len(pages)} pages)")
    print("svg files:", len(glob.glob(f'{VEC}/*.svg')))
    if fallbacks:
        print("fallback pages (no svg):", ", ".join(fallbacks))
