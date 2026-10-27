#!/usr/bin/env bash
# The complete campaign of 21 September 2026: every experiment the thesis
# reports, measured end to end with the corrected instruments, in one database.
#
# WHY THIS EXISTS. Two gaps remained after the 20 September correction:
#   1. Experiment 2 (training) recorded only a duration. Processor
#      utilisation, the energy proxy and peak memory were never observed on
#      that path, so the thesis had to declare them missing. The adapters are
#      now instrumented and this campaign measures them.
#   2. The width the Candidature Confirmation Report proposed (500 hidden
#      units) was never run. It is the last phase here, optional and
#      stoppable, so the answer is measured rather than argued if asked for.
#
# NOTHING EXISTING IS TOUCHED. This writes to its own working copy and its own
# database. The thesis results in ../results/benchmarks.db are left alone, and
# the two are only compared afterwards, deliberately.
#
# RESUMABLE. Every phase checks the database first and skips itself if its rows
# are already there, so re-running this after a reboot, a crash or an
# accidental stop continues instead of starting over.
set -u

WIN_DIR="/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final"
LAUNCH_DIR="$WIN_DIR/launchers"
export OUT="$WIN_DIR/complete_run_output"
export PROJ="$HOME/snn_complete_run/Complete Simulator Campaign"
export PY="$HOME/projects/snn_benchmark_dashboard.backup_20260805_224202/.venv/bin/python3.11"
export DB="$PROJ/results/benchmarks.db"
export LOG="$PROJ/complete_run.log"
export LOG_WIN="$OUT/complete_run.log"
export HIDDEN=256
export TRAIN_N=60000
export CHUNK_SECONDS=1800
STATUS="$OUT/status.txt"
PHASES="$PROJ/phases.sh"

mkdir -p "$OUT" 2>/dev/null
rm -f "$OUT/FINISHED.txt" "$OUT/FINISHED_256.txt" "$OUT/FAILED.txt" 2>/dev/null
say() { echo "$*"; echo "$*" >> "$STATUS" 2>/dev/null; }
: > "$STATUS" 2>/dev/null

say "=== complete campaign, instrumented training ==="
say "started : $(date -Is)"
say "spec    : 60,000 train / 10,000 test / 10 epochs / hidden $HIDDEN"
say "new     : training now measures utilisation, energy proxy and peak memory"
say "scope   : every experiment, every backend, nothing skipped"
say ""

# Parent first: killing run.py alone lets a phase runner notice the child exit,
# advance and spawn a replacement, which on 12 Sep left two campaigns running
# at once and voided a morning of timings.
kill_matching() {
  local pat="$1" sig="${2:-TERM}" pid
  for pid in $(pgrep -f "$pat" 2>/dev/null); do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    kill "-$sig" "$pid" 2>/dev/null
  done
}
kill_matching "snn_launch256.sh"
kill_matching "snn_launch_complete.sh"

if pgrep -f "run.py|phases.sh" > /dev/null 2>&1; then
  say "stopping the previous run (parent first):"
  pgrep -af "run.py bench|phases.sh" | head -4 | while IFS= read -r l; do say "   ${l:0:100}"; done
  stopped=0
  for attempt in 1 2 3 4 5; do
    kill_matching "campaign_phases"; kill_matching "phases.sh"
    sleep 1
    kill_matching "run.py bench"; kill_matching "nest_train_worker"; kill_matching "nest_worker"
    sleep 2
    kill_matching "run.py" KILL; kill_matching "phases.sh" KILL
    sleep 1
    if ! pgrep -f "run.py" >/dev/null 2>&1 && ! pgrep -f "phases.sh" >/dev/null 2>&1; then
      stopped=1; say "stopped cleanly on attempt $attempt"; break
    fi
  done
  if [ "$stopped" != 1 ]; then
    say "ABORTING: processes survived five stop attempts. Starting now would"
    say "run two campaigns at once and void every timing. Nothing was started."
    pgrep -af "run.py|phases.sh" | while IFS= read -r l; do say "   ${l:0:100}"; done
    sleep 90
    exit 1
  fi
