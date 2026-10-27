**Current October 2026 four-criterion version: start with `README_START_HERE_APPROVED_TITLE.md` and the latest thesis file `thesis/Thesis_SNN_Methods_Four_Criteria_Optimisation_2026.docx`. Previous design documentation and original data remain for provenance.**

# SNN Simulator Benchmark: final project folder

This folder is the complete, current copy of the thesis project "Building a
Benchmarking Dashboard for SNN Comparison". It holds the code, the launchers, the
measured results, the dashboard and the thesis. Older copies and duplicates were
moved to `..\_duplicates_to_delete` for you to review and delete.

## Layout

| Folder / file | What it is |
|---|---|
| `RUN_DASHBOARD.py` | Double-click to open the dashboard (http://127.0.0.1:5000, or the next free port if 5000 is reserved) |
| `dashboard/` | Flask dashboard: app, data layer, JS, CSS and templates |
| `snnbench/`, `run.py`, `RUN_ME.py` | The benchmark code, including the patched Brian2 checkpoint runner |
| `launchers/` | Windows `.bat` launchers and the WSL shell scripts they call |
| `results/benchmarks.db` | **The database the dashboard and thesis use.** Inference and scalability come from the CPU-corrected session of 20 Sep 2026; training comes from the August fixed-budget campaign and the September full-budget campaign |
| `results/benchmarks_before_cpu_correction.db` | The same database before the CPU-corrected sessions were added |
| `results/benchmarks_before_fullrun_merge.db` | The database before the nine full-budget training rows were added |
| `results/benchmarks_PRE_REPAIR_2026-08-27.db` | The database before the 27 Aug profiler repair, kept as evidence |
| `full_run_output/` | Raw output of the full-scale campaign (its own DB, log, validation, CSVs) |
| `cpu_corrected_output/` | Raw output of the two CPU-corrected sessions (20 Sep), the instrument self-test and the analysis summaries |
| `thesis/` | `Final Thesis Edition - Rewritten.docx/.pdf` (current; every change highlighted yellow) and the review report |
| `tools/` | `audit_completeness.py`, `cpu_instrument_check.py`, `merge_corrected.py`, `merge_fixed_budget.py`, `apply_ch4_fullrun.py`, and `thesis_build/` (the scripts that rebuilt the thesis's figures, tables and text) |
| `docs/` | `CPU_MEASUREMENT_CORRECTION.md` (read this first), the verification report, changelogs, revision notes, the old READMEs, screenshots and `evidence/` |

## View the dashboard

Double-click `RUN_DASHBOARD.py`, or run `python RUN_DASHBOARD.py`. The training
page has a sample-budget toggle: 6,000 images / 3 epochs, or 60,000 / 10 (the default).

## Re-run or resume the campaign

Run `launchers\RUN 256 CAMPAIGN.bat`. Use `CHECK PROGRESS.bat` to watch it and
`STOP EXPERIMENT.bat` to stop it. The campaign resumes where it stopped. It runs
inside WSL from a working copy at
`~/snn_full_run/Full-Scale Simulator Comparison`. On a fresh machine the launcher
creates that copy from this folder.

The simulators run in a Python environment that exists only on this laptop's WSL:
`~/projects/snn_benchmark_dashboard.backup_20260805_224202/.venv/bin/python3.11`
(set as `PY=` in `launchers/run_256_campaign.sh`). On another machine, build an
environment from `requirements-frameworks.txt` (see `launchers/prepare_environment.sh`)
and change `PY=`.

## Re-measure CPU utilisation (inference + scalability)

Run `launchers\RUN CPU-CORRECTED MEASUREMENT.bat` (about 10 minutes). It checks the CPU instrument against
known loads, then repeats Experiments 1 and 3 into a fresh database under `cpu_corrected_output/`.

## Check that every experiment really ran

    python tools/audit_completeness.py "<path to this folder>"

Result on 20 Sep 2026: **0 problems.**

| Experiment | Thesis / dashboard data | Replication (corrected session 2) | Full-scale campaign |
|---|---|---|---|
| Inference (CPU, energy, memory on every run) | 22 / 22 | 22 / 22 | 22 / 22 (CPU not used) |
| Scalability (5 measured runs each) | 110 / 110 | 110 / 110 | 110 / 110 (CPU not used) |
| Training, 6,000 images / 3 epochs | 9 / 9 | n/a | n/a |
| Training, 60,000 images / 10 epochs | 9 / 9 | n/a | 9 / 9 |

What was fixed on 20 Sep and why is in `docs/CPU_MEASUREMENT_CORRECTION.md`. In short, the old CPU instrument gave
false readings in both earlier campaigns, so inference and scalability were measured again with a corrected, tested
instrument. Every one of the 660 runs now has a CPU reading and an energy value.

Not measured, with the reason recorded in the thesis (Sections 4.6 and 4.12):
- Training CPU utilisation, energy and peak memory. The training code timed wall-clock only, and repeating the
  training campaigns would take about 8 days (the full-budget run took 7 days 20 hours).
- Hidden width 500. This is a declared deviation; the earlier 500-width results were discarded.
