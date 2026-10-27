"""Disposable subprocess worker for one NEST train() attempt.

Same rationale as nest_worker.py: NEST 3.10.0 crashes the process with an
uncatchable native abort inside nest.ResetKernel(), after a small, consistent
number of ResetKernel() calls within one process. nest_adapter.py's train()
already has its own checkpoint/resume protocol (TrainingIncomplete, a pickle
file on disk, and an optional wall-clock deadline that makes it save and
return early instead of running the whole multi-minute job in one call) --
built so an ordinary restart could resume training. That same mechanism is
reused here for a different purpose: a single call to train() only ever
calls nest.ResetKernel() once, right at the top, so running each attempt in
a fresh subprocess keeps that count at 1 in every attempt -- always inside
the safe zone -- no matter how many attempts a full training run ends up
needing, and no matter which attempt (if any) hits the native abort.

Usage:
    python -m snnbench.nest_train_worker <backend> <hidden> <train_n> <test_n> <epochs> <deadline_epoch_s>

Stdout, flushed immediately:
    INCOMPLETE <message>          -- checkpoint saved to disk, rerun to continue
    DONE <json: {"mean_epoch_s": ..., "accuracy_pct": ..., "note": ...}>

A crash (native abort) prints neither line; the caller
(snnbench.runner._train_nest_subprocess) treats that as "retry" too, and the
retry picks up from whatever chunk train()'s own checkpoint last saved.
"""
from __future__ import annotations
import json
import os
import sys


def main():
    backend = sys.argv[1]
    hidden, train_n, test_n, epochs = (
        int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
    deadline = sys.argv[6]
    os.environ["SNNBENCH_TRAIN_DEADLINE"] = deadline

    from snnbench.adapters.base import TrainingIncomplete
    from snnbench.adapters.nest_adapter import NestAdapter

    ad = NestAdapter()
    try:
        mean_epoch, acc, note = ad.train(hidden, train_n, test_n, epochs, backend)
    except TrainingIncomplete as e:
        print(f"INCOMPLETE {e}", flush=True)
        return
    # The parent process never runs this training, so it cannot observe its
    # utilisation or its peak memory. The worker measured both itself; they
    # travel back with the result.
    print("DONE " + json.dumps({"mean_epoch_s": mean_epoch,
                                 "accuracy_pct": acc, "note": note,
                                 "metrics": getattr(ad, "last_train_metrics", None)}),
          flush=True)


if __name__ == "__main__":
    main()
