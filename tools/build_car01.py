# Build Spine 4.2 skeleton for car_01 (red muscle car, twin stripes, hood scoop). All motion = Spine keys on PNGs.
# usage: python3 build_car01.py <car_dir>       (images/ + layout.json from prep_car.py)
# Anims: idle (1.2s loop) · run (0.8s loop) · crash (2.6s one-shot) · wreck (2s loop, after crash)
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carlib as C
from carlib import bone, slot, region, put, center, W, k1, k2, eo1, eo2, ck, life, hexc, jitter, R, BW, bones, slots, att, anims

LY = C.setup(sys.argv[1])
Ly = LY["layers"]

# ---------------- bones ----------------
bone("car", "root", 0, 0)
bone("chassis", "car", 0, 0)
WB = {"wheel_front_L": "wheel_FL", "wheel_front_R": "wheel_FR", "wheel_rear_L": "wheel_RL", "wheel_rear_R": "wheel_RR"}
for n, b in WB.items(): bone(b, "car", *center(n))
bone("scoop", "chassis", *center("hood_scoop"))
bone("bumper_F", "chassis", *center("bumper_front"))
bone("bumper_R", "chassis", *center("bumper_rear"))
bone("mirror_L", "chassis", *center("mirror_L")); bone("mirror_R", "chassis", *center("mirror_R"))
# stripe shimmer: 2 clip rects (one per stripe) + 1 shine streak each
STR = [(713, 780), (828, 895)]; SY0, SY1 = 151, 1538
for i, (x0, x1) in enumerate(STR):
    bone(f"shine_{'LR'[i]}", "chassis", W((x0 + x1) / 2, SY0)[0], W(0, SY0)[1] + 40)
SC_ = center("hood_scoop")
for i in range(7): bone(f"smoke_{i + 1}", "car", SC_[0] + (-15, 20, -5, 25, -25, 10, 0)[i], SC_[1] + (0, 15, 30, -10, 20, 40, 10)[i])
rear_y = W(0, Ly["wheel_rear_L"][3])[1] + 10
for s_, n in (("L", "wheel_rear_L"), ("R", "wheel_rear_R")):
    for i in (1, 2): bone(f"dust_{s_}{i}", "car", center(n)[0], rear_y)
BR = Ly["bumper_rear"]; ex_y = W(0, BR[3])[1] + 6
for s_, px in (("L", BR[0] + 120), ("R", BR[2] - 120)):
    for i in (1, 2): bone(f"exsmoke_{s_}{i}", "car", W(px, 0)[0], ex_y)
FR = center("bumper_front")
bone("fire", "car", FR[0], FR[1] - 20)
debris = C.special_debris("car_01")
for i, (nm, kind) in enumerate(debris): bone("d_" + nm, "car", FR[0] + (i * 41 % 120 - 60), FR[1] - 30 - (i * 23 % 40))
for i in range(3): bone(f"spark_{i + 1}", "car", FR[0] + (-90, 80, 0)[i], FR[1] + 20, rotation=(140, 40, 90)[i])

# ---------------- slots (bottom → top) ----------------
slot("shadow", "car", "shadow"); sc = center("shadow"); put("shadow", "shadow", region("shadow", x=sc[0] + 8, y=sc[1] - 12))
for s_ in "LR":
    for i in (1, 2):
        slot(f"dust_{s_}{i}", f"dust_{s_}{i}", "smoke_round", color="c8a87a00"); put(f"dust_{s_}{i}", "smoke_round", region("smoke_round", scale=0.55))
PART = {"body": "chassis", "stripes": "chassis", "bumper_front": "bumper_F", "bumper_rear": "bumper_R", "glass_front": "chassis",
        "glass_rear": "chassis", "hood_scoop": "scoop", "mirror_L": "mirror_L", "mirror_R": "mirror_R", **WB}
for n in LY["order"]:
    bn = PART[n]; slot(n, bn, n); put(n, n, region(n, *center(n), b=bn))
    if n == "wheel_front_L": put(n, "wheel_loose", region("wheel_loose"))          # side-view wheel, used when it tears off
    if n == "stripes":
        for i, (x0, x1) in enumerate(STR):
            sd = "LR"[i]; (ax, ay), (bx, by) = W(x0, SY0), W(x1, SY1)
            slot(f"clip_{sd}", "chassis", f"clip_{sd}")
            put(f"clip_{sd}", f"clip_{sd}", {"type": "clipping", "end": f"shine_{sd}", "vertexCount": 4,
                                             "vertices": [ax, ay, bx, ay, bx, by, ax, by], "color": "ce3a3aff"})
            slot(f"shine_{sd}", f"shine_{sd}", "stripe_shine", blend="additive", color="ffffff00")
            put(f"shine_{sd}", "stripe_shine", region("stripe_shine", scale=1.6))
