# Full-Scale SNN Simulator Comparison — Experiment 2 at the literal Chapter 3 spec

This is a dedicated copy of the benchmarking project, made so the full-scale
training run (60,000 training images, 10,000 test images, 10 epochs,
hidden=500 — exactly what Chapter 3 specifies) can be executed without
touching the original project, its results database, or any file already
used to produce the thesis and dashboard.

Nothing here overwrites anything in `SNN Benchmark Dashboard/`. This folder
is self-contained: its own `snnbench/` package, its own `results/` folder
(seeded with the cached MNIST dataset so nothing needs to be re-downloaded),
and its own database, written fresh when the run starts.

Terminology: "simulator" is used throughout in place of "framework" in all
comments, docstrings, and printed output, since that is the comparison this
thesis makes. Internal plumbing that has to match the existing database
schema and code contract (the `framework` column/keyword used when storing
a result) was left as-is on purpose, so results written here stay
structurally compatible with the existing analysis and dashboard code —
only what a person actually reads was renamed.

## Running the full experiment

From this folder, in the same Python environment you've used for every
previous run (the one with brian2 / nest / nengo / snntorch / spikingjelly
importable):

```
python run.py bench --tasks training --preset full
```

This runs all six simulators (Brian2, NEST, Nengo, snnTorch, SpikingJelly,
and the NumPy reference control) sequentially, training each at the literal
spec, with no size or epoch reduction. Results land in `results/benchmarks.db`
in this folder — a brand-new database, not the one the thesis currently
cites.

Expect this to take a long time — plausibly the better part of a day for
the slower simulators. Run it in the background so it survives a closed
terminal:

```
nohup python run.py bench --tasks training --preset full > full_run.log 2>&1 &
disown
```

Check progress any time with `tail -f full_run.log`.

## After it finishes

Send the updated thesis author (or just say so in the next session) and the
real numbers — including for whichever simulators still don't converge at
this scale, which is itself the honest finding — get folded into Chapter 3/4
and the dashboard.
