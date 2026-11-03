# Build Spine 4.2 skeleton for car_04 (yellow compact, round & cute). All motion = Spine keys on PNGs.
# usage: python3 build_car04.py <car_dir>   (images/ + layout.json from prep_car.py, light_glow + *_cracked from fx_car04.py)
# Anims: idle (1.2s loop) · run (0.8s loop) · crash (2.6s one-shot) · wreck (2s loop, after crash)
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carlib as C
from carlib import bone, slot, region, put, center, W, k1, k2, eo1, eo2, ck, life, hexc, jitter, R, BW, bones, slots, att, anims

LY = C.setup(sys.argv[1])
Ly = LY["layers"]
F = 1 / 30                                            # one frame @30fps

# ---------------- bones ----------------
bone("car", "root", 0, 0)
WB = {"wheel_front_L": "wheel_FL", "wheel_front_R": "wheel_FR", "wheel_rear_L": "wheel_RL", "wheel_rear_R": "wheel_RR"}
for n, b in WB.items(): bone(b, "car", *center(n))
bone("body", "car", 0, -40)                           # squash pivot a bit behind center
for n in ("bumper_front", "bumper_rear", "mirror_L", "mirror_R", "roof", "roof_spoiler"): bone(n, "body", *center(n))
for s in "LR":
    bone(f"headlight_{s}", "body", *center(f"headlight_{s}"))
    bone(f"tail_{s}", "body", *center(f"tail_light_{s}"))
FR = center("bumper_front")
for i in range(6): bone(f"smoke_{i + 1}", "car", FR[0] + (-40, 30, -10, 45, -55, 15)[i], FR[1] - 60 + (0, 15, 35, -10, 25, 45)[i])
rear_y = W(0, Ly["wheel_rear_L"][3])[1] + 10
for s_, n in (("L", "wheel_rear_L"), ("R", "wheel_rear_R")):
    for i in (1, 2): bone(f"dust_{s_}{i}", "car", center(n)[0], rear_y)
bone("fire", "car", FR[0], FR[1] - 20)
debris = C.special_debris("car_04")
for i, (nm, kind) in enumerate(debris): bone("d_" + nm, "car", FR[0] + (i * 41 % 120 - 60), FR[1] - 20 - (i * 23 % 40))
for i in range(3): bone(f"spark_{i + 1}", "car", FR[0] + (-90, 80, 0)[i], FR[1] + 20, rotation=(140, 40, 90)[i])

# ---------------- slots (bottom → top) ----------------
slot("shadow", "car", "shadow"); sc = center("shadow"); put("shadow", "shadow", region("shadow", x=sc[0] + 8, y=sc[1] - 12))
for s_ in "LR":
    for i in (1, 2):
        slot(f"dust_{s_}{i}", f"dust_{s_}{i}", "smoke_round", color="c8a87a00"); put(f"dust_{s_}{i}", "smoke_round", region("smoke_round", scale=0.55))
PART = {"body": "body", **WB, **{n: n for n in ("bumper_front", "bumper_rear", "mirror_L", "mirror_R", "roof", "roof_spoiler")},
        "headlight_L": "headlight_L", "headlight_R": "headlight_R", "tail_light_L": "tail_L", "tail_light_R": "tail_R"}
for n in LY["order"]:
    bn = PART[n]; slot(n, bn, n); put(n, n, region(n, *center(n), b=bn))
    if n.startswith("headlight_"): put(n, n + "_cracked", region(n + "_cracked", *center(n), b=bn))
for s in "LR":                                         # additive light glows (tint per slot)
    slot(f"headlight_glow_{s}", f"headlight_{s}", "light_glow", blend="additive", color="fff2c400")
    put(f"headlight_glow_{s}", "light_glow", region("light_glow", scale=1.3, y=10))
    slot(f"tail_glow_{s}", f"tail_{s}", "light_glow", blend="additive", color="ff281400")
    put(f"tail_glow_{s}", "light_glow", region("light_glow", scale=1.25, y=-8))
for nm, kind in debris: slot(nm, "d_" + nm); put(nm, kind, region(kind, scale=C.DSCALE[nm]))
for i in range(3): slot(f"spark_{i + 1}", f"spark_{i + 1}", blend="additive"); put(f"spark_{i + 1}", "spark_small", region("spark_small", rot=-45))
slot("fire_flash", "fire", "flame_glow", blend="additive", color="ffd27a00"); put("fire_flash", "flame_glow", region("flame_glow", scale=4.5))
slot("fire_puff", "fire", "explosion_main", color="ffffff00"); put("fire_puff", "explosion_main", region("explosion_main", scale=0.5))
for i in range(6):
    n = f"smoke_{i + 1}"; a = "smoke_soft" if i % 2 else "smoke_round"
    slot(n, n, a, color="55555a00"); put(n, a, region(a, scale=0.7))

