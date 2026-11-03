# Shared Spine 4.2 JSON helpers for car builders. Call setup(car_dir) first.
import sys, os, json, math
from PIL import Image

CX, CY = 800, 800
D = IMG = LY = S = None
def setup(d):
    global D, IMG, LY, S
    D = d; IMG = os.path.join(d, "images"); LY = json.load(open(os.path.join(d, "layout.json"))); S = LY["scale"]
    return LY                                   # PSD pixel = skeleton origin (car center)
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


# ---------------- crash debris taken from car_special parts ----------------
SP_PARTS = ["blower_scoop", "engine_block", "header_cover_L", "header_cover_R", "susp_arm_L", "susp_arm_R", "exhaust_pipe_L", "fender_rear_R"]
DSCALE = {}
def special_debris(seed, n_obj=2, per=2, target=80):
    """Pick n_obj random car_special parts (seeded by car id), copy them in as sp_<part>.png, return [(slot, attachment)]."""
    import random, shutil
    picks = random.Random(seed + "-debris").sample(SP_PARTS, n_obj)
    src = os.path.join(os.path.dirname(os.path.abspath(D)), "car_special", "images")
    out = []
    for p in picks:
        shutil.copy(os.path.join(src, p + ".png"), os.path.join(IMG, "sp_" + p + ".png"))
        base = target / max(size("sp_" + p))
        for k in range(per):
            nm = f"sp_{p}_{k + 1}"; DSCALE[nm] = round(base * (1, .72, .85)[k % 3], 3); out.append((nm, "sp_" + p))
    print("debris from car_special:", picks)
    return out
