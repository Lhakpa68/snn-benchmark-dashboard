# SNN Benchmark Dashboard

Everything needed to view the benchmarking dashboard lives in this one
folder now. Nothing else needs to be connected, moved, or copied.

## To view the dashboard

Double-click `RUN_DASHBOARD.py`, or from a terminal in this folder:

    python RUN_DASHBOARD.py

It installs Flask automatically if needed, then opens
`http://127.0.0.1:5000` in your browser after about a second.

If double-clicking shows nothing, run the command above from a Command
Prompt or PowerShell window instead - that will print the actual error
(most commonly: Python is not on PATH, or `.py` files are associated with
something other than Python). Whatever it prints, that's what to fix, or
send it back for help.

## What's in here

- `RUN_DASHBOARD.py` - the entry point. Run this.
- `dashboard/` - the Flask app (`app.py`, `dashboard_data.py`,
  `dashboard_config.py`, `dashboard_theme.py`, `templates/`, `static/`) and
  the Streamlit alternative (`streamlit_app.py`, `run_streamlit.py`).
- `results/` - the benchmark data the dashboard reads:
  `benchmarks.db` (the database), `validate.txt`, plus the CSV/JSON exports
  and analysis notes generated alongside it.
- `snnbench/` - the benchmarking library that produced the data (framework
  adapters, the runner, the analysis pipeline). Not needed just to view the
  dashboard; kept here so the full pipeline is in one place.
- `run.py`, `RUN_ME.py` - entry points into the benchmarking suite itself
  (re-running measurements, validation, analysis).

## Where this came from

This folder consolidates what was previously split across:

- `Latest LT RF\SNN_CPU_Experiment\` - the canonical, git-tracked source for
  `dashboard/`, `snnbench/`, and `results/`.
- `MIT College\Last Edition LT\code\` - a working mirror of the above, which
  had `dashboard_config.py` edited independently (that newer version, with
  the `SNN_RESULTS_DIR` override, is the one kept here).

Those original locations were left as they were - nothing was deleted or
moved out of them. This folder is a clean, self-contained copy assembled
from the current, correct versions of each file. Anything under a
`DELETE_THIS_FOLDER`, `_to_delete`, `_old_*`, or `*_backup` name in any of
the connected folders was skipped as already-superseded.
