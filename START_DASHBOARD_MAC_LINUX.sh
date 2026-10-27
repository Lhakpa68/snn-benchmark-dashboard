#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
if [[ ! -x .dashboard_venv/bin/python ]]; then "$PY" -m venv .dashboard_venv; fi
if ! .dashboard_venv/bin/python -c 'import flask' 2>/dev/null; then
  echo 'Installing Flask for the dashboard (first launch requires internet)'
  .dashboard_venv/bin/python -m pip install 'Flask>=3.0,<4'
fi
.dashboard_venv/bin/python -c 'import pathlib,sqlite3; p=pathlib.Path("results/benchmarks.db"); assert p.is_file(),"Results DB missing"; c=sqlite3.connect(p); assert c.execute("PRAGMA quick_check").fetchone()[0]=="ok"; c.close()'
echo 'Open http://127.0.0.1:5000 in your browser'
exec .dashboard_venv/bin/python RUN_DASHBOARD.py
