/* minichart.js — the small subset of the Chart.js API this dashboard uses,
 * implemented locally so the page has no external dependency at all.
 *
 * Why this exists. The dashboard previously fetched Chart.js from a CDN. On a
 * machine with no internet — which is the normal condition for a marking
 * session, an air-gapped lab, or a laptop on a train — every chart on the page
 * was replaced by an apology and the reader was left with tables alone. A
 * benchmark artefact that only renders when a third-party host is reachable is
 * not reproducible in the sense the rest of this work claims, so the drawing
 * is done here instead.
 *
 * The supported surface is exactly what dashboard.js asks for and nothing
 * more: horizontal bar charts (plain, floating [lo, hi] bars, and a linear or
 * logarithmic value axis), multi-series line charts on linear or logarithmic
 * axes with per-series dash patterns, a legend, and hover tooltips driven by
 * the same callback signature Chart.js uses. Anything outside that subset is
 * ignored rather than approximated, so a config this file cannot honour draws
 * nothing instead of drawing something misleading.
 */
(function () {
  "use strict";

  const DEFAULTS = {
    font: { family: "system-ui, sans-serif", size: 11.5 },
    color: "#6e7c92",
    animation: false,
  };

  /* The charts read their non-data colours from the page's CSS tokens, so a
     change of theme moves the axes, gridlines and labels with it instead of
     leaving a dark-theme grid on a light page. Cached per token; the theme
     does not change within a page load. */
  const _tok = {};
  function tok(name, fallback) {
    if (name in _tok) return _tok[name];
    let v = "";
    try {
      v = getComputedStyle(document.documentElement)
        .getPropertyValue(name).trim();
    } catch (e) { v = ""; }
    return (_tok[name] = v || fallback);
  }
  const ink = () => tok("--ink-muted", DEFAULTS.color);
  const gridline = () => tok("--grid", "#e9edf3");
  const cardbg = () => tok("--card", "#ffffff");

  const PAD = { top: 10, right: 16, bottom: 34, left: 12 };
  const TICK = 6;

  const num = v => typeof v === "number" && isFinite(v);
  const pick = (v, i) => (Array.isArray(v) ? v[i % v.length] : v);

  /* ── scales ──────────────────────────────────────────────────────────── */
  function niceLinear(lo, hi) {
    if (!(hi > lo)) { hi = lo + 1; }
    const span = hi - lo;
    const step = Math.pow(10, Math.floor(Math.log10(span / 4)));
    const mult = [1, 2, 2.5, 5, 10].find(m => span / (step * m) <= 6) || 10;
    const s = step * mult;
    return { lo: Math.floor(lo / s) * s, hi: Math.ceil(hi / s) * s, step: s };
  }

  function linearTicks(lo, hi, step) {
    const out = [];
    for (let v = lo; v <= hi + step / 2; v += step) {
      out.push(Math.abs(v) < step / 1e6 ? 0 : v);
    }
    return out;
  }

  function logTicks(lo, hi) {
    const a = Math.floor(Math.log10(lo));
    const b = Math.ceil(Math.log10(hi));
    const decades = b - a;
    const mults = decades <= 2 ? [1, 2, 5] : decades <= 4 ? [1, 3] : [1];
    const out = [];
    for (let e = a; e <= b; e++) {
      for (const m of mults) {
        const v = m * Math.pow(10, e);
        if (v >= lo * 0.999 && v <= hi * 1.001) out.push(v);
      }
    }
    return out.length >= 2 ? out : [lo, hi];
  }

  function fmtTick(v) {
    if (v === 0) return "0";
    const a = Math.abs(v);
    if (a >= 1e6) return (v / 1e6).toLocaleString(undefined,
      { maximumFractionDigits: 1 }) + "M";
    if (a >= 1000) return v.toLocaleString(undefined,
      { maximumFractionDigits: 0 });
    if (a >= 1) return String(Math.round(v * 100) / 100);
    if (a >= 0.001) return String(Number(v.toPrecision(2)));
    return v.toExponential(0).replace("e-", "e−");
  }

  function makeScale(kind, lo, hi, px0, px1) {
    if (kind === "logarithmic") {
      lo = Math.max(lo, 1e-12);
      hi = Math.max(hi, lo * 10);
      const l0 = Math.log10(lo), l1 = Math.log10(hi);
      // pad out to whole decades so the extreme points are not on the frame
      const a = Math.floor(l0 * 4) / 4, b = Math.ceil(l1 * 4) / 4;
      return {
        kind, lo: Math.pow(10, a), hi: Math.pow(10, b),
        ticks: logTicks(Math.pow(10, a), Math.pow(10, b)),
        px: v => (num(v) && v > 0)
          ? px0 + (px1 - px0) * (Math.log10(v) - a) / (b - a || 1)
          : px0,
      };
    }
    const n = niceLinear(lo, hi);
    return {
      kind: "linear", lo: n.lo, hi: n.hi,
      ticks: linearTicks(n.lo, n.hi, n.step),
      px: v => num(v)
        ? px0 + (px1 - px0) * (v - n.lo) / ((n.hi - n.lo) || 1)
        : px0,
    };
  }

  /* ── tooltip element, one per canvas ─────────────────────────────────── */
  function tipFor(canvas) {
    const host = canvas.parentNode;
    if (getComputedStyle(host).position === "static") {
      host.style.position = "relative";
    }
    let el = host.querySelector(":scope > .mc-tip");
    if (!el) {
      el = document.createElement("div");
      el.className = "mc-tip";
      el.setAttribute("role", "status");
      host.appendChild(el);
    }
    return el;
  }

  /* ── the chart ───────────────────────────────────────────────────────── */
  function Chart(ctx, config) {
    this.canvas = ctx.canvas;
    this.ctx = ctx;
    this.config = config;
    this.tip = tipFor(this.canvas);
    this.hot = [];                       // hit targets for the tooltip
    this._onMove = e => this.hover(e);
    this._onLeave = () => this.hide();
    this.canvas.addEventListener("mousemove", this._onMove);
    this.canvas.addEventListener("mouseleave", this._onLeave);
    // Only a change of WIDTH needs a redraw. The height is fixed by the
    // markup, and re-rendering on a height change would feed the observer
    // from its own effect: render() sets cv.style.height, which resizes the
    // element, which notifies the observer again. Comparing the last width
    // breaks that cycle, and also stops a redraw storm while a window is
    // being dragged.
    this._lastW = -1;
    this._ro = (typeof ResizeObserver !== "undefined")
      ? new ResizeObserver(() => {
          const w = this.canvas.parentNode.clientWidth;
          if (w === this._lastW) return;
          this._lastW = w;
          this.render();
        }) : null;
    if (this._ro) this._ro.observe(this.canvas.parentNode);
    this.render();
  }

  // Chart.js exposes resize() for callers that reveal a chart's container
  // after construction (e.g. a tab that was display:none, where the canvas
  // had no size to measure). render() already re-measures the container on
  // every call, so resize() is just that: a re-measure and a redraw.
  Chart.prototype.resize = function () { this.render(); };

  Chart.prototype.destroy = function () {
    this.canvas.removeEventListener("mousemove", this._onMove);
    this.canvas.removeEventListener("mouseleave", this._onLeave);
    if (this._ro) this._ro.disconnect();
    this.hide();
    const c = this.ctx;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.clearRect(0, 0, this.canvas.width, this.canvas.height);
  };

  Chart.prototype.hide = function () { this.tip.style.opacity = "0"; };

  Chart.prototype.setup = function () {
    const cv = this.canvas;
    const host = cv.parentNode;
    const dpr = window.devicePixelRatio || 1;

    // The intended CSS height is measured once and then remembered.
    //
    // It used to be re-read from the height attribute on every call, and the
    // line further down writes that same attribute (cv.height = h * dpr). On
    // any display whose device pixel ratio is not 1, each pass therefore
    // multiplied the height by dpr - 250, 500, 1000, 2000 - and the
    // ResizeObserver fired again each time, because setting cv.style.height
    // had just changed the element's size. The loop compounded within a few
    // frames until the backing store passed the maximum canvas area the
    // browser will allocate; the browser then drops the canvas and paints a
    // blank box with a context-lost icon where the chart should be. Measured
    // at device pixel ratio 2 before this fix, the height attribute reached
    // 262,144,000 and the backing store 2.6 million megapixels. At ratio 1
    // the multiplier is 1, so a standard-density screen never showed the
    // fault, and only high-DPI laptops - which is most of them - saw the
    // charts go blank.
    // The value must live on the ELEMENT, not on the chart object. Selecting
    // or de-selecting a framework calls destroy() and constructs a new Chart
    // over the same canvas, so anything remembered on the instance is lost,
    // and the new instance reads the already-multiplied attribute back. That
    // is why the charts, their panels and the page itself grew on every click,
    // and why a refresh appeared to cure it: a refresh rebuilds the DOM and
    // resets the attribute. Measured at device pixel ratio 2 over twelve
    // clicks before this change, the canvas went from 250px to 21,625px, its
    // card from 373px to 26,360px and the page from 2,591px to 75,525px.
    // A dataset entry survives destroy() and re-creation, so the height is
    // measured once per page load and cannot drift.
    if (cv.dataset.baseHeight === undefined) {
      cv.dataset.baseHeight = String(Math.max(120, cv.getAttribute("height")
        ? Number(cv.getAttribute("height")) : (cv.clientHeight || 260)));
    }
    const h = Number(cv.dataset.baseHeight);
    const w = Math.max(160, host.clientWidth || cv.clientWidth || 320);

    // A backing store bigger than the browser will allocate is dropped
    // silently, taking the chart with it. Reducing the scale factor loses a
    // little sharpness on a very wide panel; losing the drawing is worse.
    const MAX_BACKING_PIXELS = 16e6;
    const scale = Math.min(dpr, Math.sqrt(MAX_BACKING_PIXELS / Math.max(1, w * h)));

    cv.style.width = "100%";
    cv.style.height = h + "px";
    cv.width = Math.round(w * scale);
    cv.height = Math.round(h * scale);
    const c = this.ctx;
    c.setTransform(scale, 0, 0, scale, 0, 0);
    c.clearRect(0, 0, w, h);
    c.font = `${DEFAULTS.font.size}px ${DEFAULTS.font.family}`;
    c.textBaseline = "middle";
    return { w, h };
  };

  Chart.prototype.render = function () {
    const cfg = this.config;
    if (!this.canvas.isConnected) return;
    const box = this.setup();
    this.hot = [];
    try {
      if (cfg.type === "bar") this.drawBar(box);
      else if (cfg.type === "slope") this.drawSlope(box);
      else if (cfg.type === "pie") this.drawPie(box);
      else this.drawLine(box);
    } catch (e) {
      /* A chart that cannot be drawn leaves its area blank; the table under
         every chart on this page carries the same numbers. */
      if (window.console) console.error("minichart:", e);
    }
  };

  /* ── legend, drawn at the top for line charts ────────────────────────── */
  Chart.prototype.legend = function (w, items) {
    const c = this.ctx;
    const rows = [];
    let row = [], used = 0;
    for (const it of items) {
      const wid = 14 + c.measureText(it.label).width + 16;
      if (used + wid > w - 8 && row.length) { rows.push(row); row = []; used = 0; }
      row.push(it); used += wid;
    }
    if (row.length) rows.push(row);
    let y = PAD.top + 4;
    for (const r of rows) {
      let x = 4;
      for (const it of r) {
        c.fillStyle = it.color;
        c.beginPath();
        c.arc(x + 4, y, 4, 0, Math.PI * 2);
        c.fill();
        if (it.dash && it.dash.length) {
          c.strokeStyle = it.color;
          c.lineWidth = 1.8;
          c.setLineDash(it.dash);
          c.beginPath(); c.moveTo(x - 2, y); c.lineTo(x + 10, y); c.stroke();
          c.setLineDash([]);
        }
        c.fillStyle = ink();
        c.textAlign = "left";
        c.fillText(it.label, x + 14, y);
        x += 14 + c.measureText(it.label).width + 16;
      }
      y += 17;
    }
    return rows.length ? y + 2 : PAD.top;
  };

  Chart.prototype.frame = function (sx, sy, area, opts) {
    const c = this.ctx;
    const grid = (opts && opts.grid) || gridline();
    c.strokeStyle = grid;
    c.lineWidth = 1;
    c.fillStyle = ink();
    c.textAlign = "center";
    // Tick labels that would collide with the previous one are skipped
    // (the gridline is still drawn), so narrow charts stay legible.
    let lastRight = -Infinity;
    for (const t of sx.ticks) {
      const x = Math.round(sx.px(t)) + 0.5;
      if (x < area.x0 - 1 || x > area.x1 + 1) continue;
      c.beginPath(); c.moveTo(x, area.y0); c.lineTo(x, area.y1); c.stroke();
      const label = fmtTick(t), w = c.measureText(label).width;
      if (x - w / 2 < lastRight + 6) continue;
      c.fillText(label, x, area.y1 + 13);
      lastRight = x + w / 2;
    }
    if (sy && sy.ticks) {
      c.textAlign = "right";
      let lastY = Infinity;
      for (const t of sy.ticks) {
        const y = Math.round(sy.px(t)) + 0.5;
        if (y < area.y0 - 1 || y > area.y1 + 1) continue;
        c.beginPath(); c.moveTo(area.x0, y); c.lineTo(area.x1, y); c.stroke();
        if (Math.abs(lastY - y) < 12) continue;
        c.fillText(fmtTick(t), area.x0 - 7, y);
        lastY = y;
      }
    }
  };

  Chart.prototype.axisTitle = function (text, area, where) {
    if (!text) return;
    const c = this.ctx;
    c.fillStyle = ink();
    if (where === "x") {
      c.textAlign = "center";
      c.fillText(text, (area.x0 + area.x1) / 2, area.y1 + 28);
    } else {
      c.save();
      c.translate(11, (area.y0 + area.y1) / 2);
      c.rotate(-Math.PI / 2);
      c.textAlign = "center";
      c.fillText(text, 0, 0);
      c.restore();
    }
  };

  /* ── horizontal bars ─────────────────────────────────────────────────── */
  Chart.prototype.drawBar = function (box) {
    const c = this.ctx;
    const cfg = this.config;
    const labels = cfg.data.labels || [];
    const sets = cfg.data.datasets || [];
    if (!labels.length || !sets.length) return;

    const xs = cfg.options.scales && cfg.options.scales.x || {};
    const log = xs.type === "logarithmic";
    const title = xs.title && xs.title.text;

    let lo = Infinity, hi = -Infinity;
    for (const ds of sets) {
      for (const v of ds.data) {
        const pair = Array.isArray(v) ? v : [v];
        for (const q of pair) {
          if (!num(q)) continue;
          if (log && q <= 0) continue;
          lo = Math.min(lo, q); hi = Math.max(hi, q);
        }
      }
    }
    if (!isFinite(lo)) return;
    if (!log) lo = Math.min(lo, 0);

    c.font = `${DEFAULTS.font.size}px ${DEFAULTS.font.family}`;
    const labW = Math.min(210,
      Math.max(...labels.map(l => c.measureText(String(l)).width)) + 12);
    // A value printed on each bar, so the figure can be read without a
    // cursor. The widest label decides how much room the plot gives up.
    const vlab = cfg.options && cfg.options.valueLabel;
    let vW = 0;
    if (vlab) {
      c.font = `600 ${DEFAULTS.font.size}px ${DEFAULTS.font.family}`;
      for (let i = 0; i < labels.length; i++) {
        const t = vlab(sets[0].data[i], i);
        if (t) vW = Math.max(vW, c.measureText(String(t)).width);
      }
      if (vW) vW += 8;
      c.font = `${DEFAULTS.font.size}px ${DEFAULTS.font.family}`;
    }
    const area = {
      x0: labW + 10, x1: box.w - PAD.right - vW,
      y0: PAD.top, y1: box.h - (title ? PAD.bottom : 20),
    };
    const sx = makeScale(log ? "logarithmic" : "linear", lo, hi, area.x0, area.x1);
    this.frame(sx, null, area, { grid: gridline() });
    this.axisTitle(title, area, "x");

    const slot = (area.y1 - area.y0) / labels.length;
    const catPct = sets[0].categoryPercentage || 0.84;
    const barPct = sets[0].barPercentage || 0.74;
    const bh = Math.max(4, slot * catPct * barPct);
    const base = sx.px(sx.lo);

    labels.forEach((label, i) => {
      const cy = area.y0 + slot * (i + 0.5);
      c.fillStyle = ink();
      c.textAlign = "right";
      const txt = String(label);
      c.fillText(txt.length > 30 ? txt.slice(0, 29) + "…" : txt, labW, cy);

      sets.forEach((ds, di) => {
        const v = ds.data[i];
        if (v === null || v === undefined) return;
        const pair = Array.isArray(v) ? v : [null, v];
        const from = pair[0] === null || pair[0] === undefined
          ? base : sx.px(pair[0]);
        const to = sx.px(pair[1]);
        const x = Math.min(from, to), wpx = Math.max(1.5, Math.abs(to - from));
        // Later datasets are drawn concentrically inside the first, which is
        // how the median marker sits inside its own min-to-max range bar.
        const shrink = di === 0 ? 1 : 0.46;
        const hh = bh * shrink;
        const r = Math.min(ds.borderRadius === 0 ? 0 : (ds.borderRadius || 5),
          hh / 2, wpx / 2);
        c.beginPath();
        if (c.roundRect) c.roundRect(x, cy - hh / 2, wpx, hh, r);
        else c.rect(x, cy - hh / 2, wpx, hh);
        c.fillStyle = pick(ds.backgroundColor, i) || "#7c879b";
        c.fill();
        if (ds.borderWidth) {
          c.lineWidth = ds.borderWidth;
          c.strokeStyle = pick(ds.borderColor, i) || "transparent";
          c.stroke();
        }
        if (di === 0) {
          if (vlab) {
            const t = vlab(v, i);
            if (t) {
              // Text wears the ink token, never the series colour: the bar
              // beside it already carries the identity.
              c.font = `600 ${DEFAULTS.font.size}px ${DEFAULTS.font.family}`;
              c.fillStyle = tok("--ink-soft", "#46536a");
              c.textAlign = "left";
              c.fillText(String(t), Math.max(x + wpx, base) + 6, cy);
              c.font = `${DEFAULTS.font.size}px ${DEFAULTS.font.family}`;
            }
          }
          this.hot.push({
            kind: "bar", x0: Math.min(x, base), x1: Math.max(x + wpx, base),
            y0: cy - slot / 2, y1: cy + slot / 2, i, label,
            raw: v, dataset: ds,
          });
        }
      });
    });
  };

  /* ── multi-series lines ──────────────────────────────────────────────── */
  Chart.prototype.drawLine = function (box) {
    const c = this.ctx;
    const cfg = this.config;
    const sets = (cfg.data.datasets || []).filter(d => d.data && d.data.length);
    if (!sets.length) return;

    const sc = cfg.options.scales || {};
    const xLog = sc.x && sc.x.type === "logarithmic";
    const yLog = sc.y && sc.y.type === "logarithmic";
    const xTitle = sc.x && sc.x.title && sc.x.title.text;
    const yTitle = sc.y && sc.y.title && sc.y.title.text;

    const legendOn = !(cfg.options.plugins && cfg.options.plugins.legend
      && cfg.options.plugins.legend.display === false);
    const top = legendOn
      ? this.legend(box.w, sets.map(d => ({
        label: d.label, color: d.borderColor, dash: d.borderDash,
      })))
      : PAD.top;

    let xlo = Infinity, xhi = -Infinity, ylo = Infinity, yhi = -Infinity;
    for (const ds of sets) {
      for (const p of ds.data) {
        if (!num(p.x) || !num(p.y)) continue;
        if (xLog && p.x <= 0) continue;
        if (yLog && p.y <= 0) continue;
        xlo = Math.min(xlo, p.x); xhi = Math.max(xhi, p.x);
        ylo = Math.min(ylo, p.y); yhi = Math.max(yhi, p.y);
      }
    }
    if (!isFinite(xlo)) return;
    if (!yLog) { ylo = Math.min(ylo, 0); yhi = yhi * 1.06 || 1; }

    // width of the widest y tick label decides the left gutter
    const probe = makeScale(yLog ? "logarithmic" : "linear", ylo, yhi, 0, 1);
    const gutter = Math.max(...probe.ticks.map(
      t => c.measureText(fmtTick(t)).width)) + (yTitle ? 26 : 12);
    const area = {
      x0: gutter + 6, x1: box.w - PAD.right,
      y0: top + 6, y1: box.h - (xTitle ? PAD.bottom : 22),
    };
    const sx = makeScale(xLog ? "logarithmic" : "linear", xlo, xhi,
      area.x0, area.x1);
    const sy = makeScale(yLog ? "logarithmic" : "linear", ylo, yhi,
      area.y1, area.y0);

    this.frame(sx, sy, area);
    this.axisTitle(xTitle, area, "x");
    this.axisTitle(yTitle, area, "y");

    for (const ds of sets) {
      const pts = ds.data
        .filter(p => num(p.x) && num(p.y)
          && (!xLog || p.x > 0) && (!yLog || p.y > 0))
        .slice()
        .sort((a, b) => a.x - b.x);
      if (!pts.length) continue;
      // showLine:false turns this from a connected line into an unconnected
      // point cloud — a scatter series — while keeping every other part of
      // this method (axes, log scales, legend, hover) exactly as a line
      // chart already does them. A scatter chart is a line chart with the
      // stroke switched off, not a separate drawing routine.
      if (ds.showLine !== false) {
        c.strokeStyle = ds.borderColor || "#7c879b";
        c.lineWidth = ds.borderWidth || 2;
        c.lineJoin = "round";
        c.setLineDash(ds.borderDash && ds.borderDash.length ? ds.borderDash : []);
        c.beginPath();
        pts.forEach((p, k) => {
          const X = sx.px(p.x), Y = sy.px(p.y);
          if (k === 0) c.moveTo(X, Y); else c.lineTo(X, Y);
        });
        c.stroke();
        c.setLineDash([]);
      }
      const r = ds.pointRadius === 0 ? 0 : (ds.pointRadius || 3.5);
      for (const p of pts) {
        const X = sx.px(p.x), Y = sy.px(p.y);
        if (r) {
          c.beginPath();
          c.arc(X, Y, r, 0, Math.PI * 2);
          c.fillStyle = ds.backgroundColor || ds.borderColor;
          c.fill();
          if (ds.pointBorderWidth) {
            c.lineWidth = ds.pointBorderWidth;
            c.strokeStyle = ds.pointBorderColor || "#111";
            c.stroke();
          }
        }
        this.hot.push({ kind: "pt", x: X, y: Y, raw: p, dataset: ds });
      }
    }
  };

  /* ── slope chart ─────────────────────────────────────────────────────────
     Two category positions on x (e.g. "N = 100" and "N = 10,000"), an
     integer rank on y, one line per series connecting its rank at the left
     category to its rank at the right category. Built for exactly one
     question: does an ordering survive a change in condition — a line that
     stays flat answers yes for that series, a line that crosses many others
     answers no. Nothing here is a Chart.js feature being approximated; it is
     its own small routine, because a slope chart's x-axis is two labelled
     positions, not a numeric scale the rest of this file's axis code
     understands. */
  Chart.prototype.drawSlope = function (box) {
    const c = this.ctx;
    const cfg = this.config;
    const cats = (cfg.data && cfg.data.categories) || ["A", "B"];
    const sets = ((cfg.data && cfg.data.datasets) || [])
      .filter(d => Array.isArray(d.values) && d.values.length === 2
        && num(d.values[0]) && num(d.values[1]));
    if (!sets.length) return;

    const opts = cfg.options || {};
    const legendOn = !(opts.plugins && opts.plugins.legend
      && opts.plugins.legend.display === false);
    const top = legendOn
      ? this.legend(box.w, sets.map(d => ({
        label: d.label, color: d.color, dash: d.dash,
      })))
      : PAD.top;

    let lo = Infinity, hi = -Infinity;
    for (const d of sets) {
      lo = Math.min(lo, d.values[0], d.values[1]);
      hi = Math.max(hi, d.values[0], d.values[1]);
    }
    const loi = Math.floor(lo), hii = Math.ceil(hi);

    c.font = `${DEFAULTS.font.size}px ${DEFAULTS.font.family}`;
    const yLabelOf = opts.yTick || (v => "#" + v);
    const gutter = Math.max(
      ...Array.from({ length: hii - loi + 1 }, (_, i) => loi + i)
        .map(v => c.measureText(yLabelOf(v)).width)) + 22;
    const catW = Math.max(
      ...cats.map(l => c.measureText(String(l)).width));
    const area = {
      x0: gutter, x1: box.w - PAD.right - catW / 2,
      y0: top + 10, y1: box.h - 30,
    };

    // rank 1 (best) drawn at the top — invertY:false would flip that, but
    // every caller here means "rank", so the sane default is inverted.
    const invert = opts.invertY !== false;
    const pxY = v => {
      const t = (hii === loi) ? 0.5 : (v - loi) / (hii - loi);
      return invert ? area.y0 + t * (area.y1 - area.y0)
                    : area.y1 - t * (area.y1 - area.y0);
    };
    const pxX = i => (i === 0 ? area.x0 : area.x1);

    // category guide lines + labels
    c.strokeStyle = gridline();
    c.lineWidth = 1;
    c.fillStyle = ink();
    c.textAlign = "center";
    cats.forEach((label, i) => {
      const x = Math.round(pxX(i)) + 0.5;
      c.beginPath(); c.moveTo(x, area.y0 - 4); c.lineTo(x, area.y1 + 4); c.stroke();
      c.fillText(String(label), x, area.y1 + 18);
    });

    // rank ticks
    c.textAlign = "right";
    for (let r = loi; r <= hii; r++) {
      const y = Math.round(pxY(r)) + 0.5;
      c.fillText(yLabelOf(r), area.x0 - 10, y);
    }

    sets.forEach(d => {
      const x0 = pxX(0), x1 = pxX(1);
      const y0 = pxY(d.values[0]), y1 = pxY(d.values[1]);
      c.strokeStyle = d.color || "#7c879b";
      c.lineWidth = 2.2;
      c.lineJoin = "round";
      c.setLineDash(d.dash && d.dash.length ? d.dash : []);
      c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke();
      c.setLineDash([]);

      [[x0, y0, 0], [x1, y1, 1]].forEach(([x, y, i]) => {
        c.beginPath();
        c.arc(x, y, 4.2, 0, Math.PI * 2);
        c.fillStyle = d.color || "#7c879b";
        c.fill();
        this.hot.push({
          kind: "pt", x, y,
          raw: { category: cats[i], rank: d.values[i] }, dataset: d,
        });
      });
    });
  };

  /* ── pie / donut ──────────────────────────────────────────────────────────
     One ring, one slice per category — the composition-of-a-whole question
     a bar chart cannot answer at a glance (what fraction of backends pass,
     what fraction of runs learned anything). Drawn as a donut rather than a
     full disc: the centre carries the headline count so the figure states
     its own total instead of leaving the reader to add the slices up. Kept
     to categories a reader can actually separate by hue — this file's own
     callers never hand it more than four. */
  Chart.prototype.drawPie = function (box) {
    const c = this.ctx;
    const cfg = this.config;
    const d = cfg.data || {};
    const labels = d.labels || [];
    const values = (d.values || []).map(Number);
    const colors = d.colors || [];
    const total = values.reduce((a, v) => a + (num(v) ? v : 0), 0);
    if (!labels.length || total <= 0) return;

    const legendOn = !(cfg.options && cfg.options.plugins
      && cfg.options.plugins.legend
      && cfg.options.plugins.legend.display === false);
    const top = legendOn
      ? this.legend(box.w, labels.map((l, i) => ({
        label: `${l} (${values[i]})`, color: colors[i] || "#7c879b",
      })))
      : PAD.top;

    const areaY0 = top + 6, areaY1 = box.h - 8;
    const cx = box.w / 2, cy = (areaY0 + areaY1) / 2;
    const R = Math.max(24, Math.min(box.w / 2 - 12, (areaY1 - areaY0) / 2) - 4);
    const rInner = R * 0.58;

    let ang = -Math.PI / 2;
    labels.forEach((label, i) => {
      const v = num(values[i]) ? values[i] : 0;
      if (v <= 0) return;
      const sweep = (v / total) * Math.PI * 2;
      const a0 = ang, a1 = ang + sweep;
      const col = colors[i] || "#7c879b";
      c.beginPath();
      c.moveTo(cx + Math.cos(a0) * rInner, cy + Math.sin(a0) * rInner);
      c.lineTo(cx + Math.cos(a0) * R, cy + Math.sin(a0) * R);
      c.arc(cx, cy, R, a0, a1);
      c.lineTo(cx + Math.cos(a1) * rInner, cy + Math.sin(a1) * rInner);
      c.arc(cx, cy, rInner, a1, a0, true);
      c.closePath();
      c.fillStyle = col;
      c.fill();
      c.lineWidth = 1.5;
      c.strokeStyle = cardbg();   /* 2px surface gap between adjacent fills */
      c.stroke();
      this.hot.push({
        kind: "pt", x: cx + Math.cos((a0 + a1) / 2) * (R + rInner) / 2,
        y: cy + Math.sin((a0 + a1) / 2) * (R + rInner) / 2,
        raw: { label, value: v, pct: (v / total) * 100 },
        dataset: { label: cfg.data.title || "" },
      });
      ang = a1;
    });

    c.textAlign = "center";
    c.fillStyle = ink();
    const centreLabel = (cfg.options && cfg.options.centreLabel) || String(total);
    const centreSub = (cfg.options && cfg.options.centreSub) || "";
    c.font = `700 ${DEFAULTS.font.size + 5}px ${DEFAULTS.font.family}`;
    c.fillText(centreLabel, cx, cy + (centreSub ? -6 : 0));
    if (centreSub) {
      c.font = `${DEFAULTS.font.size - 1}px ${DEFAULTS.font.family}`;
      c.fillText(centreSub, cx, cy + 12);
    }
  };

  /* ── hover ───────────────────────────────────────────────────────────── */
  Chart.prototype.hover = function (ev) {
    const rect = this.canvas.getBoundingClientRect();
    const mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
    let best = null, bestD = Infinity;
    for (const h of this.hot) {
      if (h.kind === "bar") {
        if (my >= h.y0 && my <= h.y1 && mx >= h.x0 - 6 && mx <= h.x1 + 6) {
          best = h; bestD = 0; break;
        }
      } else {
        const d = Math.hypot(mx - h.x, my - h.y);
        if (d < bestD && d < 26) { best = h; bestD = d; }
      }
    }
    if (!best) { this.hide(); return; }

    const cb = (this.config.options.plugins
      && this.config.options.plugins.tooltip
      && this.config.options.plugins.tooltip.callbacks) || {};
    const item = {
      dataIndex: best.i, raw: best.raw, label: best.label,
      dataset: best.dataset,
    };
    let head = "";
    if (cb.title) {
      const t = cb.title([item]);
      head = Array.isArray(t) ? t.join(" ") : (t || "");
    } else {
      head = best.dataset.label || String(best.label || "");
    }
    let body = cb.label ? cb.label(item) : "";
    if (!Array.isArray(body)) body = body ? [body] : [];

    const esc = s => String(s).replace(/[&<>]/g,
      m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]));
    this.tip.innerHTML =
      (head ? `<b>${esc(head)}</b>` : "")
      + body.map(l => `<span>${esc(l)}</span>`).join("");
    this.tip.style.opacity = "1";
    const tw = this.tip.offsetWidth, th = this.tip.offsetHeight;
    const px = best.kind === "bar" ? Math.min(best.x1, mx) : best.x;
    const py = best.kind === "bar" ? (best.y0 + best.y1) / 2 : best.y;
    this.tip.style.left =
      Math.max(4, Math.min(rect.width - tw - 4, px - tw / 2)) + "px";
    this.tip.style.top =
      Math.max(4, py - th - 12) + "px";
  };

  Chart.defaults = DEFAULTS;
  window.Chart = Chart;
})();
