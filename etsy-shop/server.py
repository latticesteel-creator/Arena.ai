#!/usr/bin/env python3
"""Download page server for TwinkleTotsClub product files.
Serves the file tree with a friendly index page + direct download links.
Binds 0.0.0.0 so it works as a sandbox live preview.
"""
import os, io, zipfile, mimetypes, html, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT = "/home/user/Arena.ai/etsy-shop"
PORT = 8000

# ---------------------------------------------------------------- manifest
SETS = [
    {
        "id": "master",
        "title": "MASTER PACKAGE - Set-01 + Set-02 (everything)",
        "blurb": "The complete delivery ZIP: 8 colouring pages A4/300DPI + 8-page PDF "
                 "+ 6 true-vector SVG files + 8 transparent clip-art PNGs + all 5 "
                 "listing photos + a README with Etsy upload notes and licence terms.",
        "accent": "#6C4FC4",
        "path": ".",
        "exts": (".zip", ".txt"),
        "exclude_dirs": ("assets", "fonts", "wip", "listings", "designs", "videos",
                         "coloring", "clipart", "set-01-coloring-pages",
                         "set-02-character-clipart"),
    },
    {
        "id": "set-01",
        "title": "Set 01 — Printable Coloring Pages",
        "blurb": "8 colouring pages, clean black & white line art. A4 @ 300 DPI, "
                 "print-ready. Includes a single multi-page PDF for easy printing.",
        "accent": "#F2785C",
        "path": "set-01-coloring-pages",
        "exts": (".pdf", ".png"),
        "exclude_dirs": ("listing-images",),
    },
    {
        "id": "set-02",
        "title": "Set 02 — Character Clip Art",
        "blurb": "Cute character clip art as transparent-background PNGs (2000×2000). "
                 "Drop them onto worksheets, invitations, labels and party printables.",
        "accent": "#3FB8AF",
        "path": "set-02-character-clipart",
        "exts": (".png",),
        "exclude_dirs": (),
    },
    {
        "id": "listing-images",
        "title": "Listing Photos — Main Bundle",
        "blurb": "The six 2000×2000 Etsy listing photos for the Fun Kids Learning "
                 "Printables bundle, plus the two listing videos.",
        "accent": "#D6336C",
        "path": "listings",
        "exts": (".jpg",),
        "exclude_dirs": (),
        "extra_dirs": ["videos"],
    },
    {
        "id": "bonus",
        "title": "Bonus — Celestial Botanical Art Prints",
        "blurb": "Six bonus wall-art prints in a matching palette. Use as a second "
                 "listing or a free gift with purchase.",
        "accent": "#7FA37A",
        "path": "designs",
        "exts": (".png",),
        "exclude_dirs": (),
    },
]

def collect(paths, exts, exclude_dirs=()):
    found = []
    for base in paths:
        full = os.path.join(ROOT, base)
        if not os.path.isdir(full):
            continue
        if base == ".":                       # top level only, no recursion
            for fn in sorted(os.listdir(full)):
                fp = os.path.join(full, fn)
                if os.path.isfile(fp) and not fn.startswith(".") and fn.lower().endswith(exts):
                    found.append((fn, os.path.getsize(fp)))
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            for fn in sorted(filenames):
                if fn.startswith(".") or not fn.lower().endswith(exts):
                    continue
                p = os.path.join(dirpath, fn)
                found.append((os.path.relpath(p, ROOT), os.path.getsize(p)))
    return sorted(found)

def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n/1:.0f} {unit}" if False else (
                f"{n:.0f} {unit}" if n >= 10 or unit == "B" else f"{n:.1f} {unit}")
        n /= 1024
    return f"{n:.1f} GB"

def fmt_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n/1024:.0f} KB"
    return f"{n/1024/1024:.1f} MB"

def build_zip(paths):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel in paths:
            z.write(os.path.join(ROOT, rel), rel.replace("/", os.sep))
    return buf.getvalue()

