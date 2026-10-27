"""Data access shared by both dashboards.

app.py (Flask, JavaScript charts) and streamlit_app.py (pure Python,
Streamlit + Plotly) read the same results database through this module, so
the scaling-exponent fit, the equivalence-log parser and every SQL query are
defined exactly once. Neither dashboard imports the benchmark package itself
(snnbench/), so this file - plus dashboard_config.py, dashboard_theme.py, the
database and the validation log - is everything either dashboard needs; it
can be copied somewhere else on its own.

This module has no simulator dependency of its own (no Flask, no Streamlit):
it is plain sqlite3, re and math, so its functions can be exercised directly
from a plain Python shell for a quick sanity check without either dashboard
running.

SINGLE HARDWARE PLATFORM. This benchmark is a controlled comparison: the
machine is held fixed so that a difference in runtime can be attributed to a
difference in the simulator rather than to the hardware. There is therefore no
hardware filter and no device column - every row was measured under identical
conditions, which is the property that makes the comparison valid. Extending
the same harness to additional hardware is set out as future work in the
thesis.
"""
from __future__ import annotations
import json
import math
import re
import sqlite3

import dashboard_config as config


def q(sql, *args):
    # A results database that is absent or cannot be opened is a normal state,
    # not a crash. Before this guard existed, every query function except
    # get_meta() called sqlite3.connect() unconditionally, so a missing
    # database raised OperationalError inside index() and Flask returned a
    # bare 500 page - which is what a browser shows as a blank screen. The
    # launcher made that reachable in ordinary use by defaulting
    # SNN_RESULTS_DIR to a folder that need not exist on this machine.
    #
    # Only the ABSENCE of a readable database is absorbed here. A malformed
    # query against a database that does exist still raises, so a genuine bug
    # in the SQL is not hidden behind an empty chart.
    if not config.DB_PATH.exists():
        return []
    try:
        con = sqlite3.connect(str(config.DB_PATH))
    except sqlite3.OperationalError:
        return []
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()


# --------------------------------------------------------------- de-duplication
# The database is append-only: re-running one simulator writes a fresh row
# rather than overwriting the old one, which is what makes a partial re-run
# safe. The cost is that a condition measured three times has three rows, and
# a chart that plots all three draws the same backend as three overlapping
# series. Every query below therefore keeps only the newest row per
# (framework, backend, task, network_size, phase).
#
# Newest is decided by id, not created_at: id is the insertion order and is
# never ambiguous, whereas two rows written inside the same second share a
# timestamp.
#
# A second rule matters more than de-duplication, and was added after a defect
# was found: every query is also restricted to ONE MACHINE. The database can
# legitimately hold rows from more than one host — a partial re-run performed
# elsewhere appends here like any other run — and because the newest row wins,
# a handful of rows measured on a different machine can silently replace the
# campaign's own rows for those conditions. That is not a de-duplication
# problem; it is a validity problem, because the whole comparison rests on the
# machine being held fixed.
#
# Restricting to "the machine with the most measured conditions" is not
# enough on its own, and a second defect was found because of it: this same
# database also holds several earlier, superseded attempts at this campaign
# on this laptop (partial runs left behind while a NEST subprocess-isolation
# bug was being fixed), on the SAME machine_id as the real campaign. A
# machine-only filter cannot tell those apart from the campaign itself, and
# because the newest row still wins, one such attempt — run after the real
# campaign had already measured Brian2, apparently while re-checking a
# result — silently overrode twelve of the campaign's own Brian2/NumPy rows
# here even though snnbench/analyse.py, which restricts to an explicit pair
# of run_groups instead of a machine_id, was never affected. CANONICAL_
# RUN_GROUPS below is that same explicit pair, kept in sync with the
# constant of the same name in snnbench/analyse.py: one run that measured
# brian2's three backends end to end, and one later run — after the NEST
# crash was fixed — that measured every other simulator end to end, with no
# overlap between them. Every row outside this exact pair, whatever its
# machine_id, is excluded from every figure and reported in the provenance
# panel as excluded, rather than being deleted, so the exclusion is
# auditable. See STATUS_INTERIM.md for the full account.
# 20 Sep 2026 - Experiments 1 and 3 (inference, scalability) now come from the
# CPU-corrected re-measurement, not from the August campaign. The August
# campaign's processor utilisation was read by a sampler thread that native
# simulator code starved of the GIL (up to 388,844 per cent, or no sample at
# all), and the September campaign's by a 10 ms-tick counter that cannot
# resolve millisecond regions; runtime was timed correctly in both, but
# utilisation - and so the energy proxy - was not. The corrected session
# (CLOCK_PROCESS_CPUTIME_ID, kernel peak-RSS mark, no sampler thread) repeats
# the identical protocol on the same laptop. Its twin session, run ten minutes
# later, and the two earlier campaigns stay in the database as replications
# (REPLICATION_RUN_GROUPS) and are never mixed into a figure.
#
# Experiment 2 (training) is unchanged: its rows come from the August
# fixed-budget campaign and the September full-budget campaign.
# The complete campaign of 21-27 September 2026. Every figure on this
# dashboard is drawn from it and from nothing else: one campaign, one machine,
# one instrument, run end to end with no other benchmark on the machine. The
# earlier campaigns are archived beside the database for provenance, but they
# are not mixed into a figure - that is what caused the ambiguity this list
# exists to prevent.
INFSCAL_RUN_GROUPS = (
    "3dd09b61bd76-fb679a",   # session A, 21 Sep 2026 11:07
)
TRAINING_RUN_GROUPS = (
    # Repeat budget: 6,000 train / 1,000 test, 3 epochs, hidden 256.
    "3dd09b61bd76-01ec46", "3dd09b61bd76-4ee008", "3dd09b61bd76-fedb55",
    "3dd09b61bd76-e6f7fa", "3dd09b61bd76-880471", "3dd09b61bd76-d7ed67",
    "3dd09b61bd76-11bfd9", "3dd09b61bd76-bc3e49", "3dd09b61bd76-411615",
    # Reference budget: 60,000 train / 10,000 test, 10 epochs, hidden 256.
    "3dd09b61bd76-1be46c", "3dd09b61bd76-240c5e", "3dd09b61bd76-a41901",
    "3dd09b61bd76-86dc75", "3dd09b61bd76-3a9ac5", "3dd09b61bd76-b2cf40",
    "3dd09b61bd76-0bee0e", "3dd09b61bd76-077773", "3dd09b61bd76-14a25b",
    # The width the Candidature Confirmation Report proposed, hidden 500, at
    # the reference budget. Three of the nine backends were measured before
    # the run was stopped; the rows carry their own width, so they sit beside
    # the hidden-256 rows rather than replacing them.
    "3dd09b61bd76-cdf269", "3dd09b61bd76-28927c", "3dd09b61bd76-951336",
)
REPLICATION_RUN_GROUPS = {
    "3dd09b61bd76-0077ae": "session B, the repeat run, 21 Sep 2026 11:14",
}
CANONICAL_RUN_GROUPS = INFSCAL_RUN_GROUPS + TRAINING_RUN_GROUPS
_INFSCAL_LIST = ", ".join(f"'{g}'" for g in INFSCAL_RUN_GROUPS)
_TRAINING_LIST = ", ".join(f"'{g}'" for g in TRAINING_RUN_GROUPS)
# A row is canonical only for the experiment its group was chosen for: the
# August groups also hold inference/scalability rows, and those must not
# re-enter a figure through the training allow-list.
_CANONICAL_ROW = (f"((task IN ('inference','scalability') AND run_group IN ({_INFSCAL_LIST})) "
                  f"OR (task = 'training' AND run_group IN ({_TRAINING_LIST})))")
