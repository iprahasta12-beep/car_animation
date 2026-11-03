# Build Spine 4.2 skeleton for car_05 (purple van / SUV, long cream roof). All motion = Spine keys on PNGs.
# usage: python3 build_car05.py <car_dir>
#   needs images/ + layout.json from prep_car.py, then fx_car04.py (cracked headlights) + fx_car05.py (car_flash, fx_dent),
#   roof_shine.png generated once.
# Skeleton fps 30. Root bone scale 1.2 (car_05 is 20% bigger than the other cars).
# Anims: idle (2.4s loop) · run (0.8s loop) · crash (36 frames = 1.2s, events sfx_crash @0 / crash_end @36) · wreck (2s loop)
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carlib as C
from carlib import bone, slot, region, put, center, W, k1, k2, eo1, eo2, ck, life, hexc, jitter, R, BW, bones, slots, att, anims

LY = C.setup(sys.argv[1])
Ly = LY["layers"]
FPS = 30
f = lambda n: R(n / FPS)                                     # frame → seconds

# ---------------- bones ----------------
bone("shake", "root", 0, 0)                                  # screen-shake layer
bone("car_main", "shake", 0, 0)
WB = {"wheel_front_L": "wheel_FL", "wheel_front_R": "wheel_FR", "wheel_rear_L": "wheel_RL", "wheel_rear_R": "wheel_RR"}
for n, b in WB.items(): bone(b, "car_main", *center(n))
bone("body_bounce", "car_main", 0, 0)
for n in ("roof", "bumper_front", "bumper_rear", "mirror_L", "mirror_R"): bone(n, "body_bounce", *center(n))
DL, DR = Ly["rear_door_L"], Ly["rear_door_R"]
bone("rear_door_L", "body_bounce", *W(DL[0] + 4, (DL[1] + DL[3]) / 2))      # hinge = outer edge
bone("rear_door_R", "body_bounce", *W(DR[2] - 4, (DR[1] + DR[3]) / 2))
RF = Ly["roof"]; ry0, ry1 = W(0, RF[1])[1], W(0, RF[3])[1]; rx0, rx1 = W(RF[0], 0)[0], W(RF[2], 0)[0]
bone("roof_shine", "body_bounce", 0, ry0 + 40)
FRB = center("bumper_front")
for i in range(3): bone(f"spark_{i + 1}", "car_main", FRB[0] + (-90, 80, 0)[i], FRB[1] + 10, rotation=(140, 40, 90)[i])
rear_y = W(0, Ly["wheel_rear_L"][3])[1] + 10
for s_, n in (("L", "wheel_rear_L"), ("R", "wheel_rear_R")):
    for i in (1, 2): bone(f"dust_{s_}{i}", "car_main", center(n)[0], rear_y)
ROT_END = 50                                                 # settled car_main rotation
hx, hy = 0, FRB[1] - 70                                      # hood point in car space → world after the turn
a = math.radians(ROT_END); HX, HY = hx * math.cos(a) - hy * math.sin(a), hx * math.sin(a) + hy * math.cos(a)
for i in range(4): bone(f"smoke_{i + 1}", "shake", HX + (-12, 14, -4, 10)[i], HY + (0, 6, 12, -4)[i])

# ---------------- slots (bottom → top) ----------------
slot("shadow", "car_main", "shadow"); sc = center("shadow"); put("shadow", "shadow", region("shadow", x=sc[0] + 8, y=sc[1] - 12))
for s_ in "LR":
    for i in (1, 2):
        slot(f"dust_{s_}{i}", f"dust_{s_}{i}", "smoke_round", color="c8a87a00"); put(f"dust_{s_}{i}", "smoke_round", region("smoke_round", scale=0.6))
PART = {"body": "body_bounce", **WB, **{n: n for n in ("roof", "bumper_front", "bumper_rear", "mirror_L", "mirror_R", "rear_door_L", "rear_door_R")},
        "headlight_L": "body_bounce", "headlight_R": "body_bounce", "tail_light_L": "body_bounce", "tail_light_R": "body_bounce"}
