#!/usr/bin/env bash
# CPU-corrected re-measurement of Experiments 1 and 3 (inference, scalability).
#
# Why: the utilisation instrument was defective in both earlier campaigns
# (see docs/CPU_MEASUREMENT_CORRECTION.md). Runtime was timed correctly, but
# processor utilisation - and therefore the energy proxy - was not. This run
# repeats the same protocol (all 11 backends, N = 100..10000, 5 warm-up +
# 5 measured runs) with the corrected instrument in snnbench/profiler.py.
# Training is not repeated. About 10 minutes. Uses a fresh database; nothing
# existing is modified.
set -u
WIN_DIR="/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final"
OUT="$WIN_DIR/cpu_corrected_output"
WORK="$HOME/snn_cpu_corrected"
PY="$HOME/projects/snn_benchmark_dashboard.backup_20260805_224202/.venv/bin/python3.11"
LOG="$WORK/cpu_corrected.log"

mkdir -p "$OUT" "$WORK/results"
rm -f "$OUT/FINISHED.txt" "$OUT/FAILED.txt" 2>/dev/null
exec > >(tee -a "$LOG") 2>&1

fail() { echo "FAILED: $*"; echo "$*" > "$OUT/FAILED.txt"; cp -f "$LOG" "$OUT/" 2>/dev/null; exit 1; }

echo "=== CPU-corrected measurement: inference + scalability ==="
echo "started $(date -Is)"
[ -x "$PY" ] || fail "simulator Python not found at $PY"

# Nothing else may compete for the processor while utilisation is measured.
if pgrep -f "python[0-9.]* run\.py bench" >/dev/null 2>&1; then
  fail "another benchmark (run.py bench) is still running - stop it first (STOP EXPERIMENT.bat)"
fi
pkill -f "snn_launch256.sh" 2>/dev/null   # old campaign mirror loop, if still alive

# Fresh copy of the current code from the project folder.
rm -rf "$WORK/snnbench" "$WORK/tools"
cp -f "$WIN_DIR/run.py" "$WIN_DIR/RUN_ME.py" "$WORK/"
tar -C "$WIN_DIR" --exclude=__pycache__ -cf - snnbench tools | tar -C "$WORK" -xf -
[ -f "$WORK/results/mnist_784.npz" ] || cp -f "$WIN_DIR/results/mnist_784.npz" "$WORK/results/" 2>/dev/null
cd "$WORK" || fail "cannot enter $WORK"
export SNN_RESULTS_DIR="$WORK/results"
DB="$WORK/results/benchmarks.db"
if [ -f "$DB" ]; then mv "$DB" "$DB.previous_$(date +%Y%m%d_%H%M%S)"; fi

echo; echo "--- instrument check (known loads) ---"
"$PY" tools/cpu_instrument_check.py | tee "$OUT/instrument_check.txt"
grep -q "^SELFTEST PASS" "$OUT/instrument_check.txt" || fail "instrument self-test did not pass"

echo; echo "--- machine load before the run ---"
uptime; nproc

echo; echo "--- benchmark ---"
"$PY" run.py bench --tasks inference,scalability ${SNN_TEST_ONLY:+--only $SNN_TEST_ONLY} || fail "benchmark exited with an error"
"$PY" run.py validate > "$OUT/validate.txt" 2>&1 || echo "(validate returned non-zero; see validate.txt)"

cp -f "$DB" "$OUT/benchmarks.db"
cp -f "$WORK/results/"*.csv "$OUT/" 2>/dev/null
echo "finished $(date -Is)"
cp -f "$LOG" "$OUT/"
date -Is > "$OUT/FINISHED.txt"
echo; echo "DONE. You can close this window."