_RUN_GROUP_LIST = ", ".join(f"'{g}'" for g in CANONICAL_RUN_GROUPS)
_CAMPAIGN_MACHINE = f"""
    SELECT machine_id FROM conditions
    WHERE run_group IN ({_RUN_GROUP_LIST})
    GROUP BY machine_id ORDER BY COUNT(*) DESC, machine_id LIMIT 1
"""

# For Experiment 2 the sample budget is part of a row's identity, not an
# incidental detail: the same backend at the same hidden width trained on
# 6,000 images for three epochs and on 60,000 for ten are two different
# measurements, not a re-run of one. Without the budget in this key the two
# collide and MAX(id) silently keeps only the newer, so merging the two
# campaigns into one database would make an entire budget disappear from
# every figure rather than showing both. The budget is parsed out of notes
# because that is where the harness records it; SQLite has no regex, hence
# the substr/instr pair. Non-training rows always key to the empty string,
# so their de-duplication is unchanged.
_TRAIN_N = ("substr(notes, instr(notes,'train_n=')+8, "
            "instr(notes,'; test_n=')-instr(notes,'train_n=')-8)")
_EPOCHS = ("substr(substr(notes, instr(notes,'epochs=')+7), 1, "
           "instr(substr(notes, instr(notes,'epochs=')+7), ';')-1)")
_BUDGET_KEY = (f"CASE WHEN task='training' AND instr(notes,'train_n=')>0 "
               f"AND instr(notes,'; test_n=')>0 AND instr(notes,'epochs=')>0 "
               f"THEN {_TRAIN_N} || '/' || {_EPOCHS} ELSE '' END")

_LATEST = f"""
    SELECT c.* FROM conditions c
    JOIN (SELECT framework, backend, task, network_size, phase,
                 {_BUDGET_KEY} AS budget_key, MAX(id) AS id
          FROM conditions
          WHERE machine_id = ({_CAMPAIGN_MACHINE})
            AND {_CANONICAL_ROW}
          GROUP BY framework, backend, task, network_size, phase, budget_key) m
      ON c.id = m.id
"""


def fit_scaling(sizes, times):
    """Least-squares slope of log10(runtime) on log10(N), with its standard
    error and 95% interval. This is the same fit the thesis's own analysis
    module computes; it is reimplemented here (rather than imported) so a
    dashboard never needs the benchmark package itself installed."""
    n = len(sizes)
    if n < 3:
        return None
    xs = [math.log10(s) for s in sizes]
    ys = [math.log10(t) for t in times if t > 0]
    if len(ys) != n:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    b = my - k * mx
    resid = [y - (k * x + b) for x, y in zip(xs, ys)]
    sse = sum(r * r for r in resid)
    sst = sum((y - my) ** 2 for y in ys)
    se = math.sqrt(sse / (n - 2) / sxx) if n > 2 else 0.0
    tcrit = {3: 12.706, 4: 4.303, 5: 3.182, 6: 2.776, 7: 2.571}.get(n, 2.0)
    return dict(k=k, se=se, ci=[k - tcrit * se, k + tcrit * se],
                r2=(1 - sse / sst) if sst else 1.0)


def interpret_k(fit):
    """Plain words for a fitted exponent, including the case the fit itself
    rules out. An r-squared near zero means there is no relationship between
    size and runtime to describe, and quoting k for such a series invites a
    reader to compare a number that is not measuring anything."""
    if not fit:
        return "too few sizes to fit"
    k, r2 = fit["k"], fit["r2"]
    if r2 < 0.25:
        return "flat - runtime does not track size here"
    if k < 0.15:
        return "near-flat; fixed overhead dominates"
    if k < 0.7:
        return "sub-linear; cost grows slower than the network"
    if k < 1.15:
        return "approximately linear in network size"
    return "super-linear; cost outgrows the network"


