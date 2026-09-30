#!/usr/bin/env python3
"""Build Canva-style Etsy listing images for TwinkleTotsClub.
All typography/shapes drawn with Pillow (crisp); AI images used as photo/art bases.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = "/home/user/Arena.ai/etsy-shop"
FONTS = f"{ROOT}/fonts"
ASSETS = f"{ROOT}/assets"
OUT = f"{ROOT}/listings"
WIP = f"{ROOT}/wip"
os.makedirs(OUT, exist_ok=True)
os.makedirs(WIP, exist_ok=True)

S = 2000  # canvas size

# ---------- palette ----------
INK      = (58, 58, 58)
MAGENTA  = (214, 51, 108)
PINK     = (240, 98, 146)
CORAL    = (242, 120, 92)
YELLOW   = (255, 201, 60)
TEAL     = (63, 184, 175)
GREEN    = (126, 217, 87)
BLUE     = (74, 144, 217)
PURPLE   = (155, 126, 222)
CREAM    = (255, 250, 242)
WHITE    = (255, 255, 255)

def F(name, size):
    return ImageFont.truetype(f"{FONTS}/{name}.ttf", size)

H1   = lambda s: F("Fredoka-700", s)
H2   = lambda s: F("Fredoka-600", s)
BODY = lambda s: F("Nunito-700", s)
BODY8= lambda s: F("Nunito-800", s)

# ---------- helpers ----------
def cover(img, size):
    """Scale + centre-crop to exactly size."""
    tw, th = size
    r = max(tw / img.width, th / img.height)
    im = img.resize((max(1, int(img.width * r + .5)), max(1, int(img.height * r + .5))), Image.LANCZOS)
    l = (im.width - tw) // 2
    t = (im.height - th) // 2
    return im.crop((l, t, l + tw, t + th))

def fit_contain(img, size, radius=0):
    tw, th = size
    r = min(tw / img.width, th / img.height)
    im = img.convert("RGBA").resize((max(1, int(img.width * r)), max(1, int(img.height * r))), Image.LANCZOS)
    if radius:
        im = round_corners(im, radius)
    return im

def round_corners(img, radius):
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius, fill=255)
    img.putalpha(mask)
    return img

def autocrop_white(img, tol=245, pad=18):
    """Trim near-white margins so worksheet art fills its sheet."""
    g = img.convert("L")
    mask = g.point(lambda v: 255 if v < tol else 0)
    bbox = mask.getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(img.width, r + pad), min(img.height, b + pad)
    return img.crop((l, t, r, b))

def make_sheet(art_path, box_w, box_h, radius=18, pad_frac=0.06):
    """White paper sheet with worksheet art (auto-cropped) centred on it."""
    art = autocrop_white(Image.open(art_path).convert("RGB"))
    inner = fit_contain(art, (int(box_w * (1 - pad_frac * 2)), int(box_h * (1 - pad_frac * 2))))
    sheet = Image.new("RGBA", (box_w, box_h), WHITE)
    sd = ImageDraw.Draw(sheet)
    sd.rounded_rectangle([0, 0, box_w - 1, box_h - 1], radius, fill=WHITE, outline=(228, 222, 214), width=3)
    sheet.alpha_composite(inner, ((box_w - inner.width) // 2, (box_h - inner.height) // 2))
    return sheet

def shadowed(base, im, pos, blur=26, opacity=95, dy=14, tint=(70, 55, 45)):
    """Paste RGBA `im` onto `base` (RGBA) at pos with a soft drop shadow."""
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    alpha = im.split()[3].point(lambda v: v * opacity // 255)
    layer = Image.new("RGBA", im.size, tint + (255,))
    layer.putalpha(alpha)
    sh.paste(layer, (pos[0], pos[1] + dy), layer)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh)
    base.alpha_composite(im, pos)
    return base

def paste_rot(base, im, center, angle, **kw):
    rot = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    pos = (int(center[0] - rot.width / 2), int(center[1] - rot.height / 2))
    return shadowed(base, rot, pos, **kw)

def pill(d, box, text, font, fg, bg, pad=(46, 24), outline=None, ow=0, radius=None):
    x, y = box
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + pad[0] * 2, th + pad[1] * 2
    r = h // 2 if radius is None else radius
    d.rounded_rectangle([x, y, x + w, y + h], r, fill=bg, outline=outline, width=ow)
    d.text((x + w / 2, y + h / 2 - (bb[1] + bb[3]) / 2 + th / 2), text, font=font, fill=fg, anchor="mm")
    return w, h

def text_w(d, text, font):
    bb = d.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]

def fit_font(make, text, max_w, start=200, d=None):
    size = start
    while size > 12:
        f = make(size)
        bb = (d or ImageDraw.Draw(Image.new("RGB", (10, 10)))).textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= max_w:
            return f
        size -= 4
    return make(12)

def title_stack(base, draw, lines, center_x, top_y, size, gap=14, fills=None, stroke=WHITE,
                sw=16, shadow=True, anchor_center=True, max_frac=0.86):
    """Big playful headline with white outline + drop shadow.
    Uses real font metrics for line advance so nothing overlaps."""
    y = top_y
    for i, ln in enumerate(lines):
        f = fit_font(H1, ln, int(base.width * max_frac) - sw * 2, start=size)
        asc, desc = f.getmetrics()
        x = center_x if anchor_center else 0
        if shadow:
            draw.text((x + 6, y + 8), ln, font=f, fill=(0, 0, 0, 40), anchor="ma" if anchor_center else "la")
        draw.text((x, y), ln, font=f, fill=(fills or [MAGENTA] * len(lines))[i],
                  anchor="ma" if anchor_center else "la", stroke_width=sw, stroke_fill=stroke)
        y += asc + desc + gap
    return y

# ---------- vector icons (drawn, no font deps) ----------
def icon(d, kind, cx, cy, r, color, ink=INK):
    if kind == "star":
        import math
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        d.polygon(pts, fill=color, outline=ink, width=max(3, int(r * 0.09)))
    elif kind == "heart":
        d.ellipse([cx - r, cy - r * .95, cx, cy + r * .05], fill=color, outline=ink, width=max(3, int(r * .1)))
        d.ellipse([cx, cy - r * .95, cx + r, cy + r * .05], fill=color, outline=ink, width=max(3, int(r * .1)))
        d.polygon([(cx - r * .98, cy - r * .18), (cx + r * .98, cy - r * .18), (cx, cy + r)], fill=color,
                  outline=ink, width=max(3, int(r * .1)))
    elif kind == "smiley":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=ink, width=max(3, int(r * .1)))
        er = r * .13
        for ex in (cx - r * .38, cx + r * .38):
            d.ellipse([ex - er, cy - r * .32 - er, ex + er, cy - r * .32 + er], fill=ink)
        d.arc([cx - r * .55, cy - r * .35, cx + r * .55, cy + r * .55], 20, 160, fill=ink, width=max(4, int(r * .11)))
    elif kind == "pencil":
        w = r * .62
        d.polygon([(cx - w, cy + r * .72), (cx + w, cy + r * .72), (cx + w, cy - r * .34), (cx - w, cy - r * .34)],
                  fill=color, outline=ink, width=max(3, int(r * .09)))
        d.polygon([(cx - w, cy - r * .34), (cx + w, cy - r * .34), (cx + w * .45, cy - r * .72), (cx - w * .45, cy - r * .72)],
                  fill=YELLOW, outline=ink, width=max(3, int(r * .09)))
        d.polygon([(cx - w * .45, cy - r * .72), (cx + w * .45, cy - r * .72), (cx, cy - r)],
                  fill=(240, 200, 170), outline=ink, width=max(3, int(r * .09)))
    elif kind == "printer":
        d.rounded_rectangle([cx - r * .92, cy - r * .62, cx + r * .92, cy + r * .42], r * .2,
                            fill=color, outline=ink, width=max(3, int(r * .1)))
        d.rectangle([cx - r * .58, cy - r, cx + r * .58, cy - r * .5], fill=WHITE, outline=ink, width=max(3, int(r * .1)))
        d.rectangle([cx - r * .58, cy + r * .18, cx + r * .58, cy + r], fill=WHITE, outline=ink, width=max(3, int(r * .1)))
        for i in range(3):
            yy = cy + r * (.34 + i * .18)
            d.line([cx - r * .38, yy, cx + r * .38, yy], fill=ink, width=max(2, int(r * .06)))
    elif kind == "book":
        d.rounded_rectangle([cx - r, cy - r * .8, cx + r, cy + r * .8], r * .14, fill=color, outline=ink, width=max(3, int(r * .1)))
        d.line([cx, cy - r * .78, cx, cy + r * .78], fill=ink, width=max(3, int(r * .08)))
    elif kind == "download":
        d.line([cx, cy - r * .82, cx, cy + r * .18], fill=color, width=max(8, int(r * .26)))
        d.polygon([(cx - r * .42, cy - r * .1), (cx + r * .42, cy - r * .1), (cx, cy + r * .52)], fill=color)
        d.line([cx - r * .72, cy + r * .82, cx + r * .72, cy + r * .82], fill=color, width=max(8, int(r * .26)))
    elif kind == "clock":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=ink, width=max(3, int(r * .1)))
        d.line([cx, cy, cx, cy - r * .58], fill=ink, width=max(4, int(r * .11)))
        d.line([cx, cy, cx + r * .45, cy], fill=ink, width=max(4, int(r * .11)))
    elif kind == "abc":
        d.text((cx, cy), "ABC", font=F("Fredoka-700", int(r * 1.05)), fill=color, anchor="mm",
               stroke_width=max(2, int(r * .07)), stroke_fill=ink)
    elif kind == "check":
        d.line([cx - r * .72, cy, cx - r * .12, cy + r * .58], fill=color, width=max(8, int(r * .3)))
        d.line([cx - r * .12, cy + r * .58, cx + r * .78, cy - r * .58], fill=color, width=max(8, int(r * .3)))


def pill_fit(d, y, text, make_font, fg, bg, max_w=None, start=58, pad=(54, 26),
             outline=None, ow=0, center=True, x=None):
    """Auto-shrink text so the pill fits inside max_w, then centre (or place at x)."""
    max_w = max_w or int(S * 0.88)
    size = start
    while size > 20:
        f = make_font(size)
        w, _ = text_w(d, text, f)
        if w + pad[0] * 2 <= max_w:
            break
        size -= 2
    f = make_font(size)
    w, _ = text_w(d, text, f)
    total = w + pad[0] * 2
    left = (S - total) // 2 if center else x
    return pill(d, (left, y), text, f, fg, bg, pad=pad, outline=outline, ow=ow)

def circle_badge(base, cx, cy, r, kind, color, label=None, label_font=None):
    d = ImageDraw.Draw(base)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=color, width=int(r * .09))
    icon(d, kind, cx, cy - (r * .26 if label else 0), r * .5, color)
    if label:
        d.text((cx, cy + r * .38), label, font=label_font or BODY8(int(r * .3)), fill=INK, anchor="mm")

# =====================================================================
# 1. HERO
# =====================================================================
def build_hero():
    bg = cover(Image.open(f"{ASSETS}/base_kid_doodle_bg.png").convert("RGB"), (S, S)).convert("RGBA")
    # mute the doodles so type pops
    bg.alpha_composite(Image.new("RGBA", (S, S), (255, 255, 255, 150)))
    d = ImageDraw.Draw(bg)

    # brand bar (top-left)
    w1, _ = pill(d, (110, 58), "TWINKLETOTSCLUB", H2(46), WHITE, MAGENTA, pad=(44, 20))
    pill(d, (110 + w1 + 24, 58), "PRESCHOOL EDITION", H2(46), INK, YELLOW, pad=(44, 20))

    # headline block — kept clear of the top-right badge
    y = title_stack(bg, d, ["FUN KIDS"], S // 2, 215, 235, fills=[MAGENTA], max_frac=0.80)
    y = title_stack(bg, d, ["LEARNING PRINTABLES"], S // 2, y + 6, 120, fills=[INK], sw=16, max_frac=0.80)
    d = ImageDraw.Draw(bg)

    # feature pills row, well below the headline
    labels = [("ALPHABET", TEAL), ("NUMBERS", CORAL), ("TRACING", PURPLE), ("COLORING", GREEN)]
    gapx = 22
    widths = []
    for t, c in labels:
        f = BODY8(54)
        w, _ = text_w(d, t, f)
        widths.append(w + 96 + gapx)
    x = (S - (sum(widths) - gapx)) // 2
    pill_y = y + 26
    for (t, c), wpad in zip(labels, widths):
        w, h = pill(d, (x, pill_y), t, BODY8(54), WHITE, c, pad=(48, 22))
        x += wpad

    # worksheet cards fanned across the lower half
    cards = [("ws_alphabet", -11, (int(S * .225), int(S * .685)), int(S * .315)),
             ("ws_coloring", 10, (int(S * .785), int(S * .695)), int(S * .315)),
             ("ws_numbers", 2.5, (int(S * .505), int(S * .715)), int(S * .395))]
    for name, ang, (cx, cy), cw in cards:
        sheet = make_sheet(f"{ASSETS}/{name}.png", cw, int(cw * 1.18))
        paste_rot(bg, sheet, (cx, cy), ang, blur=30, opacity=80, dy=18)

    d = ImageDraw.Draw(bg)
    # "40+ pages" badge bottom-right, clear of everything
    br = int(S * .085)
    badge = Image.new("RGBA", (br * 2 + 60, br * 2 + 60), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse([30, 30, 30 + br * 2, 30 + br * 2], fill=PINK, outline=WHITE, width=14)
    bd.text((30 + br, 30 + br * .76), "40+", font=H1(int(br * .86)), fill=WHITE, anchor="mm")
    bd.text((30 + br, 30 + br * 1.34), "PAGES", font=BODY8(int(br * .42)), fill=WHITE, anchor="mm")
    paste_rot(bg, badge, (int(S * .875), int(S * .805)), -12, blur=22, opacity=70, dy=12)

    d = ImageDraw.Draw(bg)
    pill_fit(d, int(S * .925), "INSTANT DOWNLOAD  •  PRINT AT HOME  •  AGES 2-6",
             BODY8, INK, WHITE, start=58, pad=(56, 28), outline=MAGENTA, ow=6)
    bg.convert("RGB").save(f"{OUT}/01_hero.jpg", quality=93, subsampling=1)
    return "01_hero.jpg"

# =====================================================================
# 2. WHAT'S INSIDE (flatlay + worksheet)
# =====================================================================
def build_flatlay():
    raw = Image.open(f"{ASSETS}/base_desk_flatlay.png").convert("RGB")
    base = cover(raw, (S, S)).convert("RGBA")

    # large printed worksheet, right of centre
    sheet = make_sheet(f"{ASSETS}/ws_alphabet.png", int(S * .52), int(S * .62))
    paste_rot(base, sheet, (int(S * .645), int(S * .545)), -4, blur=34, opacity=95, dy=22)

    d = ImageDraw.Draw(base)
    # title banner (top-left)
    bann = Image.new("RGBA", (int(S * .545), 250), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bann)
    bd.rounded_rectangle([0, 0, bann.width - 1, bann.height - 1], 46, fill=MAGENTA + (248,))
    bd.text((bann.width / 2, 96), "WHAT'S INSIDE?", font=H1(104), fill=WHITE, anchor="mm")
    bd.text((bann.width / 2, 186), "40+ ready-to-print pages", font=BODY8(54), fill=(255, 226, 238), anchor="mm")
    shadowed(base, bann, (60, 78), blur=30, opacity=70, dy=14)

    # feature cards stacked down the left, clear of the sheet
    d = ImageDraw.Draw(base)
    feats = [("abc", TEAL, "A-Z letter tracing"), ("check", CORAL, "Numbers 1-20"),
             ("star", PURPLE, "Coloring pages"), ("heart", GREEN, "Shapes & feelings")]
    card_w, card_h = int(S * .335), 116
    y = int(S * .325)
    for kind, col, txt in feats:
        card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, card_w - 1, card_h - 1], card_h // 2, fill=(255, 255, 255, 246),
                             outline=col, width=6)
        icon(cd, kind, 74, card_h // 2, 36, col)
        f = fit_font(BODY8, txt, card_w - 165, start=50)
        cd.text((136, card_h // 2), txt, font=f, fill=INK, anchor="lm")
        shadowed(base, card, (60, y), blur=18, opacity=58, dy=8)
        y += card_h + 22

    d = ImageDraw.Draw(base)
    pill_fit(d, int(S * .93), "PRINT AS MANY TIMES AS YOU LIKE  •  A4 & US LETTER",
             BODY8, WHITE, INK, start=54, pad=(54, 26))
    base.convert("RGB").save(f"{OUT}/02_whats_inside.jpg", quality=93, subsampling=1)
    return "02_whats_inside.jpg"

# =====================================================================
# 3. BENEFITS
# =====================================================================
def build_benefits():
    bg = cover(Image.open(f"{ASSETS}/base_kid_doodle_bg.png").convert("RGB"), (S, S)).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (S, S), (255, 255, 255, 168)))
    d = ImageDraw.Draw(bg)

    pill(d, (int(S * .06), 60), "WHY PARENTS & GRANDPARENTS LOVE IT", H2(50), WHITE, TEAL, pad=(44, 20))
    title_stack(bg, d, ["LEARNING THAT FEELS", "LIKE PLAY"], S // 2, 185, 150, fills=[MAGENTA, INK])
    d = ImageDraw.Draw(bg)

    items = [("pencil", CORAL, "Builds fine motor skills", "Tracing dotted lines strengthens little hands"),
             ("abc", TEAL, "Letters & numbers", "A-Z plus 1-20, the preschool essentials"),
             ("clock", PURPLE, "Screen-free quiet time", "Perfect for rainy days and long car rides"),
             ("printer", GREEN, "Print again and again", "One purchase, unlimited copies at home")]
    x0, y0 = int(S * .07), int(S * .38)
    cw, ch = int(S * .41), int(S * .20)
    for i, (kind, col, head, sub) in enumerate(items):
        cx = x0 + (i % 2) * (cw + int(S * .045))
        cy = y0 + (i // 2) * (ch + int(S * .045))
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], 46, fill=WHITE, outline=col + (255,), width=8)
        cd.ellipse([54, 46, 54 + 128, 46 + 128], fill=col + (255,))
        icon(cd, kind, 54 + 64, 46 + 64, 44, WHITE)
        tx = 54 + 160
        avail = cw - tx - 46
        hf = fit_font(H2, head, avail, start=60)
        cd.text((tx, 66), head, font=hf, fill=INK)
        # wrap subtitle inside the card, shrinking font if needed
        bf = BODY(42)
        def wrap(font):
            out, line = [], ""
            for w_ in sub.split():
                t = (line + " " + w_).strip()
                if text_w(cd, t, font)[0] > avail:
                    out.append(line); line = w_
                else:
                    line = t
            out.append(line)
            return out
        lines = wrap(bf)
        while len(lines) > 2 and bf.size > 28:
            bf = BODY(bf.size - 2)
            lines = wrap(bf)
        for j, ln in enumerate(lines):
            cd.text((tx, 150 + j * (bf.size + 12)), ln, font=bf, fill=(112, 106, 100))
        shadowed(bg, card, (cx, cy), blur=26, opacity=60, dy=12)

    d = ImageDraw.Draw(bg)
    pill_fit(d, int(S * .925), "LOVED BY PARENTS  •  GRANDPARENTS  •  TEACHERS  •  HOMESCHOOLERS",
             BODY8, WHITE, MAGENTA, start=50, pad=(50, 24))
    bg.convert("RGB").save(f"{OUT}/03_benefits.jpg", quality=93, subsampling=1)
    return "03_benefits.jpg"

# =====================================================================
# 4. WHO IT'S FOR
# =====================================================================
def build_who_for():
    bg = cover(Image.open(f"{ASSETS}/base_child_coloring.png").convert("RGB"), (S, S)).convert("RGBA")
    veil = Image.new("RGBA", (S, S), (255, 252, 247, 0))
    vd = ImageDraw.Draw(veil)
    vd.rectangle([0, 0, S, int(S * .40)], fill=(255, 252, 247, 232))
    vd.rectangle([0, int(S * .40), S, int(S * .52)], fill=(255, 252, 247, 150))
    vd.rectangle([0, int(S * .78), S, S], fill=(255, 252, 247, 238))
    bg.alpha_composite(veil)
    d = ImageDraw.Draw(bg)

    pill(d, (int(S * .06), 58), "PERFECT FOR", H2(50), WHITE, MAGENTA, pad=(46, 20))
    title_stack(bg, d, ["BIG SMILES,", "BUSY HANDS"], S // 2, 175, 160, fills=[INK, CORAL])
    d = ImageDraw.Draw(bg)

    ages = [("TODDLERS", "2-4 yrs", YELLOW), ("PRESCHOOL", "3-5 yrs", TEAL), ("KINDERGARTEN", "5-6 yrs", PURPLE)]
    w_ = int(S * .285)
    x = (S - (w_ * 3 + 68)) // 2
    for txt, sub, col in ages:
        h = 214
        card = Image.new("RGBA", (w_, h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, w_ - 1, h - 1], 40, fill=WHITE, outline=col, width=8)
        cd.text((w_ / 2, 78), txt, font=H2(fit_font(H2, txt, w_ - 60, 66).size), fill=INK, anchor="mm")
        cd.text((w_ / 2, 156), sub, font=BODY8(52), fill=col, anchor="mm")
        shadowed(bg, card, (x, int(S * .425)), blur=24, opacity=58, dy=12)
        x += w_ + 34

    d = ImageDraw.Draw(bg)
    lines = [("Parents at home", HEART := "heart", PINK),
             ("Grandparents' kitchen table", "star", CORAL),
             ("Preschool & daycare", "book", TEAL),
             ("Homeschool & travel", "check", PURPLE)]
    y = int(S * .805)
    x = int(S * .06)
    for txt, kind, col in lines:
        icon(d, kind, x + 34, y + 34, 30, col)
        d.text((x + 88, y + 34), txt, font=BODY8(56), fill=INK, anchor="lm")
        y += 92
    bg.convert("RGB").save(f"{OUT}/04_who_for.jpg", quality=93, subsampling=1)
    return "04_who_for.jpg"

# =====================================================================
# 5. HOW IT WORKS
# =====================================================================
def build_how_it_works():
    bg = Image.new("RGBA", (S, S), CREAM + (255,))
    d = ImageDraw.Draw(bg)
    # soft polka dots
    for i in range(0, S, 150):
        for j in range(0, S, 150):
            d.ellipse([i + 40, j + 40, i + 70, j + 70], fill=(238, 228, 214, 255))

    pill(d, (int(S * .06), 60), "HOW IT WORKS", H2(50), WHITE, CORAL, pad=(46, 20))
    title_stack(bg, d, ["BUY  •  DOWNLOAD  •  PRINT"], S // 2, 180, 140, fills=[MAGENTA])
    d = ImageDraw.Draw(bg)

    steps = [("1", BLUE, "download", "Buy & download", "Instant access the moment you checkout - no waiting"),
             ("2", CORAL, "printer", "Print at home", "A4 & US Letter sizes included. Home or print shop"),
             ("3", GREEN, "smiley", "Learn & play", "Grab the crayons and get tracing, counting, colouring")]
    y = int(S * .365)
    for num, col, kind, head, sub in steps:
        h = 250
        card = Image.new("RGBA", (int(S * .88), h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, card.width - 1, h - 1], 46, fill=WHITE, outline=col, width=8)
        cd.ellipse([40, 44, 40 + 162, 44 + 162], fill=col)
        cd.text((40 + 81, 44 + 81), num, font=H1(104), fill=WHITE, anchor="mm")
        cd.text((240, 74), head, font=H2(66), fill=INK)
        cd.text((240, 152), sub, font=BODY(44), fill=(112, 106, 100))
        shadowed(bg, card, (int(S * .06), y), blur=26, opacity=60, dy=12)
        y += h + 40

    d = ImageDraw.Draw(bg)
    pill_fit(d, int(S * .905), "NO SHIPPING FEES  •  NO WAITING  •  PRINT FOREVER",
             BODY8, INK, YELLOW, start=52, pad=(52, 26), outline=INK, ow=5)
    bg.convert("RGB").save(f"{OUT}/05_how_it_works.jpg", quality=93, subsampling=1)
    return "05_how_it_works.jpg"

# =====================================================================
# 6. VIDEO COVER
# =====================================================================
def build_video_cover():
    bg = cover(Image.open(f"{ASSETS}/base_desk_flatlay.png").convert("RGB"), (S, S)).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (S, S), (255, 255, 255, 40)))
    d = ImageDraw.Draw(bg)

    # dark vignette panel for contrast
    panel = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rectangle([0, 0, S, int(S * .42)], fill=(40, 26, 34, 130))
    pd.rectangle([0, int(S * .80), S, S], fill=(40, 26, 34, 130))
    bg.alpha_composite(panel)

    d = ImageDraw.Draw(bg)
    pill(d, (int(S * .06), 62), "TWINKLETOTSCLUB", H2(50), INK, WHITE, pad=(46, 20))
    title_stack(bg, d, ["SEE IT IN ACTION"], S // 2, 170, 165, fills=[WHITE], stroke=MAGENTA, sw=12)
    d = ImageDraw.Draw(bg)

    # play button
    cx, cy, r = S // 2, int(S * .585), int(S * .115)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE + (245,), outline=MAGENTA, width=14)
    d.polygon([(cx - r * .30, cy - r * .46), (cx - r * .30, cy + r * .46), (cx + r * .46, cy)], fill=MAGENTA)

    pill_fit(d, int(S * .845), "12 SECOND PREVIEW  •  SOUND OFF, IT IS ALL VISUAL",
             BODY8, WHITE, MAGENTA, start=50, pad=(48, 24))
    bg.convert("RGB").save(f"{OUT}/06_video_cover.jpg", quality=93, subsampling=1)
    return "06_video_cover.jpg"

if __name__ == "__main__":
    made = []
    for fn in (build_hero, build_flatlay, build_benefits, build_who_for, build_how_it_works, build_video_cover):
        try:
            made.append(fn())
            print("built:", fn.__name__)
        except Exception as e:
            import traceback
            print("FAILED", fn.__name__, type(e).__name__, e)
            traceback.print_exc()
    print("done:", made)