else
  say "nothing was running."
fi
say ""

# The working copy is rebuilt from the project folder on every launch, because
# the instrumentation of 21 Sep lives there. The results directory is kept.
say "installing the current code into: $PROJ"
mkdir -p "$PROJ/results" || { say "FAILED: cannot create $PROJ"; sleep 60; exit 1; }
rm -rf "$PROJ/snnbench" "$PROJ/tools"
cp -f "$WIN_DIR/run.py" "$WIN_DIR/RUN_ME.py" "$PROJ/" \
  && ( cd "$WIN_DIR" && tar --exclude=__pycache__ -cf - snnbench tools ) | ( cd "$PROJ" && tar -xf - ) \
  || { say "FAILED: could not install the code into $PROJ"; sleep 60; exit 1; }
[ -f "$PROJ/results/mnist_784.npz" ] || cp -f "$WIN_DIR/results/mnist_784.npz" "$PROJ/results/" 2>/dev/null

tr -d '\r' < "$LAUNCH_DIR/campaign_phases_complete.sh" > "$PHASES" \
  || { say "FAILED: could not install $PHASES"; sleep 60; exit 1; }

[ -x "$PY" ]          || { say "FAILED: interpreter not found at $PY"; sleep 60; exit 1; }
[ -f "$PROJ/run.py" ] || { say "FAILED: project not found at $PROJ";   sleep 60; exit 1; }

export SNN_RESULTS_DIR="$PROJ/results"
if [ -f "$DB" ]; then
  say "database: reusing $(basename "$DB") - completed phases will be skipped"
else
  say "database: will be created fresh (the thesis database is not touched)"
fi
say ""

touch "$LOG"
if command -v setsid >/dev/null 2>&1; then RUNNER="setsid nohup"; else RUNNER="nohup"; fi
$RUNNER env SNN_RESULTS_DIR="$PROJ/results" bash "$PHASES" >> "$LOG" 2>&1 < /dev/null &
say "LAUNCHED: pid $!"

# Mirror the log and database to Windows every 30 s while the runner is alive,
# then once more and stop. An earlier "while true" mirror was found still
# copying hours after its campaign had ended.
sleep 3
( while pgrep -f "$PHASES" >/dev/null 2>&1; do
    cp -f "$LOG" "$LOG_WIN" 2>/dev/null
    cp -f "$DB" "$OUT/benchmarks.db" 2>/dev/null
    sleep 30
  done
  cp -f "$LOG" "$LOG_WIN" 2>/dev/null
  cp -f "$DB" "$OUT/benchmarks.db" 2>/dev/null ) >/dev/null 2>&1 &

say ""
say "   0  processor-clock self-test                        < 1 min"
say "   1  inference + scalability, 11 backends (A)           0.1 h"
say "   2  inference + scalability, 11 backends (B, repeat)   0.1 h"
say "   3  training 6,000/3ep, all 9 backends                 4.5 h   <- repeat budget"
say "   4  training 60,000/10ep, all 9 backends             134   h   <- the thesis budget"
say "        4a-4f Nengo, SpikingJelly, snnTorch, NEST x3    23   h"
say "        4g-4i Brian2 Cython, NumPy, C++ standalone     111   h"
say "      -> everything the thesis reports is measured here: about 5.8 days"
say "   5  OPTIONAL hidden 500, the CCR-proposed width      ~260   h"
say "      stop it by creating: $OUT/SKIP_WIDTH_500.txt"
say ""
say "Resumable: re-running this launcher skips phases already recorded."
say "log     : $LOG"
say "mirrored: $LOG_WIN  (every 30 s)"
say "database: $OUT/benchmarks.db  (every 30 s)"

echo
echo "==============================================================="
echo "  Complete campaign running. Nothing skipped."
echo "  Closing this window does NOT stop it."
echo "==============================================================="
echo
sleep 5
tail -f "$LOG"
