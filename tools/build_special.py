# Build Spine 4.2 skeleton for car "special" (white hot rod) — every motion is Spine keys, no code.
# usage: python3 build_special.py <car_dir>      (car_dir holds images/ + layout.json from prep_special.py)
# Anims: idle (1.2s loop), run (0.96s loop), crash (2.8s one-shot, ends wrecked), wreck (2s loop, after crash)
import sys, os, json, math
from PIL import Image

D = sys.argv[1]
IMG = os.path.join(D, "images")
LY = json.load(open(os.path.join(D, "layout.json")))
S = LY["scale"]
CX, CY = 800, 800                                   # PSD pixel = skeleton origin (car center)
R = lambda v: round(v, 3)

def W(px, py): return (R((px - CX) * S), R((CY - py) * S))
def center(n):
    l, t, r, b = LY["layers"][n]; return W((l + r) / 2, (t + b) / 2)
def size(img): return Image.open(os.path.join(IMG, img + ".png")).size

bones, slots, att, anims = [], [], {}, {}
BW = {"root": (0, 0)}                               # bone world pos (no rotation on parents → local = world - parent)
def bone(name, parent, wx, wy, **kw):
    px, py = BW[parent]; BW[name] = (wx, wy)
    b = {"name": name, "parent": parent}
    if R(wx - px): b["x"] = R(wx - px)
    if R(wy - py): b["y"] = R(wy - py)
    b.update(kw); bones.append(b)
def slot(name, b, attachment=None, blend=None, color=None):
    s = {"name": name, "bone": b}
    if attachment: s["attachment"] = attachment
    if blend: s["blend"] = blend
    if color: s["color"] = color
    slots.append(s)
def region(img, wx=None, wy=None, b=None, scale=1, x=0, y=0, rot=0, path=None, seq=None):
    tw, th = size(img if not seq else img + "1")
    if b is not None and wx is not None:
        x, y = wx - BW[b][0], wy - BW[b][1]
    a = {"x": R(x), "y": R(y), "width": tw, "height": th}
    if scale != 1: a["scaleX"] = a["scaleY"] = scale
    if rot: a["rotation"] = rot
    if path: a["path"] = path
    if seq: a["sequence"] = seq
    return a
def put(slot_name, att_name, a): att.setdefault(slot_name, {})[att_name] = a

# ---------------- bones ----------------
bone("car", "root", 0, 0)
bone("chassis", "car", 0, 0)
for n, b in (("wheel_rear_L", "wheel_RL"), ("wheel_rear_R", "wheel_RR")): bone(b, "car", *center(n))
bone("engine", "car", *center("engine_block"))
bone("blower", "engine", *center("blower_scoop"))
bone("header_L", "engine", *center("header_cover_L"))
bone("header_R", "engine", *center("header_cover_R"))
bone("exhaust_L", "car", *center("exhaust_pipe_L"))
bone("exhaust_R", "car", *center("exhaust_pipe_R"))
l, t, r, b = LY["layers"]["exhaust_pipe_L"]; TIP_L = W(l + 50, b - 34)
l, t, r, b = LY["layers"]["exhaust_pipe_R"]; TIP_R = W(r - 50, b - 34)
bone("tip_L", "exhaust_L", *TIP_L, rotation=-18)
bone("tip_R", "exhaust_R", *TIP_R, rotation=18)
bone("flame_L", "tip_L", *TIP_L); bone("flame_R", "tip_R", *TIP_R)
bone("susp_L", "car", *center("susp_arm_L")); bone("susp_R", "car", *center("susp_arm_R"))
bone("wheel_FL", "car", *center("wheel_front_L")); bone("wheel_FR", "car", *center("wheel_front_R"))
bone("wing", "car", *center("wing_front"))
# fx bones
RL, RR = BW["wheel_RL"], BW["wheel_RR"]
rear_y = (CY - LY["layers"]["wheel_rear_L"][3]) * S + 10
for s_, wx in (("L", RL[0]), ("R", RR[0])):
    for i in (1, 2): bone(f"dust_{s_}{i}", "car", wx, rear_y)
