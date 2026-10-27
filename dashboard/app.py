"""Building a Benchmarking Dashboard for SNN Methods — Flask application.

Reads the results database produced by the benchmark suite and serves one
page. All data access is delegated to dashboard_data.py, shared with
streamlit_app.py, the pure-Python alternative in this same folder — pick
whichever one you want to run; both read the same database, the same
dashboard_config.py and the same dashboard_theme.py, so the two pages cannot
report different numbers for the same condition.

Single hardware platform. This is a controlled comparison: the machine is held
fixed so that a difference in runtime can be attributed to a difference in the
simulator rather than to the hardware it happened to run on. That is why there
is no hardware selector — every row was measured under identical conditions,
which is the property that makes the comparison valid. Extending the same
harness to GPU hardware is set out as future work in the thesis.

Two rules govern what appears on the page:

  1. Nothing is displayed without a value. A panel that renders a dash, a zero
     or an empty cell for a quantity that was never measured is
     indistinguishable from one reporting a genuine zero. Unmeasured
     quantities are labelled in words.

  2. Nothing that mutates the stored results is exposed. An earlier version of
     this dashboard had a Run Benchmark button that cleared the measured rows
     before re-running; it destroyed a full result set once. The Run Benchmark
     control here starts the command-line harness as a separate process and
     never deletes anything — the harness appends, and the dashboard reads.
"""
from __future__ import annotations
import csv
import io
import math
import sys
from datetime import datetime
from pathlib import Path

try:
    from flask import Flask, Response, jsonify, render_template, request
except ImportError:
    sys.exit(
        "\n  Flask is not installed in this Python environment.\n"
        "  Install it, then run this file again:\n\n"
        f"      {sys.executable} -m pip install flask\n\n"
        "  (Prefer no JavaScript at all? Run streamlit_app.py instead —\n"
        "  see dashboard/requirements-streamlit.txt.)\n")

import dashboard_config as config
import dashboard_data as data
import dashboard_theme as theme
import optimization
import robustness

app = Flask(__name__)

# Do not let a browser hold on to a stale copy of the chart code.
#
# This dashboard is served from disk on the same machine that is viewing it,
# so there is nothing to gain from caching the static files and something to
# lose: after a fix to dashboard.js or minichart.js, a browser that reuses its
# cached copy keeps showing the old behaviour, and the person looking at it
# has no way to tell that the file on disk already differs. Revalidating on
# every request costs nothing across localhost.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.after_request
def _no_store_static(response):
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


# The dashboard reads and never writes. Starting a measurement campaign is
# the command line's job (`python run.py bench`), for two reasons that the
# results themselves supply. A campaign has to run on an otherwise idle
# machine, which a browser session is evidence against; and because the
# results store is append-only, a sweep started casually on a second computer
# would append rows measured on different hardware, which is precisely the
# defect Section 4.8 of the thesis documents. Keeping the write path in the
# terminal makes starting a campaign a deliberate act.

# --------------------------------------------------------------------- pages
#
# One template, one real URL, per experiment — a reader clicking "Scalability"
# in the sidebar gets a server-rendered page at /scalability, not a section of
# a single giant document toggled by JavaScript. This used to be one route
# (index()) rendering one template (dashboard.html) with all seven views
# stacked in the DOM and shown/hidden client-side; PAGES below is that same
# per-view content, split so each has its own address, and its own focused
# page rather than sharing space with six others.
PAGES = {
    "home":        ("home.html", "Dashboard",
                     "Summary and a starting point for each experiment."),
    "optimization": ("optimization.html", "Optimisation",
                     "Select measured SNN methods by inference, memory, scalability and exploratory accuracy priorities."),
    "all_simulators": ("all_simulators.html", "All Simulators",
                     "Every headline KPI, ranked across every simulator measured — no charts, just the numbers, in order."),
    "inference":   ("inference.html", "Inference",
                     "Single-run cost: wall-clock time, peak memory, energy proxy and CPU utilisation."),
    "scalability": ("scalability.html", "Scalability",
                     "How runtime grows with network size, and the fitted scaling exponent per backend."),
    "memory":      ("memory.html", "Memory",
                     "Peak footprint against network size, and the repeatability of the quoted medians."),
    "training":    ("training.html", "Training",
                     "MNIST test accuracy and cost per epoch, one native learning rule per simulator."),
    "sensitivity": ("sensitivity.html", "Sensitivity",
                     "Experiment 4 — whether the simulator ranking survives a change in size or metric."),
    "robustness":  ("robustness.html", "Robustness",
                     "Which recommendations survive a change of normalisation, session or criteria, and what a wrong-size choice costs."),
    "provenance":  ("provenance.html", "Equivalence & provenance",
                     "Cross-backend equivalence checks, plus the machine, package and configuration record."),
    "about":       ("about.html", "Methods and limitations",
                     "Evidence scope, method descriptions and limitations of recommendations."),
}


