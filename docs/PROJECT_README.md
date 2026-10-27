# Building a Benchmarking Dashboard for SNN Methods

A CPU-only benchmark of six spiking neural network frameworks under one
protocol, plus a dashboard that reads the results. **The measurement campaign
is finished** — `results/benchmarks.db` already holds the full dataset this
thesis reports on. You do not need to re-run anything to see the results.

---

## To see the results

In PyCharm, pick the run configuration named **`5 Dashboard`** from the
dropdown at the top of the window and press Run (the green triangle). The
console prints a link — `http://127.0.0.1:5000` — click it or paste it into a
browser. The page reloads itself every 20 seconds, so it always shows the
current database with no manual refresh needed.

To stop it, press the red square in the Run panel.

If you'd rather not use PyCharm: open the project's terminal and run
`python dashboard/app.py` from `SNN_CPU_Experiment/`, using the same Python
environment the `5 Dashboard` configuration uses.

---

## The other run configurations

| Configuration | Runs | What it does |
|---|---|---|
| `1 Run Everything` | `RUN_ME.py` | The full four-step campaign: check, validate, benchmark, analyse. Only needed to measure a **new** campaign — not needed to view the existing results. |
| `2 Check Environment` | `run.py check` | Reports the machine and which frameworks/backends it can see. Takes a second, changes nothing. |
| `3 Quick Test` | `run.py bench --quick` | A two-minute pipeline smoke test. Not thesis data. |
| `4 Analyse Only` | `run.py analyse` | Recomputes `results/ANALYSIS.md` from whatever is already in the database. |
| `5 Dashboard` | `dashboard/app.py` | Serves the results page. Read-only — nothing here writes to the database. |

**Important:** `1 Run Everything`, `3 Quick Test`, and any other command that
starts a new benchmark **append** to `results/benchmarks.db`. Running one of
these on a different machine (or profile) than the one the thesis reports on
would mix in rows from a second machine, which the dashboard would then have
to exclude — see "Single hardware platform" below. Only re-run these if you
specifically intend to extend the campaign, and do it on the same machine the
existing 598 rows were measured on.

---

## What was measured

Three experiments, all on one machine (CPU only — no GPU backend is
registered by any adapter), across six frameworks plus a NumPy control:

- **Inference** — one forward simulation at N = 100 neurons, setup and
  simulation timed separately.
- **Scalability** — the same network at 100 / 500 / 1000 / 5000 / 10 000
  neurons.
- **Training** — supervised MNIST, each framework using its own native
  learning rule (surrogate-gradient backprop, spike-timing-dependent
  plasticity, or Nengo's analytic decoder solve, as appropriate).

Frameworks: Brian2 (NumPy, Cython, C++ standalone backends), NEST (multiple
thread counts), Nengo, snnTorch, SpikingJelly, Norse, plus a hand-written
NumPy implementation of the same specification as an experimental control.

Protocol: 5 warm-up runs discarded, then 5 measured runs kept, with every
individual run stored (not just a mean and standard deviation).

**Single hardware platform.** The whole comparison depends on holding the
machine fixed, so that a runtime difference can be attributed to the
simulator rather than to the hardware it happened to run on. That is why the
dashboard has no hardware selector, and why a second machine's rows are
excluded rather than pooled.

Full parameter list: `snnbench/config.py` — every value used lives there and
nowhere else.

---

## Layout

```
SNN_CPU_Experiment/
  README.md                 this file
  RUN_ME.py                 full campaign, no arguments (1 Run Everything)
  run.py                    the command line (check / validate / bench / analyse)
  requirements-frameworks.txt   the six frameworks
  snnbench/
    config.py                every parameter, defined once
    machine.py, profiler.py, store.py, registry.py, runner.py,
    analyse.py, eflop.py, mnist.py, adapters/
  dashboard/
    app.py                   Flask, read-only (5 Dashboard)
    dashboard_config.py, dashboard_data.py, dashboard_theme.py
    templates/, static/
    streamlit_app.py         a pure-Python alternative to app.py — same data,
                              no Flask/HTML/JS at all, if you'd rather run
                              `streamlit run dashboard/streamlit_app.py`
  results/
    benchmarks.db             the finished campaign — SQLite: runs, conditions, meta
    runs.csv, conditions.csv  the same data as CSV
    ANALYSIS.md, analysis.json  every statistic, already computed
    check.txt, validate.txt, bench_log.txt
```

---

## If something looks wrong on the dashboard

**A framework/backend is missing from a chart.** Almost always means
`results/benchmarks.db` has been overwritten or appended to from a run on a
different machine. The dashboard's Provenance tab (bottom of the page) shows
which machine(s) the current database's rows came from, and how many rows, if
any, were excluded as off-platform.

**"No results to show."** `results/benchmarks.db` is missing or empty —
re-run `1 Run Everything`, or restore a backup if one exists.

**Charts don't render / "Charts could not load."** The page's charting is
fully local (`static/js/minichart.js`) — nothing is fetched from the internet,
so this should not happen offline. If it does, check the browser console for
an error and confirm `static/js/minichart.js` is being served (Network tab).