for s_, tp in (("L", TIP_L), ("R", TIP_R)):
    for i in (1, 2): bone(f"exsmoke_{s_}{i}", "car", tp[0], tp[1] - 20)
EN = BW["engine"]
bone("fire", "car", EN[0], EN[1] + 30)
for i in range(6): bone(f"smoke_{i + 1}", "car", EN[0] + (-40, 30, -10, 50, -50, 10)[i], EN[1] + (20, 50, -20, 0, 60, 90)[i])
DEB = [("bolt", 7), ("shard", 5), ("debris_round", 4)]
debris = []
for kind, n in DEB:
    for i in range(n):
        nm = f"{kind}_{i + 1}"; debris.append((nm, kind))
        bone("d_" + nm, "car", EN[0] + ((i * 37) % 60 - 30), EN[1] + ((i * 53) % 80 - 20))
for i in range(4): bone(f"spark_{i + 1}", "car", (-150, 160, -60, 80)[i], BW["wing"][1] + (10, 0, 30, 25)[i], rotation=(150, 30, 110, 60)[i])

# ---------------- slots (draw order bottom → top) ----------------
slot("shadow", "car", "shadow")
put("shadow", "shadow", region("shadow", x=center("shadow")[0] + 8, y=center("shadow")[1] - 12))
for s_ in "LR":
    for i in (1, 2): slot(f"dust_{s_}{i}", f"dust_{s_}{i}", color="c8a87aff")
PART_BONE = {"bottom_body": "chassis", "body": "chassis", "stripes": "chassis", "fender_rear_R": "chassis", "fender_rear_L": "chassis",
             "bumper_rear": "chassis", "wheel_rear_L": "wheel_RL", "wheel_rear_R": "wheel_RR", "blower_scoop": "blower",
             "engine_block": "engine", "header_cover_L": "header_L", "header_cover_R": "header_R", "susp_arm_L": "susp_L",
             "susp_arm_R": "susp_R", "wheel_front_L": "wheel_FL", "wheel_front_R": "wheel_FR", "wing_front": "wing",
             "exhaust_pipe_L": "exhaust_L", "exhaust_pipe_R": "exhaust_R"}
SEQ4 = {"count": 4, "start": 1, "digits": 1}
MESH_V = {}
def grid_mesh(img, bname, cols=3, rows=8):
    """Unweighted grid mesh, hull first. Returns attachment + (vertex list order) for deforms."""
    tw, th = size(img); cx, cy = center(img); ox, oy = cx - BW[bname][0], cy - BW[bname][1]
    grid = [(c, r) for r in range(rows + 1) for c in range(cols + 1)]
    hull = [(c, 0) for c in range(cols + 1)] + [(cols, r) for r in range(1, rows + 1)] + \
           [(c, rows) for c in range(cols - 1, -1, -1)] + [(0, r) for r in range(rows - 1, 0, -1)]
    order = hull + [g for g in grid if g not in hull]
    ix = {g: i for i, g in enumerate(order)}
    uvs, verts = [], []
    for c, r in order:
        u, v = c / cols, r / rows
        uvs += [R(u), R(v)]; verts += [R(ox + (u - 0.5) * tw), R(oy + (0.5 - v) * th)]
    tris = []
    for r in range(rows):
        for c in range(cols):
            a, b_, c2, d = ix[(c, r)], ix[(c + 1, r)], ix[(c, r + 1)], ix[(c + 1, r + 1)]
            tris += [a, b_, d, a, d, c2]
    MESH_V[img] = order
    return {"type": "mesh", "uvs": uvs, "triangles": tris, "vertices": verts, "hull": len(hull), "width": tw, "height": th}

