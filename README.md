# SNN Simulator Benchmark and Selection Dashboard

Code, measured data and an interactive dashboard for two companion journal manuscripts on
spiking neural network (SNN) simulators:

1. **How Stable Are Spiking Neural Network Simulator Rankings? A Backend-Level Benchmark across Network Size, Metric and Measurement Session**
2. **An Interactive Benchmarking Dashboard for Preference-Aware Selection of Spiking Neural Network Simulators**

Both manuscripts are under review. They share one benchmark harness and one results database,
so they share this repository. The manuscripts themselves are not included here.

Author: **Lhakpa Tshering**, School of Information Technology and Engineering,
Melbourne Institute of Technology, Australia.

---

## Overview

Five SNN simulators are compared across **nine execution backends** on one CPU-only machine,
using the same feedforward leaky integrate-and-fire (LIF) workload at five network sizes
(100, 500, 1,000, 5,000 and 10,000 neurons):

| Simulator | Backends measured |
|---|---|
| Brian2 | NumPy, Cython, C++ standalone |
| NEST | 1, 2 and 4 threads |
| Nengo | reference backend |
| snnTorch | PyTorch (CPU) |
| SpikingJelly | PyTorch (CPU) |

Two plain-NumPy reference implementations act as validation controls. Every measured run is
stored with its provenance (machine, package versions, configuration) in a SQLite database.

---

## Paper 1: ranking stability benchmark

*How Stable Are Spiking Neural Network Simulator Rankings?* asks whether the order of the
backends holds when the network size, the cost metric or the measurement session changes.

| What the paper reports | Where it comes from in this repository |
|---|---|
| Runtime, peak memory and processor use for every backend and size | `results/benchmarks.db`, exported as `results/runs.csv` and `results/conditions.csv` |
| Statistics, pairwise comparisons and rank agreement (Kendall's tau-b) | `snnbench/analyse.py` → `results/ANALYSIS.md`, `results/analysis.json` |
| Scaling exponents (log-log fit of runtime against network size) | `snnbench/analyse.py`, `results/ANALYSIS.md` |
| Two measurement sessions on the same machine | `cpu_corrected_output/session1_*`, `cpu_corrected_output/session2_*` and `cpu_corrected_output/analysis/` |
| Longer simulated window (1 s) check | `long_duration_output/` and `tools/analyse_long_duration.py` |
| Processor-time energy proxy | `snnbench/profiler.py`, `snnbench/eflop.py` |
| Cross-backend equivalence check | `results/validate.txt` |

Regenerate the analysis from the stored data (no simulators needed):

```bash
python run.py analyse                       # writes results/ANALYSIS.md and results/analysis.json
python tools/analyse_long_duration.py       # 1 s long-duration check
```

---

## Paper 2: interactive selection dashboard

*An Interactive Benchmarking Dashboard for Preference-Aware Selection of SNN Simulators*
presents the dashboard built on the same data. For a chosen network size and set of priorities
(runtime, memory growth, scalability and optional exploratory accuracy), it ranks the measured
backends with a weighted-sum method, shows how much each criterion contributed, and converts
the scores into priority shares with a softmax activation function. It also reports how stable
each recommendation is.

| What the paper reports | Where it comes from in this repository |
|---|---|
| Dashboard application | `dashboard/app.py` (Flask) and `dashboard/streamlit_app.py` (Streamlit) |
| Selection method and activation function | `dashboard/optimization.py` |
| Data layer used by every page and export | `dashboard/dashboard_data.py` |
| Robustness of recommendations | `dashboard/robustness.py`, `dashboard/robustness_data/` |
| Recommendation tables, worked example, sensitivity and consequence analyses | `review/reproduce.py`, `review/worked_example.py`, `review/sensitivity.py`, `review/verify.py`, `review/consequence.py` |
| Recommendations recomputed with the 1 s exponents | `review/scalability_with_long_exponents.py` |
| Automated tests (102) | `tests/` |

Run the dashboard locally:

```bash
python -m pip install -r dashboard/requirements.txt
python RUN_DASHBOARD.py                      # http://127.0.0.1:5000

# Streamlit version
python -m pip install -r dashboard/requirements-streamlit.txt
streamlit run dashboard/streamlit_app.py     # http://localhost:8501
```

Regenerate the paper's tables and run the tests:

```bash
python review/reproduce.py
python review/worked_example.py
python review/sensitivity.py
python review/verify.py
python review/consequence.py
python review/scalability_with_long_exponents.py
python -m pip install pytest flask
python -m pytest tests
```

---

## Repository layout

```
snnbench/                 Benchmark harness: one adapter per simulator, runner, profiler, analysis
  adapters/               Brian2, NEST, Nengo, snnTorch, SpikingJelly and NumPy reference adapters
run.py, RUN_ME.py         Command-line entry points for the benchmark
dashboard/                Flask and Streamlit dashboard, selection method, templates and static files
results/                  Main results database (benchmarks.db), CSV exports, analysis outputs
cpu_corrected_output/     Raw output of the two measurement sessions and their analysis
full_run_output/          Raw output of the full-budget training campaign
complete_run_output/      Raw output of the complete campaign
instrument_smoke_output/  Self-test of the CPU measurement instrument
long_duration_output/     1 s simulated-window check
review/                   Scripts that regenerate the dashboard paper's numbers
tests/                    Automated tests of the selection method and dashboard pages
tools/                    Audit, merge and analysis scripts
launchers/                Windows and WSL scripts that ran the campaigns
docs/                     Method notes, verification reports and changelogs
CHECKSUMS.sha256          SHA-256 hash of every file in the release
```

---

## Re-running the benchmark

Measuring again needs the simulators themselves (Python 3.11 or 3.12; NEST is easiest on
Linux or WSL):

```bash
python -m pip install -r requirements-frameworks.txt
python run.py check        # which backends this machine can run
python run.py validate     # cross-backend equivalence check
python run.py bench --tasks inference,scalability --warmup 5 --measured 5
python run.py bench --tasks training --preset paper
python run.py analyse
```

New runs are appended to `results/benchmarks.db`. A backend that cannot run on the machine is
skipped with a printed reason and is never recorded as zero. The published measurements were
taken on one machine (Intel Core i9-14900HX, no accelerator); values on other hardware will differ.

---

## Scope and limitations

- All measurements come from one CPU-only machine. The results compare the implemented
  simulator-backend configurations under one protocol, not the simulators in general.
- The workload is a feedforward LIF network with fixed fan-in; recurrent and convolutional
  networks are out of scope.
- The energy figure is an estimate derived from processor time, not a measurement of
  electrical power.
- Accuracy is reported for context and is used only in clearly labelled exploratory selection
  scenarios.
- The dashboard ranks only the measured backends at the measured network sizes.

---

## Integrity

```bash
sha256sum -c CHECKSUMS.sha256
```

## Licence

- Code: MIT licence (`LICENSE`).
- Measured data in `results/` and the campaign output folders: CC BY 4.0 (`DATA_LICENSE.md`).

## Citation

`CITATION.cff` gives the citation details. Until the two articles are published, please cite
the thesis on which they are based:

> L. Tshering, "Building a Benchmarking Dashboard for SNN Methods," Master of ICT Research thesis,
> School of Information Technology and Engineering, Melbourne Institute of Technology, 2026.
