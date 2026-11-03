# Build Spine 4.2 skeleton for car_02 (blue muscle car, rear spoiler, wipers). All motion = Spine keys on PNGs.
# usage: python3 build_car02.py <car_dir>       (images/ + layout.json from prep_car.py)
# Anims: idle (2.4s loop) · run (0.8s loop) · crash (2.6s one-shot) · wreck (2s loop, after crash)
# Smoke / explosion / spark / debris PNGs reused from car_special.
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carlib as C
from carlib import bone, slot, region, put, center, W, k1, k2, eo1, eo2, ck, life, hexc, jitter, R, BW, bones, slots, att, anims

LY = C.setup(sys.argv[1])
Ly = LY["layers"]
WIPE = -35          # wiper sweep: 35° onto the glass (clockwise in screen = negative in Spine)

# ---------------- bones ----------------
bone("car", "root", 0, 0)
bone("chassis", "car", 0, 0)
WB = {"wheel_front_L": "wheel_FL", "wheel_front_R": "wheel_FR", "wheel_back_L": "wheel_RL", "wheel_back_R": "wheel_RR"}
for n, b in WB.items(): bone(b, "car", *center(n))
bone("scoop", "chassis", *center("hood_scoop"))
bone("bumper_F", "chassis", *center("front_bumper"))
bone("bumper_R", "chassis", *center("rear_bumper"))
bone("spoiler", "chassis", *center("spoiler"))
bone("wiper_L", "chassis", *W(631, 580))          # pivots = blade root (left end)
bone("wiper_R", "chassis", *W(822, 551))
SC_ = center("hood_scoop")
for i in range(6): bone(f"smoke_{i + 1}", "car", SC_[0] + (-20, 25, -5, 30, -30, 10)[i], SC_[1] + (0, 15, 35, -10, 25, 45)[i])
rear_y = W(0, Ly["wheel_back_L"][3])[1] + 10
for s_, n in (("L", "wheel_back_L"), ("R", "wheel_back_R")):
    for i in (1, 2): bone(f"dust_{s_}{i}", "car", center(n)[0], rear_y)
BR = Ly["rear_bumper"]; ex_y = W(0, BR[3])[1] + 6
for s_, px in (("L", BR[0] + 120), ("R", BR[2] - 120)):
    for i in (1, 2): bone(f"exsmoke_{s_}{i}", "car", W(px, 0)[0], ex_y)
FR = center("front_bumper")
bone("fire", "car", FR[0], FR[1] - 25)
debris = C.special_debris("car_02")
for i, (nm, kind) in enumerate(debris): bone("d_" + nm, "car", FR[0] + (i * 41 % 120 - 60), FR[1] - 30 - (i * 23 % 40))
for i in range(3): bone(f"spark_{i + 1}", "car", FR[0] + (-90, 80, 0)[i], FR[1] + 20, rotation=(140, 40, 90)[i])

# ---------------- slots (bottom → top) ----------------
slot("shadow", "car", "shadow"); sc = center("shadow"); put("shadow", "shadow", region("shadow", x=sc[0] + 8, y=sc[1] - 12))
for s_ in "LR":
    for i in (1, 2):
        slot(f"dust_{s_}{i}", f"dust_{s_}{i}", "smoke_round", color="c8a87a00"); put(f"dust_{s_}{i}", "smoke_round", region("smoke_round", scale=0.55))
PART = {"body": "chassis", "stripe": "chassis", "hood_scoop": "scoop", "spoiler": "spoiler", "wiper_L": "wiper_L", "wiper_R": "wiper_R",
        "front_bumper": "bumper_F", "rear_bumper": "bumper_R", **WB}
for n in LY["order"]:
    bn = PART[n]; slot(n, bn, n); put(n, n, region(n, *center(n), b=bn))
for s_ in "LR":
    for i in (1, 2):
        n = f"exsmoke_{s_}{i}"; slot(n, n, "smoke_round", color="bebec600"); put(n, "smoke_round", region("smoke_round", scale=0.3))
