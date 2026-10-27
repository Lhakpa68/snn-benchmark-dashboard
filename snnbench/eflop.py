"""Effective operation counts for the benchmark model.

EFLOP (Narduzzi et al., 2025) counts only operations performed on non-zero
operands, so it is a property of the model and its activity rather than of the
simulator running it. That is what makes it usable as an external reference for
the runtime-based energy proxy, and it is also why it cannot discriminate
between simulators: all of them run the same specification and therefore have
the same operation count at a given size.

The synaptic term uses the expected input-spike count, which is determined by
the model rather than by any simulator: N independent Poisson sources at a fixed
rate over a fixed interval. The output spike count IS measured, by every
adapter, and is used for the equivalence check in registry.validate rather than
for the operation count. Reporting both keeps the distinction visible.
"""
from __future__ import annotations
import snnbench.config as C


def eflop(n: int, input_spikes: int) -> dict:
    steps = int(round(C.SIM_MS / C.DT_MS))
    syn = input_spikes * C.FANIN     # one accumulate per delivered spike
    mem = n * steps                  # one MAC per neuron per step for the leak
    return dict(syn_ops=syn, mem_ops=mem, eflop=syn + mem, steps=steps)


def expected_input_spikes(n: int) -> int:
    """Expected number of input spikes: N Poisson sources at the configured rate
    over the simulated interval. Used where an adapter reports only output
    spikes, and reported as an expectation rather than a measurement."""
    return int(round(n * C.INPUT_RATE_HZ * (C.SIM_MS / 1000.0)))
