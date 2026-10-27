# Verification report: thesis_cpu.docx, highlighted text (Exp 1/3, utilisation, memory, energy, sensitivity, reproducibility)

Everything was recomputed from the raw runs in c1.db, c2.db and benchmarks.db (August groups fb0ab3 and 1ca062). summary_S.json was used only for the September session's times. Every definition matches the brief. CV is SD/median, as the thesis's own eq. 3.12 defines it; the stored cv_pct uses the same formula.

**Checks passed: about 850 values** are exactly supported, and none of the table cells is wrong. That covers every cell of Tables 4.1, 4.2, 4.3, 4.7, 4.8, C.1–C.4, D.1 and D.2 in scope, plus all numbers in the text except those listed below. The following all check out: the Welch ANOVA, Levene, Shapiro-Wilk, the 50/55 Holm split, all 55 Cohen's d and Holm p values, the size and metric taus, the 35/20 concordant/discordant pairs, the 31–38% reversed pairs, all rank moves, the exponents, SE and R², the memory and CPU tables, the 660-run CPU distribution (100.4 / 100.0–189.1 / 57.3–3,189.1, snnTorch at 2.4x, Nengo highest), the decomposition (1.141, R² 0.911), the per-backend rho with exact p, the pooled rho 0.645 over n=55, the TDP/exponent sensitivity (6 × 1.000, 3 × 0.964, the NEST/2-thread vs SpikingJelly swap at a=1.2), the between-session taus (0.745–1.000, twin ≥0.891, 0.200–0.273, weakest 0.127–0.273, weakest at 500 vs 1000), NEST 1.4–2.8x slower, Nengo 7.1x slower, the twin's 0.463/0.497, the August Nengo CV of 58.0%, the exclusion counts 462 = 123 + 75 + 264 and 264/1,320, and 168/669 and 181/501.

## Mismatches

1. **P564 (instrument self-test), "at most 1.3% while sleeping".** This is not supported. 1.3% is the *median* for the 1 ms sleep region. The maximum readings are 7.9% (1 ms region), 1.25% (10 ms) and 0.16% (100 ms). The per-region table also shows a median of 2.4% and a maximum of 4.9% for a 10 ms sleep. Correct wording: "a median of at most 1.3% while sleeping (maximum 7.9%)", or "under 10%". The other self-test figures are OK: 100.5%, 0%/25,056%, 195%, 199 of 200 MB.
2. **P489, "NEST with one thread ... whose five runs include one slow outlier".** The runs are 2.337, 2.355, 2.367, **2.813, 2.899** ms, so there are *two* slow runs, not one. p = 0.038 is OK.
3. **P510, "every condition of the twin session lies within -21% to +15% of this one".** This holds only for scalability *simulate* conditions: -20.6% for Brian2/Cython at N=1000 and +14.7% for Brian2/Cython at N=100. The inference conditions fall outside it:
   - Inference simulate for NEST/1 thread is **+18.8%**.
   - Inference setup reaches +27.3%.
   - Scalability setup spans -18.6% to +13.6%.
   Either restrict the sentence to "every scalability condition" or change it to -21% to +19% for simulate conditions (-21% to +27% if setup counts).
4. **P595 and P598, how Brian2 affects tau(exponent, runtime) = 0.236.**
   - **The direction is wrong in P595.** Brian2/NumPy and Brian2/Cython are *fast and flat*, which is concordant, so they *raise* agreement. Removing those two drops tau to 0.056. Brian2/C++ is slow and flat, which is discordant; removing it raises tau to 0.467. P595 says the Brian2 placement is "part of the mechanical reason the two orderings agree only weakly", which gets the direction backwards for two of the three backends.
   - **P598 is only partly right.** It says the association is "driven largely by the three Brian2 backends". The positive association is indeed driven by Brian2/NumPy and Brian2/Cython. Brian2/C++ works against it, so "three" is wrong.
5. **P559, "At runtime it is an order of magnitude slower than the slowest simulating backend in the study".** This is true only at N ≤ 1000: at N=100 it is 1.669 s vs 0.143 s, 11.7x. At N=5000 it is only 1.3x slower than Nengo (1.656 vs 1.252 s). At N=10000 it is *faster* than Nengo (1.691 vs 4.530 s) and ranks 10 of 11. Qualify it as "at the reference size".
6. **P528, "beyond two threads, at these sizes, synchronization overhead consumes everything additional threads provide".** The size scope is wrong and the cause is unsupported:
   - At N=500 and N=1000, four threads beat two by about 15%: 0.0080 vs 0.0094 s and 0.0161 vs 0.0189 s. At N=100 the gap is not separable.
   - Two threads are only equal or better at N ≥ 5000.
   - "Synchronization overhead" was not measured. Restrict the claim to N ≥ 5000 and drop the causal wording, or mark it as a hypothesis. The earlier sentence ("buys nothing but a larger energy proxy") is fine at N=10000: 2.02x the CPU time and 110.8 vs 54.7 J.
7. **P525, "about 65 times Brian2's NumPy target".** The NEST growth per neuron divided by Brian2/NumPy's is 61.8, 62.6 and 64.5 (1, 2 and 4 threads). With the thesis's own rounded figures, 81–85 / 1.32 = 61–64. Say "about 62–65 times" or "over 60 times".

## Minor or definitional (numbers are right, wording is loose)

