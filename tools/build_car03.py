# Build Spine 4.2 skeleton for car_03 (teal pickup, cream cab, spare tire in bed). All motion = Spine keys on PNGs.
# usage: python3 build_car03.py <car_dir>       (images/ + layout.json from prep_car.py)
# Anims: idle (1.2s loop) · run (0.8s loop) · crash (2.6s one-shot) · wreck (2s loop, after crash)
# Smoke / explosion / spark / bolt / shard PNGs reused from car_special. Tailgate = mesh (deform).
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carlib as C
from carlib import bone, slot, region, put, center, W, k1, k2, eo1, eo2, ck, life, hexc, jitter, R, BW, bones, slots, att, anims, size

LY = C.setup(sys.argv[1])
Ly = LY["layers"]

def grid_mesh(img, bname, cols=6, rows=3):
    """Unweighted grid mesh, hull first. Returns attachment; vertex order kept in MESH[img] = [(c, r)]."""
    tw, th = size(img); cx, cy = center(img); ox, oy = cx - BW[bname][0], cy - BW[bname][1]
    grid = [(c, r) for r in range(rows + 1) for c in range(cols + 1)]
    hull = [(c, 0) for c in range(cols + 1)] + [(cols, r) for r in range(1, rows + 1)] + \
           [(c, rows) for c in range(cols - 1, -1, -1)] + [(0, r) for r in range(rows - 1, 0, -1)]
    order = hull + [g for g in grid if g not in hull]; ix = {g: i for i, g in enumerate(order)}
    uvs, verts, tris = [], [], []
    for c, r in order:
        u, v = c / cols, r / rows; uvs += [R(u), R(v)]; verts += [R(ox + (u - .5) * tw), R(oy + (.5 - v) * th)]
    for r in range(rows):
        for c in range(cols):
            a, b, c2, d = ix[(c, r)], ix[(c + 1, r)], ix[(c, r + 1)], ix[(c + 1, r + 1)]
            tris += [a, b, d, a, d, c2]
    MESH[img] = (order, cols, rows, th)
    return {"type": "mesh", "uvs": uvs, "triangles": tris, "vertices": verts, "hull": len(hull), "width": tw, "height": th}
MESH = {}

# ---------------- bones ----------------
bone("car", "root", 0, 0)
bone("chassis", "car", 0, 0)
WB = {"wheel_front_L": "wheel_FL", "wheel_front_R": "wheel_FR", "wheel_back_L": "wheel_RL", "wheel_back_R": "wheel_RR"}
for n, b in WB.items(): bone(b, "car", *center(n))
bone("hood", "chassis", *center("hood"))
bone("bumper_F", "chassis", *center("bumper_front"))
bone("bumper_R", "chassis", *center("bumper_rear"))
bone("mirror_L", "chassis", *center("mirror_L")); bone("mirror_R", "chassis", *center("mirror_R"))
bone("spare", "chassis", *center("spare_tire"))
TG = Ly["tailgate"]; bone("tailgate", "chassis", *W((TG[0] + TG[2]) / 2, TG[3]))     # hinge = rear edge
HC = center("hood")
for i in range(6): bone(f"smoke_{i + 1}", "car", HC[0] + (-30, 25, -5, 35, -40, 10)[i], HC[1] + (0, 15, 35, -10, 25, 45)[i])
rear_y = W(0, Ly["wheel_back_L"][3])[1] + 10
for s_, n in (("L", "wheel_back_L"), ("R", "wheel_back_R")):
    for i in (1, 2, 3): bone(f"dust_{s_}{i}", "car", center(n)[0], rear_y)
FR = center("bumper_front")
bone("fire", "car", FR[0], FR[1] - 25)
debris = C.special_debris("car_03")
for i, (nm, kind) in enumerate(debris): bone("d_" + nm, "car", FR[0] + (i * 41 % 120 - 60), FR[1] - 30 - (i * 23 % 40))
for i in range(3): bone(f"spark_{i + 1}", "car", FR[0] + (-90, 80, 0)[i], FR[1] + 20, rotation=(140, 40, 90)[i])

# ---------------- slots (bottom → top) ----------------
slot("shadow", "car", "shadow"); sc = center("shadow"); put("shadow", "shadow", region("shadow", x=sc[0] + 8, y=sc[1] - 12))
for s_ in "LR":
    for i in (1, 2, 3):
        n = f"dust_{s_}{i}"; slot(n, n, "smoke_round", color="c8a87a00"); put(n, "smoke_round", region("smoke_round", scale=0.6))
PART = {"body": "chassis", "hood": "hood", "bumper_front": "bumper_F", "bumper_rear": "bumper_R", "cab_roof": "chassis",
        "mirror_L": "mirror_L", "mirror_R": "mirror_R", "spare_tire": "spare", "tailgate": "tailgate", **WB}