CAR_SLOTS = []
for n in LY["order"]:
    bn = PART[n]; slot(n, bn, n); CAR_SLOTS.append(n); put(n, n, region(n, *center(n), b=bn))
    if n == "headlight_L": put(n, "headlight_L_cracked", region("headlight_L_cracked", *center(n), b=bn))
    if n == "bumper_front":
        slot("fx_dent", "body_bounce"); CAR_SLOTS.append("fx_dent"); put("fx_dent", "fx_dent", region("fx_dent", *center("fx_dent"), b="body_bounce"))
    if n == "roof":                                          # shine clipped to the roof panel (rounded rect)
        ins, rr = 6, 22; ax, bx, ay, by = rx0 + ins, rx1 - ins, ry0 - ins, ry1 + ins
        poly = [ax + rr, ay, bx - rr, ay, bx, ay - rr, bx, by + rr, bx - rr, by, ax + rr, by, ax, by + rr, ax, ay - rr]
        slot("roof_clip", "body_bounce", "roof_clip")
        put("roof_clip", "roof_clip", {"type": "clipping", "end": "roof_shine", "vertexCount": 8, "vertices": [R(v) for v in poly], "color": "ce3a3aff"})
        slot("roof_shine", "roof_shine", "roof_shine", blend="additive", color="ffffff00")
        put("roof_shine", "roof_shine", region("roof_shine", scale=1.15))
slot("car_flash", "body_bounce"); put("car_flash", "car_flash", region("car_flash", *center("car_flash"), b="body_bounce"))
for i in range(3): slot(f"spark_{i + 1}", f"spark_{i + 1}", blend="additive"); put(f"spark_{i + 1}", "spark_small", region("spark_small", rot=-45))
for i in range(4):
    n = f"smoke_{i + 1}"; a_ = "smoke_soft" if i % 2 else "smoke_round"
    slot(n, n, a_, color="8a8a9000"); put(n, a_, region(a_, scale=0.6))

# ---------------- IDLE 2.4s: slow, long roof shine sweep ----------------
P = 2.4
idle = {"bones": {}, "slots": {}}
travel = (ry1 - ry0) - 80
idle["bones"]["roof_shine"] = {"translate": [k2(0, 0, 0), k2(.2, 0, 0, [.8, 0, 1.4, 0, .6, 0, 1.6, travel]), k2(1.9, 0, travel), k2(P, 0, travel)]}
idle["slots"]["roof_shine"] = {"rgba": [ck(0, "ffffff00"), ck(.2, "ffffff00"), ck(.55, "ffffffb0"), ck(1.5, "ffffffa0"), ck(1.9, "ffffff00"), ck(P, "ffffff00")]}
idle["bones"]["body_bounce"] = {"translate": [k2(t, v * .4, w * .4) for (t, v), (_, w) in zip(jitter(P, 0.15, 1, 3), jitter(P, 0.15, 1, 7))]}
anims["idle"] = idle

# ---------------- RUN 0.8s: heavy body roll (shear X ±2°) ----------------
P = 0.8
run = {"bones": {}, "slots": {}}
run["bones"]["body_bounce"] = {"shear": [k2(R(i * .05), 2 * math.cos(i * .05 / P * 2 * math.pi), 0) for i in range(17)],
                               "translate": [k2(R(i * .05), -2 * math.cos(i * .05 / P * 2 * math.pi), 0) for i in range(17)],
                               "scale": [k2(0, 1, 1), k2(.2, .995, 1), k2(.4, 1, 1), k2(.6, .995, 1), k2(P, 1, 1)]}
run["bones"]["mirror_L"] = {"rotate": [k1(0, 0), k1(.4, -4), k1(P, 0)]}
run["bones"]["mirror_R"] = {"rotate": [k1(0, 0), k1(.4, 4), k1(P, 0)]}
for b, sd in (("wheel_FL", 2), ("wheel_FR", 4)): run["bones"][b] = {"translate": [k2(t, v * .6, 0) for t, v in jitter(P, 0.08, 1, sd)]}
for s_, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        st = (i - 1) * 0.4 + (0.1 if s_ == "R" else 0); nm = f"dust_{s_}{i}"
        run["bones"][nm] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (0.55, (sx * 40, -140))], (sx * 40, -140))],
                            "scale": [k2(t, *v) for t, v in life(P, st, [(0, (0.3, 0.3)), (0.55, (1.2, 1.1))], (1.2, 1.1))]}
        run["slots"][nm] = {"rgba": [ck(t, hexc((200, 168, 122), v[0])) for t, v in life(P, st, [(0, (0,)), (0.06, (0.75,)), (0.55, (0,))], (0,))]}
anims["run"] = run