def _render_page(page, **extra):
    # The page must always render. Building the shell out of live queries
    # meant a single failing query took the whole document with it: Flask
    # returned its 500 page, and a 500 page with no body is what the user sees
    # as a blank browser window. The shell is therefore built defensively and
    # any failure is reported in words inside the page, which is the same rule
    # ("nothing is displayed without a value") that governs the panels.
    template, page_title, page_sub = PAGES[page]
    meta = data.get_meta()
    try:
        frameworks = [f for f in data.get_frameworks() if not f["is_control"]]
        backends = [b for b in data.get_backends() if b["framework"] != "reference"]
        gaps = data.get_gaps()
    except Exception as exc:  # noqa: BLE001 - deliberately broad; see above
        frameworks, backends, gaps = [], [], []
        meta = dict(meta, ok=False,
                    error=f"Could not read the results database at "
                          f"{config.DB_PATH}: {exc}")
    return render_template(
        template,
        page=page,
        **extra,
        page_title=page_title,
        page_sub=page_sub,
        title=config.TITLE,
        subtitle=config.SUBTITLE,
        author=getattr(config, "AUTHOR", ""),
        institution=getattr(config, "INSTITUTION", ""),
        loaded_at=datetime.now().strftime("%H:%M:%S"),
        meta=meta,
        frameworks=frameworks,
        backends=backends,
        gaps=gaps,
        theme=dict(
            surface=theme.SURFACE, card=theme.CARD, card_alt=theme.CARD_ALT,
            border=theme.BORDER, grid=theme.GRID, ink=theme.INK,
            ink_soft=theme.INK_SOFT, ink_muted=theme.INK_MUTED,
            good=theme.GOOD, warn=theme.WARN, bad=theme.BAD,
            colors=theme.FRAMEWORK_COLORS, labels=theme.FRAMEWORK_LABELS,
            controls=sorted(theme.CONTROL_FRAMEWORKS)),
    )


@app.context_processor
def _guide_context():
    """The reading guide in the simulator bar is built only when a page template asks for it, and a
    failure to compute the take-aways never stops a page from rendering."""
    def guide_items():
        try:
            tk = robustness.takeaways()
        except Exception:                      # noqa: BLE001 - the guide is optional
            tk = []
        return dict(reading_path=robustness.READING_PATH, takeaways=tk)
    return dict(guide_items=guide_items)


@app.route("/")
def index():
    return _render_page("home")


@app.route("/all-simulators")
def page_all_simulators():
    return _render_page("all_simulators")


def _multi_optimisation():
    """Unified parsing path for page, live fragment and CSV export."""
    sizes = optimization.available_sizes()
    n = int(request.args.get("n", sizes[0] if sizes else 100))
    weights = {key: float(request.args.get(key, default))
               for key, default in optimization.DEFAULT_WEIGHTS.items()}
    cap = request.args.get("cap", "")
    norm = request.args.get("norm", "minmax")
    result = optimization.evaluate_four(n, weights, cap, normalisation=norm)
    robustness.decorate(result, n, weights, cap, norm)
    result["answer"] = robustness.answer(result)
    if result.get("ok"):
        result["profiles"] = robustness.attach_profile_ties(
            optimization.evaluate_profiles(n, cap, normalisation=norm, extra=weights))
        result["softmax"] = optimization.softmax_priorities(result["profiles"])
        result["softmax_charts"] = _softmax_charts(result["softmax"])
    return sizes, result


def _softmax_charts(sm, width=660, height=320):
    """SVG geometry of the activation curve for every profile: the score axis
    runs from 1 (left) to 0 (right) so that better simulators sit to the right,
    and the priority axis is on the left."""
    left, right, top, bottom = 60, 20, 16, 48
    w, h = width - left - right, height - top - bottom
    charts = {}
    for pf in sm["profiles"]:
        c = optimization.softmax_curve(pf, sm["tau"])
        pmax = max(p["priority"] for p in c["points"])
        ymax = min(1.0, max(0.5, math.ceil(pmax * 10 + 0.5) / 10))
        px = lambda x: left + (1 - x) * w
        py = lambda y: top + (1 - min(y, ymax) / ymax) * h
        shown = [(x, y) for x, y in c["curve"] if y <= ymax * 1.02]
        path = " ".join(("M" if i == 0 else "L") + f"{px(x):.1f},{py(y):.1f}"
                        for i, (x, y) in enumerate(shown))
        pts, used = [], []
        for p in c["points"]:
            x, y = px(p["score"]), py(p["priority"])
            options = [o for k in range(6) for o in (y - 8 - 15 * k, y + 18 + 15 * k)]
            options = [o for o in options if top + 10 < o < top + h - 4] or [top + 10]
            ly = next((o for o in options if all(abs(o - u) >= 15 for u in used)), options[0])
            used.append(ly)
            far_left = x < left + 0.45 * w
            pts.append(dict(p, x=round(x, 1), y=round(y, 1), ly=round(ly, 1),
                            lx=round(x + 8 if far_left else x - 8, 1),
                            anchor="start" if far_left else "end",
                            label=theme.FRAMEWORK_LABELS.get(p["simulator"], p["simulator"])))
        yt = [round(ymax * k / 5, 2) for k in range(6)]
        charts[pf["key"]] = dict(
            path=path, points=pts, width=width, height=height, left=left, top=top,
            right=width - right, bottom=top + h,
            yticks=[dict(v=v, y=round(py(v), 1)) for v in yt],
            xticks=[dict(v=v, x=round(px(v), 1)) for v in (1.0, 0.8, 0.6, 0.4, 0.2, 0.0)])
    return charts


