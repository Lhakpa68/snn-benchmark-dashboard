"""The experiment runner.

Three experiments, CPU only:

  1  inference   one forward simulation at N = 100, setup and simulation timed
                 separately
  2  training    supervised MNIST, each simulator using its own native rule
  3  scalability the same network across five sizes

Protocol: WARMUP_RUNS discarded, then MEASURED_RUNS kept, every individual run
stored. A backend that cannot run is recorded as an explicit skip with a reason
and writes no numeric row.
"""
from __future__ import annotations
import sys, time, traceback, uuid
import snnbench.config as C
from snnbench import machine, store, eflop as eflop_mod
from snnbench.profiler import measure
from snnbench.registry import ADAPTERS, COMPILE_DOMINATED
from snnbench.adapters.base import TrainingIncomplete


def _log(msg):
    print(msg, flush=True)


def _measure_condition(ad, backend_key, n, warmup, measured):
    """Time setup and simulation separately across the protocol."""
    setup_samples, sim_samples = [], []
    handle = {"h": None}

    def do_setup():
        handle["h"] = ad.setup(n, backend_key)
        return 0

    def do_sim():
        return ad.simulate(handle["h"])

    for _ in range(warmup):
        do_setup(); do_sim(); ad.teardown(handle["h"])
    for _ in range(measured):
        setup_samples.append(measure(do_setup))
        sim_samples.append(measure(do_sim))
        ad.teardown(handle["h"])
    return setup_samples, sim_samples


def _measure_condition_nest_subprocess(backend_key, n, warmup, measured, timeout=180):
    """Resilient replacement for _measure_condition, used only for NEST.

    NEST 3.10.0 crashes this process outright — a native abort inside
    nest.ResetKernel(), confirmed with faulthandler, not a catchable Python
    exception — after a small, consistent number of ResetKernel() calls in
    this environment. See snnbench/nest_worker.py for the full account and
    the fix: each condition's warmup/measured cycles run in a disposable
    subprocess; if it dies partway, a fresh one picks up whatever cycles are
    still needed. Every individual measured sample is still timed entirely
    inside one live worker process, so this changes nothing about what is
    measured — only how many worker processes it took to gather it all."""
    import json, subprocess, sys
    setup_samples, sim_samples = [], []
    warmup_done = 0
    attempts = 0
    max_attempts = warmup + measured + 10   # generous ceiling; see the raise below
    while (warmup_done < warmup or len(setup_samples) < measured) and attempts < max_attempts:
        attempts += 1
        w_remain = warmup - warmup_done
        m_remain = measured - len(setup_samples)
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "snnbench.nest_worker", backend_key, str(n),
                 str(w_remain), str(m_remain)],
                capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            _log(f"    [nest worker timed out after {timeout}s on n={n} "
                 f"{backend_key}; retrying]")
            continue
        for line in proc.stdout.splitlines():
            if line.startswith("WARMUP"):
                warmup_done += 1
            elif line.startswith("MEASURED "):
                payload = json.loads(line[len("MEASURED "):])
                from snnbench.profiler import RunSample
                setup_samples.append(RunSample(**payload["setup"]))
                sim_samples.append(RunSample(**payload["sim"]))
        if proc.returncode != 0:
            _log(f"    [nest worker died (exit {proc.returncode}) on n={n} "
                 f"{backend_key}: {warmup_done}/{warmup} warmup, "
                 f"{len(setup_samples)}/{measured} measured so far; retrying "
                 f"with a fresh worker for what's left]")
    if warmup_done < warmup or len(setup_samples) < measured:
        raise RuntimeError(
            f"NEST subprocess isolation could not complete the protocol for "
            f"n={n} {backend_key} after {attempts} worker attempts "
            f"({warmup_done}/{warmup} warmup, {len(setup_samples)}/{measured} "
            f"measured) — giving up")
    return setup_samples, sim_samples


