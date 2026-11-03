# Extra PNGs for car_04: light_glow (white radial, tint per slot) + cracked headlights.
# usage: python3 fx_car04.py <images_dir>
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
D = sys.argv[1]
G = 128; y, x = np.mgrid[0:G, 0:G].astype(float); d = np.hypot(x - G / 2, y - G / 2) / (G / 2)
a = np.clip(1 - d, 0, 1) ** 1.8
Image.fromarray(np.dstack([np.full_like(a, 255)] * 3 + [a * 255]).astype(np.uint8)).save(os.path.join(D, "light_glow.png"))
for side, seed in (("L", 3), ("R", 8)):
    im = Image.open(os.path.join(D, f"headlight_{side}.png")).convert("RGBA")
    w, h = im.size; rnd = random.Random(seed)
    base = Image.blend(im, Image.new("RGBA", im.size, (90, 100, 115, 255)), 0.25); base.putalpha(im.getchannel("A"))
    cr = Image.new("RGBA", im.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(cr)
    cx, cy = w * rnd.uniform(.4, .6), h * rnd.uniform(.4, .6)
    for k in range(7):                                         # radial cracks with kinks
        ang = k / 7 * 2 * math.pi + rnd.uniform(-.3, .3); px, py = cx, cy; pts = [(px, py)]
        for s in range(3):
            ang += rnd.uniform(-.5, .5); L = rnd.uniform(.12, .22) * max(w, h)
            px += math.cos(ang) * L; py += math.sin(ang) * L; pts.append((px, py))
        dr.line(pts, fill=(25, 30, 40, 235), width=2)
        dr.line([(p[0] + 1, p[1] + 1) for p in pts], fill=(255, 255, 255, 120), width=1)
    for r in (6, 11):                                          # impact rings
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(25, 30, 40, 200), width=1)
    cr.putalpha(Image.fromarray(np.minimum(np.asarray(cr.getchannel("A")), np.asarray(im.getchannel("A")))))
    out = Image.alpha_composite(base, cr); out.save(os.path.join(D, f"headlight_{side}_cracked.png"))
print("ok")