for n in LY["order"]:
    bn = PART_BONE[n]
    slot(n, bn, n)
    if n.startswith("wheel_rear"):
        put(n, n, region(n + "_", *center(n), b=bn, path=n + "_", seq=SEQ4))
    elif n.startswith("exhaust_pipe"):
        put(n, n, grid_mesh(n, bn))
    else:
        put(n, n, region(n, *center(n), b=bn))
for s_ in "LR":
    for i in (1, 2): slot(f"exsmoke_{s_}{i}", f"exsmoke_{s_}{i}", color="9a9aa0ff")
for s_ in "LR":
    slot(f"flame_glow_{s_}", f"tip_{s_}", blend="additive", color="ffffff00")
    put(f"flame_glow_{s_}", "flame_glow", region("flame_glow", scale=1.4, y=-30))
    slot(f"flame_{s_}", f"flame_{s_}")
    fw, fh = size("flame_1")
    put(f"flame_{s_}", "flame", region("flame_", path="flame_", scale=1.0, y=R(-fh * 1.0 / 2 + 6), seq={"count": 6, "start": 1, "digits": 1}))
for s_ in "LR":
    for i in (1, 2):
        put(f"dust_{s_}{i}", "smoke_round", region("smoke_round", scale=0.8))
        put(f"exsmoke_{s_}{i}", "smoke_wisps", region("smoke_wisps", scale=0.55, rot=90))
        put(f"exsmoke_{s_}{i}", "smoke_round", region("smoke_round", scale=0.32))
for nm, kind in debris:
    slot(nm, "d_" + nm); put(nm, kind, region(kind))
for i in range(4):
    slot(f"spark_{i + 1}", f"spark_{i + 1}", blend="additive"); put(f"spark_{i + 1}", "spark_small", region("spark_small", rot=-45))
slot("fire_cloud_1", "fire", "smoke_round", blend="additive", color="ff8a2a00"); put("fire_cloud_1", "smoke_round", region("smoke_round", scale=1.2, x=-30))
slot("fire_cloud_2", "fire", "smoke_soft", blend="additive", color="ffc04000"); put("fire_cloud_2", "smoke_soft", region("smoke_soft", scale=1.0, x=40, y=20))
slot("fire_puff", "fire", color="ffffff00"); put("fire_puff", "explosion_main", region("explosion_main", scale=0.9))
slot("fire_flash", "fire", blend="additive", color="ffd27a00"); put("fire_flash", "flame_glow", region("flame_glow", scale=7.0))
for i in range(6):
    slot(f"smoke_{i + 1}", f"smoke_{i + 1}", "smoke_soft" if i % 2 else "smoke_round", color="55555a00")
    put(f"smoke_{i + 1}", "smoke_soft" if i % 2 else "smoke_round", region("smoke_soft" if i % 2 else "smoke_round", scale=0.8))

# ---------------- key helpers ----------------
def k1(t, v, curve=None):
    e = {"value": R(v)}
    if t: e = {"time": R(t), **e}
    if curve: e["curve"] = curve
    return e
def k2(t, x, y, curve=None):
    e = {"x": R(x), "y": R(y)}
    if t: e = {"time": R(t), **e}
    if curve: e["curve"] = curve
    return e
def eo1(t0, v0, t1, v1):             # ease-out bezier (value timelines)
    dt, dv = t1 - t0, v1 - v0; return [R(t0 + dt * 0.12), R(v0 + dv * 0.55), R(t0 + dt * 0.45), R(v1)]