for nm, kind in debris: slot(nm, "d_" + nm); put(nm, kind, region(kind, scale=C.DSCALE[nm]))
for i in range(3): slot(f"spark_{i + 1}", f"spark_{i + 1}", blend="additive"); put(f"spark_{i + 1}", "spark_small", region("spark_small", rot=-45))
slot("fire_flash", "fire", "flame_glow", blend="additive", color="ffd27a00"); put("fire_flash", "flame_glow", region("flame_glow", scale=5.0))
slot("fire_puff", "fire", "explosion_main", color="ffffff00"); put("fire_puff", "explosion_main", region("explosion_main", scale=0.6))
for i in range(6):
    n = f"smoke_{i + 1}"; a = "smoke_soft" if i % 2 else "smoke_round"
    slot(n, n, a, color="55555a00"); put(n, a, region(a, scale=0.75))

# ---------------- IDLE 2.4s: one slow wiper sweep 0 → 35° → 0 ----------------
P = 2.4
idle = {"bones": {}, "slots": {}}
for b, d in (("wiper_L", 0), ("wiper_R", 0.06)):
    t0, t1, t2 = .3 + d, 1.05 + d, 1.8 + d                        # ease-in-out out & back, then rest
    idle["bones"][b] = {"rotate": [k1(0, 0), k1(t0, 0, [R(t0 + .3), 0, R(t1 - .3), WIPE]), k1(t1, WIPE, [R(t1 + .3), WIPE, R(t2 - .3), 0]),
                                   k1(t2, 0), k1(P, 0)]}
idle["bones"]["chassis"] = {"translate": [k2(t, v * .5, w * .5) for (t, v), (_, w) in zip(jitter(P, 0.1, 1, 3), jitter(P, 0.1, 1, 7))]}
for s_, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        m = f"exsmoke_{s_}{i}"; st = (i - 1) * 1.2 + (0.6 if s_ == "R" else 0)
        idle["bones"][m] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (1.3, (sx * 50, -120))], (sx * 50, -120))],
                            "scale": [k2(t, *v) for t, v in life(P, st, [(0, (0.6, 0.6)), (1.3, (2.0, 2.0))], (2, 2))]}
        idle["slots"][m] = {"rgba": [ck(t, hexc((190, 190, 198), v[0])) for t, v in life(P, st, [(0, (0,)), (0.15, (0.75,)), (0.6, (0.45,)), (1.3, (0,))], (0,))]}
anims["idle"] = idle

# ---------------- RUN 0.8s: spoiler vibrates (scale X ±2%, translate Y ±1px) ----------------
P = 0.8
run = {"bones": {}, "slots": {}}
n = 20
run["bones"]["spoiler"] = {"scale": [k2(R(i * P / n), (1.02, 0.98)[i % 2] if i < n else 1.02, 1) for i in range(n + 1)],
                           "translate": [k2(R(i * P / n), 0, (1, -1)[i % 2] if i < n else 1) for i in range(n + 1)]}
run["bones"]["car"] = {"translate": [k2(R(i * 0.1), 0, (0, 1.2, 0, -1)[i % 4]) for i in range(9)]}
run["bones"]["wiper_L"] = {"rotate": [k1(R(i * .08), (0, -1.2)[i % 2]) for i in range(11)]}
run["bones"]["wiper_R"] = {"rotate": [k1(R(i * .08), (-1.2, 0)[i % 2]) for i in range(11)]}
for b, sd in (("wheel_FL", 2), ("wheel_FR", 4)): run["bones"][b] = {"translate": [k2(t, v * .6, 0) for t, v in jitter(P, 0.08, 1, sd)]}
for s_, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        st = (i - 1) * 0.4 + (0.1 if s_ == "R" else 0); nm = f"dust_{s_}{i}"
        run["bones"][nm] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (0.55, (sx * 40, -140))], (sx * 40, -140))],
                            "scale": [k2(t, *v) for t, v in life(P, st, [(0, (0.3, 0.3)), (0.55, (1.2, 1.1))], (1.2, 1.1))]}
        run["slots"][nm] = {"rgba": [ck(t, hexc((200, 168, 122), v[0])) for t, v in life(P, st, [(0, (0,)), (0.06, (0.8,)), (0.55, (0,))], (0,))]}
anims["run"] = run

# ---------------- CRASH 2.6s ----------------
P = 2.6
cr = {"bones": {}, "slots": {}}
cr["bones"]["car"] = {"translate": [k2(0, 0, 0), k2(.04, -10, -14), k2(.09, 7, -22), k2(.15, -4, -27), k2(.3, 0, -32, eo2(.3, (0, -32), .8, (0, -36))), k2(.8, 0, -36)],
                      "rotate": [k1(0, 0), k1(.05, -3), k1(.12, 3, eo1(.12, 3, .8, 8)), k1(.8, 8)]}
