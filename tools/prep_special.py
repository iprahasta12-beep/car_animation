# Prep art for car "special" (white hot rod) from special.psd + fx source PNGs.
# usage: python3 prep_special.py <special.psd> <fx_src_dir> <out_images_dir> <out_layout.json>
#   fx_src_dir must hold: cloud_round.png, cloud_soft.png, cloud_wisps.png,
#                         explosion_main.png, bolt.png, shard.png, debris_round.png, spark_small.png
# Output: trimmed PNGs at SCALE of PSD + layout.json (PSD-pixel bbox per layer) used by build_special.py
import sys, os, json, math
import numpy as np
from PIL import Image, ImageFilter
from psd_tools import PSDImage

psd_path, fx_dir, out_dir, layout_path = sys.argv[1:5]
SCALE = 0.5
os.makedirs(out_dir, exist_ok=True)
psd = PSDImage.open(psd_path)
layout = {"psd_size": list(psd.size), "scale": SCALE, "layers": {}}

def save(im, name):
    im.save(os.path.join(out_dir, name + ".png"), optimize=True)

def half(im):
    return im.resize((max(1, round(im.width * SCALE)), max(1, round(im.height * SCALE))), Image.LANCZOS)

# ---------- car layers ----------
union = None
for l in psd:
    if l.kind != "smartobject" or not l.visible:
        continue
    im = l.composite().convert("RGBA")
    bb = im.getbbox()
    im = im.crop(bb)
    L, T = l.bbox[0] + bb[0], l.bbox[1] + bb[1]
    layout["layers"][l.name] = [L, T, L + im.width, T + im.height]
    save(half(im), l.name)
    if union is None:
        union = Image.new("RGBA", psd.size, (0, 0, 0, 0))
    union.alpha_composite(im, (L, T))
    print("layer", l.name, layout["layers"][l.name])
layout["order"] = [l.name for l in psd if l.kind == "smartobject" and l.visible]

# shadow: blurred silhouette
a = union.getchannel("A").point(lambda v: 255 if v > 20 else 0)
bb = a.getbbox(); pad = 60
a = a.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)).filter(ImageFilter.GaussianBlur(22))
sh = Image.new("RGBA", a.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * 0.55)))
sh = Image.merge("RGBA", (Image.new("L", a.size, 10), Image.new("L", a.size, 12), Image.new("L", a.size, 20), sh.getchannel("A")))
layout["layers"]["shadow"] = [bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad]
save(half(sh), "shadow")
thumb = union.crop(union.getbbox()); thumb.thumbnail((220, 220), Image.LANCZOS); thumb.save(os.path.join(os.path.dirname(layout_path), "thumb.png"))

# ---------- rear tire tread sequence (4 frames, tread rolls toward front = up) ----------
FR = 4
for side in ("L", "R"):
    name = "wheel_rear_" + side
    src = np.asarray(Image.open(os.path.join(out_dir, name + ".png")).convert("RGBA")).astype(np.float32)
    H, W = src.shape[:2]
    rows = src[..., 3].mean(1) > 200
    y0, y1 = np.where(rows)[0][[0, -1]]
    per = 99 * SCALE                                    # tread period measured on PSD (autocorrelation)
    ym = (y0 + y1) // 2
    tile = src[int(ym - per / 2): int(ym - per / 2) + int(round(per))].copy()   # one tread period
    P = tile.shape[0]
    alpha = Image.fromarray(src[..., 3].astype(np.uint8))
    inner = alpha.filter(ImageFilter.MinFilter(11)).filter(ImageFilter.GaussianBlur(3))
    m = np.asarray(inner).astype(np.float32)[..., None] / 255.0
    # shading of original rows (end caps darker) vs tile mean
    lum = src[..., :3].mean(2); tl = tile[..., :3].mean()
    shade = np.clip(np.array([lum[y][src[y, :, 3] > 200].mean() if (src[y, :, 3] > 200).any() else tl for y in range(H)]) / tl, 0.35, 1.15)
    shade = np.convolve(shade, np.ones(15) / 15, mode="same")[:, None, None]
    for f in range(FR):
        off = f * P / FR
        idx = (np.arange(H) + off).astype(int) % P
        tex = tile[idx][:, :W]
        tex = tex[..., :3] * shade
        out = src.copy()
        out[..., :3] = src[..., :3] * (1 - m) + tex * m
        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(out_dir, f"{name}_{f + 1}.png"), optimize=True)
    os.remove(os.path.join(out_dir, name + ".png"))

