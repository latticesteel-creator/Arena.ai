#!/usr/bin/env python3
"""Listing preview images for Set-02 (character clip art).
Layout auto-adapts to however many characters exist."""
import os, glob, sys
sys.path.insert(0, "/home/user/Arena.ai/etsy-shop")
from PIL import Image, ImageDraw
from build_listings import (cover, fit_contain, shadowed, paste_rot, pill, pill_fit,
                            text_w, fit_font, title_stack, icon,
                            S, ASSETS, F, H1, H2, BODY, BODY8,
                            INK, MAGENTA, PINK, CORAL, YELLOW, TEAL, GREEN, BLUE, PURPLE,
                            CREAM, WHITE)

ROOT = "/home/user/Arena.ai/etsy-shop"
CLIP = f"{ROOT}/set-02-character-clipart"
OUT = f"{CLIP}/listing-images"

NAMES = {
    "k01_cat": "Cat", "k02_dog": "Dog", "k03_elephant": "Elephant", "k04_bunny": "Bunny",
    "k05_bear": "Bear", "k06_fox": "Fox", "k07_owl": "Owl", "k08_penguin": "Penguin",
}

def chars():
    return sorted(glob.glob(f"{CLIP}/k*.png"))

def checker(size, a=(255, 246, 250), b=(255, 255, 255), step=34):
    im = Image.new("RGB", size, b)
    d = ImageDraw.Draw(im)
    for i in range(0, size[0], step):
        for j in range(0, size[1], step):
            if (i // step + j // step) % 2 == 0:
                d.rectangle([i, j, i + step - 1, j + step - 1], fill=a)
    return im.convert("RGBA")

def cover_set02(out):
    """Hero: characters in a row with a big headline."""
    files = chars()
    bg = checker((S, S))
    bg.alpha_composite(Image.new("RGBA", (S, S), (255, 255, 255, 120)))
    d = ImageDraw.Draw(bg)

    pill(d, (110, 58), "TWINKLETOTSCLUB", H2(46), WHITE, TEAL, pad=(44, 20))
    w1, _ = text_w(d, "TWINKLETOTSCLUB", H2(46))
    pill(d, (110 + w1 + 44 + 24, 58), "SET 02", H2(46), INK, YELLOW, pad=(44, 20))

    y = title_stack(bg, d, ["CUTE CHARACTER"], S // 2, 210, 225, fills=[TEAL], max_frac=0.80, stroke=WHITE)
    y = title_stack(bg, d, ["CLIP ART"], S // 2, y + 4, 180, fills=[MAGENTA], sw=16, max_frac=0.80)
    d = ImageDraw.Draw(bg)

    n = max(1, min(len(files), 4))
    per_row = n if n <= 4 else 4
    rows = (len(files) + per_row - 1) // per_row
    cell_w = int(S * 0.86 / per_row)
    avail_h = int(S * 0.40)
    cell_h = min(cell_w, avail_h // max(1, rows))
    y0 = y + 40
    for i, f in enumerate(files[:8]):
        col, row = i % per_row, i // per_row
        im = Image.open(f)
        r = min(cell_w * 0.92 / im.width, cell_h * 0.92 / im.height)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
        cx = int(S * 0.07) + col * cell_w + cell_w // 2
        cy = y0 + row * cell_h + cell_h // 2
        paste_rot(bg, im, (cx, cy), 0, blur=16, opacity=45, dy=10,
                  tint=(120, 110, 100))

    d = ImageDraw.Draw(bg)
    pill_fit(d, int(S * 0.915), "TRANSPARENT PNG  •  2000 x 2000  •  COMMERCIAL USE",
             BODY8, WHITE, INK, start=56, pad=(54, 26))
    bg.convert("RGB").save(out, quality=93, subsampling=1)

def detail_set02(out):
    """Show 1 transparency proof + benefit cards."""
    files = chars()
    bg = checker((S, S))
    d = ImageDraw.Draw(bg)
    pill_fit(d, 70, "TRANSPARENT BACKGROUND — DROP IT ON ANYTHING", H2, WHITE, TEAL,
             start=54, pad=(50, 22))
    d = ImageDraw.Draw(bg)

    if files:
        im = Image.open(files[0])
        r = min(int(S * .40) / im.width, int(S * .40) / im.height)
        im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        # two demo tiles showing the cut-out over colour
        for k, tile_col in enumerate([(255, 214, 232), (214, 240, 236)]):
            tw, th = int(S * .30), int(S * .30)
            tile = Image.new("RGB", (tw, th), tile_col).convert("RGBA")
            cm = im.copy()
            rr = min(tw * .84 / cm.width, th * .84 / cm.height)
            cm = cm.resize((int(cm.width * rr), int(cm.height * rr)), Image.LANCZOS)
            tile.alpha_composite(cm, ((tw - cm.width) // 2, (th - cm.height) // 2))
            shadowed(bg, tile, (int(S * .08) + k * (tw + 40), int(S * .17)), blur=24, opacity=55, dy=12)

    d = ImageDraw.Draw(bg)
    feats = [("download", TEAL, "PNG, transparent bg"), ("star", CORAL, "2000 x 2000 px"),
             ("printer", PURPLE, "Print & digital ready"), ("check", GREEN, "Commercial licence")]
    y = int(S * .54)
    for kind, col, txt in feats:
        card_w, card_h = int(S * .84), 118
        card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, card_w - 1, card_h - 1], card_h // 2,
                             fill=(255, 255, 255, 246), outline=col, width=6)
        icon(cd, kind, 78, card_h // 2, 38, col)
        cd.text((148, card_h // 2), txt, font=BODY8(54), fill=INK, anchor="lm")
        shadowed(bg, card, (int(S * .08), y), blur=18, opacity=58, dy=8)
        y += card_h + 24

    d = ImageDraw.Draw(bg)
    pill_fit(d, int(S * .935), "PERFECT FOR WORKSHEETS  •  INVITES  •  LABELS  •  PARTY PRINTABLES",
             BODY8, WHITE, MAGENTA, start=50, pad=(50, 24))
    bg.convert("RGB").save(out, quality=93, subsampling=1)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cover_set02(f"{OUT}/01_cover.jpg");  print("set02 01_cover")
    detail_set02(f"{OUT}/02_transparent.jpg"); print("set02 02_transparent")
    print("characters found:", len(chars()))