def eo2(t0, a, t1, b): return eo1(t0, a[0], t1, b[0]) + eo1(t0, a[1], t1, b[1])
def ck(t, hexa): return {"time": R(t), "color": hexa} if t else {"color": hexa}
def life(period, start, pts, rest):
    """pts: [(tau, value)] over a particle life; returns linear keys over [0,period] with wrap-around."""
    L = pts[-1][0]
    def ev(T):
        tau = (T - start) % period
        if tau > L: return rest
        for (a, va), (b, vb) in zip(pts, pts[1:]):
            if a <= tau <= b:
                f = 0 if b == a else (tau - a) / (b - a)
                return tuple(x + (y - x) * f for x, y in zip(va, vb))
        return pts[-1][1]
    ts = {R((start + tau) % period) for tau, _ in pts} | {0, period}
    sT = R(start % period)
    if sT > 0.002: ts.add(R(sT - 0.001))
    return [(T, ev(T)) for T in sorted(ts)]
def hexc(rgb, a): return "%02x%02x%02x%02x" % (*rgb, max(0, min(255, int(a * 255))))

def jitter(period, step, amp, seed):
    vals, s = [], seed
    n = int(round(period / step))
    for i in range(n):
        s = (s * 1103515245 + 12345) & 0x7fffffff
        vals.append(((s % 1000) / 500 - 1) * amp)
    vals.append(vals[0])
    return [(R(i * step), v) for i, v in enumerate(vals)]

# ---------------- IDLE (1.2s) ----------------
P = 1.2
idle = {"bones": {}, "slots": {}}
jx, jy = jitter(P, 0.05, 1.5, 3), jitter(P, 0.05, 1.5, 11)
idle["bones"]["engine"] = {"translate": [k2(t, x, y) for (t, x), (_, y) in zip(jx, jy)]}
sc = []
for i in range(4):
    t0 = i * 0.3
    sc += [k2(t0, 1, 1, [R(t0 + .04), 1, R(t0 + .08), 1.04, R(t0 + .04), 1, R(t0 + .08), 1.08]), k2(t0 + 0.12, 1.04, 1.08)]
sc.append(k2(P, 1, 1))
idle["bones"]["blower"] = {"scale": sc}
idle["bones"]["header_L"] = {"translate": [k2(t, 0, v * 0.4) for t, v in jitter(P, 0.1, 1, 5)]}
idle["bones"]["header_R"] = {"translate": [k2(t, 0, v * 0.4) for t, v in jitter(P, 0.1, 1, 9)]}
idle["bones"]["wing"] = {"translate": [k2(t, 0, v) for t, v in jitter(P, 0.1, 0.5, 21)]}
idle["attachments"] = {"default": {f"wheel_rear_{s}": {f"wheel_rear_{s}": {"sequence": [{"mode": "hold", "index": 0}]}} for s in "LR"}}
# idle exhaust smoke: soft lazy puffs from both pipes (2 per side)
idle["slots"] = {}
for s_, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        m = f"exsmoke_{s_}{i}"; st = (i - 1) * 0.6 + (0.3 if s_ == "R" else 0)
        idle["bones"][m] = {"translate": [k2(t, *v) for t, v in life(1.2, st, [(0, (0, 0)), (1.1, (sx * 22, -80))], (sx * 22, -80))],
                            "scale": [k2(t, *v) for t, v in life(1.2, st, [(0, (0.22, 0.22)), (1.1, (0.75, 0.75))], (0.75, 0.75))],
                            "rotate": [k1(0, 0), k1(1.2, sx * 25)]}
        idle["slots"][m] = {"attachment": [{"name": "smoke_round"}],
                            "rgba": [ck(t, hexc((215, 215, 222), v[0])) for t, v in life(1.2, st, [(0, (0,)), (0.15, (0.5,)), (0.6, (0.32,)), (1.1, (0,))], (0,))]}