# ---------------- IDLE 1.2s: bouncy squash (scale Y 1.00 → 1.04) + headlight blink ----------------
P = 1.2
idle = {"bones": {}, "slots": {}}
sq = []
for i in range(2):                                     # 2 bounces: stretch 1.04 → overshoot back → settle
    t0 = i * .6
    sq += [k2(t0, 1, 1, eo2(t0, (1, 1), t0 + .16, (.985, 1.04))), k2(t0 + .16, .985, 1.04), k2(t0 + .3, 1.008, .985), k2(t0 + .42, .998, 1.012), k2(t0 + .52, 1, 1)]
sq.append(k2(P, 1, 1))
idle["bones"]["body"] = {"scale": sq, "translate": [k2(0, 0, 0), k2(.16, 0, 2), k2(.3, 0, -.6), k2(.6, 0, 0), k2(.76, 0, 2), k2(.9, 0, -.6), k2(1.2, 0, 0)]}
blink = [ck(0, "ffffffff"), ck(.82, "ffffffff"), ck(.86, "ffffff4d"), ck(.92, "ffffff4d"), ck(.96, "ffffffff"), ck(1.0, "ffffff4d"), ck(1.05, "ffffff4d"), ck(1.09, "ffffffff")]
glow = [ck(0, "fff2c499"), ck(.82, "fff2c499"), ck(.86, "fff2c400"), ck(.92, "fff2c400"), ck(.96, "fff2c4bb"), ck(1.0, "fff2c400"), ck(1.05, "fff2c400"), ck(1.09, "fff2c499")]
for s in "LR":
    idle["slots"][f"headlight_{s}"] = {"rgba": blink}
    idle["slots"][f"headlight_glow_{s}"] = {"rgba": glow}
anims["idle"] = idle

# ---------------- RUN 0.8s: cartoon bounce + rear lights glow on ----------------
P = 0.8
run = {"bones": {}, "slots": {}}
bs, bt = [], []
for i in range(4):                                     # 4 hops per loop
    t0 = i * .2
    bs += [k2(t0, 1.03, .95), k2(t0 + .07, .97, 1.07), k2(t0 + .14, 1.01, .99)]
    bt += [k2(t0, 0, -2), k2(t0 + .07, 0, 4), k2(t0 + .14, 0, 0)]
bs.append(k2(P, 1.03, .95)); bt.append(k2(P, 0, -2))
run["bones"]["body"] = {"scale": bs, "translate": bt, "rotate": [k1(0, 0), k1(.2, 1.6), k1(.4, 0), k1(.6, -1.6), k1(.8, 0)]}
run["bones"]["mirror_L"] = {"rotate": [k1(R(i * .1), (0, -6)[i % 2]) for i in range(9)]}
run["bones"]["mirror_R"] = {"rotate": [k1(R(i * .1), (0, 6)[i % 2]) for i in range(9)]}
for s in "LR":
    run["slots"][f"tail_glow_{s}"] = {"rgba": [ck(0, "ff2814dd"), ck(.2, "ff3a1cff"), ck(.4, "ff2814cc"), ck(.6, "ff3a1cff"), ck(.8, "ff2814dd")]}
    run["slots"][f"tail_light_{s}"] = {"rgba": [ck(0, "ffd8d8ff")]}
    run["slots"][f"headlight_glow_{s}"] = {"rgba": [ck(0, "fff2c4aa")]}
for b, sd in (("wheel_FL", 2), ("wheel_FR", 4)): run["bones"][b] = {"translate": [k2(t, v * .6, 0) for t, v in jitter(P, 0.08, 1, sd)]}
for s_, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        st = (i - 1) * 0.4 + (0.1 if s_ == "R" else 0); nm = f"dust_{s_}{i}"
        run["bones"][nm] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (0.55, (sx * 40, -130))], (sx * 40, -130))],
                            "scale": [k2(t, *v) for t, v in life(P, st, [(0, (0.3, 0.3)), (0.55, (1.1, 1.0))], (1.1, 1.0))]}
        run["slots"][nm] = {"rgba": [ck(t, hexc((200, 168, 122), v[0])) for t, v in life(P, st, [(0, (0,)), (0.06, (0.75,)), (0.55, (0,))], (0,))]}
