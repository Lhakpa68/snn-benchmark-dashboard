"""Brian2.

Three code-generation targets are exposed as separate backends because they
differ by more than an order of magnitude on the same machine. Reporting Brian2
on one of them and calling the result "Brian2" is the flaw the backend axis
exists to prevent.

cpp_standalone is included as a capability result, not a timing result: it
regenerates and recompiles source on every invocation, so its measured interval
is dominated by an external compiler and no number of warm-up runs can exclude
that. The runner marks it compile_dominated so the analysis can exclude it on
stated grounds rather than by hand.
"""
from __future__ import annotations
import numpy as np
import snnbench.config as C
from snnbench.adapters.base import Adapter, Backend, Unsupported, TrainingIncomplete


class Brian2Adapter(Adapter):
    key = "brian2"
    label = "Brian2"
    caveat = ("Equation-level ODE integration (exact exponential Euler for the "
              "linear LIF equation). Fan-in built as explicit index arrays.")

    def probe(self):
        try:
            import brian2
            return True, brian2.__version__
        except Exception as e:
            return False, f"import failed: {e}"

    def backends(self):
        ok, _ = self.probe()
        if not ok:
            return []
        out = [Backend("numpy", "Brian2 / NumPy"),
               Backend("cython", "Brian2 / Cython")]
        # cpp_standalone needs a working C++ toolchain
        import shutil
        cxx = shutil.which("g++") or shutil.which("clang++")
        out.append(Backend(
            "cpp_standalone", "Brian2 / C++ standalone",
            available=bool(cxx),
            reason="" if cxx else "no C++ compiler on PATH",
            note="recompiles per invocation; wall-clock is compile-dominated"))
        return out

    def setup(self, n, backend):
        import brian2 as b2
        b2.prefs.codegen.target = "numpy" if backend == "cpp_standalone" else backend
        b2.seed(C.SEED)
        rng = np.random.default_rng(C.SEED)

        if backend == "cpp_standalone":
            b2.set_device("cpp_standalone", build_on_run=False, directory=None)
        else:
            b2.set_device("runtime")

        net_ns = {}
        tau = C.TAU_MS * b2.ms
        P = b2.PoissonGroup(n, rates=C.INPUT_RATE_HZ * b2.Hz)
        G = b2.NeuronGroup(
            n, "dv/dt = -v/tau : 1",
            threshold=f"v > {C.V_THRESH}", reset=f"v = {C.V_RESET}",
            method="exact", namespace={"tau": tau})
        G.v = C.V_RESET
        # fixed in-degree: each target draws FANIN distinct sources
        j = np.repeat(np.arange(n), C.FANIN)
        i = np.concatenate([rng.choice(n, size=C.FANIN, replace=False)
                            for _ in range(n)])
        S = b2.Synapses(P, G, on_pre=f"v_post += {C.SYN_WEIGHT}")
        S.connect(i=i, j=j)
        M = b2.SpikeMonitor(G, record=False)
        net = b2.Network(P, G, S, M)
        net_ns.update(net=net, monitor=M, b2=b2, backend=backend)
        return net_ns

    def simulate(self, h) -> int:
        b2 = h["b2"]
        h["net"].run(C.SIM_MS * b2.ms, report=None)
        if h["backend"] == "cpp_standalone":
            b2.device.build(directory=None, compile=True, run=True, debug=False)
        return int(h["monitor"].num_spikes)

    def teardown(self, h):
        try:
            h["b2"].device.reinit()
            h["b2"].set_device("runtime")
        except Exception:
            pass

    # -- Experiment 2 ------------------------------------------------------
    def supports_training(self) -> bool:
        return True

    def train(self, hidden, train_n, test_n, epochs, backend):
        """Unsupervised spike-timing-dependent plasticity with a neuron-labelling
        readout, the standard procedure for this class of simulator.

        Per-neuron spike counts come from SpikeMonitor.count, which Brian2
        maintains even with record=False, so no spike times are stored and the
        memory figure is not inflated by the monitor.
        """
        import time, brian2 as b2
        from snnbench.mnist import load_mnist
        b2.prefs.codegen.target = "numpy" if backend == "cpp_standalone" else backend
        b2.set_device("runtime")
        b2.seed(C.SEED)
        (xtr, ytr), (xte, yte) = load_mnist(train_n, test_n)

        tau = C.TAU_MS * b2.ms
        taupre = taupost = 20 * b2.ms
        gmax, dApre = 1.0, 0.01
        dApost = -dApre * 1.05

        P = b2.PoissonGroup(C.MNIST_INPUTS, rates=np.zeros(C.MNIST_INPUTS) * b2.Hz)
        G = b2.NeuronGroup(hidden, "dv/dt = -v/tau : 1",
                           threshold="v > 1.0", reset="v = 0", method="exact",
                           namespace={"tau": tau})
        S = b2.Synapses(
            P, G,
            """w : 1
               dApre/dt  = -Apre/taupre   : 1 (event-driven)
               dApost/dt = -Apost/taupost : 1 (event-driven)""",
            on_pre="""v_post += w
                      Apre += dApre
                      w = clip(w + Apost, 0, gmax)""",
            on_post="""Apost += dApost
                       w = clip(w + Apre, 0, gmax)""",
            namespace=dict(taupre=taupre, taupost=taupost,
                           dApre=dApre, dApost=dApost, gmax=gmax))
        S.connect()
        rng = np.random.default_rng(C.SEED)
        w0 = 0.02
        S.w = rng.uniform(0.0, w0, size=len(S.w))
        M = b2.SpikeMonitor(G, record=False)
        net = b2.Network(P, G, S, M)
        window = C.TRAIN_SIM_MS * b2.ms

        # Found while attempting a full-size run: with dense 784-input
        # all-to-all connectivity and no homeostasis, every synapse in this
        # network saturates to gmax within about five samples (measured: all
        # weights at 1.0, 60-80 spikes/neuron per 25 ms presentation), the
        # same instability found in NEST's version of this network and fixed
        # the same way, by synaptic scaling: after every sample, each neuron's
        # incoming weight vector is rescaled to a constant sum, so
        # potentiation cannot run away as more samples are presented.
        post_idx = np.array(S.j[:])
        target_sum = w0 * 0.5 * C.MNIST_INPUTS

        plastic = [True]   # normalise only while STDP is still updating weights

        def normalise():
            w = np.array(S.w[:])
            for nid in np.unique(post_idx):
                m = post_idx == nid
                s_ = w[m].sum()
                if s_ > 0:
                    w[m] *= target_sum / s_
            S.w = w

        def present(x):
            before = np.array(M.count, dtype=np.int64)
            P.rates = (x * C.INPUT_RATE_HZ) * b2.Hz
            net.run(window, report=None)
            if plastic[0]:
                normalise()
            return np.array(M.count, dtype=np.int64) - before

        # Checkpointed training, chunked by individual sample. A full-size
        # run takes far longer than one process lives here, so progress is
        # saved to disk and resumed, the same pattern used for snnTorch and
        # NEST. Brian2's learned state is the synaptic weight vector S.w,
        # saved and restored explicitly between processes.
        import os, pickle, pathlib as _pl
        ckpt_path = _pl.Path(os.environ.get("SNNBENCH_TRAIN_CKPT", "")
                             or (C.RESULTS_DIR / f"ckpt_brian2_{backend}.pkl"))
        deadline = float(os.environ.get("SNNBENCH_TRAIN_DEADLINE", "inf"))

        # Utilisation and peak memory accumulate over exactly the region
        # whose duration becomes the per-epoch figure, and travel in the
        # checkpoint, so a run split across many chunks reports the sum of its
        # own compute rather than one chunk of it.
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
                S.w = st["weights"]
                phase, idx = st["phase"], st["idx"]
                per_epoch, epoch_elapsed = st["per_epoch"], st["epoch_elapsed"]
                counts, labels = st["counts"], st.get("labels")
                test_correct = st.get("test_correct", 0)
                clk = RegionClock(st.get("clk_wall", 0.0), st.get("clk_cpu", 0.0))
                peak0 = st.get("peak_mb", 0.0)
        reset_peak_rss()

        def save():
            d = dict(hidden=hidden, train_n=train_n, test_n=test_n,
                    epochs=epochs, phase=phase, idx=idx,
                    per_epoch=per_epoch, epoch_elapsed=epoch_elapsed,
                    counts=counts, labels=labels, test_correct=test_correct,
                    weights=np.array(S.w),
                    clk_wall=clk.wall_s, clk_cpu=clk.cpu_s,
                    peak_mb=max(peak0, peak_rss_mb() or 0.0))
            with open(ckpt_path, "wb") as f:
                pickle.dump(d, f)

        def run_chunked(xs, on_result, resume_idx, time_it=False):
            nonlocal epoch_elapsed
            i = resume_idx
            while i < len(xs):
                if time_it:
                    clk.start()
                t0 = time.perf_counter()
                row = present(xs[i])
                dt = time.perf_counter() - t0
                if time_it:
                    clk.stop()
                on_result(i, row)
                if time_it:
                    epoch_elapsed += dt
                i += 1
                if time.time() > deadline and i < len(xs):
                    return i
            return None

        if phase == "epochs":
            while len(per_epoch) < epochs:
                remain = run_chunked(xtr, lambda i, row: None, idx, time_it=True)
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
            plastic[0] = False
            S.namespace["dApre"] = 0.0
            S.namespace["dApost"] = 0.0
            save()

        if phase == "train_readout":
            def acc_train(i, row):
                counts[:, int(ytr[i])] += row
            remain = run_chunked(xtr, acc_train, idx)
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
            remain = run_chunked(xte, acc_test, idx)
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
        note = ("Unsupervised STDP, neuron-labelling readout, spike-count "
                "vote, checkpointed across process restarts so a full-size "
                "run can span multiple invocations.")
        mean_epoch = float(np.mean(per_epoch)) if per_epoch else float("nan")
        return mean_epoch, acc, note
