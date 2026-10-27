#!/usr/bin/env bash
# Phase runner for the complete campaign of 21 September 2026.
#
# What makes this one different from campaign_phases.sh: the training path is
# now instrumented. Before 21 Sep, Experiment 2 recorded only a duration -
# processor utilisation, the energy proxy and peak memory were not observed at
# all, so the thesis had to declare them as a gap. Each adapter now accumulates
# CPU and wall time over exactly the region whose duration it reports as the
# per-epoch figure, and carries both through its checkpoints, so a run split
# across hundreds of chunks reports the sum of its own compute. NEST measures
# inside its disposable worker, the only process that ever runs that training,
# and sends the figures back with the result.
#
# Invoked detached by run_complete_campaign.sh, which exports the settings.
set -u

: "${PY:?}"; : "${PROJ:?}"; : "${DB:?}"; : "${OUT:?}"
: "${LOG_WIN:?}"; : "${LOG:?}"; : "${HIDDEN:?}"; : "${TRAIN_N:?}"

cd "$PROJ" || exit 1
CHUNK="${CHUNK_SECONDS:-1800}"

sql() {   # sql <query>
  "$PY" - "$DB" "$1" <<'PYX' 2>/dev/null
import sqlite3, sys
try:
    print(sqlite3.connect(sys.argv[1]).execute(sys.argv[2]).fetchone()[0])
except Exception:
    print(0)
PYX
}

