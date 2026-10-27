"""SpikingJelly.

Added in the August 2026 revision so that the comparison covers six simulators
rather than four. SpikingJelly is the machine-learning-oriented simulator most
frequently cited alongside snnTorch, and including it tests whether the
snnTorch result generalises to the PyTorch-based class or is specific to one
library.

CPU only, and the multi-step mode is used because that is the configuration the
simulator is optimised for.
"""
from __future__ import annotations
import math
import numpy as np
import snnbench.config as C
from snnbench.adapters.base import Adapter, Backend, TrainingIncomplete


class SpikingJellyAdapter(Adapter):
    key = "spikingjelly"
    label = "SpikingJelly"
    caveat = ("Discrete-time tensor recurrence like snnTorch. Multi-step mode "
              "with the torch backend, which fuses the timestep loop.")

    def probe(self):
        try:
            import spikingjelly, torch
            from spikingjelly.activation_based import neuron  # noqa: F401
            v = getattr(spikingjelly, "__version__", "present")
            return True, f"{v} (torch {torch.__version__})"
        except Exception as e:
            return False, f"import failed: {e}"

    def backends(self):
        ok, _ = self.probe()
        return [Backend("cpu", "SpikingJelly / CPU tensors")] if ok else []

    def setup(self, n, backend):
        import torch
        from spikingjelly.activation_based import neuron, functional
        torch.manual_seed(C.SEED)
        rng = np.random.default_rng(C.SEED)
        steps = int(round(C.SIM_MS / C.DT_MS))
        dt = C.DT_MS / 1000.0
        p_spike = C.INPUT_RATE_HZ * dt

        train = torch.from_numpy(
            (rng.random((steps, n)) < p_spike).astype(np.float32))
        W = np.zeros((n, n), dtype=np.float32)
        for j in range(n):
            W[j, rng.choice(n, size=C.FANIN, replace=False)] = C.SYN_WEIGHT
        Wt = torch.from_numpy(W).T.contiguous()

        # SpikingJelly parameterises the leak as tau in timesteps, and by
        # default also divides the input current by tau. The shared
        # specification is v <- alpha*v + w*s with alpha = exp(-dt/tau) and the
        # input added undivided, so decay_input is turned off and tau is set to
        # the value that makes SpikingJelly's (1 - 1/tau) leak equal alpha.
        # Passing tau in timesteps with decay_input left on scales the drive
        # down by a factor of 100 and the neurons never reach threshold.
        alpha = math.exp(-C.DT_MS / C.TAU_MS)
        tau_steps = 1.0 / (1.0 - alpha)
        lif = neuron.LIFNode(tau=tau_steps, decay_input=False,
                             v_threshold=C.V_THRESH,
                             v_reset=C.V_RESET, step_mode="m", backend="torch")
        return dict(torch=torch, functional=functional, train=train,
                    W=Wt, lif=lif, steps=steps)

    def simulate(self, h) -> int:
        torch = h["torch"]
        h["functional"].reset_net(h["lif"])
        with torch.no_grad():
            drive = h["train"] @ h["W"]
            out = h["lif"](drive)
        return int(out.sum().item())

    def teardown(self, h):
        try:
            h["functional"].reset_net(h["lif"])
        except Exception:
            pass

    # -- Experiment 2 ------------------------------------------------------
    def supports_training(self) -> bool:
        return True

    def train(self, hidden, train_n, test_n, epochs, backend):
        """Surrogate-gradient backpropagation through time with Adam, rate-coded
        Poisson input over a fixed presentation window and a spike-count
        readout. Identical procedure to snnTorch, so the two PyTorch-based
        simulators are compared on equal terms, not just on identical
        inference: the network shape, learning rule, input coding, optimiser,
        and loss are all the same, and only the neuron implementation
        (SpikingJelly's LIFNode vs snnTorch's Leaky) differs."""
        import time, torch, torch.nn as nn
        from spikingjelly.activation_based import neuron, surrogate as sj_surrogate, functional
        from snnbench.mnist import load_mnist
        torch.manual_seed(C.SEED)
        (xtr, ytr), (xte, yte) = load_mnist(train_n, test_n)
        steps = int(round(C.TRAIN_SIM_MS / C.TRAIN_DT_MS))
        # Single-step mode here, not the multi-step mode used for inference:
        # a manual per-timestep loop is needed anyway for the rate-coded
        # Poisson draw, which redraws every step, so multi-step's advantage
        # (processing the whole time axis as one tensor op) is not available.
        alpha = math.exp(-C.TRAIN_DT_MS / C.TAU_MS)
        tau_steps = 1.0 / (1.0 - alpha)

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = nn.Linear(C.MNIST_INPUTS, hidden)
                self.lif1 = neuron.LIFNode(
                    tau=tau_steps, decay_input=False, v_threshold=1.0,
                    v_reset=0.0, step_mode="s",
                    surrogate_function=sj_surrogate.ATan())
                self.fc2 = nn.Linear(hidden, C.MNIST_CLASSES)
                self.lif2 = neuron.LIFNode(
                    tau=tau_steps, decay_input=False, v_threshold=1.0,
                    v_reset=0.0, step_mode="s",
                    surrogate_function=sj_surrogate.ATan())

            def forward(self, x):
                functional.reset_net(self)
                out = 0
                for _ in range(steps):
                    inp = (torch.rand_like(x) < x).float()   # rate coding
                    s1 = self.lif1(self.fc1(inp))
                    s2 = self.lif2(self.fc2(s1))
                    out = out + s2
                return out

        net = Net()
        opt = torch.optim.Adam(net.parameters(), lr=1e-3)
        lossfn = nn.CrossEntropyLoss()
        Xtr = torch.from_numpy(xtr.astype(np.float32))
        Ytr = torch.from_numpy(ytr.astype(np.int64))
        Xte = torch.from_numpy(xte.astype(np.float32))
        Yte = torch.from_numpy(yte.astype(np.int64))
        bs = 64

        # Checkpointed training. A full-size run (train_n in the tens of
        # thousands) takes longer than one process is given to run in this
        # setup, so training state is saved to disk and resumed rather than
        # restarted, exactly like resuming a long job after a machine reboot.
        # SNNBENCH_TRAIN_DEADLINE is a Unix timestamp; past it, the current
        # batch finishes, state is saved, and a Resume signal is raised instead
        # of a result, so nothing incomplete is ever written to the database.
        import os, pickle, pathlib as _pl
        ckpt_path = _pl.Path(os.environ.get("SNNBENCH_TRAIN_CKPT", "")
                             or (C.RESULTS_DIR / "ckpt_spikingjelly.pkl"))
        deadline = float(os.environ.get("SNNBENCH_TRAIN_DEADLINE", "inf"))

        # Utilisation and peak memory accumulate over exactly the region
        # whose duration becomes the per-epoch figure, and travel in the
        # checkpoint, so a run split across several processes reports the sum
        # of its own compute rather than one chunk of it.
        from snnbench.profiler import RegionClock, reset_peak_rss, peak_rss_mb
        clk, peak0 = RegionClock(), 0.0
        start_epoch, start_batch, per_epoch = 0, 0, []
        if ckpt_path.exists():
            with open(ckpt_path, "rb") as f:
                st = pickle.load(f)
            if (st.get("hidden"), st.get("train_n"), st.get("test_n"),
                    st.get("epochs")) == (hidden, train_n, test_n, epochs):
                net.load_state_dict(st["model"])
                opt.load_state_dict(st["opt"])
                start_epoch, start_batch = st["epoch"], st["batch"]
                per_epoch = st["per_epoch"]
                clk = RegionClock(st.get("clk_wall", 0.0), st.get("clk_cpu", 0.0))
                peak0 = st.get("peak_mb", 0.0)
                torch.set_rng_state(st["rng"])

        class Resume(Exception):
            pass

        reset_peak_rss()
        try:
            for ep in range(start_epoch, epochs):
                clk.start()
                t0 = time.perf_counter()
                torch.manual_seed(C.SEED + ep)
                perm = torch.randperm(len(Xtr))
                b0 = start_batch if ep == start_epoch else 0
                start_batch = 0
                for i in range(b0 * bs, len(Xtr), bs):
                    idx = perm[i:i + bs]
                    opt.zero_grad()
                    loss = lossfn(net(Xtr[idx]), Ytr[idx])
                    loss.backward()
                    opt.step()
                    if time.time() > deadline:
                        raise Resume(ep, i // bs + 1, per_epoch,
                                    time.perf_counter() - t0)
                clk.stop()
                per_epoch.append(time.perf_counter() - t0)
        except Resume as r:
            ep, batch, done_epochs, partial = r.args
            with open(ckpt_path, "wb") as f:
                pickle.dump(dict(hidden=hidden, train_n=train_n, test_n=test_n,
                                 epochs=epochs, epoch=ep, batch=batch,
                                 per_epoch=done_epochs, model=net.state_dict(),
                                 opt=opt.state_dict(), rng=torch.get_rng_state(),
                                 clk_wall=clk.wall_s, clk_cpu=clk.cpu_s,
                                 peak_mb=max(peak0, peak_rss_mb() or 0.0)),
                           f)
            n_batches = (len(Xtr) + bs - 1) // bs
            raise TrainingIncomplete(
                f"epoch {ep + 1}/{epochs}, batch {batch}/{n_batches} "
                f"({partial:.0f}s into this epoch); checkpoint saved to "
                f"{ckpt_path.name}, rerun to continue")

        if ckpt_path.exists():
            ckpt_path.unlink()

        with torch.no_grad():
            pred = torch.cat([net(Xte[i:i + 256]).argmax(1)
                              for i in range(0, len(Xte), 256)])
        self.last_train_metrics = dict(cpu_s=clk.cpu_s, wall_s=clk.wall_s,
                                       cpu_pct=clk.pct(),
                                       peak_rss_mb=max(peak0, peak_rss_mb() or 0.0))
        acc = 100.0 * float((pred == Yte).float().mean())
        note = ("Surrogate-gradient BPTT (ATan surrogate), Adam, rate-coded Poisson "
                "input over a 25 ms window, spike-count readout as logits, "
                "identical procedure to snnTorch.")
        return float(np.mean(per_epoch)), acc, note