@app.route("/optimization")
def page_optimization():
    error = None
    try:
        sizes, result = _multi_optimisation()
    except (ValueError, TypeError) as exc:
        error = f"Invalid optimisation settings: {exc}. Showing defaults."
        sizes = optimization.available_sizes()
        result = optimization.evaluate_four(sizes[0] if sizes else 100)
        robustness.decorate(result, sizes[0] if sizes else 100, None, None, "minmax")
        result["answer"] = robustness.answer(result)
    meta = data.get_meta()
    return render_template(
        "optimization.html", page="optimization", page_title="Optimisation",
        page_sub="Four-criterion, weight-aware selection of measured SNN methods",
        title=config.TITLE, subtitle=config.SUBTITLE,
        author=getattr(config, "AUTHOR", ""), institution=getattr(config, "INSTITUTION", ""),
        loaded_at=datetime.now().strftime("%H:%M:%S"), meta=meta,
        frameworks=[f for f in data.get_frameworks() if not f["is_control"]],
        backends=[b for b in data.get_backends() if b["framework"] != "reference"],
        gaps=data.get_gaps(), sizes=sizes, opt=result, error=error,
        presets=robustness.presets(), glossary=robustness.GLOSSARY, backend_names=robustness.names(),
        how_to_read=robustness.HOW_TO_READ,
        theme=dict(surface=theme.SURFACE, card=theme.CARD, card_alt=theme.CARD_ALT,
                   border=theme.BORDER, grid=theme.GRID, ink=theme.INK,
                   ink_soft=theme.INK_SOFT, ink_muted=theme.INK_MUTED,
                   good=theme.GOOD, warn=theme.WARN, bad=theme.BAD,
                   colors=theme.FRAMEWORK_COLORS, labels=theme.FRAMEWORK_LABELS,
                   controls=sorted(theme.CONTROL_FRAMEWORKS)))


@app.route("/api/optimization/fragment")
def api_optimization_fragment():
    try:
        _, result = _multi_optimisation()
    except (ValueError, TypeError) as exc:
        return Response(str(exc), status=400, mimetype="text/plain")
    return render_template("optimization_results.html", opt=result,
                           theme=dict(colors=theme.FRAMEWORK_COLORS, labels=theme.FRAMEWORK_LABELS))


