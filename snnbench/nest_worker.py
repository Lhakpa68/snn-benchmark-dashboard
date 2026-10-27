"""Disposable subprocess worker for one stretch of NEST warmup/measured cycles.

Why this exists: on this machine, NEST 3.10.0 crashes the whole process with
a native abort inside nest.ResetKernel() — confirmed with Python's own
faulthandler, which caught a real C-level signal, not a Python exception —
after a small, consistent number of ResetKernel() calls. That kind of crash
cannot be caught from inside the process it happens in; try/except around it
in runner.py does nothing, because there is no Python exception to catch.

The fix applied here does not depend on knowing *why* NEST crashes. Each
condition's ten-cycle warmup+measured protocol is run by a worker process
started fresh for the job. If it dies partway, whatever cycles it completed
before dying were already printed to stdout, so the caller
(snnbench.runner._measure_condition_nest_subprocess) just starts a new worker
for whatever is left. Every individual measured sample's timing is captured
entirely inside one live, already-running worker — process start-up is never
inside a timed region — so this changes nothing about what gets measured,
only how many worker processes it took to gather all of it.

Usage:
    python -m snnbench.nest_worker <backend> <n> <warmup_remaining> <measured_remaining>

Stdout, one line per completed step (flushed immediately, so a crash after
line k still leaves lines 1..k readable by the parent):
    WARMUP <index>
    MEASURED <json: {"setup": {...RunSample fields...}, "sim": {...}}>
"""
from __future__ import annotations
import json
import sys


def main():
    backend, n, warmup_n, measured_n = (
        sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))

    from snnbench.adapters.nest_adapter import NestAdapter
    from snnbench.profiler import measure

    ad = NestAdapter()
    handle = {"h": None}

    def do_setup():
        handle["h"] = ad.setup(n, backend)
        return 0

    def do_sim():
        return ad.simulate(handle["h"])

    for i in range(warmup_n):
        do_setup()
        do_sim()
        ad.teardown(handle["h"])
        print(f"WARMUP {i}", flush=True)

    for i in range(measured_n):
        su = measure(do_setup)
        si = measure(do_sim)
        ad.teardown(handle["h"])
        print("MEASURED " + json.dumps({"setup": su.__dict__, "sim": si.__dict__}),
              flush=True)


if __name__ == "__main__":
    main()
