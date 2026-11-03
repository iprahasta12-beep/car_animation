// Offline car-crash preview. Data from data.js (window.CAR_DATA) or "Load folder". No fetch → works on file://
// Visuals = PNG only: background PNG + Spine cars (all car motion = Spine keys on PNG attachments).
// Code only sets each car root position from scene/placements.json (drive in / through) + the HTML game UI bar.
(async () => {
  const $ = (id) => document.getElementById(id);
  const toast = (t) => { const e = $("toast"); e.textContent = t; e.style.display = "block"; clearTimeout(toast.h); toast.h = setTimeout(() => (e.style.display = "none"), 2200); };
  const store = { get: (k) => { try { return localStorage.getItem(k); } catch { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch {} } };

  let DATA = window.CAR_DATA || { cars: [] };
  const SC = DATA.scene?.placements || { width: 1920, height: 1080, carScale: 0.2, A: { angle: 90, idle: [637, 542], hit: [883, 542], runFrom: [-120, 542], runTo: [2040, 542] }, B: { angle: 0, idle: [1008, 790], hit: [1008, 667], runFrom: [1008, 1200], runTo: [1008, -120] }, approach: 0.8, runSpeed: 1100, runOffsetB: 1.4 };
  const DW = SC.width, DH = SC.height;

  const app = new PIXI.Application();
  await app.init({ resizeTo: $("stage"), background: "#14161b", antialias: true, autoDensity: true, resolution: Math.min(2, window.devicePixelRatio || 1) });
  $("stage").prepend(app.canvas);
  const world = new PIXI.Container(); app.stage.addChild(world);
  const bg = new PIXI.Sprite(), carLayer = new PIXI.Container(), mask = new PIXI.Graphics();
  world.addChild(bg, carLayer, mask); carLayer.mask = mask;
  mask.rect(0, 0, DW, DH).fill(0xffffff);

  let pick = { A: store.get("car-A"), B: store.get("car-B") };
  let mode = "idle", speed = 1, playing = true, simT = 0, crashed = false;
  const cars = { A: null, B: null };
  const sdCache = {}, texCache = {};

  const SLOTS = ["car_01", "car_02", "car_03", "car_04", "car_05", "car_special"];
  const carById = (id) => DATA.cars.find((c) => c.id === id) || DATA.cars.find((c) => c.id === "car_special") || DATA.cars[0];
  const imgTex = (key, src) => new Promise((res, rej) => {
    if (texCache[key]) return res(texCache[key]);
    const img = new Image();
    img.onload = () => res((texCache[key] = PIXI.Texture.from(img)));
    img.onerror = () => rej(new Error("image decode failed: " + key));
    img.src = src;
  });
  async function skeletonData(c) {
    if (sdCache[c.id]) return sdCache[c.id];
    const atlas = new spine.TextureAtlas(c.atlas);
    for (const page of atlas.pages) {
      const src = c.images[page.name];
      if (!src) throw new Error(`Atlas page "${page.name}" missing (${c.id})`);
      page.setTexture(spine.SpineTexture.from((await imgTex(c.id + "/" + page.name, src)).source));
    }
    const json = typeof c.skeleton === "string" ? JSON.parse(c.skeleton) : c.skeleton;
    return (sdCache[c.id] = new spine.SkeletonJson(new spine.AtlasAttachmentLoader(atlas)).readSkeletonData(json));
  }

  function fit() {
    const w = app.screen.width, h = app.screen.height;
    const s = Math.min(w / DW, h / DH);
    const x = (w - DW * s) / 2, y = (h - DH * s) / 2;
    world.scale.set(s); world.position.set(x, y);
  }
  // game UI bar sits on the main canvas (1920×1080 design px), scaled with the frame
  function fitUI() {
    const w = app.screen.width, h = app.screen.height, s = Math.min(w / DW, h / DH);
    const ui = $("ui"); ui.style.transform = `translate(${(w - DW * s) / 2}px, ${(h - DH * s) / 2}px) scale(${s})`;
    ui.style.setProperty("--cnt", (18 / s).toFixed(2) + "px");       // auto counter = 18px on screen
    ui.style.setProperty("--cnt2", (12 / s).toFixed(2) + "px");
  }
  app.renderer.on("resize", fitUI);
  app.renderer.on("resize", fit);

  // ---------- side preview canvases (one per car) ----------
  const side = {};
  for (const k of ["A", "B"]) {
    const a = new PIXI.Application();
    await a.init({ resizeTo: $("pv" + k), backgroundAlpha: 0, antialias: true, autoDensity: true, resolution: Math.min(2, window.devicePixelRatio || 1) });
    $("pv" + k).prepend(a.canvas);
    side[k] = { app: a, spine: null, anim: "" };
    const lay = () => { const sp = side[k].spine; if (!sp) return; const w = a.screen.width, h = a.screen.height;
      sp.scale.set(Math.min(w / 1150, h / 1400)); sp.position.set(w / 2, h * 0.58); };
    side[k].layout = lay; a.renderer.on("resize", lay);
  }
  function sideTag(k) { const s = side[k]; $("tag" + k).innerHTML = s.spine ? `<b>${cars[k]?.id || ""}</b> · ${s.spine.state.getCurrent(0)?.animation?.name || "—"}` : ""; }
  function playSide(k, anim, loop, then) {
    const sp = side[k].spine; if (!sp || !sp.skeleton.data.findAnimation(anim)) return;
    sp.state.clearTracks(); sp.skeleton.setToSetupPose();
    sp.state.setAnimation(0, anim, loop);
    if (then && sp.skeleton.data.findAnimation(then)) sp.state.addAnimation(0, then, true, 0);
    sp.update(0); sideTag(k);
  }

  // ---------- cars ----------
  async function buildCars() {
    for (const k of ["A", "B"]) {
      const c = carById(pick[k]); if (!c) continue;
      pick[k] = c.id;
      if (cars[k]) { cars[k].spine.destroy(); cars[k] = null; }
      const sp = new spine.Spine({ skeletonData: await skeletonData(c), autoUpdate: false });
      sp.scale.set(SC.carScale); sp.angle = SC[k].angle;
      carLayer.addChild(sp);
      cars[k] = { id: c.id, spine: sp };
      if (side[k].spine) side[k].spine.destroy();
      const ss = new spine.Spine({ skeletonData: sp.skeleton.data, autoUpdate: false });
      side[k].app.stage.addChild(ss); side[k].spine = ss; side[k].layout();
    }
    renderPanels();
    setMode(mode, true);
  }
  const has = (k, a) => !!cars[k]?.spine.skeleton.data.findAnimation(a);
  function play(k, anim, loop, then) {
    const sp = cars[k]?.spine; if (!sp) return;
    sp.state.clearTracks(); sp.skeleton.setToSetupPose();
    if (!has(k, anim)) { toast(`${cars[k].id}: no "${anim}" anim`); return; }
    sp.state.setAnimation(0, anim, loop);
    if (then && has(k, then)) sp.state.addAnimation(0, then, true, 0);
    sp.update(0);
    playSide(k, anim, loop, then);
  }
  const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  const dist = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]);
  function place() {
    for (const k of ["A", "B"]) {
      const sp = cars[k]?.spine; if (!sp) continue;
      const P = SC[k];
      let p = P.idle;
      if (mode === "run") {
        const len = dist(P.runFrom, P.runTo) / SC.runSpeed, cyc = Math.max(dist(SC.A.runFrom, SC.A.runTo), dist(SC.B.runFrom, SC.B.runTo)) / SC.runSpeed + SC.runOffsetB;
        const t = ((simT - (k === "B" ? SC.runOffsetB : 0)) % cyc + cyc) % cyc;
        p = t <= len ? lerp(P.runFrom, P.runTo, t / len) : P.runTo;
      } else if (mode === "crash") {
        const u = Math.min(1, simT / SC.approach), e = u * u * (1.6 - 0.6 * u);
        const back = [P.hit[0] - (P.runTo[0] - P.runFrom[0]) * 0.3, P.hit[1] - (P.runTo[1] - P.runFrom[1]) * 0.3];
        p = lerp(back, P.hit, e);
      }
      sp.position.set(p[0], p[1]);
    }
    if (mode === "crash" && !crashed && simT >= SC.approach) { crashed = true; play("A", "crash", false, "wreck"); play("B", "crash", false, "wreck"); }
  }
  function setMode(m, force) {
    if (m === mode && !force && m !== "crash") return;
    mode = m; simT = 0; crashed = false;
    for (const k of ["A", "B"]) if (cars[k]) play(k, m === "crash" ? "run" : m, true);
    $("modes").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.m === m));
    place(); state();
  }
  function state() {
    const n = (k) => cars[k] ? carById(cars[k].id).label : "—";
    const cur = (k) => cars[k]?.spine.state.getCurrent(0)?.animation?.name || "—";
    $("state").innerHTML = `A <b>${n("A")}</b> · ${cur("A")} &nbsp;&nbsp; B <b>${n("B")}</b> · ${cur("B")}${playing ? "" : " &nbsp; (paused)"}`;
  }

  // ---------- side panels ----------
  function renderPanels() {
    const ids = DATA.cars.map((c) => c.id);
    const list = SLOTS.concat(ids.filter((id) => !SLOTS.includes(id)));
    for (const k of ["A", "B"]) {
      const host = $("pick" + k);
      host.innerHTML = list.map((id) => `<button data-id="${id}" class="${id === cars[k]?.id ? "on" : ""}${ids.includes(id) ? "" : " na"}" title="${ids.includes(id) ? id : id + " — not in cars/ yet"}">${id}</button>`).join("");
      host.querySelectorAll("button").forEach((b) => (b.onclick = () => {
        if (!ids.includes(b.dataset.id)) return toast(`${b.dataset.id}: add cars/${b.dataset.id}/ (car.json + atlas) → bake or Load folder`);
        pick[k] = b.dataset.id; store.set("car-" + k, pick[k]); buildCars();
      }));
      const sd = cars[k]?.spine.skeleton.data;
      $("anims" + k).innerHTML = sd ? sd.animations.map((a) => `<button data-a="${a.name}">${a.name}</button>`).join("") : "";
      $("anims" + k).querySelectorAll("button").forEach((b) => (b.onclick = () => {
        const a = b.dataset.a; playSide(k, a, a !== "crash", a === "crash" ? "wreck" : null);
      }));
    }
  }

  // ---------- top controls ----------
  $("modes").querySelectorAll("button").forEach((b) => (b.onclick = () => { stopRound(); setMode(b.dataset.m); }));
  function setPlaying(p) { playing = p; $("play").textContent = p ? "❚❚ Pause" : "▶ Play"; state(); }
  $("play").onclick = () => setPlaying(!playing);
  function setSpeed(s) { speed = s; $("speed").value = s; $("speedV").textContent = s.toFixed(2) + "x"; }
  $("speed").oninput = (e) => setSpeed(+e.target.value);
  $("speedChips").querySelectorAll("button").forEach((b) => (b.onclick = () => setSpeed(+b.dataset.s)));

  // ---------- game UI bar (HTML/CSS) ----------
  const BETS = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100];
  const ui = { bal: 1000, win: 0, bet: 3, auto: false, autoLeft: 0, turbo: false, busy: false };
  const fmt = (v) => "$" + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const btn = (n) => document.querySelector(`[data-ui="${n}"]`);
  function renderUI() {
    $("uBal").textContent = fmt(ui.bal); $("uWin").textContent = fmt(ui.win); $("uBet").textContent = fmt(BETS[ui.bet]);
    btn("minus").classList.toggle("dis", ui.bet === 0 || ui.busy);
    btn("plus").classList.toggle("dis", ui.bet === BETS.length - 1 || ui.busy);
    btn("spin").classList.toggle("busy", ui.busy);
    btn("auto").classList.toggle("on", ui.auto || $("autoPop").classList.contains("open"));
    btn("spin").classList.toggle("autoc", ui.auto);
    btn("spin").classList.toggle("dis", !ui.auto && !ui.busy && ui.bal < BETS[ui.bet]);
    $("autoCnt").textContent = ui.autoLeft;
    btn("turbo").classList.toggle("on", ui.turbo);
  }
  let round = null;   // { t, crash, winAmt }
  const tScale = () => (ui.turbo ? 2 : 1);
  function spin() {
    if (ui.busy || ui.bal < BETS[ui.bet]) return;
    ui.busy = true; ui.win = 0; ui.bal -= BETS[ui.bet];
    if (ui.auto) ui.autoLeft = Math.max(0, ui.autoLeft - 1);
    const crash = Math.random() < 0.55;
    const mult = crash ? [1.5, 2, 3, 5, 10, 25][Math.floor(Math.random() ** 2 * 6)] : 0;
    round = { t: 0, crash, winAmt: +(BETS[ui.bet] * mult).toFixed(2), end: crash ? 3.6 : 3.0, counted: false };
    setMode(crash ? "crash" : "run", true);
    renderUI();
  }
  function stopRound() { if (round) { round = null; ui.busy = false; renderUI(); } }
  function tickRound(dt) {
    if (!round) return;
    round.t += dt;
    if (round.crash && !round.counted && round.t > SC.approach + 0.6) {
      round.counted = true; const from = ui.win, to = round.winAmt, t0 = performance.now();
      const step = () => { const u = Math.min(1, (performance.now() - t0) / 900); ui.win = from + (to - from) * u; renderUI(); if (u < 1) requestAnimationFrame(step); };
      step();
    }
    if (round.t >= round.end) {
      if (round.crash) { ui.bal += round.winAmt; ui.win = round.winAmt; } else ui.win = 0;
      round = null; ui.busy = false; setMode("idle", true); renderUI();
      if (ui.auto && (ui.autoLeft <= 0 || ui.bal < BETS[ui.bet])) { ui.auto = false; renderUI(); }
      if (ui.auto) setTimeout(() => { if (ui.auto && !ui.busy) spin(); }, 450);
    }
  }
  const actions = {
    info: () => toast("Info: cars crash at the intersection = win."),
    settings: () => toast("Settings"),
    minus: () => { if (!ui.busy && ui.bet > 0) { ui.bet--; renderUI(); } },
    plus: () => { if (!ui.busy && ui.bet < BETS.length - 1) { ui.bet++; renderUI(); } },
    auto: () => { if (ui.auto) return stopAuto(); setPop(!$("autoPop").classList.contains("open")); },
    spin: () => (ui.auto ? stopAuto() : spin()),
    turbo: () => { ui.turbo = !ui.turbo; renderUI(); },
  };
  document.querySelectorAll("[data-ui]").forEach((b) => (b.onclick = () => { if (!b.classList.contains("dis")) actions[b.dataset.ui](); }));
  // auto play popover (anchored above AUTO PLAY, not a modal)
  function setPop(open) { $("autoPop").classList.toggle("open", open); renderUI(); }
  function stopAuto() { ui.auto = false; ui.autoLeft = 0; renderUI(); }
  $("autoPop").querySelectorAll("[data-n]").forEach((b) => (b.onclick = (e) => {
    e.stopPropagation(); setPop(false); ui.auto = true; ui.autoLeft = +b.dataset.n; renderUI(); if (!ui.busy) spin();
  }));
  $("autoCancel").onclick = (e) => { e.stopPropagation(); setPop(false); };
  document.addEventListener("pointerdown", (e) => { if (!e.target.closest(".autowrap")) setPop(false); });

  // UI state preview (force normal / hover / click / disabled on picked buttons)
  let uiSt = "live";
  function applyUIState() {
    const tgt = $("uiTarget").value;
    document.querySelectorAll("[data-ui]").forEach((b) => {
      b.classList.remove("f-hover", "f-press", "f-dis", "f-lock");
      if (uiSt === "live" || (tgt !== "all" && b.dataset.ui !== tgt)) return;
      b.classList.add("f-lock");
      if (uiSt !== "normal") b.classList.add("f-" + uiSt);
    });
    $("uiState").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x.dataset.st === uiSt));
  }
  $("uiState").querySelectorAll("button").forEach((b) => (b.onclick = () => { uiSt = b.dataset.st; applyUIState(); }));
  $("uiTarget").onchange = applyUIState;

  // ---------- loop / keys ----------
  function step(dt) {
    simT += dt; place(); tickRound(dt);
    for (const k of ["A", "B"]) { cars[k]?.spine.update(dt); side[k].spine?.update(dt); }
  }
  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    const k = e.key.toLowerCase();
    if (k === " ") { e.preventDefault(); setPlaying(!playing); }
    else if (k === "enter") { e.preventDefault(); ui.auto ? stopAuto() : spin(); }
    else if (k === "escape") setPop(false);
    else if (k === "i") { stopRound(); setMode("idle"); } else if (k === "r") { stopRound(); setMode("run"); } else if (k === "c") { stopRound(); setMode("crash"); }
    else if (k === ".") { setPlaying(false); step(1 / 30); state(); }
  });
  let last = 0;
  app.ticker.add((t) => {
    const dt = Math.min(0.05, t.deltaMS / 1000);
    if (playing) step(dt * speed * tScale());
    if ((last += t.deltaMS) > 200) { last = 0; state(); sideTag("A"); sideTag("B"); }
  });

  // ---------- boot ----------
  if (!DATA.cars.length) { $("state").textContent = "No cars. Run tools/bake.py."; return; }
  if (DATA.scene?.background) { bg.texture = await imgTex("scene/bg", DATA.scene.background); bg.width = DW; bg.height = DH; }
  fit(); fitUI(); renderUI();
  await buildCars();
  window.__preview = { setMode, cars, side, step, spin, ui };
})().catch((e) => { console.error(e); document.getElementById("state").textContent = "Error: " + e.message; });
