# The complete campaign — 21 September 2026

This records what was left unmeasured after the 20 September processor-clock
correction, what is being measured now, and what will still be outside the
evidence when this campaign ends. It is written so that no gap can be
discovered later that is not already named here.

## 1. Audit of the thesis database before this campaign

Counted directly from `results/benchmarks.db`, restricted to the run groups the
thesis actually reports.

| Experiment | Rows | Utilisation | Energy proxy | Peak memory | EFLOP |
|---|---|---|---|---|---|
| 1 — inference, 11 backends | 44 conditions | complete | complete | complete | on all 22 `simulate` rows |
| 3 — scalability, 11 backends × 5 sizes | 220 conditions | complete | complete | complete | on all 110 `simulate` rows |
| 2 — training, 9 backends, 60k/10ep | 9 conditions | **all NULL** | **all NULL** | **all NULL** | not defined |

The `setup`-phase rows carry no EFLOP or spike count by design: EFLOP counts
synaptic operations during simulation, and the setup phase runs none.

So one experiment of three was measured on one axis only. Experiment 2 recorded
a duration and an accuracy and nothing else. That is the gap this campaign
closes.

## 2. Why Experiment 2 had no utilisation, and what changed

The training path never ran the instruments. `runner.py` called the adapter,
timed the call, and stored the duration. Utilisation was written as the
constant `100.0` and memory as `0.0` until 20 September, when both were replaced
by `None` — an honest absence, but still an absence.

Measuring it is harder than on the inference path, for three reasons, and each
needed its own answer:

1. **The reported figure is compute time, not wall time.** Each adapter sums the
   duration of the individual sample or batch presentations, excluding anything
   between them. A utilisation taken over the whole call would divide CPU by a
   different interval from the one whose duration is reported, and the energy
   proxy of equation (3.8) would then multiply two quantities measured over
   different regions. Each adapter now carries a `RegionClock` that accumulates
   **wall and CPU over exactly the region it already times**, so both terms of
   the proxy come from the same interval.

2. **A full-size run spans hundreds of processes.** Brian2 and NEST checkpoint
   and resume; a single backend can take 40 hours across 80 chunks. A clock that
   lived in one process would report one chunk. The two accumulators are now
   saved and restored with the learned weights, so the totals are the run's own,
   summed across every chunk and excluding per-chunk process startup.

3. **NEST trains in a disposable subprocess.** The parent never executes that
   work, so it cannot observe it. The worker now measures itself and returns the
   figures with its result.

Peak memory comes from the kernel's high-water mark (VmHWM), reset once per
process and carried as a running maximum through the checkpoints.

## 3. Proof before commitment

`launchers/smoke_training_instruments.sh`, run 21 Sep before the campaign was
started. Tiny budget (hidden 100, 300 train, 2 epochs); Brian2 was deliberately
chopped into 20-second chunks so the accumulators were saved and restored a
dozen times. Full output in `instrument_smoke_output/RESULT.txt`.

| backend | s/epoch | CPU % | peak MB | energy J | chunks |
|---|---|---|---|---|---|
| brian2/cpp_standalone | 59.54 | 99.9 | 647 | 3270.3 | 13 |
| brian2/cython | 52.87 | 99.8 | 644 | 2903.4 | 12 |
| brian2/numpy | 59.89 | 99.9 | 647 | 3288.8 | 13 |
| nengo/reference | 4.29 | 2945.0 | 718 | 6952.3 | 1 |
| nest/threads1 | 7.92 | 99.7 | 473 | 434.4 | subprocess |
| nest/threads2 | 4.46 | 182.1 | 474 | 446.3 | subprocess |
| nest/threads4 | 2.70 | 316.3 | 478 | 469.7 | subprocess |
| snntorch/cpu | 1.14 | 36.4 | 882 | 22.9 | 1 |
| spikingjelly/cpu | 0.88 | 46.0 | 892 | 22.3 | 1 |