for s_, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        m = f"exsmoke_{s_}{i}"; st = (i - 1) * 0.6 + (0.3 if s_ == "R" else 0)
        idle["bones"][m] = {"translate": [k2(t, *v) for t, v in life(1.2, st, [(0, (0, 0)), (1.1, (sx * 85, -120))], (sx * 85, -120))],
                            "scale": [k2(t, *v) for t, v in life(1.2, st, [(0, (0.7, 0.7)), (1.1, (2.4, 2.4))], (2.4, 2.4))],
                            "rotate": [k1(0, 0), k1(1.2, sx * -25)]}
        idle["slots"][m] = {"attachment": [{"name": "smoke_round"}],
                            "rgba": [ck(t, hexc((190, 190, 198), v[0])) for t, v in life(1.2, st, [(0, (0,)), (0.15, (0.85,)), (0.5, (0.55,)), (1.1, (0,))], (0,))]}
anims["idle"] = idle

# ---------------- RUN (0.96s) ----------------
P = 0.96
run = {"bones": {}, "slots": {}, "attachments": {"default": {}}}
A = run["attachments"]["default"]
for s in "LR":
    A[f"wheel_rear_{s}"] = {f"wheel_rear_{s}": {"sequence": [{"mode": "loop", "delay": 0.03}]}}
    A[f"flame_{s}"] = {"flame": {"sequence": [{"mode": "loop", "delay": 0.04, "index": 0 if s == "L" else 3}]}}
    run["slots"][f"flame_{s}"] = {"attachment": [{"name": "flame"}]}
    run["slots"][f"flame_glow_{s}"] = {"rgba": [ck(t, hexc((255, 255, 255), a)) for t, a in
                                               [(0, .9), (.08, .55), (.16, 1), (.24, .6), (.32, .95), (.4, .5), (.48, .9), (.56, .6), (.64, 1), (.72, .55), (.8, .9), (.88, .6), (.96, .9)]]}
    fl = []
    for i in range(12):
        t = i * 0.08; v = (1.15, 0.85, 1.25, 0.9)[i % 4] if s == "L" else (0.9, 1.2, 0.85, 1.25)[i % 4]
        fl.append(k2(t, 1 + (v - 1) * 0.3, v))
    fl.append(k2(P, *(fl[0]["x"], fl[0]["y"])))
    run["bones"][f"flame_{s}"] = {"scale": fl}
# wheels front: tiny shimmy
for b, sd in (("wheel_FL", 2), ("wheel_FR", 4)): run["bones"][b] = {"translate": [k2(t, v * .6, 0) for t, v in jitter(P, 0.06, 1, sd)]}
# wing vibrate
wr, wt = jitter(P, 0.04, 1.4, 31), jitter(P, 0.04, 2.0, 37)
run["bones"]["wing"] = {"rotate": [k1(t, v) for t, v in wr], "translate": [k2(t, 0, v) for t, v in wt]}
# engine harder shake + scoop pump
jx, jy = jitter(P, 0.04, 2.2, 41), jitter(P, 0.04, 2.2, 43)
run["bones"]["engine"] = {"translate": [k2(t, x, y) for (t, x), (_, y) in zip(jx, jy)]}
run["bones"]["blower"] = {"scale": [k2(R(i * 0.12), *((1, 1) if i % 2 == 0 else (1.05, 1.12))) for i in range(9)]}
run["bones"]["car"] = {"translate": [k2(R(i * 0.08), 0, (0, 1.2, 0, -1)[i % 4]) for i in range(13)]}
run["bones"]["susp_L"] = {"rotate": [k1(R(i * .08), (0, 1.5, 0, -1.5)[i % 4]) for i in range(13)]}
run["bones"]["susp_R"] = {"rotate": [k1(R(i * .08), (0, -1.5, 0, 1.5)[i % 4]) for i in range(13)]}
# dust bursts behind rear tires (tan), 2 puffs / tire
for s, sx in (("L", -1), ("R", 1)):
    for i in (1, 2):
        st = (i - 1) * 0.48 + (0.12 if s == "R" else 0)
        pts_t = [(0, (0, 0)), (0.6, (sx * 45, -150))]
        pts_s = [(0, (0.3, 0.3)), (0.6, (1.25, 1.1))]
        pts_a = [(0, (0,)), (0.06, (0.85,)), (0.6, (0,))]
        n = f"dust_{s}{i}"
        run["bones"][n] = {"translate": [k2(t, *v) for t, v in life(P, st, pts_t, (sx * 45, -150))],
                           "scale": [k2(t, *v) for t, v in life(P, st, pts_s, (1.25, 1.1))],
                           "rotate": [k1(0, i * 70), k1(P, i * 70 + sx * 40)]}
        run["slots"][n] = {"attachment": [{"name": "smoke_round"}],
                           "rgba": [ck(t, hexc((200, 168, 122), v[0])) for t, v in life(P, st, pts_a, (0,))]}
        m = f"exsmoke_{s}{i}"
        st2 = (i - 1) * 0.48 + 0.2
        run["bones"][m] = {"translate": [k2(t, *v) for t, v in life(P, st2, [(0, (0, 0)), (0.55, (sx * 30, -110))], (sx * 30, -110))],
                           "scale": [k2(t, *v) for t, v in life(P, st2, [(0, (0.3, 0.3)), (0.55, (1.0, 1.0))], (1, 1))]}
        run["slots"][m] = {"attachment": [{"name": "smoke_wisps"}],
                           "rgba": [ck(t, hexc((205, 205, 212), v[0])) for t, v in life(P, st2, [(0, (0,)), (0.05, (0.7,)), (0.55, (0,))], (0,))]}
