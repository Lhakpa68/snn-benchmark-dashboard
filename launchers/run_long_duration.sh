#!/usr/bin/env bash
# Longer-duration check for the journal revision (Paper 1): the scalability sweep repeated with
# a 1 s simulated window (10,000 steps) instead of 10 ms. Same nine SNN backends, same sizes,
# 2 warm-up + 3 measured runs per condition. Uses its own database; nothing existing is changed.
# Also records the installed SpikingJelly version.
set -u
WIN_DIR="/mnt/c/Users/Tsher/OneDrive/Desktop/LT Final Theis Files/SNN_Benchmark_Dashboard_V6_Final/SNN_Benchmark_Dashboard"
OUT="$WIN_DIR/long_duration_output"
WORK="$HOME/snn_long_duration"
PY="$HOME/projects/snn_benchmark_dashboard.backup_20260805_224202/.venv/bin/python3.11"
LOG="$WORK/long_duration.log"
mkdir -p "$OUT" "$WORK/results"
rm -f "$OUT/FINISHED.txt" "$OUT/FAILED.txt" 2>/dev/null
exec > >(tee -a "$LOG") 2>&1
fail() { echo "FAILED: $*"; echo "$*" > "$OUT/FAILED.txt"; cp -f "$LOG" "$OUT/" 2>/dev/null; exit 1; }
echo "=== Long-duration scalability check (SIM_MS = 1000) ==="; echo "started $(date -Is)"
[ -x "$PY" ] || fail "simulator Python not found at $PY"
"$PY" - > "$OUT/package_versions.txt" <<'PYEOF'
import importlib.metadata as m
for p in ["spikingjelly","snntorch","torch","brian2","nengo","numpy","scipy"]:
    try: print(p, m.version(p))
    except Exception as e: print(p, "not found:", e)
try:
    import nest; print("nest", nest.__version__)
except Exception as e: print("nest", "import failed:", e)
PYEOF
cat "$OUT/package_versions.txt"
if pgrep -f "python[0-9.]* run\.py bench" >/dev/null 2>&1; then fail "another benchmark is still running"; fi
rm -rf "$WORK/snnbench" "$WORK/tools"
cp -f "$WIN_DIR/run.py" "$WIN_DIR/RUN_ME.py" "$WORK/"
tar -C "$WIN_DIR" --exclude=__pycache__ -cf - snnbench tools | tar -C "$WORK" -xf -
cd "$WORK" || fail "cannot enter $WORK"
export SNN_RESULTS_DIR="$WORK/results" SNN_SIM_MS=1000
DB="$WORK/results/benchmarks.db"; [ -f "$DB" ] && mv "$DB" "$DB.previous_$(date +%Y%m%d_%H%M%S)"
uptime; nproc
"$PY" run.py bench --tasks scalability --warmup 2 --measured 3 --only brian2,nest,nengo,snntorch,spikingjelly || fail "benchmark exited with an error"
cp -f "$DB" "$OUT/benchmarks.db"; cp -f "$WORK/results/"*.csv "$OUT/" 2>/dev/null
echo "finished $(date -Is)"; cp -f "$LOG" "$OUT/"; date -Is > "$OUT/FINISHED.txt"
echo; echo "DONE. You can close this window."