- **P524/P525, per-neuron memory growth.** The figures are (RSS at 10,000 − RSS at 100) / 10,000 neurons, in KiB. Dividing by the 9,900 neurons actually added gives NEST 82.3–85.8, Nengo 161.7 and Brian2/NumPy 1.33 KB per neuron. Either state the divisor or use the 9,900 figures.
- **P527, "Nengo uses 32" cores at N=10000.** The measured value is 3,167%, about 31.7 cores; the same paragraph says "about thirty-one". Use "about 32" or "31–32" consistently.
- **P476, "150 conditions from 678 ... runs".** 678 = 660 + the n_runs of the 18 training conditions. Only 9 training run rows actually exist in benchmarks.db: the 9 full-budget training conditions have no run rows. Likewise, the cloud groups hold 598 run rows, of which 595 belong to the 123 conditions (3 orphan training runs). Both counts are defensible but depend on counting convention.
- **P600, "Across all conditions of the session ... 55 paired observations".** n=55 is the scalability-simulate conditions only. Adding the 11 inference conditions gives rho = 0.648 with n=66. Say "across the 55 scalability conditions".
- **P510, "within one afternoon".** The two sessions ran 02:30–02:47 UTC. The data cannot establish "afternoon"; say "within the same hour".
- **P594 and P604, "the same pattern appears in each of the four sessions".** Only "agreement at N=100 is weak (0.200–0.273)" and "N=5000 recovers most" (0.673–0.818) reproduce. The weakest point is at N=500 only in this session; it is at N=100 in the twin and September, and N=1000 in August. P510 itself says so.
- **P579, "the remaining variance sits exactly where utilisation departs from one core".** Mostly true: Nengo, NEST/4, Brian2/C++ and SpikingJelly account for 75% of the residual sum of squares. But the six single-core configurations still account for about 22%, and multi-core NEST/2 for only 3.7%. "Exactly" is too strong; "mostly" is supported.

## Claims presented as fact that the data cannot establish

- **P488:** says Nengo's 58% CV in August arises "because its reference backend does variable work inside the timed interval that the discarded warm-up runs do not always absorb". This cause was not measured.
- **P520/P523:** say the RSS split between NEST and the rest is "almost entirely driven by which libraries each process has imported", and is "the cost of importing NumPy and PyTorch". The same passages say NEST's worker "imports NEST alone". None of this was measured; per-import RSS was never recorded, and PyNEST itself imports NumPy. Present it as an explanation, not a finding.
- **P526:** says NEST's growth comes "from allocating its kernel structures for the network it is given". This is a plausible mechanism, but it was not measured.
- **P527/P549:** attribute Brian2/C++'s ~8 cores to "the compiler and binary processes it starts", and say that "the interval ... is dominated by the compiler". The instrument reports total CPU including children, not a breakdown by process. The compile-dominance argument rests on the flat runtime, not on a measurement.
- **P559:** says "the process whose memory is measured is not the one holding the network". Since RSS now includes waited-for children only through CPU time, not memory, this is an assumption about where the memory lives. It should be stated as such.
- **P597:** says Nengo's growth in memory and in runtime are "both driven by the same closed-form solve". The simulate-phase time is not a decoder solve, and nothing in the data isolates the solve. This is unsupported.
- **P522:** says the 57.3% snnTorch run was one where "the process was waiting for part of its interval". This is a reasonable reading of below-100% utilisation, but it is inferred, not observed.
- **P564:** the "291 regions shorter than 50 ms in the September campaign, each an exact multiple of 10 ms" cannot be checked, because September's CPU-time values are not in the provided databases. The August figures (168/669, 181/501) are confirmed from n_cpu_samples. 388,844% cannot be checked either, because August's CPU values have been NULLed.

## Round 2 (re-check of revised statements only)

**Now OK:** P488, P489, P510 (the size-sweep conditions span -20.6% to +14.7%), P527 (31.7 cores), P525 (62–65x), P549, P559, P579, P594, P595 and P598 (tau 0.056 without Brian2's NumPy and Cython targets, 0.467 without the C++ target), P600, P604, P614, P565 (26 condition records and 29 training runs, all now missing rather than zero). The 678-run count now matches the run rows: 660 plus 18 laptop training runs. benchmarks.db holds 2,959 run rows. The cloud group's 595 runs is unchanged (598 rows including 3 orphan runs), as noted in round 1.

**Remaining issues:**
1. **P524 has a broken template placeholder.** The text reads literally "Nengo grows most, from {M['nengo/reference']['100']:.0f} to 2,204 MB". The value should be **641**.
2. **P528, "four threads were 17–17% faster than two".** This contains a typo and uses the wrong base.
   - At N=500 the medians are 0.008042 vs 0.009407 s; at N=1000 they are 0.016091 vs 0.018865 s.
   - Four threads took about **15% less time** (14.5% and 14.7%). Equivalently, two threads took 17% longer.
   - Suggested wording: "four threads took about 15% less time than two" (or "two threads took 17% longer").
3. **P564, "a median of 0.1–1.3% while sleeping".** This is right for the second self-test block: medians of 1.30, 0.50 and 0.058%. But the first comparison block, which reports the current instrument as C_current, gives a median of **2.4%** (max 4.9%) for a 10 ms sleep. Either say "a median of at most 2.4% while sleeping" or name the block being quoted.
4. **P520/P523: the import explanation does not fit the run order.** The text says every other backend "is measured in the main process after the libraries of the simulators before it have been imported". But Brian2/NumPy was measured *first* in the session (02:30:04, before every other backend), and it already reads 629 MB at N=100, within 65 MB of the last-measured backends (694 MB). So the main process's large baseline cannot come from the libraries of simulators run before it.
   - Suggested wording: the main process carries a large startup footprint (at least about 630 MB before any other simulator has run), while NEST's worker does not.
   - The worker's import list (NEST and NumPy only) cannot be checked from the data. I have taken it as stated from the code.
