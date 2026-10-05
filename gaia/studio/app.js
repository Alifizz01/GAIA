/* GAIA Studio - a thin client of the local GAIA REST API (gaia/api.py). */
"use strict";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const fmt = (v, d = 1) => (v == null || Number.isNaN(v) ? "—" : Number(v).toFixed(d));

async function api(name, body = {}) {
  const r = await fetch(`/api/${name}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

/* ------------------------------------------------------------ charts */
function makeChart(el, series, { xLabel = "", y2 = false, xDir = 1, bands = [] } = {}) {
  const axis = { stroke: css("--muted"), grid: { stroke: "#E4E9E5" }, ticks: { stroke: "#E4E9E5" }, font: `11px ${css("--f-num")}` };
  const axes = [{ ...axis, label: xLabel, labelFont: `11px ${css("--f-label")}`, labelSize: 22 }, { ...axis, size: 50 }];
  if (y2) axes.push({ ...axis, scale: "y2", side: 1, size: 50, grid: { show: false } });
  const chart = new uPlot({
    width: el.clientWidth, height: el.clientHeight,
    scales: { x: { time: false, dir: xDir } },
    legend: { show: true, live: false },
    cursor: { points: { size: 6 } },
    series: [{ label: xLabel }, ...series],
    axes,
    hooks: { drawAxes: [(u) => bands.forEach((b) => {
      const y = u.valToPos(b.y, "y", true);
      u.ctx.save(); u.ctx.strokeStyle = b.color; u.ctx.setLineDash([5, 4]); u.ctx.lineWidth = devicePixelRatio;
      u.ctx.beginPath(); u.ctx.moveTo(u.bbox.left, y); u.ctx.lineTo(u.bbox.left + u.bbox.width, y); u.ctx.stroke(); u.ctx.restore();
    })] },
  }, [[], ...series.map(() => [])], el);
  new ResizeObserver(() => chart.setSize({ width: el.clientWidth, height: el.clientHeight })).observe(el);
  return chart;
}

/* ------------------------------------------------------------ tabs */
$$(".tab").forEach((t) => (t.onclick = () => {
  $$(".tab").forEach((x) => x.setAttribute("aria-selected", x === t));
  $$(".page").forEach((p) => (p.hidden = p.id !== `page-${t.dataset.page}`));
  window.dispatchEvent(new Event("resize"));
}));

/* ============================================================ PACK */
const PACK = { running: false, speed: 60, selected: 0, timer: null, state: null };
const SPREAD = { 0: {}, 1: { capacity: 0.02, soc: 1.5, resistance: 0.05 }, 2: { capacity: 0.06, soc: 5, resistance: 0.15 } };
let chSoc, chVI, chT;

const TEMP_STOPS = [[20, [47, 143, 106]], [30, [141, 191, 74]], [40, [226, 179, 60]], [50, [224, 122, 47]], [60, [200, 65, 59]]];
function tempColor(c) {
  if (c <= TEMP_STOPS[0][0]) return `rgb(${TEMP_STOPS[0][1]})`;
  for (let i = 1; i < TEMP_STOPS.length; i++) {
    const [t1, c1] = TEMP_STOPS[i], [t0, c0] = TEMP_STOPS[i - 1];
    if (c <= t1) { const f = (c - t0) / (t1 - t0); return `rgb(${c0.map((v, k) => Math.round(v + f * (c1[k] - v)))})`; }
  }
  return `rgb(${TEMP_STOPS.at(-1)[1]})`;
}

function contactor(name, closed) {
  const blade = closed ? '<line x1="12" y1="9" x2="34" y2="9"/>' : '<line x1="12" y1="9" x2="32" y2="1"/>';
  return `<span class="contactor ${closed ? "closed" : ""}"><svg viewBox="0 0 46 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
    <line x1="1" y1="9" x2="12" y2="9"/>${blade}<line x1="34" y1="9" x2="45" y2="9"/><circle cx="12" cy="9" r="2" fill="currentColor"/><circle cx="34" cy="9" r="2" fill="currentColor"/></svg>${name} ${closed ? "closed" : "open"}</span>`;
}

function renderPack(s) {
  PACK.state = s;
  const cap = s.config.nominal_capacity;
  $("#p-pack-label").textContent = `${s.config.cells_in_series}s${s.config.cells_in_parallel}p · ${s.config.chemistry} · ${cap} Ah cells · t = ${(s.time / 60).toFixed(1)} min`;
  const tmax = Math.max(...s.cells.map((c) => c.temperature));
  $("#p-strip").innerHTML = `
    <div><b>BMS</b><span class="state ${s.state}">${s.state}</span>${contactor("DSG", s.discharge_contactor)}${contactor("CHG", s.charge_contactor)}</div>
    <div><b>Pack voltage</b><output>${fmt(s.pack_voltage)}<small>V</small></output></div>
    <div><b>Current</b><output>${fmt(s.pack_current)}<small>A</small></output><span class="muted mono">req ${fmt(s.requested_current, 0)} A</span></div>
    <div><b>SOC estimate</b><output>${fmt(s.soc_estimated)}<small>%</small></output><span class="muted mono">true ${fmt(s.soc_true)} %</span></div>
    <div><b>Hottest cell</b><output style="color:${tempColor(tmax)}">${fmt(tmax)}<small>°C</small></output></div>
    <div><b>Energy out</b><output>${fmt(s.energy_out_wh, 0)}<small>Wh</small></output><span class="muted mono">in ${fmt(s.energy_in_wh, 0)} Wh</span></div>
    <div><b>Faults</b><output style="font-size:13px;color:${s.latched.length ? css("--fail") : css("--muted")}">${s.latched.length ? s.latched.join(", ") : s.faults.length ? s.faults.join(", ") : "none"}</output></div>`;
  $("#p-cells").innerHTML = s.cells.map((c) => {
    const soc = Math.max(0, Math.min(100, c.soc));
    const flag = c.leak ? '<span class="flag short">SHORT</span>' : c.bleeding ? '<span class="flag bal">BAL</span>' : "";
    return `<div class="cell ${c.id === PACK.selected ? "sel" : ""} ${c.temperature > 45 ? "hot" : ""}" data-id="${c.id}" title="cell ${c.id + 1}: ${fmt(c.capacity)} Ah, BMS estimate ${fmt(c.soc_est)} %">
      <span class="cap"></span>
      <div class="can"><div class="fill" style="height:${soc}%;background:${tempColor(c.temperature)}"></div>${flag}<span class="soc ${soc < 14 ? "dark" : ""}">${fmt(c.soc, 0)}%</span></div>
      <div class="meta"><b>${fmt(c.voltage, 3)} V</b><br>${fmt(c.temperature)} °C</div></div>`;
  }).join("");
  $$("#p-cells .cell").forEach((el) => (el.onclick = () => { PACK.selected = +el.dataset.id; $("#p-sel").textContent = PACK.selected + 1; renderPack(PACK.state); }));
  const h = s.history;
  if (h.time) {
    const tm = h.time.map((t) => t / 60);
    chSoc.setData([tm, h.soc_estimated, h.soc_true]);
    chVI.setData([tm, h.pack_voltage, h.pack_current]);
    chT.setData([tm, h.temperature_true_max.map((k) => k - 273.15)]);
  }
  $("#p-events").innerHTML = s.events.slice().reverse().map((e) =>
    `<li class="${e.text.startsWith("TRIP") ? "trip" : ""}"><span>${(e.t / 60).toFixed(1)} min</span><span>${e.text}</span></li>`).join("") || '<li><span></span><span class="muted">Press Run.</span></li>';
}

async function packTick() {
  if (!PACK.running) return;
  try {
    if (PROFILE.kind === "manual") renderPack(await api("pack_step", { seconds: 0.25 * PACK.speed }));
    else await profileStep(0.25 * PACK.speed);
  } catch (e) { stopPack(); alertLine(e); }
  PACK.timer = setTimeout(packTick, 250);
}
function stopPack() { PACK.running = false; clearTimeout(PACK.timer); $("#p-run").textContent = "Run"; $("#p-run").classList.remove("stop"); }
function alertLine(e) { $("#p-events").insertAdjacentHTML("afterbegin", `<li class="trip"><span>error</span><span>${e.message}</span></li>`); }

async function buildPack() {
  stopPack();
  const s = await api("pack_reset", {
    cells_in_series: +$("#p-series").value, chemistry: $("#p-chem").value, nominal_capacity: +$("#p-cap").value,
    initial_soc: +$("#p-soc").value, cell_variation: SPREAD[$("#p-spread").value],
    ambient_temperature: 273.15 + +$("#p-amb").value,
  });
  await sendCurrent();
  renderPack(s);
}
async function sendCurrent() {
  $("#p-cur-v").textContent = `${$("#p-cur").value} A`;
  renderPack(await api("pack_command", { current: +$("#p-cur").value }));
}

function initPack() {
  chSoc = makeChart($("#p-chart-soc"), [
    { label: "BMS estimate %", stroke: css("--accent"), width: 2 },
    { label: "true %", stroke: css("--ink"), width: 1.4, dash: [6, 4] }], { xLabel: "time [min]" });
  chVI = makeChart($("#p-chart-vi"), [
    { label: "voltage V", stroke: css("--volt"), width: 2 },
    { label: "current A", stroke: css("--copper"), width: 1.6, scale: "y2" }], { xLabel: "time [min]", y2: true });
  chT = makeChart($("#p-chart-t"), [{ label: "hottest cell °C", stroke: css("--temp"), width: 2 }],
    { xLabel: "time [min]", bands: [{ y: 60, color: css("--fail") }, { y: 45, color: css("--warn") }] });
  $("#p-build").onclick = buildPack;
  $("#p-cur").oninput = () => ($("#p-cur-v").textContent = `${$("#p-cur").value} A`);
  $("#p-cur").onchange = sendCurrent;
  $$("[data-c]").forEach((b) => (b.onclick = () => { $("#p-cur").value = Math.round(+b.dataset.c * +$("#p-cap").value); sendCurrent(); }));
  $$("#p-speed button").forEach((b) => (b.onclick = () => {
    PACK.speed = +b.dataset.v; $$("#p-speed button").forEach((x) => x.setAttribute("aria-pressed", x === b));
  }));
  $("#p-run").onclick = () => {
    if (PACK.running) return stopPack();
    PACK.running = true; $("#p-run").textContent = "Pause"; $("#p-run").classList.add("stop"); packTick();
  };
  $$("[data-f]").forEach((b) => (b.onclick = async () => renderPack(await api("pack_fault", { cell: PACK.selected, kind: b.dataset.f }))));
  $("#p-reset").onclick = async () => renderPack(await api("pack_reset_fault"));
  buildPack();
}

/* ============================================================ CELL LAB */
const RUN_COLORS = ["#0E7C66", "#2F6FDE", "#B8642A", "#8A5CD6", "#C8413B", "#1F2933", "#D9822B"];
const CELL = { runs: [] };
let chCellV, chCellT;

function drawCellRuns() {
  const host = $("#c-chart-v"), hostT = $("#c-chart-t");
  [chCellV, chCellT].forEach((c) => c && c.destroy());
  host.innerHTML = ""; hostT.innerHTML = "";
  const col = (i) => RUN_COLORS[i % RUN_COLORS.length];
  chCellV = makeChart(host, CELL.runs.map((r, i) => ({ label: r.label, stroke: col(i), width: 2, spanGaps: true })), { xLabel: "state of charge [%]", xDir: -1 });
  chCellT = makeChart(hostT, CELL.runs.map((r, i) => ({ label: r.label, stroke: col(i), width: 2, spanGaps: true })), { xLabel: "time [min]" });
  if (CELL.runs.length) {
    chCellV.setData(uPlot.join(CELL.runs.map((r) => { const idx = r.soc.map((_, k) => k).sort((a, b) => r.soc[a] - r.soc[b]); return [idx.map((k) => r.soc[k]), idx.map((k) => r.voltage[k])]; })));
    chCellT.setData(uPlot.join(CELL.runs.map((r) => [r.t.map((t) => t / 60), r.temperature])));
  }
  $("#c-table tbody").innerHTML = CELL.runs.map((r, i) => `<tr><td><span class="swatch" style="background:${col(i)}"></span>${r.label}</td>
    <td class="num">${fmt(r.capacity, 2)} Ah</td><td class="num">${fmt(r.t.at(-1) / 60, 0)} min</td><td class="num">${fmt(Math.min(...r.voltage), 2)} V</td><td class="num">${fmt(Math.max(...r.temperature), 1)} °C</td></tr>`).join("");
}

function initCell() {
  $("#c-rate").oninput = () => ($("#c-rate-v").textContent = `${$("#c-rate").value} C`);
  $("#c-run").onclick = async () => {
    $("#c-run").disabled = true; $("#c-status").textContent = "Solving the electrochemistry…";
    try {
      const r = await api("cell_simulate", { chemistry: $("#c-chem").value, model: $("#c-model").value, c_rate: +$("#c-rate").value,
        thermal: $("#c-thermal").checked, temperature_c: +$("#c-temp").value });
      CELL.runs.push(r); drawCellRuns(); $("#c-status").textContent = `${r.label}: done.`;
    } catch (e) { $("#c-status").innerHTML = `<span class="err">${e.message}</span>`; }
    $("#c-run").disabled = false;
  };
  $("#c-clear").onclick = () => { CELL.runs = []; drawCellRuns(); };
  drawCellRuns();
}

/* ============================================================ SOC LAB */
const SOC_COLORS = { COULOMB_COUNTING: "#B8642A", KALMAN_FILTER: "#2F6FDE", AEKF: "#0E7C66" };
const SOC_NAMES = { COULOMB_COUNTING: "Coulomb counting", KALMAN_FILTER: "Extended Kalman filter", AEKF: "Adaptive EKF" };
let chS, chSI;

function initSoc() {
  chS = makeChart($("#s-chart"), [{ label: "true SOC", stroke: "#13201B", width: 2.4 },
    ...Object.keys(SOC_COLORS).map((k) => ({ label: SOC_NAMES[k], stroke: SOC_COLORS[k], width: 1.8 }))], { xLabel: "time [min]" });
  chSI = makeChart($("#s-chart-i"), [{ label: "cell current A", stroke: css("--copper"), width: 1.4 }], { xLabel: "time [min]" });
  $("#s-guess").oninput = () => ($("#s-guess-v").textContent = `${$("#s-guess").value} %`);
  $("#s-run").onclick = runSoc;
  runSoc();
}
async function runSoc() {
  $("#s-run").disabled = true; $("#s-status").textContent = "Running PyBaMM truth and three estimators…";
  try {
    const r = await api("soc_benchmark", { chemistry: $("#s-chem").value, initial_soc_guess: +$("#s-guess").value,
      voltage_noise: +$("#s-vnoise").value / 1000, current_offset: +$("#s-offset").value / 100 });
    const tm = r.t.map((t) => t / 60);
    chS.setData([tm, r.soc_true, ...Object.keys(SOC_COLORS).map((k) => r.estimates[k])]);
    chSI.setData([tm, r.current]);
    const worst = Math.max(...Object.values(r.rmse_after_10min), 1);
    $("#s-meters").innerHTML = Object.keys(SOC_COLORS).map((k) => `<div class="meter"><b>${SOC_NAMES[k]}</b>
      <output style="color:${SOC_COLORS[k]}">${fmt(r.rmse_after_10min[k], 2)}<small style="font-size:13px"> % RMSE</small></output>
      <div class="barline"><i style="width:${(100 * r.rmse_after_10min[k]) / worst}%;background:${SOC_COLORS[k]}"></i></div>
      <span class="muted" style="font-size:12px">after 10 min · end error ${fmt(r.final_error[k], 2)} %</span></div>`).join("");
    $("#s-status").textContent = `${r.chemistry}, ${fmt(r.capacity, 2)} Ah cell, start guess ${r.conditions.initial_soc_guess} % (truth 100 %).`;
  } catch (e) { $("#s-status").innerHTML = `<span class="err">${e.message}</span>`; }
  $("#s-run").disabled = false;
}

/* ------------------------------------------------------------ boot */
async function health() {
  try {
    const i = await api("info"); $("#conn").className = "dot ok"; $("#conn-text").textContent = `API ${location.host} · v${i.version}`;
  } catch { $("#conn").className = "dot"; $("#conn-text").textContent = "API not reachable"; }
}
initPack(); initCell(); initSoc(); health(); setInterval(health, 5000);


/* ============================================================ CONDITIONS: ambient and load profiles */
// Synthetic test profiles in C-rate (fraction of the pack's Ah capacity). They are not a
// standard drive cycle; they exist to exercise the BMS with pulses and regenerative charge.
const PROFILE = { kind: "manual" };
const PROFILES = {
  pulse: { hint: "Pulsed: 1.8C for 10 s, rest for 20 s, repeating. Above the BMS limit (100 A discharge) it trips: that is the protection working.",
           segs: [[10, 1.8], [20, 0]] },
  drive: { hint: "Drive cycle (synthetic, 120 s): accelerate at 1.8C, cruise, regenerative braking down to -0.8C, stop. On a pack big enough that 1.8C exceeds 100 A, the BMS trips.",
           segs: [[10, 1.8], [40, 0.6], [8, -0.5], [10, 0], [12, 1.4], [30, 1.0], [10, -0.8]] },
};
function packAh() { const c = PACK.state ? PACK.state.config : { nominal_capacity: +$("#p-cap").value, cells_in_parallel: 1 }; return c.nominal_capacity * (c.cells_in_parallel || 1); }
function profileAt(t) {   // [current in A, seconds until the next change]
  const segs = PROFILES[PROFILE.kind].segs, period = segs.reduce((a, s) => a + s[0], 0);
  let x = t % period;
  for (const [d, c] of segs) { if (x < d) return [c * packAh(), d - x]; x -= d; }
  return [0, 1];
}
async function profileStep(seconds) {
  // step exactly to each segment boundary, so a fast playback speed does not smear the profile
  let left = seconds, s = PACK.state;
  while (left > 1e-6) {
    const [amps, untilChange] = profileAt(s ? s.time : 0);
    const dt = Math.max(0.5, Math.min(left, untilChange));
    await api("pack_command", { current: amps });
    s = await api("pack_step", { seconds: dt });
    left -= dt;
    $("#p-cur").value = Math.round(amps); $("#p-cur-v").textContent = `${Math.round(amps)} A (profile)`;
  }
  renderPack(s);
}
$$("#p-profile button").forEach((b) => (b.onclick = () => {
  PROFILE.kind = b.dataset.v;
  $$("#p-profile button").forEach((x) => x.setAttribute("aria-pressed", x === b));
  $("#p-profile-hint").textContent = PROFILE.kind === "manual" ? "Manual: the current slider above sets the load." : PROFILES[PROFILE.kind].hint;
  $("#p-cur").disabled = PROFILE.kind !== "manual";
}));
$("#p-amb").oninput = () => ($("#p-amb-v").textContent = `${$("#p-amb").value} °C`);
$("#p-amb").onchange = async () => renderPack(await api("pack_command", { current: +$("#p-cur").value, ambient: 273.15 + +$("#p-amb").value }));

/* ============================================================ SYSTEM SCHEMATIC */
// Draws only what /api/pack_state reports: contactor states, pack current and voltage, every cell's
// SOC, temperature, balancing and short flags, the BMS state. The motion is the measured current.
const SYS = { phase: 0, last: performance.now(), rot: 0 };
function sysContactor(g, x, y, closed, label, latched) {
  g.strokeStyle = closed ? css("--copper") : latched ? css("--fail") : css("--muted"); g.fillStyle = g.strokeStyle; g.lineWidth = 2.4;
  g.beginPath(); g.arc(x - 14, y, 3.2, 0, 7); g.fill(); g.beginPath(); g.arc(x + 14, y, 3.2, 0, 7); g.fill();
  g.beginPath(); g.moveTo(x - 14, y); closed ? g.lineTo(x + 14, y) : g.lineTo(x + 11, y - 14); g.stroke();
  g.font = `600 11px ${css("--f-label")}`; g.textAlign = "center";
  g.fillText(`${label} ${closed ? "CLOSED" : "OPEN"}`, x, y + 22); g.textAlign = "left";
}
function sysBox(g, x, y, w, h, title, sub, active) {
  g.fillStyle = active ? "#F4FAF7" : css("--sunk"); g.strokeStyle = active ? css("--accent") : css("--rule"); g.lineWidth = 1.5;
  g.beginPath(); g.roundRect(x, y, w, h, 8); g.fill(); g.stroke();
  g.fillStyle = css("--ink"); g.font = `600 12px ${css("--f-label")}`; g.textAlign = "center";
  g.fillText(title, x + w / 2, y + 18);
  g.fillStyle = css("--muted"); g.font = `11px ${css("--f-num")}`; g.fillText(sub, x + w / 2, y + h - 10); g.textAlign = "left";
}
function drawSystem(now) {
  requestAnimationFrame(drawSystem);
  const cv = $("#p-system"), s = PACK.state;
  if (!cv || !s || cv.offsetParent === null) return;
  const dpr = devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight;
  if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
  const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
  const dt = Math.min(0.05, (now - SYS.last) / 1000); SYS.last = now;
  const I = s.pack_current, V = s.pack_voltage, amb = s.ambient_c;
  const regen = I < -0.05 && PROFILE.kind === "drive", charging = I < -0.05 && !regen, discharging = I > 0.05;
  const yb = H * 0.38;                                        // the power path
  const xCh = 14, wCh = 96, xChg = 160, xP0 = 214, xP1 = W - 300, xDsg = W - 250, xInv = W - 200, wInv = 92, xMot = W - 50;
  const latched = s.latched.length > 0;

  // wires
  g.strokeStyle = css("--copper"); g.lineWidth = 3;
  g.beginPath(); g.moveTo(xCh + wCh, yb); g.lineTo(xChg - 14, yb); g.moveTo(xChg + 14, yb); g.lineTo(xP0, yb);
  g.moveTo(xP1, yb); g.lineTo(xDsg - 14, yb); g.moveTo(xDsg + 14, yb); g.lineTo(xInv, yb);
  g.moveTo(xInv + wInv, yb); g.lineTo(xMot - 26, yb); g.stroke();

  // moving charge carriers: speed from the measured current, direction from its sign
  SYS.phase += dt * Math.min(220, 25 + Math.abs(I) * 1.6);
  const dots = (x0, x1, dir) => {
    g.fillStyle = css("--copper");
    const L = x1 - x0;
    for (let k = 0; k < L; k += 22) { const x = dir > 0 ? x0 + ((k + SYS.phase) % L) : x1 - ((k + SYS.phase) % L); g.beginPath(); g.arc(x, yb, 3, 0, 7); g.fill(); }
  };
  if (charging && s.charge_contactor) { dots(xCh + wCh, xChg - 14, 1); dots(xChg + 14, xP0, 1); }
  if (discharging && s.discharge_contactor) { dots(xP1, xDsg - 14, 1); dots(xDsg + 14, xInv, 1); dots(xInv + wInv, xMot - 26, 1); }
  if (regen && s.discharge_contactor) { dots(xP1, xDsg - 14, -1); dots(xDsg + 14, xInv, -1); dots(xInv + wInv, xMot - 26, -1); }

  // charger, contactors, inverter, motor
  sysBox(g, xCh, yb - 34, wCh, 68, "Charger", charging ? `${fmt(-I, 1)} A in` : "idle", charging);
  sysContactor(g, xChg, yb, s.charge_contactor, "CHG", latched && !s.charge_contactor);
  sysContactor(g, xDsg, yb, s.discharge_contactor, "DSG", latched && !s.discharge_contactor);
  sysBox(g, xInv, yb - 34, wInv, 68, "Inverter", regen ? "regen" : discharging ? `${fmt(I * V / 1000, 2)} kW` : "idle", discharging || regen);
  if (discharging || regen) SYS.rot += dt * (regen ? -1 : 1) * (2 + Math.abs(I) * 0.12);
  g.strokeStyle = css("--ink"); g.lineWidth = 2; g.beginPath(); g.arc(xMot, yb, 24, 0, 7); g.stroke();
  for (let k = 0; k < 3; k++) { const a = SYS.rot + k * 2.094; g.beginPath(); g.moveTo(xMot, yb); g.lineTo(xMot + 18 * Math.cos(a), yb + 18 * Math.sin(a)); g.stroke(); }
  g.fillStyle = css("--ink"); g.font = `600 12px ${css("--f-label")}`; g.textAlign = "center"; g.fillText("Motor", xMot, yb + 44); g.textAlign = "left";

  // the pack: series string of cells, each filled to its SOC and coloured by its temperature
  const n = s.cells.length, pw = xP1 - xP0, cw = Math.min(30, (pw - 20) / n - 4), gap = (pw - 20 - n * cw) / Math.max(1, n - 1);
  g.fillStyle = "#FBFCFB"; g.strokeStyle = css("--rule"); g.lineWidth = 1.5;
  g.beginPath(); g.roundRect(xP0, yb - 48, pw, 112, 10); g.fill(); g.stroke();
  const cy0 = yb - 34, ch = 70;
  s.cells.forEach((c, i) => {
    const x = xP0 + 10 + i * (cw + gap);
    g.fillStyle = css("--sunk"); g.strokeStyle = c.leak ? css("--fail") : css("--rule"); g.lineWidth = c.leak ? 2.5 : 1;
    g.beginPath(); g.roundRect(x, cy0, cw, ch, 4); g.fill(); g.stroke();
    const f = Math.max(0, Math.min(1, c.soc / 100));
    g.fillStyle = tempColor(c.temperature); g.fillRect(x + 2, cy0 + ch - 2 - f * (ch - 4), cw - 4, f * (ch - 4));
    g.strokeStyle = css("--ink"); g.lineWidth = 1.5;                      // BMS estimate as a tick
    const ye = cy0 + ch - 2 - Math.max(0, Math.min(1, c.soc_est / 100)) * (ch - 4);
    g.beginPath(); g.moveTo(x - 2, ye); g.lineTo(x + cw + 2, ye); g.stroke();
    if (c.bleeding) { g.fillStyle = css("--warn"); g.font = `600 9px ${css("--f-label")}`; g.fillText("BAL", x + cw / 2 - 8, cy0 - 4); }
    if (c.temperature > amb + 8) {                                       // warmer than the air: heat leaves the cell
      g.strokeStyle = tempColor(c.temperature); g.lineWidth = 1.2;
      for (let k = 0; k < 2; k++) { const xx = x + cw * (0.3 + 0.4 * k), yy = cy0 - 8 - ((now / 40 + k * 7) % 14);
        g.beginPath(); g.moveTo(xx, yy + 6); g.quadraticCurveTo(xx + 3, yy + 3, xx, yy); g.stroke(); }
    }
    g.strokeStyle = "rgba(93,107,100,0.35)"; g.lineWidth = 1;            // sense wire to the BMS
    g.beginPath(); g.moveTo(x + cw / 2, cy0 + ch); g.lineTo(x + cw / 2, yb + 74); g.stroke();
  });
  g.fillStyle = css("--muted"); g.font = `11px ${css("--f-num")}`;
  g.fillText(`${n}s · ${fmt(V, 1)} V · ${fmt(I, 1)} A`, xP0 + 10, yb + 60);
  // BMS board under the pack
  const bx = xP0 + 40, bw = pw - 80, by = yb + 74;
  const st = s.state, col = latched ? css("--fail") : st === "idle" ? css("--muted") : css("--accent");
  g.fillStyle = "#EAF3EE"; g.strokeStyle = col; g.lineWidth = 1.5; g.beginPath(); g.roundRect(bx, by, bw, 42, 8); g.fill(); g.stroke();
  g.fillStyle = col; g.font = `700 12px ${css("--f-label")}`; g.textAlign = "center";
  g.fillText(`BMS · ${st.toUpperCase()}`, bx + bw / 2, by + 17);
  g.fillStyle = css("--ink"); g.font = `11px ${css("--f-num")}`;
  g.fillText(`SOC estimate ${fmt(s.soc_estimated, 1)} %  ·  true ${fmt(s.soc_true, 1)} %${latched ? "  ·  LATCHED: " + s.latched.join(", ") : ""}`, bx + bw / 2, by + 33);
  g.textAlign = "left";

  // ambient
  g.fillStyle = css("--muted"); g.font = `11px ${css("--f-num")}`;
  g.fillText(`ambient ${fmt(amb, 0)} °C${regen ? "  ·  regenerative braking" : ""}`, 14, H - 12);
  g.textAlign = "right"; g.fillText("cell fill = true SOC · black tick = BMS estimate · colour = temperature", W - 14, H - 12); g.textAlign = "left";
}
requestAnimationFrame(drawSystem);