def _train_nest_subprocess(backend_key, hidden, train_n, test_n, epochs,
                            chunk_seconds=300, timeout=900, max_attempts=1000):
    """Resilient replacement for ad.train(), used only for NEST.

    Each attempt runs in its own fresh subprocess (see
    snnbench/nest_train_worker.py), so nest.ResetKernel() is always that
    process's first and only call -- inside the safe zone the deterministic
    native-abort crash needs several more calls than that to reach. Every
    attempt is also given a near wall-clock deadline (chunk_seconds), so it
    checkpoints and exits cleanly on its own well before the subprocess
    timeout, whether or not anything actually goes wrong; a crashed attempt
    still leaves the checkpoint from its last completed chunk on disk (see
    nest_adapter.train()'s own save()), so the next attempt just picks up
    from there -- at most one chunk of work is ever repeated.

    The ceiling on total work is max_attempts * chunk_seconds, because an
    attempt that runs cleanly still ends at its deadline. The original
    200 x 60 s allowed 3.33 h, which comfortably covered the 6,000-image
    campaign (about 9 chunks at four threads) but silently caps the full
    60,000-image configuration. Derived from the measured full-budget runs,
    counting the labelling and test passes as well as the ten epochs, the
    work comes to about 233 chunks at four threads, 430 at two and 820 at
    one. In the log the cap stopped threads4 during the labelling pass,
    after all ten epochs had completed, and stopped threads1 as well; each
    time it reported a failure that reads like a NEST defect but is entirely
    an artefact of this limit. Raised to 1000 x 300 s, an 83 h ceiling.
    (An earlier version of this comment gave 218, 380 and 680 chunks and
    "about 20" for the small campaign; those were estimates, not
    measurements, and have been replaced.)
    The longer chunk also cuts process-spawn and nest-import
    overhead roughly fivefold without weakening the crash isolation, since
    each attempt still makes exactly one ResetKernel() call whatever its
    duration; the subprocess timeout is raised in step so a full-length
    chunk cannot race it."""
    import json, subprocess, sys, time
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        deadline = time.time() + chunk_seconds
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "snnbench.nest_train_worker", backend_key,
                 str(hidden), str(train_n), str(test_n), str(epochs),
                 str(deadline)],
                capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            _log(f"    [nest train worker timed out after {timeout}s "
                 f"{backend_key}; retrying]")
            continue
        lines = proc.stdout.splitlines()
        done = next((l for l in lines if l.startswith("DONE ")), None)
        incomplete = next((l for l in lines if l.startswith("INCOMPLETE ")), None)
        if done:
            payload = json.loads(done[len("DONE "):])
            return (payload["mean_epoch_s"], payload["accuracy_pct"],
                    payload["note"], payload.get("metrics"))
        if incomplete:
            _log(f"    [nest train] {incomplete[len('INCOMPLETE '):]}")
            continue
        _log(f"    [nest train worker died (exit {proc.returncode}) "
             f"{backend_key}; retrying from last checkpoint]")
    raise RuntimeError(
        f"NEST subprocess isolation could not complete training for "
        f"{backend_key} after {attempts} worker attempts -- giving up")


