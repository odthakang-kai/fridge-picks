#!/usr/bin/env python3
"""Build Floor Copilot and the customer page from the templates in src/.

The fridge catalog and its price date live in exactly one place: the deployed
customer page, index.html (const RAW=`...` and const DATA_DATE=...). The weekly
refresh rewrites those; this build reads them back so a rebuild never ships
stale prices.

Outputs
  index.html                      customer page served by GitHub Pages
  build/floor-copilot.html        Julian's floor tool, published as a Claude artifact
  build/customer-artifact.html    backup copy of the customer page as a Claude artifact
  app/                            Floor Copilot as a home-screen web app (offline, barcode scanning)

usage: python3 tools/build.py
"""
import os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

# ---- catalog + price date from the deployed page ----
deployed = read(P("index.html"))
m = re.search(r"const RAW=`([\s\S]*?)`;", deployed)
d = re.search(r'const DATA_DATE=new Date\("(\d{4}-\d{2}-\d{2})T12:00:00"\)', deployed)
if not m or not d:
    sys.exit("index.html is missing its catalog or price date; restore it from git before building")
catalog, day = m.group(1).strip(), d.group(1)
rows = catalog.split("\n")
bad = [r for r in rows if r.count("|") != 30]
if len(rows) < 600 or bad:
    sys.exit(f"catalog looks wrong: {len(rows)} rows, {len(bad)} malformed")

def set_date(text):
    out, n = re.subn(r'const DATA_DATE=new Date\("\d{4}-\d{2}-\d{2}T12:00:00"\)',
                     f'const DATA_DATE=new Date("{day}T12:00:00")', text, count=1)
    if n != 1:
        sys.exit("template is missing const DATA_DATE")
    return out

# ---- Floor Copilot ----
app_t = read(P("src", "floor-copilot.template.html"))
qrlib = read(P("src", "vendor", "qrcode-generator.js")).replace("</script", "<\\/script")
app = set_date(app_t.replace("__CATALOG__", catalog).replace("__QRLIB__", qrlib))
write(P("build", "floor-copilot.html"), app)

# ---- customer page (shares fit logic with the app template) ----
def between(src, a, b):
    i = src.index(a); j = src.index(b, i); return src[i:j]
shared = (between(app_t, "const STYLE=", "function space(){")
          + between(app_t, "function fit(", "/* ---------- list")
          + between(app_t, "const BAYES=", "const DISP=")
          + between(app_t, "const people=", "function optCard("))
cust = set_date(read(P("src", "customer.template.html")).replace("__SHARED__", shared).replace("__CATALOG__", catalog))
write(P("build", "customer-artifact.html"), cust)

body = cust.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
cut = body.index("</style>") + len("</style>")
page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
        "<meta name=\"robots\" content=\"noindex\">\n"
        + body[:cut]
        + "\n<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
          "body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n"
        + body[cut:] + "\n</body>\n</html>\n")
write(P("index.html"), page)

# ---- home-screen web app (GitHub Pages /app/, works offline) ----
def wrap(body, head_extra, tail_script=""):
    body = body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    cut = body.index("</style>") + len("</style>")
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
            "<meta name=\"robots\" content=\"noindex\">\n" + head_extra
            + body[:cut]
            + "\n<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
              "body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n"
            + body[cut:] + tail_script + "\n</body>\n</html>\n")

APP_HEAD = ('<link rel="manifest" href="manifest.webmanifest">\n'
            '<meta name="theme-color" content="#F96302">\n'
            '<meta name="mobile-web-app-capable" content="yes">\n'
            '<meta name="apple-mobile-web-app-capable" content="yes">\n'
            '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
            '<meta name="apple-mobile-web-app-title" content="Copilot">\n'
            '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
            '<link rel="icon" type="image/png" href="icon-192.png">\n'
            '<script defer src="vendor/zxing-reader.js"></script>\n')
pwa_js = read(P("src", "app", "pwa.js"))
write(P("app", "index.html"), wrap(app, APP_HEAD, '\n<script id="pwa">\n' + pwa_js + "</script>"))

import hashlib
os.makedirs(P("app", "vendor"), exist_ok=True)
h = hashlib.sha256()
for name in ("manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"):
    shutil.copyfile(P("src", "app", name), P("app", name)); h.update(open(P("src", "app", name), "rb").read())
for name in ("zxing-reader.js", "zxing_reader.wasm", "LICENSE"):
    shutil.copyfile(P("src", "vendor", "zxing", name), P("app", "vendor", name)); h.update(open(P("src", "vendor", "zxing", name), "rb").read())
sw = read(P("src", "app", "sw.template.js"))
h.update(sw.encode())
write(P("app", "sw.js"), sw.replace("__VERSION__", h.hexdigest()[:12]))

# ---- syntax check every page's main script ----
node = shutil.which("node")
checks = [(f, re.findall(r"<script>([\s\S]*?)</script>", read(P(f)))[-1])
          for f in ("index.html", "build/floor-copilot.html", "build/customer-artifact.html", "app/index.html")]
checks += [("app/index.html pwa", pwa_js), ("app/sw.js", read(P("app", "sw.js")))]
for f, js in checks:
    tmp = P("build", ".check.js"); write(tmp, js)
    if node:
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        if r.returncode:
            os.remove(tmp); sys.exit(f"syntax error in {f}:\n{r.stderr}")
    os.remove(tmp)
print(f"built 4 pages + app shell: {len(rows)} fridges, prices dated {day}" + ("" if node else " (node not found, skipped syntax check)"))