# ------------------------------------------------------------- equivalence log
# validate.txt is a plain-text run log, not a database table, because
# run.py validate is a one-shot check rather than a stored experiment. Its
# table has a fixed column layout that this regex mirrors:
#   simulator/backend   status   rate Hz   ref Hz   [rel]   [message]
#
# rel (the relative deviation) is matched as optional, not required. The
# current run.py cmd_validate() always prints it, but earlier runs of the
# same command did not, and a log written by that earlier version is still a
# real, valid equivalence check — the row should parse, just without a
# relative-deviation figure, rather than the whole row (and the entire
# panel, since "no recognisable rows" reads as no validation at all) being
# silently dropped because one trailing column is missing.
#
# The status alternation also has to include "rate mismatch": cmd_validate's
# own bad-row filter checks for exactly that status, so a log can contain it
# for real.
_VALIDATE_ROW = re.compile(
    r"^\s*(?P<id>\S+/\S+)\s+"
    r"(?P<status>pass|fail|rate mismatch|not installed|error|skip)"
    r"\s+(?P<rate>-|[\d.]+)\s+(?P<ref>-|[\d.]+)"
    r"(?:\s+(?P<rel>-|[\d.]+))?"
    r"(?:\s+(?P<message>.*))?$"
)


def parse_validate_log(text):
    header = None
    rows = []
    for line in text.splitlines():
        m = _VALIDATE_ROW.match(line)
        if m:
            d = m.groupdict()
            rows.append(dict(
                id=d["id"], status=d["status"],
                rate_hz=None if d["rate"] == "-" else float(d["rate"]),
                ref_hz=None if d["ref"] == "-" else float(d["ref"]),
                rel=None if d["rel"] in (None, "-") else float(d["rel"]),
                message=(d["message"] or "").strip() or None))
        elif "Equivalence validation" in line:
            header = line.strip()
    return dict(header=header, rows=rows)


# ------------------------------------------------------------- higher level
def db_exists():
    return config.DB_PATH.exists()


def get_meta():
    """Machine, package and config metadata for the most recent run, plus
    row counts and the set of network sizes measured. Returns
    dict(ok=False, error=...) if there is nothing to report yet, so a caller
    never has to guess why a field is missing."""
    if not db_exists():
        return dict(ok=False,
                     error=f"No results database at {config.DB_PATH}. "
                           f"Run `python run.py bench` first.")
    m = q(f"SELECT * FROM meta WHERE run_group IN ({_RUN_GROUP_LIST}) "
           f"ORDER BY id DESC LIMIT 1")
    if not m:
        return dict(ok=False, error="The database has no run metadata.")
    cfg = json.loads(m[0]["config_json"])
    keep = ("TAU_MS", "V_THRESH", "V_RESET", "DT_MS", "SIM_MS", "FANIN",
            "INPUT_RATE_HZ", "SYN_WEIGHT", "SEED", "WARMUP_RUNS",
            "MEASURED_RUNS", "TDP_CPU_W", "TDP_CPU_SOURCE")
    # Everything below is restricted by run_group, not by machine_id alone —
    # see the CANONICAL_RUN_GROUPS comment above for why a machine-only
    # restriction is not sufficient on its own.
    excluded_other_machine = q(
        f"SELECT COUNT(*) c FROM conditions "
        f"WHERE NOT {_CANONICAL_ROW} "
        f"AND machine_id <> ({_CAMPAIGN_MACHINE})")[0]["c"]
    excluded_same_machine = q(
        f"SELECT COUNT(*) c FROM conditions "
        f"WHERE NOT {_CANONICAL_ROW} "
        f"AND machine_id = ({_CAMPAIGN_MACHINE})")[0]["c"]
    _rep = ", ".join(f"'{g}'" for g in REPLICATION_RUN_GROUPS)
    excluded_replication = q(
        f"SELECT COUNT(*) c FROM conditions "
        f"WHERE NOT {_CANONICAL_ROW} AND run_group IN ({_rep})")[0]["c"]
    return dict(
        ok=True,
        title=config.TITLE,
        subtitle=config.SUBTITLE,
        machine=json.loads(m[0]["machine_json"]),
        packages=json.loads(m[0]["packages_json"]),
        config={k: cfg.get(k) for k in keep if cfg.get(k) is not None},
        counts=dict(
            runs=q(f"SELECT COALESCE(SUM(n_runs),0) c FROM ({_LATEST})")[0]["c"],
            conditions=len(q(f"SELECT 1 FROM ({_LATEST})")),
            backends=len(get_backends()),
            snn_backends=len([b for b in get_backends()
                              if b["framework"] != "reference"]),
            controls=len([b for b in get_backends()
                          if b["framework"] == "reference"])),
        # Rows excluded from every figure, split by why: measured on a
        # different host entirely, versus measured on the campaign's own
        # machine but during an earlier, superseded attempt at this same
        # campaign (a partial re-run left behind while a bug was being
        # fixed — see the comment on CANONICAL_RUN_GROUPS above). Reported
        # rather than hidden: a reader is entitled to know that the database
        # holds more than the figures use, and why those rows are not in
        # them.
        excluded=excluded_other_machine + excluded_same_machine,
        excluded_other_machine=excluded_other_machine,
        excluded_same_machine=excluded_same_machine - excluded_replication,
        excluded_replication=excluded_replication,
        replication_sessions=sorted(set(REPLICATION_RUN_GROUPS.values())),
        other_machines=[r["machine_id"] for r in
                        q(f"SELECT DISTINCT machine_id FROM conditions "
                          f"WHERE NOT {_CANONICAL_ROW} "
                          f"AND machine_id <> ({_CAMPAIGN_MACHINE})")],
        sizes=[r["network_size"] for r in
               q(f"SELECT DISTINCT network_size FROM conditions "
                 f"WHERE task='scalability' "
                 f"AND run_group IN ({_INFSCAL_LIST}) ORDER BY 1")],
        db=str(config.DB_PATH))


def get_backends():
    """Every simulator/backend pair that produced at least one measured row,
    in a stable order. This is what the filter control is built from, so a
    backend that was never measured never appears as an option."""
    import dashboard_theme as theme
    rows = q(f"SELECT DISTINCT framework, backend FROM ({_LATEST}) "
             f"ORDER BY framework, backend")
    return [dict(id=f"{r['framework']}/{r['backend']}",
                 framework=r["framework"], backend=r["backend"],
                 note=theme.backend_note(r["framework"], r["backend"]))
            for r in rows]