# Has this simulator/backend been trained at this width and budget already?
trained() {       # trained <framework> <backend> <hidden> <train_n>
  [ -f "$DB" ] || return 1
  local n
  n=$("$PY" - "$DB" "$1" "$2" "$3" "$4" <<'PYX' 2>/dev/null
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

# How many separate inference+scalability sessions are recorded?
sessions() {
  [ -f "$DB" ] || { echo 0; return; }
  sql "SELECT COUNT(DISTINCT run_group) FROM conditions WHERE task='scalability'"
}

# Brian2 in chunks, so a reboot costs one chunk instead of the whole run.
# The adapter only writes its checkpoint when given a deadline, so each
# invocation gets an absolute one. This does not change the measurement: the
# adapter accumulates per-sample compute time AND per-sample CPU time inside
# the checkpoint, so both the reported s/epoch and the reported utilisation are
# summed compute, excluding the per-chunk process startup.
brian2_chunked() {
  local fw="$1" be="$2" hid="$3" tn="$4"; shift 4
  local attempt=0 max=8000 fast=0 t0 t1
  while [ "$attempt" -lt "$max" ]; do
    attempt=$((attempt + 1))
    t0=$(date +%s)
    SNNBENCH_TRAIN_DEADLINE=$(( t0 + CHUNK )) "$PY" run.py bench "$@"
    t1=$(date +%s)
    if trained "$fw" "$be" "$hid" "$tn"; then
      echo "    [chunked] finished after $attempt chunk(s) of ${CHUNK}s"
      return 0
    fi
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

train_phase() {   # train_phase <label> <fw> <be> <hidden> <train_n> <run.py args...>
  local label="$1" fw="$2" be="$3" hid="$4" tn="$5"; shift 5
  echo
  echo "################ $label"
  if trained "$fw" "$be" "$hid" "$tn"; then
    echo "already complete in the database - skipping"; return 0
  fi
  echo "started $(date -Is)"
  if [ "$fw" = "brian2" ]; then
    brian2_chunked "$fw" "$be" "$hid" "$tn" "$@"
  else
    "$PY" run.py bench "$@"
  fi
  echo "ended   $(date -Is)"
}

sweep_phase() {   # sweep_phase <label> <required_session_count>
  local label="$1" need="$2"
  echo
  echo "################ $label"
  if [ "$(sessions)" -ge "$need" ]; then
    echo "already complete in the database - skipping"; return 0
  fi
  echo "started $(date -Is)"
  "$PY" run.py bench --tasks inference,scalability
  echo "ended   $(date -Is)"
}

echo "=============================================================="
echo " COMPLETE CAMPAIGN - instrumented training"
echo " started $(date -Is)"
echo " database $DB"
echo "=============================================================="

# --- 0. the instrument must prove itself before anything is measured -------
echo
echo "################ PHASE 0  processor-clock self-test"
"$PY" tools/cpu_instrument_check.py 2>&1 | tee "$OUT/instrument_check.txt"
if ! grep -q "^SELFTEST PASS" "$OUT/instrument_check.txt"; then
  echo "ABORTING: the utilisation instrument did not pass its self-test."
  echo "Nothing was measured. See $OUT/instrument_check.txt"
  date -Is > "$OUT/FAILED.txt"
  exit 1
fi

# --- 1-2. inference + scalability, twice, for the within-campaign repeat ---
sweep_phase "PHASE 1  inference + scalability, all 11 backends (session A)" 1
sweep_phase "PHASE 2  inference + scalability, all 11 backends (session B, repeat)" 2

# --- 3. training at the Chapter 4 reporting budget, now instrumented -------
# A second, cheaper budget is measured as well as the full one. It gives the
# training ordering a repeat measurement, which the full budget cannot afford,
# and it is a cross-check on the utilisation figures: the same backend should
# report the same utilisation at both budgets even though the durations differ
# by an order of magnitude.
P="--preset paper"
train_phase "PHASE 3a training 6k/3ep: Nengo"        nengo        reference  256 6000 --tasks training $P --only nengo
train_phase "PHASE 3b training 6k/3ep: snnTorch"     snntorch     cpu        256 6000 --tasks training $P --only snntorch
train_phase "PHASE 3c training 6k/3ep: SpikingJelly" spikingjelly cpu        256 6000 --tasks training $P --only spikingjelly
train_phase "PHASE 3d training 6k/3ep: NEST/4"       nest         threads4   256 6000 --tasks training $P --only nest --backends threads4
train_phase "PHASE 3e training 6k/3ep: NEST/2"       nest         threads2   256 6000 --tasks training $P --only nest --backends threads2
train_phase "PHASE 3f training 6k/3ep: NEST/1"       nest         threads1   256 6000 --tasks training $P --only nest --backends threads1
train_phase "PHASE 3g training 6k/3ep: Brian2/Cython" brian2      cython     256 6000 --tasks training $P --only brian2 --backends cython
train_phase "PHASE 3h training 6k/3ep: Brian2/NumPy"  brian2      numpy      256 6000 --tasks training $P --only brian2 --backends numpy
train_phase "PHASE 3i training 6k/3ep: Brian2/C++"    brian2      cpp_standalone 256 6000 --tasks training $P --only brian2 --backends cpp_standalone

"$PY" run.py validate > "$OUT/validate.txt" 2>&1 || echo "(validate returned non-zero; see validate.txt)"
"$PY" run.py analyse  > "$OUT/analysis_after_phase3.txt" 2>&1 || true
cp -f "$DB" "$OUT/benchmarks.db" 2>/dev/null

# --- 4. training at the full specification budget, cheapest first ----------
# Ordered by measured cost so the fast simulators are on disk within a day and
# only Brian2 is still running at the end.
F="--preset full --hidden $HIDDEN"
train_phase "PHASE 4a training 60k/10ep: Nengo"        nengo        reference 256 60000 --tasks training $F --only nengo
train_phase "PHASE 4b training 60k/10ep: SpikingJelly" spikingjelly cpu       256 60000 --tasks training $F --only spikingjelly
train_phase "PHASE 4c training 60k/10ep: snnTorch"     snntorch     cpu       256 60000 --tasks training $F --only snntorch
train_phase "PHASE 4d training 60k/10ep: NEST/4"       nest         threads4  256 60000 --tasks training $F --only nest --backends threads4
train_phase "PHASE 4e training 60k/10ep: NEST/2"       nest         threads2  256 60000 --tasks training $F --only nest --backends threads2
train_phase "PHASE 4f training 60k/10ep: NEST/1"       nest         threads1  256 60000 --tasks training $F --only nest --backends threads1
train_phase "PHASE 4g training 60k/10ep: Brian2/Cython" brian2      cython    256 60000 --tasks training $F --only brian2 --backends cython
train_phase "PHASE 4h training 60k/10ep: Brian2/NumPy"  brian2      numpy     256 60000 --tasks training $F --only brian2 --backends numpy
train_phase "PHASE 4i training 60k/10ep: Brian2/C++"    brian2      cpp_standalone 256 60000 --tasks training $F --only brian2 --backends cpp_standalone

"$PY" run.py validate > "$OUT/validate.txt" 2>&1 || echo "(validate returned non-zero; see validate.txt)"
"$PY" run.py analyse  > "$OUT/analysis_256_complete.txt" 2>&1 || true
cp -f "$DB" "$OUT/benchmarks_256_complete.db" 2>/dev/null
cp -f "$DB" "$OUT/benchmarks.db" 2>/dev/null
date -Is > "$OUT/FINISHED_256.txt"
echo
echo "=============================================================="
echo " The hidden-256 campaign is COMPLETE. Everything the thesis"
echo " reports is now measured, including training utilisation,"
echo " energy and peak memory."
echo " finished $(date -Is)"
echo "=============================================================="

# --- 5. optional tail: the width the CCR proposed --------------------------
# Not needed for any claim the thesis makes at present - Section 3.7 declares
# the 256 width and its reasons. This runs only so that, if an examiner asks
# for the proposed 500, the answer is measured rather than argued. It can be
# stopped at any time without affecting anything above: create the file named
# below, or just close the window.
if [ -f "$OUT/SKIP_WIDTH_500.txt" ]; then
  echo
  echo "hidden-500 tail skipped ($OUT/SKIP_WIDTH_500.txt exists)."
  date -Is > "$OUT/FINISHED.txt"
  exit 0
fi
echo
echo "################ PHASE 5  optional: the CCR-proposed hidden 500"
echo "This is a bonus, not a requirement. Create"
echo "  $OUT/SKIP_WIDTH_500.txt"
echo "to stop after the current backend."
W="--preset full"
for spec in "nengo reference --only nengo" \
            "spikingjelly cpu --only spikingjelly" \
            "snntorch cpu --only snntorch" \
            "nest threads4 --only nest --backends threads4" \
            "nest threads2 --only nest --backends threads2" \
            "nest threads1 --only nest --backends threads1" \
            "brian2 cython --only brian2 --backends cython" \
            "brian2 numpy --only brian2 --backends numpy" \
            "brian2 cpp_standalone --only brian2 --backends cpp_standalone"; do
  [ -f "$OUT/SKIP_WIDTH_500.txt" ] && { echo "stopping the 500 tail on request"; break; }
  set -- $spec
  fw="$1"; be="$2"; shift 2
  train_phase "PHASE 5 training 60k/10ep hidden 500: $fw/$be" "$fw" "$be" 500 60000 \
              --tasks training $W "$@"
  cp -f "$DB" "$OUT/benchmarks.db" 2>/dev/null
done

"$PY" run.py validate > "$OUT/validate.txt" 2>&1 || true
"$PY" run.py analyse  > "$OUT/analysis_with_500.txt" 2>&1 || true
cp -f "$DB" "$OUT/benchmarks.db" 2>/dev/null
date -Is > "$OUT/FINISHED.txt"
echo "ALL PHASES COMPLETE $(date -Is)"
