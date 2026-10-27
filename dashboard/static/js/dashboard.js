/* Building a Benchmarking Dashboard for SNN Methods — behaviour.
 *
 * Fetches from the /api/* routes in app.py and draws with the local
 * charting module in minichart.js. Each experiment is now its own
 * server-rendered page (see app.py's PAGES / _render_page and
 * templates/base.html); this file renders only the one page currently
 * loaded — window.SNN.page says which — rather than an every-view render
 * behind a client-side tab swap.
 *
 * The selection model is SIMULATOR-level. A reader picks simulators, not
 * backends, because the simulator is the unit the research question is asked
 * about; every backend belonging to a selected simulator is included, and
 * every chart, table and headline figure is recomputed from that selection.
 *
 * The KPI tiles are recomputed in the browser rather than read from
 * /api/kpis, because they have to answer "of what is currently selected",
 * which the server cannot know. The eligibility rules they apply are the same
 * ones the server applies — controls and compile-dominated backends are shown
 * everywhere but never win a headline figure — so a tile and the server agree
 * whenever the selection is everything.
 *
 * Colour is assigned by framework, never by rank or row order, so toggling a
 * simulator off never repaints the ones that remain.
 */
(function () {
  "use strict";

  const T = window.SNN.theme;
  const FRAMEWORKS = window.SNN.frameworks;
  const ALL_FW = FRAMEWORKS.map(f => f.id);

  // The charting is local (minichart.js), so it is always present. The guard
  // is kept because it costs nothing and turns a missing file into a stated
  // absence rather than an exception that would take the tables down with it.
  const HAVE_CHARTS = typeof window.Chart !== "undefined";

  const PAGE = window.SNN.page || "home";

  // The simulator filter is a global control that now lives on every real
  // page (see base.html), so a real navigation between pages — a normal link
  // click, not a JS-driven tab swap — would otherwise reset it. Persisting
  // the selection in localStorage is what makes "de-select NEST, then open
  // Scalability" keep NEST off on the page that loads next. A simulator the
  // stored selection does not recognise (the set of simulators changed since
  // it was saved) is dropped rather than kept, so a stale selection can never
  // silently hide a simulator this run of the suite actually has.
  const STORE_KEY = "snn-dashboard-active-frameworks";
  function loadActive() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return new Set(ALL_FW);
      const saved = JSON.parse(raw).filter(fw => ALL_FW.includes(fw));
      return saved.length ? new Set(saved) : new Set(ALL_FW);
    } catch { return new Set(ALL_FW); }
  }
  function saveActive() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify([...active])); }
    catch { /* private browsing or storage disabled — filter still works
               in-page, it just will not survive a navigation. */ }
  }

  let active = loadActive();
  const charts = {};
  let DATA = {};

  /* ─────────────────────────────────────────── training sample budget
     Experiment 2 was run at two budgets: the fixed budget that makes the
     cross-simulator comparison controlled (every simulator gets identical
     work), and the full reference budget the specification asks for. Every
     training figure — KPI, ranking, chart — must come from ONE of them.
     Mixing them silently compares a simulator trained on 60,000 images
     against one trained on 6,000, which is the differing-budget confound
     this campaign exists to remove. It is not hypothetical: because Nengo's
     closed-form solve scores marginally lower at the larger budget, a plain
     "highest accuracy per simulator" ranks Nengo on its 6,000-image row and
     every other simulator on its 60,000-image row. */
  const budgetKey = r => `${r.train_n}/${r.epochs}`;
  const budgetLabel = r =>
    `${Number(r.train_n).toLocaleString()} train · ` +
    `${r.epochs} epoch${Number(r.epochs) === 1 ? "" : "s"}`;

  function budgetsPresent() {
    const seen = new Map();
    (DATA.training || []).forEach(r => {
      if (r.train_n === null || r.train_n === undefined) return;
      if (!seen.has(budgetKey(r))) seen.set(budgetKey(r), r);
    });
    // Largest budget first: the full reference configuration is the headline.
    return [...seen.entries()].sort((a, b) => b[1].train_n - a[1].train_n);
  }

  const BUDGET_KEY = "snn-dashboard-training-budget";
  let budgetSel = null;          // resolved once DATA has loaded
  function resolveBudget() {
    const present = budgetsPresent().map(([k]) => k);
    if (!present.length) { budgetSel = null; return; }
    let want = null;
    try { want = localStorage.getItem(BUDGET_KEY); } catch { /* ignore */ }
    // Default to the largest budget available, and never keep a stored
    // choice the current data no longer contains.
    budgetSel = (want && present.includes(want)) ? want : present[0];
  }
  function setBudget(k) {
    budgetSel = k;
    try { localStorage.setItem(BUDGET_KEY, k); } catch { /* storage off */ }
    renderCurrentPage();
  }

  /* ────────────────────────────────────────────── hidden-layer width
     Experiment 2's main arm trains every backend at a hidden width of 256.
     A wider 500-unit arm was started but reached only three of the nine
     backends before it was stopped, so it is a partial check, not a second
     comparison. Because both arms share the same sample budget, the budget
     gate above does not separate them, and a plain "highest accuracy" would
     rank three backends on their 500-unit row and the other six on their
     256-unit row. Every cross-simulator figure therefore uses the width that
     covers the most backends; the partial arm stays visible, labelled as
     partial, in the detail table and the note beneath the charts. */
  function widthCoverage() {
    const byWidth = new Map();
    (DATA.training || []).forEach(r => {
      if (r.hidden === null || r.hidden === undefined) return;
      if (budgetSel !== null && budgetKey(r) !== budgetSel) return;
      if (!byWidth.has(r.hidden)) byWidth.set(r.hidden, new Set());
      byWidth.get(r.hidden).add(r.backend_id || `${r.framework}/${r.backend}`);
    });
    return byWidth;
  }
  function mainWidth() {
    const cov = widthCoverage();
    if (!cov.size) return null;
    // Most backends wins; a tie goes to the narrower width, which is the one
    // the protocol names as the main arm.
    return [...cov.entries()].sort(
      (a, b) => (b[1].size - a[1].size) || (Number(a[0]) - Number(b[0])))[0][0];
  }
  function partialWidths() {
    const cov = widthCoverage();
    const main = mainWidth();
    if (main === null) return [];
    const full = cov.get(main).size;
    return [...cov.entries()]
      .filter(([w]) => String(w) !== String(main))
      .map(([w, s]) => ({ width: w, covered: s.size, of: full }));
  }

  /* The single gate every training figure goes through. */
  function trainRows(opts) {
    const o = opts || {};
    const main = o.allWidths ? null : mainWidth();
    return (DATA.training || []).filter(r =>
      (o.allFrameworks ? true : keep(r)) &&
      (budgetSel === null || budgetKey(r) === budgetSel) &&
      (main === null || r.hidden === null || r.hidden === undefined
        || String(r.hidden) === String(main)));
  }

  /* The one-line disclosure that keeps the partial arm honest. */
  function renderWidthNote(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const main = mainWidth();
    const partial = partialWidths();
    if (main === null) { el.innerHTML = ""; el.hidden = true; return; }
    let html = `Every figure on this page uses the main arm, hidden width
      <b>${esc(String(main))}</b>.`;
    if (partial.length) {
      html += " " + partial.map(p =>
        `A wider arm at hidden width <b>${esc(String(p.width))}</b> reached
         <b>${p.covered} of the ${p.of}</b> backends before it was stopped;
         the remaining ${p.of - p.covered} were not run. It is reported as a
         partial check in the table below and is excluded from every
         comparison and headline figure.`).join(" ");
    }
    el.innerHTML = html;
    el.hidden = false;
  }

  function renderBudgetToggle(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const present = budgetsPresent();
    // One budget is the normal case before the full run lands: say which it
    // is rather than offering a switch with nothing to switch to.
    if (present.length < 2) {
      el.innerHTML = present.length
        ? `<span class="budget-lead">Sample budget</span>
           <span class="budget-only">${esc(budgetLabel(present[0][1]))}</span>`
        : "";
      return;
    }
    el.innerHTML = `<span class="budget-lead">Sample budget</span>` +
      present.map(([k, r]) =>
        `<button type="button" class="budget-btn${k === budgetSel ? " on" : ""}"
                 data-budget="${esc(k)}" ${k === budgetSel ? 'aria-current="true"' : ""}>
           ${esc(budgetLabel(r))}</button>`).join("") +
      `<span class="budget-why">Figures below use one budget at a time;
         comparing across budgets would not be controlled.</span>`;
    el.querySelectorAll(".budget-btn").forEach(b =>
      b.addEventListener("click", () => setBudget(b.dataset.budget)));
  }

  const colorOf = fw => T.colors[fw] || "#7c879b";
  const labelOf = fw => T.labels[fw] || fw;
  const isControl = fw => T.controls.includes(fw);
  const rowColor = r => colorOf(r.framework);
  const keep = r => active.has(r.framework);

  /* ───────────────────────────────────────────────── charting house style */
  if (HAVE_CHARTS) {
    Chart.defaults.font.family =
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif";
    Chart.defaults.font.size = 11.5;
    Chart.defaults.color = T.ink_muted;
    Chart.defaults.animation = window.matchMedia(
      "(prefers-reduced-motion: reduce)").matches ? false : { duration: 240 };
  }

  const tooltip = {
    backgroundColor: T.card, titleColor: T.ink, bodyColor: T.ink_soft,
    borderColor: T.border, borderWidth: 1, padding: 11, displayColors: false,
    titleFont: { weight: "700" }, cornerRadius: 8,
  };

  function axes(o) {
    o = o || {};
    const grid = { color: T.grid, drawBorder: false };
    const x = { grid, ticks: { color: T.ink_muted } };
    // autoSkip off on the category axis. Chart.js drops labels when it thinks
    // space is tight, which on an eleven-backend bar chart silently leaves several
    // bars unlabelled — the reader then cannot tell which simulator a bar
    // belongs to, which is the one thing the chart exists to say.
    const y = {
      grid: o.hideYGrid ? { display: false } : grid,
      ticks: { color: T.ink_muted, autoSkip: false, font: { size: 11 } },
    };
    // An axis type is set only when a log scale is wanted. Declaring "linear"
    // otherwise breaks the categorical axis the horizontal bar charts need.
    if (o.logx) x.type = "logarithmic";
    if (o.logy) y.type = "logarithmic";
    if (o.xtitle) x.title = { display: true, text: o.xtitle, color: T.ink_muted };
    if (o.ytitle) y.title = { display: true, text: o.ytitle, color: T.ink_muted };
    return { x, y };
  }

  function draw(id, config) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!HAVE_CHARTS) {
      if (el.dataset.replaced) return;
      el.dataset.replaced = "1";
      const p = document.createElement("div");
      p.className = "empty";
      p.textContent = "Chart could not be drawn — the table below carries the "
        + "same numbers.";
      el.replaceWith(p);
      return;
    }
    if (charts[id]) charts[id].destroy();
    // willReadFrequently steers the browser to a software-backed 2D context
    // instead of a GPU-accelerated one. These charts are small, redrawn
    // rarely, and never read back, so the software path costs nothing here.
    //
    // This flag was originally added because the charts sometimes rendered as
    // blank boxes carrying the browser's context-lost icon, and that was read
    // as a GPU-allocation failure on hybrid-graphics laptops. It was not. The
    // canvas was growing without bound on any display whose device pixel
    // ratio is not 1 - see the note in minichart.js setup() - until no
    // allocation of that size could succeed on any hardware. That cause is
    // fixed at source; the flag is kept because the software path genuinely
    // suits these charts, not because it works around anything.
    charts[id] = new Chart(el.getContext("2d", { willReadFrequently: true }), config);
  }

  /* Every figure is followed by the numbers it draws (27 Sep 2026). A chart
     that only yields its values on hover cannot be read on a printed page, in
     a screenshot, or by someone working from the keyboard; the table carries
     the same rows in the same order, so the two can never disagree.

     cols: [{h: header, num: true|false, get: row => cell}] — a cell is either
     a string or {t: text, c: colour} to show the simulator's swatch. */
  function figTable(hostId, cols, rows, caption) {
    const el = document.getElementById(hostId);
    if (!el) return;
    if (!rows || !rows.length) {
      el.innerHTML = `<div class="empty">No rows for the current selection.</div>`;
      return;
    }
    const head = cols.map(c => `<th${c.num ? ' class="num"' : ""}>${esc(c.h)}</th>`).join("");
    const body = rows.map(r => "<tr>" + cols.map(c => {
      const v = c.get(r);
      if (v && typeof v === "object") {
        return `<td class="name"><span class="swatch" style="--c:${v.c}"></span>${esc(v.t)}</td>`;
      }
      return `<td${c.num ? ' class="num"' : ""}>${esc(v)}</td>`;
    }).join("") + "</tr>").join("");
    el.innerHTML = `<table>${caption ? `<caption>${esc(caption)}</caption>` : ""}`
      + `<thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  }

  /* The identity cell for a results table: the backend name behind its own
     colour swatch, so the table and the figure are read as one object. */
  const idCell = r => ({ t: r.id, c: colorOf(r.framework) });

  /* Horizontal bars, one per backend, coloured by simulator. Horizontal
     because backend names are long — rotated labels are harder to read than
     a slightly taller figure. */
  function barChart(canvasId, rows, valueKey, o) {
    o = o || {};
    draw(canvasId, {
      type: "bar",
      data: {
        labels: rows.map(r => r.label || r.id),
        datasets: [{
          data: rows.map(r => r[valueKey]),
          backgroundColor: rows.map(rowColor),
          borderRadius: 5, borderSkipped: false,
          barPercentage: 0.74, categoryPercentage: 0.84,
        }],
      },
      options: {
        indexAxis: "y", responsive: true, maintainAspectRatio: false,
        // Printed on the bar, so the chart can be read without hovering.
        valueLabel: o.valueLabel || (v => (v === null || v === undefined)
          ? "" : f(Array.isArray(v) ? v[1] : v, o.decimals === undefined ? 2 : o.decimals)),
        plugins: {
          legend: { display: false },
          tooltip: Object.assign({}, tooltip, {
            callbacks: { label: c => o.label ? o.label(rows[c.dataIndex]) : "" },
          }),
        },
        scales: axes({ logx: o.logx, xtitle: o.xtitle, hideYGrid: true }),
      },
    });
  }

  /* ───────────────────────────────────────────────────────── formatting */
  const f = (v, d) => (v === null || v === undefined || Number.isNaN(v))
    ? "—" : Number(v).toFixed(d === undefined ? 2 : d);
  const int = v => (v === null || v === undefined)
    ? "—" : Number(v).toLocaleString();
  const esc = s => String(s === null || s === undefined ? "" : s)
    .replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const sw = fw => `<span class="swatch" style="background:${colorOf(fw)}"></span>`;

  function fill(id, rows, cells) {
    const tb = document.getElementById(id);
    if (tb) tb.innerHTML = rows.map(r => "<tr>" + cells(r) + "</tr>").join("");
  }

  // Every chart on an experiment page is followed by its own .chart-result
  // element — the answer to "so what does this figure say", stated in one
  // short sentence directly under the figure, rather than left for the
  // reader to work out from the axes. Null-safe so a page missing one slot
  // never throws.
  function resultLine(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  /* ─────────────────────────────────────────────────────────────── KPIs
     Recomputed from the current selection. Controls and compile-dominated
     backends stay visible in every chart but never win a headline figure —
     the same rule the server applies. */
  function eligible(rows) {
    return rows.filter(r => keep(r) && !isControl(r.framework)
                             && !r.compile_dominated);
  }

  function setKpi(n, value, whoFw, whoText, note) {
    const el = document.getElementById("kpi" + n);
    const c = whoFw ? colorOf(whoFw) : T.ink_muted;
    el.style.setProperty("--c", c);
    el.querySelector(".kpi-val").textContent = value;
    el.querySelector(".kpi-who").innerHTML = whoText
      ? `<span class="dot"></span>${esc(whoText)}` : "";
    el.querySelector(".kpi-note").textContent = note || "";
  }

  function renderKpis() {
    const inf = eligible(DATA.inference || []);
    const mem = eligible(DATA.memory || []);
    const scale = eligible(DATA.scalability || []).filter(
      s => s.fit && s.fit.r2 >= 0.25);
    const train = trainRows().filter(
      r => !isControl(r.framework) && r.accuracy_pct !== null);

    if (inf.length) {
      const b = inf.reduce((a, r) => r.runtime_median_s < a.runtime_median_s ? r : a);
      setKpi(1, f(b.runtime_median_s * 1000, 2) + " ms", b.framework,
        `${labelOf(b.framework)} / ${b.backend}`,
        `median over ${b.n_runs} runs at N=${int(b.network_size)}`);
    } else setKpi(1, "—", null, "", "no eligible simulator selected");

    if (mem.length) {
      const b = mem.reduce((a, r) => r.peak_mb < a.peak_mb ? r : a);
      setKpi(2, f(b.peak_mb, 0) + " MB", b.framework,
        `${labelOf(b.framework)} / ${b.backend}`,
        `peak RSS at N=${int(b.largest_n)}`);
    } else setKpi(2, "—", null, "", "no eligible simulator selected");

    if (scale.length) {
      const b = scale.reduce((a, s) => s.fit.k < a.fit.k ? s : a);
      setKpi(3, "k = " + f(b.fit.k, 3), b.framework,
        `${labelOf(b.framework)} / ${b.backend}`,
        `r² = ${f(b.fit.r2, 2)} over ${b.points.length} sizes`);
    } else setKpi(3, "—", null, "", "no eligible simulator selected");

    if (train.length) {
      const b = train.reduce((a, r) => r.accuracy_pct > a.accuracy_pct ? r : a);
      setKpi(4, f(b.accuracy_pct, 2) + "%", b.framework,
        `${labelOf(b.framework)} / ${b.backend}`,
        `${int(b.train_n)} train · ${b.epochs} epoch(s)`);
    } else setKpi(4, "—", null, "", "no training rows for this selection");

    // The scope line names exactly what is on screen, so a reader always
    // knows what the figures above are a summary of.
    const names = ALL_FW.filter(x => active.has(x)).map(labelOf);
    const hidden = ALL_FW.filter(x => !active.has(x)).map(labelOf);
    const note = document.getElementById("scopeNote");
    if (!names.length) {
      note.innerHTML = "<b>Nothing selected.</b> Choose at least one simulator above.";
    } else {
      note.innerHTML =
        `<b>Showing:</b> ${esc(names.join(", "))}` +
        (hidden.length ? ` &nbsp;·&nbsp; <b>hidden:</b> ${esc(hidden.join(", "))}` : "") +
        ". Headline figures exclude the two NumPy validation controls and any compile-dominated " +
        "backend — both stay visible in the charts and tables below, but neither " +
        "is comparable on these axes.";
    }
  }

  /* ────────────────────────────────────────────────────── ALL SIMULATOR
     Every headline KPI above names only the winner. This view expands each
     one into a full ranking of every simulator that produced an eligible
     measurement, best to worst — "fastest inference is NEST, then ..., then
     ..." for each KPI in turn. Deliberately unaffected by the simulator
     selector: the point of this page is the complete field, so it always
     ranks everyone eligible rather than whatever subset happens to be
     toggled on elsewhere. The exclusion rule is the same one every headline
     figure already applies — the NumPy reference and any compile-dominated
     backend are not simulators this comparison ranks. */
  function allEligible(rows) {
    return rows.filter(r => !isControl(r.framework) && !r.compile_dominated);
  }

  // One entry per simulator: its single best eligible backend for this
  // metric, so a simulator with several backends is ranked on its strongest
  // showing rather than being listed once per backend.
  function bestPerSimulator(rows, valueOf, higherIsBetter) {
    const bySim = {};
    rows.forEach(r => {
      const v = valueOf(r);
      if (v === null || v === undefined || Number.isNaN(v)) return;
      const cur = bySim[r.framework];
      if (!cur || (higherIsBetter ? v > cur.value : v < cur.value)) {
        bySim[r.framework] = { framework: r.framework, value: v, row: r };
      }
    });
    const list = Object.values(bySim);
    list.sort((a, b) => higherIsBetter ? b.value - a.value : a.value - b.value);
    return list;
  }

  function renderRankList(id, list, valueText, detailText) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!list.length) {
      el.innerHTML = '<div class="empty">No simulator has an eligible measured value for this KPI yet.</div>';
      return;
    }
    el.innerHTML = list.map((item, i) => `
      <div class="rank-row${i === 0 ? " rank-first" : ""}" style="--c:${colorOf(item.framework)}">
        <div class="rank-pos">${i + 1}</div>
        <div class="rank-id">
          <span class="rank-dot"></span>
          <span class="rank-name">${esc(labelOf(item.framework))}</span>
        </div>
        <div class="rank-val">${valueText(item)}</div>
        <div class="rank-detail">${esc(detailText(item))}</div>
      </div>`).join("");
  }

  function renderAllSimulators() {
    renderBudgetToggle("rankBudget");
    const inf = allEligible(DATA.inference || []);
    const mem = allEligible(DATA.memory || []);
    const scale = allEligible(DATA.scalability || [])
      .filter(s => s.fit && s.fit.r2 >= 0.25);
    const train = trainRows({ allFrameworks: true }).filter(
      r => !isControl(r.framework) && r.accuracy_pct !== null);

    renderRankList("rankInference",
      bestPerSimulator(inf, r => r.runtime_median_s, false),
      it => f(it.value * 1000, 2) + " ms",
      it => `${it.row.backend} · median over ${it.row.n_runs} runs at N=${int(it.row.network_size)}`);

    renderRankList("rankMemory",
      bestPerSimulator(mem, r => r.peak_mb, false),
      it => f(it.value, 0) + " MB",
      it => `${it.row.backend} · peak RSS at N=${int(it.row.largest_n)}`);

    renderRankList("rankScaling",
      bestPerSimulator(scale, s => s.fit.k, false),
      it => "k = " + f(it.value, 3),
      it => `${it.row.backend} · r² = ${f(it.row.fit.r2, 2)} over ${it.row.points.length} sizes`);

    renderRankList("rankTraining",
      bestPerSimulator(train, r => r.accuracy_pct, true),
      it => f(it.value, 2) + "%",
      it => `${it.row.backend} · ${int(it.row.train_n)} train · ${it.row.epochs} epoch(s)`);
  }

  /* Backends within one simulator share a hue, so line style is what keeps
     them apart. Controls are always dashed so they read as a reference line
     rather than as another competitor. */
  function lineDash(s) {
    if (isControl(s.framework)) return [6, 4];
    if (s.backend === "cython") return [8, 4];
    if (s.backend === "cpp_standalone") return [2, 3];
    if (s.backend === "threads2") return [8, 4];
    return [];
  }

  /* ─────────────────────────────────────────────────────── INFERENCE */
  function renderInference() {
    const rows = (DATA.inference || []).filter(keep);
    // "Eligible" mirrors the KPI rule: the NumPy baseline and any
    // compile-dominated backend stay on every chart, but a Result line never
    // crowns one of them the winner — the same reason the KPI tiles exclude
    // them.
    const elig = rows.filter(r => !isControl(r.framework) && !r.compile_dominated);

    barChart("runtimeChart", rows, "runtime_median_s", {
      logx: true, xtitle: "seconds (log)",
      valueLabel: v => v === null ? "" : f(v * 1000, 2) + " ms",
      label: r => [r.id, `${f(r.runtime_median_s * 1000, 3)} ms median`,
                   `CV ${f(r.cv_pct, 1)}% over ${r.n_runs} runs`],
    });
    figTable("runtimeChartTable", [
      { h: "Backend", get: idCell },
      { h: "Median (ms)", num: true, get: r => f(r.runtime_median_s * 1000, 2) },
      { h: "CV %", num: true, get: r => f(r.cv_pct, 1) },
      { h: "Runs", num: true, get: r => int(r.n_runs) },
    ], rows, "Inference runtime at the reference size");
    if (elig.length) {
      const fastest = elig.reduce((a, r) => r.runtime_median_s < a.runtime_median_s ? r : a);
      const slowest = elig.reduce((a, r) => r.runtime_median_s > a.runtime_median_s ? r : a);
      const spread = slowest.runtime_median_s / fastest.runtime_median_s;
      resultLine("runtimeResult",
        `<strong>${esc(fastest.id)}</strong> is fastest at ${f(fastest.runtime_median_s * 1000, 2)} ms median` +
        (fastest.id === slowest.id ? "." :
          `; <strong>${esc(slowest.id)}</strong> is slowest at ${f(slowest.runtime_median_s * 1000, 2)} ms — a ${f(spread, 0)}&times; spread.`));
    } else resultLine("runtimeResult", "No eligible backend in the current selection.");

    barChart("memChart", rows, "peak_rss_mb", {
      xtitle: "MB", valueLabel: v => v === null ? "" : f(v, 0) + " MB", label: r => [r.id, `${f(r.peak_rss_mb, 0)} MB peak RSS`],
    });
    figTable("memChartTable", [
      { h: "Backend", get: idCell },
      { h: "Peak RSS (MB)", num: true, get: r => f(r.peak_rss_mb, 0) },
    ], rows, "Peak resident memory at the reference size");
    if (elig.length) {
      const lo = elig.reduce((a, r) => r.peak_rss_mb < a.peak_rss_mb ? r : a);
      const hi = elig.reduce((a, r) => r.peak_rss_mb > a.peak_rss_mb ? r : a);
      resultLine("memResult",
        `<strong>${esc(lo.id)}</strong> holds the smallest footprint at ${f(lo.peak_rss_mb, 0)} MB` +
        (lo.id === hi.id ? "." : `; <strong>${esc(hi.id)}</strong> the largest at ${f(hi.peak_rss_mb, 0)} MB.`));
    } else resultLine("memResult", "No eligible backend in the current selection.");

    const energyRows = rows.filter(r => r.energy_index !== null);
    barChart("energyChart", energyRows, "energy_index", {
      logx: true, xtitle: "index, log scale (costliest simulating backend = 100)",
      valueLabel: v => v === null ? "" : f(v, 1),
      label: r => [r.id, `index ${f(r.energy_index, 1)}`,
                   `${f(r.energy_median_j, 3)} J estimated`],
    });
    figTable("energyChartTable", [
      { h: "Backend", get: idCell },
      { h: "Energy index", num: true, get: r => f(r.energy_index, 1) },
      { h: "Estimated J", num: true, get: r => f(r.energy_median_j, 3) },
    ], energyRows, "Energy proxy, costliest simulating backend = 100");
    const energyElig = energyRows.filter(r => !isControl(r.framework) && !r.compile_dominated);
    if (energyElig.length) {
      const best = energyElig.reduce((a, r) => r.energy_index < a.energy_index ? r : a);
      resultLine("energyResult",
        `<strong>${esc(best.id)}</strong> reads lowest on the energy proxy at index ${f(best.energy_index, 1)}` +
        (best.energy_median_j !== null ? ` (~${f(best.energy_median_j, 3)} J per run).` : "."));
    } else resultLine("energyResult", "No eligible backend reports an energy estimate.");

    // Processor utilisation vs runtime — a scatter, one point per backend,
    // coloured by framework, in place of a fourth bar chart repeating the
    // same "one axis of one metric" shape as the three above it.
    const byFw = {};
    rows.forEach(r => { (byFw[r.framework] = byFw[r.framework] || []).push(r); });
    draw("cpuScatterChart", {
      type: "line",
      data: {
        datasets: Object.keys(byFw).map(fw => ({
          label: labelOf(fw), showLine: false,
          data: byFw[fw].map(r => ({ x: r.runtime_median_s, y: r.cpu_pct, id: r.id })),
          borderColor: colorOf(fw), backgroundColor: colorOf(fw),
          pointRadius: 5.5, pointHoverRadius: 8,
          pointBorderColor: T.card, pointBorderWidth: 1.4,
        })),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, padding: 12 } },
          tooltip: Object.assign({}, tooltip, {
            callbacks: {
              title: c => c[0].raw.id,
              label: c => [`${f(c.raw.x * 1000, 2)} ms median runtime`, `${f(c.raw.y, 0)}% mean CPU`],
            },
          }),
        },
        scales: axes({ logx: true, xtitle: "runtime, seconds (log)", ytitle: "% of one core" }),
      },
    });
    figTable("cpuScatterChartTable", [
      { h: "Backend", get: idCell },
      { h: "Runtime (ms)", num: true, get: r => f(r.runtime_median_s * 1000, 2) },
      { h: "CPU %", num: true, get: r => f(r.cpu_pct, 1) },
    ], rows, "Processor utilisation against runtime");
    if (elig.length) {
      const fastest = elig.reduce((a, r) => r.runtime_median_s < a.runtime_median_s ? r : a);
      const mostParallel = elig.reduce((a, r) => r.cpu_pct > a.cpu_pct ? r : a);
      resultLine("cpuResult",
        `<strong>${esc(mostParallel.id)}</strong> uses the most of the machine at ${f(mostParallel.cpu_pct, 0)}% CPU` +
        (mostParallel.id === fastest.id
          ? `, and it is also the fastest backend above.`
          : `, but <strong>${esc(fastest.id)}</strong> is the fastest — using more cores is not the same as less wall-clock time.`));
    } else resultLine("cpuResult", "No eligible backend in the current selection.");

    fill("infTable", rows, r => `
      <td class="name">${sw(r.framework)}${esc(r.id)}</td>
      <td class="num">${f(r.runtime_median_s, 6)}</td>
      <td class="num">${f(r.cv_pct, 2)}</td>
      <td class="num">${r.setup_s ? f(r.setup_s, 4) : "—"}</td>
      <td class="num">${f(r.peak_rss_mb, 1)}</td>
      <td class="num">${f(r.cpu_pct, 1)}</td>
      <td class="num">${int(r.spikes)}</td>
      <td class="num">${f(r.energy_median_j, 4)}</td>
      <td class="num">${int(r.n_runs)}</td>
      <td>${r.compile_dominated
            ? '<span class="tag tag-warn">compile-dominated</span>'
            : (isControl(r.framework) ? '<span class="tag tag-muted">baseline</span>' : "")}</td>`);
  }

  /* ───────────────────────────────────────────────────── SCALABILITY */
  function renderScalability() {
    const series = (DATA.scalability || []).filter(keep);
    draw("scaleChart", {
      type: "line",
      data: {
        datasets: series.map(s => ({
          label: s.id,
          data: s.points.map(p => ({ x: p.n, y: p.t, cv: p.cv, spikes: p.spikes, runs: p.runs })),
          borderColor: colorOf(s.framework), backgroundColor: colorOf(s.framework),
          borderDash: lineDash(s), borderWidth: 2.2,
          pointRadius: 4, pointHoverRadius: 7,
          pointBorderColor: T.card, pointBorderWidth: 1.6, tension: 0,
        })),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, padding: 12 } },
          tooltip: Object.assign({}, tooltip, {
            callbacks: {
              title: c => c[0].dataset.label,
              label: c => [`N = ${int(c.raw.x)}`, `${f(c.raw.y, 4)} s median`,
                           `CV ${f(c.raw.cv, 1)}% over ${c.raw.runs} runs`,
                           `${int(c.raw.spikes)} spikes`],
            },
          }),
        },
        scales: axes({ logx: true, logy: true, xtitle: "neurons (N)", ytitle: "seconds" }),
      },
    });
    figTable("scaleChartTable", [
      { h: "Backend", get: idCell },
      { h: "Exponent k", num: true, get: s => s.fit ? f(s.fit.k, 3) : "—" },
      { h: "r²", num: true, get: s => s.fit ? f(s.fit.r2, 2) : "—" },
      { h: "Largest N", num: true, get: s => int(s.largest_n) },
      { h: "At largest N (s)", num: true, get: s => s.largest_t ? f(s.largest_t, 4) : "—" },
    ], series, "Runtime against network size: fitted exponent per backend");

    // The headline card on the home page answers this same question, so both
    // must apply the same rule or the dashboard contradicts itself: a backend
    // that is "flattest" here and not there is a defect, not a nuance. The
    // threshold is the headline's (r2 >= 0.25); what keeps a weak fit honest is
    // reporting its interval beside it, not hiding it behind a higher cut-off.
    const fitted = series.filter(s => s.fit && s.fit.r2 >= 0.25 && !isControl(s.framework));
    if (fitted.length) {
      // "Flattest" means k closest to zero from either side, not the most
      // negative k — a backend whose cost falls slightly as N grows is just
      // as flat a line as one that rises slightly, and the table's own
      // "near-flat" reading treats them the same way.
      const flattest = fitted.reduce((a, s) => Math.abs(s.fit.k) < Math.abs(a.fit.k) ? s : a);
      const steepest = fitted.reduce((a, s) => s.fit.k > a.fit.k ? s : a);
      const ci = flattest.fit.ci;
      const spansZero = ci && ci[0] <= 0 && ci[1] >= 0;
      resultLine("scaleResult",
        `<strong>${esc(flattest.id)}</strong> scales flattest at k = ${f(flattest.fit.k, 3)} (r&sup2; = ${f(flattest.fit.r2, 2)})` +
        (ci ? `, 95% CI [${f(ci[0], 3)}, ${f(ci[1], 3)}]` : "") +
        (spansZero ? " — an interval that includes zero, so the slope is not distinguishable from flat" : "") +
        (flattest.id === steepest.id ? "." : `; <strong>${esc(steepest.id)}</strong> grows fastest at k = ${f(steepest.fit.k, 3)}.`));
    } else resultLine("scaleResult", "No backend in the current selection has a well-fitted scaling curve.");

    const thr = series.filter(s => s.throughput).sort((a, b) => b.throughput - a.throughput);
    barChart("throughputChart", thr, "throughput", {
      logx: true, xtitle: "neurons per second (log)",
      valueLabel: v => v === null ? "" : int(Math.round(v)),
      label: s => [s.id, `${int(Math.round(s.throughput))} neurons/s`,
                   `at N = ${int(s.largest_n)}`],
    });
    figTable("throughputChartTable", [
      { h: "Backend", get: idCell },
      { h: "Neurons / s", num: true, get: s => int(Math.round(s.throughput)) },
      { h: "At N", num: true, get: s => int(s.largest_n) },
    ], thr, "Throughput at the largest size measured");
    const thrElig = thr.filter(s => !isControl(s.framework));
    if (thrElig.length) {
      const best = thrElig.reduce((a, s) => s.throughput > a.throughput ? s : a);
      resultLine("throughputResult",
        `<strong>${esc(best.id)}</strong> processes the most neurons per second at the largest size measured: ${int(Math.round(best.throughput))} neurons/s.`);
    } else resultLine("throughputResult", "No eligible backend reports a throughput figure.");

    fill("scaleTable", series, s => `
      <td class="name">${sw(s.framework)}${esc(s.id)}</td>
      <td class="num">${s.fit ? f(s.fit.k, 3) : "—"}</td>
      <td>${s.fit ? `${f(s.fit.ci[0], 3)} … ${f(s.fit.ci[1], 3)}` : "—"}</td>
      <td class="num">${s.fit ? f(s.fit.r2, 3) : "—"}</td>
      <td class="num">${s.points.length}</td>
      <td class="num">${s.largest_t ? f(s.largest_t, 4) + " s" : "—"}</td>
      <td class="note">${esc(s.interpretation)}</td>`);
  }

  /* ────────────────────────────────────────────────────────── MEMORY */
  function renderMemory() {
    const mem = (DATA.memory || []).filter(keep);
    draw("memScaleChart", {
      type: "line",
      data: {
        datasets: mem.map(s => ({
          label: s.id,
          data: s.points.map(p => ({ x: p.n, y: p.mem })),
          borderColor: colorOf(s.framework), backgroundColor: colorOf(s.framework),
          borderDash: lineDash(s), borderWidth: 2.2,
          pointRadius: 4, pointHoverRadius: 7,
          pointBorderColor: T.card, pointBorderWidth: 1.6, tension: 0,
        })),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, padding: 12 } },
          tooltip: Object.assign({}, tooltip, {
            callbacks: {
              title: c => c[0].dataset.label,
              label: c => [`N = ${int(c.raw.x)}`, `${f(c.raw.y, 0)} MB peak RSS`],
            },
          }),
        },
        scales: axes({ logx: true, xtitle: "neurons (N)", ytitle: "peak RSS (MB)" }),
      },
    });
    figTable("memScaleChartTable", [
      { h: "Backend", get: idCell },
      { h: "Peak at largest N (MB)", num: true, get: s => f(s.peak_mb, 0) },
      { h: "Largest N", num: true, get: s => int(s.largest_n) },
    ], mem, "Peak memory against network size");

    const memElig = mem.filter(s => !isControl(s.framework) && !s.compile_dominated);
    if (memElig.length) {
      const lo = memElig.reduce((a, s) => s.peak_mb < a.peak_mb ? s : a);
      const hi = memElig.reduce((a, s) => s.peak_mb > a.peak_mb ? s : a);
      resultLine("memScaleResult",
        `At the largest size measured, <strong>${esc(lo.id)}</strong> holds the smallest footprint at ${f(lo.peak_mb, 0)} MB` +
        (lo.id === hi.id ? "." : `; <strong>${esc(hi.id)}</strong> the largest at ${f(hi.peak_mb, 0)} MB.`));
    } else resultLine("memScaleResult", "No eligible backend in the current selection.");

    const kb = mem.filter(s => s.kb_per_neuron !== null)
      .sort((a, b) => b.kb_per_neuron - a.kb_per_neuron);
    barChart("perNeuronChart", kb, "kb_per_neuron", {
      xtitle: "KB per neuron",
      valueLabel: v => v === null ? "" : f(v, 2) + " KB",
      label: s => [s.id, `${f(s.kb_per_neuron, 2)} KB/neuron`,
                   `${f(s.growth_mb, 1)} MB growth to N = ${int(s.largest_n)}`],
    });
    figTable("perNeuronChartTable", [
      { h: "Backend", get: idCell },
      { h: "KB / neuron", num: true, get: s => f(s.kb_per_neuron, 2) },
      { h: "Growth (MB)", num: true, get: s => f(s.growth_mb, 1) },
    ], kb, "Memory growth per neuron");
    const kbElig = kb.filter(s => !isControl(s.framework) && !s.compile_dominated);
    if (kbElig.length) {
      const leanest = kbElig.reduce((a, s) => s.kb_per_neuron < a.kb_per_neuron ? s : a);
      resultLine("perNeuronResult",
        `<strong>${esc(leanest.id)}</strong> attributes the least memory to the network itself, at ${f(leanest.kb_per_neuron, 2)} KB per neuron.`);
    } else resultLine("perNeuronResult", "No eligible backend reports a per-neuron figure.");

    fill("memTable", mem, s => `
      <td class="name">${sw(s.framework)}${esc(s.id)}</td>
      <td class="num">${f(s.baseline_mb, 1)}</td>
      <td class="num">${f(s.peak_mb, 1)}</td>
      <td class="num">${f(s.growth_mb, 1)}</td>
      <td class="num">${s.kb_per_neuron === null ? "—" : f(s.kb_per_neuron, 3)}</td>`);

    /* Chart.js has no box plot without a plugin, and a plugin from a CDN is a
       dependency this page does not need: the same question — how far apart
       are the individual runs — is answered by drawing min-to-max as a
       floating bar with the median marked inside it. */
    const spread = (DATA.spread || []).filter(keep);
    draw("spreadChart", {
      type: "bar",
      data: {
        labels: spread.map(s => s.id),
        datasets: [
          {
            data: spread.map(s => [s.min, s.max]),
            backgroundColor: spread.map(s => colorOf(s.framework) + "3a"),
            borderColor: spread.map(s => colorOf(s.framework)),
            borderWidth: 1.2, borderSkipped: false, borderRadius: 3,
            barPercentage: 0.62, categoryPercentage: 0.84,
          },
          {
            data: spread.map(s => [s.median * 0.994, s.median * 1.006]),
            backgroundColor: spread.map(s => colorOf(s.framework)),
            borderWidth: 0, borderSkipped: false,
            barPercentage: 0.62, categoryPercentage: 0.84,
          },
        ],
      },
      options: {
        indexAxis: "y", responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: Object.assign({}, tooltip, {
            callbacks: {
              title: c => c[0].label,
              label: c => {
                const s = spread[c.dataIndex];
                return [`median ${f(s.median, 5)} s`,
                        `range ${f(s.min, 5)} – ${f(s.max, 5)} s`,
                        `CV ${f(s.cv_pct, 2)}% over ${s.n} runs`];
              },
            },
          }),
        },
        scales: axes({ logx: true, xtitle: "seconds per run (log)", hideYGrid: true }),
      },
    });
    figTable("spreadChartTable", [
      { h: "Backend", get: idCell },
      { h: "Median (s)", num: true, get: s => f(s.median, 5) },
      { h: "Min (s)", num: true, get: s => f(s.min, 5) },
      { h: "Max (s)", num: true, get: s => f(s.max, 5) },
      { h: "CV %", num: true, get: s => f(s.cv_pct, 2) },
      { h: "Runs", num: true, get: s => int(s.n) },
    ], spread, "Spread of the individual runs behind each median");

    const spreadElig = spread.filter(s => !isControl(s.framework));
    if (spreadElig.length) {
      const tightest = spreadElig.reduce((a, s) => s.cv_pct < a.cv_pct ? s : a);
      const loosest = spreadElig.reduce((a, s) => s.cv_pct > a.cv_pct ? s : a);
      resultLine("spreadResult",
        `<strong>${esc(tightest.id)}</strong>'s runs are the most repeatable, CV ${f(tightest.cv_pct, 2)}%` +
        (tightest.id === loosest.id ? "." : `; <strong>${esc(loosest.id)}</strong>'s are the most scattered at CV ${f(loosest.cv_pct, 2)}%.`));
    } else resultLine("spreadResult", "No eligible backend in the current selection.");

    fill("spreadTable", spread, s => `
      <td class="name">${sw(s.framework)}${esc(s.id)}</td>
      <td class="num">${int(s.n)}</td>
      <td class="num">${f(s.median, 6)}</td>
      <td class="num">${f(s.min, 6)}</td>
      <td class="num">${f(s.max, 6)}</td>
      <td class="num">${f(s.cv_pct, 2)}</td>`);
  }

  /* ──────────────────────────────────────────────────────── TRAINING */
  function renderTraining() {
    renderBudgetToggle("trainBudget");
    renderWidthNote("widthNote");
    const rows = trainRows();
    document.getElementById("trainEmpty").hidden = rows.length > 0;

    barChart("accChart", rows, "accuracy_pct", {
      xtitle: "test accuracy (%)  ·  chance = 10%",
      valueLabel: v => v === null ? "" : f(v, 2) + "%",
      label: r => [r.id, `${f(r.accuracy_pct, 2)}% test accuracy`,
                   `${int(r.train_n)} train / ${int(r.test_n)} test`,
                   `${r.epochs} epoch(s), hidden ${r.hidden}`],
    });
    figTable("accChartTable", [
      { h: "Backend", get: idCell },
      { h: "Accuracy %", num: true, get: r => f(r.accuracy_pct, 2) },
      { h: "s / epoch", num: true, get: r => f(r.seconds_per_epoch, 2) },
      { h: "Epochs", num: true, get: r => int(r.epochs) },
      { h: "Train / test", get: r => `${int(r.train_n)} / ${int(r.test_n)}` },
      { h: "Learned?", get: r => r.at_chance ? "at chance" : "yes" },
    ], rows, "MNIST test accuracy, each simulator's own learning rule");
    const learned = rows.filter(r => !r.at_chance);
    if (learned.length) {
      const best = learned.reduce((a, r) => r.accuracy_pct > a.accuracy_pct ? r : a);
      resultLine("accResult",
        `<strong>${esc(best.id)}</strong> reaches the highest test accuracy among backends that learned anything: ${f(best.accuracy_pct, 2)}%.` +
        (rows.length > learned.length
          ? ` ${rows.length - learned.length} of ${rows.length} scored no better than guessing — see the chart alongside.`
          : ""));
    } else resultLine("accResult", rows.length
      ? "Every row in the current selection scored no better than guessing."
      : "No training rows for the current selection.");

    // Accuracy against cost per epoch — a scatter, replacing a second bar
    // chart of the same "seconds per epoch" axis with the tradeoff a reader
    // actually wants: is the accurate backend also the cheap one to train.
    const byFw = {};
    rows.forEach(r => { (byFw[r.framework] = byFw[r.framework] || []).push(r); });
    draw("costAccChart", {
      type: "line",
      data: {
        datasets: Object.keys(byFw).map(fw => ({
          label: labelOf(fw), showLine: false,
          data: byFw[fw].map(r => ({ x: r.seconds_per_epoch, y: r.accuracy_pct, id: r.id })),
          borderColor: colorOf(fw), backgroundColor: colorOf(fw),
          pointRadius: 5.5, pointHoverRadius: 8,
          pointBorderColor: T.card, pointBorderWidth: 1.4,
        })),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, padding: 12 } },
          tooltip: Object.assign({}, tooltip, {
            callbacks: {
              title: c => c[0].raw.id,
              label: c => [`${f(c.raw.y, 2)}% accuracy`, `${f(c.raw.x, 2)} s / epoch`],
            },
          }),
        },
        scales: axes({ logx: true, xtitle: "seconds per epoch (log)", ytitle: "test accuracy (%)" }),
      },
    });
    figTable("costAccChartTable", [
      { h: "Backend", get: idCell },
      { h: "s / epoch", num: true, get: r => f(r.seconds_per_epoch, 2) },
      { h: "Accuracy %", num: true, get: r => f(r.accuracy_pct, 2) },
    ], rows, "Accuracy against the cost of an epoch");
    if (learned.length) {
      const cheapest = learned.reduce((a, r) => r.seconds_per_epoch < a.seconds_per_epoch ? r : a);
      const mostAccurate = learned.reduce((a, r) => r.accuracy_pct > a.accuracy_pct ? r : a);
      resultLine("costAccResult", cheapest.id === mostAccurate.id
        ? `<strong>${esc(cheapest.id)}</strong> is both the cheapest to train (${f(cheapest.seconds_per_epoch, 2)} s/epoch) and the most accurate.`
        : `<strong>${esc(cheapest.id)}</strong> is cheapest at ${f(cheapest.seconds_per_epoch, 2)} s/epoch, but <strong>${esc(mostAccurate.id)}</strong> is the most accurate at ${f(mostAccurate.accuracy_pct, 2)}%.`);
    } else resultLine("costAccResult", "No backend in the current selection learned anything to compare a cost against.");

    // "Did it learn?" composition — a donut, because this is a part-of-whole
    // question (how many of the current selection's rows actually learned
    // something) that a bar chart states less directly than a ring reading
    // "N of M" at a glance.
    const learnedN = rows.filter(r => !r.at_chance).length;
    const chanceN = rows.length - learnedN;
    draw("learnedDonut", {
      type: "pie",
      data: {
        labels: ["Learned", "At chance"],
        values: [learnedN, chanceN],
        colors: [T.good, T.bad],
      },
      options: {
        centreLabel: String(rows.length), centreSub: "rows",
        plugins: { legend: { display: true } },
      },
    });
    figTable("learnedDonutTable", [
      { h: "Outcome", get: r => r.k },
      { h: "Backends", num: true, get: r => int(r.v) },
      { h: "Share", num: true, get: r => rows.length ? f(100 * r.v / rows.length, 1) + "%" : "—" },
    ], [{ k: "Learned beyond chance", v: learnedN }, { k: "At chance", v: chanceN }],
      "Did it learn? Composition of the current selection");
    resultLine("learnedResult", rows.length
      ? `<strong>${learnedN} of ${rows.length}</strong> backend${rows.length === 1 ? "" : "s"} in the current selection learned something beyond chance; ${chanceN} did not.`
      : "No training rows for the current selection.");

    // The detail table is the one place the partial arm is shown, marked as
    // partial, so a reader can see it without it entering any comparison.
    const mainW = mainWidth();
    const allRows = trainRows({ allWidths: true }).slice().sort(
      (a, b) => (String(a.hidden) === String(mainW) ? 0 : 1)
              - (String(b.hidden) === String(mainW) ? 0 : 1)
              || b.accuracy_pct - a.accuracy_pct);
    fill("trainTable", allRows, r => `
      <td class="name">${sw(r.framework)}${esc(r.id)}${
        String(r.hidden) === String(mainW) ? ""
          : '<span class="tag tag-warn" title="A partial arm: it did not cover '
            + 'every backend, so it is excluded from comparisons and headline '
            + 'figures."> partial arm</span>'}</td>
      <td class="num">${f(r.accuracy_pct, 2)}</td>
      <td>${r.at_chance
            ? '<span class="tag tag-bad" title="Scored no better than random '
              + 'guessing. With ten digit classes, guessing alone gives about '
              + '10%.">no — no better than guessing</span>'
            : '<span class="tag tag-good">yes</span>'}</td>
      <td class="num">${int(r.hidden)}</td>
      <td class="num">${int(r.train_n)}</td>
      <td class="num">${int(r.test_n)}</td>
      <td class="num">${int(r.epochs)}</td>
      <td class="num">${f(r.seconds_per_epoch, 2)}</td>
      <td class="note">${esc(r.mechanism)}</td>`);

    const chance = rows.filter(r => r.at_chance);
    const cav = document.getElementById("chanceCaveat");
    cav.hidden = chance.length === 0;
    if (chance.length) {
      const names = [...new Set(chance.map(r => r.id))];
      const plural = names.length > 1;
      cav.innerHTML =
        `<strong>${esc(names.join(", "))} ${plural ? "score" : "scores"} no better than guessing, and the
         ${plural ? "rows say" : "row says"} so rather than burying it.</strong>
         These use unsupervised spike-timing-dependent plasticity with a
         neuron-labelling readout. Without lateral inhibition and an adaptive
         threshold, every hidden neuron converges on the same filter, the
         labelling pass assigns most of them to one class, and that class then
         wins every test image — and the full budget, with ten times the images
         and more than three times the epochs, still leaves every such row at or
         below chance. What
         is measured here is that limitation, not a property of the simulator.`;
    }
  }

  /* ───────────────────────────────────────────────────── SENSITIVITY */
  function tauColor(tau) {
    if (tau === null || tau === undefined) return T.ink_muted;
    if (tau >= 0.8) return T.good;
    if (tau >= 0.5) return T.warn;
    return T.bad;
  }

  /* `shown` is the text placed in the tile's headline slot. It is passed in
     rather than formatted here because not every tile holds a Kendall tau:
     the O2 panel shows a Spearman rho and a plain count, and labelling
     either of those "τ" would name the wrong statistic. `colorBy` is the
     value the colour scale reads, which is not always the value displayed. */
  function tauTile(k, shown, reading, isRef, colorBy) {
    const c = tauColor(colorBy === undefined ? null : colorBy);
    return `<div class="tau${isRef ? " ref" : ""}" style="--tc:${c}">
      <div class="tau-k">${esc(k)}</div>
      <div class="tau-v" style="color:${c}">${esc(shown)}</div>
      <div class="tau-r">${esc(reading)}</div></div>`;
  }

  const tauCell = (k, tau, reading, isRef) =>
    tauTile(k, `τ = ${f(tau, 3)}`, reading, isRef, tau);

  function renderSensitivity() {
    // Rank-order slope chart, computed directly from the scalability series
    // (already fetched for that page's own chart) rather than from a
    // separate endpoint — a rank is just a sort of the same runtimes shown
    // there, so nothing here is a number that page does not already carry.
    const series = (DATA.scalability || []).filter(keep);
    const allNs = new Set();
    series.forEach(sr => sr.points.forEach(p => allNs.add(p.n)));
    const ns = [...allNs].sort((a, b) => a - b);
    if (ns.length >= 2) {
      const nSmall = ns[0], nLarge = ns[ns.length - 1];
      const at = (sr, n) => { const p = sr.points.find(pt => pt.n === n); return p ? p.t : null; };
      const withBoth = series.filter(sr => at(sr, nSmall) !== null && at(sr, nLarge) !== null);
      const rank = n => {
        const sorted = withBoth.slice().sort((a, b) => at(a, n) - at(b, n));
        const m = new Map();
        sorted.forEach((sr, i) => m.set(sr.id, i + 1));
        return m;
      };
      const rankSmall = rank(nSmall), rankLarge = rank(nLarge);
      draw("rankSlopeChart", {
        type: "slope",
        data: {
          categories: [`N = ${nSmall.toLocaleString()}`, `N = ${nLarge.toLocaleString()}`],
          datasets: withBoth.map(sr => ({
            label: sr.id, color: colorOf(sr.framework), dash: lineDash(sr),
            values: [rankSmall.get(sr.id), rankLarge.get(sr.id)],
          })),
        },
        options: { yTick: v => "#" + v },
      });
      figTable("rankSlopeChartTable", [
        { h: "Backend", get: sr => idCell(sr) },
        { h: `Rank at N = ${nSmall.toLocaleString()}`, num: true, get: sr => "#" + rankSmall.get(sr.id) },
        { h: `Rank at N = ${nLarge.toLocaleString()}`, num: true, get: sr => "#" + rankLarge.get(sr.id) },
        { h: "Movement", num: true, get: sr => {
            const d = rankSmall.get(sr.id) - rankLarge.get(sr.id);
            return d === 0 ? "held" : (d > 0 ? "+" + d : String(d));
          } },
      ], withBoth.slice().sort((a, b) => rankSmall.get(a.id) - rankSmall.get(b.id)),
        "Speed rank at the smallest network measured against the largest");
      const moveOf = sr => Math.abs(rankSmall.get(sr.id) - rankLarge.get(sr.id));
      if (withBoth.length) {
        const steadiest = withBoth.filter(sr => !isControl(sr.framework))
          .reduce((a, sr) => (a === null || moveOf(sr) < moveOf(a)) ? sr : a, null);
        const flippedMost = withBoth.reduce((a, sr) => (a === null || moveOf(sr) > moveOf(a)) ? sr : a, null);
        resultLine("rankSlopeResult",
          (steadiest ? `<strong>${esc(steadiest.id)}</strong> holds its rank most closely (#${rankSmall.get(steadiest.id)} &rarr; #${rankLarge.get(steadiest.id)}). ` : "") +
          (flippedMost && moveOf(flippedMost) > 0
            ? `<strong>${esc(flippedMost.id)}</strong> moves the most, from #${rankSmall.get(flippedMost.id)} to #${rankLarge.get(flippedMost.id)}.`
            : `No backend changes rank between the two sizes in the current selection.`));
      } else resultLine("rankSlopeResult", "No backend in the current selection was measured at both the smallest and largest network size.");
    } else resultLine("rankSlopeResult", "Fewer than two network sizes are available for the current selection.");

    const s = DATA.sensitivity || {};
    const sizeEl = document.getElementById("tauSize");
    const metEl = document.getElementById("tauMetric");
    const o2El = document.getElementById("o2Body");

    if (!s.ok) {
      sizeEl.innerHTML = `<div class="empty">${esc(s.error || "No sensitivity data.")}</div>`;
      metEl.innerHTML = ""; o2El.innerHTML = "";
      return;
    }

    sizeEl.innerHTML = s.size_stability.map(r => tauCell(
      `N = ${int(r.n)}`, r.tau,
      r.is_reference ? "reference ordering" : r.reading.split(": ").pop(),
      r.is_reference)).join("");

    const worst = s.size_stability.filter(r => !r.is_reference)
      .reduce((a, r) => (a === null || r.tau < a.tau) ? r : a, null);
    document.getElementById("sizeReading").innerHTML = worst
      ? `<strong>The ordering measured at one size does not carry to another.</strong>
         Against the ordering at the largest network measured, the weakest
         agreement is at N = ${int(worst.n)}, where τ = ${f(worst.tau, 3)}
         (${worst.reading.split(": ").pop()}). A benchmark reporting a
         single small network would therefore recommend a different simulator
         from one reporting a large network, using the same measurements. This
         is the strongest argument in this study against single-point
         benchmarking, and it is why the scalability sweep rather than the
         inference figure carries the simulator-selection guidance.`
      : "";

    metEl.innerHTML = s.metric_stability.map(r => tauCell(
      r.metric, r.tau,
      r.is_reference ? "reference ordering" : r.reading.split(": ").pop(),
      r.is_reference)).join("");

    const mem = s.metric_stability.find(r => /memory/i.test(r.metric));
    const scal = s.metric_stability.find(r => /scaling/i.test(r.metric));
    document.getElementById("metricReading").innerHTML =
      `<strong>Which metric you choose changes which simulator wins.</strong>` +
      (mem ? ` Ranking by peak memory gives τ = ${f(mem.tau, 3)} against ranking
        by runtime (${mem.reading.split(": ").pop()}): the fastest simulator
        here is not necessarily the most memory-efficient one.` : "") +
      (scal ? ` Ranking by scaling exponent gives τ = ${f(scal.tau, 3)}, so how
        fast a simulator is at one size tells a reader almost nothing about how
        its cost grows.` : "") +
      ` A single-metric recommendation is therefore not a recommendation about
        the simulator; it is a recommendation about the metric.`;

    const ev = s.energy_validation;
    o2El.innerHTML = ev
      ? `<div class="tau-grid">
           ${tauTile("Spearman rank correlation",
              `\u03C1 = ${f(ev.rho, 3)}`,
              `energy proxy against EFLOP, ${int(ev.n_pairs)} paired observations across network sizes`,
              false, ev.rho)}
           ${tauTile("Distinct EFLOP values at the largest N",
              int(ev.eflop_distinct_at_ref),
              ev.discriminates
                ? "EFLOP separates the simulators, so the correlation above compares two instruments that both discriminate"
                : "one identical value for every simulator \u2014 EFLOP cannot rank them against each other",
              true, ev.discriminates ? 1 : 0)}
         </div>
         <div class="caveat">${esc(ev.reading)}</div>`
      : `<div class="empty">Not enough paired energy and EFLOP observations to
         compute the correlation.</div>`;
  }

  /* ──────────────────────────────────────────────────── EQUIVALENCE */
  function renderEquivalence() {
    const v = DATA.validation || {};
    const empty = document.getElementById("validEmpty");
    if (!v.ok) {
      empty.hidden = false;
      empty.textContent = v.error || "No validation log.";
      fill("validTable", [], () => "");
      draw("equivScatterChart", { type: "line", data: { datasets: [] } });
      resultLine("equivScatterResult", v.error || "No validation log.");
      return;
    }
    empty.hidden = true;
    const tag = s => s === "pass" ? '<span class="tag tag-good">pass</span>'
      : (s === "not installed" ? '<span class="tag tag-muted">not installed</span>'
        : `<span class="tag tag-bad">${esc(s)}</span>`);
    // The log is keyed by "simulator/backend", so it filters on the same
    // simulator selection as everything else.
    const rows = v.rows.filter(r => active.has(String(r.id).split("/")[0]));
    fill("validTable", rows, r => `
      <td class="name">${sw(String(r.id).split("/")[0])}${esc(r.id)}</td>
      <td>${tag(r.status)}</td>
      <td class="num">${r.rate_hz === null ? "—" : f(r.rate_hz, 1)}</td>
      <td class="num">${r.ref_hz === null ? "—" : f(r.ref_hz, 1)}</td>
      <td class="num">${r.rel === null ? "—" : f(r.rel, 3)}</td>
      <td class="note">${esc(r.message)}</td>`);

    // Measured vs reference rate — a scatter, one dataset per framework,
    // plus a dashed y=x reference line. A point on the line is exact
    // agreement; its distance from the line is the same relative deviation
    // the table states as a number, made visible instead of only tabular.
    const withRates = rows.filter(r => r.rate_hz !== null && r.ref_hz);
    const byFw = {};
    withRates.forEach(r => {
      const fw = String(r.id).split("/")[0];
      (byFw[fw] = byFw[fw] || []).push(r);
    });
    const vals = withRates.flatMap(r => [r.rate_hz, r.ref_hz]);
    const lo = vals.length ? Math.min(...vals) * 0.95 : 0;
    const hi = vals.length ? Math.max(...vals) * 1.05 : 1;
    draw("equivScatterChart", {
      type: "line",
      data: {
        datasets: [
          {
            label: "exact agreement", showLine: true, pointRadius: 0,
            data: [{ x: lo, y: lo }, { x: hi, y: hi }],
            borderColor: T.ink_muted, borderDash: [6, 4], borderWidth: 1.5,
          },
          ...Object.keys(byFw).map(fw => ({
            label: labelOf(fw), showLine: false,
            data: byFw[fw].map(r => ({ x: r.ref_hz, y: r.rate_hz, id: r.id })),
            borderColor: colorOf(fw), backgroundColor: colorOf(fw),
            pointRadius: 5.5, pointHoverRadius: 8,
            pointBorderColor: T.card, pointBorderWidth: 1.4,
          })),
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, padding: 12 } },
          tooltip: Object.assign({}, tooltip, {
            callbacks: {
              title: c => (c[0].raw && c[0].raw.id) ? c[0].raw.id : "exact agreement (y = x)",
              label: c => c.raw.id
                ? [`${f(c.raw.y, 1)} Hz measured`, `${f(c.raw.x, 1)} Hz reference`,
                   `${f(100 * (c.raw.y - c.raw.x) / c.raw.x, 2)}% relative deviation`]
                : [],
            },
          }),
        },
        scales: axes({ xtitle: "reference rate, Hz", ytitle: "measured rate, Hz" }),
      },
    });
    figTable("equivScatterChartTable", [
      { h: "Backend", get: r => ({ t: r.id, c: colorOf(String(r.id).split("/")[0]) }) },
      { h: "Measured (Hz)", num: true, get: r => f(r.rate_hz, 1) },
      { h: "Reference (Hz)", num: true, get: r => f(r.ref_hz, 1) },
      { h: "Relative deviation", num: true, get: r => r.rel === null ? "—" : f(r.rel, 3) },
    ], withRates, "Measured firing rate against the plain-NumPy reference rate");
    if (withRates.length) {
      const devOf = r => Math.abs(r.rate_hz - r.ref_hz) / r.ref_hz * 100;
      const best = withRates.reduce((a, r) => devOf(r) < devOf(a) ? r : a);
      const worst = withRates.reduce((a, r) => devOf(r) > devOf(a) ? r : a);
      resultLine("equivScatterResult",
        `<strong>${esc(best.id)}</strong> sits closest to the reference rate, ${f(devOf(best), 2)}% relative deviation` +
        (best.id === worst.id ? "." : `; <strong>${esc(worst.id)}</strong> is furthest off at ${f(devOf(worst), 2)}%.`));
    } else resultLine("equivScatterResult", "No backend in the current selection has both a measured and a reference rate.");
  }

  /* ───────────────────────────────────────────────────────────── HOME
     Six compact previews, one per experiment page — a thumbnail of that
     page's headline chart plus (for the two pages with no single obvious
     chart) a small strip of colour-coded status blocks. Each teaser reads
     the same filtered data its own page would, so the preview never
     disagrees with what a click through to it shows. */
  function renderHomeTeasers() {
    const inf = eligible(DATA.inference || []);
    const topInf = inf.slice().sort((a, b) => a.runtime_median_s - b.runtime_median_s).slice(0, 6);
    barChart("teaserInference", topInf, "runtime_median_s", {
      logx: true, valueLabel: v => v === null ? "" : f(v * 1000, 2) + " ms",
      label: r => [r.id, `${f(r.runtime_median_s * 1000, 2)} ms median`],
    });
    figTable("teaserInferenceTable", [
      { h: "Backend", get: idCell },
      { h: "Median (ms)", num: true, get: r => f(r.runtime_median_s * 1000, 2) },
    ], topInf, "Fastest six at the reference size");

    const scale = (DATA.scalability || []).filter(keep).slice(0, 6);
    draw("teaserScalability", {
      type: "line",
      data: {
        datasets: scale.map(s => ({
          label: s.id,
          data: s.points.map(p => ({ x: p.n, y: p.t })),
          borderColor: colorOf(s.framework), backgroundColor: colorOf(s.framework),
          borderDash: lineDash(s), borderWidth: 2, pointRadius: 0, tension: 0,
        })),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: axes({ logx: true, logy: true }),
      },
    });
    figTable("teaserScalabilityTable", [
      { h: "Backend", get: idCell },
      { h: "k", num: true, get: s => s.fit ? f(s.fit.k, 3) : "—" },
      { h: "At largest N (s)", num: true, get: s => s.largest_t ? f(s.largest_t, 3) : "—" },
    ], scale, "Fitted scaling exponent and cost at the largest size");

    const mem = eligible(DATA.memory || []);
    const topMem = mem.slice().sort((a, b) => a.peak_mb - b.peak_mb).slice(0, 6);
    barChart("teaserMemory", topMem, "peak_mb", {
      valueLabel: v => v === null ? "" : f(v, 0) + " MB",
      label: r => [r.id, `${f(r.peak_mb, 0)} MB peak`],
    });
    figTable("teaserMemoryTable", [
      { h: "Backend", get: idCell },
      { h: "Peak (MB)", num: true, get: r => f(r.peak_mb, 0) },
    ], topMem, "Smallest six footprints at the largest network size");

    const train = trainRows().filter(
      r => !isControl(r.framework) && r.accuracy_pct !== null);
    const topTrain = train.slice().sort((a, b) => b.accuracy_pct - a.accuracy_pct).slice(0, 6);
    barChart("teaserTraining", topTrain, "accuracy_pct", {
      valueLabel: v => v === null ? "" : f(v, 1) + "%",
      label: r => [r.id, `${f(r.accuracy_pct, 1)}% accuracy`],
    });
    figTable("teaserTrainingTable", [
      { h: "Backend", get: idCell },
      { h: "Accuracy %", num: true, get: r => f(r.accuracy_pct, 2) },
    ], topTrain, "Highest six MNIST test accuracies");

    // Sensitivity — one block per network size tested, coloured by how well
    // the ranking at that size agrees with the reference ordering. A reader
    // sees whether the ranking held (green) or drifted (amber/red) before
    // clicking through for the reading.
    const sens = DATA.sensitivity || {};
    const stripEl = document.getElementById("teaserSensitivity");
    if (stripEl) {
      const rows = (sens.ok && sens.size_stability) || [];
      stripEl.innerHTML = rows.length
        ? rows.map(r => `<span class="strip-seg" style="--c:${tauColor(r.tau)}"
            title="N = ${int(r.n)}: ${r.is_reference ? "reference ordering" : "τ = " + f(r.tau, 2)}"></span>`).join("")
        : `<span class="strip-empty">no sensitivity data</span>`;
      stripEl.innerHTML = rows.length
        ? rows.map(r => `<span class="strip-seg" style="--c:${tauColor(r.tau)}"
            title="N = ${int(r.n)}: ${r.is_reference ? "reference ordering" : "τ = " + f(r.tau, 2)}"
            ><b>${r.is_reference ? "ref" : f(r.tau, 2)}</b><i>N=${int(r.n)}</i></span>`).join("")
        : `<span class="strip-empty">no sensitivity data</span>`;
    }

    // Provenance — one dot per backend's equivalence check, the same
    // pass/fail/not-installed colouring the full table's status tag uses.
    const val = DATA.validation || {};
    const dotsEl = document.getElementById("teaserProvenance");
    if (dotsEl) {
      const rows = ((val.ok && val.rows) || [])
        .filter(r => active.has(String(r.id).split("/")[0]));
      dotsEl.innerHTML = rows.length
        ? rows.map(r => `<span class="dot-seg" style="--c:${
            r.status === "pass" ? T.good
              : (r.status === "not installed" ? T.ink_muted : T.bad)}"
            title="${esc(r.id)}: ${esc(r.status)}"></span>`).join("")
        : `<span class="strip-empty">no validation log</span>`;
      const passN = rows.filter(r => r.status === "pass").length;
      const el = document.getElementById("teaserProvenanceCount");
      if (el) {
        el.textContent = rows.length
          ? `${passN} of ${rows.length} backends pass the equivalence check`
          : "";
      }
    }
  }

  /* ────────────────────────────────────────── PROVENANCE STATUS GRID
     A colour-coded pass/fail/not-installed tile per backend, sitting above
     the full equivalence table — the same categorical read the home-page
     dots give, but with the backend name attached since this page has the
     room for it. */
  function renderProvenanceStatusGrid() {
    const el = document.getElementById("statusGrid");
    const v = DATA.validation || {};
    const rows = (v.ok && v.rows) ? v.rows.filter(r => active.has(String(r.id).split("/")[0])) : [];

    // Pass / fail / not-installed composition — a donut, because "what
    // fraction of the current selection agrees with the reference" is a
    // part-of-whole question the status grid's individual tiles answer one
    // at a time but do not summarise.
    const passN = rows.filter(r => r.status === "pass").length;
    const notInstN = rows.filter(r => r.status === "not installed").length;
    const failN = rows.length - passN - notInstN;
    draw("statusDonut", {
      type: "pie",
      data: {
        labels: ["Pass", "Fail", "Not installed"],
        values: [passN, failN, notInstN],
        colors: [T.good, T.bad, T.ink_muted],
      },
      options: { centreLabel: rows.length ? `${passN}/${rows.length}` : "—", centreSub: "pass" },
    });
    figTable("statusDonutTable", [
      { h: "Status", get: r => r.k },
      { h: "Backends", num: true, get: r => int(r.v) },
      { h: "Share", num: true, get: r => rows.length ? f(100 * r.v / rows.length, 1) + "%" : "—" },
    ], [{ k: "Pass", v: passN }, { k: "Fail", v: failN }, { k: "Not installed", v: notInstN }],
      "Equivalence check: pass / fail composition");
    resultLine("statusDonutResult", rows.length
      ? `<strong>${passN} of ${rows.length}</strong> backend${rows.length === 1 ? "" : "s"} in the current selection pass equivalence against the NumPy reference` +
        (failN ? `, ${failN} fail` : "") + (notInstN ? `, ${notInstN} not installed.` : ".")
      : "No validation log.");

    if (!el) return;
    if (!v.ok || !v.rows) { el.innerHTML = ""; return; }
    const cls = s => s === "pass" ? "good" : (s === "not installed" ? "muted" : "bad");
    el.innerHTML = rows.length ? rows.map(r => {
      const fw = String(r.id).split("/")[0];
      return `<div class="status-tile status-${cls(r.status)}" style="--c:${colorOf(fw)}">
        <div class="status-name">${sw(fw)}${esc(r.id)}</div>
        <div class="status-val">${esc(r.status)}</div>
      </div>`;
    }).join("") : `<div class="empty">No validation log.</div>`;
  }

  /* ───────────────────────────────────────── WHAT THE BASELINES ARE */
  function renderExplain() {
    const el = document.getElementById("explainGrid");
    if (!el) return;
    // The control is placed last so the simulators under test read first,
    // and it is visually distinguished because it is not one of them.
    const ordered = FRAMEWORKS.slice().sort(
      (a, b) => (a.is_control ? 1 : 0) - (b.is_control ? 1 : 0));
    el.innerHTML = ordered.map(fw => `
      <div class="explain" style="--c:${fw.color}">
        <h4>${esc(fw.label)}</h4>
        <div class="kind">${esc(fw.is_control ? "experimental control" : fw.kind)}
          · ${fw.n_backends} backend${fw.n_backends === 1 ? "" : "s"}</div>
        <div class="one">${esc(fw.one_line)}</div>
        <div class="detail">${esc(fw.detail)}</div>
        <div class="best"><b>Best for:</b> ${esc(fw.best_for)}</div>
      </div>`).join("");
  }

  /* ───────────────────────────────────────────────────────── plumbing
     Each page is now a real URL rendering one template (see app.py's
     PAGES / _render_page), so — unlike the old single-document version,
     which called every render* function and toggled seven stacked
     <section class="view"> blocks — only the page actually on screen needs
     rendering. Several render* functions reach for elements (KPI tiles,
     sensitivity tiles, the equivalence empty-state) with no null guard,
     because on the page that owns them those elements always exist; calling
     one on the wrong page would throw, so PAGE decides which run. */
  function renderCurrentPage() {
    switch (PAGE) {
      case "home":        renderKpis(); renderHomeTeasers(); break;
      case "all_simulators": renderAllSimulators(); break;
      case "inference":    renderInference(); break;
      case "scalability":  renderScalability(); break;
      case "memory":       renderMemory(); break;
      case "training":     renderTraining(); break;
      case "sensitivity":  renderSensitivity(); break;
      case "provenance":   renderEquivalence(); renderProvenanceStatusGrid(); break;
      case "about":        renderExplain(); break;
      default: break;
    }
  }

  function syncButtons() {
    document.querySelectorAll(".fw").forEach(b => {
      const on = active.has(b.dataset.fw);
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function wire() {
    document.querySelectorAll(".fw").forEach(b =>
      b.addEventListener("click", () => {
        const fw = b.dataset.fw;
        if (active.has(fw)) active.delete(fw); else active.add(fw);
        saveActive(); syncButtons(); renderCurrentPage();
      }));

    document.getElementById("allBtn").addEventListener("click", () => {
      active = new Set(ALL_FW); saveActive(); syncButtons(); renderCurrentPage();
    });
    document.getElementById("noneBtn").addEventListener("click", () => {
      active = new Set(); saveActive(); syncButtons(); renderCurrentPage();
    });

    // "Show backend detail" and "Guide Open / Guide Close" share the area under the selector bar: one open at a time.
    const panels = [
      { btn: document.getElementById("detailBtn"), panel: document.getElementById("backendPanel"),
        show: "Show backend detail &#9662;", hide: "Hide backend detail &#9652;" },
      { btn: document.getElementById("guideBtn"), panel: document.getElementById("guidePanel"),
        show: "Guide Open &#9662;", hide: "Guide Close &#9652;" },
    ].filter(p => p.btn && p.panel);
    function setPanel(item, open) {
      item.panel.hidden = !open;
      item.btn.setAttribute("aria-expanded", open ? "true" : "false");
      item.btn.innerHTML = open ? item.hide : item.show;
    }
    panels.forEach(item => item.btn.addEventListener("click", () => {
      const open = item.panel.hidden;
      panels.forEach(other => setPanel(other, other === item ? open : false));
    }));
  }

  const DATA_NAMES = ["inference", "scalability", "memory", "training",
                      "validation", "spread", "sensitivity"];

  async function fetchData() {
    const got = await Promise.all(
      DATA_NAMES.map(p => fetch("/api/" + p).then(r => r.json())));
    DATA_NAMES.forEach((n, i) => { DATA[n] = got[i]; });
    // Re-resolved on every fetch, not just at startup: the background refresh
    // is how a newly finished budget first appears, and a stored choice that
    // the data no longer contains must not survive it.
    resolveBudget();
  }

  // Keeps the page current without ever navigating away from it. This used
  // to be a bare <meta http-equiv="refresh"> in dashboard.html that reloaded
  // the whole document every 20 seconds — simple, but it repainted the
  // entire page each cycle, which read as the dashboard flickering or going
  // blank to anyone actually looking at it, and it silently reset whichever
  // simulator filter or view tab the reader had selected. Re-fetching the
  // same data and calling the same render functions again, in place, keeps
  // the numbers fresh with nothing visibly changing unless a value did.
  function startBackgroundRefresh() {
    setInterval(() => {
      fetchData().then(renderCurrentPage).catch(
        err => console.error("background refresh failed:", err));
    }, 20000);
  }

  async function boot() {
    await fetchData();
    syncButtons();
    wire();
    renderCurrentPage();

    if (!HAVE_CHARTS) {
      const host = document.querySelector(".page-content") || document.querySelector(".main-col");
      host.insertAdjacentHTML("afterbegin",
        '<div class="caveat" style="margin:0 0 18px"><strong>Charts could not '
        + 'load.</strong> Chart.js is fetched from a CDN and that request did '
        + 'not succeed — usually no internet connection. Every table, caption '
        + 'and caveat on this page is rendered by the server and is '
        + 'unaffected, so the numbers are all still here. For a dashboard that '
        + 'needs no CDN at all, run <code>streamlit_app.py</code> instead.</div>');
    }

    startBackgroundRefresh();
  }

  boot().catch(err => {
    console.error(err);
    const host = document.querySelector(".page-content") || document.querySelector(".main-col");
    host.insertAdjacentHTML("afterbegin",
      '<div class="card"><div class="card-title">Could not load the results</div>' +
      '<div class="card-sub">' + esc(err.message) +
      '. The page is served, but an /api/ route did not answer — check the ' +
      'terminal running app.py for a traceback.</div></div>');
  });
})();