for n in LY["order"]:
    bn = PART[n]; slot(n, bn, n)
    put(n, n, grid_mesh(n, bn) if n == "tailgate" else region(n, *center(n), b=bn))
for nm, kind in debris: slot(nm, "d_" + nm); put(nm, kind, region(kind, scale=C.DSCALE[nm]))
for i in range(3): slot(f"spark_{i + 1}", f"spark_{i + 1}", blend="additive"); put(f"spark_{i + 1}", "spark_small", region("spark_small", rot=-45))
slot("fire_flash", "fire", "flame_glow", blend="additive", color="ffd27a00"); put("fire_flash", "flame_glow", region("flame_glow", scale=5.0))
slot("fire_puff", "fire", "explosion_main", color="ffffff00"); put("fire_puff", "explosion_main", region("explosion_main", scale=0.6))
for i in range(6):
    n = f"smoke_{i + 1}"; a = "smoke_soft" if i % 2 else "smoke_round"
    slot(n, n, a, color="55555a00"); put(n, a, region(a, scale=0.75))

def dust(anim, P, starts, life_t, drift, peak, scl):
    for s_, sx in (("L", -1), ("R", 1)):
        for i, st0 in enumerate(starts):
            st = st0 + (0.07 if s_ == "R" else 0); n = f"dust_{s_}{i + 1}"; dx, dy = drift
            anim["bones"][n] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (life_t, (sx * dx, dy))], (sx * dx, dy))],
                                "scale": [k2(t, *v) for t, v in life(P, st, [(0, (scl[0], scl[0])), (life_t, (scl[1], scl[1] * .9))], (scl[1], scl[1] * .9))],
                                "rotate": [k1(0, i * 60), k1(P, i * 60 + sx * 50)]}
            anim["slots"][n] = {"rgba": [ck(t, hexc((200, 168, 122), v[0])) for t, v in life(P, st, [(0, (0,)), (0.07, (peak,)), (life_t, (0,))], (0,))]}

# ---------------- IDLE 1.2s: spare tire bounces in bed (translate Y ±2) ----------------
P = 1.2
idle = {"bones": {}, "slots": {}}
sp = []
for i in range(4):
    t0 = i * .3
    sp += [k2(t0, 0, 2, [R(t0 + .06), 2, R(t0 + .12), -2, R(t0 + .06), 2, R(t0 + .12), -2]), k2(t0 + .15, 0, -2, [R(t0 + .2), -2, R(t0 + .26), 2, R(t0 + .2), -2, R(t0 + .26), 2])]
sp.append(k2(P, 0, 2))
idle["bones"]["spare"] = {"translate": sp}
idle["bones"]["chassis"] = {"translate": [k2(t, v * .5, w * .5) for (t, v), (_, w) in zip(jitter(P, 0.1, 1, 3), jitter(P, 0.1, 1, 7))]}
anims["idle"] = idle

# ---------------- RUN 0.8s: spare jiggles harder + dust puffs behind (no exhaust) ----------------
P = 0.8
run = {"bones": {}, "slots": {}}
jx, jy, jr = jitter(P, 0.05, 2.5, 5), jitter(P, 0.05, 5.5, 9), jitter(P, 0.05, 4, 13)
run["bones"]["spare"] = {"translate": [k2(t, x, y) for (t, x), (_, y) in zip(jx, jy)], "rotate": [k1(t, v) for t, v in jr],
                         "scale": [k2(R(i * .1), *((1, 1) if i % 2 == 0 else (1.03, 1.03))) for i in range(9)]}
run["bones"]["car"] = {"translate": [k2(t, v * .8, w * 1.6) for (t, v), (_, w) in zip(jitter(P, 0.08, 1, 21), jitter(P, 0.08, 1, 23))],
                       "rotate": [k1(t, v * .6) for t, v in jitter(P, 0.1, 1, 29)]}
run["bones"]["tailgate"] = {"translate": [k2(t, 0, v) for t, v in jitter(P, 0.08, 1.2, 31)]}
for b, sd in (("wheel_FL", 2), ("wheel_FR", 4)): run["bones"][b] = {"translate": [k2(t, v * .8, 0) for t, v in jitter(P, 0.08, 1, sd)]}
dust(run, P, (0, .27, .54), .62, (60, -190), .9, (.35, 1.6))
anims["run"] = run

