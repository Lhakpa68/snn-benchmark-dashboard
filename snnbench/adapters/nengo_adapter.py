"""Nengo.

Nengo's reference simulator is NumPy-based and has no GPU path of its own; the
GPU routes are the third-party nengo-dl and nengo-ocl projects, neither of which
is used here because this study is CPU only.

The benchmark network is built with direct neuron connections rather than
through the Neural Engineering Framework's decoded connections, so that Nengo
runs the same leaky integrate-and-fire computation as the other simulators
rather than a functionally equivalent but structurally different one. Nengo's
LIF neuron carries a refractory period parameter, which is set to zero to match
the shared specification.
"""
from __future__ import annotations
import numpy as np
import snnbench.config as C
from snnbench.adapters.base import Adapter, Backend, Unsupported


class NengoAdapter(Adapter):
    key = "nengo"
    label = "Nengo"
    caveat = ("Direct neuron-to-neuron connections rather than NEF decoded "
              "connections, so the computation matches the shared specification. "
              "Nengo's LIF uses a fixed voltage scale; gain and bias are set so "
              "that the threshold sits at the shared normalised value.")

    def probe(self):
        try:
            import nengo
            return True, nengo.__version__
        except Exception as e:
            return False, f"import failed: {e}"

    def backends(self):
        ok, _ = self.probe()
        return [Backend("reference", "Nengo / reference simulator")] if ok else []

    def setup(self, n, backend):
        import nengo
        from nengo.dists import Choice
        rng = np.random.default_rng(C.SEED)
        dt = C.DT_MS / 1000.0
        p_spike = C.INPUT_RATE_HZ * dt
        steps = int(round(C.SIM_MS / C.DT_MS))

        # Pre-generate the input spike train so the Poisson process is identical
        # in distribution to the other adapters and costs nothing at run time.
        train = (rng.random((steps, n)) < p_spike).astype(float)

        # fixed in-degree connectivity as a sparse-by-construction dense matrix
        W = np.zeros((n, n))
        for j in range(n):
            W[j, rng.choice(n, size=C.FANIN, replace=False)] = C.SYN_WEIGHT

        with nengo.Network(seed=C.SEED) as model:
            # Nengo calls a node at t = dt, 2*dt, ..., so the index has to be
            # shifted back by one for step k to see train[k], as in every other
            # adapter.
            src = nengo.Node(
                lambda t: train[min(max(int(round(t / dt)) - 1, 0), steps - 1)],
                size_out=n)
            # Nengo initialises membrane voltages from Uniform(0, 1) by default.
            # Every other simulator here starts every neuron at zero, and so
            # does the shared specification. Left at the default, Nengo begins
            # the run with a large fraction of its population already close to
            # threshold and fires about 37 per cent more spikes than the same
            # network in Brian2, NEST or snnTorch, which would be charged to
            # Nengo as a performance difference when it is an initial condition
            # difference. Pinning the initial voltage to zero makes the spike
            # count match the reference implementation exactly.
            ens = nengo.Ensemble(
                n_neurons=n, dimensions=1,
                neuron_type=nengo.LIF(tau_rc=C.TAU_MS / 1000.0, tau_ref=0.0,
                                      initial_state={"voltage": Choice([0.0])}),
                gain=np.ones(n), bias=np.zeros(n))
            # Nengo's LIF relaxes the membrane toward the input current
            # rather than adding it: v <- alpha*v + (1 - alpha)*J with
            # alpha = exp(-dt/tau_rc). The shared specification adds the
            # synaptic weight directly, so J must be scaled by 1/(1 - alpha)
            # for one presynaptic spike to move the membrane by exactly
            # SYN_WEIGHT. Dividing by dt instead overdrives the ensemble by two
            # orders of magnitude and saturates every neuron.
            one_minus_alpha = 1.0 - np.exp(-dt / (C.TAU_MS / 1000.0))
            nengo.Connection(src, ens.neurons, transform=W / one_minus_alpha,
                             synapse=None)
            probe = nengo.Probe(ens.neurons, "output")
        sim = nengo.Simulator(model, dt=dt, progress_bar=False)
        return dict(sim=sim, probe=probe, steps=steps, dt=dt)

    def simulate(self, h) -> int:
        h["sim"].run_steps(h["steps"], progress_bar=False)
        return int((h["sim"].data[h["probe"]] > 0).sum())

    def teardown(self, h):
        try:
            h["sim"].close()
        except Exception:
            pass

    # -- Experiment 2 ------------------------------------------------------
    def supports_training(self) -> bool:
        return True

    def train(self, hidden, train_n, test_n, epochs, backend):
        """Nengo learns by solving analytically for decoders rather than by
        iterating over epochs, so 'seconds per epoch' is reported as the cost of
        one full solve. This is stated on the row rather than silently reshaped
        into an epoch count that does not exist in the simulator."""
        import time, nengo
        from nengo.solvers import LstsqL2
        from snnbench.mnist import load_mnist
        (xtr, ytr), (xte, yte) = load_mnist(train_n, test_n)
        targets = np.eye(C.MNIST_CLASSES)[ytr.astype(int)]

        with nengo.Network(seed=C.SEED) as model:
            ens = nengo.Ensemble(n_neurons=hidden, dimensions=C.MNIST_INPUTS,
                                 neuron_type=nengo.LIF(tau_rc=C.TAU_MS / 1000.0))
        # Utilisation and peak memory over exactly the region whose duration
        # is reported as the per-epoch figure, so the energy proxy of
        # equation (3.8) is formed from two quantities measured over the same
        # interval. See docs/TRAINING_INSTRUMENTATION.md.
        from snnbench.profiler import RegionClock, reset_peak_rss, peak_rss_mb
        reset_peak_rss()
        clk = RegionClock()
        clk.start()
        t0 = time.perf_counter()
        with nengo.Simulator(model, progress_bar=False) as sim:
            _, acts = nengo.utils.ensemble.tuning_curves(ens, sim, inputs=xtr)
            dec, _ = LstsqL2(reg=0.05)(acts, targets, rng=np.random.RandomState(C.SEED))
            _, acts_te = nengo.utils.ensemble.tuning_curves(ens, sim, inputs=xte)
        elapsed = time.perf_counter() - t0
        clk.stop()
        self.last_train_metrics = dict(cpu_s=clk.cpu_s, wall_s=clk.wall_s,
                                       cpu_pct=clk.pct(),
                                       peak_rss_mb=peak_rss_mb())
        pred = (acts_te @ dec).argmax(axis=1)
        acc = 100.0 * float((pred == yte.astype(int)).mean())
        note = ("NEF decoder solving (LstsqL2), a single closed-form solve. "
                "'Epochs' does not apply natively to this simulator; the reported "
                "per-epoch figure is the cost of one complete solve.")
        return elapsed, acc, note
