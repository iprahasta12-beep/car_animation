# car-animation — Spine 4.2 + Pixi v8 (offline)

Car-crash theme. Top-down Spine cars on a PNG intersection (1920×1080). Open `car.json` in Spine 4.2, tweak, export, done.

## Rule
**Every visual = PNG. Every animation = Spine keys on PNG attachments.** No Graphics-drawn art, no code tweens on car parts.
Code only does 2 game-side things: set each car root x/y from `scene/placements.json` (drive in / drive through), and the HTML/CSS game UI bar.

## Folders
| path | what |
|------|------|
| `cars/<id>/car.json` + `car.atlas` + `car.png` | Spine 4.2 skeleton + packed atlas (runtime export) |
| `cars/<id>/images/` | Source PNGs for Spine editor (`"images": "./images/"`) |
| `cars/<id>/meta.json` / `thumb.png` | Label / description / order + card thumbnail |
| `cars/car_special/layout.json` | PSD layer bboxes (used by build script) |
| `scene/bg_landscape.png` | Intersection background 1920×1080 |
| `scene/placements.json` | Car scale + idle / hit / run path points per car (bg pixels) |
| `preview/index.html` | Offline preview. Double-click |
| `source_fx/` | Smoke clouds (your uploads) + reused crash fx (explosion, bolt, shard, debris, spark from win_fx) |
| `tools/` | Python rebuild scripts (optional) |

## Preview
- **Left panel** = Car A (drives from west): preview canvas (300px) + anim chips · **car select at the very bottom**.
- **Middle** = 16:9 game frame with the **game UI bar on the canvas** (bottom) → **UI state row** (Live / Normal / Hover / Click / Disabled + target button) → animation controls (IDLE / RUN / CRASH, pause, speed).
- **Right panel** = Car B (drives from south): preview canvas + anim chips · **car select at the very bottom**. (Load folder + keys list removed; keys still work: I / R / C / Enter / Space / . / Esc.)
- **Middle** = 16:9 game frame → **game UI bar row** → animation controls (IDLE / RUN / CRASH, pause, speed).
- **AUTO PLAY** opens a popover above the button (10 / 25 / 50 / 100 / 250 / 500, Cancel; outside click or Esc closes). While auto runs, SPIN shows the remaining count (18px on screen) + STOP (12px) (click = stop). Info / settings icons = your SVGs. SPIN button smaller (icon-first, label still readable).
- Car buttons: dashed = folder `cars/<id>/` not there yet. Default = `car_special` on both. Mode buttons / SPIN also sync both preview canvases.
- Car ids: `car_01`…`car_05` (to come), `car_special` = white hot rod.
- IDLE: cars wait before crosswalks. RUN: cars drive through, one after other. CRASH: both drive in, hit → `crash` → `wreck` loop.

### Game UI bar (HTML/CSS, design px at 1920×1080, scales with frame)
Info · Settings · BALANCE / WIN · BET − / + · AUTO PLAY · SPIN · TURBO.
- Works: − / + step bet (0.10 → 100, disabled at ends and during round). SPIN = bet off balance → 55% crash round (win × 1.5–25, count-up) / 45% run-through (no win) → idle. AUTO PLAY = repeat spins. TURBO = 2× speed. Spin icon rotates while busy.
- **UI state preview** (right panel): Live (real mouse hover / click) · Normal · Hover · Click · Disabled, on **All buttons** or one button (Info, Settings, Bet −, Bet +, Auto, Spin, Turbo).
- States in CSS: `:hover` / `:active` + forced classes `.f-hover` `.f-press` `.f-dis`; `.dis` = real disabled; `.on` = Auto / Turbo active.
- Keys: `I` idle · `R` run · `C` crash · `Enter` spin · `Space` pause · `.` step 1 frame.
- After exporting from Spine: `python3 tools/bake.py .` to refresh `data.js` (bakes cars + scene).

## Special (#6 white hot rod) — skeleton
Built from `special.psd` (1600×1600) at **50% scale**, origin = PSD (800,800), front = +Y. Draw order = PSD order. 59 bones, 65 slots, one `default` skin.

