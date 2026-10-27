"""NEST.

Thread count is exposed as the backend axis, because single-threaded NEST and
multi-threaded NEST are not the same system and the difference is measurable.

NEST has no CUDA backend on any hardware from any vendor. Its kernel is CPU,
OpenMP and MPI only. The separate nest-gpu project is a different simulator with
its own model library, so substituting it and labelling the row NEST would
report a cross-simulator comparison as a device comparison.
"""
from __future__ import annotations
import os
import numpy as np
import snnbench.config as C
from snnbench.adapters.base import Adapter, Backend, Unsupported, TrainingIncomplete


def _thread_options():
    cores = os.cpu_count() or 1
    opts = [1]
    for t in (2, 4, 8):
        if t <= cores and t not in opts:
            opts.append(t)
    if cores not in opts:
        opts.append(cores)
    return opts[:3]


class NestAdapter(Adapter):
    key = "nest"
    label = "NEST"
    caveat = ("iaf_psc_delta with C_m = 1 pF, so a delta post-synaptic current of "
              "weight w produces a membrane jump of w mV and the normalised "
              "threshold of 1.0 maps directly onto 1.0 mV.")

    def probe(self):
        try:
            import nest
            v = getattr(nest, "__version__", None) or str(nest.version())
            return True, str(v)
        except Exception as e:
            return False, f"import failed: {e}"

    def backends(self):
        import os
        if os.environ.get("SNNBENCH_NEST_DEBUG"):
            print("[nest debug] backends(): probing", flush=True)
        ok, _ = self.probe()
        if not ok:
            return []
        opts = _thread_options()
        if os.environ.get("SNNBENCH_NEST_DEBUG"):
            print(f"[nest debug] backends(): thread options = {opts}", flush=True)
        return [Backend(f"threads{t}", f"NEST / {t} thread{'s' if t > 1 else ''}")
                for t in opts]

    _setup_calls = 0

    def setup(self, n, backend):
        import os
        NestAdapter._setup_calls += 1
        _call_no = NestAdapter._setup_calls
        _dbg = bool(os.environ.get("SNNBENCH_NEST_DEBUG"))
        def _d(msg):
            if _dbg:
                print(f"[nest debug] call#{_call_no} {msg}", flush=True)
        _d("import nest")
        import nest
        _d(f"imported, version={getattr(nest, '__version__', '?')}")
        threads = int(backend.replace("threads", ""))
        _d(f"n={n} threads={threads}")
        nest.set_verbosity("M_ERROR")
        _d("set_verbosity done")
        nest.ResetKernel()
        _d("ResetKernel done")
        nest.SetKernelStatus(dict(resolution=C.DT_MS,
                                  local_num_threads=threads,
                                  rng_seed=C.SEED,
                                  print_time=False))
        _d("SetKernelStatus done")
        pg = nest.Create("poisson_generator", n, params={"rate": C.INPUT_RATE_HZ})
        _d("Create poisson_generator done")
        par = nest.Create("parrot_neuron", n)     # turns the generator into spikes
        _d("Create parrot_neuron done")
        neurons = nest.Create("iaf_psc_delta", n, params={
            "C_m": 1.0, "tau_m": C.TAU_MS, "t_ref": 0.0,
            "E_L": 0.0, "V_reset": C.V_RESET, "V_th": C.V_THRESH,
            "V_m": 0.0, "I_e": 0.0, "V_min": -1e6})
        _d("Create iaf_psc_delta done")
        nest.Connect(pg, par, "one_to_one")
        _d("Connect pg->par done")
        nest.Connect(par, neurons,
                     conn_spec={"rule": "fixed_indegree", "indegree": C.FANIN,
                                "allow_autapses": False, "allow_multapses": False},
                     syn_spec={"weight": C.SYN_WEIGHT, "delay": C.DT_MS})
        _d("Connect par->neurons done")
        rec = nest.Create("spike_recorder")
        _d("Create spike_recorder done")
        nest.Connect(neurons, rec)
        _d("Connect neurons->rec done, setup complete")
        return dict(nest=nest, rec=rec)

    def simulate(self, h) -> int:
        nest = h["nest"]
        nest.Simulate(C.SIM_MS)
        return int(nest.GetStatus(h["rec"], "n_events")[0])

    def teardown(self, h):
        # setup() already calls nest.ResetKernel() as its first action, so a
        # second reset here was pure redundancy — and a plausible source of
        # the intermittent native crash this adapter was hitting partway
        # through the warmup/measured loop (ResetKernel called twice back to
        # back, every single cycle, for hundreds of cycles across sizes and
        # thread counts). Nothing needs cleaning up between setup() calls
        # that the next setup()'s own reset does not already handle, so this
        # is now a no-op rather than a second, unnecessary kernel reset.
        #
        # The debug counter showed the crash surviving several full cycles
        # before dying (e.g. call #4 of 10) rather than failing on the first
        # one, which points at accumulating unreleased state rather than a
        # one-shot bug. An explicit gc.collect() here gives Python a chance
        # to drop its last references to the previous cycle's NEST handle
        # objects (node/connection wrappers) before the next setup() call
        # allocates a fresh batch, rather than leaving that to whenever the
        # interpreter next happens to collect on its own.
        import gc
        gc.collect()

    # -- Experiment 2 ------------------------------------------------------
    def supports_training(self) -> bool:
        return True

    def train(self, hidden, train_n, test_n, epochs, backend):
        """Spike-timing-dependent plasticity through NEST's stdp_synapse, with
        the same neuron-labelling readout used for Brian2 so that the two
        plasticity-based simulators are compared on equal terms."""
        import time, nest
        from snnbench.mnist import load_mnist
        threads = int(backend.replace("threads", ""))
        (xtr, ytr), (xte, yte) = load_mnist(train_n, test_n)

        nest.set_verbosity("M_ERROR")
        nest.ResetKernel()
        nest.SetKernelStatus(dict(resolution=C.TRAIN_DT_MS,
                                  local_num_threads=threads,
                                  rng_seed=C.SEED, print_time=False))
        # Input is delivered by spike_generator rather than poisson_generator.
        # A device's parameters cannot be changed inside a Prepare/Run context:
        # nest.SetStatus on a poisson_generator there is silently ignored, the
        # rates stay at zero, and the network records no spikes at all. Loading
        # precomputed spike times instead lets a whole pass run under one
        # Prepare/Run, and matches the other adapters, which also generate their
        # Poisson input with NumPy before the timed region.
        pg = nest.Create("spike_generator", C.MNIST_INPUTS)
        par = nest.Create("parrot_neuron", C.MNIST_INPUTS)
        neurons = nest.Create("iaf_psc_delta", hidden, params={
            "C_m": 1.0, "tau_m": C.TAU_MS, "t_ref": 0.0, "E_L": 0.0,
            "V_reset": 0.0, "V_th": 1.0, "V_m": 0.0, "V_min": -1e6})
        nest.Connect(pg, par, "one_to_one")
        # weight=0.05 with dense 784-input all-to-all connectivity and no
        # homeostasis drove every neuron to fire on nearly every timestep
        # (measured 22 spikes/neuron/sample against a 25-step window), found
        # while attempting a full-size run: not a performance bug, a network
        # that was never stable. w0 is calibrated empirically to a firing
        # regime that is active but not saturated at chunk = 20 samples, and
        # is kept stable at larger sample counts by synaptic scaling, applied
        # after every chunk in present_many: each neuron's incoming weight
        # vector is rescaled to a constant sum, the standard STDP homeostasis
        # mechanism (used, for instance, in Diehl and Cook 2015), so
        # potentiation cannot run away as more samples are presented.
        w0 = 0.006
        nest.Connect(par, neurons, "all_to_all", syn_spec={
            "synapse_model": "stdp_synapse", "weight": w0,
            "delay": C.TRAIN_DT_MS, "Wmax": w0 * 20})
        rec = nest.Create("spike_recorder")
        nest.Connect(neurons, rec)
        target_sum = w0 * C.MNIST_INPUTS
        conns = nest.GetConnections(par, neurons)
        post_of = np.array(nest.GetStatus(conns, "target"))
        plastic = [True]   # normalise only while STDP is still updating weights

        first_gid = neurons[0].global_id
        sim_ms = C.TRAIN_SIM_MS
        res = C.TRAIN_DT_MS
        n_steps = int(round(sim_ms / res))
        rng = np.random.default_rng(C.SEED)

        def load_pass(xs, t_start):
            """Fill every input generator with the Poisson train for a whole
            pass, so the pass costs one Prepare/Run instead of one per sample."""
            n = len(xs)
            # p[sample, step, input] -> spike times on the shared grid
            probs = np.repeat(xs[:, None, :] * C.INPUT_RATE_HZ * (res / 1000.0),
                              n_steps, axis=1)
            fired = rng.random(probs.shape) < probs
            k, st, j = np.nonzero(fired)
            times = t_start + k * sim_ms + (st + 1) * res
            order = np.argsort(j, kind="stable")
            j, times = j[order], times[order]
            bounds = np.searchsorted(j, np.arange(C.MNIST_INPUTS + 1))
            nest.SetStatus(pg, [
                {"spike_times": np.round(times[bounds[i]:bounds[i + 1]], 3)}
                for i in range(C.MNIST_INPUTS)])
            return n * sim_ms

        def present_many(xs):
            """Run one pass and return an [len(xs), hidden] spike count matrix."""
            # Cleared before every call, not just once per epoch. Left
            # accumulating, the recorder's event buffer grows with every
            # sample presented in the process's lifetime, and each call reads
            # and filters that whole buffer, so the cost of chunk k is O(k):
            # a process making many small chunks pays the same quadratic
            # penalty that nest.Simulate() paid before the earlier fix, just
            # moved one level up.
            rec.n_events = 0
            t0 = nest.biological_time
            dur = load_pass(xs, t0)
            nest.Prepare()
            try:
                nest.Run(dur)
            finally:
                nest.Cleanup()
            if plastic[0]:
                w = np.array(nest.GetStatus(conns, "weight"))
                for nid in np.unique(post_of):
                    m = post_of == nid
                    s_ = w[m].sum()
                    if s_ > 0:
                        w[m] *= target_sum / s_
                nest.SetStatus(conns, [{"weight": float(x)} for x in w])
            ev = nest.GetStatus(rec, "events")[0]
            sen, tim = ev["senders"], ev["times"]
            keep = tim > t0
            sen, tim = sen[keep], tim[keep]
            out = np.zeros((len(xs), hidden), dtype=np.int64)
            if sen.size:
                k = np.floor((tim - t0) / sim_ms).astype(np.int64)
                j = (sen - first_gid).astype(np.int64)
                ok = (k >= 0) & (k < len(xs)) & (j >= 0) & (j < hidden)
                np.add.at(out, (k[ok], j[ok]), 1)
            return out

        # Checkpointed training, chunked by sample sub-batch. A full-size run
        # takes far longer than one process lives here, so progress is saved
        # to disk and resumed, the same pattern used for snnTorch. NEST's
        # learned state is the synaptic weight vector, saved and restored
        # explicitly; connection order from an identical deterministic build
        # is stable across a fresh kernel, so reapplying weights by position
        # is safe. Per-epoch timing accumulates actual chunk-processing time
        # from time.perf_counter() deltas taken inside each chunk, so a
        # resumed epoch's reported duration is real compute time and does not
        # include the gaps between separate process runs.
        import os, pickle, pathlib as _pl
        ckpt_path = _pl.Path(os.environ.get("SNNBENCH_TRAIN_CKPT", "")
                             or (C.RESULTS_DIR / f"ckpt_nest_{backend}.pkl"))
        deadline = float(os.environ.get("SNNBENCH_TRAIN_DEADLINE", "inf"))
        chunk = int(os.environ.get("SNNBENCH_TRAIN_CHUNK", "500"))

        # Utilisation and peak memory accumulate over exactly the region
        # whose duration becomes the per-epoch figure, and travel in the
        # checkpoint. This process is a disposable worker (nest_train_worker),
        # so the totals must survive the handover between workers; the parent
        # never observes this work itself.
        from snnbench.profiler import RegionClock, reset_peak_rss, peak_rss_mb
        clk, peak0 = RegionClock(), 0.0
        phase, idx = "epochs", 0
        per_epoch, epoch_elapsed = [], 0.0
        counts = np.zeros((hidden, C.MNIST_CLASSES))
        labels, test_correct = None, 0
        if ckpt_path.exists():
            with open(ckpt_path, "rb") as f:
                st = pickle.load(f)
            if (st.get("hidden"), st.get("train_n"), st.get("test_n"),
                    st.get("epochs")) == (hidden, train_n, test_n, epochs):
                nest.SetStatus(conns, [{"weight": w} for w in st["weights"]])
                phase, idx = st["phase"], st["idx"]
                per_epoch, epoch_elapsed = st["per_epoch"], st["epoch_elapsed"]
                counts, labels = st["counts"], st.get("labels")
                test_correct = st.get("test_correct", 0)
                clk = RegionClock(st.get("clk_wall", 0.0), st.get("clk_cpu", 0.0))
                peak0 = st.get("peak_mb", 0.0)
        reset_peak_rss()

        def save(**extra):
            d = dict(hidden=hidden, train_n=train_n, test_n=test_n,
                    epochs=epochs, phase=phase, idx=idx,
                    per_epoch=per_epoch, epoch_elapsed=epoch_elapsed,
                    counts=counts, labels=labels, test_correct=test_correct,
                    weights=np.array(nest.GetStatus(conns, "weight")),
                    clk_wall=clk.wall_s, clk_cpu=clk.cpu_s,
                    peak_mb=max(peak0, peak_rss_mb() or 0.0))
            d.update(extra)
            with open(ckpt_path, "wb") as f:
                pickle.dump(d, f)

        def run_chunked(xs, on_result, resume_idx, time_it=False):
            """Present xs[resume_idx:] in sub-batches, calling on_result(i, row)
            per sample. Returns (next_idx_or_None, seconds_spent_this_call)."""
            nonlocal epoch_elapsed
            i, spent = resume_idx, 0.0
            while i < len(xs):
                j = min(i + chunk, len(xs))
                if time_it:
                    clk.start()
                t0 = time.perf_counter()
                rows = present_many(xs[i:j])
                spent += time.perf_counter() - t0
                for off, row in enumerate(rows):
                    on_result(i + off, row)
                i = j
                if time_it:
                    epoch_elapsed += time.perf_counter() - t0
                    clk.stop()
                if time.time() > deadline and i < len(xs):
                    return i, spent
            return None, spent

        if phase == "epochs":
            while len(per_epoch) < epochs:
                remain, _ = run_chunked(xtr, lambda i, row: None, idx,
                                        time_it=True)
                if remain is not None:
                    idx = remain
                    save()
                    raise TrainingIncomplete(
                        f"epoch {len(per_epoch) + 1}/{epochs}, sample "
                        f"{remain}/{train_n}; checkpoint saved to "
                        f"{ckpt_path.name}, rerun to continue")
                per_epoch.append(epoch_elapsed)
                epoch_elapsed = 0.0
                idx = 0
            phase, idx = "train_readout", 0
            save()

        if phase == "train_readout":
            plastic[0] = False
            nest.SetStatus(conns, [{"lambda": 0.0}
                                   for _ in nest.GetStatus(conns, "weight")])

            def acc_train(i, row):
                counts[:, int(ytr[i])] += row
            remain, _ = run_chunked(xtr, acc_train, idx)
            if remain is not None:
                idx = remain
                save()
                raise TrainingIncomplete(
                    f"train readout, sample {remain}/{train_n}; checkpoint "
                    f"saved to {ckpt_path.name}, rerun to continue")
            labels = counts.argmax(axis=1)
            phase, idx = "test_readout", 0
            save()

        if phase == "test_readout":
            def acc_test(i, fired):
                nonlocal test_correct
                if fired.sum() == 0:
                    return
                votes = np.zeros(C.MNIST_CLASSES)
                np.add.at(votes, labels, fired)
                if votes.argmax() == int(yte[i]):
                    test_correct += 1
            remain, _ = run_chunked(xte, acc_test, idx)
            if remain is not None:
                idx = remain
                save()
                raise TrainingIncomplete(
                    f"test readout, sample {remain}/{test_n}; checkpoint "
                    f"saved to {ckpt_path.name}, rerun to continue")

        if ckpt_path.exists():
            ckpt_path.unlink()
        self.last_train_metrics = dict(cpu_s=clk.cpu_s, wall_s=clk.wall_s,
                                       cpu_pct=clk.pct(),
                                       peak_rss_mb=max(peak0, peak_rss_mb() or 0.0))
        acc = 100.0 * test_correct / max(len(yte), 1)
        note = ("STDP via nest stdp_synapse with neuron-labelling readout, "
                "trained with nest.Prepare/Run rather than repeated "
                "nest.Simulate(), checkpointed across process restarts so a "
                "full-size run can span multiple invocations.")
        mean_epoch = float(np.mean(per_epoch)) if per_epoch else float("nan")
        return mean_epoch, acc, note
