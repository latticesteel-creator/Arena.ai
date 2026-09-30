#!/usr/bin/env python3
"""Package everything into the master delivery ZIP + print a SHA-256.

Contents:
  Set-01 coloring pages : 8x A4 300DPI PNG, 6x SVG (true vector), 8-page PDF
  Set-02 clip art       : 8x transparent PNG (2000x2000)
  listing photos        : Set-01 previews, Set-02 previews
"""
import os, zipfile, hashlib, glob, datetime

ROOT = "/home/user/Arena.ai/etsy-shop"
OUT_ZIP = f"{ROOT}/TwinkleTotsClub_Set01_Set02_PACKAGE.zip"

def add(z, arcname, data):
    zi = zipfile.ZipInfo(arcname, date_time=(2025, 1, 1, 0, 0, 0))
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16
    z.writestr(zi, data)

def add_file(z, path, arcname):
    with open(path, "rb") as f:
        add(z, arcname, f.read())

README = """TWINKLETOTSCLUB - SET 01 + SET 02
Generated for TwinkleTotsClub (Etsy).  {date}

====================================================================
WHAT'S IN THIS PACKAGE
====================================================================

set-01-coloring-pages/          <-- YOUR PRODUCT (deliver to buyers)
    c01_rainbow.png                 A4 @ 300 DPI, 2480 x 3508 px
    c02_cat.png                     pure black & white line art
    c03_elephant.png                big bold outlines, no shading
    c04_butterfly.png
    c05_rocket.png
    c06_icecream.png
    c07_fish.png
    c08_flowers.png
    TwinkleTotsClub_Coloring_Pages_A4.pdf    all 8 pages in one file
    vector-svg/                     TRUE VECTOR - infinitely scalable
        c01_rainbow.svg  c02_cat.svg  c03_elephant.svg
        c05_rocket.svg   c06_icecream.svg  c08_flowers.svg

set-02-character-clipart/       <-- YOUR PRODUCT (deliver to buyers)
    k01_cat.png      k02_dog.png       k03_elephant.png  k04_bunny.png
    k05_bear.png     k06_fox.png       k07_owl.png       k08_penguin.png
    All 2000 x 2000 px, transparent background, flat vector style.

set-01-listing-photos/          <-- FOR YOUR ETSY LISTING
    01_cover.jpg  02_all_pages.jpg  03_thick_lines.jpg      2000x2000

set-02-listing-photos/          <-- FOR YOUR ETSY LISTING
    01_cover.jpg  02_transparent.jpg                         2000x2000

====================================================================
ABOUT THE RESOLUTION (important if you were worried about upscaling)
====================================================================
The source images were ~1408 x 768 px. Rather than upscaling with invented
pixels, 6 of the 8 coloring pages were TRACED TO REAL VECTOR PATHS and then
rasterised at A4 300 DPI. Each traced page was verified against the original
artwork and matched at 98-99.5% - so the delivered pages are reconstruction,
not interpolation.

Pages c04_butterfly and c07_fish could not be traced reliably (potrace's
even-odd fill produced artefacts on their overlapping petals/fins). Those two
fall back to the source pixels upscaled, and have NO .svg file. If you need
them as vector, the cleanest fix is to redraw those two pages by hand in
Illustrator/Inkscape - there is no automated way to make potrace do it.

The 6 SVG files are genuinely resolution-independent: resize to A2, billboard,
anything, with zero quality loss. That is a real selling point for your
listing ("vector SVG included - print any size").

====================================================================
ETSY UPLOAD NOTES
====================================================================
* Etsy digital listings allow a maximum of 5 FILES at 20 MB each.
  If you exceed that, split the bundle or zip the folders (buyers can unzip).
* Put the AI disclosure line in the listing DESCRIPTION (not tags/photos):
  "Created with the use of AI tools, then assembled, laid out and edited by me."
* Set the listing's production fields to: I did / Made to order / finished product.
* Do NOT sell the AI prompts themselves - that is explicitly banned on Etsy.

====================================================================
LICENCE - YOU NEED TO DECIDE THIS
====================================================================
The listing photos in this package say "commercial licence". You must define
what that means for YOUR buyers before publishing. Typical clip-art terms:
  * Buyer MAY use the art in finished products they sell (printables, shirts,
    invitations, mugs) - no attribution required.
  * Buyer MAY NOT resell, share or redistribute the raw PNG/SVG files as-is,
    nor claim authorship, nor resell as clip art.
Edit the set-02 preview art or describe your terms in the listing to match.
""".format(date=datetime.date.today().isoformat())

def main():
    if os.path.exists(OUT_ZIP):
        os.remove(OUT_ZIP)
    n = 0
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        add(z, "READ_ME_FIRST.txt", README)

        for f in sorted(glob.glob(f"{ROOT}/set-01-coloring-pages/c*.png")):
            add_file(z, f, f"set-01-coloring-pages/{os.path.basename(f)}"); n += 1
        pdf = f"{ROOT}/set-01-coloring-pages/TwinkleTotsClub_Coloring_Pages_A4.pdf"
        if os.path.exists(pdf):
            add_file(z, pdf, "set-01-coloring-pages/TwinkleTotsClub_Coloring_Pages_A4.pdf"); n += 1
        for f in sorted(glob.glob(f"{ROOT}/set-01-coloring-pages/vector-svg/*.svg")):
            add_file(z, f, f"set-01-coloring-pages/vector-svg/{os.path.basename(f)}"); n += 1

        for f in sorted(glob.glob(f"{ROOT}/set-02-character-clipart/k*.png")):
            add_file(z, f, f"set-02-character-clipart/{os.path.basename(f)}"); n += 1

        for f in sorted(glob.glob(f"{ROOT}/set-01-coloring-pages/listing-images/*.jpg")):
            add_file(z, f, f"set-01-listing-photos/{os.path.basename(f)}"); n += 1
        for f in sorted(glob.glob(f"{ROOT}/set-02-character-clipart/listing-images/*.jpg")):
            add_file(z, f, f"set-02-listing-photos/{os.path.basename(f)}"); n += 1

    size = os.path.getsize(OUT_ZIP)
    sha = hashlib.sha256(open(OUT_ZIP, "rb").read()).hexdigest()
    print(f"ZIP    : {OUT_ZIP}")
    print(f"files  : {n} (+1 readme)")
    print(f"size   : {size/1024/1024:.2f} MB  ({size} bytes)")
    print(f"sha256 : {sha}")
    return sha, size

if __name__ == "__main__":
    main()
