#!/usr/bin/env bash
# Liveness check for the running campaign. Writes a report; changes nothing.
set -u
WIN_DIR="/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final"
OUT="$WIN_DIR/full_run_output"
PROJ="$HOME/snn_full_run/Full-Scale Simulator Comparison"
R="$OUT/check.txt"
mkdir -p "$OUT" 2>/dev/null
say() { echo "$*"; echo "$*" >> "$R" 2>/dev/null; }
: > "$R" 2>/dev/null

say "=== campaign liveness check ==="
say "when : $(date -Is)"
say ""

PIDS=$(pgrep -f "run.py bench" 2>/dev/null)
if [ -z "$PIDS" ]; then
  say "NOT RUNNING - no 'run.py bench' process found."
  if [ -f "$OUT/FINISHED.txt" ]; then
    say "FINISHED.txt exists: the campaign completed."
  else
    say "and FINISHED.txt does NOT exist: it died before completing."
  fi
else
  say "RUNNING. pid(s): $(echo $PIDS | tr '\n' ' ')"
  say ""
  say "sample 1:"
  ps -o pid,etime,time,pcpu,pmem,rss,stat --no-headers -p $PIDS 2>/dev/null \
    | while IFS= read -r l; do say "   $l"; done
  say "   (columns: pid  elapsed  cpu-time  %cpu  %mem  rss-kb  state)"
  sleep 15
  say ""
  say "sample 2, 15 s later:"
  ps -o pid,etime,time,pcpu,pmem,rss,stat --no-headers -p $PIDS 2>/dev/null \
    | while IFS= read -r l; do say "   $l"; done
  say ""
  say "If cpu-time advanced between the two samples, it is genuinely computing."
fi
say ""

say "--- child / worker processes ---"
pgrep -af "python" 2>/dev/null | head -12 | while IFS= read -r l; do say "   $l"; done
say ""

say "--- results database ---"
DB="$PROJ/results/benchmarks.db"
if [ -f "$DB" ]; then
  say "   $(ls -l "$DB" | awk '{print $5" bytes   modified "$6" "$7" "$8}')"
  PY="$HOME/projects/snn_benchmark_dashboard.backup_20260805_224202/.venv/bin/python3.11"
  [ -x "$PY" ] || PY=python3
  "$PY" - "$DB" <<'PYX' 2>/dev/null | while IFS= read -r l; do say "   $l"; done
import sqlite3, sys
con = sqlite3.connect(sys.argv[1]); con.row_factory = sqlite3.Row
for t in ("runs", "conditions"):
    try:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n} rows")
    except Exception as e:
        print(f"{t}: {e}")
try:
    rows = con.execute(
        "SELECT framework, backend, task, COUNT(*) c FROM conditions "
        "GROUP BY framework, backend, task ORDER BY MAX(id)").fetchall()
    print("recorded so far:")
    for r in rows:
        print(f"   {r['framework']}/{r['backend']:<16} {r['task']:<12} {r['c']}")
except Exception as e:
    print(e)
PYX
else
  say "   no database yet"
fi
say ""

say "--- last 25 lines of the run log ---"
tail -25 "$PROJ/full_run.log" 2>/dev/null | while IFS= read -r l; do say "   $l"; done
say ""
say "=== end of check ==="
sleep 3
