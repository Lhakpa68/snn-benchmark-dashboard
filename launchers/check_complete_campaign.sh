#!/usr/bin/env bash
# Progress report for the complete campaign. Read-only; safe at any time.
set -u
OUT="/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final/complete_run_output"
PROJ="$HOME/snn_complete_run/Complete Simulator Campaign"
PY="$HOME/projects/snn_benchmark_dashboard.backup_20260805_224202/.venv/bin/python3.11"
DB="$PROJ/results/benchmarks.db"

echo "=== complete campaign status  $(date -Is) ==="
if pgrep -f "phases.sh" >/dev/null 2>&1; then
  echo "RUNNING"
  pgrep -af "run.py bench" | head -3 | sed 's/^/   now: /' | cut -c1-140
else
  echo "NOT RUNNING"
fi
[ -f "$OUT/FINISHED_256.txt" ] && echo "hidden-256 campaign COMPLETE: $(cat "$OUT/FINISHED_256.txt")"
[ -f "$OUT/FINISHED.txt" ]     && echo "ALL PHASES COMPLETE: $(cat "$OUT/FINISHED.txt")"
[ -f "$OUT/FAILED.txt" ]       && echo "FAILED: $(cat "$OUT/FAILED.txt")"
echo
"$PY" - "$DB" <<'PYX'
import sqlite3, sys, re
try:
    c = sqlite3.connect(sys.argv[1]); c.row_factory = sqlite3.Row
except Exception as e:
    print("no database yet:", e); raise SystemExit
n = c.execute("SELECT COUNT(DISTINCT run_group) FROM conditions WHERE task='scalability'").fetchone()[0]
print(f"inference/scalability sessions recorded: {n} of 2")
rows = c.execute("SELECT * FROM conditions WHERE task='training' ORDER BY notes, framework, backend").fetchall()
NEED = ["nengo/reference","snntorch/cpu","spikingjelly/cpu","nest/threads1","nest/threads2",
        "nest/threads4","brian2/cython","brian2/numpy","brian2/cpp_standalone"]
for hid, tn, label in ((256,6000,"PHASE 3  training 6,000 / 3 epochs"),
                       (256,60000,"PHASE 4  training 60,000 / 10 epochs  <- the thesis budget"),
                       (500,60000,"PHASE 5  training 60,000 / 10 epochs, hidden 500 (optional)")):
    sel = [r for r in rows if f"hidden={hid};" in (r['notes'] or '') and f"train_n={tn};" in (r['notes'] or '')]
    got = {f"{r['framework']}/{r['backend']}": r for r in sel}
    print(f"\n{label}: {len(got)} of 9 backends")
    for k in NEED:
        r = got.get(k)
        if not r:
            print(f"   {k:<24} -")
            continue
        cpu = r['cpu_pct']; mem = r['peak_rss_mb']; en = r['energy_median_j']
        flag = "" if (cpu is not None and mem is not None and en is not None) else "   << MISSING A MEASUREMENT"
        print(f"   {k:<24} {r['runtime_median_s']:>9.1f} s/epoch  "
              f"{(f'{cpu:6.1f}%' if cpu is not None else '     -')}  "
              f"{(f'{mem:5.0f} MB' if mem is not None else '    -')}  "
              f"{(f'{en:10.1f} J' if en is not None else '     -')}  "
              f"acc {r['accuracy_pct']:.2f}%{flag}")
PYX
echo
echo "log: $OUT/complete_run.log"