def get_frameworks():
    """One entry per simulator that produced measured rows, with its
    backends, its colour, and the description and citation that explain what
    it is. This is what the simulator selector is built from: the reader
    picks a simulator, not a backend, because a simulator is the unit the
    research question is asked about.

    Simulators that were never measured are absent by construction. Nothing
    is listed that has no data behind it."""
    import dashboard_theme as theme
    order = list(theme.FRAMEWORK_COLORS)
    seen = {}
    for b in get_backends():
        seen.setdefault(b["framework"], []).append(b)

    out = []
    for fw in sorted(seen, key=lambda f: order.index(f) if f in order else 99):
        info = theme.info_for(fw)
        out.append(dict(
            id=fw,
            label=theme.label_for(fw),
            color=theme.color_for(fw),
            is_control=fw in theme.CONTROL_FRAMEWORKS,
            backends=seen[fw],
            n_backends=len(seen[fw]),
            kind=info.get("kind", ""),
            one_line=info.get("one_line", ""),
            detail=info.get("detail", ""),
            best_for=info.get("best_for", ""),
        ))
    return out


def get_scalability_series():
    """One entry per backend: its points across network size, sorted by
    size, with a fitted scaling exponent attached. Sorted by that exponent,
    steepest first, matching the ranking the exponent table shows."""
    rows = q(f"SELECT framework, backend, network_size, runtime_median_s, "
             f"runtime_sd_s, " f"(CASE WHEN runtime_mean_s > 0 THEN 100.0 * runtime_sd_s / runtime_mean_s ELSE 0 END) AS cv_pct, " f"peak_rss_mb, energy_median_j, spikes, "
             f"cpu_pct, eflop, compile_dominated, n_runs "
             f"FROM ({_LATEST}) WHERE task='scalability' AND phase='simulate' "
             f"ORDER BY framework, backend, network_size")
    series = {}
    for r in rows:
        key = f"{r['framework']}/{r['backend']}"
        s = series.setdefault(key, dict(
            id=key, framework=r["framework"], backend=r["backend"],
            compile_dominated=bool(r["compile_dominated"]), points=[]))
        s["points"].append(dict(
            n=r["network_size"], t=r["runtime_median_s"], sd=r["runtime_sd_s"],
            cv=r["cv_pct"], mem=r["peak_rss_mb"], e=r["energy_median_j"],
            spikes=r["spikes"], cpu=r["cpu_pct"], eflop=r["eflop"],
            runs=r["n_runs"]))
    out = []
    for s in series.values():
        s["points"].sort(key=lambda p: p["n"])
        s["fit"] = fit_scaling([p["n"] for p in s["points"]],
                                [p["t"] for p in s["points"]])
        s["interpretation"] = interpret_k(s["fit"])
        s["sizes"] = [p["n"] for p in s["points"]]
        # Throughput at the largest size measured: neurons simulated per
        # second of wall clock. Reported at one size rather than averaged,
        # because averaging across sizes hides exactly the growth the
        # scalability experiment exists to expose.
        last = s["points"][-1] if s["points"] else None
        s["throughput"] = (last["n"] / last["t"]) if last and last["t"] else None
        s["largest_n"] = last["n"] if last else None
        s["largest_t"] = last["t"] if last else None
        out.append(s)
    out.sort(key=lambda s: -(s["fit"]["k"] if s["fit"] else -99))
    return out


def get_inference():
    """Experiment 1 at the reference size, with the setup phase kept separate
    from the simulate phase. They are different questions - how long to build
    the network, and how long to run it - and a simulator that is slow to
    build but fast to run should be visible as exactly that."""
    sim = q(f"SELECT framework, backend, network_size, runtime_median_s, "
            f"runtime_sd_s, " f"(CASE WHEN runtime_mean_s > 0 THEN 100.0 * runtime_sd_s / runtime_mean_s ELSE 0 END) AS cv_pct, " f"peak_rss_mb, cpu_pct, spikes, "
            f"energy_median_j, eflop, n_runs, framework_version, "
            f"compile_dominated, notes "
            f"FROM ({_LATEST}) WHERE task='inference' AND phase='simulate' "
            f"ORDER BY runtime_median_s")
    setup = {(r["framework"], r["backend"]): r["runtime_median_s"] for r in
             q(f"SELECT framework, backend, runtime_median_s FROM ({_LATEST}) "
               f"WHERE task='inference' AND phase='setup'")}
    # Normalised to the costliest backend whose time is its simulator's, not
    # its compiler's. With utilisation measured correctly, Brian2's standalone
    # target (whose compiler runs in parallel child processes) costs about a
    # hundred times more than any simulating backend, and normalising to it
    # flattened every other bar to zero. It keeps its own index, above 100.
    comparable = [r for r in sim if not r["compile_dominated"]]
    worst = max((r["energy_median_j"] or 0) for r in (comparable or sim)) if sim else 0
    for r in sim:
        r["setup_s"] = setup.get((r["framework"], r["backend"]))
        r["id"] = f"{r['framework']}/{r['backend']}"
        # Energy index: the raw joule estimate rescaled so the worst backend
        # reads 100. The index is for reading a bar chart at a glance; the
        # joule figure it came from stays in the row and in the CSV export,
        # so nothing is lost by rescaling.
        r["energy_index"] = (100.0 * r["energy_median_j"] / worst
                             if worst and r["energy_median_j"] is not None else None)
    return sim