def run(tasks=("inference", "scalability", "training"), sizes=None,
        warmup=None, measured=None, train_preset=None, train_override=None, only=None,
        only_backends=None,
        db_path=None):
    sizes = sizes or C.SIZES
    warmup = C.WARMUP_RUNS if warmup is None else warmup
    measured = C.MEASURED_RUNS if measured is None else measured
    train_preset = train_preset or C.DEFAULT_TRAIN_PRESET

    mach = machine.profile()
    pkgs = machine.versions()
    group = f"{mach['fingerprint']}-{uuid.uuid4().hex[:6]}"
    con = store.connect(db_path)
    store.write_meta(con, group, mach, pkgs)

    _log(f"\nmachine : {mach['machine_id']}")
    _log(f"group   : {group}")
    _log(f"protocol: warmup {warmup}, measured {measured}, sizes {sizes}\n")

    skipped = []
    for key, ad in ADAPTERS.items():
        if only and key not in only:
            continue
        ok, info = ad.probe()
        if not ok:
            _log(f"[skip] {ad.label}: {info}")
            skipped.append((key, None, info))
            continue
        _log(f"=== {ad.label} ({info}) ===")

        for be in ad.backends():
            # Backend filter, so a single slow backend (Brian2's
            # cpp_standalone recompiles on every invocation) can be measured on
            # its own without re-measuring and duplicating its siblings.
            if only_backends and be.key not in only_backends:
                continue
            if not be.available:
                _log(f"  [skip] {be.label}: {be.reason}")
                skipped.append((key, be.key, be.reason))
                continue
            cd = (key, be.key) in COMPILE_DOMINATED

            # --- Experiments 1 and 3 ------------------------------------
            plan = []
            if "inference" in tasks:
                plan.append(("inference", [C.SIZES[0]]))
            if "scalability" in tasks:
                plan.append(("scalability", sizes))
            for task, ns in plan:
                for n in ns:
                    t0 = time.perf_counter()
                    try:
                        if key == "nest":
                            su, si = _measure_condition_nest_subprocess(
                                be.key, n, warmup, measured)
                        else:
                            su, si = _measure_condition(ad, be.key, n, warmup, measured)
                    except Exception as e:
                        _log(f"  [fail] {be.label} {task} N={n}: {type(e).__name__}: {e}")
                        skipped.append((key, be.key, f"{task} N={n}: {e}"))
                        continue
                    out_spikes = int(si[0].spikes)
                    ef = eflop_mod.eflop(n, eflop_mod.expected_input_spikes(n))
                    for phase, samples in (("setup", su), ("simulate", si)):
                        store.record_condition(
                            con, run_group=group, machine_id=mach["machine_id"],
                            framework=key, backend=be.key, task=task,
                            network_size=n, phase=phase, samples=samples,
                            eflop=ef["eflop"] if phase == "simulate" else None,
                            compile_dominated=cd, framework_version=info,
                            notes=ad.caveat + (f" {be.note}" if be.note else ""))
                    med = sorted(s.runtime_s for s in si)[len(si) // 2]
                    _log(f"  {be.label:<28} {task:<12} N={n:<6} "
                         f"sim {med*1000:8.2f} ms   spikes {out_spikes:<7} "
                         f"({time.perf_counter()-t0:.1f}s)")

            # --- Experiment 2 -------------------------------------------
            if "training" in tasks and ad.supports_training():
                p = dict(C.TRAIN_PRESETS[train_preset])
                if train_override:
                    p.update(train_override)
                _log(f"  {be.label}: training [{train_preset}] "
                     f"hidden={p['hidden']} train={p['train_n']} epochs={p['epochs']} ...")
                try:
                    t0 = time.perf_counter()
                    if key == "nest":
                        sec, acc, note, tmetrics = _train_nest_subprocess(
                            be.key, p["hidden"], p["train_n"], p["test_n"],
                            p["epochs"])
                    else:
                        ad.last_train_metrics = None
                        sec, acc, note = ad.train(p["hidden"], p["train_n"],
                                                  p["test_n"], p["epochs"], be.key)
                        tmetrics = getattr(ad, "last_train_metrics", None)
                    from snnbench.profiler import RunSample
                    # Utilisation and peak memory for training come from the
                    # adapter, which accumulates them over exactly the region
                    # whose duration it reports as the per-epoch figure, and
                    # carries them through its checkpoints. For NEST they come
                    # back from the disposable worker, which is the only
                    # process that ever runs that training.
                    #
                    # Before 21 Sep 2026 this path observed neither quantity.
                    # Utilisation was written as the constant 100.0 and memory
                    # as 0.0 -- values indistinguishable in the database from
                    # measurements -- until 20 Sep, when both were replaced by
                    # None, an honest absence. They are now measured. Where an
                    # adapter still reports nothing, None is stored: a quantity
                    # that was not measured must never be stored as though it
                    # had been.
                    cpu_pct = tmetrics.get("cpu_pct") if tmetrics else None
                    peak_mb = tmetrics.get("peak_rss_mb") if tmetrics else None
                    sample = RunSample(runtime_s=sec, peak_rss_mb=peak_mb,
                                       rss_delta_mb=None, mean_cpu_pct=cpu_pct,
                                       n_cpu_samples=0, spikes=0)
                    store.record_condition(
                        con, run_group=group, machine_id=mach["machine_id"],
                        framework=key, backend=be.key, task="training",
                        network_size=p["hidden"], phase="train",
                        samples=[sample], accuracy=acc,
                        framework_version=info,
                        notes=(f"preset={train_preset}; hidden={p['hidden']}; "
                               f"train_n={p['train_n']}; test_n={p['test_n']}; "
                               f"epochs={p['epochs']}; "
                               + (f"util_cpu_s={tmetrics['cpu_s']:.1f}; "
                                  f"util_wall_s={tmetrics['wall_s']:.1f}; "
                                  if tmetrics else "util=not measured; ")
                               + note))
                    _log(f"    -> {sec:.2f} s/epoch, {acc:.2f}% accuracy, "
                         f"{'%.1f%% CPU' % cpu_pct if cpu_pct is not None else 'CPU n/a'}, "
                         f"{'%.0f MB peak' % peak_mb if peak_mb is not None else 'mem n/a'} "
                         f"({time.perf_counter()-t0:.0f}s total)")
                except TrainingIncomplete as e:
                    # Not a failure: state was checkpointed. Nothing is written
                    # to the database and no skip is recorded, so the next
                    # identical bench invocation resumes and eventually
                    # completes rather than being counted as a dead backend.
                    _log(f"    [in progress] {e}")
                except Exception as e:
                    _log(f"    [fail] training: {type(e).__name__}: {e}")
                    skipped.append((key, be.key, f"training: {e}"))

    _log("\n--- export ---")
    store.export_csv(con)
    n_runs = con.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    n_cond = con.execute("SELECT COUNT(*) FROM conditions").fetchone()[0]
    _log(f"\n{n_runs} individual runs, {n_cond} conditions stored in {C.DB_PATH}")
    if skipped:
        _log("\nSkipped or failed, with reasons:")
        for f, b, r in skipped:
            _log(f"  {f}/{b or '-'}: {r}")
    con.close()
    return group