# ---------------- CRASH 2.6s ----------------
P = 2.6
cr = {"bones": {}, "slots": {}, "attachments": {"default": {}}}
cr["bones"]["car"] = {"translate": [k2(0, 0, 0), k2(.04, -10, -14), k2(.09, 7, -22), k2(.15, -4, -27), k2(.3, 0, -32, eo2(.3, (0, -32), .8, (0, -36))), k2(.8, 0, -36)],
                      "rotate": [k1(0, 0), k1(.05, 3), k1(.12, -3, eo1(.12, -3, .8, -6)), k1(.8, -6)]}
# spare tire launches out of the bed (hop), lands behind the truck, bounces, rolls a little and lies on the ground
cr["bones"]["spare"] = {
    "translate": [k2(0, 0, 0), k2(.06, 0, 8), k2(.1, 0, 8, eo2(.1, (0, 8), .55, (45, -250))), k2(.55, 45, -250), k2(.68, 55, -275),
                  k2(.8, 62, -292, eo2(.8, (62, -292), 1.3, (70, -315))), k2(1.3, 70, -315)],
    "rotate": [k1(0, 0), k1(.1, 0), k1(.55, -300), k1(.8, -420, eo1(.8, -420, 1.3, -540)), k1(1.3, -540)],
    "scale": [k2(0, 1, 1), k2(.1, 1.05, 1.05), k2(.32, 1.45, 1.45), k2(.55, 1, 1), k2(.6, 1.12, 1.12), k2(.68, 1, 1), k2(.74, 1.04, 1.04), k2(.8, 1, 1)]}
# tailgate deforms open (mesh): bed-side edge swings back past the hinge, twisted + bent
order, cols, rows, th = MESH["tailgate"]
def gate(k):
    off = []
    for c, r in order:
        u, v = c / cols, r / rows; f = 1 - v                      # 1 at bed edge, 0 at hinge
        twist = 1 + 0.35 * (u - .5) * 2                           # right side opens further
        off += [R(k * f * math.sin(u * math.pi) * 8 * (1 - u)), R(-k * f * th * 1.55 * twist - k * 10 * math.sin(u * math.pi) * f)]
    return off
cr["attachments"]["default"]["tailgate"] = {"tailgate": {"deform": [{"vertices": gate(0)}, {"time": .08, "vertices": gate(0)},
                                                                     {"time": .2, "vertices": gate(1.15)}, {"time": .3, "vertices": gate(.88)},
                                                                     {"time": .4, "vertices": gate(1.02)}, {"time": .5, "vertices": gate(1.0)}]}}
cr["bones"]["tailgate"] = {"rotate": [k1(0, 0), k1(.2, -4), k1(.5, -3)]}
cr["bones"]["hood"] = {"translate": [k2(0, 0, 0), k2(.1, 0, -10), k2(.25, 3, -8)], "rotate": [k1(0, 0), k1(.1, 4), k1(.25, 3)],
                       "scale": [k2(0, 1, 1), k2(.1, 1.02, .95), k2(.25, 1.01, .96)]}
SC = [("mirror_L", -160, 40, -200, .7, 1.3), ("mirror_R", 150, 70, 240, .7, 1.3)]
rnd = random.Random(31)
for nm, kind in debris:
    ang = rnd.uniform(20, 160); dist = rnd.uniform(140, 280)
    SC.append(("d_" + nm, math.cos(math.radians(ang)) * dist, math.sin(math.radians(ang)) * dist, rnd.choice((-1, 1)) * rnd.uniform(200, 540), rnd.uniform(.55, .9), rnd.uniform(1.2, 1.45)))
for i, (b, dx, dy, rot, te, hop) in enumerate(SC):
    d0 = 0.02 * (i % 4)
    cr["bones"][b] = {"translate": [k2(0, 0, 0), k2(d0, 0, 0, eo2(d0, (0, 0), te, (dx, dy))), k2(te, dx, dy), k2(te + .12, dx * 1.03, dy * 1.03)],
                      "rotate": [k1(0, 0), k1(d0, 0, eo1(d0, 0, te + .12, rot)), k1(te + .12, rot)],
                      "scale": [k2(0, 1, 1), k2(d0 + (te - d0) * .4, hop, hop), k2(te, 1, 1), k2(te + .06, 1.05, 1.05), k2(te + .12, 1, 1)]}
for nm, kind in debris: cr["slots"][nm] = {"attachment": [{"name": kind}], "rgba": [ck(0, "ffffff00"), ck(.07, "ffffffff")]}
for i in range(3):
    s = f"spark_{i + 1}"; t0 = .02 * i
    cr["slots"][s] = {"attachment": [{"name": "spark_small"}, {"time": .4, "name": None}],
                      "rgba": [ck(0, "ffffff00"), ck(t0, "ffffffff"), ck(t0 + .06, "ffffff66"), ck(t0 + .12, "ffffffff"), ck(.38, "ffffff00")]}
    cr["bones"][s] = {"scale": [k2(0, .4, .4), k2(t0 + .1, 1.2, 1.2), k2(.38, .8, .8)]}