anims["run"] = run

# ---------------- CRASH (2.8s, one-shot) ----------------
P = 2.8
cr = {"bones": {}, "slots": {}, "attachments": {"default": {}}}
cr["bones"]["car"] = {"translate": [k2(0, 0, 0), k2(.04, -12, -16), k2(.09, 8, -26), k2(.15, -5, -32), k2(.24, 3, -38), k2(.4, 0, -42, eo2(.4, (0, -42), .9, (0, -46))), k2(.9, 0, -46)],
                      "rotate": [k1(0, 0), k1(.05, 3), k1(.12, -4, eo1(.12, -4, .9, -9)), k1(.9, -9)]}
# scatter: (bone, dx, dy, rot, t_end, hop)
SC = [("wing", 30, 300, -75, 0.85, 1.3), ("blower", -200, 210, 230, 0.9, 1.35), ("header_L", -270, 60, -170, 0.8, 1.25),
      ("header_R", 260, 120, 190, 0.85, 1.25), ("susp_L", -240, 230, -130, 0.9, 1.2), ("susp_R", 230, 260, 150, 0.9, 1.2),
      ("wheel_FL", -320, 110, -45, 1.1, 1.15), ("wheel_FR", 320, 40, 40, 1.1, 1.15), ("engine", 25, 80, 20, 0.6, 1.12)]
import random
rnd = random.Random(6)
for nm, kind in debris:
    ang = rnd.uniform(-160, 160) + 90; dist = rnd.uniform(170, 380)
    SC.append(("d_" + nm, math.cos(math.radians(ang)) * dist, math.sin(math.radians(ang)) * dist, rnd.choice((-1, 1)) * rnd.uniform(200, 620), rnd.uniform(0.6, 1.1), rnd.uniform(1.2, 1.5)))
for i, (b, dx, dy, rot, te, hop) in enumerate(SC):
    d0 = 0.0 if b in ("wing", "engine") else 0.02 * (i % 5)
    cr["bones"][b] = {
        "translate": [k2(0, 0, 0), k2(d0, 0, 0, eo2(d0, (0, 0), te, (dx, dy))), k2(te, dx, dy), k2(te + .12, dx * 1.03, dy * 1.03)],
        "rotate": [k1(0, 0), k1(d0, 0, eo1(d0, 0, te + .12, rot)), k1(te + .12, rot)],
        "scale": [k2(0, 1, 1), k2(d0 + (te - d0) * 0.4, hop, hop), k2(te, 1, 1), k2(te + .06, 1.06, 1.06), k2(te + .12, 1, 1)]}