| anim | len | how (Spine keys only) |
|------|-----|------|
| `idle` | 1.2s loop | `engine` bone translate jitter ±1.5px every 0.05s (block + blower + headers ride on it). `blower` (intake scoop) scale pulse ×4. Headers / wing micro jitter. **Exhaust smoke**: 2 soft puffs / pipe drift back-outward, grow, fade (alpha keys). Rear tires sequence `hold` |
| `run` | 0.96s loop | `flame_L/R` = **sequence attachment** `flame_1…6` loop (0.04s) + scale flicker + additive `flame_glow`. Exhaust smoke wisps ×2/side. `wing` rotate ±1.4° + translate jitter every 0.04s. Rear tires = **sequence** `wheel_rear_*_1…4` loop 0.03s (tread scroll) + tan dust burst ×2/tire. Engine shake ±2.2, scoop pump, susp arm wiggle, car bounce, (no speed streaks) |
| `crash` | 2.8s one-shot | Car jolt + turn −9°. **Most debris**: wing, blower scoop, both headers, both susp arms, both front wheels, engine shove + 16 extra pieces (7 bolt, 5 shard, 4 debris_round) fly with spin + hop (scale) + settle. Exhaust pipes = **mesh 3×8, deform** bend outward + crumple. Big fire puff from engine: `explosion_main` alpha 0→1 in 0.05s, holds, tints warm, fades out over 1.2s while growing + additive `fire_flash` glow + 2 additive fire clouds (all alpha keyed, no hard show/hide). Debris fades in → 6 smoke puffs dark→light. 4 sparks. Draw-order key lifts flying parts above body. Flames off |
| `wreck` | 2s loop | Crash end pose held + smoke column from engine. Queue after `crash` |

Game code:
```js
car.state.setAnimation(0, "crash", false);
car.state.addAnimation(0, "wreck", true, 0);
// switching back: clearTracks() + skeleton.setToSetupPose() first (crash moves many bones)
```

Setup pose = clean car: flames / dust / smoke / debris hidden (no attachment or alpha 0).

## car_01 (red muscle car, twin stripes, hood scoop) — skeleton
From `car_01.psd` (1600×1600) at 50%, origin PSD (800,800), front = +Y. Built by `tools/prep_car.py` + `tools/build_car01.py` (helpers in `tools/carlib.py`).

| anim | len | how (Spine keys only) |
|------|-----|------|
| `idle` | 1.2s loop | `scoop` bone scale 1.00 → 1.04 pulse ×4 (engine rev). Body micro shake. Soft exhaust puffs from rear bumper |
| `run` | 0.8s loop | Twin stripe **shimmer sweep** each loop: 2 clipping rects (one per stripe) + additive `stripe_shine` PNG translating front → rear with alpha in/out. Dust bursts behind rear tires, scoop pump, car bounce. No white streaks |
| `crash` | 2.6s one-shot | Hood scoop pops + tilts (translate Y −10, rotate 20°, scale lift). Gray smoke ×7 from scoop (same as other cars, alpha keyed). Car jolt. Front bumper, both mirrors, 2 car_special parts ×2 fly. **Front-left top-view wheel tears off** and swaps to `wheel_loose` (your side-view wheel PNG) mid-air, spins, lands. Small fire flash + fireball (alpha in/out), sparks |
| `wreck` | 2s loop | Crash end pose held (loose wheel on ground, scoop tilted) + gray smoke from scoop |

Rebuild:
```
python3 tools/prep_car.py car_01.psd cars/car_01/images cars/car_01/layout.json source_fx/wheel_side.png=wheel_loose:150
python3 tools/build_car01.py cars/car_01
python3 tools/pack_atlas.py cars/car_01/images cars/car_01 car
python3 tools/bake.py .
```
(fx PNGs smoke/spark/explosion/flame_glow copied from car_special, debris `sp_*.png` copied by build script; `stripe_shine.png` generated. Run `tools/prune_images.py` after.)

## car_02 (blue muscle car, rear spoiler, wipers) — skeleton
From `car_02.psd` at 50%, origin PSD (800,800), front = +Y. `tools/prep_car.py` + `tools/build_car02.py`. Smoke / explosion / spark PNGs reused from car_special; debris = 2 car_special parts.