# ---------------------------------------------------------------- html
def page():
    total_files = 0
    total_bytes = 0
    sections = []
    for s in SETS:
        paths = [s["path"]] + s.get("extra_dirs", [])
        files = collect(paths, s["exts"], s.get("exclude_dirs", ()))
        total_files += len(files)
        total_bytes += sum(sz for _, sz in files)
        if not files:
            continue
        rows = []
        for rel, sz in files:
            name = os.path.basename(rel)
            sub = os.path.dirname(rel).split("/")[-1] if os.path.dirname(rel) != s["path"] else ""
            rows.append(f"""
            <li>
              <a class="dl" href="/files/{urllib.parse.quote(rel)}" download>
                <span class="ico">{icon_for(name)}</span>
                <span class="nm">{html.escape(name)}<em>{html.escape(sub)}</em></span>
                <span class="sz">{fmt_size(sz)}</span>
                <span class="arrow">&darr;</span>
              </a>
            </li>""")
        sections.append(f"""
      <section class="card" style="--accent:{s['accent']}">
        <header>
          <div>
            <h2>{html.escape(s['title'])}</h2>
            <p>{html.escape(s['blurb'])}</p>
          </div>
          <a class="btn" href="/zip/{s['id']}">Download set &darr;</a>
        </header>
        <ul class="files">{''.join(rows)}</ul>
        <footer>{len(files)} files &middot; {fmt_size(sum(sz for _, sz in files))}</footer>
      </section>""")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TwinkleTotsClub — Download Centre</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<style>
  * {{ box-sizing: border-box; }}
  :root {{
    --ink:#3A3A3A; --mag:#D6336C; --coral:#F2785C; --teal:#3FB8AF;
    --cream:#FFFAF2; --line:#EFE6D8;
  }}
  body {{
    margin:0; background:var(--cream); color:var(--ink);
    font:16px/1.55 "Nunito","Segoe UI",system-ui,-apple-system,sans-serif;
    background-image:
      radial-gradient(circle at 12% 18%, rgba(214,51,108,.06) 0 14px, transparent 15px),
      radial-gradient(circle at 82% 42%, rgba(63,184,175,.07) 0 18px, transparent 19px),
      radial-gradient(circle at 34% 78%, rgba(255,201,60,.10) 0 12px, transparent 13px);
    background-size: 260px 260px, 300px 300px, 220px 220px;
  }}
  .wrap {{ max-width: 1020px; margin: 0 auto; padding: 44px 22px 90px; }}
  .hero {{ text-align:center; margin-bottom: 36px; }}
  .brand {{
    display:inline-block; background:var(--mag); color:#fff; font-weight:800;
    letter-spacing:.09em; font-size:13px; padding:9px 20px; border-radius:999px;
    text-transform:uppercase;
  }}
  h1 {{ font-size: clamp(30px,5.4vw,50px); line-height:1.08; margin:18px 0 10px; font-weight:800; }}
  h1 span {{ color:var(--mag); }}
  .sub {{ color:#7A736B; max-width:640px; margin:0 auto; font-size:17px; }}
  .stats {{
    display:flex; gap:26px; justify-content:center; flex-wrap:wrap; margin-top:22px;
    font-weight:800; color:#8A8178; font-size:14px; letter-spacing:.04em; text-transform:uppercase;
  }}
  .card {{
    background:#fff; border-radius:22px; padding:26px 26px 18px; margin-bottom:26px;
    border:2px solid var(--line); border-top:7px solid var(--accent);
    box-shadow:0 10px 26px rgba(90,70,50,.07);
  }}
  .card header {{ display:flex; gap:18px; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; }}
  h2 {{ margin:0 0 6px; font-size:22px; }}
  .card header p {{ margin:0; color:#7A736B; font-size:15px; max-width:600px; }}
  .btn {{
    background:var(--accent); color:#fff; text-decoration:none; font-weight:800;
    padding:12px 20px; border-radius:999px; white-space:nowrap; font-size:14px;
    box-shadow:0 6px 14px rgba(0,0,0,.13); transition:transform .12s ease;
  }}
  .btn:hover {{ transform:translateY(-2px); }}
  ul.files {{ list-style:none; margin:20px 0 8px; padding:0; }}
  ul.files li + li {{ border-top:1px dashed var(--line); }}
  a.dl {{
    display:flex; align-items:center; gap:14px; padding:12px 8px; text-decoration:none;
    color:var(--ink); border-radius:12px; transition:background .12s ease;
  }}
  a.dl:hover {{ background:#FFF7EC; }}
  .ico {{
    width:40px; height:40px; flex:0 0 40px; border-radius:11px; display:grid;
    place-items:center; font-size:16px; font-weight:800; color:#fff;
    background:var(--accent);
  }}
  .nm {{ flex:1; font-weight:700; word-break:break-all; }}
  .nm em {{ display:block; font-style:normal; font-weight:600; color:#A79E93; font-size:12.5px; }}
  .sz {{ color:#A79E93; font-size:13px; font-weight:700; white-space:nowrap; }}
  .arrow {{ color:var(--accent); font-weight:800; font-size:18px; }}
  .card footer {{ color:#A79E93; font-size:13px; font-weight:700; padding:6px 8px 4px; }}
  .note {{
    background:#fff; border:2px dashed var(--line); border-radius:18px; padding:20px 24px;
    color:#7A736B; font-size:14.5px; margin-top:8px;
  }}
  .note b {{ color:var(--ink); }}
  .note ul {{ margin:10px 0 0; padding-left:20px; }}
  .note li {{ margin:5px 0; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <span class="brand">TwinkleTotsClub &middot; Download Centre</span>
      <h1>Your files are <span>ready to download</span></h1>
      <p class="sub">Everything generated for the shop — print-ready products, Etsy listing
      photos, videos and bonus art. Click any file, or grab a whole set as a ZIP.</p>
      <div class="stats">
        <span>{total_files} files</span><span>&middot;</span>
        <span>{fmt_size(total_bytes)} total</span><span>&middot;</span>
        <span>updated just now</span>
      </div>
    </div>

    {''.join(sections)}

    <div class="note">
      <b>How to use these:</b>
      <ul>
        <li><b>Set 01 / Set 02</b> are the products you deliver to buyers after they purchase.</li>
        <li><b>Listing photos</b> go in the Etsy <i>Photo and video</i> tab — upload them in filename order.</li>
        <li>Etsy allows <b>max 5 files per digital listing, 20&nbsp;MB each</b> — zip the set if you're over.</li>
        <li>Add the AI disclosure line to your listing description (it's in the shop README).</li>
      </ul>
    </div>
  </div>
</body>
</html>"""

def icon_for(name):
    n = name.lower()
    if n.endswith(".pdf"):
        return "PDF"
    if n.endswith(".mp4"):
        return "VID"
    if n.endswith(".zip"):
        return "ZIP"
    if n.endswith(".txt"):
        return "B64"
    if n.endswith(".jpg"):
        return "IMG"
    return "PNG"

# ---------------------------------------------------------------- server
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype, extra=None):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/" or path == "/index.html":
            return self._send(200, page(), "text/html; charset=utf-8",
                              {"Cache-Control": "no-store"})

        if path.startswith("/zip/"):
            sid = path[len("/zip/"):]
            s = next((x for x in SETS if x["id"] == sid), None)
            if not s:
                return self._send(404, "unknown set", "text/plain")
            paths = [r for r, _ in collect([s["path"]] + s.get("extra_dirs", []),
                                           s["exts"], s.get("exclude_dirs", ()))]
            data = build_zip(paths)
            return self._send(200, data, "application/zip", {
                "Content-Disposition": f'attachment; filename="{sid}.zip"',
            })

        if path.startswith("/files/"):
            rel = urllib.parse.unquote(path[len("/files/"):])
            full = os.path.realpath(os.path.join(ROOT, rel))
            if not full.startswith(os.path.realpath(ROOT)) or not os.path.isfile(full):
                return self._send(404, "not found", "text/plain")
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            size = os.path.getsize(full)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition",
                             f'attachment; filename="{os.path.basename(full)}"')
            self.end_headers()
            if self.command == "HEAD":
                return
            with open(full, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            return

        return self._send(404, "not found", "text/plain")

if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Download centre on http://0.0.0.0:{PORT}")
    srv.serve_forever()