def get_memory():
    """Memory across the scalability sweep. Peak RSS is a whole-process
    figure - interpreter, NumPy and every imported module included - so at
    small N it is almost entirely fixed overhead and says little about the
    network. The growth from the smallest to the largest size is the part
    that is actually attributable to simulating more neurons, so it is
    computed here rather than left for the reader to do by eye."""
    series = {}
    rows = q(f"SELECT framework, backend, network_size, peak_rss_mb, "
             f"compile_dominated "
             f"FROM ({_LATEST}) WHERE task='scalability' AND phase='simulate' "
             f"ORDER BY framework, backend, network_size")
    for r in rows:
        key = f"{r['framework']}/{r['backend']}"
        s = series.setdefault(key, dict(id=key, framework=r["framework"],
                                         backend=r["backend"],
                                         compile_dominated=bool(r["compile_dominated"]),
                                         points=[]))
        s["points"].append(dict(n=r["network_size"], mem=r["peak_rss_mb"]))

    # Simulation-attributable memory, measured as the run-level delta over
    # the pre-run baseline, averaged across the runs at the largest size.
    delta = {(r["framework"], r["backend"]): r["d"] for r in q(
        f"SELECT framework, backend, AVG(rss_delta_mb) d FROM runs "
        f"WHERE task='scalability' AND run_group IN ({_INFSCAL_LIST}) "
        f"AND network_size="
        f"(SELECT MAX(network_size) FROM runs WHERE task='scalability' "
        f"AND run_group IN ({_INFSCAL_LIST})) "
        f"GROUP BY framework, backend")}

    out = []
    for s in series.values():
        s["points"].sort(key=lambda p: p["n"])
        first, last = s["points"][0], s["points"][-1]
        s["baseline_mb"] = first["mem"]
        s["peak_mb"] = last["mem"]
        s["growth_mb"] = last["mem"] - first["mem"]
        s["largest_n"] = last["n"]
        s["delta_mb"] = delta.get((s["framework"], s["backend"]))
        # KB per neuron, from the growth rather than the peak: the fixed
        # interpreter cost is not a per-neuron cost and dividing it by N
        # would manufacture a number that shrinks as the network grows.
        s["kb_per_neuron"] = ((s["growth_mb"] * 1024.0 / last["n"])
                               if last["n"] else None)
        out.append(s)
    out.sort(key=lambda s: -s["peak_mb"])
    return out


def get_training():
    """Experiment 2. The preset actually used is parsed out of the notes so
    the table can state the sample budget beside the accuracy - the two are
    not separable, and an accuracy quoted without its budget is misleading
    for the unsupervised rules in particular."""
    rows = q(f"SELECT framework, backend, network_size, runtime_median_s, "
             f"accuracy_pct, peak_rss_mb, cpu_pct, notes, framework_version "
             f"FROM ({_LATEST}) WHERE task='training' "
             f"ORDER BY accuracy_pct DESC")

    # For Experiment 2, network_size is the hidden-layer width, so one backend
    # can legitimately appear more than once - trained at two different widths
    # on two different sample budgets. Those are separate results, not
    # duplicates, but they would collide on a shared "simulator/backend" label
    # and draw as one series. Where a backend has more than one row, the width
    # goes into its identifier so the two stay distinguishable everywhere.
    seen = {}
    for r in rows:
        seen[(r["framework"], r["backend"])] = seen.get(
            (r["framework"], r["backend"]), 0) + 1

    for r in rows:
        base = f"{r['framework']}/{r['backend']}"
        # backend_id is what the filter control matches on and is identical
        # across every view; id is what the reader sees and may carry the
        # width. Keeping them separate means widening the label never breaks
        # filtering.
        r["backend_id"] = base
        r["id"] = (f"{base} (hidden {r['network_size']})"
                    if seen[(r["framework"], r["backend"])] > 1 else base)
        note = r.get("notes") or ""
        for field, pattern in (("hidden", r"hidden=(\d+)"),
                               ("train_n", r"train_n=(\d+)"),
                               ("test_n", r"test_n=(\d+)"),
                               ("epochs", r"epochs=(\d+)")):
            m = re.search(pattern, note)
            r[field] = int(m.group(1)) if m else None
        # The mechanism sentence is everything after the preset prefix; it is
        # the part that explains why two rows are not doing the same thing.
        r["mechanism"] = re.sub(r"^preset=[^;]*;\s*(?:\w+=\d+;\s*)*", "", note).strip()
        # The harness stores training cost already divided per epoch: every
        # adapter's train() returns the mean of its per-epoch times (Nengo's
        # closed-form solve, which has no epochs, returns the one solve).
        # An earlier version divided by the epoch count a second time, which
        # understated every training cost on this page three- or tenfold.
        r["seconds_per_epoch"] = r["runtime_median_s"]
        # Chance is 10% on ten classes. Flagging it in the data rather than
        # in the view keeps both dashboards honest in the same way.
        r["at_chance"] = (r["accuracy_pct"] is not None
                          and r["accuracy_pct"] < 15.0)
    return rows


def get_validation():
    if not config.VALIDATE_PATH.exists():
        return dict(ok=False,
                     error=f"No validation log at {config.VALIDATE_PATH}. "
                           f"Run `python run.py validate` first.")
    text = config.VALIDATE_PATH.read_text(errors="replace")
    parsed = parse_validate_log(text)
    if not parsed["rows"]:
        return dict(ok=False, error="The validation log has no recognisable rows.")
    return dict(ok=True, **parsed)