for nm, kind in debris:
    cr["slots"][nm] = {"attachment": [{"name": kind}], "rgba": [ck(0, "ffffff00"), ck(.07, "ffffffff")]}
# exhaust pipes bend (mesh deform): tip end swings outward + crumples up
for s, sx in (("L", -1), ("R", 1)):
    n = f"exhaust_pipe_{s}"; order = MESH_V[n]; rows = max(r for _, r in order)
    def bend(k):
        off = []
        for c, r in order:
            v = r / rows
            off += [R(sx * k * 70 * v ** 2), R(k * 40 * v ** 1.6 + k * 8 * math.sin(v * math.pi) * sx * 0)]
        return off
    cr["attachments"]["default"][n] = {n: {"deform": [{"vertices": bend(0)}, {"time": .08, "vertices": bend(0.6)},
                                                      {"time": .18, "vertices": bend(1.15)}, {"time": .3, "vertices": bend(0.95)}, {"time": .4, "vertices": bend(1.0)}]}}
    cr["bones"][f"exhaust_{s}"] = {"rotate": [k1(0, 0), k1(.12, sx * -6), k1(.3, sx * -4)]}
    cr["slots"][f"flame_{s}"] = {"attachment": [{"name": None}]}
    cr["attachments"]["default"][f"wheel_rear_{s}"] = {f"wheel_rear_{s}": {"sequence": [{"mode": "hold", "index": 1}]}}
# sparks
for i in range(4):
    n = f"spark_{i + 1}"; t0 = 0.02 * i
    cr["slots"][n] = {"attachment": [{"name": "spark_small"}, {"time": .45, "name": None}],
                      "rgba": [ck(0, "ffffff00"), ck(t0, "ffffffff"), ck(t0 + .06, "ffffff66"), ck(t0 + .12, "ffffffff"), ck(.42, "ffffff00")]}
    cr["bones"][n] = {"scale": [k2(0, .4, .4), k2(t0 + .1, 1.3, 1.3), k2(.42, .8, .8)]}
# big fire puff from engine then smoke
cr["slots"]["fire_puff"] = {"attachment": [{"name": "explosion_main"}, {"time": 1.3, "name": None}],
                            "rgba": [ck(0, "ffffff00"), ck(.05, "ffffffe6"), ck(.12, "ffffffff"), ck(.4, "fff0e0f0"),
                                     ck(.7, "ffd0b099"), ck(1.0, "c8a09040"), ck(1.25, "a0908000")]}
cr["slots"]["fire_flash"] = {"attachment": [{"name": "flame_glow"}, {"time": .6, "name": None}],
                             "rgba": [ck(0, "ffd27a00"), ck(.03, "ffe6a0ff"), ck(.12, "ffc060c0"), ck(.3, "ff904060"), ck(.55, "ff702000")]}
cr["bones"]["fire"] = {"scale": [k2(0, .15, .15, eo2(0, (.15, .15), .3, (1.05, 1.05))), k2(.3, 1.05, 1.05, eo2(.3, (1.05, 1.05), 1.25, (1.4, 1.4))), k2(1.25, 1.4, 1.4)]}
for j, (c0, t1) in enumerate((("ff8a2a", .9), ("ffc040", .7))):
    cr["slots"][f"fire_cloud_{j + 1}"] = {"rgba": [ck(0, c0 + "00"), ck(.05, c0 + "ee"), ck(.35, c0 + "aa"), ck(t1, c0 + "00")]}