# ---------------- CRASH: 36 frames (frame table) ----------------
GREY = "ccccccff"                                            # 80% grey tint
cr = {"bones": {}, "slots": {}, "events": [{"name": "sfx_crash"}, {"time": f(36), "name": "crash_end"}]}
# f0: all slots flash white 1 frame (white silhouette PNG on top)
cr["slots"]["car_flash"] = {"attachment": [{"name": "car_flash"}, {"time": f(1), "name": None}]}
# f0–2: car_main up 14px then snaps back; body_bounce squash Y 0.92 / X 1.06
# f2–14: car_main rotate 0 → 70 → 55; f14–28 settle → 50
cr["bones"]["car_main"] = {"translate": [k2(0, 0, 0), k2(f(1), 0, 14), k2(f(2), 0, 0)],
                           "rotate": [k1(0, 0), k1(f(2), 0, eo1(f(2), 0, f(8), 70)), k1(f(8), 70), k1(f(14), 55, [f(18), 55, f(24), ROT_END]), k1(f(28), ROT_END)]}
cr["bones"]["body_bounce"] = {"scale": [k2(0, 1, 1), k2(f(1), 1.06, .92), k2(f(2), 1.06, .92), k2(f(5), .98, 1.03), k2(f(8), 1, 1),
                                        k2(f(14), 1, 1), k2(f(18), 1.03, .97), k2(f(22), .99, 1.02), k2(f(26), 1, 1)]}
# screen shake ±6px f2–14
sh = [k2(0, 0, 0), k2(f(2), 0, 0)]
for i, fr in enumerate(range(3, 14)):
    amp = 6 * (1 - i / 12); sh.append(k2(f(fr), (amp, -amp)[i % 2] * (1 if i % 3 else .6), (-amp, amp)[i % 2] * (.7 if i % 2 else 1)))
sh.append(k2(f(14), 0, 0)); cr["bones"]["shake"] = {"translate": sh}
# f3: dent on; headlight L cracked + alpha flicker; f12–20 everything tints to 80% grey
cr["slots"]["fx_dent"] = {"attachment": [{"name": None}, {"time": f(3), "name": "fx_dent"}], "rgba": [ck(0, "ffffffff"), ck(f(12), "ffffffff"), ck(f(20), GREY)]}
cr["slots"]["headlight_L"] = {"attachment": [{"name": "headlight_L"}, {"time": f(3), "name": "headlight_L_cracked"}],
                              "rgba": [ck(0, "ffffffff"), ck(f(3), "ffffffff"), ck(f(5), "ffffff4d"), ck(f(6), "ffffffff"), ck(f(8), "ffffff33"),
                                       ck(f(9), "ffffffff"), ck(f(11), "ffffff66"), ck(f(12), "ffffffff"), ck(f(20), GREY)]}
for n in CAR_SLOTS:
    if n not in cr["slots"]: cr["slots"][n] = {"rgba": [ck(0, "ffffffff"), ck(f(12), "ffffffff"), ck(f(20), GREY)]}
# f3–10: sparks at the front bumper; bumper_front flies off (40px, 200°, alpha → 0)
for i in range(3):
    s = f"spark_{i + 1}"; t0 = f(3 + i)
    cr["slots"][s] = {"attachment": [{"name": None}, {"time": t0, "name": "spark_small"}, {"time": f(11), "name": None}],
                      "rgba": [ck(0, "ffffffff"), ck(f(7), "ffffffcc"), ck(f(10), "ffffff00")]}
    cr["bones"][s] = {"scale": [k2(0, .4, .4), k2(t0, .5, .5), k2(f(6 + i), 1.3, 1.3), k2(f(10), .8, .8)]}
cr["bones"]["bumper_front"] = {"translate": [k2(0, 0, 0), k2(f(3), 0, 0, eo2(f(3), (0, 0), f(10), (10, 40))), k2(f(10), 10, 40)],
                               "rotate": [k1(0, 0), k1(f(3), 0, eo1(f(3), 0, f(10), 200)), k1(f(10), 200)]}
cr["slots"]["bumper_front"] = {"rgba": [ck(0, "ffffffff"), ck(f(3), "ffffffff"), ck(f(10), "ffffff00")]}
# f4–12: roof shifts loose (scale Y 0.95, rotate 3°, 4px offset)
cr["bones"]["roof"] = {"scale": [k2(0, 1, 1), k2(f(4), 1, 1, eo2(f(4), (1, 1), f(12), (1, .95))), k2(f(12), 1, .95)],
                       "rotate": [k1(0, 0), k1(f(4), 0, eo1(f(4), 0, f(12), 3)), k1(f(12), 3)],
                       "translate": [k2(0, 0, 0), k2(f(4), 0, 0, eo2(f(4), (0, 0), f(12), (4, -2))), k2(f(12), 4, -2)]}