# ---------- flame sequence (6 frames). base at top, tip pointing down ----------
rng = np.random.default_rng(7)
FW, FH = 64, 150
yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
v = yy / FH; u = (xx - FW / 2) / (FW / 2)
for f in range(6):
    ph = f / 6 * 2 * math.pi
    wob = 0.12 * np.sin(v * 9 + ph) + 0.06 * np.sin(v * 23 - ph * 2)
    length = 0.82 + 0.16 * math.sin(ph + 1.3)
    t = np.clip(v / length, 0, 1)
    rad = (0.55 + 0.45 * np.sin(np.clip(t, 0, 1) * math.pi * 0.5 + 0.35)) * (1 - t) ** 0.9 * 0.95 + 0.02
    rad = rad * (0.85 + 0.25 * np.sin(t * 6 + ph * 1.7)) * 1.55
    d = np.abs(u - wob * t) / np.maximum(rad, 1e-3)
    inside = np.clip(1 - d, 0, 1)
    a = np.clip(inside * 2.2, 0, 1) * np.clip((length - v) / 0.25, 0, 1) * np.clip(v / 0.04, 0, 1)
    core = np.clip(inside * 1.6 - t * 0.9, 0, 1)
    r = 255 * np.ones_like(a)
    g = 70 + 185 * core
    b = 20 + 200 * np.clip(core * 1.4 - 0.6, 0, 1)
    img = np.dstack([r, g, b, a * 255]).astype(np.uint8)
    Image.fromarray(img).filter(ImageFilter.GaussianBlur(0.8)).save(os.path.join(out_dir, f"flame_{f + 1}.png"))
# additive glow
G = 96; gy, gx = np.mgrid[0:G, 0:G].astype(np.float32)
d = np.hypot(gx - G / 2, gy - G / 2) / (G / 2)
ga = np.clip(1 - d, 0, 1) ** 2
Image.fromarray(np.dstack([np.full_like(ga, 255), np.full_like(ga, 140), np.full_like(ga, 40), ga * 255]).astype(np.uint8)).save(os.path.join(out_dir, "flame_glow.png"))

# ---------- smoke / dust (neutral white so slot tint sets color) ----------
def neutral(src, name, size):
    im = Image.open(os.path.join(fx_dir, src)).convert("RGBA")
    im = im.crop(im.getbbox()); im.thumbnail((size, size), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32)
    lum = arr[..., :3].mean(2)
    lum = 175 + (lum - lum[arr[..., 3] > 30].min()) / max(1, (lum.max() - lum[arr[..., 3] > 30].min())) * 80
    out = np.dstack([lum, lum, lum, arr[..., 3]])
    save(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), name)
neutral("cloud_round.png", "smoke_round", 220)
neutral("cloud_soft.png", "smoke_soft", 220)
neutral("cloud_wisps.png", "smoke_wisps", 200)

# ---------- reused crash fx ----------
for n, sz in (("explosion_main", 520), ("bolt", 44), ("shard", 60), ("debris_round", 60), ("spark_small", 90)):
    im = Image.open(os.path.join(fx_dir, n + ".png")).convert("RGBA"); im = im.crop(im.getbbox()); im.thumbnail((sz, sz), Image.LANCZOS)
    save(im, n)

json.dump(layout, open(layout_path, "w"), indent=1)
print("done")