| anim | len | how (Spine keys only) |
|------|-----|------|
| `idle` | 2.4s loop | **Wipers one slow sweep** per loop: rotate 0 → 35° → 0 (ease in-out, R wiper 0.06s behind). Bones pivot at blade root. Spine value is −35 (clockwise = onto the glass). Soft exhaust puffs from rear, micro body shake |
| `run` | 0.8s loop | **Spoiler vibrates**: scale X 1.02 ↔ 0.98 + translate Y ±1 every 0.04s. Wiper flutter, dust behind rear tires, car bounce |
| `crash` | 2.6s one-shot | **Spoiler snaps off** (small jerk) → flies backward with 530° spin + hop scale → bounces → lands upside-down behind car (draw-order key lifts it on top). **Wipers flop to broken angles** (L ≈ 55°, R ≈ −106°, overshoot + settle). Fire flash + fireball at front (alpha in/out), sparks, car_special debris, gray smoke from hood, bumper + scoop knocked |
| `wreck` | 2s loop | Crash end pose held + smoke from hood |

Rebuild:
```
python3 tools/prep_car.py car_02.psd cars/car_02/images cars/car_02/layout.json
cp cars/car_special/images/{smoke_round,smoke_soft,spark_small,explosion_main,flame_glow}.png cars/car_02/images/
python3 tools/build_car02.py cars/car_02
python3 tools/pack_atlas.py cars/car_02/images cars/car_02 car
python3 tools/bake.py .
```

## car_03 (teal pickup, cream cab, spare tire in bed) — skeleton
From `car_03.psd` at 50%, origin PSD (800,800), front = +Y. `tools/prep_car.py` + `tools/build_car03.py`. Smoke / explosion / spark PNGs reused from car_special; debris = 2 car_special parts.

| anim | len | how (Spine keys only) |
|------|-----|------|
| `idle` | 1.2s loop | **Spare tire bounces** in the bed: translate Y +2 ↔ −2, 4 bounces per loop (ease). Micro body shake |
| `run` | 0.8s loop | **Spare jiggles harder** (X ±2.5, Y ±5.5, rotate ±4°, scale pop). **Dust puffs** behind both rear tires ×3 (tan, big, no exhaust). Off-road body shake + tilt, tailgate rattle |
| `crash` | 2.6s one-shot | **Spare tire launches** out of bed (hop scale 1.45) → lands behind the truck, bounces, rolls a little (rotate −540° total) and **stays lying on the ground** (also in `wreck`). **Tailgate deforms open** via mesh (6×3 grid, deform keys: bed edge swings back past hinge, twisted + bent, overshoot settle). Mirrors fly, hood buckles, fire flash + fireball, sparks, car_special debris, gray smoke, impact dust |
| `wreck` | 2s loop | Crash end pose held (tailgate open) + smoke from hood |

## car_04 (yellow compact, round & cute) — skeleton
From `car_04.psd` at 50%, origin PSD (800,800), front = +Y. `tools/prep_car.py` + `tools/fx_car04.py` (makes `light_glow.png` + `headlight_*_cracked.png`) + `tools/build_car04.py`. Body parts sit on a `body` bone (squash pivot); wheels stay unsquashed. Skeleton fps = 30.

| anim | len | how (Spine keys only) |
|------|-----|------|
| `idle` | 1.2s loop | **Bouncy squash**: `body` scale Y 1.00 → 1.04 (X 0.985) with overshoot + settle, ×2 per loop, small Y bob. **Headlights blink** (double blink): alpha keys on `headlight_L/R` slots + additive `headlight_glow` |
| `run` | 0.8s loop | **Cartoon bounce**: 4 hops per loop (squash 0.95 / stretch 1.07, Y hop, side wobble), mirrors flap. **Rear lights glow on**: additive red `tail_glow_L/R` (light_glow PNG tinted red) pulsing. Dust behind rear tires |
| `crash` | 2.6s one-shot | **Pancake squash**: `body` scale Y 0.8 (X 1.12) held exactly 2 frames → pops back (1.14 → 0.94 → 1.03 → 1). **Headlights swap to `headlight_*_cracked`** attachment at impact (glow flashes then dies). Tail lights flicker, mirrors fly, bumper knocked, small fireball + sparks, car_special debris, gray smoke |
| `wreck` | 2s loop | Cracked headlights, mirrors on ground, tail light dying flicker, smoke |

