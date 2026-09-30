#!/usr/bin/env python3
"""Build Etsy listing preview images for Set-01 (coloring pages) and Set-02 (clipart).
Reuses the helpers from build_listings.py so the branding matches the shop."""
import os, glob, sys
sys.path.insert(0, "/home/user/Arena.ai/etsy-shop")
from PIL import Image, ImageDraw, ImageFont
from build_listings import (cover, fit_contain, shadowed, paste_rot, pill, pill_fit,
                            text_w, fit_font, title_stack, icon, make_sheet,
                            S, ASSETS, OUT, F, H1, H2, BODY, BODY8,
                            INK, MAGENTA, PINK, CORAL, YELLOW, TEAL, GREEN, BLUE, PURPLE,
                            CREAM, WHITE)

ROOT = "/home/user/Arena.ai/etsy-shop"

def page_thumb(path, box):
    """Coloring page -> white sheet thumbnail of size box."""
    art = Image.open(path).convert("RGB")
    im = art.crop(art.convert("L").point(lambda v: 255 if v < 248 else 0).getbbox())
    return fit_contain(im, box)

# ---------------------------------------------------------------- SET 01
def set01_cover(out):
    bg = cover(Image.open(f"{ASSETS}/base_kid_doodle_bg.png").convert("RGB"), (S, S)).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (S, S), (255, 255, 255, 152)))
    d = ImageDraw.Draw(bg)
    pill(d, (110, 58), "TWINKLETOTSCLUB", H2(46), WHITE, MAGENTA, pad=(44, 20))
    w1, _ = text_w(d, "TWINKLETOTSCLUB", H2(46))
    pill(d, (110 + w1 + 44 + 24, 58), "SET 01", H2(46), INK, YELLOW, pad=(44, 20))

    y = title_stack(bg, d, ["8 PRINTABLE"], S // 2, 210, 240, fills=[MAGENTA], max_frac=0.78)
    y = title_stack(bg, d, ["COLORING PAGES"], S // 2, y + 4, 165, fills=[INK], sw=16, max_frac=0.78)
    d = ImageDraw.Draw(bg)

    pages = sorted(glob.glob(f"{ROOT}/set-01-coloring-pages/*.png"))
    picks = [pages[1], pages[3], pages[4]]      # cat, butterfly, rocket
    layout = [(-10, (int(S * .225), int(S * .70)), int(S * .30)),
              (9,  (int(S * .785), int(S * .705)), int(S * .30)),
              (2,  (int(S * .505), int(S * .73)), int(S * .365))]
    for f, (ang, ctr, cw) in zip(picks, layout):
        ph = int(cw * 1.30)
        sheet = Image.new("RGBA", (cw, ph), WHITE)
        sd = ImageDraw.Draw(sheet)
        sd.rounded_rectangle([0, 0, cw - 1, ph - 1], 18, fill=WHITE, outline=(226, 220, 212), width=3)
        art = page_thumb(f, (int(cw * .86), int(ph * .86)))
        sheet.alpha_composite(art, ((cw - art.width) // 2, (ph - art.height) // 2))
        paste_rot(bg, sheet, ctr, ang, blur=30, opacity=80, dy=18)

    d = ImageDraw.Draw(bg)
    br = int(S * .085)
    badge = Image.new("RGBA", (br * 2 + 60, br * 2 + 60), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse([30, 30, 30 + br * 2, 30 + br * 2], fill=CORAL, outline=WHITE, width=14)
    bd.text((30 + br, 30 + br * .76), "8", font=H1(int(br * .95)), fill=WHITE, anchor="mm")
    bd.text((30 + br, 30 + br * 1.34), "PAGES", font=BODY8(int(br * .42)), fill=WHITE, anchor="mm")
    paste_rot(bg, badge, (int(S * .875), int(S * .80)), -12, blur=22, opacity=70, dy=12)

    d = ImageDraw.Draw(bg)
    pill_fit(d, int(S * .925), "INSTANT DOWNLOAD  •  A4 300DPI  •  AGES 2-6",
             BODY8, INK, WHITE, start=58, pad=(56, 28), outline=MAGENTA, ow=6)
    bg.convert("RGB").save(out, quality=93, subsampling=1)

def set01_grid(out):
    bg = Image.new("RGBA", (S, S), CREAM + (255,))
    d = ImageDraw.Draw(bg)
    for i in range(0, S, 150):
        for j in range(0, S, 150):
            d.ellipse([i + 40, j + 40, i + 70, j + 70], fill=(240, 231, 219, 255))

    pill_fit(d, 70, "ALL 8 PAGES INCLUDED", H2, WHITE, CORAL, start=64, pad=(54, 24))
    d = ImageDraw.Draw(bg)
    pages = sorted(glob.glob(f"{ROOT}/set-01-coloring-pages/*.png"))
    cols, rows = 4, 2
    gx0, gy0 = 96, int(S * .215)
    cell = (S - gx0 * 2 - 30 * (cols - 1)) // cols
    for i, f in enumerate(pages[:8]):
        col, row = i % cols, i // cols
        x = gx0 + col * (cell + 30)
        y = gy0 + row * (int(cell * 1.32) + 40)
        ph = int(cell * 1.32)
        sheet = Image.new("RGBA", (cell, ph), WHITE)
        sd = ImageDraw.Draw(sheet)
        sd.rounded_rectangle([0, 0, cell - 1, ph - 1], 16, fill=WHITE, outline=(228, 222, 214), width=3)
        art = page_thumb(f, (int(cell * .88), int(ph * .88)))
        sheet.alpha_composite(art, ((cell - art.width) // 2, (ph - art.height) // 2))
        shadowed(bg, sheet, (x, y), blur=20, opacity=52, dy=10)

    d = ImageDraw.Draw(bg)
    pill_fit(d, int(S * .90), "PRINT AT HOME  •  UNLIMITED COPIES  •  A4 + US LETTER",
             BODY8, WHITE, INK, start=56, pad=(54, 26))
    bg.convert("RGB").save(out, quality=93, subsampling=1)

def set01_closeup(out):
    raw = Image.open(f"{ASSETS}/base_desk_flatlay.png").convert("RGB")
    base = cover(raw, (S, S)).convert("RGBA")
    pages = sorted(glob.glob(f"{ROOT}/set-01-coloring-pages/*.png"))
    sheet = make_sheet(pages[3], int(S * .50), int(S * .615))       # butterfly
    paste_rot(base, sheet, (int(S * .655), int(S * .545)), -4, blur=34, opacity=95, dy=22)

    d = ImageDraw.Draw(base)
    bann = Image.new("RGBA", (int(S * .545), 250), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bann)
    bd.rounded_rectangle([0, 0, bann.width - 1, bann.height - 1], 46, fill=CORAL + (248,))
    bd.text((bann.width / 2, 96), "THICK EASY LINES", font=H1(96), fill=WHITE, anchor="mm")
    bd.text((bann.width / 2, 186), "perfect for little hands", font=BODY8(54), fill=(255, 232, 224), anchor="mm")
    shadowed(base, bann, (60, 78), blur=30, opacity=70, dy=14)

    d = ImageDraw.Draw(base)
    feats = [("star", CORAL, "Big bold outlines"), ("smiley", TEAL, "Cute friendly art"),
             ("printer", PURPLE, "A4 + US Letter"), ("download", GREEN, "Instant download")]
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
    pill_fit(d, int(S * .93), "SET 01  •  8 PRINTABLE COLORING PAGES",
             BODY8, WHITE, INK, start=54, pad=(54, 26))
    base.convert("RGB").save(out, quality=93, subsampling=1)

if __name__ == "__main__":
    OUT1 = f"{ROOT}/set-01-coloring-pages/listing-images"
    os.makedirs(OUT1, exist_ok=True)
    set01_cover(f"{OUT1}/01_cover.jpg");        print("set01 01_cover")
    set01_grid(f"{OUT1}/02_all_pages.jpg");     print("set01 02_all_pages")
    set01_closeup(f"{OUT1}/03_thick_lines.jpg");print("set01 03_thick_lines")
