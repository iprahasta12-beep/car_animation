# Extra PNGs for car_05: car_flash (white silhouette for the 1-frame impact flash) + fx_dent (front crumple overlay).
# usage: python3 fx_car05.py <car_dir>      (run after prep_car.py; also run fx_car04.py <car_dir>/images for cracked headlights)
import sys, os, json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
D = sys.argv[1]; IMG = os.path.join(D, "images"); LP = os.path.join(D, "layout.json")
L = json.load(open(LP)); S = L["scale"]
names = [n for n in L["order"]]
x0 = min(L["layers"][n][0] for n in names); y0 = min(L["layers"][n][1] for n in names)
x1 = max(L["layers"][n][2] for n in names); y1 = max(L["layers"][n][3] for n in names)
W, H = round((x1 - x0) * S) + 2, round((y1 - y0) * S) + 2
sil = Image.new("L", (W, H), 0)
for n in names:
    im = Image.open(os.path.join(IMG, n + ".png")).convert("RGBA")
    sil.paste(255, (round((L["layers"][n][0] - x0) * S), round((L["layers"][n][1] - y0) * S)), im.getchannel("A"))
Image.merge("RGBA", (Image.new("L", (W, H), 255),) * 3 + (sil,)).save(os.path.join(IMG, "car_flash.png"))
L["layers"]["car_flash"] = [x0, y0, x0 + W / S, y0 + H / S]
# dent overlay across the front (bumper + hood edge)
bf = L["layers"]["bumper_front"]; dw, dh = round((bf[2] - bf[0]) * S), 110
rnd = random.Random(5)
dent = Image.new("RGBA", (dw, dh), (0, 0, 0, 0)); dr = ImageDraw.Draw(dent)
shade = Image.new("L", (dw, dh), 0); ds = ImageDraw.Draw(shade)
for i in range(5):                                       # dark crumple blotches
    cx, cy = rnd.uniform(.15, .85) * dw, rnd.uniform(.25, .7) * dh; r = rnd.uniform(18, 34)
    ds.ellipse((cx - r * 1.4, cy - r, cx + r * 1.4, cy + r), fill=90)
shade = shade.filter(ImageFilter.GaussianBlur(10))
dent.putalpha(shade)
for i in range(9):                                       # crease lines: dark + highlight
    xa = rnd.uniform(.08, .92) * dw; ya = rnd.uniform(.1, .45) * dh
    pts = [(xa, ya)]
    for s in range(3): pts.append((pts[-1][0] + rnd.uniform(-22, 22), pts[-1][1] + rnd.uniform(10, 22)))
    dr.line(pts, fill=(20, 10, 30, 210), width=3)
    dr.line([(p[0] + 2, p[1] - 1) for p in pts], fill=(255, 240, 255, 150), width=1)
dent.save(os.path.join(IMG, "fx_dent.png"))
L["layers"]["fx_dent"] = [bf[0], bf[1] + 40, bf[0] + dw / S, bf[1] + 40 + dh / S]
json.dump(L, open(LP, "w"), indent=1)
print("car_flash", (W, H), "fx_dent", (dw, dh))