anims["run"] = run

# ---------------- CRASH 2.6s: pancake squash (scale Y 0.8 for 2 frames) → pop back; cracked headlights ----------------
P = 2.6
cr = {"bones": {}, "slots": {}}
cr["bones"]["car"] = {"translate": [k2(0, 0, 0), k2(.04, -8, -12), k2(.1, 6, -20), k2(.18, -3, -24), k2(.35, 0, -28, eo2(.35, (0, -28), .8, (0, -30))), k2(.8, 0, -30)],
                      "rotate": [k1(0, 0), k1(.05, -3), k1(.14, 3, eo1(.14, 3, .8, 5)), k1(.8, 5)]}
t0 = .04
cr["bones"]["body"] = {"scale": [k2(0, 1, 1), k2(t0, 1.12, .8), k2(t0 + 2 * F, 1.12, .8), k2(t0 + 2 * F + .06, .9, 1.14), k2(t0 + 2 * F + .14, 1.05, .94),
                                 k2(t0 + 2 * F + .22, .98, 1.03), k2(t0 + 2 * F + .32, 1, .98)],
                       "translate": [k2(0, 0, 0), k2(t0, 0, -8), k2(t0 + 2 * F, 0, -8), k2(t0 + 2 * F + .06, 0, 6), k2(t0 + 2 * F + .2, 0, 0)]}
for s in "LR":
    cr["slots"][f"headlight_{s}"] = {"attachment": [{"name": f"headlight_{s}"}, {"time": t0, "name": f"headlight_{s}_cracked"}]}
    cr["slots"][f"headlight_glow_{s}"] = {"rgba": [ck(0, "fff2c4aa"), ck(t0, "ffffffff"), ck(t0 + .05, "fff2c400")]}     # flash then dead
    cr["slots"][f"tail_glow_{s}"] = {"rgba": [ck(0, "ff281400"), ck(t0, "ff2814ff"), ck(.3, "ff281444"), ck(.36, "ff2814cc"), ck(.45, "ff281400")]}
SC = [("mirror_L", -150, 30, -220, .7, 1.3), ("mirror_R", 140, 60, 250, .7, 1.3), ("bumper_front", 10, 40, 14, .45, 1.08)]
rnd = random.Random(41)
for nm, kind in debris:
    ang = rnd.uniform(20, 160); dist = rnd.uniform(130, 260)
    SC.append(("d_" + nm, math.cos(math.radians(ang)) * dist, math.sin(math.radians(ang)) * dist, rnd.choice((-1, 1)) * rnd.uniform(200, 540), rnd.uniform(.55, .9), rnd.uniform(1.2, 1.45)))
for i, (b, dx, dy, rot, te, hop) in enumerate(SC):
    d0 = 0.02 * (i % 4) + .04
    cr["bones"][b] = {"translate": [k2(0, 0, 0), k2(d0, 0, 0, eo2(d0, (0, 0), te, (dx, dy))), k2(te, dx, dy), k2(te + .12, dx * 1.03, dy * 1.03)],
                      "rotate": [k1(0, 0), k1(d0, 0, eo1(d0, 0, te + .12, rot)), k1(te + .12, rot)],
                      "scale": [k2(0, 1, 1), k2(d0 + (te - d0) * .4, hop, hop), k2(te, 1, 1), k2(te + .06, 1.05, 1.05), k2(te + .12, 1, 1)]}
for nm, kind in debris: cr["slots"][nm] = {"attachment": [{"name": kind}], "rgba": [ck(0, "ffffff00"), ck(.08, "ffffffff")]}
for i in range(3):
    s = f"spark_{i + 1}"; ts = .04 + .02 * i
    cr["slots"][s] = {"attachment": [{"name": "spark_small"}, {"time": .45, "name": None}],
                      "rgba": [ck(0, "ffffff00"), ck(ts, "ffffffff"), ck(ts + .06, "ffffff66"), ck(ts + .12, "ffffffff"), ck(.42, "ffffff00")]}
    cr["bones"][s] = {"scale": [k2(0, .4, .4), k2(ts + .1, 1.2, 1.2), k2(.42, .8, .8)]}
