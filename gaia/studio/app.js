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
  try { renderPack(await api("pack_step", { seconds: 0.25 * PACK.speed })); } catch (e) { stopPack(); alertLine(e); }
  PACK.timer = setTimeout(packTick, 250);
}
function stopPack() { PACK.running = false; clearTimeout(PACK.timer); $("#p-run").textContent = "Run"; $("#p-run").classList.remove("stop"); }
function alertLine(e) { $("#p-events").insertAdjacentHTML("afterbegin", `<li class="trip"><span>error</span><span>${e.message}</span></li>`); }

async function buildPack() {
  stopPack();
  const s = await api("pack_reset", {
    cells_in_series: +$("#p-series").value, chemistry: $("#p-chem").value, nominal_capacity: +$("#p-cap").value,
    initial_soc: +$("#p-soc").value, cell_variation: SPREAD[$("#p-spread").value],
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
