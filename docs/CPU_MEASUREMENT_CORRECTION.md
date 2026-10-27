# Processor-utilisation correction, 20 September 2026

This file explains why Experiments 1 and 3 (inference and scalability) were measured again, what changed, and where each result now comes from. Every figure below was measured. Nothing here is estimated.

## What was wrong

Processor utilisation feeds the energy proxy directly: E = runtime × utilisation / 100 × 55 W. The instrument that measured utilisation was wrong in two successive forms.

**1. The August campaign's sampler.** A background thread read `psutil.cpu_percent()` every 5 ms, and a region with no sample was stored as 100 %.

- Native simulator code that holds Python's GIL stops that thread from running. A 0.48 s NEST simulation got no sample at all.
- 181 of the 501 remaining runs got fewer than a quarter of the samples their duration implies.
- The samples that did arrive read as high as 388,844 %.
- The 27 August repair withdrew only the 168 runs that had been given 100 %. The rest of the values were still noise.

**2. The September fix: differencing `psutil.cpu_times()`.** On Linux those counters advance in 10 ms clock ticks, so a 1 ms region reads either 0 % or about 1,000 %.

- All 291 of the September campaign's regions shorter than 50 ms have a CPU time that is an exact multiple of 10 ms.

Runtime was not affected by either problem, because it is timed separately with `time.perf_counter()`. Spike counts and accuracy were not affected either. Peak memory came from the same starved thread, so it could miss a short-lived peak.

## The instrument now

Source: `snnbench/profiler.py`.

- **Utilisation** is the CPU time the region consumed divided by its wall time. The CPU time comes from `time.process_time()`, which reads `CLOCK_PROCESS_CPUTIME_ID`. That clock is kept in nanoseconds, covers every thread of the process, and does not need any thread to be scheduled to read it. The CPU time of child processes the region waits for is added from `getrusage(RUSAGE_CHILDREN)`; Brian2's C++ standalone target runs its compiler and binary that way.
- **Peak memory** comes from the kernel's high-water mark (`VmHWM`), which is reset at the start of each region by writing `5` to `/proc/self/clear_refs`. Because of this, no sampler thread runs during a measurement.
- **Self-test.** `tools/cpu_instrument_check.py` checks the instrument against loads whose answer is known, and every campaign runs it first. Results on the laptop, session 1:

| Load | Old sampler | Sep counters | Current |
|---|---|---|---|
| 1 ms busy loop (true 100 %) | median 0 %, max 25,056 % | median 0 %, max 1,000 % | 100.5 % |
| 100 ms busy loop | 102 % (86–123) | 100 % (90–110) | 100.5 % |
| Native code holding the GIL, about 97 ms | median 57 % | 100 % | 100.6 % |
| Two threads outside the GIL | — | — | 195 % |
| Sleeping | — | — | median 0.1–1.3 % |
| 200 MB allocation freed inside the region | — | — | 199 MB registered |

## Re-measurement

The launcher is `launchers/RUN CPU-CORRECTED MEASUREMENT.bat`, which runs `launchers/run_cpu_corrected.sh`. It repeats the same protocol: all 11 backends, N = 100 to 10,000, 5 warm-up runs and 5 measured runs. It wrote to a fresh database, so nothing existing was modified.

- **Session 1** ran 12:29–12:37 local time on LT68, run group `3dd09b61bd76-4109d4`. It is the primary data for Chapter 4, Experiments 1 and 3. All 660 runs have a utilisation reading.
- **Session 2** ran 12:40–12:47 local time, run group `3dd09b61bd76-773409`. It is a same-day replication.
- Both sessions passed the equivalence check (11/11).
- Raw outputs are in `cpu_corrected_output/session1_…` and `session2_…`, and analysis summaries are in `cpu_corrected_output/analysis/`.

## Reproducibility across four sessions

- **Ordering at a fixed network size.** The other sessions agree with session 1 at tau 0.745–1.000; the twin session agrees at 0.891 or better.
- **Ordering across the sweep.** Within each session, the ordering at N = 100 agrees with the one at N = 10,000 at only tau 0.200–0.273. The central finding therefore reproduces.
- **Absolute times.** The twin session is within −21 % to +15 % of session 1 on every condition of the size sweep. Between days the multi-threaded configurations vary more: NEST at N = 10,000 was 1.4–2.8× slower on 20 September, and Nengo at N = 1,000 was 7.1× slower than in August. The cause was not measured.

## What changed in the database (`results/benchmarks.db`)

A copy of the database before these changes is kept as `results/benchmarks_before_cpu_correction.db`. The changes were:

- Added sessions 1 and 2, using `tools/merge_corrected.py`.
- Withdrew the August campaign's inference and scalability utilisation (`cpu_pct` and `energy` set to NULL on 660 runs and 132 conditions). Its runtimes are kept as a replication.
- Stored the training memory placeholders (0.0 MB) as NULL: 26 conditions and 29 runs.
- Added the 9 full-budget training run rows. An earlier merge had copied only their condition rows.

## What changed in the dashboard

- `dashboard_data.py`:
  - Inference and scalability now come from session 1, and training from the August and September campaigns (`INFSCAL_RUN_GROUPS`, `TRAINING_RUN_GROUPS`).
  - The provenance panel now names the replication sessions.
  - Fixed a bug on the training page: it divided the stored cost per epoch by the number of epochs a second time.
  - The energy index is now normalised to the costliest simulating backend, and the chart uses a log scale.
- Training page text: removed the claim that more epochs make the plasticity rules worse. The full-budget run shows otherwise.

## What changed in the thesis

The thesis was `thesis/Final Thesis Edition - CPU corrected.docx/.pdf`, now superseded by `thesis/Final Thesis Edition - Rewritten.docx/.pdf`, built by `tools/apply_cpu_correction.py`. All changes are highlighted yellow. Every number comes from the databases, and every qualitative claim about the numbers is checked by `claim()` before it is written. An independent verification pass recomputed about 850 values from the raw runs. The findings it raised were corrected, and a second pass confirmed the corrections.

Findings that changed:

- **Energy proxy.** With correct utilisation it is largely runtime rescaled: log-energy against log-runtime gives R² = 0.911 (it was 0.421). The earlier "substantial independent contribution" came from the defective values and has been withdrawn.
- **Proxy against operation count.** Per-backend rho is +1.000 for 8 of 11 backends (it was 4 of 11). Pooled rho is 0.645 over 55 conditions; the thesis's earlier 0.716 was stale.
- **Brian2 C++ standalone** uses about 790 % CPU, not 5.3 %.
- **NEST utilisation** tracks its thread count (about 100 / 200 / 400 %).
- **Nengo** uses about 31 cores from N = 1,000 upwards.
- **Rank agreement across sizes:** tau is 0.273 / 0.236 / 0.382 / 0.818 at N = 100 / 500 / 1,000 / 5,000.
- **Rank agreement between metrics:** energy 0.782, memory 0.418, exponent 0.236.
- **Defect count** is now twelve (5 in the harness, 7 in recording and reporting). Section 4.8 describes each one.

## Not measured, with reason

- **Training utilisation, energy and peak memory.** The training path timed wall-clock only. Measuring these would mean repeating the training campaigns: the full-budget campaign took 7 days 20 hours by its own log. The thesis states this in Sections 4.6 and 4.12 and Chapter 6.
