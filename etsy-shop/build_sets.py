#!/usr/bin/env python3
"""Process raw generated art into print-ready product files.
Set-01: coloring pages -> clean B/W, A4 300DPI PNG + multi-page PDF
Set-02: character clip art -> transparent-background 2000px PNG
"""
import os, glob
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np

ROOT = "/home/user/Arena.ai/etsy-shop"
A4 = (2480, 3508)          # A4 @ 300 DPI
DPI = (300, 300)
MARGIN = 150

# ---------------------------------------------------------------- helpers
def crisp_lineart(img, lo=110, hi=190):
    """Force near-white background to pure white while keeping smooth AA lines."""
    g = img.convert("L")
    g = ImageOps_autocontrast(g)
    lut = []
    for v in range(256):
        if v <= lo:      lut.append(0)
        elif v >= hi:    lut.append(255)
        else:            lut.append(int(round((v - lo) * 255.0 / (hi - lo))))
    g = g.point(lut)
    return g.convert("RGB")

def ImageOps_autocontrast(g, cutoff=1):
    from PIL import ImageOps
    return ImageOps.autocontrast(g, cutoff=cutoff)

def content_bbox(img, tol=245, pad=0):
    g = img.convert("L").point(lambda v: 255 if v < tol else 0)
    bb = g.getbbox()
    if not bb:
        return (0, 0, img.width, img.height)
    l, t, r, b = bb
    return (max(0, l - pad), max(0, t - pad),
            min(img.width, r + pad), min(img.height, b + pad))

def place_on_a4(img, out_path, margin=MARGIN):
    """Trim whitespace and centre the art on a clean A4 white page."""
    img = img.convert("RGB")
    img = img.crop(content_bbox(img, tol=248, pad=10))
    avail = (A4[0] - margin * 2, A4[1] - margin * 2)
    r = min(avail[0] / img.width, avail[1] / img.height)
    art = img.resize((max(1, int(img.width * r)), max(1, int(img.height * r))), Image.LANCZOS)
    page = Image.new("RGB", A4, (255, 255, 255))
    page.paste(art, ((A4[0] - art.width) // 2, (A4[1] - art.height) // 2))
    page.save(out_path, dpi=DPI, optimize=True)
    return page

# ------------------------------------------------------- background removal
def strip_background(src_path, out_path, target=2000, tol=42):
    """Flood-fill the white background from the borders -> transparent PNG.
    Keeps white areas *inside* the character opaque (they stay white)."""
    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    ff = img.copy()
    seeds = [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3),
             (w // 2, 2), (w // 2, h - 3), (2, h // 2), (w - 3, h // 2)]
    KEY = (255, 0, 255)
    for s in seeds:
        try:
            ImageDraw.floodfill(ff, s, KEY, thresh=tol)
        except Exception:
            pass
    a = np.array(ff).astype(np.int16)
    key = np.array(KEY, dtype=np.int16)
    dist = np.abs(a - key).sum(axis=2)
    alpha = np.where(dist < 60, 0, 255).astype(np.uint8)

    # smooth the alpha edge so cut-outs aren't jagged
    am = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.6))
    # erode 1px so a faint white halo does not survive
    am = ImageChops.subtract(am, am.point(lambda v: 40 if v > 200 else 0))
    am = am.filter(ImageFilter.GaussianBlur(0.5))

    rgba = img.convert("RGBA")
    rgba.putalpha(am)
    # trim to the character, then pad to a square canvas
    bb = rgba.split()[3].getbbox()
    if bb:
        rgba = rgba.crop(bb)
    side = int(max(rgba.width, rgba.height) * 1.10)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.alpha_composite(rgba, ((side - rgba.width) // 2, (side - rgba.height) // 2))
    canvas = canvas.resize((target, target), Image.LANCZOS)
    canvas.save(out_path, optimize=True)
    return canvas

# ------------------------------------------------------------------ run
if __name__ == "__main__":
    S1 = f"{ROOT}/set-01-coloring-pages"
    S2 = f"{ROOT}/set-02-character-clipart"
    os.makedirs(S1, exist_ok=True)
    os.makedirs(S2, exist_ok=True)

    # NOTE: coloring pages are owned by build_hires.py (vector pipeline).
    # This script only processes Set-02 clip art so the two never fight over the
    # same output files. Set PROCESS_COLORING=1 to force the old pixel path.
    if os.environ.get("PROCESS_COLORING") == "1":
        pages = []
        for f in sorted(glob.glob(f"{ROOT}/coloring/raw/c*.png")):
            name = os.path.splitext(os.path.basename(f))[0]
            pages.append(place_on_a4(crisp_lineart(Image.open(f)), f"{S1}/{name}.png"))
            print("coloring ->", name)
        pdf = f"{S1}/TwinkleTotsClub_Coloring_Pages_A4.pdf"
        pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=300.0)
        print("pdf ->", os.path.basename(pdf))

    for f in sorted(glob.glob(f"{ROOT}/clipart/raw/k*.png")):
        name = os.path.splitext(os.path.basename(f))[0]
        out = f"{S2}/{name}.png"
        strip_background(f, out)
        print("clipart  ->", os.path.basename(out))