cr["slots"]["fire_flash"] = {"rgba": [ck(0, "ffd27a00"), ck(.03, "ffe6a0ee"), ck(.12, "ffc060aa"), ck(.3, "ff904050"), ck(.5, "ff702000")]}
cr["slots"]["fire_puff"] = {"rgba": [ck(0, "ffffff00"), ck(.05, "ffffffdd"), ck(.12, "ffffffee"), ck(.35, "ffe0c0bb"), ck(.6, "c8a09060"), ck(.85, "a0908000")]}
cr["bones"]["fire"] = {"scale": [k2(0, .2, .2, eo2(0, (.2, .2), .25, (1, 1))), k2(.25, 1, 1, eo2(.25, (1, 1), .85, (1.3, 1.3))), k2(.85, 1.3, 1.3)]}
for i in range(6):
    s = f"smoke_{i + 1}"; t0 = .25 + i * .12; te = min(P, t0 + 1.8)
    dx, dy = (-70, 50, -20, 90, -110, 30)[i], (150, 200, 250, 130, 190, 280)[i]
    cr["slots"][s] = {"rgba": [ck(0, "55555a00"), ck(t0, "55555a00"), ck(t0 + .22, "4a4a50dd"), ck(t0 + .9, "8a8a90aa"), ck(te, "b4b4ba00")]}
    cr["bones"][s] = {"translate": [k2(0, 0, 0), k2(t0, 0, 0, eo2(t0, (0, 0), te, (dx, dy))), k2(te, dx, dy)],
                      "scale": [k2(0, .3, .3), k2(t0, .3, .3, eo2(t0, (.3, .3), te, (2.1, 2.1))), k2(te, 2.1, 2.1)],
                      "rotate": [k1(0, 0), k1(te, (-40, 30, -20, 50, -30, 25)[i])]}
dust(cr, P, (0.02, 0.06, 0.1), 1.0, (90, -120), .8, (.4, 2.0))       # one dust burst on impact
orig = [s["name"] for s in slots]
lift = ["spare_tire", "mirror_L", "mirror_R"]
rest = [s for s in orig if s not in lift]; at = rest.index("tailgate") + 1
new = rest[:at] + lift + rest[at:]
cr["drawOrder"] = [{"offsets": [{"slot": s, "offset": new.index(s) - orig.index(s)} for s in sorted(lift, key=orig.index) if new.index(s) != orig.index(s)]}]
anims["crash"] = cr

# ---------------- WRECK 2s loop ----------------
P = 2.0
wk = {"bones": {}, "slots": {}, "attachments": {"default": {}}, "drawOrder": cr["drawOrder"]}
for b, dx, dy, rot, te, hop in SC: wk["bones"][b] = {"translate": [k2(0, dx * 1.03, dy * 1.03)], "rotate": [k1(0, rot)]}
for b in ("car", "tailgate", "hood", "spare"):
    wk["bones"][b] = {k: [{kk: vv for kk, vv in v[-1].items() if kk not in ("time", "curve")}] for k, v in cr["bones"][b].items()}
wk["attachments"]["default"]["tailgate"] = {"tailgate": {"deform": [{"vertices": gate(1.0)}]}}
for nm, kind in debris: wk["slots"][nm] = {"attachment": [{"name": kind}]}
for i in range(6):
    s = f"smoke_{i + 1}"; st = i * P / 6
    wk["bones"][s] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (1.6, ((-50, 40, -20, 60, -60, 30)[i], 200))], (0, 200))],
                      "scale": [k2(t, *v) for t, v in life(P, st, [(0, (.3, .3)), (1.6, (1.4, 1.4))], (1.4, 1.4))]}
    wk["slots"][s] = {"rgba": [ck(t, hexc((110, 110, 118), v[0])) for t, v in life(P, st, [(0, (0,)), (.3, (.7,)), (1.6, (0,))], (0,))]}
anims["wreck"] = wk

for a in anims.values():
    for k in [k for k, v in a.items() if not v]: del a[k]
J = {"skeleton": {"hash": "car_03", "spine": "4.2.40", "x": -260, "y": -400, "width": 520, "height": 800, "images": "./images/", "audio": ""},
     "bones": [{"name": "root"}] + bones, "slots": slots, "skins": [{"name": "default", "attachments": att}], "animations": anims}
json.dump(J, open(os.path.join(C.D, "car.json"), "w"), indent=1)
print("bones", len(J["bones"]), "slots", len(slots), "anims", list(anims))
