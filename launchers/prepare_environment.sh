#!/usr/bin/env bash
# Stop any running campaign, then take a full inventory of every Python
# environment on this machine and what each one can actually import.
# Launches nothing.
set -u

WIN_DIR="/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final"
OUT="$WIN_DIR/full_run_output"
WORK="$HOME/snn_full_run"
PROJ="$WORK/Full-Scale Simulator Comparison"
REPORT="$OUT/environment_report.txt"

mkdir -p "$OUT" 2>/dev/null
say() { echo "$*"; echo "$*" >> "$REPORT" 2>/dev/null; }
: > "$REPORT" 2>/dev/null

say "=== python environment inventory ==="
say "when : $(date -Is)"
say "host : $(whoami)@$(hostname)"
say ""

# --- 1. stop anything that is running -------------------------------------
if pgrep -f "run.py" > /dev/null 2>&1; then
  say "stopping the campaign that is currently running:"
  pgrep -af "run.py" | while IFS= read -r l; do say "   $l"; done
  pkill -f "run.py bench"     2>/dev/null
  pkill -f "run.py validate"  2>/dev/null
  pkill -f "run.py check"     2>/dev/null
  sleep 2
  pkill -9 -f "run.py"        2>/dev/null
  sleep 1
  say "stopped."
else
  say "no campaign was running."
fi
pkill -f "snn_run.sh" 2>/dev/null
say ""

# --- 2. set aside any partial database ------------------------------------
DB="$PROJ/results/benchmarks.db"
if [ -f "$DB" ]; then
  TS=$(date +%Y%m%d_%H%M%S)
  mv "$DB" "$PROJ/results/benchmarks_aborted_$TS.db" 2>/dev/null \
    && say "moved the partial database aside: benchmarks_aborted_$TS.db" \
    || say "could not move the partial database aside"
  say "(so the real campaign starts from an empty database, with no rows"
  say " measured under a different set of package versions)"
else
  say "no database written yet - nothing to set aside."
fi
rm -f "$OUT/FINISHED.txt" 2>/dev/null
say ""

# --- 3. find every interpreter -------------------------------------------
say "searching for python interpreters ..."
RAW=$(
  { find "$HOME" -maxdepth 7 -path '*/bin/python3*' -type f 2>/dev/null
    find /opt /usr/local -maxdepth 6 -path '*/bin/python3*' -type f 2>/dev/null
    ls -1 /usr/bin/python3* 2>/dev/null
  } | grep -v -- '-config$' | grep -v '/pkgs/'
)
# de-duplicate by the file each one really resolves to
LIST=$(
  for p in $RAW; do
    [ -x "$p" ] || continue
    rp=$(readlink -f "$p" 2>/dev/null) || rp="$p"
    printf '%s\t%s\n' "$rp" "$p"
  done | sort -u -k1,1 | cut -f2
)
N=$(printf '%s\n' "$LIST" | grep -c . )
say "$N distinct interpreters found."
say ""

MODS="numpy scipy brian2 nest nengo snntorch spikingjelly psutil"

probe_mod() {
  "$1" - "$2" <<'PY' 2>/dev/null
import sys, importlib
m = sys.argv[1]
try:
    mod = importlib.import_module(m)
    v = getattr(mod, "__version__", None) or getattr(mod, "version", None) or "present"
    if m == "nest":
        v = getattr(mod, "__version__", None) or "present"
    print(str(v).strip().splitlines()[-1] if str(v).strip() else "present")
except ModuleNotFoundError:
    print("-"); sys.exit(3)
except Exception as e:
    print("ERR:%s" % type(e).__name__); sys.exit(4)
PY
}

say "TARGET (what the existing results were measured with):"
say "  numpy 2.4.6 | scipy 1.17.1 | brian2 2.9.0 | nest 3.10.0 | nengo 4.1.0 | snntorch 1.0.0 | spikingjelly present"
say ""
printf '%-72s %-9s %-8s %-8s %-8s %-8s %-8s %-8s %-8s %-8s\n' \
  "interpreter" "python" $MODS >> "$REPORT"
say "$(printf '%.0s-' $(seq 1 150))"

for py in $LIST; do
  pv=$("$py" -c "import sys;print(sys.version.split()[0])" 2>/dev/null) || pv="?"
  row=$(printf '%-72s %-9s' "$py" "$pv")
  sims=0
  for m in $MODS; do
    out=$(probe_mod "$py" "$m" | tail -1)
    [ -n "$out" ] || out="?"
    case "$m" in
      brian2|nest|nengo|snntorch|spikingjelly)
        case "$out" in -|ERR:*|"?") ;; *) sims=$((sims+1));; esac ;;
    esac
    row="$row $(printf '%-8.8s' "$out")"
  done
  say "$row   [$sims/5 sims]"
done

say ""
say "=== end of inventory - nothing was launched ==="
say ""
say "Report written to:"
say "  $REPORT"
sleep 5
