"use strict";

const state = {
  runs: new Map(),
  selectedRunId: null,
  logLen: 0,
  pollTimer: null,
  listTimer: null,
  animator: null,
  network: null,
  stationDist: null, // station code -> cumulative km
  trainWaypoints: null, // train_id -> {type, points:[[tMs,km],...], tMin, tMax}
  timeDomain: null, // [minMs, maxMs]
  nowMs: 0,
  playing: false,
  rafId: null,
  lastFrameTs: null,
  selectedScheduleTrain: null,
};

const $ = (sel) => document.querySelector(sel);

// ---------- bootstrap ----------

async function loadMeta() {
  const res = await fetch("/api/meta");
  const meta = await res.json();
  const sel = $("#f-dataset");
  sel.innerHTML = "";
  for (const name of meta.datasets) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    sel.appendChild(opt);
  }
}

function fmtTime(t) {
  if (!t) return "--";
  return new Date((t.created_at || t) * 1000).toLocaleTimeString();
}

function fmtDuration(run) {
  if (!run.started_at) return "";
  const end = run.finished_at || Date.now() / 1000;
  const secs = Math.max(0, end - run.started_at);
  if (secs < 60) return `${secs.toFixed(0)}s`;
  return `${(secs / 60).toFixed(1)}m`;
}

async function refreshRunsList() {
  const res = await fetch("/api/runs");
  const rows = await res.json();
  const list = $("#runs-list");
  list.innerHTML = "";
  for (const run of rows) {
    state.runs.set(run.id, run);
    const el = document.createElement("div");
    el.className = "run-row" + (run.id === state.selectedRunId ? " selected" : "");
    el.innerHTML = `
      <div class="run-title">${run.config.corridor_dataset}</div>
      <div class="run-sub">
        <span class="badge ${run.state}">${run.state}</span>
        <span>${run.config.network_section}</span>
        <span>${fmtDuration(run)}</span>
      </div>`;
    el.addEventListener("click", () => selectRun(run.id));
    list.appendChild(el);
  }
  if (!state.listTimer) {
    state.listTimer = setInterval(refreshRunsList, 2000);
  }
}

// ---------- run submission ----------

function collectConfig() {
  const autoblock = $("#f-autoblock").value.split(",").map((s) => s.trim()).filter(Boolean);
  const startMode = $("#f-start-mode").value;
  const cfg = {
    corridor_dataset: $("#f-dataset").value,
    network_section: $("#f-corridor").value,
    use_halt_deviation: $("#f-halt-dev").checked,
    use_speed_randomness: $("#f-speed-rand").checked,
    start_dt_mode: startMode,
    start_dt_buffer_minutes: Number($("#f-buffer").value),
    chart_duration_hrs: Number($("#f-duration").value),
    headway_distance: Number($("#f-headway").value),
    goods_max_priority_wait_hours: Number($("#f-goods-wait").value),
    halt_deviation_seed: Number($("#f-seed-halt").value),
    speed_randomness_seed: Number($("#f-seed-speed").value),
    autoblock_stations: autoblock,
  };
  if (startMode === "manual") {
    cfg.start_dt_manual = $("#f-start-manual").value;
  }
  return cfg;
}

async function submitRun(ev) {
  ev.preventDefault();
  const btn = $("#run-btn");
  btn.disabled = true;
  try {
    const res = await fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectConfig()),
    });
    const body = await res.json();
    if (!res.ok) {
      alert(body.error || "failed to start run");
      return;
    }
    await refreshRunsList();
    selectRun(body.run_id);
  } finally {
    btn.disabled = false;
  }
}

// ---------- run selection / polling ----------

function selectRun(id) {
  state.selectedRunId = id;
  state.logLen = 0;
  state.animator = null;
  $("#empty-state").style.display = "none";
  $("#tabs").style.display = "flex";
  $("#log-output").textContent = "";
  document.querySelectorAll(".run-row").forEach((el) => el.classList.remove("selected"));
  refreshRunsList();
  if (state.pollTimer) clearInterval(state.pollTimer);
  pollSelectedRun();
  state.pollTimer = setInterval(pollSelectedRun, 900);
}