for i in range(6):
    n = f"smoke_{i + 1}"; t0 = 0.3 + i * 0.13; te = min(P, t0 + 1.9)
    dx, dy = (-90, 60, -30, 120, -140, 40)[i], (140, 190, 230, 120, 180, 260)[i]
    cr["slots"][n] = {"rgba": [ck(0, "2a2a2e00"), ck(t0, "2a2a2e00"), ck(t0 + .25, "55555add"), ck(t0 + .9, "9a9aa0bb"), ck(te, "c4c4ca00")]}
    cr["bones"][n] = {"translate": [k2(0, 0, 0), k2(t0, 0, 0, eo2(t0, (0, 0), te, (dx, dy))), k2(te, dx, dy)],
                      "scale": [k2(0, .3, .3), k2(t0, .3, .3, eo2(t0, (.3, .3), te, (2.3, 2.3))), k2(te, 2.3, 2.3)],
                      "rotate": [k1(0, 0), k1(te, (-40, 30, -20, 50, -30, 25)[i])]}
# move flying parts above body (draw order key)
orig = [s["name"] for s in slots]
lift = ["blower_scoop", "engine_block", "header_cover_L", "header_cover_R", "susp_arm_L", "susp_arm_R", "wheel_front_L", "wheel_front_R", "wing_front"]
rest = [s for s in orig if s not in lift]
at = rest.index("flame_R") + 1
new = rest[:at] + lift + rest[at:]
cr["drawOrder"] = [{"offsets": [{"slot": s, "offset": new.index(s) - orig.index(s)} for s in sorted(lift, key=orig.index) if new.index(s) != orig.index(s)]}]
anims["crash"] = cr

# ---------------- WRECK (2s loop, play after crash; holds crash end pose) ----------------
P = 2.0
wk = {"bones": {}, "slots": {}, "attachments": {"default": {}}, "drawOrder": cr["drawOrder"]}
for b, dx, dy, rot, te, hop in SC:
    wk["bones"][b] = {"translate": [k2(0, dx * 1.03, dy * 1.03)], "rotate": [k1(0, rot)]}
wk["bones"]["car"] = {"translate": [k2(0, 0, -46)], "rotate": [k1(0, -9)]}
for nm, kind in debris: wk["slots"][nm] = {"attachment": [{"name": kind}]}
for s, sx in (("L", -1), ("R", 1)):
    n = f"exhaust_pipe_{s}"
    wk["attachments"]["default"][n] = {n: {"deform": [cr["attachments"]["default"][n][n]["deform"][-1] | {"time": 0}]}}
    wk["attachments"]["default"][n][n]["deform"][0].pop("time")
    wk["bones"][f"exhaust_{s}"] = {"rotate": [k1(0, sx * -4)]}
    wk["attachments"]["default"][f"wheel_rear_{s}"] = {f"wheel_rear_{s}": {"sequence": [{"mode": "hold", "index": 1}]}}
for i in range(6):
    n = f"smoke_{i + 1}"; st = i * P / 6
    wk["bones"][n] = {"translate": [k2(t, *v) for t, v in life(P, st, [(0, (0, 0)), (1.6, ((-50, 40, -20, 60, -60, 30)[i], 200))], (0, 200))],
                      "scale": [k2(t, *v) for t, v in life(P, st, [(0, (.3, .3)), (1.6, (1.3, 1.3))], (1.3, 1.3))]}
    wk["slots"][n] = {"rgba": [ck(t, hexc((120, 120, 128), v[0])) for t, v in life(P, st, [(0, (0,)), (.3, (.75,)), (1.6, (0,))], (0,))]}
anims["wreck"] = wk

# drop empty groups
for a in anims.values():
    for k in [k for k, v in a.items() if not v]: del a[k]

J = {"skeleton": {"hash": "car_special", "spine": "4.2.40", "x": -260, "y": -400, "width": 520, "height": 800, "images": "./images/", "audio": ""},
     "bones": [{"name": "root"}] + bones, "slots": slots, "skins": [{"name": "default", "attachments": att}], "animations": anims}
json.dump(J, open(os.path.join(D, "car.json"), "w"), indent=1)
print("bones", len(J["bones"]), "slots", len(slots), "anims", list(anims))