# f6–16: rear door L pops open 70° on its hinge (outward = clockwise = −70 in Spine) with a small bounce
cr["bones"]["rear_door_L"] = {"rotate": [k1(0, 0), k1(f(6), 0), k1(f(11), -78), k1(f(14), -64), k1(f(16), -70)]}
# f6–14: mirror R flies off (move + 360°, alpha → 0)
cr["bones"]["mirror_R"] = {"translate": [k2(0, 0, 0), k2(f(6), 0, 0, eo2(f(6), (0, 0), f(14), (90, 40))), k2(f(14), 90, 40)],
                           "rotate": [k1(0, 0), k1(f(6), 0), k1(f(14), -360)],
                           "scale": [k2(0, 1, 1), k2(f(10), 1.25, 1.25), k2(f(14), 1, 1)]}
cr["slots"]["mirror_R"] = {"rgba": [ck(0, "ffffffff"), ck(f(8), "ffffffff"), ck(f(14), "ffffff00")]}
# f8–18: wheel FR wobbles ±15° and moves out 8px
cr["bones"]["wheel_FR"] = {"rotate": [k1(0, 0), k1(f(8), 0), k1(f(10), 15), k1(f(12), -15), k1(f(14), 12), k1(f(16), -8), k1(f(18), 5)],
                           "translate": [k2(0, 0, 0), k2(f(8), 0, 0, eo2(f(8), (0, 0), f(12), (8, 0))), k2(f(12), 8, 0)]}
# f12–36: smoke from the hood loops up, alpha 0.4
for i in range(4):
    s = f"smoke_{i + 1}"; t0, te = f(12 + i * 4), f(12 + i * 4 + 12)
    cr["slots"][s] = {"rgba": [ck(0, "8a8a9000"), ck(t0, "8a8a9000"), ck(R(t0 + .12), "8a8a9066"), ck(te, "9a9aa000")]}
    cr["bones"][s] = {"translate": [k2(0, 0, 0), k2(t0, 0, 0, eo2(t0, (0, 0), te, ((-10, 12, -6, 8)[i], 110))), k2(te, (-10, 12, -6, 8)[i], 110)],
                      "scale": [k2(0, .3, .3), k2(t0, .3, .3, eo2(t0, (.3, .3), te, (1.4, 1.4))), k2(te, 1.4, 1.4)]}
anims["crash"] = cr

# ---------------- WRECK 2s loop: hold crash end pose, smoke up (alpha 0.4), headlight flicker ----------------
P = 2.0
wk = {"bones": {}, "slots": {}}
for b in ("car_main", "roof", "rear_door_L", "mirror_R", "wheel_FR", "bumper_front"):
    wk["bones"][b] = {k: [{kk: vv for kk, vv in v[-1].items() if kk not in ("time", "curve")}] for k, v in cr["bones"][b].items()}
for n in CAR_SLOTS: wk["slots"][n] = {"rgba": [ck(0, GREY)]}
wk["slots"]["bumper_front"] = {"rgba": [ck(0, "cccccc00")]}
wk["slots"]["mirror_R"] = {"rgba": [ck(0, "cccccc00")]}
wk["slots"]["fx_dent"] = {"attachment": [{"name": "fx_dent"}], "rgba": [ck(0, GREY)]}
wk["slots"]["headlight_L"] = {"attachment": [{"name": "headlight_L_cracked"}],
                              "rgba": [ck(0, GREY), ck(1.3, GREY), ck(1.34, "cccccc40"), ck(1.4, GREY), ck(1.46, "cccccc30"), ck(1.52, GREY)]}
for i in range(4):
    s = f"smoke_{i + 1}"; st = i * P / 4
    wk["bones"][s] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (1.4, ((-10, 12, -6, 8)[i], 130))], (0, 130))],
                      "scale": [k2(t, *v) for t, v in life(P, st, [(0, (.3, .3)), (1.4, (1.4, 1.4))], (1.4, 1.4))]}
    wk["slots"][s] = {"rgba": [ck(t, hexc((138, 138, 144), v[0])) for t, v in life(P, st, [(0, (0,)), (.25, (.4,)), (1.4, (0,))], (0,))]}
anims["wreck"] = wk

for an in anims.values():
    for k in [k for k, v in an.items() if not v]: del an[k]
bones_out = [{"name": "root", "scaleX": 1.2, "scaleY": 1.2}] + bones
J = {"skeleton": {"hash": "car_05", "spine": "4.2.40", "x": -320, "y": -480, "width": 640, "height": 960, "images": "./images/", "audio": "", "fps": FPS},
     "bones": bones_out, "slots": slots, "skins": [{"name": "default", "attachments": att}],
     "events": {"sfx_crash": {}, "crash_end": {}}, "animations": anims}
json.dump(J, open(os.path.join(C.D, "car.json"), "w"), indent=1)
print("bones", len(J["bones"]), "slots", len(slots), "anims", list(anims))