for s_ in "LR":
    for i in (1, 2):
        n = f"exsmoke_{s_}{i}"; slot(n, n, "smoke_round", color="bebec600"); put(n, "smoke_round", region("smoke_round", scale=0.3))
for nm, kind in debris: slot(nm, "d_" + nm); put(nm, kind, region(kind, scale=C.DSCALE[nm]))
for i in range(3): slot(f"spark_{i + 1}", f"spark_{i + 1}", blend="additive"); put(f"spark_{i + 1}", "spark_small", region("spark_small", rot=-45))
slot("fire_flash", "fire", "flame_glow", blend="additive", color="ffd27a00"); put("fire_flash", "flame_glow", region("flame_glow", scale=5.0))
slot("fire_puff", "fire", "explosion_main", color="ffffff00"); put("fire_puff", "explosion_main", region("explosion_main", scale=0.55))
for i in range(7):
    n = f"smoke_{i + 1}"; a = "smoke_soft" if i % 2 else "smoke_round"
    slot(n, n, a, color="55555a00"); put(n, a, region(a, scale=0.75))

# ---------------- IDLE 1.2s ----------------
P = 1.2
idle = {"bones": {}, "slots": {}}
sc = []
for i in range(4):                                   # rev pulse 1.00 → 1.04
    t0 = i * 0.3
    sc += [k2(t0, 1, 1, [R(t0 + .03), 1, R(t0 + .06), 1.04, R(t0 + .03), 1, R(t0 + .06), 1.04]), k2(t0 + 0.1, 1.04, 1.04)]
sc.append(k2(P, 1, 1))
idle["bones"]["scoop"] = {"scale": sc}
idle["bones"]["chassis"] = {"translate": [k2(t, v * .5, w * .5) for (t, v), (_, w) in zip(jitter(P, 0.1, 1, 3), jitter(P, 0.1, 1, 7))]}
for s_, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        m = f"exsmoke_{s_}{i}"; st = (i - 1) * 0.6 + (0.3 if s_ == "R" else 0)
        idle["bones"][m] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (1.1, (sx * 50, -110))], (sx * 50, -110))],
                            "scale": [k2(t, *v) for t, v in life(P, st, [(0, (0.6, 0.6)), (1.1, (2.0, 2.0))], (2, 2))]}
        idle["slots"][m] = {"rgba": [ck(t, hexc((190, 190, 198), v[0])) for t, v in life(P, st, [(0, (0,)), (0.15, (0.8,)), (0.5, (0.5,)), (1.1, (0,))], (0,))]}
anims["idle"] = idle

# ---------------- RUN 0.8s ----------------
P = 0.8
run = {"bones": {}, "slots": {}}
for i, sd in enumerate("LR"):                         # shimmer sweep front → rear once per loop
    st = 0.05 + i * 0.06; travel = W(0, SY1)[1] - W(0, SY0)[1] - 80
    run["bones"][f"shine_{sd}"] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (0.42, (0, travel))], (0, travel))]}
    run["slots"][f"shine_{sd}"] = {"rgba": [ck(t, hexc((255, 255, 255), v[0])) for t, v in life(P, st, [(0, (0,)), (0.05, (1.0,)), (0.34, (1.0,)), (0.42, (0,))], (0,))]}
run["bones"]["car"] = {"translate": [k2(R(i * 0.1), 0, (0, 1.2, 0, -1)[i % 4]) for i in range(9)]}
run["bones"]["scoop"] = {"scale": [k2(R(i * 0.1), *((1, 1) if i % 2 == 0 else (1.03, 1.03))) for i in range(9)]}
for b, sd in (("wheel_FL", 2), ("wheel_FR", 4)): run["bones"][b] = {"translate": [k2(t, v * .6, 0) for t, v in jitter(P, 0.08, 1, sd)]}
for s_, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        st = (i - 1) * 0.4 + (0.1 if s_ == "R" else 0); n = f"dust_{s_}{i}"
        run["bones"][n] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (0.55, (sx * 40, -140))], (sx * 40, -140))],
                           "scale": [k2(t, *v) for t, v in life(P, st, [(0, (0.3, 0.3)), (0.55, (1.2, 1.1))], (1.2, 1.1))]}
        run["slots"][n] = {"rgba": [ck(t, hexc((200, 168, 122), v[0])) for t, v in life(P, st, [(0, (0,)), (0.06, (0.8,)), (0.55, (0,))], (0,))]}
