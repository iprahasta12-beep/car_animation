# Generic car art prep: PSD smart-object layers -> trimmed PNGs at SCALE + shadow + thumb + layout.json
# usage: python3 prep_car.py <car.psd> <out_images_dir> <out_layout.json> [extra.png=name:size ...]
#   extra args copy+resize extra PNGs into images/, e.g.  wheel.png=wheel_loose:150
import sys, os, json
from PIL import Image, ImageFilter
from psd_tools import PSDImage

psd_path, out_dir, layout_path = sys.argv[1:4]
extras = sys.argv[4:]
SCALE = 0.5
os.makedirs(out_dir, exist_ok=True)
psd = PSDImage.open(psd_path)
L = {"psd_size": list(psd.size), "scale": SCALE, "layers": {}, "order": []}
half = lambda im: im.resize((max(1, round(im.width * SCALE)), max(1, round(im.height * SCALE))), Image.LANCZOS)
union = Image.new("RGBA", psd.size, (0, 0, 0, 0))
for l in psd:
    if l.kind != "smartobject" or not l.visible:
        continue
    name = l.name.replace(" copy", "_copy").replace(" ", "_")
    if name == "mirror_L_copy": name = "mirror_R"
    im = l.composite().convert("RGBA")
    bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    im = im.crop(bb)
    x0, y0 = l.bbox[0] + bb[0], l.bbox[1] + bb[1]
    L["layers"][name] = [x0, y0, x0 + im.width, y0 + im.height]
    L["order"].append(name)
    half(im).save(os.path.join(out_dir, name + ".png"), optimize=True)
    union.alpha_composite(im, (x0, y0))
    print("layer", name, L["layers"][name])
a = union.getchannel("A").point(lambda v: 255 if v > 20 else 0)
bb = a.getbbox(); pad = 60
a = a.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)).filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.55))
sh = Image.merge("RGBA", (Image.new("L", a.size, 10), Image.new("L", a.size, 12), Image.new("L", a.size, 20), a))
L["layers"]["shadow"] = [bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad]
half(sh).save(os.path.join(out_dir, "shadow.png"), optimize=True)
th = union.crop(union.getbbox()); th.thumbnail((220, 220), Image.LANCZOS); th.save(os.path.join(os.path.dirname(layout_path), "thumb.png"))
for e in extras:
    src, spec = e.split("="); n, sz = spec.split(":")
    im = Image.open(src).convert("RGBA"); im = im.crop(im.getbbox()); im.thumbnail((int(sz), int(sz)), Image.LANCZOS)
    im.save(os.path.join(out_dir, n + ".png"), optimize=True); print("extra", n, im.size)
json.dump(L, open(layout_path, "w"), indent=1)
