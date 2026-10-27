#!/usr/bin/env bash
# Phase runner for the complete CCR-specification campaign.
# Invoked detached by run_full_ccr_campaign.sh, which exports the settings.
# Kept as its own file deliberately: an eleven-day run should not depend on
# quoting inside a nested bash -c string.
set -u

: "${PY:?}"; : "${PROJ:?}"; : "${DB:?}"; : "${OUT:?}"
: "${LOG_WIN:?}"; : "${LOG:?}"; : "${HIDDEN:?}"; : "${TRAIN_N:?}"

cd "$PROJ" || exit 1

# How long one Brian2 chunk runs before it checkpoints and exits.
CHUNK="${CHUNK_SECONDS:-1800}"

# Has this framework/backend already been trained at the full specification?
trained() {
  [ -f "$DB" ] || return 1
  local n
  n=$("$PY" - "$DB" "$1" "$2" "$HIDDEN" "$TRAIN_N" <<'PYX' 2>/dev/null
import sqlite3, sys
db, fw, be, hid, tn = sys.argv[1:6]
try:
    c = sqlite3.connect(db)
    q = ("SELECT COUNT(*) FROM conditions WHERE task='training' AND framework=? "
         "AND backend=? AND notes LIKE ? AND notes LIKE ?")
    print(c.execute(q, (fw, be, f"%hidden={hid};%", f"%train_n={tn};%")).fetchone()[0])
except Exception:
    print(0)
PYX
)
  [ "${n:-0}" -gt 0 ]
}

# Has the inference/scalability sweep already covered every backend?
swept() {
  [ -f "$DB" ] || return 1
  local n
  n=$("$PY" - "$DB" <<'PYX' 2>/dev/null
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1])
    print(c.execute("SELECT COUNT(DISTINCT framework||'/'||backend) FROM conditions "
                    "WHERE task='scalability'").fetchone()[0])
except Exception:
    print(0)
PYX
)
  [ "${n:-0}" -ge 11 ]
}

# Brian2 in chunks, so a reboot costs one chunk instead of the whole run.
#
# The Brian2 adapter only writes its checkpoint when it is given a deadline:
#   deadline = float(os.environ.get("SNNBENCH_TRAIN_DEADLINE", "inf"))
# With no deadline that comparison is never true, save() is never reached, and
# the whole run lives or dies with one process. On 15 Sep the machine restarted
# itself 26.25 h into Brian2/NumPy and every hour of it was lost, because
# nothing had been written to disk. Setting an absolute deadline per invocation
# makes the adapter checkpoint and raise TrainingIncomplete, which runner.py
# already treats as progress rather than failure, so the next invocation
# resumes where the last one stopped.
#
# This does NOT change the measurement. The adapter accumulates per-sample
# compute time (epoch_elapsed += dt around each present() call) and carries it
# inside the checkpoint, so the reported s/epoch is summed compute time, not
# wall clock, and excludes the per-chunk process startup. That is the same
# property that makes the chunked NEST rows valid.
brian2_chunked() {
  local fw="$1" be="$2"; shift 2
  local attempt=0 max=4000 fast=0 t0 t1
  while [ "$attempt" -lt "$max" ]; do
    attempt=$((attempt + 1))
    t0=$(date +%s)
    SNNBENCH_TRAIN_DEADLINE=$(( t0 + CHUNK )) "$PY" run.py bench "$@"
    t1=$(date +%s)
    if trained "$fw" "$be"; then
      echo "    [chunked] finished after $attempt chunk(s) of ${CHUNK}s"
      return 0
    fi
    # A chunk returning almost immediately without progress means the run is
    # failing, not working. Spinning on that for hours would fill the log and
    # bury the real error, so stop after a few in a row.
    if [ $(( t1 - t0 )) -lt 60 ]; then
      fast=$(( fast + 1 ))
      if [ "$fast" -ge 5 ]; then
        echo "    [chunked] ABORTING: five consecutive chunks returned in under a"
        echo "    minute without recording a row. That is a failure, not slow"
        echo "    progress - see the error above."
        return 1
      fi
    else
      fast=0
    fi
    sleep 2
  done
  echo "    [chunked] GAVE UP after $max chunks of ${CHUNK}s"
  return 1
}

phase() {           # phase <label> <framework|-> <backend|-> <run.py args...>
  local label="$1" fw="$2" be="$3"; shift 3
  echo
  echo "################ $label"
  if [ "$fw" = "-" ]; then
    if swept; then echo "already complete in the database - skipping"; return 0; fi
  else
    if trained "$fw" "$be"; then echo "already complete in the database - skipping"; return 0; fi
  fi
  echo "started $(date -Is)"
  if [ "$fw" = "brian2" ]; then
    brian2_chunked "$fw" "$be" "$@"
  else
    "$PY" run.py bench "$@"
  fi
  echo "ended   $(date -Is)"
}

H="--hidden $HIDDEN"

phase "PHASE 1/8  inference + scalability, all 11 backends" - - \
      --tasks inference,scalability
phase "PHASE 2/8  training: Nengo"                nengo        reference \
      --tasks training $H --only nengo
phase "PHASE 2/8  training: snnTorch"             snntorch     cpu \
      --tasks training $H --only snntorch
phase "PHASE 2/8  training: SpikingJelly"         spikingjelly cpu \
      --tasks training $H --only spikingjelly
phase "PHASE 3/8  training: NEST / 4 threads"     nest         threads4 \
      --tasks training $H --only nest --backends threads4
phase "PHASE 4/8  training: NEST / 2 threads"     nest         threads2 \
      --tasks training $H --only nest --backends threads2
phase "PHASE 5/8  training: NEST / 1 thread"      nest         threads1 \
      --tasks training $H --only nest --backends threads1
phase "PHASE 6/8  training: Brian2 / Cython"      brian2       cython \
      --tasks training $H --only brian2 --backends cython
phase "PHASE 7/8  training: Brian2 / NumPy"       brian2       numpy \
      --tasks training $H --only brian2 --backends numpy
phase "PHASE 8/8  training: Brian2 / C++ standalone" brian2    cpp_standalone \
      --tasks training $H --only brian2 --backends cpp_standalone

echo
echo "################ equivalence validation"
"$PY" run.py validate > "$PROJ/results/validate.txt" 2>&1
cat "$PROJ/results/validate.txt"

echo
echo "################ CAMPAIGN COMPLETE"
echo "finished $(date -Is)"
cp -f "$DB"                          "$OUT/benchmarks.db"  2>/dev/null
cp -f "$PROJ/results/validate.txt"   "$OUT/validate.txt"   2>/dev/null
cp -f "$PROJ/results/conditions.csv" "$OUT/conditions.csv" 2>/dev/null
cp -f "$PROJ/results/runs.csv"       "$OUT/runs.csv"       2>/dev/null
cp -f "$LOG" "$LOG_WIN" 2>/dev/null
echo done > "$OUT/FINISHED.txt"