async function pollSelectedRun() {
  const id = state.selectedRunId;
  if (!id) return;
  const res = await fetch(`/api/runs/${id}?since=${state.logLen}`);
  if (!res.ok) return;
  const run = await res.json();
  state.runs.set(id, run);

  if (run.log.length) {
    const pre = $("#log-output");
    const atBottom = pre.scrollHeight - pre.scrollTop - pre.clientHeight < 40;
    pre.textContent += (state.logLen > 0 ? "\n" : "") + run.log.join("\n");
    state.logLen = run.log_total;
    if (atBottom) pre.scrollTop = pre.scrollHeight;
  }

  $("#queue-status").textContent = `run ${id} · ${run.state}`;

  if (run.state === "error") {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
    const pre = $("#log-output");
    pre.textContent += `\n\n--- FAILED ---\n${run.error || ""}`;
    pre.scrollTop = pre.scrollHeight;
  } else if (run.state === "done") {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
    if (!state.animator) await loadResults(id, run);
  }
}

async function loadResults(runId, run) {
  const [animatorRes, networkRes] = await Promise.all([
    fetch(`/api/runs/${runId}/files/animator`),
    fetch(`/api/network/${run.config.network_section}`),
  ]);
  state.animator = await animatorRes.json();
  state.network = await networkRes.json();
  buildVizData();
  renderScheduleList();
  wireFileButtons(runId);
  initViz();
}

function wireFileButtons(runId) {
  $("#dl-excel").onclick = () => window.open(`/api/runs/${runId}/files/excel`, "_blank");
  $("#dl-chart").onclick = () => window.open(`/api/runs/${runId}/files/chart`, "_blank");
  $("#dl-animator").onclick = () => window.open(`/api/runs/${runId}/files/animator`, "_blank");
}

// ---------- tabs ----------

function wireTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.querySelector(`.tab-panel[data-tab="${btn.dataset.tab}"]`).classList.add("active");
      if (btn.dataset.tab === "visualize") requestAnimationFrame(() => draw());
    });
  });
}

// ---------- visualize ----------

function buildVizData() {
  const { order, segments } = state.network;
  const dist = { [order[0]]: 0 };
  const segByPair = {};
  for (const [a, b, km] of segments) {
    segByPair[`${a}|${b}`] = km;
    segByPair[`${b}|${a}`] = km;
  }

  let cum = 0;
  for (let i = 1; i < order.length; i++) {
    const a = order[i - 1], b = order[i];
    const km = segByPair[`${a}|${b}`];
    cum += typeof km === "number" ? km : 0;
    dist[b] = cum;
  }
  state.stationDist = dist;

  const waypoints = {};
  let minMs = Infinity, maxMs = -Infinity;
  for (const tr of state.animator.trains) {
    const pts = [];
    for (const stop of tr.route) {
      if (!(stop.station in dist)) continue;
      const km = dist[stop.station];
      const arrMs = Date.parse(stop.arr.replace(" ", "T"));
      const depMs = Date.parse(stop.dep.replace(" ", "T"));
      pts.push([arrMs, km], [depMs, km]);
    }
    pts.sort((a, b) => a[0] - b[0]);
    if (pts.length < 2) continue;
    waypoints[tr.train_id] = { type: tr.train_type, points: pts, tMin: pts[0][0], tMax: pts[pts.length - 1][0] };
    minMs = Math.min(minMs, pts[0][0]);
    maxMs = Math.max(maxMs, pts[pts.length - 1][0]);
  }
  state.trainWaypoints = waypoints;
  state.timeDomain = [minMs, maxMs];
  state.nowMs = minMs;

  const scrub = $("#viz-scrub");
  scrub.min = 0;
  scrub.max = 1000;
  scrub.value = 0;
}

function interpAt(points, tMs) {
  if (tMs < points[0][0] || tMs > points[points.length - 1][0]) return null;
  for (let i = 1; i < points.length; i++) {
    const [t0, d0] = points[i - 1];
    const [t1, d1] = points[i];
    if (tMs <= t1) {
      if (t1 === t0) return d0;
      const frac = (tMs - t0) / (t1 - t0);
      return d0 + frac * (d1 - d0);
    }
  }
  return null;
}

let canvasCtx = null;

function resizeCanvas() {
  const canvas = $("#viz-canvas");
  const wrap = $("#viz-canvas-wrap");
  const dpr = window.devicePixelRatio || 1;
  const w = wrap.clientWidth, h = wrap.clientHeight;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvasCtx = canvas.getContext("2d");
  canvasCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { w, h };
}

const PAD = { left: 56, right: 20, top: 16, bottom: 28 };

