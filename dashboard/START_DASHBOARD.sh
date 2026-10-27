#!/usr/bin/env bash
# Serves the dashboard. Database path, host, port and title all come from
# dashboard_config.py in this folder — edit that file, not this script, to
# point the dashboard somewhere else.
set -u
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"

$PY -c "import flask" 2>/dev/null || {
  echo "Flask is missing. Installing it..."
  $PY -m pip install flask || { echo "Could not install Flask."; exit 1; }
}

exec $PY app.py