# spoiler snaps off → flies backward with spin, bounces, settles behind the car
SPX, SPY = 50, -215
cr["bones"]["spoiler"] = {
    "translate": [k2(0, 0, 0), k2(.05, 0, -6), k2(.08, 0, -6, eo2(.08, (0, -6), .85, (SPX, SPY))), k2(.85, SPX, SPY), k2(1.0, SPX * 1.08, SPY - 24), k2(1.15, SPX * 1.1, SPY - 30)],
    "rotate": [k1(0, 0), k1(.05, 4), k1(.08, 4, eo1(.08, 4, .85, 530)), k1(.85, 530), k1(1.0, 548), k1(1.15, 543)],
    "scale": [k2(0, 1, 1), k2(.05, 1.03, .97), k2(.4, 1.3, 1.3), k2(.85, 1, 1), k2(.92, 1.06, 1.06), k2(1.0, 1, 1)]}
# wipers flop to a broken angle (overshoot + settle, R one bent the other way)
cr["bones"]["wiper_L"] = {"rotate": [k1(0, 0), k1(.06, 0), k1(.16, 72), k1(.26, 48), k1(.36, 62), k1(.48, 55)]}
cr["bones"]["wiper_R"] = {"rotate": [k1(0, 0), k1(.08, 0), k1(.18, -128), k1(.3, -96), k1(.42, -112), k1(.55, -106)],
                          "translate": [k2(0, 0, 0), k2(.18, 4, -6), k2(.55, 3, -5)]}
cr["bones"]["bumper_F"] = {"translate": [k2(0, 0, 0), k2(.1, 0, -14), k2(.25, -6, -18)], "rotate": [k1(0, 0), k1(.1, -6), k1(.25, -9)]}
cr["bones"]["scoop"] = {"translate": [k2(0, 0, 0), k2(.12, 0, 6), k2(.3, 2, 4)], "rotate": [k1(0, 0), k1(.12, -8), k1(.3, -6)]}
SC = []
rnd = random.Random(23)
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
orig = [s["name"] for s in slots]
lift = ["spoiler"]
rest = [s for s in orig if s not in lift]; at = rest.index("rear_bumper") + 1
new = rest[:at] + lift + rest[at:]
cr["drawOrder"] = [{"offsets": [{"slot": s, "offset": new.index(s) - orig.index(s)} for s in sorted(lift, key=orig.index) if new.index(s) != orig.index(s)]}]
anims["crash"] = cr

# ---------------- WRECK 2s loop ----------------
P = 2.0
wk = {"bones": {}, "slots": {}, "drawOrder": cr["drawOrder"]}
for b, dx, dy, rot, te, hop in SC: wk["bones"][b] = {"translate": [k2(0, dx * 1.03, dy * 1.03)], "rotate": [k1(0, rot)]}
for b in ("car", "spoiler", "wiper_L", "wiper_R", "bumper_F", "scoop"):     # hold crash end pose
    wk["bones"][b] = {k: [{kk: vv for kk, vv in v[-1].items() if kk not in ("time", "curve")}] for k, v in cr["bones"][b].items()}
for nm, kind in debris: wk["slots"][nm] = {"attachment": [{"name": kind}]}
for i in range(6):
    s = f"smoke_{i + 1}"; st = i * P / 6
    wk["bones"][s] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (1.6, ((-50, 40, -20, 60, -60, 30)[i], 200))], (0, 200))],
                      "scale": [k2(t, *v) for t, v in life(P, st, [(0, (.3, .3)), (1.6, (1.4, 1.4))], (1.4, 1.4))]}
    wk["slots"][s] = {"rgba": [ck(t, hexc((110, 110, 118), v[0])) for t, v in life(P, st, [(0, (0,)), (.3, (.7,)), (1.6, (0,))], (0,))]}
anims["wreck"] = wk

for a in anims.values():
    for k in [k for k, v in a.items() if not v]: del a[k]
J = {"skeleton": {"hash": "car_02", "spine": "4.2.40", "x": -260, "y": -400, "width": 520, "height": 800, "images": "./images/", "audio": ""},
     "bones": [{"name": "root"}] + bones, "slots": slots, "skins": [{"name": "default", "attachments": att}], "animations": anims}
json.dump(J, open(os.path.join(C.D, "car.json"), "w"), indent=1)
print("bones", len(J["bones"]), "slots", len(slots), "anims", list(anims))
