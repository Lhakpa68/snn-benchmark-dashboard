#!/usr/bin/env bash
# The complete CCR-specification campaign. Nothing skipped.
#
# Specification, Candidature Confirmation Report Section 4.1:
#   "The input layer has 784 neurons ... The hidden layer has 500 neurons.
#    The output layer has 10 neurons."
#   "The same network is trained on the full MNIST dataset, with 60,000
#    training and 10,000 test examples. Training for 10 epoch."
#
# WIDTH: this campaign runs at hidden 256, not the 500 the CCR proposed. The
# deviation is deliberate and must be declared in Section 3.7. Reasons: the
# whole of Chapter 4 is already measured at 256, so 256 keeps the thesis
# internally consistent; it leaves the training budget as the ONLY variable
# that changes against Table 4.4, avoiding a width/budget confound; and it
# makes these results a direct replacement for the Table 4.5 projections,
# which were themselves computed at 256. The CCR's hardware plan was likewise
# not followed (it specifies an i7-12700 on Ubuntu 22.04; the work ran on an
# i9-14900HX under WSL2) and is handled the same way - by documenting what was
# actually used.
#
# Every training-capable backend is measured at that specification, so
# Chapter 4 can report executed results where it now reports a projection.
# Roughly 140 hours.
#
# RESUMABLE. Each phase checks the database first and skips itself if its rows
# are already there, so re-running this launcher after a reboot, a crash or an
# accidental stop continues instead of starting over.
set -u

WIN_DIR="/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final"
LAUNCH_DIR="$WIN_DIR/launchers"
export OUT="$WIN_DIR/full_run_output"
export PROJ="$HOME/snn_full_run/Full-Scale Simulator Comparison"
export PY="$HOME/projects/snn_benchmark_dashboard.backup_20260805_224202/.venv/bin/python3.11"
export DB="$PROJ/results/benchmarks.db"
export LOG="$PROJ/full_run.log"
export LOG_WIN="$OUT/full_run.log"
export HIDDEN=256
export TRAIN_N=60000
STATUS="$OUT/status.txt"
PHASES="$PROJ/phases.sh"

mkdir -p "$OUT" 2>/dev/null
rm -f "$OUT/FINISHED.txt" 2>/dev/null
say() { echo "$*"; echo "$*" >> "$STATUS" 2>/dev/null; }
: > "$STATUS" 2>/dev/null

say "=== complete CCR-specification campaign ==="
say "started : $(date -Is)"
say "spec    : 60,000 train / 10,000 test / 10 epochs / hidden $HIDDEN"
say "source  : CCR Section 4.1 proposed 500 hidden; 256 used - see header, declare in Section 3.7"
say "scope   : every training-capable backend, nothing skipped"
say ""

# Parent FIRST. Killing run.py alone lets campaign_phases.sh notice the child
# exit, advance to its next phase and spawn a replacement - which on 12 Sep
# orphaned a NEST training from a superseded campaign and left it running
# concurrently with the new one, voiding every timing measured that morning.
kill_matching() {
  local pat="$1" sig="${2:-TERM}" pid
  for pid in $(pgrep -f "$pat" 2>/dev/null); do
    [ "$pid" = "$$" ] && continue
    [ "$pid" = "$PPID" ] && continue
    kill "-$sig" "$pid" 2>/dev/null
  done
}

# Mirror loops from launches made before 19 Sep never exited on their own.
# They run as "bash /tmp/snn_launch256.sh"; kill_matching skips this shell.
kill_matching "snn_launch256.sh"

if pgrep -f "run.py|phases.sh" > /dev/null 2>&1; then
  say "stopping the previous run (parent first):"
  pgrep -af "run.py bench|phases.sh" | head -4 | while IFS= read -r l; do say "   ${l:0:100}"; done
  stopped=0
  for attempt in 1 2 3 4 5; do
    kill_matching "campaign_phases.sh"; kill_matching "phases.sh"; kill_matching "snn_phases"
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
    say "run two campaigns at once and void the timings. Nothing was started."
    pgrep -af "run.py|phases.sh" | while IFS= read -r l; do say "   ${l:0:100}"; done
    sleep 90
    exit 1
  fi