anims["run"] = run

# ---------------- CRASH 2.6s ----------------
P = 2.6
cr = {"bones": {}, "slots": {}}
cr["bones"]["car"] = {"translate": [k2(0, 0, 0), k2(.04, -10, -14), k2(.09, 7, -22), k2(.15, -4, -27), k2(.3, 0, -32, eo2(.3, (0, -32), .8, (0, -36))), k2(.8, 0, -36)],
                      "rotate": [k1(0, 0), k1(.05, 3), k1(.12, -3, eo1(.12, -3, .8, -7)), k1(.8, -7)]}
# hood scoop pops up + tilts: translate Y -10, rotate 20°, scale lift
cr["bones"]["scoop"] = {"translate": [k2(0, 0, 0), k2(.06, 0, 0, eo2(.06, (0, 0), .28, (0, -10))), k2(.28, 0, -10)],
                        "rotate": [k1(0, 0), k1(.06, 0, eo1(.06, 0, .28, 24)), k1(.28, 24), k1(.38, 18), k1(.48, 20)],
                        "scale": [k2(0, 1, 1), k2(.06, 1, 1), k2(.18, 1.22, 1.22), k2(.3, 1.08, 1.08), k2(.42, 1.12, 1.12)]}
# parts that fly: (bone, dx, dy, rot, t_end, hop)
SC = [("bumper_F", 20, 190, 28, 0.75, 1.25), ("mirror_L", -170, 60, -220, 0.7, 1.3), ("mirror_R", 160, 90, 260, 0.7, 1.3),
      ("wheel_FL", -280, 150, -420, 1.0, 1.35)]
rnd = random.Random(11)
for nm, kind in debris:
    ang = rnd.uniform(20, 160); dist = rnd.uniform(140, 300)
    SC.append(("d_" + nm, math.cos(math.radians(ang)) * dist, math.sin(math.radians(ang)) * dist, rnd.choice((-1, 1)) * rnd.uniform(200, 540), rnd.uniform(.55, .9), rnd.uniform(1.2, 1.45)))
for i, (b, dx, dy, rot, te, hop) in enumerate(SC):
    d0 = 0.02 * (i % 4)
    cr["bones"][b] = {"translate": [k2(0, 0, 0), k2(d0, 0, 0, eo2(d0, (0, 0), te, (dx, dy))), k2(te, dx, dy), k2(te + .12, dx * 1.03, dy * 1.03)],
                      "rotate": [k1(0, 0), k1(d0, 0, eo1(d0, 0, te + .12, rot)), k1(te + .12, rot)],
                      "scale": [k2(0, 1, 1), k2(d0 + (te - d0) * .4, hop, hop), k2(te, 1, 1), k2(te + .06, 1.05, 1.05), k2(te + .12, 1, 1)]}
# torn-off wheel flips flat mid-air → side-view wheel PNG
cr["slots"]["wheel_front_L"] = {"attachment": [{"name": "wheel_front_L"}, {"time": .22, "name": "wheel_loose"}]}
for nm, kind in debris: cr["slots"][nm] = {"attachment": [{"name": kind}], "rgba": [ck(0, "ffffff00"), ck(.07, "ffffffff")]}
for i in range(3):
    n = f"spark_{i + 1}"; t0 = .02 * i
    cr["slots"][n] = {"attachment": [{"name": "spark_small"}, {"time": .4, "name": None}],
                      "rgba": [ck(0, "ffffff00"), ck(t0, "ffffffff"), ck(t0 + .06, "ffffff66"), ck(t0 + .12, "ffffffff"), ck(.38, "ffffff00")]}
    cr["bones"][n] = {"scale": [k2(0, .4, .4), k2(t0 + .1, 1.2, 1.2), k2(.38, .8, .8)]}
