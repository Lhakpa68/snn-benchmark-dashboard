"""A direct NumPy implementation of the same specification.

This is not a simulator. It is a control condition, and it serves two purposes.

First, it gives the comparison a floor. Every simulator provides abstraction,
and abstraction costs something; without a direct implementation of the same
computation there is nothing to measure that cost against. Reporting that a
simulator is 30 times slower than a hand-written loop is a different and more
useful statement than reporting that it is twice as slow as another simulator.

Second, it always runs. The suite therefore has at least one working backend on
any machine with NumPy, so the pipeline can be validated end to end before the
simulators are installed.
"""
from __future__ import annotations
import numpy as np
import snnbench.config as C
from snnbench.adapters.base import Adapter, Backend


class ReferenceAdapter(Adapter):
    key = "reference"
    label = "NumPy reference"
    caveat = ("Direct implementation of the shared specification with no "
              "simulator. Included as a control condition establishing the floor "
              "cost of the computation, not as a simulator under test.")

    def probe(self):
        return True, f"numpy {np.__version__}"

    def backends(self):
        return [Backend("vectorised", "NumPy reference / vectorised"),
                Backend("scalar", "NumPy reference / scalar loop",
                        note="per-neuron Python loop; shows the cost of "
                             "implementation style within one language")]

    def setup(self, n, backend):
        rng = np.random.default_rng(C.SEED)
        steps = int(round(C.SIM_MS / C.DT_MS))
        p = C.INPUT_RATE_HZ * (C.DT_MS / 1000.0)
        pre = np.stack([rng.choice(n, size=C.FANIN, replace=False)
                        for _ in range(n)])
        train = rng.random((steps, n)) < p
        return dict(n=n, steps=steps, pre=pre, train=train, backend=backend,
                    alpha=float(np.exp(-C.DT_MS / C.TAU_MS)))

    def simulate(self, h) -> int:
        if h["backend"] == "scalar":
            return self._scalar(h)
        v = np.zeros(h["n"])
        total = 0
        alpha, pre = h["alpha"], h["pre"]
        for t in range(h["steps"]):
            s = h["train"][t]
            v = alpha * v + C.SYN_WEIGHT * s[pre].sum(axis=1)
            fired = v >= C.V_THRESH
            total += int(fired.sum())
            v[fired] = C.V_RESET
        return total

    @staticmethod
    def _scalar(h) -> int:
        """The same computation written as an explicit per-neuron loop.

        Included because the gap between this and the vectorised version is the
        cost of implementation style inside one language, which sets a scale
        against which the gaps between simulators can be read.
        """
        n, alpha, pre, train = h["n"], h["alpha"], h["pre"], h["train"]
        v = [0.0] * n
        total = 0
        for t in range(h["steps"]):
            s = train[t]
            for j in range(n):
                drive = 0.0
                for k in pre[j]:
                    if s[k]:
                        drive += C.SYN_WEIGHT
                v[j] = alpha * v[j] + drive
                if v[j] >= C.V_THRESH:
                    total += 1
                    v[j] = C.V_RESET
        return total
