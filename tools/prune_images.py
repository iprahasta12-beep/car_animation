# Remove PNGs in <car_dir>/images that car.json never references (regions, meshes, sequence frames).
# usage: python3 prune_images.py <car_dir> [--dry]
import sys, os, json
d = sys.argv[1]; dry = "--dry" in sys.argv
J = json.load(open(os.path.join(d, "car.json")))
used = set()
for skin in J["skins"]:
    for slot, atts in skin["attachments"].items():
        for name, a in atts.items():
            if a.get("type", "region") not in ("region", "mesh", "linkedmesh"): continue
            p = a.get("path", name); seq = a.get("sequence")
            if seq:
                for i in range(seq["count"]): used.add(p + str(seq.get("start", 1) + i).zfill(seq.get("digits", 0)))
            else: used.add(p)
img = os.path.join(d, "images"); removed = []
for f in sorted(os.listdir(img)):
    if f.endswith(".png") and f[:-4] not in used:
        removed.append(f)
        if not dry: os.remove(os.path.join(img, f))
missing = sorted(u for u in used if not os.path.isfile(os.path.join(img, u + ".png")))
print(os.path.basename(d.rstrip("/")), "removed:", removed or "-", "| missing:", missing or "-")