cr["slots"]["fire_flash"] = {"rgba": [ck(0, "ffd27a00"), ck(.03, "ffe6a0ee"), ck(.12, "ffc060aa"), ck(.3, "ff904050"), ck(.5, "ff702000")]}
cr["slots"]["fire_puff"] = {"rgba": [ck(0, "ffffff00"), ck(.05, "ffffffdd"), ck(.12, "ffffffee"), ck(.35, "ffe0c0bb"), ck(.6, "c8a09060"), ck(.85, "a0908000")]}
cr["bones"]["fire"] = {"scale": [k2(0, .2, .2, eo2(0, (.2, .2), .25, (1, 1))), k2(.25, 1, 1, eo2(.25, (1, 1), .85, (1.3, 1.3))), k2(.85, 1.3, 1.3)]}
# smoke from the scoop (same gray as other cars)
for i in range(7):
    n = f"smoke_{i + 1}"; t0 = .12 + i * .11; te = min(P, t0 + 1.8)
    dx, dy = (-70, 50, -20, 90, -110, 30, 0)[i], (150, 200, 250, 130, 190, 280, 220)[i]
    cr["slots"][n] = {"rgba": [ck(0, "55555a00"), ck(t0, "55555a00"), ck(t0 + .22, "4a4a50dd"), ck(t0 + .9, "8a8a90aa"), ck(te, "b4b4ba00")]}
    cr["bones"][n] = {"translate": [k2(0, 0, 0), k2(t0, 0, 0, eo2(t0, (0, 0), te, (dx, dy))), k2(te, dx, dy)],
                      "scale": [k2(0, .3, .3), k2(t0, .3, .3, eo2(t0, (.3, .3), te, (2.3, 2.3))), k2(te, 2.3, 2.3)],
                      "rotate": [k1(0, 0), k1(te, (-40, 30, -20, 50, -30, 25, 10)[i])]}
orig = [s["name"] for s in slots]
lift = ["wheel_front_L", "bumper_front", "mirror_L", "mirror_R"]
rest = [s for s in orig if s not in lift]; at = rest.index("mirror_R" if "mirror_R" not in lift else "hood_scoop") + 1
new = rest[:at] + lift + rest[at:]
cr["drawOrder"] = [{"offsets": [{"slot": s, "offset": new.index(s) - orig.index(s)} for s in sorted(lift, key=orig.index) if new.index(s) != orig.index(s)]}]
anims["crash"] = cr

# ---------------- WRECK 2s loop ----------------
P = 2.0
wk = {"bones": {}, "slots": {}, "drawOrder": cr["drawOrder"]}
for b, dx, dy, rot, te, hop in SC: wk["bones"][b] = {"translate": [k2(0, dx * 1.03, dy * 1.03)], "rotate": [k1(0, rot)]}
wk["bones"]["car"] = {"translate": [k2(0, 0, -36)], "rotate": [k1(0, -7)]}
wk["bones"]["scoop"] = {"translate": [k2(0, 0, -10)], "rotate": [k1(0, 20)], "scale": [k2(0, 1.12, 1.12)]}
wk["slots"]["wheel_front_L"] = {"attachment": [{"name": "wheel_loose"}]}
for nm, kind in debris: wk["slots"][nm] = {"attachment": [{"name": kind}]}
for i in range(7):
    n = f"smoke_{i + 1}"; st = i * P / 7
    wk["bones"][n] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (1.7, ((-50, 40, -20, 60, -60, 30, 0)[i], 220))], (0, 220))],
                      "scale": [k2(t, *v) for t, v in life(P, st, [(0, (.35, .35)), (1.7, (1.7, 1.7))], (1.7, 1.7))]}
    wk["slots"][n] = {"rgba": [ck(t, hexc((110, 110, 118), v[0])) for t, v in life(P, st, [(0, (0,)), (.3, (.7,)), (1.7, (0,))], (0,))]}
anims["wreck"] = wk

for a in anims.values():
    for k in [k for k, v in a.items() if not v]: del a[k]
J = {"skeleton": {"hash": "car_01", "spine": "4.2.40", "x": -260, "y": -400, "width": 520, "height": 800, "images": "./images/", "audio": ""},
     "bones": [{"name": "root"}] + bones, "slots": slots, "skins": [{"name": "default", "attachments": att}], "animations": anims}
json.dump(J, open(os.path.join(C.D, "car.json"), "w"), indent=1)
print("bones", len(J["bones"]), "slots", len(slots), "anims", list(anims))