Three things make these credible rather than merely present. NEST rises almost
linearly with thread count (99.7 / 182.1 / 316.3 per cent) — the instrument is
responding to real parallelism, and the figures crossed the subprocess boundary
intact. Brian2 reports 99.8–99.9 per cent, the single-threaded answer, after
twelve save-and-restore cycles — the accumulators survive checkpointing. Nengo
reports 2945 per cent, about 29 of the machine's 32 cores, matching its
behaviour on the inference path, where it reaches roughly 3,100 per cent.

The two PyTorch backends read low (36 and 46 per cent) because at this budget an
epoch is five batches and is dominated by setup rather than compute. Phase 3 of
the campaign measures the same backends at 6,000 images and Phase 4 at 60,000;
the figure should rise, and if it does not, that is itself a finding about how
little of the machine those simulators use. It is checked, not assumed.

## 4. What the campaign runs

Resumable. Every phase checks the database first and skips itself if its rows
are already there, so a reboot costs at most one chunk.

| Phase | What | Cost |
|---|---|---|
| 0 | processor-clock self-test; the run aborts if it fails | < 1 min |
| 1 | inference + scalability, all 11 backends | 0.1 h |
| 2 | the same again — a within-campaign repeat | 0.1 h |
| 3 | training, 6,000 images / 3 epochs, all 9 backends | 4.5 h |
| 4 | training, 60,000 images / 10 epochs, all 9 backends | 134 h |
| 5 | optional: training at hidden 500, the CCR-proposed width | ~260 h |

Phase 3 is not redundant. The full budget can be afforded once, so it gives no
repeat measurement of the training ordering; the cheaper budget does, and it
also cross-checks the utilisation figures — a backend should report much the
same utilisation at both budgets even though the durations differ by an order of
magnitude. A disagreement there would mean the instrument, not the simulator.

Phase 4 is ordered cheapest first, so Nengo, both PyTorch simulators and all
three NEST configurations are on disk within about a day, and only Brian2 is
still running at the end.

Phase 5 is a bonus, not a requirement: Section 3.7 already declares the 256
width and its reasons. It exists so that if an examiner asks for the 500 the
Candidature Confirmation Report proposed, the answer is measured rather than
argued. Stop it at any time by creating
`complete_run_output/SKIP_WIDTH_500.txt`; nothing above it is affected.

Nothing existing is touched. The campaign writes to its own working copy and
its own database, and the thesis results in `results/benchmarks.db` are left
alone so the two can be compared afterwards.

## 5. What will still be outside the evidence, and why

Named here so it cannot be discovered later as a surprise.

- **No EFLOP for training.** EFLOP counts synaptic operations of the forward
  simulation. It does not model a learning rule, so it has no defined value for
  a training workload and cannot be used to validate the energy proxy there.
  The proxy's ordinal validation against EFLOP therefore covers Experiments 1
  and 3, as Section 4.9 states, and not Experiment 2. Computing a number anyway
  would be inventing a metric, not measuring one.

- **No plain-NumPy training control.** The reference implementation is the
  control for inference and scalability, but it has no training implementation.
  Writing one now would put an unreviewed implementation of STDP and a
  labelling readout into the comparison days before submission, and any defect
  in it would become a false claim. It is named in Section 6.5 as future work
  instead.

- **No accelerator hardware.** Declared throughout: the comparison is a single
  processor-based platform, which is why results are reported as orderings,
  exponents and rank correlations rather than absolute times.

- **No repeat of the full training budget.** One 60,000-image run per backend
  is what the time allows. Phase 3 supplies the repeat at the smaller budget,
  and the reproducibility claim for training is stated at that budget, not at
  the full one.

- **Absolute joules are still not measured.** The proxy is ordinal by
  construction. Section 6.5 specifies the power-meter comparison that would make
  it quantitative.

## 6. What happens to the results

They go nowhere near the thesis automatically. When the campaign finishes, the
new database is compared against the one the thesis reports, backend by backend.
If the numbers agree, the thesis gains the measurements it currently declares as
missing and loses that limitation. If they disagree, the disagreement is the
finding and is reported as such.