cr["slots"]["fire_flash"] = {"rgba": [ck(0, "ffd27a00"), ck(.05, "ffe6a0ee"), ck(.14, "ffc060aa"), ck(.3, "ff904050"), ck(.5, "ff702000")]}
cr["slots"]["fire_puff"] = {"rgba": [ck(0, "ffffff00"), ck(.07, "ffffffcc"), ck(.14, "ffffffdd"), ck(.35, "ffe0c0aa"), ck(.6, "c8a09050"), ck(.85, "a0908000")]}
cr["bones"]["fire"] = {"scale": [k2(0, .2, .2, eo2(0, (.2, .2), .27, (1, 1))), k2(.27, 1, 1, eo2(.27, (1, 1), .85, (1.25, 1.25))), k2(.85, 1.25, 1.25)]}
for i in range(6):
    s = f"smoke_{i + 1}"; ts = .25 + i * .12; te = min(P, ts + 1.8)
    dx, dy = (-70, 50, -20, 90, -110, 30)[i], (150, 200, 250, 130, 190, 280)[i]
    cr["slots"][s] = {"rgba": [ck(0, "55555a00"), ck(ts, "55555a00"), ck(ts + .22, "4a4a50dd"), ck(ts + .9, "8a8a90aa"), ck(te, "b4b4ba00")]}
    cr["bones"][s] = {"translate": [k2(0, 0, 0), k2(ts, 0, 0, eo2(ts, (0, 0), te, (dx, dy))), k2(te, dx, dy)],
                      "scale": [k2(0, .3, .3), k2(ts, .3, .3, eo2(ts, (.3, .3), te, (2.0, 2.0))), k2(te, 2.0, 2.0)],
                      "rotate": [k1(0, 0), k1(te, (-40, 30, -20, 50, -30, 25)[i])]}
orig = [s["name"] for s in slots]
lift = ["mirror_L", "mirror_R"]
rest = [s for s in orig if s not in lift]; at = rest.index("tail_light_R") + 1
new = rest[:at] + lift + rest[at:]
cr["drawOrder"] = [{"offsets": [{"slot": s, "offset": new.index(s) - orig.index(s)} for s in sorted(lift, key=orig.index) if new.index(s) != orig.index(s)]}]
anims["crash"] = cr

# ---------------- WRECK 2s loop ----------------
P = 2.0
wk = {"bones": {}, "slots": {}, "drawOrder": cr["drawOrder"]}
for b, dx, dy, rot, te, hop in SC: wk["bones"][b] = {"translate": [k2(0, dx * 1.03, dy * 1.03)], "rotate": [k1(0, rot)]}
wk["bones"]["car"] = {"translate": [k2(0, 0, -30)], "rotate": [k1(0, 5)]}
wk["bones"]["body"] = {"scale": [k2(0, 1, .98)]}
for s in "LR":
    wk["slots"][f"headlight_{s}"] = {"attachment": [{"name": f"headlight_{s}_cracked"}]}
    wk["slots"][f"tail_glow_{s}"] = {"rgba": [ck(0, "ff281400"), ck(1.4, "ff281400"), ck(1.45, "ff281488"), ck(1.5, "ff281400")]}   # dying flicker
for nm, kind in debris: wk["slots"][nm] = {"attachment": [{"name": kind}]}
for i in range(6):
    s = f"smoke_{i + 1}"; st = i * P / 6
    wk["bones"][s] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (1.6, ((-50, 40, -20, 60, -60, 30)[i], 200))], (0, 200))],
                      "scale": [k2(t, *v) for t, v in life(P, st, [(0, (.3, .3)), (1.6, (1.4, 1.4))], (1.4, 1.4))]}
    wk["slots"][s] = {"rgba": [ck(t, hexc((110, 110, 118), v[0])) for t, v in life(P, st, [(0, (0,)), (.3, (.7,)), (1.6, (0,))], (0,))]}
anims["wreck"] = wk

for a in anims.values():
    for k in [k for k, v in a.items() if not v]: del a[k]
J = {"skeleton": {"hash": "car_04", "spine": "4.2.40", "x": -260, "y": -400, "width": 520, "height": 800, "images": "./images/", "audio": "", "fps": 30},
     "bones": [{"name": "root"}] + bones, "slots": slots, "skins": [{"name": "default", "attachments": att}], "animations": anims}
json.dump(J, open(os.path.join(C.D, "car.json"), "w"), indent=1)
print("bones", len(J["bones"]), "slots", len(slots), "anims", list(anims))