def get_kpis():
    """The four headline figures. Each carries the id it came from, so the
    card can name the winner instead of asserting a bare number, and each is
    computed over measured rows only.

    Two exclusions apply to every ranking, and for the same reason - a card
    that names a winner should be answering the question a reader thinks it
    is answering:

      controls           the NumPy reference exists to show what the same
                         network costs with no simulator at all. Letting it
                         win "fastest simulator" would answer a question
                         nobody asked.
      compile-dominated  a backend whose measured time is its compiler's
                         rather than its simulator's is not comparable on any
                         of these axes. Brian2's standalone target rebuilds
                         per run, so it posts a near-flat scaling curve and a
                         small footprint that describe the build, not the
                         simulation. It stays visible in every chart and
                         table, clearly marked; it just cannot win a prize.
    """
    from dashboard_theme import CONTROL_FRAMEWORKS

    def eligible(rows):
        return [r for r in rows
                if r["framework"] not in CONTROL_FRAMEWORKS
                and not r.get("compile_dominated")]

    inf = eligible(get_inference())
    mem = eligible(get_memory())
    scale = [s for s in eligible(get_scalability_series()) if s["fit"]]

    out = {}

    if inf:
        best = min(inf, key=lambda r: r["runtime_median_s"])
        out["fastest"] = dict(
            id=best["id"], value=best["runtime_median_s"],
            unit="s", label="Fastest inference",
            sub=f"{best['runtime_median_s'] * 1000:.2f} ms at N={best['network_size']}")

    if mem:
        best = min(mem, key=lambda r: r["peak_mb"])
        out["memory"] = dict(
            id=best["id"], value=best["peak_mb"], unit="MB",
            label="Lowest peak memory",
            sub=f"{best['peak_mb']:.0f} MB at N={best['largest_n']}")

    # Best scaler is the smallest exponent, but only among series whose fit
    # actually describes the data. A flat series with no relationship to fit
    # would otherwise take first place on a meaningless k.
    fitted = [s for s in scale if s["fit"]["r2"] >= 0.25]
    if fitted:
        best = min(fitted, key=lambda s: s["fit"]["k"])
        out["scaling"] = dict(
            id=best["id"], value=best["fit"]["k"], unit="k",
            label="Flattest scaling",
            sub=f"k = {best['fit']['k']:.3f} (r² = {best['fit']['r2']:.2f})")

    frameworks = {r["framework"] for r in inf}
    out["coverage"] = dict(
        id=None, value=len(frameworks), unit="",
        label="Simulators measured",
        sub=f"{len([b for b in get_backends() if b['framework'] not in CONTROL_FRAMEWORKS])} SNN simulator backends, one hardware platform")
    return out


def get_runs(task="scalability", framework=None, backend=None, n=None, limit=2000):
    """Individual measured runs, so any aggregate elsewhere can be checked."""
    sql = ("SELECT framework, backend, task, network_size, run_index, runtime_s,"
           " peak_rss_mb, rss_delta_mb, cpu_pct, spikes, energy_j FROM runs "
           f"WHERE task=? AND phase='simulate' "
           f"AND {_CANONICAL_ROW}")
    args = [task]
    if framework:
        sql += " AND framework=?"
        args.append(framework)
    if backend:
        sql += " AND backend=?"
        args.append(backend)
    if n:
        sql += " AND network_size=?"
        args.append(int(n))
    sql += f" ORDER BY framework, backend, network_size, run_index LIMIT {int(limit)}"
    return q(sql, *args)


def get_run_spread(task="inference"):
    """Every individual run for a task, grouped by backend. The reference
    dashboard plotted sampled memory over time here; this database does not
    store a timeline, but it does store each measured run separately, which
    supports the more useful question: how repeatable is the figure being
    quoted? A median with five tight runs behind it and a median with five
    scattered ones are not the same claim."""
    rows = get_runs(task=task, limit=5000)
    series = {}
    for r in rows:
        key = f"{r['framework']}/{r['backend']}"
        s = series.setdefault(key, dict(id=key, framework=r["framework"],
                                         backend=r["backend"], values=[]))
        s["values"].append(r["runtime_s"])
    out = []
    for s in series.values():
        vals = sorted(v for v in s["values"] if v is not None)
        if not vals:
            continue
        n = len(vals)
        mean = sum(vals) / n
        sd = (math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1))
              if n > 1 else 0.0)
        s["n"] = n
        s["min"] = vals[0]
        s["max"] = vals[-1]
        s["median"] = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
        s["mean"] = mean
        s["sd"] = sd
        s["cv_pct"] = (100.0 * sd / mean) if mean else 0.0
        out.append(s)
    out.sort(key=lambda s: s["median"])
    return out


# ══════════════════════════════════════════ Experiment 4 — sensitivity
# The question this experiment answers is not "how fast is each simulator",
# which the other three experiments answer, but "how much does the answer
# depend on how we chose to ask". A benchmark whose ranking flips when the
# network size or the metric changes has not produced a recommendation; it
# has produced an artefact of its own configuration, and saying which of the
# two you have is the point of a sensitivity analysis.
#
# The statistic used is Kendall's tau-b, the rank correlation between two
# orderings of the same backends. tau = 1 means the two orderings agree
# exactly; tau = 0 means they are unrelated; tau = -1 means one is the
# reverse of the other. Rank correlation is used rather than a comparison of
# the values themselves because the claim under test is about the ORDER a
# reader would act on, not about the magnitudes.
#
# Method follows Dey and Dimitrov (2023), who apply sensitivity analysis to
# point-neuron simulations to separate model behaviour from implementation
# artefact [6]. The use of rank-based statistics to compare methods across
# multiple conditions, rather than averaging raw scores, follows Demsar
# (2006), the standard reference for this style of comparison.

def kendall_tau(a, b):
    """Kendall's tau-b between two equal-length sequences of values, with
    ties handled. Implemented here rather than imported so the dashboard
    keeps its no-SciPy dependency footprint; at these sizes (eleven backends)
    the O(n^2) form is free."""
    n = len(a)
    if n < 2:
        return None
    concordant = discordant = ties_a = ties_b = 0
    for i in range(n):
        for j in range(i + 1, n):
            da = a[i] - a[j]
            db = b[i] - b[j]
            prod = da * db
            if prod > 0:
                concordant += 1
            elif prod < 0:
                discordant += 1
            else:
                if da == 0:
                    ties_a += 1
                if db == 0:
                    ties_b += 1
    n0 = n * (n - 1) / 2
    denom = math.sqrt((n0 - ties_a) * (n0 - ties_b))
    if denom == 0:
        return None
    return (concordant - discordant) / denom


