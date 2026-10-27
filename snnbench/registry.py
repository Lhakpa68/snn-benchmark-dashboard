"""Adapter registry and the equivalence-validation suite."""
from __future__ import annotations
import numpy as np
import snnbench.config as C
from snnbench.adapters.base import Adapter, Backend, Unsupported

from snnbench.adapters.brian2_adapter import Brian2Adapter
from snnbench.adapters.nest_adapter import NestAdapter
from snnbench.adapters.nengo_adapter import NengoAdapter
from snnbench.adapters.snntorch_adapter import SnnTorchAdapter
from snnbench.adapters.spikingjelly_adapter import SpikingJellyAdapter
from snnbench.adapters.reference_adapter import ReferenceAdapter

# Norse was dropped from the registry: it never imported in any measurement
# environment this project used, produced zero rows across every campaign,
# and is not part of the thesis's reported comparison. Re-add it here (and to
# dashboard_theme.py's FRAMEWORK_COLORS/FRAMEWORK_LABELS) only alongside a
# real, working install and a fresh campaign that actually measures it.
ADAPTERS: dict[str, Adapter] = {
    a.key: a for a in (
        Brian2Adapter(), NestAdapter(), NengoAdapter(),
        SnnTorchAdapter(), SpikingJellyAdapter(),
        ReferenceAdapter(),
    )
}

#: Backends whose measured interval is dominated by something other than the
#: simulation. Recorded on the row so the analysis can exclude them on stated
#: grounds rather than by hand.
COMPILE_DOMINATED = {("brian2", "cpp_standalone")}


def inventory() -> list[dict]:
    rows = []
    for key, ad in ADAPTERS.items():
        ok, info = ad.probe()
        bes = ad.backends() if ok else []
        rows.append(dict(framework=key, label=ad.label, importable=ok,
                         version_or_reason=info,
                         backends=[dict(key=b.key, label=b.label,
                                        available=b.available, reason=b.reason,
                                        note=b.note) for b in bes]))
    return rows


# --- equivalence validation ------------------------------------------------
# Firing-rate agreement is a necessary condition for the four implementations to
# be computing the same function. It is not a sufficient one, and Section 4.15
# of the thesis says so: two simulators can match on rate while integrating
# different equations. It is the strongest check available without a third
# independent numerical implementation.

def reference_spike_count(n: int) -> int:
    """Plain-NumPy reference implementation of the same specification."""
    rng = np.random.default_rng(C.SEED)
    steps = int(round(C.SIM_MS / C.DT_MS))
    p = C.INPUT_RATE_HZ * (C.DT_MS / 1000.0)
    alpha = float(np.exp(-C.DT_MS / C.TAU_MS))
    pre = np.stack([rng.choice(n, size=C.FANIN, replace=False) for _ in range(n)])
    v = np.zeros(n)
    total = 0
    for _ in range(steps):
        s = rng.random(n) < p
        v = alpha * v + C.SYN_WEIGHT * s[pre].sum(axis=1)
        fired = v >= C.V_THRESH
        total += int(fired.sum())
        v[fired] = C.V_RESET
    return total


def validate(n: int = 500, tolerance: float = 0.35) -> list[dict]:
    """Run every available backend once and compare its output firing rate
    against the reference. Returns one record per backend."""
    ref = reference_spike_count(n)
    ref_rate = ref / n / (C.SIM_MS / 1000.0)
    out = []
    for key, ad in ADAPTERS.items():
        ok, info = ad.probe()
        if not ok:
            out.append(dict(framework=key, backend=None, status="not installed",
                            reason=info))
            continue
        for be in ad.backends():
            if not be.available:
                out.append(dict(framework=key, backend=be.key,
                                status="unavailable", reason=be.reason))
                continue
            try:
                h = ad.setup(n, be.key)
                spikes = ad.simulate(h)
                ad.teardown(h)
                rate = spikes / n / (C.SIM_MS / 1000.0)
                rel = abs(rate - ref_rate) / max(ref_rate, 1e-9)
                out.append(dict(framework=key, backend=be.key,
                                status="pass" if rel <= tolerance else "rate mismatch",
                                spikes=spikes, rate_hz=round(rate, 2),
                                ref_rate_hz=round(ref_rate, 2),
                                rel_diff=round(rel, 3)))
            except Exception as e:
                out.append(dict(framework=key, backend=be.key, status="error",
                                reason=f"{type(e).__name__}: {e}"))
    return out
