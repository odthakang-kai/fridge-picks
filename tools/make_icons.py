#!/usr/bin/env python3
"""Draw the home-screen icons for the Floor Copilot web app (needs Pillow).
Original artwork: a plain fridge outline with a fit check mark. No store logos.
usage: python3 tools/make_icons.py   (writes src/app/icon-*.png)"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "app")
ORANGE, WHITE, INK = (249, 99, 2), (255, 255, 255), (51, 51, 51)

def icon(size, maskable=False):
    S = 1024
    im = Image.new("RGB", (S, S), ORANGE)
    d = ImageDraw.Draw(im)
    k = 0.78 if maskable else 1.0          # keep art inside the maskable safe zone
    cx, cy = S / 2, S / 2
    def r(x0, y0, x1, y1):
        return [cx + (x0 - 512) * k, cy + (y0 - 512) * k, cx + (x1 - 512) * k, cy + (y1 - 512) * k]
    w = int(46 * k)
    d.rounded_rectangle(r(300, 150, 724, 874), radius=int(48 * k), outline=WHITE, width=w)
    d.line(r(300, 420, 724, 420)[:4], fill=WHITE, width=w)
    d.line(r(380, 240, 380, 340)[:4], fill=WHITE, width=w)
    d.line(r(380, 500, 380, 620)[:4], fill=WHITE, width=w)
    # check badge
    d.ellipse(r(560, 620, 820, 880), fill=WHITE)
    pts = [(615, 752), (670, 805), (765, 695)]
    d.line([(cx + (x - 512) * k, cy + (y - 512) * k) for x, y in pts], fill=ORANGE, width=int(40 * k), joint="curve")
    return im.resize((size, size), Image.LANCZOS)

os.makedirs(OUT, exist_ok=True)
icon(192).save(os.path.join(OUT, "icon-192.png"))
icon(512).save(os.path.join(OUT, "icon-512.png"))
icon(512, True).save(os.path.join(OUT, "icon-maskable-512.png"))
icon(180).save(os.path.join(OUT, "apple-touch-icon.png"))
print("icons written to src/app/")