else
  say "nothing was running."
fi
say ""

# First run on a machine: build the WSL working copy of the project from the
# final folder. An existing copy is never overwritten - it is what produced
# the recorded results. .venv/.idea are Windows-side and not part of it.
if [ ! -f "$PROJ/run.py" ]; then
  say "setting up the project in WSL from: $WIN_DIR"
  mkdir -p "$PROJ/results" \
    && cp -f "$WIN_DIR/run.py" "$WIN_DIR/RUN_ME.py" "$PROJ/" \
    && ( cd "$WIN_DIR" && tar --exclude=__pycache__ -cf - snnbench ) | ( cd "$PROJ" && tar -xf - ) \
    && cp -f "$WIN_DIR/results/mnist_784.npz" "$PROJ/results/" \
    || { say "FAILED: could not set up the project in $PROJ"; sleep 60; exit 1; }
  say "project set up."
fi
# The phase runner is always taken fresh from launchers/, so an edit there
# takes effect on the next launch.
tr -d '\r' < "$LAUNCH_DIR/campaign_phases.sh" > "$PHASES" \
  || { say "FAILED: could not install $PHASES"; sleep 60; exit 1; }

[ -x "$PY" ]          || { say "FAILED: interpreter not found at $PY"; sleep 60; exit 1; }
[ -f "$PROJ/run.py" ] || { say "FAILED: project not found at $PROJ";   sleep 60; exit 1; }

# The database is KEPT, not set aside - completed phases are what makes this
# resumable. Rows from the aborted hidden=256 attempt live in a separate file,
# so nothing here is at the wrong width.
if [ -f "$DB" ]; then
  say "database: reusing $(basename "$DB") - completed phases will be skipped"
else
  say "database: will be created fresh"
fi
say ""

touch "$LOG"

if command -v setsid >/dev/null 2>&1; then RUNNER="setsid nohup"; else RUNNER="nohup"; fi
$RUNNER bash "$PHASES" >> "$LOG" 2>&1 < /dev/null &

say "LAUNCHED: pid $!"

# Mirror the log and database to Windows every 30 s while the phase runner is
# alive, then once more and stop. The previous loop was "while true" and kept
# copying for hours after the campaign ended (found still running 19 Sep).
sleep 3
( while pgrep -f "$PHASES" >/dev/null 2>&1; do
    cp -f "$LOG" "$LOG_WIN" 2>/dev/null
    cp -f "$DB" "$OUT/benchmarks.db" 2>/dev/null
    sleep 30
  done
  cp -f "$LOG" "$LOG_WIN" 2>/dev/null
  cp -f "$DB" "$OUT/benchmarks.db" 2>/dev/null ) >/dev/null 2>&1 &
say ""
say "  1/8  inference + scalability, all 11 backends      0.3 h"
say "  2/8  training: Nengo, snnTorch, SpikingJelly       0.2 h"
say "  3/8  training: NEST / 4 threads                    3.6 h"
say "  4/8  training: NEST / 2 threads                    6.3 h"
say "  5/8  training: NEST / 1 thread                    11.3 h"
say "  6/8  training: Brian2 / Cython                    29.5 h"
say "  7/8  training: Brian2 / NumPy                     44.2 h"
say "  8/8  training: Brian2 / C++ standalone            44.6 h"
say "       total ~140 h = 5.8 days"
say ""
say "Resumable: re-running this launcher skips phases already recorded."
say "log     : $LOG"
say "mirrored: $LOG_WIN  (every 30 s)"

echo
echo "==============================================================="
echo "  Complete CCR-specification campaign running (hidden $HIDDEN)."
echo "  Nothing skipped. Closing this window does NOT stop it."
echo "==============================================================="
echo
sleep 5
tail -f "$LOG"