## car_05 (purple van / SUV, long cream roof) — skeleton
From `car_05.psd` at 50%, origin PSD (800,800), front = +Y, **fps 30**, **root scale 1.2 (20% bigger than the other cars)**.
`tools/prep_car.py` → `tools/fx_car04.py cars/car_05/images` (cracked headlight) → `tools/fx_car05.py cars/car_05` (`car_flash` white silhouette, `fx_dent`) → `tools/build_car05.py`.
Bones: `shake` → `car_main` → wheels + `body_bounce` → roof, bumpers, mirrors, rear doors (hinge pivots), lights. Events: `sfx_crash`, `crash_end`.

| anim | len | how (Spine keys only) |
|------|-----|------|
| `idle` | 2.4s loop | Slow, long roof shine sweep (additive `roof_shine` clipped to roof panel, front → rear 1.7s, then rest) |
| `run` | 0.8s loop | Heavy body roll: `body_bounce` shear X ±2° (sine) + sway, mirrors lean, dust |
| `crash` | 36 frames (1.2s) | f0 event `sfx_crash` + whole car flashes white 1 frame (`car_flash` PNG) · f0–2 `car_main` up 14px & snap back, `body_bounce` squash Y 0.92 / X 1.06 · f2–14 `car_main` rotate 0 → 70 → 55°, `shake` ±6px · f3 `fx_dent` on, headlight L → cracked + alpha flicker · f3–10 sparks, `bumper_front` flies (40px, 200°, alpha → 0) · f4–12 `roof` scale Y 0.95, rotate 3°, 4px offset · f6–16 `rear_door_L` opens 70° on hinge (−70 in Spine = outward) + bounce · f6–14 `mirror_R` flies (360°, alpha → 0) · f8–18 `wheel_FR` wobbles ±15°, out 8px · f14–28 settle to 50°, small body bounce · f12–36 hood smoke rises (alpha 0.4), all car slots tint to 80% grey · f36 hold, event `crash_end` |
| `wreck` | 2s loop | Crash end pose held (50°, grey, dent, cracked light, door open, bumper + mirror gone) + hood smoke (alpha 0.4) + occasional headlight flicker |

## Crash debris (car_01 – car_04)
Each car's crash debris = **2 random car_special parts** (picked once per car by `carlib.special_debris`, seeded by car id), 2 pieces of each, copied in as `images/sp_<part>.png`:

| car | debris parts |
|-----|------|
| car_01 | susp_arm_R, susp_arm_L |
| car_02 | header_cover_R, fender_rear_R |
| car_03 | header_cover_R, susp_arm_L |
| car_04 | susp_arm_R, header_cover_L |

Old bolt / shard debris removed from those cars (car_special keeps its own bolts / shards / rocks).

## Cleanup
`python3 tools/prune_images.py cars/<id>` deletes PNGs in `images/` that `car.json` never uses (then repack with `pack_atlas.py`). Run on all cars; `source_fx/streak.png` removed too (no speed streaks anymore).

## Add more cars
1. `cars/<id>/` with `car.json`, `car.atlas`, page png(s), optional `meta.json` + `thumb.png`.
2. `python3 tools/bake.py <car-animation root>` → appears in both panels. Anim names `idle / run / crash` (+ optional `wreck`) drive the middle controls.

## Rebuild Special from PSD (optional)
```
python3 tools/prep_special.py special.psd source_fx cars/car_special/images cars/car_special/layout.json
python3 tools/build_special.py cars/car_special
python3 tools/pack_atlas.py cars/car_special/images cars/car_special car
python3 tools/bake.py .
```
Needs `pip install psd-tools pillow numpy`. Rebuild overwrites hand edits in `car.json` — after you start animating in Spine, Spine is the source.

## Notes
- Tread scroll = 4 pre-rendered frames (tread period ~49px at 50%). Flames = 6 generated frames. Both are plain PNGs in `images/` — repaint freely, keep names.
- Smoke/dust PNGs are neutral white; color comes from slot tint.
- Exhaust pipe mesh is unweighted (deform keys). Add bones + weights in Spine if you want bone-driven bends.