def spearman_rho(a, b):
    """Spearman rank correlation, used for Objective O2's stated comparison
    between the energy proxy and the EFLOP metric."""
    n = len(a)
    if n < 2:
        return None

    def ranks(xs):
        order = sorted(range(n), key=lambda i: xs[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = math.sqrt(sum((x - ma) ** 2 for x in ra))
    db = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return num / (da * db) if da and db else None


def get_sensitivity():
    """Experiment 4. Returns the three sensitivity questions the data can
    actually answer, each with its rank statistic and a plain reading of it.

    Nothing here is simulated or assumed: every ordering compared below is
    an ordering of the measured rows already shown elsewhere in this
    dashboard."""
    from dashboard_theme import CONTROL_FRAMEWORKS
    series = get_scalability_series()
    # Only genuine SNN simulator backends are ranked. The plain-NumPy
    # validation controls are not simulators a reader could choose, so
    # including them would let them change the coefficients of an ordering
    # they cannot be part of.
    usable = [s for s in series if len(s["points"]) >= 4
              and s["framework"] not in CONTROL_FRAMEWORKS]

    out = dict(ok=bool(usable), sizes=[], size_stability=[],
               metric_stability=[], energy_validation=None, notes=[])
    if not usable:
        out["error"] = ("The scalability sweep has too few sizes to test "
                        "sensitivity of the ordering.")
        return out

    sizes = sorted({p["n"] for s in usable for p in s["points"]})
    out["sizes"] = sizes
    ref_n = sizes[-1]

    def runtime_at(s, n):
        for p in s["points"]:
            if p["n"] == n:
                return p["t"]
        return None

    # ---- 1. Does the ordering depend on the network size chosen? ----------
    ref_rows = [(s["id"], runtime_at(s, ref_n)) for s in usable]
    ref_rows = [(i, v) for i, v in ref_rows if v is not None]
    ref_ids = [i for i, _ in ref_rows]
    ref_vals = [v for _, v in ref_rows]

    for n in sizes:
        vals = []
        ok = True
        for i in ref_ids:
            s = next(x for x in usable if x["id"] == i)
            v = runtime_at(s, n)
            if v is None:
                ok = False
                break
            vals.append(v)
        if not ok or len(vals) < 2:
            continue
        tau = kendall_tau(vals, ref_vals)
        if tau is None:
            continue
        fastest = ref_ids[min(range(len(vals)), key=lambda k: vals[k])]
        out["size_stability"].append(dict(
            n=n, tau=tau, is_reference=(n == ref_n), fastest=fastest,
            reading=_read_tau(tau, f"N={n:,} against N={ref_n:,}")))

    # ---- 2. Does the ordering depend on the metric chosen? ----------------
    metrics = {
        "Runtime": lambda s: runtime_at(s, ref_n),
        "Energy proxy": lambda s: next(
            (p["e"] for p in s["points"] if p["n"] == ref_n), None),
        "Peak memory": lambda s: next(
            (p["mem"] for p in s["points"] if p["n"] == ref_n), None),
        "Scaling exponent": lambda s: (s["fit"]["k"] if s["fit"] else None),
    }
    base_name = "Runtime"
    base_vals, base_ids = [], []
    for s in usable:
        v = metrics[base_name](s)
        if v is not None:
            base_ids.append(s["id"])
            base_vals.append(v)

    for name, fn in metrics.items():
        vals, ok = [], True
        for i in base_ids:
            s = next(x for x in usable if x["id"] == i)
            v = fn(s)
            if v is None:
                ok = False
                break
            vals.append(v)
        if not ok or len(vals) < 2:
            continue
        tau = kendall_tau(vals, base_vals)
        if tau is None:
            continue
        out["metric_stability"].append(dict(
            metric=name, tau=tau, is_reference=(name == base_name),
            reading=_read_tau(tau, f"{name} against {base_name.lower()}")))

    # ---- 3. Objective O2: energy proxy against the EFLOP metric -----------
    # Reported honestly rather than forced. EFLOP counts the operations the
    # MODEL performs, so at a fixed network size it is identical for every
    # simulator and cannot discriminate between them; the correlation is
    # therefore computed across sizes, where it does vary, and the
    # limitation is stated rather than hidden behind a coefficient.
    pairs = []
    for s in usable:
        for p in s["points"]:
            if p["e"] is not None and p["eflop"]:
                pairs.append((p["e"], p["eflop"]))
    if len(pairs) >= 4:
        rho = spearman_rho([p[0] for p in pairs], [p[1] for p in pairs])
        per_size_distinct = len({
            p["eflop"] for s in usable for p in s["points"]
            if p["n"] == ref_n and p["eflop"]})
        out["energy_validation"] = dict(
            rho=rho, n_pairs=len(pairs),
            eflop_distinct_at_ref=per_size_distinct,
            discriminates=per_size_distinct > 1,
            reading=(
                "The EFLOP metric counts the operations the network model "
                "performs, which at a fixed size is the same number whichever "
                "simulator executes it. It therefore assigns every simulator "
                "an identical value and cannot rank them against each other; "
                "the correlation below is computed across network sizes, "
                "where EFLOP does vary. This is a property of the metric as "
                "defined, not a fault in its implementation, and it is the "
                "reason the utilisation-weighted proxy is reported alongside "
                "it rather than replaced by it."
                if per_size_distinct <= 1 else
                "EFLOP varies across simulators at a fixed size, so the rank "
                "correlation below compares two instruments that both "
                "discriminate between simulators."),
        )

    return out


def _read_tau(tau, what):
    if tau is None:
        return "not computable"
    if tau >= 0.95:
        return f"{what}: identical ordering"
    if tau >= 0.8:
        return f"{what}: ordering essentially stable"
    if tau >= 0.5:
        return f"{what}: ordering broadly holds, with movement"
    if tau >= 0.0:
        return f"{what}: ordering largely unrelated — the choice matters"
    return f"{what}: ordering substantially reversed"


# ----------------------------------------------------------- narrative panels
# These two panels are prose, not measurements, and they are kept in the data
# layer rather than duplicated into two templates so the Flask page and the
# Streamlit page can never drift into saying different things about the same
# research. Each gap names the research question and objective it belongs to,
# so a reader can trace a dashboard panel back to the thesis.
RESEARCH_GAPS = [
    dict(n=1,
         title="No common, stability-tested benchmark of the five simulators",
         rq="RQ1 / O1",
         desc="Brian2, NEST, Nengo, snnTorch and SpikingJelly have not been "
              "compared together under one reproducible protocol, and the "
              "comparisons that exist do not test whether their ranking "
              "survives a change of network size, metric or session. The "
              "Sensitivity view reports that test."),
    dict(n=2,
         title="No transparent, checkable energy estimate for commodity processors",
         rq="RQ2 / O2",
         desc="Energy is measured on neuromorphic hardware or estimated from "
              "runtime without a stated formula. This dashboard reports a "
              "processor-time energy proxy whose formula and constant are "
              "stated, and checks its ordering against an operation count. It "
              "is an ordinal estimate, not a measurement of electrical energy."),
    dict(n=3,
         title="No interactive, evidence-aware way to compare and select a simulator",
         rq="RQ3 / O3",
         desc="Benchmark results are published as static tables. A reader "
              "cannot filter them, see the runs behind a median, check "
              "equivalence and provenance, or weigh runtime, memory and "
              "scalability for their own network size. The benchmark pages and "
              "the Optimisation page provide these functions."),
]

# Qualitative guidance, deliberately separated from the measurements. These
# statements come from each simulator's design intent and documentation, not
# from the numbers on this page: a simulator can be slow here and still be the
# right choice, and saying so is more useful than a ranking that pretends
# one number settles the question.
SELECTION_GUIDE = [
    dict(framework="brian2", best_for="Biological modelling",
         desc="Neuron and synapse dynamics are written as differential "
              "equations in a domain-specific notation close to the textbook "
              "form. Suits custom models and exploratory neuroscience. Its "
              "compiled targets pay a code-generation cost on first run, which "
              "is why the standalone backend is reported separately here."),
    dict(framework="nest", best_for="Large sparse networks",
         desc="Built for cortical-scale simulation with thread and MPI "
              "parallelism. It runs in its own worker process here, so its "
              "small footprint at N=100 reflects a smaller process, not a "
              "leaner simulation; its memory grows by about 82-85 KB per "
              "neuron, which the memory view shows directly."),
    dict(framework="snntorch", best_for="ML-oriented supervised training",
         desc="PyTorch-native surrogate-gradient training through "
              "backpropagation-through-time. The most direct route from a "
              "conventional deep-learning workflow into spiking models. In "
              "Experiment 2 it reached 97.24% against SpikingJelly's 97.46% "
              "at almost the same cost per epoch."),
    dict(framework="spikingjelly", best_for="Deep spiking architectures",
         desc="Also PyTorch-based, with a broader layer library aimed at "
              "deeper networks and event-driven vision datasets. Matches "
              "snnTorch closely on this benchmark, as the identical training "
              "procedure would predict."),
    dict(framework="nengo", best_for="Neuromorphic deployment",
         desc="The Neural Engineering Framework (NEF) solves decoders in closed form "
              "rather than by gradient descent, and compiles to neuromorphic "
              "targets. There is no epoch to time; the figure reported is the "
              "cost of the single solve."),
]


def get_gaps():
    return RESEARCH_GAPS


def get_selection_guide():
    return SELECTION_GUIDE


def export_rows(kind="inference"):
    """Flat rows for CSV export, one dict per record. The export is built
    from the same functions the charts use, so a downloaded file always
    matches what was on screen rather than re-querying and possibly
    disagreeing with it."""
    if kind == "inference":
        return [dict(framework=r["framework"], backend=r["backend"],
                     network_size=r["network_size"],
                     runtime_median_s=r["runtime_median_s"],
                     runtime_sd_s=r["runtime_sd_s"], cv_pct=r["cv_pct"],
                     setup_s=r["setup_s"], peak_rss_mb=r["peak_rss_mb"],
                     cpu_pct=r["cpu_pct"], spikes=r["spikes"],
                     energy_median_j=r["energy_median_j"],
                     energy_index=r["energy_index"], eflop=r["eflop"],
                     n_runs=r["n_runs"],
                     compile_dominated=r["compile_dominated"])
                for r in get_inference()]
    if kind == "scalability":
        out = []
        for s in get_scalability_series():
            for p in s["points"]:
                out.append(dict(framework=s["framework"], backend=s["backend"],
                                network_size=p["n"], runtime_median_s=p["t"],
                                runtime_sd_s=p["sd"], cv_pct=p["cv"],
                                peak_rss_mb=p["mem"], cpu_pct=p["cpu"],
                                spikes=p["spikes"], energy_median_j=p["e"],
                                eflop=p["eflop"], n_runs=p["runs"],
                                fitted_k=s["fit"]["k"] if s["fit"] else None,
                                fit_r2=s["fit"]["r2"] if s["fit"] else None))
        return out
    if kind == "memory":
        return [dict(framework=s["framework"], backend=s["backend"],
                     largest_n=s["largest_n"], baseline_mb=s["baseline_mb"],
                     peak_mb=s["peak_mb"], growth_mb=s["growth_mb"],
                     delta_mb=s["delta_mb"], kb_per_neuron=s["kb_per_neuron"])
                for s in get_memory()]
    if kind == "training":
        return [dict(framework=r["framework"], backend=r["backend"],
                     hidden=r["hidden"], train_n=r["train_n"],
                     test_n=r["test_n"], epochs=r["epochs"],
                     accuracy_pct=r["accuracy_pct"],
                     runtime_median_s=r["runtime_median_s"],
                     seconds_per_epoch=r["seconds_per_epoch"],
                     at_chance=r["at_chance"], mechanism=r["mechanism"])
                for r in get_training()]
    if kind == "validation":
        v = get_validation()
        return v["rows"] if v.get("ok") else []
    if kind == "runs":
        return get_runs(task="scalability", limit=5000)
    raise ValueError(f"unknown export kind: {kind}")