@app.route("/api/optimization.csv")
def api_optimization_csv():
    try:
        _, result = _multi_optimisation()
    except (ValueError, TypeError) as exc:
        return Response(str(exc), status=400, mimetype="text/plain")
    fields = ["id", "framework", "backend", "runtime_s", "memory_mb", "memory_growth_mb",
              "scaling_k", "scaling_r2", "accuracy_pct", "score", "pareto",
              "inference_cost", "memory_cost", "scalability_cost", "accuracy_cost",
              "scenario_wins", "rank_sum", "cv_pct", "n_runs"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(result["rows"])
    return Response(buf.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": f"attachment; filename=optimization-four-criteria-N{result['network_size']}-{result['normalisation']}.csv"})


@app.route("/robustness")
def page_robustness():
    rb = robustness.load_robustness()
    return _render_page("robustness", rb=rb, rb_lead=robustness.robustness_lead(rb))


@app.route("/api/robustness.csv")
def api_robustness_csv():
    rows = robustness.export_rows()
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, restval="")
    writer.writeheader()
    writer.writerows(rows)
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="robustness.csv"'})


@app.route("/api/robustness.json")
def api_robustness_json():
    return Response(robustness.export_json(), mimetype="application/json",
                    headers={"Content-Disposition": 'attachment; filename="robustness.json"'})


@app.route("/inference")
def page_inference():
    return _render_page("inference")


@app.route("/scalability")
def page_scalability():
    return _render_page("scalability")


@app.route("/memory")
def page_memory():
    return _render_page("memory")


@app.route("/training")
def page_training():
    return _render_page("training")


@app.route("/sensitivity")
def page_sensitivity():
    return _render_page("sensitivity")


@app.route("/provenance")
def page_provenance():
    return _render_page("provenance")


@app.route("/about")
def page_about():
    return _render_page("about")


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.errorhandler(Exception)
def handle_unexpected(exc):
    """Never answer with Flask's bare 500 page.

    An /api/ route that dies returns HTML, which the fetch() calls in
    dashboard.js cannot parse; the chart then fails silently and the panel
    stays empty with nothing on the page to say why. Returning JSON on those
    routes lets the browser report the reason, and returning readable text
    elsewhere means a failure is never an empty window."""
    from werkzeug.exceptions import HTTPException
    if isinstance(exc, HTTPException):   # 404 and friends pass through
        return exc
    app.logger.exception("unhandled error serving %s", request.path)
    if request.path.startswith("/api/"):
        return jsonify(ok=False, error=f"{type(exc).__name__}: {exc}"), 500
    return Response(
        f"The dashboard could not build this page.\n\n"
        f"{type(exc).__name__}: {exc}\n\n"
        f"Results database: {config.DB_PATH}\n"
        f"Exists: {config.DB_PATH.exists()}\n",
        status=500, mimetype="text/plain")


# ---------------------------------------------------------------------- api
@app.route("/api/meta")
def api_meta():
    return jsonify(data.get_meta())


@app.route("/api/frameworks")
def api_frameworks():
    return jsonify(data.get_frameworks())


@app.route("/api/backends")
def api_backends():
    return jsonify(data.get_backends())


@app.route("/api/kpis")
def api_kpis():
    return jsonify(data.get_kpis())


@app.route("/api/scalability")
def api_scalability():
    return jsonify(data.get_scalability_series())


@app.route("/api/inference")
def api_inference():
    return jsonify(data.get_inference())


@app.route("/api/memory")
def api_memory():
    return jsonify(data.get_memory())


@app.route("/api/training")
def api_training():
    return jsonify(data.get_training())


@app.route("/api/validation")
def api_validation():
    return jsonify(data.get_validation())


@app.route("/api/sensitivity")
def api_sensitivity():
    return jsonify(data.get_sensitivity())


@app.route("/api/spread")
def api_spread():
    return jsonify(data.get_run_spread(request.args.get("task", "inference")))


@app.route("/api/runs")
def api_runs():
    return jsonify(data.get_runs(
        task=request.args.get("task", "scalability"),
        framework=request.args.get("framework"),
        backend=request.args.get("backend"),
        n=request.args.get("n")))


# --------------------------------------------------------------- CSV export
@app.route("/api/export/<kind>.csv")
def api_export(kind):
    """Serialises one of the named result sets straight from the shared data
    layer. The browser asks for a kind, not for a row payload: an exported
    file is therefore produced by exactly the same code path that produced
    the figures, and cannot drift from them."""
    try:
        rows = data.export_rows(kind)
    except ValueError:
        return Response("unknown export\n", status=404, mimetype="text/plain")
    if not rows:
        return Response("no rows\n", status=404, mimetype="text/plain")

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{kind}.csv"'})


@app.route("/api/export/all.csv")
def api_export_all():
    """Every result set in one file, with a `dataset` column naming which
    experiment each row came from. This is the export intended for archiving
    beside the thesis, since it is self-describing."""
    blocks = []
    for kind in ("inference", "scalability", "memory", "training", "validation"):
        try:
            rows = data.export_rows(kind)
        except ValueError:
            continue
        for r in rows:
            blocks.append(dict(dataset=kind, **r))
    blocks.extend(robustness.export_rows())   # evidence added during revision
    if not blocks:
        return Response("no rows\n", status=404, mimetype="text/plain")

    fields = ["dataset"]
    for r in blocks:
        for k in r:
            if k not in fields:
                fields.append(k)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, restval="")
    writer.writeheader()
    writer.writerows(blocks)
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="benchmark-all.csv"'})


def main():
    if not config.DB_PATH.exists():
        print(f"\n  No results database at {config.DB_PATH}")
        print("  Run the benchmark first:  python run.py bench\n")
    print(f"\n  {config.TITLE}")
    print(f"  Dashboard:  http://{config.HOST}:{config.PORT}")
    print(f"  Database :  {config.DB_PATH}")
    print(f"  Validate :  {config.VALIDATE_PATH}"
          f"{'' if config.VALIDATE_PATH.exists() else '  (not found — validation panel will say so)'}")
    print("  Ctrl+C to stop.\n")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG,
            threaded=True)


if __name__ == "__main__":
    main()