function draw() {
  if (!state.trainWaypoints) return;
  const { w, h } = resizeCanvas();
  const ctx = canvasCtx;
  const css = getComputedStyle(document.documentElement);
  const line = css.getPropertyValue("--line").trim();
  const ink = css.getPropertyValue("--ink").trim();
  const muted = css.getPropertyValue("--muted").trim();
  const pass = css.getPropertyValue("--pass").trim();
  const goods = css.getPropertyValue("--goods").trim();
  const accent = css.getPropertyValue("--accent").trim();
  const monoFont = css.getPropertyValue("--mono").trim() || "monospace";

  ctx.clearRect(0, 0, w, h);

  const plotW = w - PAD.left - PAD.right;
  const plotH = h - PAD.top - PAD.bottom;
  const [tMin, tMax] = state.timeDomain;
  const maxKm = Math.max(...Object.values(state.stationDist));

  const xOf = (tMs) => PAD.left + ((tMs - tMin) / (tMax - tMin)) * plotW;
  const yOf = (km) => PAD.top + (km / maxKm) * plotH;

  // station gridlines + labels
  ctx.font = `10px ${monoFont}`;
  ctx.strokeStyle = line;
  ctx.fillStyle = muted;
  ctx.textBaseline = "middle";
  for (const [code, km] of Object.entries(state.stationDist)) {
    const y = yOf(km);
    ctx.beginPath();
    ctx.moveTo(PAD.left, y);
    ctx.lineTo(w - PAD.right, y);
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.5;
    ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.textAlign = "right";
    ctx.fillText(code, PAD.left - 6, y);
  }

  // hour gridlines
  const hourMs = 3600 * 1000;
  const firstHour = Math.ceil(tMin / hourMs) * hourMs;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  for (let t = firstHour; t <= tMax; t += hourMs) {
    const x = xOf(t);
    ctx.strokeStyle = line;
    ctx.globalAlpha = 0.35;
    ctx.beginPath();
    ctx.moveTo(x, PAD.top);
    ctx.lineTo(x, h - PAD.bottom);
    ctx.stroke();
    ctx.globalAlpha = 1;
    const d = new Date(t);
    if (d.getHours() % 3 === 0) {
      ctx.fillStyle = muted;
      ctx.fillText(d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), x, h - PAD.bottom + 4);
    }
  }

  const showP = $("#viz-show-p").checked;
  const showG = $("#viz-show-g").checked;
  const search = $("#viz-search").value.trim().toLowerCase();
  state.markers = [];

  for (const [trainId, tw] of Object.entries(state.trainWaypoints)) {
    if (tw.type === "p" && !showP) continue;
    if (tw.type === "g" && !showG) continue;
    const highlighted = search && trainId.toLowerCase().includes(search);
    const dimmed = search && !highlighted;

    ctx.beginPath();
    tw.points.forEach(([t, km], i) => {
      const x = xOf(t), y = yOf(km);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = tw.type === "p" ? pass : goods;
    ctx.lineWidth = highlighted ? 2.2 : 1;
    ctx.globalAlpha = dimmed ? 0.12 : highlighted ? 1 : 0.55;
    ctx.stroke();
    ctx.globalAlpha = 1;

    const km = interpAt(tw.points, state.nowMs);
    if (km !== null) {
      const x = xOf(state.nowMs), y = yOf(km);
      ctx.beginPath();
      ctx.arc(x, y, highlighted ? 4.5 : 3, 0, Math.PI * 2);
      ctx.fillStyle = tw.type === "p" ? pass : goods;
      ctx.globalAlpha = dimmed ? 0.2 : 1;
      ctx.fill();
      ctx.globalAlpha = 1;
      state.markers.push({ x, y, trainId, type: tw.type, km });
    }
  }

  // now line
  const nx = xOf(state.nowMs);
  ctx.strokeStyle = accent;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(nx, PAD.top);
  ctx.lineTo(nx, h - PAD.bottom);
  ctx.stroke();

  $("#viz-now").textContent = new Date(state.nowMs).toLocaleString();
}

function initViz() {
  draw();
}

function stepPlayback(ts) {
  if (!state.playing) return;
  if (state.lastFrameTs === null) state.lastFrameTs = ts;
  const deltaReal = (ts - state.lastFrameTs) / 1000;
  state.lastFrameTs = ts;
  const speed = Number($("#viz-speed").value) * 1000; // ms of sim-time per real second
  state.nowMs += deltaReal * speed;
  const [tMin, tMax] = state.timeDomain;
  if (state.nowMs >= tMax) {
    state.nowMs = tMax;
    setPlaying(false);
  }
  const frac = (state.nowMs - tMin) / (tMax - tMin);
  $("#viz-scrub").value = String(Math.round(frac * 1000));
  draw();
  if (state.playing) state.rafId = requestAnimationFrame(stepPlayback);
}

function setPlaying(on) {
  state.playing = on;
  $("#viz-play").innerHTML = on ? "&#10074;&#10074; Pause" : "&#9654; Play";
  if (on) {
    state.lastFrameTs = null;
    state.rafId = requestAnimationFrame(stepPlayback);
  } else if (state.rafId) {
    cancelAnimationFrame(state.rafId);
  }
}

function wireViz() {
  $("#viz-play").addEventListener("click", () => setPlaying(!state.playing));
  $("#viz-scrub").addEventListener("input", (e) => {
    if (!state.timeDomain) return;
    setPlaying(false);
    const [tMin, tMax] = state.timeDomain;
    const frac = Number(e.target.value) / 1000;
    state.nowMs = tMin + frac * (tMax - tMin);
    draw();
  });
  ["viz-show-p", "viz-show-g"].forEach((id) => $(`#${id}`).addEventListener("change", draw));
  $("#viz-search").addEventListener("input", draw);
  window.addEventListener("resize", () => { if (state.trainWaypoints) draw(); });

  const canvas = $("#viz-canvas");
  const tooltip = $("#viz-tooltip");
  canvas.addEventListener("mousemove", (e) => {
    if (!state.markers) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    let best = null, bestD = 12;
    for (const m of state.markers) {
      const d = Math.hypot(m.x - mx, m.y - my);
      if (d < bestD) { bestD = d; best = m; }
    }
    if (best) {
      tooltip.style.left = `${best.x}px`;
      tooltip.style.top = `${best.y}px`;
      tooltip.style.opacity = "1";
      tooltip.textContent = `${best.trainId} (${best.type === "p" ? "passenger" : "goods"})`;
    } else {
      tooltip.style.opacity = "0";
    }
  });
  canvas.addEventListener("mouseleave", () => { tooltip.style.opacity = "0"; });
}

// ---------- schedule ----------

function renderScheduleList() {
  const wrap = $("#schedule-list");
  const query = $("#schedule-search").value.trim().toLowerCase();
  wrap.innerHTML = "";
  for (const tr of state.animator.trains) {
    if (query && !tr.train_id.toLowerCase().includes(query)) continue;
    const first = tr.route[0], last = tr.route[tr.route.length - 1];
    const row = document.createElement("div");
    row.className = "sched-row" + (tr.train_id === state.selectedScheduleTrain ? " selected" : "");
    row.innerHTML = `
      <div>
        <div class="sid">${tr.train_id}</div>
        <div class="sroute">${first ? first.station : "?"} &rarr; ${last ? last.station : "?"} &middot; ${tr.route.length} stops</div>
      </div>
      <span class="badge type-${tr.train_type}">${tr.train_type}</span>`;
    row.addEventListener("click", () => {
      state.selectedScheduleTrain = tr.train_id;
      renderScheduleList();
      renderScheduleDetail(tr);
    });
    wrap.appendChild(row);
  }
}

function renderScheduleDetail(tr) {
  const el = $("#schedule-detail");
  const rows = tr.route.map((s) => `
    <tr>
      <td>${s.station}</td>
      <td>${s.line}</td>
      <td>${s.platform}</td>
      <td>${s.arr}</td>
      <td>${s.dep}</td>
    </tr>`).join("");
  el.innerHTML = `
    <h3 style="margin-top:0">${tr.train_id} <span class="badge type-${tr.train_type}">${tr.train_type}</span></h3>
    <table class="stops">
      <thead><tr><th>Station</th><th>Line</th><th>Platform</th><th>Arrival</th><th>Departure</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function wireSchedule() {
  $("#schedule-search").addEventListener("input", renderScheduleList);
}

// ---------- form wiring ----------

function wireForm() {
  $("#run-form").addEventListener("submit", submitRun);
  $("#f-start-mode").addEventListener("change", (e) => {
    $("#f-start-manual-wrap").style.display = e.target.value === "manual" ? "flex" : "none";
  });
}

// ---------- init ----------

(async function init() {
  wireTabs();
  wireForm();
  wireViz();
  wireSchedule();
  await loadMeta();
  await refreshRunsList();
})();
