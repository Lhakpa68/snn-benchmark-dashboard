# Line-by-line verification of the thesis against the measured campaign
27 September 2026

Every sentence in the body of `Final Thesis Draft_Lhakpa V4 (clean).docx` that
states a number was extracted and checked, one at a time, against the campaign
of 21-27 September 2026 (`docs/FACT_BASE_2026-09-27.md` and
`complete_run_output/ANALYSIS.md`). Nothing was sampled.

387 sentences were judged:

| Chapter | Verified | Must change | Cannot verify | Total |
|---|---|---|---|---|
| 1, 2 and unnumbered | 49 | 15 | 1 | 65 |
| 3 Methodology | 83 | 8 | 23 | 114 |
| 4 Results | 52 | 53 | 34 | 139 |
| 5 Dashboard | 17 | 30 | 22 | 69 |
| **Total** | **201** | **106** | **80** | **387** |

"Cannot verify" does not always mean wrong. It means the campaign record does
not establish the sentence: some are claims about published literature, some
describe behaviour no measurement covers, and some are statements that must
either be evidenced or withdrawn. Each is listed with the evidence it would
need.

A further 107 sentences carry only citation markers and no measured number;
they were checked for attribution rather than against the data.

---


# Chapters 1, 2 and unnumbered sections

# Audit — Chapter 1, Chapter 2 and unnumbered sections (65 sentences)

Sources of truth for this study's own measured values: `/root/v3/FACT_BASE.md`,
`/root/v3/ANALYSIS.md` (campaign of 21–27 September 2026, machine LT68, CPU only).

Sentence set: `claims_ch1.json` (18), `claims_ch2.json` (43), `claims_chX.json` (4) = 65.

Type A = states this study's own result/scope. Type B = reports other people's published work.

Counts: **VERIFIED 49 · MUST CHANGE 15 · CANNOT VERIFY 1**
(MUST CHANGE = 4 type-A factual/precision errors + 11 type-B attribution/overstatement problems;
one sentence, para 276, carries both a type-A and a type-B defect and is listed once.)

---

## 1. MUST CHANGE (15)

### 1a. Type A — disagrees with the re-measured fact base

**[para 250 | 1.4 Scope and Contributions]** "The learning experiment compares cost rather than accuracy, because the simulators use dif…"
MUST CHANGE. "compares cost rather than accuracy" is false for the re-measured campaign. Experiment 2 measured **accuracy for all nine training backends at the full budget** (nengo 85.44 %, spikingjelly 97.46 %, snntorch 97.24 %, nest/threads4 8.32 %, nest/threads2 8.24 %, nest/threads1 8.50 %, brian2/cython 9.61 %, brian2/numpy 9.61 %, brian2/cpp_standalone 9.57 %), and Chapter 2 itself (para 275) says the benchmark "reports both speed and accuracy side-by-side with the appropriate caveats". Restate as: the learning experiment reports cost **and** accuracy, but accuracy is not read as a like-for-like comparison because the simulators use different learning rules; backends at or near the 10 % chance level are reporting the sample budget, not their learning capability. While rewriting this scope sentence, also state the two scope facts the fact base establishes and this section omits: **CPU utilisation, energy and peak memory were measured for all nine training backends at two budgets** (60,000/10,000/10 epochs and 6,000/1,000/3 epochs), and **the hidden = 500 width is a partial check — only three of nine backends (nengo, spikingjelly, snntorch) were run before the tail was stopped**.

**[para 254 | 1.4 Scope and Contributions]** "an energy proxy validated by rank against an analytic cost metric (Section 4.9);…"
MUST CHANGE. The bare word "validated" overstates the measured result. Rank agreement with the EFLOP count is rho = 1.00 for **nine of eleven** backends, **0.70 for brian2/cython**, and **−0.60 for brian2/cpp_standalone**, the compile-dominated case; the pooled figure is **rho = 0.771, p = 5.62e-11 over 50 paired observations across compute-bound backends** (not 0.645 over 55). Restate as, e.g., "an energy proxy whose ordinal validity is tested by rank against an analytic cost metric and holds across compute-bound backends (pooled rho = 0.771, p = 5.62e-11), but fails for the compile-dominated brian2/cpp_standalone target (rho = −0.60) (Section 4.9)".

**[para 276 | 2.2 Learning Paradigms of SNNs]** "Without them a few neurons dominate and the network cannot separate classes, which Section…"
MUST CHANGE (type A part). "which Section 4.6 observes directly" claims this study directly observed the *mechanism* (competition / adaptive threshold / lateral inhibition missing → a few neurons dominate → classes not separated). The fact base supports only the *outcome*: the STDP backends sit at or near chance (nest 8.24–8.50 %, brian2 9.57–9.61 % against 10 % chance) and ANALYSIS.md attributes this to the sample budget — "Simulators at or near chance are reporting the sample budget, not their learning capability" — not to missing competition or inhibition. No neuron-level dominance measurement exists in the fact base. Restate as: the STDP backends stay at or near chance accuracy in Section 4.6, which is consistent with this literature but is not, on this evidence, attributable to the absence of competition or inhibition. (Type B part: see 1b below.)

**[para 311 | 2.7 Energy Measurement Approaches]** "Here the proxy is equation (8) in Section 3.9 and the thermal design power is from the ven…"
MUST CHANGE. The constant in the proxy is **not** a thermal design power. The fact base gives E = t × (u_cpu / 100) × **55 W** with the TDP source recorded as "Intel Core i9-14900HX **processor base power**, Intel ARK datasheet". Intel's "processor base power" is a distinct datasheet quantity from TDP/maximum turbo power, and the i9-14900HX draws far more than 55 W under turbo, so calling 55 W the thermal design power misnames the constant and understates the real draw. Restate as "the power constant is the 55 W processor base power from the Intel ARK datasheet (Table 7)", and say plainly that it is a datasheet base-power figure, not a measured or peak power.

### 1b. Type B — unattributed, overstated or absolute

**[para 240 | 1.2 Problem Statement and Research Gaps]** "No published study compares all five simulators under identical conditions on the same har…"
MUST CHANGE. Two unsupportable absolutes in one sentence: "**No published study** compares all five simulators" and "**no SNN benchmark** tests whether its ranking survives a change of network size or ranking metric". A literature review can only speak for the literature it searched, and only internal cross-references (Sections 2.4 and 2.5) are offered, no citations. Chapter 2 para 294 already uses the weaker, defensible form ("no **peer-reviewed** study"). Restate as "No peer-reviewed study identified in this review compares all five simulators … and none of the SNN benchmarks reviewed in Sections 2.4 and 2.5 tests whether its ranking survives …", citing [46], [50], [8], [29].

**[para 241 | 1.2 Problem Statement and Research Gaps]** "Direct energy measurement needs special hardware, and the operation-count alternative has …"
MUST CHANGE. "has not been checked against measurements on commodity processors" is an absolute negative stated as fact with no citation (only "Section 2.7"); "Direct energy measurement needs special hardware" is likewise unattributed here, although Section 2.7 cites [72], [73]. Restate with hedge and citations: "Direct energy measurement needs instrumented hardware [72], [73], and we found no study validating the operation-count alternative [9] against measurements on commodity processors (Section 2.7)."

**[para 242 | 1.2 Problem Statement and Research Gaps]** "Existing results sit in static tables that cannot be filtered by simulator, backend or exp…"
MUST CHANGE. "Existing results" generalises over the whole literature and "cannot be filtered" is absolute; no citation in the sentence. Restate as "The comparisons reviewed in Section 2.8 publish their results as static tables, which a reader cannot filter by simulator, backend or experiment type", with the specific citations ([46], [50], and the Open Neuromorphic benchmark).

**[para 268 | 2.1 Background and Motivation of Spiking Neural Networks]** "The guarantee is partial, however: subsequent work on the simulator-to-hardware gap (Secti…"
MUST CHANGE. A claim about other people's findings ("transfer is dependent on the particular tool and device") carried by a forward cross-reference alone, with no citation in the sentence, and asserted with "shows". Restate as "…later work reports that transfer depends on the particular tool and device (Xu et al. [49]; Section 2.4)".

**[para 287 | 2.3 The SNN Simulator Landscape]** "A 2026 review of the most popular cross-simulator benchmark in the field shows why this di…"
MUST CHANGE. Two problems: the superlative "**the most popular** cross-simulator benchmark in the field" is a ranking claim a review cannot establish, and no citation appears in the sentence ([38] arrives two sentences later). Restate as "A 2026 review of a widely used community benchmark model [38] illustrates why this comparison is worth doing", and drop "the most popular"; "the community's de facto standard" would need a source of its own.

**[para 306 | 2.5 Validity of Benchmarks and Stability of Reported Rankings]** "There is no published benchmark for spiking neural network simulators, including the cross…"
MUST CHANGE. "**There is no published benchmark** … that states whether its ordering is robust" is an exhaustive claim over an entire literature, uncited. Restate as "No SNN-simulator benchmark identified in this review — including the cross-simulator comparisons of Section 2.4 [46], [50], [29] — states whether its ordering is robust to a change in network size, metric or experimental settings."

**[para 308 | 2.6 Application and Deployment Environment]** "Restricting the comparison to one processor removes a further confound: the GPU backends o…"
MUST CHANGE. "the GPU backends of these simulators are separate projects with their own release cycles" is an unattributed factual claim about third-party software, and "comparing them would measure the maturity of those projects as much as the simulators" is speculation stated as fact. Either cite the GPU paths concerned (e.g. Brian2GeNN as evaluated in [50], GeNN, the PyTorch CUDA stack [6], [5]) or reframe explicitly as this study's design rationale ("we exclude the GPU paths because they are maintained separately, so a GPU comparison would confound simulator with the state of those separate projects").

**[para 324 | 2.8 Dashboards: Purpose, Benefits and User Satisfaction]** "Existing comparisons publish static tables (Sections 2.3 and 2.4), so a researcher cannot …"
MUST CHANGE. Same defect as para 242: "Existing comparisons" over-generalises and "cannot" is absolute, with only internal cross-references. Restate as "The comparisons reviewed in Sections 2.3 and 2.4 publish their results as static tables [46], [50], so a reader cannot filter them to their own simulators, inspect run-to-run variation, or check whether a ranking holds at their own network size."

**[para 330 | 2.9 Synthesis and Identification of Research Gaps]** "Section 2.8 showed that dashboards in other fields help users when they answer the user’s …"
MUST CHANGE. "**no such tool exists** for comparing SNN simulators" is an absolute existence claim with no citation and no stated search. Also "dashboards in other fields help users when …" is stronger than the evidence Section 2.8 actually reviews: the 38-study review [87] found *little evidence* of improved achievement, and [85] reports usability problems and fading use. Restate as "…dashboards in other fields are valued when they answer the user's own question quickly and transparently, although evidence of measurable benefit is mixed [87], [85]; we found no equivalent tool for comparing SNN simulators."

**[para 332 | 2.9 Synthesis and Identification of Research Gaps]** "The right data have not yet been collected in one place, and where partial data exist, nob…"
MUST CHANGE. "**nobody has shown** whether their ordering is stable enough to act on" is an absolute claim over all authors, uncited. Restate as "…and where partial data exist, no study identified in this review reports whether its ordering is stable enough to act on (Gap 1)."

**[para 332 | 2.9 Synthesis and Identification of Research Gaps]** "And even where data are available, they do not support a decision (Gap 3).…"
MUST CHANGE (lower priority). "they do not support a decision" is absolute and over-general — static tables support some decisions, just not filtered, per-constraint ones. Restate as "…and even where data are available, their static form makes them hard to act on (Gap 3)."

**[para 276 | 2.2 Learning Paradigms of SNNs]** "Without them a few neurons dominate and the network cannot separate classes, which Section…"
MUST CHANGE (type B part of the same sentence listed in 1a). "a few neurons dominate and the network **cannot** separate classes" is an absolute mechanism claim with no citation inside the sentence; the supporting works [26], [27] are cited only in the preceding sentence, and Chapter 2 itself calls their evidence limited to small datasets. Restate as "Without them, [26] and [27] report that a few neurons come to dominate and class separation degrades."

---

## 2. CANNOT VERIFY (1)

**[para 256 | 1.4 Scope and Contributions]** "a documented set of instrument defects and the safeguards they led to (Section 4.8).…"
CANNOT VERIFY. Neither FACT_BASE.md nor ANALYSIS.md contains a defect register, a defect count, or a list of safeguards; the closest items are the utilisation cross-check that passes (NEST/4 349.9 % vs 349.0 %; NEST/2 190.9 % vs 190.5 %) and the equivalence gate (11 of 11 backends within 35 % on firing rate at N = 500, furthest nest/threads4 at 15.9 %). Evidence needed: the Section 4.8 defect register itself, i.e. the enumerated defects with the run-group evidence for each and the safeguard each produced, exported from `complete_run_output/`. Note for the rewrite: as worded the sentence claims no count, which is safe — **do not restate it as "twelve documented defects"** (or any other number) unless that register, regenerated for this campaign, contains exactly that many. The stale V4 claim of a specific defect count has no support in the current fact base.

---

## 3. VERIFIED (49)

### Chapter 1 (12)

**[para 239 | 1.2 Problem Statement and Research Gaps]** "The literature review in Chapter 2 identifies three gaps:…"
VERIFIED. Internally consistent: Section 2.9 (paras 327–330) states exactly three gaps, each tied to one RQ and one objective.

**[para 240 | 1.2 Problem Statement and Research Gaps]** "Gap 1: no common benchmark.…"
VERIFIED as a gap label; the load-bearing absolute is the following sentence, which is flagged under MUST CHANGE.

**[para 241 | 1.2 Problem Statement and Research Gaps]** "Gap 2: no validated energy proxy for ordinary computers.…"
VERIFIED as a gap label; the load-bearing claim is the following sentence, flagged under MUST CHANGE.

**[para 242 | 1.2 Problem Statement and Research Gaps]** "Gap 3: no usable way to explore results.…"
VERIFIED as a gap label. Note: "no usable way" is rhetorically absolute; if the label is kept, the elaborating sentence must carry the hedge (see MUST CHANGE, para 242).

**[para 250 | 1.4 Scope and Contributions]** "All measurements run on one processor-based platform, so that runtime differences come fro…"
VERIFIED. The fact base records a single machine (LT68, i9-14900HX, 32 logical cores, 11.5 GB RAM, WSL2, Python 3.11.15) and "CPU only" for every experiment. Precision note: differences also come from configuration within one simulator — Brian2 varies ~12.8x across code-generation targets and NEST across thread counts — so "come from the simulators" is better written "from the simulators and their execution backends".

**[para 252 | 1.4 Scope and Contributions]** "evidence that the ordering of the simulators depends on network size and on the ranking me…"
VERIFIED. Size dependence: Kendall tau-b against the N = 10,000 ordering is 0.309 / 0.236 / 0.491 / 0.745 (session A) and 0.309 / 0.345 / 0.491 / 0.818 (session B) for N = 100 / 500 / 1,000 / 5,000, and the ranking reverses across the sweep (nengo 5th → 11th, brian2/cython 10th → 2nd). Metric dependence: against runtime at N = 10,000, energy proxy tau = 0.745 and peak memory tau = 0.309. If Section 4.10 quotes numbers, they must be these, not the stale 0.782 / 0.418.

**[para 253 | 1.4 Scope and Contributions]** "an open benchmark suite and dataset covering five simulators and eleven backends (Chapter …"
VERIFIED. Five simulators (Brian2, NEST, Nengo, snnTorch, SpikingJelly) and eleven execution backends (brian2 numpy/cython/cpp_standalone, nest threads1/2/4, nengo/reference, snntorch/cpu, spikingjelly/cpu, reference/scalar, reference/vectorised) match the fact base. Precision note: two of the eleven (reference/scalar, reference/vectorised) are plain-NumPy control backends, not backends of the five simulators, so the most accurate wording is "five simulators and eleven execution backends, two of which are plain-NumPy reference controls".

**[para 255 | 1.4 Scope and Contributions]** "an interactive dashboard with per-simulator and all-simulator views (Chapter 5);…"
VERIFIED against the thesis's own Chapter 5 structure (Section 5.4 per simulator, Section 5.5 all simulators). No measured value is asserted, so the fact base is not engaged.

**[para 258 | 1.5 Thesis Structure]** "Chapter 2 reviews the literature and draws out the three gaps.…"
VERIFIED. Matches Section 2.9.

**[para 258 | 1.5 Thesis Structure]** "Chapter 3 describes the research design and the design of the dashboard.…"
VERIFIED. Consistent with the Chapter 3 cross-references used throughout (Sections 3.4, 3.6, 3.7.1, 3.9, 3.11, 3.12).

**[para 258 | 1.5 Thesis Structure]** "Chapter 4 presents and discusses the results.…"
VERIFIED. Structural statement, no measured value.

**[para 258 | 1.5 Thesis Structure]** "Chapter 5 shows how a reader explores these results in the dashboard, and Chapter 6 conclu…"
VERIFIED. Matches the Chapter 5 opening (para 672) and the stated chapter count.

### Chapter 2 (33)

**[para 267 | 2.1]** "Narduzzi et al. [9] formalize this in the EFLOP metric, which counts only non-zero operati…"
VERIFIED (type B). Cited, attributed ("they report"), hedged ("about 3.6 times", "rising to 8.9 times at high sparsity").

**[para 269 | 2.1]** "Chapter 3 carries this restriction into the benchmark design.…"
VERIFIED. Internal pointer; consistent with the learning-rule caveat in Section 3.7.1 and with Experiment 2 as recorded (different rules per backend: NEF decoder, surrogate gradient, STDP).

**[para 273 | 2.2]** "Recursive least squares offers another supervised route: Arthur et al. [21] train a millio…"
VERIFIED (type B). Citation present, work attributed to its authors, magnitude hedged ("about 1,000 times"). Minor style note: "Arthur et al. [21] **report** training …" would attribute the figure as well as the work.

**[para 281 | 2.3]** "In Section 4.4 we directly measure this strength at sizes two orders of magnitude smaller.…"
VERIFIED with a precision note. NEST scaling is measured: k = 1.159 / 1.135 / 1.133 for threads1/2/4 (R² 0.984–0.993), i.e. near-linear but slightly superlinear, over N = 100 to 10,000. The largest size measured (N = 10,000) is ~2 orders below the "millions" figure but only ~25x (≈1.4 orders) below the quarter-million real-time figure cited in the same paragraph; tie "two orders of magnitude smaller" to the million-neuron figure or write "one to two orders of magnitude smaller".

**[para 282 | 2.3]** "Uludag et al. [32] extend the Nengo-style deployment to Izhikevich neurons on Loihi 2.…"
VERIFIED (type B). Cited and attributed; no absolutes.

**[para 284 | 2.3]** "In Section 4.3 we report the measured difference without deciding between these explanatio…"
VERIFIED. The difference exists and is reported: snntorch/cpu 0.01307 s vs spikingjelly/cpu 0.00991 s at N = 100, separated after Holm (p = 6.67e-03, d = 3.40); the sentence claims no cause, which matches the fact base making no causal claim.

**[para 289 | 2.3]** "Such figures are not measurements under a common protocol, and Section 4.5 tests the claim…"
VERIFIED as written (it promises a test, not a confirmation). Two notes: the informal claim it refers to (previous sentence, "the ML-oriented libraries carry the smallest memory overhead on small networks") carries no citation at all and should either be sourced or attributed to documentation; and the measured result **refutes** it — at N = 100 peak RSS is nest/threads1 91.0 MB (smallest) against snntorch/cpu 690.3 MB and spikingjelly/cpu 694.0 MB — so no later sentence may imply Section 4.5 confirmed it.

**[para 293 | 2.4]** "Xu et al. [49] find that the gap between simulator and hardware performance ranges from 6 …"
VERIFIED (type B). Cited, attributed ("find"), range given as the source's own.

**[para 295 | 2.4]** "The absence of either a size or a metric stability analysis in [50] is precisely the type …"
VERIFIED (type B). The absence claim is about one identified, cited study, which is a checkable statement about that paper rather than a claim over the literature.

**[para 298 | 2.4]** "But, as we observe in Chapter 4, the measured runtime of Brian2 varies by more than an ord…"
VERIFIED (type A). At N = 100: brian2/cpp_standalone 1.70039 s vs brian2/numpy 0.13318 s = 12.8x; at N = 10,000: 2.12605 s vs 0.14853 s = 14.3x. "More than an order of magnitude" holds at both ends.

**[para 299 | 2.4]** "What can be done, and is done in Section 3.6 and reported in Chapter 4, is to bound the di…"
VERIFIED (type A). The equivalence gate is measured: 11 of 11 backends pass at N = 500 within a 35 % tolerance on firing rate, closest reference/scalar vs reference/vectorised at 0.0 %, furthest nest/threads4 at 15.9 %. The sentence claims bounding, not exactness, which is what the data support.

**[para 305 | 2.5]** "The formal discipline for such questions is sensitivity analysis, and its literature bears…"
VERIFIED (type B) as a framing sentence whose supporting citations [63], [64], [65], [10] follow in the same paragraph. Note "**The** formal discipline" is slightly proprietorial; "One formal discipline" is safer.

**[para 305 | 2.5]** "Experiment 4 is one-factor-at-a-time, which is a limitation, not a defense, by the standar…"
VERIFIED. Cited ([63]), self-critical rather than overstated, and factually right about the design: Experiment 4 varies network size, then the ranking metric, one factor at a time (tau-b by size, then energy and memory against runtime at N = 10,000).

**[para 306 | 2.5]** "This is why Gap 1 is described in Section 2.9 as the missing common benchmark reproducible…"
VERIFIED. Internal pointer, consistent with para 331 ("the stability requirement … part of Gap 1").

**[para 310 | 2.7]** "The first is direct electrical measurement, as found in the on-chip power monitors of Spec…"
VERIFIED (type B). Three citations for three claims, and "are reported" attributes rather than asserts.

**[para 313 | 2.7]** "Section 4.9 provides the evidence for and against the ordinal validity of the proxy, rathe…"
VERIFIED (type A). Both directions exist in the fact base: rho = 1.00 for nine of eleven backends (p = 0.0167 each) in favour, brian2/cython 0.70 and brian2/cpp_standalone −0.60 against, pooled rho = 0.771 (p = 5.62e-11) across compute-bound backends. This sentence is the correctly hedged version of the contribution claim flagged at para 254.

**[para 315 | 2.7]** "The utilization-weighted proxy of Section 3.9 is responsive to what the processor did, inc…"
VERIFIED (type A). Utilisation genuinely discriminates thread use: at N = 100, nest/threads1 100.7 %, threads2 208.4 %, threads4 521.3 %, brian2/cpp_standalone 780.5 %, single-threaded brian2 targets 100.0 %; in training, NEST/4 reads 349.9 % and 349.0 % at budgets an order of magnitude apart.

**[para 315 | 2.7]** "Rank correlation is reported in Section 4.9 as specified in Objective O2.…"
VERIFIED (type A). Spearman rank correlations against EFLOP are reported per backend and pooled.

**[para 316 | 2.7]** "Both are relative quantities that appear in the dashboard and in Chapter 4, comparable wit…"
VERIFIED (type A) as a scope caveat: one machine (LT68) is confirmed, and the caveat is supported rather than contradicted by the session evidence. Note for wording: the campaign comprises **two** sessions, and session-to-session ordering agreement at a fixed size is tau = 0.964 / 0.927 / 0.818 / 0.964 / 0.964 for N = 100 / 500 / 1,000 / 5,000 / 10,000 — so "one session" must be read as the comparability scope, not as a claim that only one session was run, and nothing anywhere may claim four sessions.

**[para 319 | 2.8]** "Bach et al. [80] studied 144 dashboards and found two broad kinds.…"
VERIFIED (type B). Cited, attributed, specific.

**[para 320 | 2.8]** "During the COVID-19 pandemic, public dashboards brought together national, hospital and on…"
VERIFIED (type B). Cited [83]; descriptive, no absolutes.

**[para 322 | 2.8]** "A review of 38 studies of learning analytics dashboards found little evidence that they im…"
VERIFIED (type B). Cited [87], attributed to the review, and appropriately negative/hedged ("little evidence").

**[para 322 | 2.8]** "Helminski et al. [82] add that only half of 118 health-care dashboards involved end users …"
VERIFIED (type B). Cited, attributed, figures given as the source's.

**[para 324 | 2.8]** "Section 3.12 turns these lessons into design principles, and Chapter 5 shows how the dashb…"
VERIFIED. Internal pointer consistent with Chapter 5's stated contents (paras 672–673).

**[para 327 | 2.9]** "The review identifies three research gaps, each linked to one of the research questions an…"
VERIFIED. Three gaps map to RQ1–RQ3 and O1–O3 as stated in paras 245–248.

**[para 328 | 2.9]** "Gap 1 is the lack of a common, reproducible benchmark across Brian2, NEST, Nengo, snnTorch…"
VERIFIED as a gap definition; the five named simulators match the study's set. The absolute that supports it in the same paragraph ("There is no peer-reviewed study that runs all five …", not in this sentence set) is at least hedged to "peer-reviewed" and should be kept in that form.

**[para 328 | 2.9]** "As pointed out in Sections 2.3 and 2.4, present comparisons are restricted to subsets or c…"
VERIFIED (type B), citation present. Note: [46] supports only the second clause (algorithmic content rather than software); add [50] and [29] for "restricted to subsets", and prefer "the comparisons reviewed here" to "present comparisons".

**[para 329 | 2.9]** "Gap 2 is the lack of a validated, hardware-agnostic energy proxy for commodity hardware.…"
VERIFIED as a gap definition, supported in the same paragraph by [72], [73], [9].

**[para 330 | 2.9]** "Gap 3 is the absence of an interactive way to use benchmark data.…"
VERIFIED as a gap label. Note: "the absence of" is absolute; the hedging must be done in the elaborating sentence (flagged under MUST CHANGE, para 330).

**[para 331 | 2.9]** "The stability requirement is not a stand-alone gap but part of Gap 1.…"
VERIFIED. Framing decision, no external claim; consistent with para 306 and with Experiment 4's role.

**[para 331 | 2.9]** "Section 2.5 shows that neighboring fields treat stability as part of the method.…"
VERIFIED (type B). Summarises works cited immediately after in the same paragraph ([54], [55], [56]).

**[para 331 | 2.9]** "A common benchmark that did the same would close half of Gap 1 (coverage) and leave the ot…"
VERIFIED as a hypothetical framing. Note "half"/"the other half" is rhetorical, not a measured split; "one part … the other part" avoids reading as a quantity.

**[para 332 | 2.9]** "One part of those data, the energy figure, cannot yet be trusted without validation (Gap 2…"
VERIFIED (type B). Normative and conditional ("without validation"), consistent with the Section 2.7 citations and with this study's own mixed validation result.

### Unnumbered sections, Chapter 5 opening (4)

**[para 672 | Development of the Benchmarking Dashboard for SNN Comparison]** "This chapter shows how a reader uses the dashboard to explore the results of Chapter 4.…"
VERIFIED. Structural, no measured value asserted.

**[para 672 | …]** "It explains how to open and reproduce the dashboard (Section 5.1), how to move around it (…"
VERIFIED. Matches the Chapter 5 section list (5.1 "Accessing and Reproducing the Dashboard").

**[para 672 | …]** "It then walks through each simulator’s results one at a time (Section 5.4) and all simulat…"
VERIFIED. Consistent with the per-simulator / all-simulator views claimed in para 255.

**[para 672 | …]** "The chapter ends with the chart forms that the printed page does not use, an evaluation of…"
VERIFIED. Structural description of Sections 5.6–5.8, no measured value.

---

## 4. SUMMARY (deduplicated, priority order)

### A. Type-A factual errors against the re-measured fact base (4)

1. **para 250 — "The learning experiment compares cost rather than accuracy".** False: accuracy was measured for all nine training backends (85.44 / 97.46 / 97.24 / 8.32 / 8.24 / 8.50 / 9.61 / 9.61 / 9.57 %). Say cost **and** accuracy are reported, with the learning-rule caveat and the 10 % chance baseline. In the same scope section, add the two facts it now omits: utilisation, energy and peak memory **were** measured for all nine backends at two budgets; and hidden = 500 is a **partial** check, three of nine backends only (nengo, spikingjelly, snntorch), the remaining six not run.
2. **para 254 — "an energy proxy validated by rank".** Unqualified "validated" overstates it. Correct figures: rho = 1.00 for nine of eleven backends, brian2/cython 0.70, brian2/cpp_standalone −0.60; pooled **rho = 0.771, p = 5.62e-11, 50 paired observations** across compute-bound backends (not 0.645 / 55). State the compile-dominated exception.
3. **para 311 — "the thermal design power is from the vendor datasheet".** Misnames the constant: it is the **55 W Intel ARK "processor base power"** for the i9-14900HX, not a thermal design power and not a measured or peak figure.
4. **para 276 — "which Section 4.6 observes directly".** The study observed near-chance STDP accuracy (nest 8.24–8.50 %, brian2 9.57–9.61 % vs 10 % chance) and ANALYSIS.md attributes that to the sample budget; it did not measure neuron dominance or establish the missing-inhibition mechanism. Weaken to consistency, not direct observation.

### B. Type-B attribution / overstatement problems (11)

5. **para 240 — "No published study … and no SNN benchmark tests …".** Double absolute, uncited. Hedge to "no peer-reviewed study identified in this review" / "none of the benchmarks reviewed" and cite [46], [50], [8], [29].
6. **para 306 — "There is no published benchmark for spiking neural network simulators … ".** Same exhaustive-negative defect; hedge and cite.
7. **para 330 — "no such tool exists for comparing SNN simulators".** Absolute existence claim, uncited; also "dashboards … help users" is stronger than [87] and [85] support. Hedge both halves.
8. **para 332 — "nobody has shown whether their ordering is stable enough to act on".** Absolute over all authors, uncited. Hedge to "no study identified in this review reports".
9. **para 287 — "the most popular cross-simulator benchmark in the field".** Superlative a review cannot establish, and [38] is not in the sentence. Drop the superlative, move the citation in.
10. **para 241 — "the operation-count alternative has not been checked against measurements on commodity processors".** Absolute negative, uncited; add [9], [72], [73] and a hedge.
11. **para 242 — "Existing results sit in static tables that cannot be filtered …".** Over-general and absolute, only a section cross-reference. Restrict to the comparisons reviewed and cite them.
12. **para 324 — "Existing comparisons publish static tables … a researcher cannot …".** Same defect as item 11; restrict and cite.
13. **para 268 — "subsequent work … (Section 2.4) shows that transfer is dependent on the particular tool and device".** Literature claim carried by a forward cross-reference only; cite [49] in-sentence and use "reports".
14. **para 308 — "the GPU backends of these simulators are separate projects with their own release cycles, so comparing them would measure the maturity of those projects".** Unattributed claim about third-party software plus speculation stated as fact; cite the GPU paths or reframe as this study's design rationale.
15. **para 276 — "a few neurons dominate and the network cannot separate classes".** Absolute mechanism claim with no in-sentence citation; attribute to [26], [27]. (Same sentence as item 4.)
16. **para 332 — "even where data are available, they do not support a decision".** Absolute and over-general; soften to "are hard to act on". (Lowest priority.)

### C. Cannot verify (1)

17. **para 256 — "a documented set of instrument defects and the safeguards they led to".** No defect register exists in FACT_BASE.md or ANALYSIS.md. Needs the Section 4.8 register regenerated for this campaign (each defect, its run-group evidence, its safeguard). As worded it states no count, which is safe; **the stale "twelve documented defects" figure must not be reintroduced** anywhere.

### D. Precision notes (not errors, worth fixing while editing)

18. **para 253** — "five simulators and eleven backends" matches the fact base, but two of the eleven (reference/scalar, reference/vectorised) are plain-NumPy control backends, not simulator backends; say "eleven execution backends, two of which are plain-NumPy reference controls".
19. **para 250** — "runtime differences come from the simulators, not the hardware": within-simulator configuration also drives differences (Brian2 12.8x across targets, NEST across thread counts); write "from the simulators and their execution backends".
20. **para 281** — "two orders of magnitude smaller": the largest measured size is N = 10,000, ~25x (≈1.4 orders) below the quarter-million figure cited in the same paragraph; NEST's measured exponents here are k = 1.133–1.159, near-linear but slightly superlinear.
21. **para 316** — the campaign is **two** sessions (session-to-session tau = 0.964 / 0.927 / 0.818 / 0.964 / 0.964); keep "one session" as a comparability scope only, and never restate as four sessions.
22. **para 289** — the informal claim being tested (ML libraries have the smallest memory overhead at small N) is uncited and is **refuted** by the data (nest/threads1 91.0 MB vs snntorch 690.3 MB, spikingjelly 694.0 MB at N = 100); no later text may imply Section 4.5 confirmed it.
23. **para 252** — if Section 4.10 is quoted in the introduction, the metric-stability figures are **energy tau = 0.745, memory tau = 0.309** (not 0.782 / 0.418), and the size figures are 0.309 / 0.236 / 0.491 / 0.745 (A) and 0.309 / 0.345 / 0.491 / 0.818 (B).
24. **para 328, 305, 331** — minor: attach [29], [50] to "restricted to subsets"; "One formal discipline" rather than "The formal discipline"; "half of Gap 1" is rhetorical, not a measured split.

### Counts

| Verdict | Count |
|---|---|
| VERIFIED | 49 |
| MUST CHANGE | 15 (4 type-A, 11 type-B; para 276 appears in both lists as one sentence with two defects) |
| CANNOT VERIFY | 1 |
| **Total sentences audited** | **65** (Ch1 18, Ch2 43, unnumbered 4) |

Stale V4 values checked for and **not** found in any Chapter 1, Chapter 2 or unnumbered-section sentence
(so they need checking only in Chapters 3–4): F(10, 17.22) = 1898.78 / eta² = 0.9986; "one of eleven backends
fails Shapiro-Wilk" (two fail: brian2/numpy p = 0.0072, nest/threads2 p = 0.0071); rho = 0.645 over 55;
tau energy 0.782 / memory 0.418; flattest scaling brian2/numpy k = 0.023 (it is brian2/cython, k = 0.014,
95 % CI [−0.014, 0.043]); "four sessions"; "twelve documented defects"; "training utilisation, energy and
memory not measured".


# Chapter 3 — Research Design and Methodology

# Chapter 3 factual audit — Research Design and Methodology

Sources of truth: `/root/v3/FACT_BASE.md` (campaign of 21–27 September 2026) and `/root/v3/ANALYSIS.md`.
Claims audited: all 114 sentences in `/root/v3/claims_ch3.json`. No sampling.

**How the verdicts were applied.** A sentence is VERIFIED when it matches a measured value, or when it is a protocol/design statement that the executed campaign is consistent with (bare navigational pointers and figure/table captions fall here). It is MUST CHANGE when the stated protocol disagrees with what the campaign actually did. It is CANNOT VERIFY when it asserts something substantive that neither the fact base nor the campaign record establishes — chiefly dashboard behaviour, cited literature, and incidents or projections that exist only in the thesis narrative. Advisory notes attached to VERIFIED entries are not defects in the sentence itself but numbers or wordings to reconcile; every one is also carried into the summary.

Counts: **83 VERIFIED, 8 MUST CHANGE, 23 CANNOT VERIFY** (total 114).

---

## MUST CHANGE (8)

16. [para 360 | 3.3 Research Paradigm and Overall Design] "The experimental design is a full factorial over simulator-backend pair and network size f…"
  MUST CHANGE — Wrong part: "a single-factor comparison for Experiment 2". Experiment 2 was run at TWO training budgets for all nine training-capable backends (60,000 train / 10,000 test / 10 epochs / hidden 256, and 6,000 / 1,000 / 3 epochs / hidden 256), plus a partial hidden-500 arm for three of the nine. Correct statement: Experiments 1 and 3 are a full factorial over the 11 simulator-backend pairs and the 5 network sizes with every cell completed; Experiment 2 crosses 9 training-capable backends with 2 training budgets, with a partial hidden-width arm (3 of 9 backends) reported separately.

37. [para 396 | 3.6 Experiment 1: Feedforward Inference] "This holds only for a backend that compiles once, which Experiment 4 tests."
  MUST CHANGE — Wrong part: "which Experiment 4 tests". Experiment 4's conditions in the record are network size, choice of metric and session repeat; none of them varies compilation behaviour. The compile-once assumption is exposed by Experiment 1/3 and the energy-proxy validation: brian2/cpp_standalone takes 1.70039 s at N = 100, has k = 0.023 (95% CI [-0.038, 0.083]) and rho = -0.60 against the EFLOP count, the only negative in the table. Correct statement: point the sentence at Experiment 3 and Section 4.7 (the compile-dominated target), not at Experiment 4.

42. [para 402 | 3.7 Experiment 2: The Cost of Learning on MNIST] "Memory and processor utilization were not observed during training, a limitation reported …"
  MUST CHANGE — Wrong part: "Memory and processor utilization were not observed during training, a limitation reported in Section 4.6." This is obsolete. Training now measures processor utilisation, peak memory AND the energy proxy for all nine backends at both budgets (nengo 2246.3% / 1593 MB / 3586 J; snntorch/cpu 99.6% / 1311 MB / 4984 J; nest/threads1 100.0% / 1574 MB / 242064 J; brian2/cpp_standalone 100.0% / 878 MB / 816776 J). FACT_BASE records this explicitly as "the declared gap closes". Delete the limitation sentence and the Section 4.6 pointer to it, and state instead that training is instrumented with the same three quantities as inference.

44. [para 403 | 3.7 Experiment 2: The Cost of Learning on MNIST] "The architecture has three layers throughout: 784 input units, a hidden layer of 256 leaky…"
  MUST CHANGE — Wrong part: "three layers throughout: 784 input units, a hidden layer of 256 ... ". Hidden 256 holds for both main budgets, but a partial hidden-500 arm was also run: nengo 4.95 s/ep at 88.38%, spikingjelly 157.60 s/ep at 97.44%, snntorch 157.94 s/ep at 97.67% - three of nine backends, the remaining six not run. Correct statement: the main comparison fixes hidden = 256 at both budgets, and a partial check at hidden = 500 covers three of the nine backends, with the other six explicitly not run.

71. [para 446 | 3.10  Statistical Analysis Plan] "Scaling exponent k: For a backend measured at network sizes N₁,..., Nₘ (m is four or five,…"
  MUST CHANGE — Wrong part: "m is four or five, depending on how many sizes that backend completed". Every one of the eleven backends completed all five sizes in this campaign, so m = 5 throughout - which is also what para 415's "three degrees of freedom" presupposes (df = m - 2 = 3). Correct statement: m = 5 for all eleven backends (df = 3); keep the four-size case only as a contingency explicitly noted as not arising.

83. [para 461 | 3.11 Experiment 4: Sensitivity Analysis] "Experiment 4 needs no new measurement: both comparisons are recomputed from the Experiment…"
  MUST CHANGE — Wrong part: "Experiment 4 needs no new measurement: both comparisons are recomputed from the Experiment 3 scalability sweep." Inference and scalability were measured TWICE, in two back-to-back sessions, and Experiment 4 now reports a comparison that only the repeat makes possible: session-to-session agreement at a fixed size (tau-b 0.964 / 0.927 / 0.818 / 0.964 / 0.964 for N = 100 / 500 / 1,000 / 5,000 / 10,000). The per-size orderings were themselves obtained twice (session A 0.309 / 0.236 / 0.491 / 0.745; session B 0.309 / 0.345 / 0.491 / 0.818). Correct statement: Experiment 4 has three comparisons - ordering across sizes and ordering across metrics, both recomputed from the sweep, and session-to-session reproducibility, which required a second full measurement session of Experiments 1 and 3.

105. [para 504 | 3.13 Reliability, Validity and Reproducibility] "Each condition follows the warm-up and retention protocol of Section 3.6, and every compar…"
  MUST CHANGE — Wrong part: "every comparison is drawn from one measurement session on one machine". Inference and scalability were measured in TWO sessions, back to back, on the one machine, and Experiment 4 explicitly compares them (session-to-session tau-b 0.964 / 0.927 / 0.818 / 0.964 / 0.964 by size; per-size orderings from session A and session B). Correct statement: one machine and one campaign, with Experiments 1 and 3 measured in two consecutive sessions so that session-to-session agreement can itself be reported. FACT_BASE also withdraws the older "four sessions" framing - two, not four.

108. [para 506 | 3.13 Reliability, Validity and Reproducibility] "The claim is that the ordering and scaling behaviour transfer, with Experiment 4 as the ev…"
  MUST CHANGE — Wrong part: "The claim is that the ordering and scaling behaviour transfer, with Experiment 4 as the evidence." Experiment 4 is a single-machine, single-campaign, two-session check and supplies no cross-machine evidence at all. Worse, it shows the ordering does NOT hold across sizes - tau-b against N = 10,000 is 0.309 at N = 100, 0.236/0.345 at N = 500, 0.491 at N = 1,000, 0.745/0.818 at N = 5,000, with an outright rank reversal (nengo 5th to 11th, brian2/cython 10th to 2nd) - nor fully across metrics (energy 0.745, peak memory 0.309). Para 352 of this same chapter already says the ordering changes with size and metric, so the two sentences contradict each other. Correct statement: the transferable findings are the scaling exponents and the size-resolved pattern, shown to replicate between two sessions on one machine (tau-b 0.818-0.964 at fixed size); the ordering is size- and metric-dependent, and transfer to other machines is untested.

---

## CANNOT VERIFY (23)

8. [para 345 | 3.1 Introduction] "Every run is stored with its provenance in an append-only database that the dashboard read…"
  CANNOT VERIFY — Per-run storage IS established (benchmarks.db; "every individual run is stored"). Not established: that the database is append-only, or that the dashboard opens it without modifying it. Evidence needed: the schema/write path and the dashboard's data-access code (read-only connection).

15. [para 359 | 3.3 Research Paradigm and Overall Design] "Section 4.8 describes what happened when that restriction was absent on one occasion."
  CANNOT VERIFY — The record contains no incident in which a query was not restricted to the measurement machine. Evidence needed: the Section 4.8 deviation log or the offending query/commit; otherwise drop the sentence.

24. [para 372 | 3.4 The Measurement Platform] "Our review of the deployment literature in Section 2.6 supports treating that setting as a…"
  CANNOT VERIFY — A claim about the Section 2.6 deployment literature, which neither the fact base nor the campaign record touches. Evidence needed: the cited sources supporting CPU-only as a deployment target.

50. [para 408 | 3.7.1 Learning Paradigms and Optimization Objectives] "Second, the cost of the full reference configuration (60,000 training and 10,000 test imag…"
  CANNOT VERIFY — The "later executed" half is confirmed (full budget run for all nine backends). Not established: that a projection from measured per-image cost was computed, or its values. Evidence needed: the projection code/spreadsheet behind Table 12; otherwise present the full budget purely as measured.

52. [para 409 | 3.7.1 Learning Paradigms and Optimization Objectives] "Section 4.8 documents all three."
  CANNOT VERIFY — "All three" of what is not resolvable from the record; no set of three deviations/incidents is documented anywhere in the fact base or ANALYSIS. Evidence needed: the Section 4.8 deviation list.

58. [para 415 | 3.8 Experiment 3: Scalability] "Below a coefficient of 0.25, the analysis and dashboard omit the exponent and report the s…"
  CANNOT VERIFY — The rule was never exercised: the lowest R-squared in the campaign is 0.322 (brian2/cpp_standalone), so no series fell below 0.25 and an exponent is reported for all eleven backends. Evidence needed: the analysis/dashboard code implementing the 0.25 threshold, or soften to a contingency that did not arise.

61. [para 420 | 3.9 The Energy Proxy and How It Is Validated] "An earlier, sampled form of this measurement was defective; Section 4.8 documents it."
  CANNOT VERIFY — No earlier, sampled utilisation instrument and no defect appear in the fact base or ANALYSIS. Evidence needed: the superseded implementation plus the Section 4.8 write-up of the defect and its effect.

63. [para 424 | 3.9 The Energy Proxy and How It Is Validated] "This is what equation (8) reduces to once (7) is substituted."
  CANNOT VERIFY — Equations (7) and (8) are not in the supplied material, so the algebraic reduction cannot be checked. Evidence needed: the two equations as typeset; the only form the record fixes is E = t x (u/100) x 55 W.

64. [para 429 | 3.9 The Energy Proxy and How It Is Validated] "the expected number of spikes from N Poisson sources at rate r over the simulated interval…"
  CANNOT VERIFY — The definition is internally plausible, but the record does not establish the Poisson rate r or that any adapter path actually used this fallback. Evidence needed: Table 2's input rate and the adapter that reports only output spikes. (The record supplies only measured medians - 108, 535, 1007, 5220, 10509 spikes - against EFLOP 11,000 to 1,100,000.)

65. [para 430 | 3.9 The Energy Proxy and How It Is Validated] "Third, a sensitivity analysis re-derives the ordering with thermal design power varied ±30…"
  CANNOT VERIFY — No sensitivity analysis over thermal design power (+/-30%) or a utilisation exponent (0.8 to 1.2) appears anywhere in the record; the Experiment 4 conditions reported are network size, metric and session. Note also that multiplying TDP by a constant cannot change any ranking, so that half of the test is trivially tau = 1. Evidence needed: the executed sensitivity output, or restrict the claim to the utilisation exponent, or delete it.

86. [para 469 | 3.12.1 Dashboard design principles] "Each is drawn from the dashboard literature reviewed in Section 2.8 or from the measuremen…"
  CANNOT VERIFY — Neither the design principles' provenance (Section 2.8) nor their visibility in the shipped interface is in the campaign record. Evidence needed: the current dashboard build plus the cited dashboard literature.

89. [para 481 | 3.12.3 Functional requirements validation] "The functional and non-functional requirements of the dashboard were derived from RQ3, fro…"
  CANNOT VERIFY — Requirement provenance (RQ3, Section 3.12.1, Rabiei and Almasi [81]) is outside the fact base and campaign record. Evidence needed: the requirements table and reference [81].

92. [para 483 | 3.12.3 Functional requirements validation] "The verification establishes that the dashboard does what it was specified to do; it does …"
  CANNOT VERIFY — Asserts that verification established the dashboard meets its specification; no dashboard verification result exists in the record. Evidence needed: the executed Table 6 verification log against the current build.

93. [para 490 | 3.12.4 Dashboard Architecture] "It can be exercised directly from an interpreter, which is how the Chapter 4 figures were …"
  CANNOT VERIFY — Not in the record. Evidence needed: the dashboard/analysis module's public entry point and the transcript of the figure-versus-interface cross-check (particularly since every figure has just been regenerated).

97. [para 498 | 3.12.4 Dashboard Architecture] "The sidebar (1) links to every page and ends with an Export all data button."
  CANNOT VERIFY — Dashboard behaviour is not in the campaign record and may have changed with the re-run. Evidence needed: the current build (presence of every page link and the Export all data control in the sidebar).

98. [para 498 | 3.12.4 Dashboard Architecture] "The top bar (2) names the page and shows when it was loaded."
  CANNOT VERIFY — Evidence needed: the current build (top bar showing page name and load time).

99. [para 498 | 3.12.4 Dashboard Architecture] "The simulator selector (3) is shared by every page: de-selecting a simulator removes its b…"
  CANNOT VERIFY — Evidence needed: the current build; that de-selecting a simulator propagates to charts, tables AND headline figures on every page has to be re-checked, since it is the strongest behavioural claim here.

100. [para 498 | 3.12.4 Dashboard Architecture] "The headline band (4) gives the fastest inference, lowest peak memory, flattest scaling an…"
  CANNOT VERIFY — Evidence needed: the current build. Note the underlying headline values have all moved with the re-run - fastest inference reference/vectorised 0.00130 s, lowest peak memory nest/threads1 91.0 MB, flattest scaling now brian2/cython k = 0.014 (was brian2/numpy), best MNIST accuracy spikingjelly/cpu 97.46% - and training now also yields energy and memory, so both the band's contents and the stated exclusions must be re-verified.

101. [para 498 | 3.12.4 Dashboard Architecture] "Below a one-line statement of the study (5), six preview cards (6) each show a small versi…"
  CANNOT VERIFY — Evidence needed: the current build - specifically that there are exactly six preview cards and which results pages they target.

102. [para 498 | 3.12.4 Dashboard Architecture] "The footer (7) counts the runs, conditions and backends behind the page."
  CANNOT VERIFY — Evidence needed: the current build; the run, condition and backend counts in the footer also change with the two-session campaign and the second training budget.

103. [para 498 | 3.12.4 Dashboard Architecture] "The homepage thus summarizes and directs rather than concludes; Figure 17 in Chapter 5 sho…"
  CANNOT VERIFY — Evidence needed: the current build and Figure 17 in Chapter 5.

109. [para 507 | 3.13 Reliability, Validity and Reproducibility] "Reproducibility is addressed by releasing the harness, the exact commands, the results dat…"
  CANNOT VERIFY — Per-row provenance and an analysis pipeline are established by the record (benchmarks.db, run.py analyse), but public release of harness, commands, database and pipeline is not. Evidence needed: the repository/archive location and a clean-clone reproduction of ANALYSIS.md.

110. [para 507 | 3.13 Reliability, Validity and Reproducibility] "Every figure in this thesis is computer-drawn, and the browser interface renders with no i…"
  CANNOT VERIFY — Neither claim is in the campaign record. Evidence needed: figure-generation provenance for every figure (including the Chapter 3 schematics) and an offline render test of the interface with networking disabled.

---

## VERIFIED (83)

1. [para 337 | 3.1 Introduction] "One design feature is stated explicitly upfront, rather than left to inference: the compar…"
  VERIFIED — Basis: FACT_BASE machine block (LT68, i9-14900HX, WSL2) and ANALYSIS "Single machine, CPU only." One hardware platform is what the campaign used.

2. [para 337 | 3.1 Introduction] "Section 6.3 discusses the major future work on extending the same harness to GPU hardware."
  VERIFIED — Structural cross-reference, consistent with the record: the campaign is CPU only, no accelerator runs exist, so GPU work is correctly future work.

3. [para 338 | 3.1 Introduction] "Experiment 4 is a sensitivity analysis to explore whether the simulator ordering is robust…"
  VERIFIED — Matches the record: Experiment 4 varies network size, choice of metric and session repeat, and reports Kendall tau-b for each.

4. [para 341 | 3.1 Introduction] "One workload and network is defined once (Table 2) and translated for every simulator, so …"
  VERIFIED — Consistent: one shared model definition, and the equivalence check passes for 11 of 11 backends at N = 500. Advisory: the agreement is within a 35% tolerance (worst case nest/threads4 at 15.9%), not exact, so avoid reading the sentence as bit-exact model identity.

5. [para 342 | 3.1 Introduction] "Warm-up, retained runs, seeding and separately timed setup follow the steady-state literat…"
  VERIFIED — Basis: setup and simulation are timed separately in the Experiment 1 table, and every condition has 5 warm-up plus 5 retained runs (Shapiro-Wilk rows all n = 5).

6. [para 343 | 3.1 Introduction] "Runtime, memory, processor utilization and the derived energy proxy are recorded by one sh…"
  VERIFIED — Now fully true, including training: processor utilisation, peak memory and the derived energy proxy are recorded for all nine training-capable backends at both budgets, and the environment is captured at run time.

7. [para 344 | 3.1 Introduction] "Descriptive and inferential statistics, scaling fits and the rank-stability test of Experi…"
  VERIFIED — Supported by ANALYSIS: "Chapter 3 specifies these before any parametric test." The plan (Levene, Shapiro-Wilk, Welch ANOVA, Holm, tau-b, Spearman, OLS fits) is the plan that was executed.

9. [para 350 | 3.2 Benchmarking Dashboard for SNN Comparison] "The full protocol is described in Sections 3.6-3.9."
  VERIFIED — Navigational; the sections named do contain the protocol elements the record exercises.

10. [para 351 | 3.2 Benchmarking Dashboard for SNN Comparison] "Section 3.12 describes the controls that do this."
  VERIFIED — Navigational.

11. [para 352 | 3.2 Benchmarking Dashboard for SNN Comparison] "No simulator is declared the winner, because the measurements in Chapter 4 demonstrate tha…"
  VERIFIED — Matches the measurements: ordering changes with size (tau-b 0.309 between N = 100 and N = 10,000; rank reversal, nengo 5th to 11th, brian2/cython 10th to 2nd) and with metric (energy 0.745, peak memory 0.309 against runtime).

12. [para 353 | 3.2 Benchmarking Dashboard for SNN Comparison] "Figure 1 shows all three elements together and the remainder of this chapter describes eac…"
  VERIFIED — Navigational.

13. [para 355 | 3.2 Benchmarking Dashboard for SNN Comparison] "Figure 1 A benchmarking dashboard for SNN comparison"
  VERIFIED — Figure caption.

14. [para 359 | 3.3 Research Paradigm and Overall Design] "Each query behind each figure in Chapter 4 is limited to the machine that ran the campaign…"
  VERIFIED — Consistent: the whole campaign ran on one machine (LT68), and ANALYSIS is generated from that single machine's rows.

17. [para 360 | 3.3 Research Paradigm and Overall Design] "Experiment 4 is of a different kind."
  VERIFIED — Consistent: Experiment 4 recomputes orderings rather than adding a new workload factor.

18. [para 361 | 3.3 Research Paradigm and Overall Design] "The design in Figure 2 runs from gap to objective, so that every measurement reported in C…"
  VERIFIED — Design statement, no conflict with the record.

19. [para 363 | 3.3 Research Paradigm and Overall Design] "Figure 2 Research design overview."
  VERIFIED — Figure caption.

20. [para 365 | 3.3 Research Paradigm and Overall Design] "Figure 3 illustrates the instrument that carries out the design."
  VERIFIED — Navigational.

21. [para 367 | 3.3 Research Paradigm and Overall Design] "Figure 3 Architecture of the benchmark harness."
  VERIFIED — Figure caption.

22. [para 371 | 3.4 The Measurement Platform] "This choice also means that we cannot quote absolute timing as a property of a simulator: …"
  VERIFIED — Design statement, consistent with a single-platform campaign.

23. [para 371 | 3.4 The Measurement Platform] "Section 3.14 records the platform in a programmatic fashion at run time, not by transcript…"
  VERIFIED — Supported: ANALYSIS carries a machine table and "Package versions, captured at run time" (numpy 2.4.6, scipy 1.17.1, brian2 2.9.0, nest 3.10.0, nengo 4.1.0, snntorch 1.0.0, torch 2.13.0+cu130, spikingjelly, cython 3.2.9, psutil 7.2.2).

25. [para 372 | 3.4 The Measurement Platform] "Applying the same harness to accelerator hardware is a separate study with its own design …"
  VERIFIED — Consistent: no accelerator runs exist in the campaign (accelerator = "CPU only").

26. [para 374 | 3.5  Variables and Operational Definitions] "Table 1 Variables, operational definitions, units and instruments."
  VERIFIED — Table caption.

27. [para 376 | 3.5  Variables and Operational Definitions] "Figure 4 shows the network used in all five simulators and names the quantities kept const…"
  VERIFIED — Five simulators is right: brian2, nest, nengo, snnTorch, SpikingJelly. Advisory: the same network is also run by the two plain-NumPy control backends (reference/scalar, reference/vectorised), which this sentence silently omits; 11 backends in total.

28. [para 377 | 3.5  Variables and Operational Definitions] "Figure 4 The network under test."
  VERIFIED — Figure caption.

29. [para 380 | 3.6 Experiment 1: Feedforward Inference] "Each simulator builds the network of Table 2, receives Poisson input at the same rate and …"
  VERIFIED — Consistent with the shared-workload design and the equivalence result (11/11 at N = 500).

30. [para 386 | 3.6 Experiment 1: Feedforward Inference] "With Δt = 0.1 ms and τₘ = 10 ms, α = 0.990."
  VERIFIED — Arithmetic checks: exp(-0.1 ms / 10 ms) = exp(-0.01) = 0.99005, i.e. 0.990.

31. [para 388 | 3.6 Experiment 1: Feedforward Inference] "When zⱼ[t] equals 1, the potential is reset."
  VERIFIED — Model definition; no conflict with the record.

32. [para 388 | 3.6 Experiment 1: Feedforward Inference] "In this equation, zⱼ[t] represents the emitted spike, and the firing threshold is the valu…"
  VERIFIED — Model definition; no conflict with the record.

33. [para 388 | 3.6 Experiment 1: Feedforward Inference] "The equivalence check in Section 3.13 compares the spike count between simulators."
  VERIFIED — The equivalence check on spiking output exists and passes 11/11. Advisory: the record states the tolerance on FIRING RATE (35%, closest reference/scalar vs reference/vectorised 0.0%, furthest nest/threads4 15.9%) and at N = 500; Chapter 3 should name the same quantity and state the size, tolerance and 11/11 outcome.

34. [para 392 | 3.6 Experiment 1: Feedforward Inference] "Table 2 gives S = 100 steps for all network sizes."
  VERIFIED — Consistent: 100 steps at dt = 0.1 ms is the 10 ms simulated interval used at every size, and the EFLOP count grows with N alone (11,000 at N = 100 up to 1,100,000 at N = 10,000, i.e. 110 x N).

35. [para 393 | 3.6 Experiment 1: Feedforward Inference] "Table 2 Shared neuron-model, network and input parameters."
  VERIFIED — Table caption.

36. [para 395 | 3.6 Experiment 1: Feedforward Inference] "Only by preserving the observations can the parametric assumption checks in Section 3.10 b…"
  VERIFIED — Supported: ANALYSIS notes the distributional checks "are computable here because every individual run is stored".

38. [para 396 | 3.6 Experiment 1: Feedforward Inference] "Section 4.7 shows what a backend that recompiles on every invocation reports instead."
  VERIFIED — Supported by the compile-dominated case: brian2/cpp_standalone 1.70039 s simulate median at N = 100, essentially flat across the sweep (1.79 s to 2.13 s), 746.96 J at N = 100, rho = -0.60 against EFLOP.

39. [para 397 | 3.6 Experiment 1: Feedforward Inference] "Figure 5 shows the protocol for each condition."
  VERIFIED — Navigational.

40. [para 399 | 3.6 Experiment 1: Feedforward Inference] "Figure 5 Measurement protocol for one condition."
  VERIFIED — Figure caption.

41. [para 402 | 3.7 Experiment 2: The Cost of Learning on MNIST] "Experiment 2 measures and reports the cost of learning: what one passes of each simulator'…"
  VERIFIED — Now correct: training reports wall-clock (s/epoch), peak memory and processor utilisation for all nine backends, e.g. spikingjelly/cpu 89.94 s/ep, 99.5%, 1322 MB; nest/threads4 1361.71 s/ep, 349.0%, 2331 MB.

43. [para 403 | 3.7 Experiment 2: The Cost of Learning on MNIST] "One network parameter needs explicit statement, because every training figure in Chapter 4…"
  VERIFIED — Design statement, no conflict.

45. [para 403 | 3.7 Experiment 2: The Cost of Learning on MNIST] "The confirmation report proposed a hidden layer of 500."
  VERIFIED — Supported: FACT_BASE names hidden 500 "the CCR-proposed width". Advisory: Chapter 3 should now add that this width was partially executed (3 of 9 backends) rather than only proposed.

46. [para 403 | 3.7 Experiment 2: The Cost of Learning on MNIST] "First, it keeps the training budget as the only difference between the fixed-budget result…"
  VERIFIED — Consistent: both executed budgets use hidden = 256, so the training budget is indeed the only difference between the small-budget and full reference configurations.

47. [para 406 | 3.7.1 Learning Paradigms and Optimization Objectives] "Experiment 2 is a cost comparison, not an accuracy benchmark, because the five simulators …"
  VERIFIED — Supported by the objectives actually used (NEF decoder for nengo, surrogate gradient for snnTorch/SpikingJelly, STDP for NEST, unsupervised for brian2) and by accuracy spanning 8.24% to 97.46% with chance at 10%.

48. [para 407 | 3.7.1 Learning Paradigms and Optimization Objectives] "Experiment 2 is therefore defined as a cost comparison, with accuracy reported beside each…"
  VERIFIED — Consistent with how the record presents accuracy: an outcome at a stated budget, with several backends at or near chance.

49. [para 408 | 3.7.1 Learning Paradigms and Optimization Objectives] "First, every training-capable simulator and backend receives the same budget: 6,000 traini…"
  VERIFIED — Exactly the repeat budget in the record: 6,000 / 1,000 / 3 epochs, all nine backends. Nengo's single closed-form solve is corroborated by its full-budget note (util_wall_s = 2.9 s equals its 2.90 s/epoch figure, i.e. one solve, not ten epochs).

51. [para 408 | 3.7.1 Learning Paradigms and Optimization Objectives] "It was later executed for all nine backends, and Table 12 sets the projection beside the m…"
  VERIFIED — "All nine backends" is exactly right: the full-budget table lists nine (nengo, spikingjelly, snntorch, nest x3, brian2 x3). See para 408 above for the projection column, which the record does not contain.

53. [para 410 | 3.7.1 Learning Paradigms and Optimization Objectives] "The warm-up protocol (Section 3.6) follows the performance-engineering literature on warm-…"
  VERIFIED — Citation/design statement, consistent with the warm-up protocol actually used for Experiments 1 and 3. Advisory: the record shows one training run per backend per budget with no dispersion reported, so this sentence must not be read as promising warm-up or replicated runs in Experiment 2.

54. [para 412 | 3.8 Experiment 3: Scalability] "A value of k ~ 1 means cost scales with network size; k ~ 0 means fixed overhead dominates…"
  VERIFIED — Consistent with the fitted exponents (nest ~1.13-1.16 and reference/scalar 0.982 near one; brian2 0.014-0.023 near zero with runtime dominated by fixed cost).

55. [para 414 | 3.8 Experiment 3: Scalability] "Five sizes are used: 100, 500, 1 000, 5 000 and 10 000 neurons, spanning two orders of mag…"
  VERIFIED — Exactly the sizes measured: 100, 500, 1,000, 5,000, 10,000; 100 to 10,000 is two orders of magnitude.

56. [para 414 | 3.8 Experiment 3: Scalability] "A simulator whose cost at 100 neurons is dominated by setup shows a property a practitione…"
  VERIFIED — Design statement, illustrated in the record by brian2/cpp_standalone (1.79 s at N = 100, dominated by compilation).

57. [para 415 | 3.8 Experiment 3: Scalability] "Three quantities are kept with the slope: its standard error, the 95 per cent confidence i…"
  VERIFIED — All three are reported for every backend, and the interval width confirms t with 3 df: brian2/cython 0.014 +/- 3.182 x 0.009 = [-0.014, 0.043], the published CI.

59. [para 416 | 3.8 Experiment 3: Scalability] "The backend yields an exponent indistinguishable from zero: its runtime does not respond t…"
  VERIFIED — True of the two backends whose intervals contain zero: brian2/cpp_standalone k = 0.023, CI [-0.038, 0.083]; brian2/cython k = 0.014, CI [-0.014, 0.043]. CAUTION: if the surrounding paragraph names brian2/numpy (the V4 exemplar, k = 0.023), that must change - brian2/numpy is now k = 0.017 with CI [0.005, 0.030], which EXCLUDES zero, and the flattest backend is brian2/cython at k = 0.014.

60. [para 420 | 3.9 The Energy Proxy and How It Is Validated] "Values above 100 per cent indicate real multi-core execution."
  VERIFIED — Supported: nest/threads4 521.3%, brian2/cpp_standalone 780.5% at inference; nengo 2246.3% and nest/threads4 349.0% in training.

62. [para 422 | 3.9 The Energy Proxy and How It Is Validated] "where E is the energy proxy in joules, T the measured runtime in seconds, and the last ter…"
  VERIFIED — Matches the definition in the record: E = t x (u_cpu / 100) x 55 W, with 55 W taken from Intel ARK. Advisory: ANALYSIS sources 55 W as the i9-14900HX PROCESSOR BASE POWER; keep that wording beside "thermal design power", and check Table 7 actually prints the 55 W value and its source.

66. [para 433 | 3.10  Statistical Analysis Plan] "Table 3 Statistical procedures, their purpose and their assumptions."
  VERIFIED — Table caption.

67. [para 435 | 3.10  Statistical Analysis Plan] "Table 3 identifies each procedure and explains why it was chosen; what follows is a descri…"
  VERIFIED — Navigational; the procedures named in the plan are the ones executed (Levene, Shapiro-Wilk, Welch ANOVA, Welch t with Holm, Cohen's d, OLS scaling fit, Kendall tau-b, Spearman rho).

68. [para 436 | 3.10  Statistical Analysis Plan] "Coefficient of variation: for a condition with retained runtimes r₁,..., r₅, median m and …"
  VERIFIED — Consistent: five retained runs per condition gives n - 1 = 4, and CV is reported as a percentage (e.g. reference/vectorised 11.7%, reference/scalar 4.8%).

69. [para 441 | 3.10  Statistical Analysis Plan] "Pairwise comparisons use Welch’s t-test (equation 13), with p-values corrected across the …"
  VERIFIED — Counts check out: the pairwise table has exactly 55 rows = C(11,2), Holm is confirmed by the first step (2.38e-08 x 55 = 1.31e-06), and Cohen's d is beside every p-value. Advisory: TWO groups now fail Shapiro-Wilk, not one (brian2/numpy p = 0.0072, nest/threads2 p = 0.0071), and the generated table carries no flag column - the flagging promise has to be honoured visibly in Chapter 4.

70. [para 445 | 3.10  Statistical Analysis Plan] "Reporting it pairs an unequal-variance test (Welch's t-test, equation 13) with an effect s…"
  VERIFIED — Accurate description of the method actually used (Welch t-test paired with a pooled-SD effect size) and an honest statement of the tension.

72. [para 449 | 3.10  Statistical Analysis Plan] "Kendall’s tau-b compares two rankings of the same n backends by counting concordant pairs …"
  VERIFIED — Correct definition of the statistic actually used (tau-b, tie-corrected), which is what the Experiment 4 coefficients are.

73. [para 449 | 3.10  Statistical Analysis Plan] "It is the statistic behind Experiment 4 (Section 4.10)."
  VERIFIED — Consistent: every Experiment 4 coefficient in the record is a Kendall tau-b.

74. [para 451 | 3.10  Statistical Analysis Plan] "The Pearson correlation coefficient calculated on the rank of data rather than the raw dat…"
  VERIFIED — Correct description of Spearman rho, which is the test used for proxy validation (per-backend rho, 1.00 for nine of eleven, brian2/cython 0.70, brian2/cpp_standalone -0.60; pooled rho = 0.771, p = 5.62e-11 over 50 runs). Advisory: the record calls the comparator the EFFECTIVE OPERATION COUNT (EFLOP); align the wording with "synaptic operation count" or explain that they are the same quantity.

75. [para 454 | 3.10  Statistical Analysis Plan] "Energy proxy: equation (8), with thermal design power stated and sourced in Table 7."
  VERIFIED — TDP is 55 W, sourced to Intel ARK. Confirm Table 7 itself prints the value and source - ANALYSIS records it beside the formula, not in the environment table.

76. [para 454 | 3.10  Statistical Analysis Plan] "It estimates energy rather than measuring it, so Section 3.9 validates its ordering agains…"
  VERIFIED — Accurate: the proxy is validated by rank agreement against the hardware-independent EFLOP count rather than by its absolute joules.

77. [para 455 | 3.10  Statistical Analysis Plan] "Section 4.3's pairwise comparisons carry that caveat, with Cohen's d beside every p-value …"
  VERIFIED — Supported: Cohen's d appears beside every one of the 55 p-values.

78. [para 457 | 3.11 Experiment 4: Sensitivity Analysis] "Experiment 4 varies each in turn and asks whether the ordering survives, discharging the s…"
  VERIFIED — Consistent with the executed Experiment 4 (ordering re-examined under size, metric and session).

79. [para 458 | 3.11 Experiment 4: Sensitivity Analysis] "One design boundary is declared here, not left to the results: Experiment 4 varies one con…"
  VERIFIED — Consistent: each reported condition varies a single factor.

80. [para 458 | 3.11 Experiment 4: Sensitivity Analysis] "Section 6.3 sets out what the joint question would take."
  VERIFIED — Navigational.

81. [para 458 | 3.11 Experiment 4: Sensitivity Analysis] "Section 4.10 therefore reports the number of backends and orderings behind each coefficien…"
  VERIFIED — Supportable from the record: n = 11 backends behind each ordering, and orderings are given at each of the five sizes plus the two sessions.

82. [para 459 | 3.11 Experiment 4: Sensitivity Analysis] "Table 4 Sensitivity conditions, their levels and the assumption each one tests."
  VERIFIED — Table caption.

84. [para 462 | 3.11 Experiment 4: Sensitivity Analysis] "Figure 6 illustrates the test in a schematic way: rather than comparing two sets of number…"
  VERIFIED — Accurate description of a rank-comparison test.

85. [para 464 | 3.11 Experiment 4: Sensitivity Analysis] "Figure 6 How Experiment 4 works."
  VERIFIED — Figure caption.

87. [para 476 | 3.12.2 Comparison with existing dashboard systems] "Table 5 compares the dashboard with representative systems for publishing benchmark result…"
  VERIFIED — Navigational description of Table 5.

88. [para 477 | 3.12.2 Comparison with existing dashboard systems] "Table 5 Comparison of the dashboard with existing benchmark reporting systems."
  VERIFIED — Table caption.

90. [para 481 | 3.12.3 Functional requirements validation] "Table 6 lists the requirements, how each was verified and the result."
  VERIFIED — Navigational.

91. [para 482 | 3.12.3 Functional requirements validation] "Table 6 Functional and non-functional requirements of the dashboard and their verification…"
  VERIFIED — Table caption.

94. [para 493 | 3.12.4 Dashboard Architecture] "Figure 7 shows the dashboard architecture."
  VERIFIED — Navigational.

95. [para 495 | 3.12.4 Dashboard Architecture] "Figure 7 Dashboard architecture."
  VERIFIED — Figure caption.

96. [para 498 | 3.12.4 Dashboard Architecture] "Figure 8 illustrates how the interface appears to a reader, with sample charts in place of…"
  VERIFIED — Describes the figure and honestly flags that its charts are samples, not live output.

104. [para 500 | 3.12.4 Dashboard Architecture] "Figure 8 The dashboard layout."
  VERIFIED — Figure caption.

106. [para 505 | 3.13 Reliability, Validity and Reproducibility] "This check is necessary but not sufficient, a residual risk Section 4.12 discusses."
  VERIFIED — Honest hedge on the equivalence check, consistent with a 35% tolerance that all 11 backends pass without implying identical dynamics.

107. [para 506 | 3.13 Reliability, Validity and Reproducibility] "Absolute timings do not transfer to other machines (Section 3.4)."
  VERIFIED — Design statement, consistent with a single-platform campaign.

111. [para 509 | 3.14 Hardware and Software Environment] "Table 7 Hardware and software environment, captured programmatically at run time."
  VERIFIED — Supported: ANALYSIS captures the machine table and "Package versions, captured at run time".

112. [para 511 | 3.14 Hardware and Software Environment] "Table 7 gives the environment."
  VERIFIED — Navigational.

113. [para 513 | 3.15 Ethical Considerations] "Section 4.8 deals with the third of these."
  VERIFIED — Navigational.

114. [para 515 | 3.16 Conclusion] "Chapter 4 reports what this design produced."
  VERIFIED — Navigational; the design described is the design the campaign executed, subject to the corrections listed below.

---

## SUMMARY — every distinct problem, deduplicated, in priority order

**Blocking factual errors (the stated protocol contradicts the campaign).**

1. **Training is now fully instrumented; the "not observed" limitation is false.** Para 402 ("Memory and processor utilization were not observed during training, a limitation reported in Section 4.6") must go. Processor utilisation, peak memory and the energy proxy were measured for all nine training-capable backends at both budgets (nengo 2246.3% / 1593 MB / 3586 J; spikingjelly 99.5% / 1322 MB / 4922 J; snntorch 99.6% / 1311 MB / 4984 J; nest/4 349.0% / 2331 MB / 261347 J; nest/2 190.5% / 1863 MB / 249606 J; nest/1 100.0% / 1574 MB / 242064 J; brian2/cython 100.0% / 864 MB / 559144 J; brian2/numpy 100.0% / 878 MB / 779635 J; brian2/cpp_standalone 100.0% / 878 MB / 816776 J). FACT_BASE states the declared gap closes. Chapter 3 must instead declare training as instrumented with the same three quantities as inference, and the Section 4.6 limitation pointer must be removed. Note the same paragraph's first sentence already promises time, memory and utilisation — the two sentences currently contradict each other.

2. **"One measurement session" is wrong: there were two.** Para 504 must say one machine, one campaign, with Experiments 1 and 3 measured in two consecutive sessions, which is what makes session-to-session agreement reportable (tau-b 0.964 / 0.927 / 0.818 / 0.964 / 0.964 for N = 100 / 500 / 1,000 / 5,000 / 10,000). The superseded "four sessions" framing is also withdrawn by FACT_BASE — two, not four.

3. **"Experiment 4 needs no new measurement" is obsolete.** Para 461: Experiment 4 now has three comparisons, not two. Ordering across sizes and ordering across metrics are recomputed from the sweep; session-to-session reproducibility required a second full measurement session (per-size orderings session A 0.309 / 0.236 / 0.491 / 0.745, session B 0.309 / 0.345 / 0.491 / 0.818).

4. **The transferability claim over-reaches and contradicts para 352.** Para 506 ("the ordering and scaling behaviour transfer, with Experiment 4 as the evidence"): Experiment 4 is single-machine and single-campaign, so it is no evidence of cross-machine transfer, and it shows the ordering does *not* survive a change of size (tau-b against N = 10,000: 0.309 / 0.236-0.345 / 0.491 / 0.745-0.818; nengo falls 5th to 11th, brian2/cython rises 10th to 2nd) or of metric (energy 0.745, peak memory 0.309). Restate: the scaling exponents and the size-resolved pattern are what replicate (between sessions, tau-b 0.818-0.964 at fixed size); ordering is size- and metric-dependent; cross-machine transfer is untested.

5. **Hidden width: "throughout" is no longer true.** Para 403 must state that hidden = 256 holds for both main budgets and that a partial hidden-500 arm was run for three of the nine backends (nengo 4.95 s/ep at 88.38%, spikingjelly 157.60 s/ep at 97.44%, snntorch 157.94 s/ep at 97.67%), with the remaining six explicitly not run and the arm reported as a partial check only, never as part of the main comparison. The related sentence that the confirmation report merely "proposed" hidden 500 should be extended to say it was partially executed.

6. **Experiment 2 is not a single-factor comparison.** Para 360 must describe it as nine training-capable backends crossed with two training budgets (60,000 / 10,000 / 10 epochs / hidden 256, and 6,000 / 1,000 / 3 epochs / hidden 256), plus the partial hidden-500 arm. While correcting that sentence, state the factorial extent of Experiments 1 and 3 explicitly: 11 backends x 5 sizes, every cell completed.

7. **The scaling fit had five points for every backend.** Para 446's "m is four or five, depending on how many sizes that backend completed" describes a case that did not occur — all eleven backends completed 100 / 500 / 1,000 / 5,000 / 10,000, so m = 5 and df = 3 throughout, which is what para 415's "three degrees of freedom" already assumes (verified: brian2/cython 0.014 +/- 3.182 x 0.009 = [-0.014, 0.043]).

8. **The compile-once assumption is not tested by Experiment 4.** Para 396 must point to Experiment 3 / Section 4.7 instead: the evidence is brian2/cpp_standalone's 1.70039 s at N = 100, k = 0.023 with CI [-0.038, 0.083], and rho = -0.60 against the EFLOP count. Experiment 4's conditions are size, metric and session only.

**Numbers and promises inside otherwise-sound protocol statements.**

9. **Shapiro-Wilk failures are now two, not one, and the flag is not yet visible.** Para 441 promises that a comparison involving a group failing Shapiro-Wilk is flagged. Two groups fail (brian2/numpy p = 0.0072, nest/threads2 p = 0.0071), and the generated pairwise table has no flag column. Keep the promise, update any count of failures wherever it appears, and make sure Chapter 4's table carries the flag.

10. **Do not name brian2/numpy as the flat / indistinguishable-from-zero exemplar.** Para 416's generic wording is safe, but brian2/numpy is now k = 0.017 with CI [0.005, 0.030], which excludes zero. The backends whose intervals contain zero are brian2/cython (k = 0.014, flattest) and brian2/cpp_standalone (k = 0.023).

11. **The TDP +/-30% / utilisation-exponent 0.8-1.2 sensitivity (para 430) is not in the record.** Either produce it or drop it. Note that scaling TDP by a constant cannot change any ranking, so that half of the test is trivially tau = 1 and is not worth claiming.

12. **The R-squared < 0.25 "report as flat" rule (para 415) was never exercised** — the lowest R-squared is 0.322 (brian2/cpp_standalone) and an exponent is reported for all eleven backends. Keep it only as a stated rule, and confirm the analysis and dashboard really implement it.

13. **The equivalence protocol is under-specified in Chapter 3.** Para 388 mentions only that spike counts are compared. State the executed check: at N = 500, a 35% tolerance, 11 of 11 backends pass, closest reference/scalar vs reference/vectorised at 0.0%, furthest nest/threads4 at 15.9% — and use the record's quantity (firing rate) or explain its equivalence with spike count. The related claim that the shared model means cost differences cannot come from the model (para 341) should acknowledge that agreement is within tolerance, not exact.

14. **Table 7 must carry the energy-proxy constant.** Paras 422 and 454 both source the TDP to Table 7. The record fixes E = t x (u_cpu/100) x 55 W with 55 W taken from Intel ARK as the i9-14900HX *processor base power*; confirm Table 7 prints the value and the source, and keep the base-power wording beside "thermal design power".

15. **Naming mismatch for the proxy's comparator.** Para 451 calls it the "synaptic operation count"; the record calls it the effective operation count (EFLOP: 11,000 / 55,000 / 110,000 / 550,000 / 1,100,000). Align the terms. The validation values themselves are pooled rho = 0.771, p = 5.62e-11 over 50 runs, with per-backend rho = 1.00 for nine of eleven, brian2/cython 0.70, brian2/cpp_standalone -0.60.

16. **Counts Chapter 3 should state outright, since Chapter 4 now leans on them:** 11 execution backends over 5 simulators plus a plain-NumPy control contributing 2 of those backends; 9 training-capable backends; 5 network sizes; 5 warm-up plus 5 retained runs per condition (only the 5 retained runs are visible in the extracted text, via r1...r5 and C(11,2) = 55); two measurement sessions; two training budgets.

**Unverifiable from the record — resolve before submission.**

17. **Dashboard behaviour (paras 469, 481, 483, 490, 498) cannot be checked against the campaign record at all, and the re-run has moved everything the homepage displays.** Re-verify against the current build: the sidebar's page links and Export all data control; the top bar's page name and load time; that de-selecting a simulator propagates to charts, tables and headline figures on every page; the headline band's four figures and its stated exclusions (now fastest inference reference/vectorised 0.00130 s, lowest peak memory nest/threads1 91.0 MB, flattest scaling brian2/cython k = 0.014, best MNIST accuracy spikingjelly/cpu 97.46%, and training energy/memory newly available); that there are exactly six preview cards and where they point; the footer's run, condition and backend counts, which change with two sessions and a second training budget; and the claim that verification established the specification was met.

18. **Undocumented incidents.** Three sentences assert events the record does not contain: a query not restricted to the measurement machine (para 359), an earlier sampled utilisation measurement that was defective (para 420), and "all three" deviations documented in Section 4.8 (para 409). Either supply the deviation log or remove them.

19. **The projection that Table 12 sets beside the measurement (para 408) is not in the record.** The full budget was executed for all nine backends; the projected per-image cost is not preserved. Supply the projection or present the full budget purely as measured.

20. **Append-only database and a read-only dashboard (para 345) are asserted, not shown.** Per-run storage is established (benchmarks.db, every individual run retained). Evidence needed: the write path/schema and the dashboard's read-only data access.

21. **Release and offline-rendering claims (para 507).** Public release of the harness, exact commands, database and analysis pipeline, and the claim that the interface renders with no internet access, both need external evidence: an archive location with a clean-clone reproduction of ANALYSIS.md, and a networking-disabled render test.

22. **Literature and provenance claims** — the Section 2.6 deployment argument (para 372), the Section 2.8 dashboard principles (para 469), the requirement categories of Rabiei and Almasi [81] (para 481), and the steady-state citations [60], [61] (paras 342, 410) — lie outside the campaign record and can only be checked against the cited sources.

23. **Equations (7)/(8) reduction (para 424) and the Poisson expected-spike fallback (para 429)** cannot be checked from the supplied material. The only fixed form in the record is E = t x (u/100) x 55 W; provide the typeset equations and Table 2's input rate, and confirm that an adapter reporting only output spikes actually exists in the harness.

24. **Advisory, no wording change strictly required:** para 376 says the network is used "in all five simulators" and silently omits the two plain-NumPy control backends that also run it; para 410's warm-up sentence sits in the Experiment 2 section, where the record shows a single run per backend per budget with no dispersion — make sure it is not read as promising warm-up or replication in training.

### Verdict counts

| Verdict | Count |
|---|---|
| VERIFIED | 83 |
| MUST CHANGE | 8 |
| CANNOT VERIFY | 23 |
| **Total** | **114** |


# Chapter 4 — Results and Discussion

# Chapter 4 factual audit against FACT_BASE.md / ANALYSIS.md

Campaign of record: 21-27 September 2026, machine LT68. Every value below is taken from
`/root/v3/FACT_BASE.md` and `/root/v3/ANALYSIS.md`; anything derived (rank agreements, per-neuron
memory, utilisation recovered from the energy proxy) is marked as derived and the derivation given.
All 139 sentences of `/root/v3/claims_ch4.json` were checked; none sampled.

| Verdict | Count |
|---|---|
| MUST CHANGE | 53 |
| CANNOT VERIFY | 34 |
| VERIFIED | 52 |
| **Total** | **139** |

Conventions used in the corrections: memory per neuron is (growth in MB x 1024) / 10,000, the
convention the chapter itself uses; Kendall tau-b over eleven backends has 55 pairs, so the number
of reversed pairs is 55 x (1 - tau) / 2; utilisation across the sweep is recovered from
E = t x (u/100) x 55 W, which reproduces the tabulated Experiment 1 values to within about 7%.

---

## MUST CHANGE (53)

[para 525 | 4.2 The Measurement Campaign] "Every figure, table and coefficient in this chapter comes from one measurement session on …"
MUST CHANGE - 'one measurement session' is wrong for Experiment 4: the fact base states the sensitivity orderings were 'measured twice' (session A and session B), and the reproducibility taus (0.964 / 0.927 / 0.818 / 0.964 / 0.964) are by definition cross-session. Correct to: one campaign on one machine (LT68), with Experiment 4's orderings measured in two sessions inside that campaign; nothing pooled across machines.

[para 540 | 4.3 Experiment 1: Inference Cost at the Reference Size] "The fastest simulator configuration is NEST with four threads at 2.120 ms."
MUST CHANGE - 'NEST with four threads at 2.120 ms' - the fastest simulator configuration is NEST with TWO threads at 2.13 ms (0.00213 s); NEST/threads4 is 0.00220 s (2.20 ms). Also note Holm does not separate the NEST thread counts (threads1 vs threads2 p = 0.723, threads2 vs threads4 p = 0.723), so the fact base forbids presenting any of them as a separated winner.

[para 540 | 4.3 Experiment 1: Inference Cost at the Reference Size] "The slowest is Brian2's C++ standalone target at 1.669 s, a 787-fold difference."
MUST CHANGE - '1.669 s, a 787-fold difference' - the slowest is brian2/cpp_standalone at 1.70039 s. Against the fastest simulator configuration (NEST/threads2, 0.00213 s) that is 798x; against the fastest backend overall (reference/vectorised, 0.00130 s) it is 1,308x.

[para 540 | 4.3 Experiment 1: Inference Cost at the Reference Size] "The spread across directly comparable simulator configurations is then 67.3 times, from NE…"
MUST CHANGE - '67.3 times, from NEST with four threads at 2.120 ms to Brian2's NumPy target at 142.663 ms' - the fact base's spread excluding the compile-dominated target is 106.88x (0.13933 s / 0.00130 s), i.e. Brian2/CYTHON at 139.33 ms against the vectorised control at 1.30 ms. Restricted to simulator configurations only it is 65.4x (0.13933 / 0.00213). Brian2/NumPy is 133.18 ms, not 142.663 ms, and is not the slowest non-compiling backend.

[para 540 | 4.3 Experiment 1: Inference Cost at the Reference Size] "At this size the vectorized NumPy control, at 1.376 ms, is faster than every simulator."
MUST CHANGE - '1.376 ms' - the vectorised NumPy control is 1.30 ms (0.00130 s). The superlative itself is correct: it is rank 1 at N = 100, ahead of every simulator.

[para 541 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Run-to-run spread is modest: the coefficient of variation ranges from 1.6% (Brian2/Cython)…"
MUST CHANGE - '1.6% (Brian2/Cython) to 11.7% (NEST with one thread)' - the CV column runs from 4.8% (reference/scalar) to 20.1% (NEST with two threads). Brian2/Cython is 7.8% and NEST/threads1 is 12.7%; 1.6% appears nowhere.

[para 541 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Nengo's coefficient was 58.0% in the initial campaign against 11.2% here, for a reason tha…"
MUST CHANGE - '58.0% in the initial campaign against 11.2% here' - Nengo's CV in this campaign is 7.8%. There is no earlier campaign to cite: the thesis must report only the 21-27 September 2026 campaign, so the comparison must be deleted rather than restated.

[para 542 | 4.3 Experiment 1: Inference Cost at the Reference Size] "The Shapiro-Wilk test fails to reject normality for ten of the eleven backends and rejects…"
MUST CHANGE - 'ten of the eleven backends ... rejects it for NEST with one thread (p = 0.038)' - the fact base says TWO of eleven fail Shapiro-Wilk: brian2/numpy (W = 0.6884, p = 0.0072) and nest/threads2 (W = 0.6877, p = 0.0071). So nine of eleven fail to reject, and NEST/threads1 is not one of the failures (its p is 0.1415).

[para 542 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Levene's test (W = 6.35, p = 6.0e-06) shows that variances differ, so Welch's ANOVA is use…"
MUST CHANGE - Both tests are stale. Levene: W = 9.38, p = 4.285e-08 (not W = 6.35, p = 6.0e-06). Welch's ANOVA: F(10, 17.10) = 451.58, p = 1.143e-18, eta-squared = 0.9930 (not F(10, 17.22) = 1898.78, p = 3.9e-24, eta-squared = 0.9986). This is the single most-cited statistic in the chapter.

[para 542 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Of the fifty-five Holm-corrected pairwise Welch tests, 50 separate at the 0.05 level."
MUST CHANGE - '50 separate' - 51 of the 55 Holm-corrected pairs separate at 0.05. Exactly four do not: nest/threads1 vs threads4 (p = 0.419), brian2/cython vs brian2/numpy (p = 0.419), nest/threads1 vs threads2 (p = 0.723), nest/threads2 vs threads4 (p = 0.723).

[para 562 | 4.4 Experiment 3: Reversing the Order and Scaling] "Nengo is steepest at k = +1.550, more than proportional to network size."
MUST CHANGE - 'k = +1.550' - Nengo's exponent is 1.544 (95% CI [0.879, 2.210]). 'Steepest' is correct.

[para 562 | 4.4 Experiment 3: Reversing the Order and Scaling] "NEST follows at k = +1.199, +1.195 and +1.151 with one, four and two threads, and the scal…"
MUST CHANGE - Every value and the ordering are wrong. NEST is k = 1.159 (one thread), 1.135 (two threads), 1.133 (four threads) - so descending order is one, TWO, four, not one, four, two - and the scalar NumPy control is k = 0.982, not +0.993.

[para 562 | 4.4 Experiment 3: Reversing the Order and Scaling] "At the other end, Brian2's three targets sit at k = +0.048, +0.023 and +0.001."
MUST CHANGE - 'k = +0.048, +0.023 and +0.001' - Brian2's three targets are 0.023 (cpp_standalone), 0.017 (numpy) and 0.014 (cython). Note the flattest backend in the study is now brian2/cython at 0.014, 95% CI [-0.014, 0.043].

[para 563 | 4.4 Experiment 3: Reversing the Order and Scaling] "Four fits follow a power law only loosely: Brian2/C++ standalone (R² = 0.013), Brian2/Cyth…"
MUST CHANGE - Every R2 is stale: brian2/cpp_standalone 0.322 (not 0.013), brian2/cython 0.454 (not 0.330), brian2/numpy 0.869 (not 0.688), snntorch 0.862 (not 0.866). The same four backends are still the four loosest fits, but NumPy (0.869) now fits slightly BETTER than snnTorch (0.862), so the listed order reverses.

[para 564 | 4.4 Experiment 3: Reversing the Order and Scaling] "Nengo falls from rank 5 to rank 11 between the smallest and the largest network, Brian2/Nu…"
MUST CHANGE - Two of the four movements are wrong: Brian2/NumPy rises from rank 9 to rank 3 (not to 2) and Brian2/Cython from rank 10 to rank 2 (not to 3) - the chapter has the two Brian2 targets swapped at N = 10,000 (cython 0.14853 s beats numpy 0.14868 s). Nengo 5 -> 11 and NEST 2-4 -> 4-6 are correct.

[para 564 | 4.4 Experiment 3: Reversing the Order and Scaling] "Among simulator configurations, the four fastest at 100 neurons (NEST with four, two and o…"
MUST CHANGE - The substantive claim (the four fastest simulator configurations differ at the two ends) is correct and the SET is right, but the N = 10,000 list is in the wrong rank order: it is Brian2/Cython (0.14853 s), then Brian2/NumPy (0.14868 s), then NEST with four threads (0.35302 s), then NEST with two (0.40209 s).

[para 565 | 4.4 Experiment 3: Reversing the Order and Scaling] "Across all eleven backends, Kendall's tau-b between the orderings at one hundred and at te…"
MUST CHANGE - '0.273' - Kendall tau-b between the N = 100 and N = 10,000 orderings is 0.309, in both measured sessions.

[para 565 | 4.4 Experiment 3: Reversing the Order and Scaling] "A tau of one would mean identical orderings; at 0.273, only 35 of the 55 pairs are ordered…"
MUST CHANGE - The pair counts follow the stale tau. At tau-b = 0.309 over 55 pairs, 36 pairs are ordered the same way and 19 the opposite way (not 35 and 20).

[para 566 | 4.4 Experiment 3: Reversing the Order and Scaling] "At any fixed size, the ordering from another session agrees with this session's at tau = 0…"
MUST CHANGE - Three errors. (i) Fixed-size session-to-session agreement is tau 0.818 to 0.964 (0.964 / 0.927 / 0.818 / 0.964 / 0.964 at N = 100 / 500 / 1,000 / 5,000 / 10,000), not 0.745 to 1.000 - no tau of 1.000 was measured. (ii) There are two sessions, not several, and no 'twin session run ten minutes later' or '0.891 or better' figure exists in the fact base. (iii) The within-session agreement between N = 100 and N = 10,000 is 0.309 in both sessions, not 'tau = 0.200 to 0.273'.

[para 566 | 4.4 Experiment 3: Reversing the Order and Scaling] "Absolute times reproduce less well: the twin session lies within −21% to +15% of this one,…"
MUST CHANGE - Nothing in this sentence is measurable from the new campaign: there is no absolute-time session-to-session delta ('-21% to +15%') and no comparison with earlier campaigns. The fact base allows two sessions of ONE campaign only, so 'NEST ... ran 1.4 to 2.8 times slower than in two earlier campaigns' must be deleted, not restated.

[para 573 | 4.4 Experiment 3: Reversing the Order and Scaling] "Here NEST's exponents are 1.151 to 1.199 at sizes two orders of magnitude smaller, where t…"
MUST CHANGE - '1.151 to 1.199' - NEST's exponents are 1.133 to 1.159 (threads4 1.133, threads2 1.135, threads1 1.159).

[para 579 | 4.5 Memory and Processor Utilization] "At the reference size the backends split into two groups: NEST at 91–94 MB and every other…"
MUST CHANGE - 'every other backend at 629-694 MB' - the non-NEST band at N = 100 is 631-696 MB (brian2/numpy 631.3 MB up to reference/scalar 696.4 MB). The NEST band 91-94 MB is correct (91.0 / 91.9 / 93.6 MB).

[para 579 | 4.5 Memory and Processor Utilization] "At the largest network, peak resident set size ranges from 641.7 MB (Brian2/NumPy) to 2,20…"
MUST CHANGE - Both endpoints are stale: at N = 10,000 peak RSS runs from 644.7 MB (brian2/numpy) to 2,206.1 MB (nengo), not 641.7 MB to 2,203.8 MB.

[para 581 | 4.5 Memory and Processor Utilization] "Processor utilization at the reference size ranges from 100.0% to 794.1%."
MUST CHANGE - '100.0% to 794.1%' - utilisation at N = 100 runs from 100.0% (brian2/numpy and brian2/cython) to 780.5% (brian2/cpp_standalone).

[para 581 | 4.5 Memory and Processor Utilization] "Eight backends use one core; NEST with two and four threads (239.5% and 376.4%) and Brian2…"
MUST CHANGE - All three values are stale: NEST with two threads is 208.4% (not 239.5%), NEST with four threads is 521.3% (not 376.4%) and brian2/cpp_standalone is 780.5% (not 794.1%). The count 'eight backends use one core' is correct (eight backends read 100.0-103.3%).

[para 582 | 4.5 Memory and Processor Utilization] "Across its three thread counts, NEST grows from roughly 91–94 MB at 100 neurons to 886–923…"
MUST CHANGE - Two of three ranges are stale. At N = 10,000 NEST is 891-925 MB (891.3 / 897.8 / 925.0), not 886-923 MB, so the increase is 800-831 MB, not 796-830 MB. The per-neuron figure 81-85 KB is correct (81.95 / 82.51 / 85.14 KB at 1 MB = 1024 KB).

[para 582 | 4.5 Memory and Processor Utilization] "Nengo grows most, from 641 to 2,204 MB, or 160 KB per neuron. snnTorch and SpikingJelly gr…"
MUST CHANGE - One stale endpoint: Nengo grows from 641.6 MB to 2,206.1 MB, not to 2,204 MB. The rest is confirmed: 160.2 KB per neuron; snnTorch +381.5 MB and SpikingJelly +383.2 MB, i.e. 39.07 and 39.24 KB per neuron.

[para 582 | 4.5 Memory and Processor Utilization] "Brian2 barely grows: its NumPy target goes from 629 to 642 megabytes across the whole swee…"
MUST CHANGE - Every number is stale: brian2/numpy goes from 631.4 MB to 644.7 MB (not 629 to 642), which is 1.36 KB per neuron (not 1.32), and brian2/cython goes from 638.8 to 646.8 MB, which is 0.82 KB per neuron (not 0.45).

[para 583 | 4.5 Memory and Processor Utilization] "At 100 neurons NEST has the smallest footprint and SpikingJelly the largest, yet across th…"
MUST CHANGE - Three problems. (i) The per-neuron values are 0.82 (Cython) and 1.36 (NumPy) KB, not 0.45 and 1.32. (ii) The ratio is 60 to 63 times brian2/numpy (81.95 / 1.36 = 60.2 up to 85.14 / 1.36 = 62.6), not 62 to 65 times. (iii) The superlative is wrong: at N = 100 the largest footprint is reference/scalar at 696.4 MB (then reference/vectorised 695.7 MB); SpikingJelly's 694.0 MB is only the largest among SIMULATORS. 'NEST smallest' (91.0 MB) and 'second only to Nengo' (160.2 KB per neuron) are correct.

[para 585 | 4.5 Memory and Processor Utilization] "NEST's utilization follows its thread count (about 100%, 200–224% and 392–485% for one, tw…"
MUST CHANGE - The four-thread band is contradicted by the fact base: at the reference size NEST with four threads reads 521.3%, above the stated ceiling of 485%, and NEST with two threads reads 208.4%. (Sweep-wide CPU % is not tabulated; recovering it from E = t x (u/100) x 55 gives roughly 100% for one thread, 191-300% for two and 394-510% for four, so both quoted bands are too narrow.)

[para 585 | 4.5 Memory and Processor Utilization] "SpikingJelly peaks at mid-sized networks; snnTorch, Brian2's NumPy and Cython targets and …"
MUST CHANGE - 'the C++ standalone target keeps about eight cores busy at every size' - it reads 780.5% (7.8 cores) at the reference size, but recovered from the energy table its sweep values are about 600-760% (6.0-7.6 cores), lowest at N = 10,000. Say 'about six to eight cores'. The rest of the sentence is confirmed: SpikingJelly peaks mid-sweep (~627% at N = 500, ~595% at N = 1,000, falling to ~132% at N = 10,000) and snnTorch, Brian2/NumPy, Brian2/Cython and both controls stay near one core.

[para 586 | 4.5 Memory and Processor Utilization] "At 10,000 neurons two and four threads are indistinguishable (0.498 s and 0.504 s) and bot…"
MUST CHANGE - Almost every number and the comparison itself are stale. At N = 10,000 NEST is 0.40209 s (two threads), 0.35302 s (four threads) and 0.58103 s (one thread). Four threads is 12% FASTER than two, so they are not indistinguishable and the fourth thread does shorten the run; and the gain over one thread is 31% (two threads) and 39% (four threads), not 'about 26%'. At N = 500 four threads is 5.6% faster than two (0.00778 vs 0.00824) and at N = 1,000 it is 19.7% faster (0.01422 vs 0.01770), not 'about 15%' at both. Also: the only pairwise tests in the fact base are at N = 100, so 'indistinguishable' at N = 10,000 has no statistical support.

[para 594 | 4.6 Experiment 2: Learning Cost and Accuracy] "At the same fixed budget, training time spans more than three orders of magnitude, from 0.…"
MUST CHANGE - 'from 0.87 s for Nengo's solve to 1,606.18 s for Brian2's C++ standalone target' - at the 6,000 / 1,000 / 3-epoch budget the fact base gives Nengo 1.7 s and brian2/cpp_standalone 1,416.4 s per epoch. That ratio is about 833x, i.e. just UNDER three orders of magnitude, so the 'more than three orders of magnitude' claim fails on per-epoch figures (it holds only if the three-epoch total of 4,249 s is used against Nengo's 1.7 s - state which basis is meant).

[para 600 | 4.6 Experiment 2: Learning Cost and Accuracy] "For the gradient libraries it overestimates by about half, and for Nengo by a factor of 2.…"
MUST CHANGE - All three quantities are stale. snnTorch costs 1.717 ms per image at 6,000 (10.3 s/epoch) and 1.516 ms at 60,000 (90.94 s/epoch), not 2.416 and 1.535 ms. The gradient libraries' projection therefore overestimates by 7% (SpikingJelly, 1.600 vs 1.499 ms) to 13% (snnTorch), not 'about half'. Nengo's overestimates by a factor of 5.9 (0.283 vs 0.048 ms per image), not 2.5.

[para 600 | 4.6 Experiment 2: Learning Cost and Accuracy] "For the plasticity rules it errs in both directions, between 0.84 and 1.16 times the measu…"
MUST CHANGE - 'between 0.84 and 1.16 times' - the plasticity rules' projection ratios are 0.95 to 1.02: brian2/cpp_standalone 0.954, brian2/numpy 0.992, nest/threads2 0.995, brian2/cython 1.018, nest/threads1 1.000, nest/threads4 1.024. 'Errs in both directions' is correct.

[para 601 | 4.6 Experiment 2: Learning Cost and Accuracy] "Because the rules differ by orders of magnitude in sample efficiency and in cost per sampl…"
MUST CHANGE - Both endpoints are stale: at the 6,000 / 1,000 budget Nengo takes 1.7 s (not 'under a second') and brian2/cpp_standalone takes 1,416.4 s per epoch, i.e. 23.6 minutes per epoch and 70.8 minutes for the three epochs - not 'almost 27 minutes'.

[para 602 | 4.6 Experiment 2: Learning Cost and Accuracy] "Given similar accuracy, cost separates them: 13.79 against 14.50 seconds per epoch."
MUST CHANGE - '13.79 against 14.50 seconds per epoch' - at the fixed budget the fact base gives SpikingJelly 9.6 s and snnTorch 10.3 s per epoch; at the full budget 89.94 and 90.94 s. The ordering (SpikingJelly cheaper) survives; the numbers do not.

[para 605 | 4.6 Experiment 2: Learning Cost and Accuracy] "The budget was tested separately: at the full reference budget NEST reaches 8.32–8.41% and…"
MUST CHANGE - Both ranges are stale: at the full reference budget NEST reaches 8.24-8.50% (threads2 8.24, threads4 8.32, threads1 8.50) and Brian2 9.57-9.61% (cpp_standalone 9.57, cython and numpy 9.61). Also, with no fixed-budget accuracies in the fact base, 'the ordering among thread counts and backends unchanged' cannot be supported as written.

[para 608 | 4.7 Compilation Reported as Computation] "Brian2's C++ standalone target took 1.6782 s at N = 100 and 1.6911 s at N = 10,000 (k = +0…"
MUST CHANGE - Four errors in one sentence. Runtime: 1.78560 s at N = 100 and 2.12605 s at N = 10,000 (Experiment 1's own median for this target is 1.70039 s), not 1.6782 and 1.6911 s. Exponent: k = 0.023, 95% CI [-0.038, 0.083], not +0.001. Fit: R2 = 0.322, not 0.013. Utilisation: 780.5% at the reference size and roughly 600-760% across the sweep, not 790-799%.

[para 608 | 4.7 Compilation Reported as Computation] "The interpreted targets move in the expected direction, but only weakly (NumPy: k = +0.023…"
MUST CHANGE - Both targets are stale and the pairing is reversed: brian2/NUMPY is k = 0.017, 95% CI [0.005, 0.030], R2 = 0.869; brian2/CYTHON is k = 0.014, 95% CI [-0.014, 0.043], R2 = 0.454. So Cython, not NumPy, is the flattest backend in the study, NumPy is the only Brian2 target whose CI excludes zero, and Cython's fit is the weak one.

[para 632 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "The proxy increases monotonically with the theoretical workload for eight of the eleven ba…"
MUST CHANGE - 'eight of the eleven backends' - the fact base gives rho = 1.00 for NINE of eleven. brian2/numpy is one of them (rho = 1.00, exact p = 0.0167), so it must move out of the exception list and into this one; only brian2/cython (0.70) and brian2/cpp_standalone (-0.60) remain below 1.00.

[para 632 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "The Brian2 targets are the exceptions: NumPy agrees strongly (rho = +0.900, p = 0.083), Cy…"
MUST CHANGE - Two of three values are stale and the framing over-counts the exceptions. brian2/numpy is rho = +1.000, p = 0.0167 (not +0.900, p = 0.083); brian2/cython is +0.700, p = 0.2333 (correct); brian2/cpp_standalone is -0.600, p = 0.3500 (not -0.400, p = 0.517). Only TWO Brian2 targets are exceptions now, not all three.

[para 632 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "For every backend whose runtime is driven by simulation, the proxy therefore preserves the…"
MUST CHANGE - Over-claims against the fact base. The rank-agreement table marks only brian2/cpp_standalone as compile-dominated, and the pooled test counts brian2/cython among the compute-bound backends (50 runs = 10 backends x 5 sizes), yet brian2/cython's rho is 0.70, not 1.00. Restate as: nine of eleven backends reproduce the workload ordering exactly (rho = 1.000). The 'joule values remain unvalidated' caveat is correct and should stay.

[para 640 | 4.10 Experiment 4: Sensitivity of the Ordering] "In the three left bars, between 31 and 38 per cent of the ordered pairs are reversed relat…"
MUST CHANGE - 'between 31 and 38 per cent' - with tau-b of 0.309 / 0.236 / 0.491 (session A) the reversed shares are 34.6% / 38.2% / 25.4%, so the range is 25 to 38 per cent; in session B (0.309 / 0.345 / 0.491) it is 25 to 35 per cent. The lower bound of 31% is wrong either way - the N = 1,000 bar reverses only a quarter of the pairs.

[para 650 | 4.10 Experiment 4: Sensitivity of the Ordering] "Against the ordering at N = 10,000, agreement is tau = 0.273 at N = 100, 0.236 at N = 500,…"
MUST CHANGE - Two values are stale and two sessions are mixed. The fact base gives session A 0.309 / 0.236 / 0.491 / 0.745 and session B 0.309 / 0.345 / 0.491 / 0.818 for N = 100 / 500 / 1,000 / 5,000. So 0.273 should be 0.309 and 0.382 should be 0.491; and quoting 0.236 (session A) beside 0.818 (session B) mixes the two replicates - report one session, or both side by side.

[para 650 | 4.10 Experiment 4: Sensitivity of the Ordering] "At the three smallest sizes the ordering has little in common with that at the largest; ag…"
MUST CHANGE - The 'weakest at 500 neurons rather than at the smallest size' pattern does not replicate. It holds in session A (0.236 at N = 500 below 0.309 at N = 100) but reverses in session B (0.345 at N = 500 ABOVE 0.309 at N = 100, so the minimum is at the smallest size). The claim must be qualified as a session-A feature, or dropped. 'Most of it returns only at 5,000' is supported (0.745 / 0.818).

[para 650 | 4.10 Experiment 4: Sensitivity of the Ordering] "Low agreement at 100 neurons appears in each of the four sessions (0.200 to 0.273; Section…"
MUST CHANGE - 'each of the four sessions (0.200 to 0.273)' - there are two sessions, not four, and both give exactly tau = 0.309 at N = 100. Neither 0.200 nor 0.273 was measured.

[para 651 | 4.10 Experiment 4: Sensitivity of the Ordering] "Ordered by fitted exponent, the backends run from Nengo (k = +1.550) through NEST, Spiking…"
MUST CHANGE - Every value and part of the ordering are wrong. Nengo k = 1.544 (not +1.550); the vectorised control is 0.732 (not +0.735); the Brian2 span is 0.023 down to 0.014 (not '+0.048 to +0.001'). And the sequence is Nengo, NEST (1.159 / 1.135 / 1.133), the SCALAR CONTROL (0.982), SpikingJelly (0.960), snnTorch (0.921), the vectorised control (0.732) - the scalar control comes BEFORE SpikingJelly, not after it.

[para 653 | 4.10 Experiment 4: Sensitivity of the Ordering] "Against runtime at the largest size, the energy-proxy ordering agrees at tau = 0.782, peak…"
MUST CHANGE - Both fact-base values are stale and the third is unsupported. Against runtime at N = 10,000 the energy proxy agrees at tau = 0.745 (not 0.782) and peak memory at 0.309 (not +0.418). The scaling-exponent tau is not in the fact base at all; recomputed from the k column against the N = 10,000 runtimes it is 0.309, not 0.236.

[para 653 | 4.10 Experiment 4: Sensitivity of the Ordering] "Energy agrees most because the proxy is largely rescaled runtime (Section 4.9), and every …"
MUST CHANGE - The 'every pair' claim is false. The energy ordering reverses 7 of the 55 pairs (tau = 0.745), and one of them involves neither NEST/2 nor NEST/4: SpikingJelly vs snnTorch, where snnTorch is slower (0.77200 s vs 0.76422 s) but cheaper on the proxy (41.815 J vs 55.570 J). Say 'six of the seven reordered pairs involve NEST with two or four threads'. 'Energy agrees most' is correct (0.745 against 0.309 for memory).

[para 655 | 4.10 Experiment 4: Sensitivity of the Ordering] "Across the 55 scalability conditions, Spearman's rho between the energy proxy and the EFLO…"
MUST CHANGE - 'Across the 55 scalability conditions ... 0.645' - the pooled figure is rho = 0.771, p = 5.62e-11, over 50 runs pooled across the COMPUTE-BOUND backends (the compile-dominated target is excluded, which is exactly why it is 50 observations and not 55). The clause 'replacing an earlier value (0.716 over 50 observations)' must be deleted: the thesis may report only this campaign.

[para 657 | 4.11 Response to the Research Questions] "The five simulators separate clearly on every dimension measured in Sections 4.3 to 4.7, b…"
MUST CHANGE - Four errors. tau = 0.236 at N = 500 and 0.818 at N = 5,000 come from different sessions (A: 0.236 / 0.745; B: 0.345 / 0.818). 'A pattern seen in all four sessions' - there are two sessions. The metric taus are 0.745 (energy) and 0.309 (peak memory), not 0.782 and +0.418; the third value 0.236 is not in the fact base (recomputed exponent-vs-runtime tau = 0.309). 'The five simulators' is correct (Brian2, NEST, Nengo, snnTorch, SpikingJelly = nine backends, plus two controls = eleven).

[para 658 | 4.11 Response to the Research Questions] "Across the 55 paired observations, Spearman's rho with EFLOP is 0.645, driven by network s…"
MUST CHANGE - 'Across the 55 paired observations ... 0.645' - rho = 0.771 over 50 paired observations, p = 5.62e-11, pooled across compute-bound backends.

---

## CANNOT VERIFY (34)

[para 520 | 4.1 Introduction] "This chapter describes what the Chapter 3 design produced and compares it with the literat…"
CANNOT VERIFY - Chapter roadmap; contains no measured quantity. Nothing in the fact base bears on it.

[para 521 | 4.1 Introduction] "The energy proxy is then validated, and Section 4.11 answers the research questions."
CANNOT VERIFY - Chapter roadmap. Nothing to check; the fact base does contain the proxy validation the sentence promises.

[para 523 | 4.1 Introduction] "Section 4.8 is placed before the energy and sensitivity analyses because one of the instru…"
CANNOT VERIFY - Asserts that an instrument defect forced Experiments 1 and 3 to be re-measured. The fact base records no defect history. Evidence needed: the defect register (the chapter's Table 13) and the run-group provenance showing which runs were discarded and re-measured.

[para 525 | 4.2 The Measurement Campaign] "Experiments 1 and 3, and every utilization, energy and sensitivity figure built on them, c…"
CANNOT VERIFY - Same provenance claim. Evidence needed: the instrument-replacement record plus the mapping from run groups to the corrected utilisation instrument. The fact base records only that one campaign (21-27 September 2026) exists on machine LT68.

[para 526 | 4.2 The Measurement Campaign] "The figures rest on 150 conditions from 678 measured runs: 132 inference and scalability c…"
CANNOT VERIFY - No condition or run counts appear in the fact base (no 150, 678, 132, 660 or 18). Evidence needed: the run-group inventory from benchmarks.db. NOTE: the fact base implies 9 + 9 + 3 = 21 training conditions (full budget, repeat budget and the partial hidden = 500 run), which is at odds with '18 training conditions'.

[para 526 | 4.2 The Measurement Campaign] "The database holds a further 462 condition records that appear in no figure."
CANNOT VERIFY - The '462 further condition records' figure is not in the fact base. Evidence needed: a database inventory separating figure-bearing from excluded records.

[para 526 | 4.2 The Measurement Campaign] "They are development runs on an earlier cloud instance, incomplete early attempts on this …"
CANNOT VERIFY - The provenance of the excluded records (cloud instance, early attempts, replications) is not in the fact base. Evidence needed: run-group metadata with host and timestamp per group. Note that the fact base does support exactly two sessions being used for the reproducibility check.

[para 527 | 4.2 The Measurement Campaign] "All eleven backends finished inference and all five sizes of the scalability sweep, includ…"
CANNOT VERIFY - The first half is confirmed: all eleven backends have complete rows at all five sizes, Nengo included at N = 10,000 (4.15104 s). The clause 'which an earlier attempt could not complete' cites a campaign the thesis may no longer report - delete it, or supply the earlier run record as documented provenance.

[para 528 | 4.2 The Measurement Campaign] "Every condition followed the protocol of Section 3.6: five discarded warm-up runs, five re…"
CANNOT VERIFY - Two of three elements are confirmed - five retained runs (n = 5 in the Shapiro-Wilk table) and setup cost timed separately (separate 'Setup median' column). The five DISCARDED warm-up runs are not recorded anywhere in the fact base. Evidence needed: the harness protocol log or run-level records showing the discarded warm-ups.

[para 530 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Both Brian2 and NEST are reported across all three of their backends rather than one arbit…"
CANNOT VERIFY - 'their dispersion is larger than most other simulators'' has no counterpart in the fact base, which computes no per-simulator dispersion measure. Read as run-to-run CV the claim is actually contradicted: Brian2's CVs are 5.3 / 7.8 / 9.0%, below the 11.7% median, while NEST's are 12.7 / 20.1 / 17.3%. Evidence needed: an explicit definition of 'dispersion' (CV, or spread of medians across a simulator's own backends) and the corresponding computation.

[para 551 | 4.4 Experiment 3: Reversing the Order and Scaling] "Figure 10 Runtime against network size, both axes logarithmic."
CANNOT VERIFY - Caption describing a plotting choice (logarithmic axes); the fact base cannot confirm how the figure was drawn. The underlying runtime-vs-size data exists for all eleven backends.

[para 579 | 4.5 Memory and Processor Utilization] "NEST runs in its own worker process, whereas the other backends run in the main benchmark …"
CANNOT VERIFY - The '629 MB' interpreter-and-libraries baseline is not measured in the fact base; the smallest non-NEST peak RSS recorded is 631.3 MB (brian2/numpy at N = 100), and no import-only baseline exists. Evidence needed: a measured RSS for the harness with libraries imported and no simulation, plus documentation that NEST runs in a separate worker process.

[para 580 | 4.5 Memory and Processor Utilization] "Documentation-based claims that the machine-learning libraries have the smallest footprint…"
CANNOT VERIFY - Cites documentation-based claims from Chapter 2's literature; external to the campaign. Evidence needed: the Chapter 2 sources. The contrast drawn (process-level residency) is consistent with the fact base's peak-RSS measurements.

[para 581 | 4.5 Memory and Processor Utilization] "Across the 660 runs of the session the median is 100.4% (middle half 100.0–189.1%), and ev…"
CANNOT VERIFY - Neither the run count nor the utilisation distribution is in the fact base: there is no '660 runs', no median 100.4% and no interquartile range 100.0-189.1%. Evidence needed: the run-level CPU % dump for the campaign's run groups.

[para 602 | 4.6 Experiment 2: Learning Cost and Accuracy] "The two surrogate-gradient libraries reach the highest accuracies (SpikingJelly 94.10%, sn…"
CANNOT VERIFY - No fixed-budget accuracies exist in the fact base, so 94.10% and 93.20% cannot be checked. At the full budget the superlative does hold: SpikingJelly 97.46% and snnTorch 97.24% are the two highest of the nine. Evidence needed: the 6,000 / 1,000 / 3-epoch accuracy table.

[para 603 | 4.6 Experiment 2: Learning Cost and Accuracy] "Nengo reaches 85.50% by a route that is different in kind: one closed-form least-squares s…"
CANNOT VERIFY - '85.50%' is a fixed-budget accuracy and the fact base contains no fixed-budget accuracies; its full-budget value is 85.44%. Evidence needed: the fixed-budget accuracy table. (The closed-form, no-epoch route is independently supported by util_wall_s = 2.9 s equalling the 2.90 s 'per epoch'.)

[para 604 | 4.6 Experiment 2: Learning Cost and Accuracy] "The gradient libraries gain three to four points (SpikingJelly 97.46%, snnTorch 97.24%) an…"
CANNOT VERIFY - The three full-budget values quoted are correct (SpikingJelly 97.46%, snnTorch 97.24%, Nengo 85.44%), but every GAIN claim needs fixed-budget accuracies that the fact base does not contain: 'three to four points', 'does not move', and 'the plasticity rules gain only 0.82 to 2.21 points'. Evidence needed: the fixed-budget accuracy table. For reference the full-budget plasticity accuracies are NEST 8.24-8.50% and Brian2 9.57-9.61%.

[para 605 | 4.6 Experiment 2: Learning Cost and Accuracy] "At the fixed budget NEST scores 7.40–7.50% and Brian2 7.70–7.80%, at or below the 10% chan…"
CANNOT VERIFY - No fixed-budget accuracies in the fact base, so NEST 7.40-7.50% and Brian2 7.70-7.80% cannot be checked. The 10% chance level on ten classes is confirmed. Evidence needed: the fixed-budget accuracy table.

[para 612 | 4.8  Defects In Measuring Instruments] "Twelve defects were found in the measuring and reporting instruments: five in the harness …"
CANNOT VERIFY - Defect counts (twelve, five, seven) have no counterpart in the fact base. Evidence needed: the defect register. The internal arithmetic (5 + 7 = 12) is at least consistent.

[para 614 | 4.8  Defects In Measuring Instruments] "Table 13 Defects found, their effect on previously reported results, and the correction ap…"
CANNOT VERIFY - Caption for the defect table; no measured content in the fact base. Evidence needed: the defect register.

[para 617 | 4.8  Defects In Measuring Instruments] "The original instrument sampled utilization from a background thread, which native simulat…"
CANNOT VERIFY - Describes the mechanism of the old utilisation instrument (GIL-blocked sampling thread, 100% fill-in, ten-millisecond ticks). Evidence needed: the harness source history or the defect register.

[para 617 | 4.8  Defects In Measuring Instruments] "The instrument was replaced by the kernel's per-process CPU clock, checked against loads w…"
CANNOT VERIFY - Describes the instrument replacement and the re-measurement. Evidence needed: the instrument validation record (the 'loads with known answers' check) and run-group provenance. The fact base confirms only that one campaign exists and that a per-process CPU-clock-based proxy is in use (E = t x u/100 x 55 W).

[para 618 | 4.8  Defects In Measuring Instruments] "Because the results database is append-only, rows from a partial re-run on another compute…"
CANNOT VERIFY - Database provenance claim (append-only rows, run-group restriction, 462 excluded records). Evidence needed: the query definitions and the run-group inventory.

[para 619 | 4.8  Defects In Measuring Instruments] "The remaining defects affected presentation or cost, not the reported measurements (Table …"
CANNOT VERIFY - Asserts the remaining defects did not affect reported measurements. Evidence needed: the defect register with a per-defect impact assessment.

[para 621 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "Section 3.9 set out a three-part validation, reported here."
CANNOT VERIFY - Only the first of the three validation parts is in the fact base (per-backend rank agreement, plus the pooled rho). The log-log decomposition and the TDP / exponent sensitivity are absent. Evidence needed: the regression output and the sensitivity table, regenerated for this campaign.

[para 633 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "Regressing log energy on log runtime over all 660 runs gives a slope of 1.141 with R² = 0.…"
CANNOT VERIFY - No log-log regression of energy on runtime exists in the fact base, so the slope 1.141, the R2 of 0.911 and the '660 runs' cannot be checked. Evidence needed: that regression, recomputed on this campaign's run groups. (A slope near 1 is at least consistent with E = t x u/100 x 55 W.)

[para 633 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "An earlier version reported 42%, a figure produced by the defective utilization values and…"
CANNOT VERIFY - 'An earlier version reported 42%' refers to a superseded campaign. The fact base contains no such figure and the thesis may report only this campaign. Evidence needed: none - the sentence should be deleted with the withdrawn value.

[para 634 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "Varying thermal design power by ±30% and the utilization exponent between 0.8 and 1.2 give…"
CANNOT VERIFY - The TDP +/-30% and exponent 0.8-1.2 sensitivity (nine orderings, six identical, three at tau = 0.964) is not in the fact base. Evidence needed: that sensitivity table for this campaign. Caution: 0.964 does appear in the fact base, but only as session-to-session agreement at a fixed size - a different quantity, so the coincidence should not be mistaken for support.

[para 652 | 4.10 Experiment 4: Sensitivity of the Ordering] "Single-size reporting is the norm in the comparative literature reviewed in Chapter 2."
CANNOT VERIFY - A claim about the comparative literature of Chapter 2; external to the campaign. Evidence needed: the Chapter 2 sources.

[para 658 | 4.11 Response to the Research Questions] "Per backend, the proxy follows the workload wherever runtime is driven by simulation and k…"
CANNOT VERIFY - 'keeps its ordering under substantial error in its constants' rests on the TDP / exponent sensitivity that the fact base does not contain (see para 634). Evidence needed: that sensitivity table. Two further notes: the clause 'wherever runtime is driven by simulation' over-claims in the same way as para 632 (brian2/cython is counted compute-bound yet gives rho = 0.70), and 'physical validation is future work' is consistent with the fact base, which validates only the ordinal property.

[para 659 | 4.11 Response to the Research Questions] "First, the design: each experiment type has its own page, and one simulator selector works…"
CANNOT VERIFY - Describes the dashboard's design; nothing in the fact base measures the artefact. Evidence needed: the Chapter 5 design record.

[para 659 | 4.11 Response to the Research Questions] "Third, the evaluation: every functional requirement was verified, representative selection…"
CANNOT VERIFY - Describes the dashboard evaluation (requirement verification, task counts, usability criteria). Evidence needed: the Chapter 5 evaluation record; none of it is in the measurement fact base.

[para 661 | 4.12 Threats to Validity] "The training comparison carries the further conditions set out in Section 3.7.1."
CANNOT VERIFY - A cross-reference to Section 3.7.1 with no measured content. Evidence needed: none from the fact base.

[para 666 | 4.13 Conclusion] "The processor-utilization instrument was replaced and Experiments 1 and 3 were measured ag…"
CANNOT VERIFY - Provenance summary. The one checkable element is consistent - the fact base does exclude the compile-dominated target and the control from the headline spread - but the instrument replacement, the run-group restriction and the placeholder-zero substitution are not recorded. Evidence needed: the defect register and the query definitions.

---

## VERIFIED (52)

[para 525 | 4.2 The Measurement Campaign] "Experiment 2 comes from a fixed-budget and a full-budget training campaign."
VERIFIED - Fact base Experiment 2 records exactly two training budgets: the full 60,000 train / 10,000 test / 10 epochs and the repeat budget 6,000 / 1,000 / 3 epochs. NOTE: a third, partial budget also exists (hidden = 500, three of nine backends) and is disclosed nowhere in the chapter.

[para 527 | 4.2 The Measurement Campaign] "The full reference training configuration was later run for the same nine backends (Sectio…"
VERIFIED - Fact base Experiment 2 table lists nine backends at 60,000 train / 10,000 test / 10 epochs, hidden 256.

[para 530 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Table 8 displays the results of the 100-neuron network's forward pass."
VERIFIED - Experiment 1 in the fact base is inference at N = 100 for all eleven backends.

[para 532 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Table 8 Cost of Inference at Reference Size"
VERIFIED - Matches the Experiment 1 table (simulate median, SD, CV, setup median, peak RSS, CPU %, spikes, energy at N = 100).

[para 533 | 4.3 Experiment 1: Inference Cost at the Reference Size] "The energy index is the energy proxy rescaled so that the costliest simulating backend rea…"
VERIFIED - By construction: the costliest simulating backend is Brian2/Cython at 7.6642 J, so it is the index anchor at 100.

[para 533 | 4.3 Experiment 1: Inference Cost at the Reference Size] "The compile-dominated target, whose measured time is its compiler's (Section 4.7), reads a…"
VERIFIED - Brian2/cpp_standalone is 737.1170 J, i.e. 9,618 on an index anchored at Brian2/Cython's 7.6642 J - far above 100.

[para 537 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Figure 9 Inference runtime at the reference network size of 100 neurons."
VERIFIED - Runtime at N = 100 is tabulated for all eleven backends (0.00130 s to 1.70039 s).

[para 540 | 4.3 Experiment 1: Inference Cost at the Reference Size] "For the reasons given in Section 4.7, the compiling backend is set aside."
VERIFIED - The fact base itself reports the inference spread 'excluding the compile-dominated target' and instructs that the compiling target be kept out of the main comparison.

[para 542 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Table 9 reports each configuration against the fastest, with Cohen's d beside every p-valu…"
VERIFIED - The Holm-corrected pairwise table in ANALYSIS.md carries a Cohen's d for every one of the 55 pairs.

[para 544 | 4.3 Experiment 1: Inference Cost at the Reference Size] "Table 9 Comparison against the fastest configuration at reference size."
VERIFIED - The pairwise Welch / Holm table exists. NOTE: the fastest configuration is reference/vectorised (0.00130 s); the fastest simulator configuration is NEST/threads2 (0.00213 s), not NEST/threads4.

[para 545 | 4.3 Experiment 1: Inference Cost at the Reference Size] "A pair is reported as separated at that level, not merely different in its point estimate,…"
VERIFIED - Matches the 'separated' column, which is exactly Holm-corrected p < 0.05, and the fact base's instruction to report the four unseparated pairs as a failure to detect a difference.

[para 554 | 4.4 Experiment 3: Reversing the Order and Scaling] "Table 10 Runtime against network size, with fitted scaling exponents."
VERIFIED - Experiment 3 table gives runtimes at N = 100 / 500 / 1,000 / 5,000 / 10,000 plus the fitted exponent k for each of the eleven backends.

[para 559 | 4.4 Experiment 3: Reversing the Order and Scaling] "Figure 11 Fitted scaling exponents with their 95% intervals, ordered by exponent."
VERIFIED - The Experiment 3 table carries k, SE(k) and a 95% CI for every backend (e.g. brian2/cython 0.014, CI [-0.014, 0.043]).

[para 562 | 4.4 Experiment 3: Reversing the Order and Scaling] "A configuration whose runtime does not scale with the problem is not measuring the problem…"
VERIFIED - Supported: Brian2's three exponents are 0.014 to 0.023 with CIs spanning zero, and the fact base calls brian2/cython 'still indistinguishable from zero' and cpp_standalone 'the compile-dominated case'.

[para 563 | 4.4 Experiment 3: Reversing the Order and Scaling] "For the Brian2 targets the poor fit is itself the finding, because a runtime that does not…"
VERIFIED - Supported: Brian2 R2 = 0.322 (cpp_standalone) and 0.454 (Cython); snnTorch k = 0.921 with SE 0.212 and CI [0.245, 1.597], so its five measured points are indeed more informative than its exponent.

[para 565 | 4.4 Experiment 3: Reversing the Order and Scaling] "Section 4.10 gives the coefficients at the other sizes, where they are the main result, an…"
VERIFIED - Consistent: the fact base lists Experiment 4 taus at each size with no p-values attached.

[para 568 | 4.4 Experiment 3: Reversing the Order and Scaling] "Figure 12 Rank by runtime at each measured network size."
VERIFIED - Ranks at N = 100 and N = 10,000 are tabulated explicitly and the intermediate sizes are recoverable from the runtime table.

[para 576 | 4.5 Memory and Processor Utilization] "Figure 13 Peak resident set size of the benchmark process across the sweep."
VERIFIED - Peak RSS is tabulated for all eleven backends at all five sizes.

[para 577 | 4.5 Memory and Processor Utilization] "This is why the lines start high, and why Section 4.5 reads growth across the sweep rather…"
VERIFIED - Supported: every non-NEST backend starts between 631 and 696 MB and grows little or much from there, so the level at any one size is dominated by the import baseline while growth is the informative quantity.

[para 585 | 4.5 Memory and Processor Utilization] "Nengo uses one core up to 500 neurons and about 31 of the 32 logical cores from 1,000 neur…"
VERIFIED - Recovered from E = t x (u/100) x 55 W: Nengo reads ~100% at N = 100 (0.246 J / 0.00446 s) and N = 500, then 3,136% / 3,164% / 3,179% at N = 1,000 / 5,000 / 10,000, i.e. about 31 of the 32 logical cores.

[para 585 | 4.5 Memory and Processor Utilization] "At 10,000 neurons the two fastest configurations use one core each, while Nengo uses 31.7 …"
VERIFIED - At N = 10,000 the two fastest (reference/vectorised 0.03572 s and brian2/cython 0.14853 s) both recover ~100% utilisation; Nengo recovers 3,179% and is last at 4.15104 s. Minor: that is 31.8 cores, not 31.7.

[para 585 | 4.5 Memory and Processor Utilization] "Each simulator was configured as its documentation recommends, which is fair by convention…"
VERIFIED - The proxy is E = t x (u_cpu / 100) x 55 W, so utilisation does enter as a multiplier. (The 'configured as its documentation recommends' clause is a design statement, not a measurement.)

[para 588 | 4.6 Experiment 2: Learning Cost and Accuracy] "Each simulator was trained with its native learning mechanism (Section 3.7)."
VERIFIED - Experiment 2 notes record a distinct native mechanism per simulator: NEF decoder (Nengo), surrogate gradient (SpikingJelly, snnTorch), STDP (NEST) and unsupervised plasticity (Brian2).

[para 588 | 4.6 Experiment 2: Learning Cost and Accuracy] "The comparison is of cost, not accuracy, for the reasons given in Section 3.7.1."
VERIFIED - Consistent with the fact base's own caveat that simulators at or near the 10% chance level are reporting the sample budget, not their learning capability.

[para 588 | 4.6 Experiment 2: Learning Cost and Accuracy] "Every training-capable backend received the same budget of 6,000 training and 1,000 test i…"
VERIFIED - The repeat budget is 6,000 / 1,000 / 3 epochs, as stated. Nengo's single-solve status is confirmed by its full-budget record: util_wall_s = 2.9 s equals its 2.90 's per epoch'.

[para 588 | 4.6 Experiment 2: Learning Cost and Accuracy] "Table 11 reports this fixed budget together with the full reference configuration (60,000 …"
VERIFIED - Fact base Experiment 2: full reference configuration 60,000 train / 10,000 test / 10 epochs, executed for all nine backends.

[para 588 | 4.6 Experiment 2: Learning Cost and Accuracy] "Table 12 reports cost per image and compares its projection with the executed run."
VERIFIED - Both budgets are tabulated for the same nine backends, so a measured cost per image and its projection are both computable from the fact base.

[para 590 | 4.6 Experiment 2: Learning Cost and Accuracy] "Table 11 Experiment 2 Results"
VERIFIED - Matches the Experiment 2 tables (s/epoch, CPU %, peak MB, energy J, accuracy %).

[para 596 | 4.6 Experiment 2: Learning Cost and Accuracy] "Table 12 Measured and projected cost per image, with the projection checked against the ex…"
VERIFIED - Both budgets exist for the same nine backends, so the projection check the caption describes is supported.

[para 597 | 4.6 Experiment 2: Learning Cost and Accuracy] "The budget in Table 11 is now constant across rows."
VERIFIED - Confirmed: the repeat budget (6,000 / 1,000 / 3 epochs) and the full budget (60,000 / 10,000 / 10 epochs) were each applied to every one of the nine training-capable backends.

[para 600 | 4.6 Experiment 2: Learning Cost and Accuracy] "For NEST it is within 8% at every thread count, because its cost really is one simulation …"
VERIFIED - Confirmed, and conservatively stated: per-image cost at the small budget over the full budget is 1.000 (one thread, 73.42 vs 73.39 ms), 0.995 (two threads, 39.50 vs 39.70 ms) and 1.024 (four threads, 23.25 vs 22.70 ms) - within 2.4%, so 'within 8%' holds and could be tightened.

[para 603 | 4.6 Experiment 2: Learning Cost and Accuracy] "It is by far the cheapest route to a working classifier here, with a ceiling set by how we…"
VERIFIED - 'By far the cheapest' is confirmed: Nengo 2.90 s/epoch against 89.94 s for the next cheapest (SpikingJelly), a factor of 31. CAVEAT: the width-ceiling explanation is not measured - the only width evidence is the partial hidden = 500 run of three of nine backends, and in that line the fact base's '88.38%' for Nengo is ambiguous between utilisation and accuracy.

[para 622 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "Table 14 gives the Spearman rank correlation between the proxy and the analytically derive…"
VERIFIED - Matches the 'Rank agreement between the proxy and EFLOP' table: Spearman rho against the EFLOP count over the size sweep, one row per backend.

[para 624 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "Table 14 Rank agreement between the energy proxy and the operation count."
VERIFIED - Matches that same table.

[para 625 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "With five points, the smallest attainable exact p-value is 0.017."
VERIFIED - Confirmed: every non-degenerate row in the table reports exact p = 0.0167 for n = 5.

[para 629 | 4.9 The Energy Proxy: Validation, Decomposition and Sensitivity] "Figure 14 Energy proxy vs. the analytic operation count."
VERIFIED - Both the energy table and the EFLOP table span the five sizes, so the figure's content exists.

[para 637 | 4.10 Experiment 4: Sensitivity of the Ordering] "Experiment 4 tests whether the ordering is a property of the simulators or of two settings…"
VERIFIED - Confirmed: Experiment 4 in the fact base measures exactly these two settings - ordering against network size, and ordering by metric (energy proxy, peak memory) against runtime at N = 10,000.

[para 637 | 4.10 Experiment 4: Sensitivity of the Ordering] "No p-values are given, because with eleven items a significance test has little power; the…"
VERIFIED - Consistent: the fact base reports every Experiment 4 tau without a p-value.

[para 639 | 4.10 Experiment 4: Sensitivity of the Ordering] "Figure 15 Rank agreement with the ordering at the largest network size."
VERIFIED - The taus against the N = 10,000 ordering are tabulated for N = 100 / 500 / 1,000 / 5,000 in both sessions.

[para 640 | 4.10 Experiment 4: Sensitivity of the Ordering] "A bar at 1.0 is an ordering identical to the reference."
VERIFIED - Definitional and correct for Kendall tau-b.

[para 642 | 4.10 Experiment 4: Sensitivity of the Ordering] "Table 15 Rank agreement between alternative and reference orderings."
VERIFIED - Matches the Experiment 4 tau values.

[para 643 | 4.10 Experiment 4: Sensitivity of the Ordering] "A value of 1.000 means the order is the same."
VERIFIED - Definitional and correct.

[para 647 | 4.10 Experiment 4: Sensitivity of the Ordering] "Figure 16 Rank agreement between each metric's ordering and runtime."
VERIFIED - The metric-vs-runtime taus at N = 10,000 exist in the fact base (energy proxy 0.745, peak memory 0.309).

[para 650 | 4.10 Experiment 4: Sensitivity of the Ordering] "A benchmark stopping short of 5,000 neurons would therefore have published an ordering onl…"
VERIFIED - Supported: agreement with the N = 10,000 ordering is 0.309 / 0.236 (session B 0.345) / 0.491 at N = 100 / 500 / 1,000 against 0.745 (session B 0.818) at N = 5,000.

[para 651 | 4.10 Experiment 4: Sensitivity of the Ordering] "Brian2's NumPy and Cython targets are among both the flattest and, at 10,000 neurons, the …"
VERIFIED - All three parts check out: brian2/cython k = 0.014 is the flattest and brian2/numpy 0.017 the second flattest; they are ranks 2 and 3 at N = 10,000; and dropping both from the exponent-vs-runtime comparison gives tau-b = 2/36 = 0.056, reproducing the quoted figure exactly.

[para 653 | 4.10 Experiment 4: Sensitivity of the Ordering] "Speed at one size also says little about how cost grows: Nengo ranks fifth on runtime at N…"
VERIFIED - Confirmed: Nengo is rank 5 at N = 100 (0.00446 s) and has the steepest exponent measured (k = 1.544).

[para 661 | 4.12 Threats to Validity] "First, all measurements come from one laptop, so absolute runtimes, and the threading resu…"
VERIFIED - Confirmed: the whole campaign is machine LT68, Intel Core i9-14900HX, WSL2, CPU only.

[para 661 | 4.12 Threats to Validity] "Second, five runs per condition is a small sample and repeats within a session are not ful…"
VERIFIED - Confirmed: n = 5 retained runs per condition (Shapiro-Wilk table), and between-session variability was measured separately (Experiment 4, two sessions).

[para 665 | 4.13 Conclusion] "First, the speed ordering of the simulators changes across the range of network sizes a re…"
VERIFIED - Confirmed: fixed-size session-to-session agreement is 0.818 to 0.964, while agreement between N = 100 and N = 10,000 within a session is only 0.309.

[para 665 | 4.13 Conclusion] "Second, scaling exponents separate configurations dominated by fixed overhead from those w…"
VERIFIED - Confirmed: brian2/cpp_standalone is flat (k = 0.023, R2 = 0.322), is the one backend with negative rank agreement against the workload (rho = -0.60) and is named 'the compile-dominated case'.

[para 665 | 4.13 Conclusion] "Third, memory growth and learning cost differ by orders of magnitude and follow network si…"
VERIFIED - Confirmed: memory added per neuron spans 0.03 KB (reference) to 160.2 KB (Nengo) and training cost spans 2.90 to 14,852.06 s per epoch - four and nearly four orders of magnitude respectively.

[para 665 | 4.13 Conclusion] "Fourth, the energy proxy is a valid ordinal instrument, but it is largely rescaled runtime…"
VERIFIED - Confirmed: E = t x (u/100) x 55 W with rho = 1.000 for nine of eleven backends, so the proxy is rescaled runtime except where utilisation departs from one core (NEST's thread counts, Nengo, brian2/cpp_standalone).

---

## SUMMARY - distinct factual errors, deduplicated, in priority order

Each item is one distinct error, whatever number of sentences repeats it. Sentence indexes are
given as paragraph numbers.

### A. Core inferential statistics (Section 4.3)

1. **Welch's ANOVA is wrong on every term.** Reported F(10, 17.22) = 1898.78, p = 3.9e-24,
   eta-squared = 0.9986; the campaign gives **F(10, 17.10) = 451.58, p = 1.143e-18,
   eta-squared = 0.9930**. (para 542)
2. **Levene's test is wrong.** Reported W = 6.35, p = 6.0e-06; correct **W = 9.38, p = 4.285e-08**.
   (para 542)
3. **Shapiro-Wilk count and identity are wrong.** Reported "ten of the eleven ... rejects it for NEST
   with one thread (p = 0.038)"; the campaign has **two failures of eleven - brian2/numpy
   (W = 0.6884, p = 0.0072) and nest/threads2 (W = 0.6877, p = 0.0071)** - so nine of eleven fail to
   reject, and NEST/threads1 (p = 0.1415) is not among the failures. (para 542)
4. **Count of separated pairs is wrong.** Reported 50 of 55; correct **51 of 55**, with exactly four
   unseparated: nest/threads1-threads4 (p = 0.419), brian2/cython-brian2/numpy (p = 0.419),
   nest/threads1-threads2 (p = 0.723), nest/threads2-threads4 (p = 0.723). (para 542)
5. **Coefficient-of-variation range is wrong at both ends.** Reported "1.6% (Brian2/Cython) to 11.7%
   (NEST with one thread)"; correct **4.8% (reference/scalar) to 20.1% (NEST with two threads)**;
   Brian2/Cython is 7.8% and NEST/threads1 is 12.7%. (para 541)

### B. Inference headline numbers (Section 4.3)

6. **The fastest simulator configuration changes.** Reported NEST with four threads at 2.120 ms;
   correct **NEST with two threads at 2.13 ms** (NEST/threads4 is 2.20 ms). The fact base also
   forbids naming a winner among the NEST thread counts, none of which Holm separates. (paras 540,
   544)
7. **Slowest value and the fold difference are wrong.** Reported 1.669 s and 787-fold; correct
   **1.70039 s**, which is **798x** the fastest simulator configuration (NEST/threads2) and **1,308x**
   the fastest backend overall (reference/vectorised). (para 540)
8. **The headline inference spread is wrong, as are both of its endpoints.** Reported 67.3x from NEST
   with four threads (2.120 ms) to Brian2/NumPy (142.663 ms); the fact base gives **106.88x
   (0.13933 s / 0.00130 s)**, i.e. **Brian2/Cython at 139.33 ms against the vectorised control at
   1.30 ms**. Brian2/NumPy is 133.18 ms and is not the slowest non-compiling backend. Restricted to
   simulator configurations the spread is **65.4x**. (para 540)
9. **Vectorised control runtime is wrong.** Reported 1.376 ms; correct **1.30 ms**. The "faster than
   every simulator" superlative stands. (para 540)

### C. Scaling exponents and fits (Sections 4.4, 4.7, 4.10)

10. **Every scaling exponent quoted in the chapter is stale.** Nengo **1.544** (reported 1.550);
    NEST **1.159 / 1.135 / 1.133** for one / two / four threads (reported 1.199 / 1.195 / 1.151, and
    in the wrong thread order - descending is one, two, four); scalar control **0.982** (reported
    0.993); vectorised control **0.732** (reported 0.735); Brian2 **0.023 (cpp_standalone) / 0.017
    (numpy) / 0.014 (cython)** (reported 0.048 / 0.023 / 0.001). The NEST range is **1.133-1.159**,
    not 1.151-1.199. (paras 562, 573, 608, 651)
11. **The flattest backend changes identity.** It is now **brian2/cython at k = 0.014, 95% CI
    [-0.014, 0.043]** - still indistinguishable from zero. Any statement making Brian2/NumPy or the
    C++ standalone target the flattest is stale; NumPy (k = 0.017, CI [0.005, 0.030]) is now the one
    Brian2 target whose interval excludes zero. (paras 562, 608, 651)
12. **Every R-squared is stale.** brian2/cpp_standalone **0.322** (reported 0.013), brian2/cython
    **0.454** (reported 0.330), brian2/numpy **0.869** (reported 0.688), snntorch **0.862** (reported
    0.866). The same four are still the loosest fits, but NumPy now fits better than snnTorch, which
    reverses the order in which they are listed. (paras 563, 608)
13. **Brian2/C++ standalone runtimes are wrong.** Reported 1.6782 s at N = 100 and 1.6911 s at
    N = 10,000; correct **1.78560 s and 2.12605 s** (Experiment 1's own median for that target is
    1.70039 s). Its runtime is therefore no longer flat to three decimal places. (para 608)
14. **The exponent-ordered sequence is misordered.** The scalar control (0.982) comes **before**
    SpikingJelly (0.960), not after it. (para 651)

### D. Rankings and rank agreement (Sections 4.4, 4.10)

15. **The two Brian2 targets are swapped at N = 10,000.** Brian2/NumPy rises from rank 9 to rank
    **3** and Brian2/Cython from rank 10 to rank **2** (cython 0.14853 s beats numpy 0.14868 s). The
    same swap appears in the list of the four fastest simulator configurations at N = 10,000.
    (para 564)
16. **Kendall tau-b between the N = 100 and N = 10,000 orderings is wrong.** Reported 0.273; correct
    **0.309** in both sessions - so **36 of 55 pairs agree and 19 are reversed**, not 35 and 20.
    (para 565)
17. **The size-vs-size tau series is wrong and mixes sessions.** Reported 0.273 / 0.236 / 0.382 /
    0.818; correct **session A 0.309 / 0.236 / 0.491 / 0.745** and **session B 0.309 / 0.345 /
    0.491 / 0.818** for N = 100 / 500 / 1,000 / 5,000. 0.273 and 0.382 were never measured, and
    quoting 0.236 beside 0.818 mixes the two replicates. (paras 650, 657)
18. **The reversed-pair percentages are wrong.** Reported "between 31 and 38 per cent"; correct
    **25 to 38 per cent** (session A: 34.6 / 38.2 / 25.4%; session B: 34.6 / 32.8 / 25.4%). The
    N = 1,000 bar reverses only a quarter of the pairs. (para 640)
19. **"Weakest at 500 neurons" does not replicate.** It holds in session A (0.236 < 0.309) but
    reverses in session B (0.345 > 0.309), where the minimum is at the smallest size. Qualify it as a
    session-A feature or drop it. (para 650)
20. **The metric taus are wrong.** Reported energy 0.782, peak memory +0.418, scaling exponent 0.236;
    correct **energy 0.745 and peak memory 0.309**. The exponent tau is not in the fact base;
    recomputed from the k column against the N = 10,000 runtimes it is **0.309**, not 0.236.
    (paras 653, 657)
21. **"Every pair the energy ordering reorders involves NEST with two or four threads" is false.**
    Of the 7 reordered pairs, the SpikingJelly-snnTorch pair involves neither: snnTorch is slower
    (0.77200 s vs 0.76422 s) but cheaper on the proxy (41.815 J vs 55.570 J). Say **six of seven**.
    (para 653)

### E. Session count and reproducibility (Sections 4.2, 4.4, 4.10, 4.11)

22. **"Four sessions" must become two.** The campaign re-measured the ordering twice. (paras 650,
    657)
23. **Fixed-size reproducibility range is wrong.** Reported tau 0.745 to 1.000; correct **0.818 to
    0.964** (0.964 / 0.927 / 0.818 / 0.964 / 0.964 at N = 100 / 500 / 1,000 / 5,000 / 10,000). No tau
    of 1.000 was measured, and there is no "twin session run ten minutes later" or "0.891 or better"
    figure. (para 566)
24. **Within-session agreement between the extremes is wrong.** Reported "tau = 0.200 to 0.273";
    correct **0.309 in both sessions**. (paras 566, 650)
25. **"Every figure, table and coefficient comes from one measurement session" is inaccurate.**
    Experiment 4's coefficients come from two sessions inside the one campaign. Restate as one
    campaign on one machine, with the ordering measured twice. (para 525)

### F. Energy proxy validation (Sections 4.9, 4.10, 4.11)

26. **The pooled energy-EFLOP correlation is wrong in value and in n.** Reported 0.645 over 55
    observations; correct **rho = 0.771, p = 5.62e-11, over 50 runs** pooled across the compute-bound
    backends - 50 rather than 55 precisely because the compile-dominated target is excluded.
    (paras 655, 658)
27. **The per-backend count is wrong.** Reported "eight of the eleven" at rho = +1.000; correct
    **nine of eleven**, because **brian2/numpy is rho = 1.00, exact p = 0.0167**, not 0.900 / 0.083.
    (para 632)
28. **Brian2/C++ standalone's rank agreement is wrong.** Reported rho = -0.400, p = 0.517; correct
    **-0.600, p = 0.3500**. Brian2/Cython's 0.700, p = 0.2333 is correct. Only two Brian2 targets are
    exceptions now, not three. (para 632)
29. **"For every backend whose runtime is driven by simulation the proxy preserves the ordering"
    over-claims.** The fact base classes only brian2/cpp_standalone as compile-dominated and counts
    brian2/cython among the compute-bound backends, yet cython's rho is 0.70. Restate as **nine of
    eleven backends reproduce the workload ordering exactly**. (paras 632, 658)

### G. Memory and processor utilisation (Section 4.5)

30. **Reference-size utilisation values are all wrong.** Range **100.0% to 780.5%** (not 794.1%);
    NEST/threads2 **208.4%** (not 239.5%); NEST/threads4 **521.3%** (not 376.4%);
    brian2/cpp_standalone **780.5%** (not 794.1%). "Eight backends use one core" is correct.
    (para 581)
31. **NEST's utilisation band is too narrow.** The claimed 392-485% for four threads is contradicted
    by the measured **521.3%** at the reference size; recovered from the energy table the sweep
    spans roughly 100% / 191-300% / 394-510% for one / two / four threads. (para 585)
32. **"About eight cores at every size" overstates the C++ standalone target.** 780.5% (7.8 cores) at
    the reference size, but about **600-760% (6.0-7.6 cores)** across the sweep, lowest at
    N = 10,000. Also reported as 790-799% in Section 4.7, which no row supports. (paras 585, 608)
33. **Peak memory at N = 10,000 is wrong at both ends.** Reported 641.7 MB (Brian2/NumPy) to
    2,203.8 MB (Nengo); correct **644.7 MB to 2,206.1 MB**. NEST at N = 10,000 is **891-925 MB**
    (not 886-923), so its increase is **800-831 MB** (not 796-830). Nengo's endpoint is 2,206.1 MB
    (not 2,204). (paras 579, 582)
34. **The non-NEST band at the reference size is wrong.** Reported 629-694 MB; correct **631-696 MB**
    (brian2/numpy 631.3 MB to reference/scalar 696.4 MB). The NEST band 91-94 MB is correct.
    (para 579)
35. **Brian2's memory-per-neuron figures are wrong.** Cython **0.82 KB** (reported 0.45), NumPy
    **1.36 KB** (reported 1.32), and NumPy's span is **631.4 to 644.7 MB** (reported 629 to 642).
    Consequently the NEST-to-Brian2/NumPy ratio is **60 to 63 times**, not 62 to 65. (paras 582, 583)
36. **"SpikingJelly the largest at 100 neurons" is wrong as written.** The largest peak RSS at
    N = 100 is **reference/scalar at 696.4 MB** (then reference/vectorised 695.7 MB); SpikingJelly's
    694.0 MB is only the largest among simulators. (para 583)
37. **The NEST threading result at N = 10,000 is wrong in every number and in its direction.**
    Reported 0.498 s / 0.504 s / 0.681 s with two and four threads "indistinguishable" and both
    beating one thread "by about 26%"; correct **0.40209 s (two), 0.35302 s (four), 0.58103 s (one)**
    - four threads is **12% faster than two**, so the fourth thread does shorten the run, and the
    gains over one thread are **31% and 39%**. At N = 500 and N = 1,000 four threads is **5.6% and
    19.7%** faster than two, not "about 15%". No pairwise test exists at N = 10,000, so
    "indistinguishable" has no statistical backing. (para 586)

### H. Training experiment (Section 4.6)

38. **The fixed-budget training spread is wrong and the "three orders of magnitude" claim fails.**
    Reported 0.87 s (Nengo) to 1,606.18 s (Brian2/C++ standalone); correct **1.7 s and 1,416.4 s per
    epoch**, a ratio of about **833x** - under three orders of magnitude on a per-epoch basis. State
    the basis if the three-epoch total (4,249 s) is meant instead. (para 594)
39. **"Under a second for Nengo and almost 27 minutes for Brian2's C++ standalone" is wrong.** Nengo
    **1.7 s**; Brian2/cpp_standalone **23.6 minutes per epoch**, i.e. **70.8 minutes** over the three
    epochs. (para 601)
40. **Surrogate-gradient cost per epoch at the fixed budget is wrong.** Reported 13.79 against 14.50
    s; correct **9.6 (SpikingJelly) against 10.3 (snnTorch)**; at the full budget 89.94 against
    90.94. The ordering survives. (para 602)
41. **The projection-accuracy claims are wrong.** snnTorch costs **1.717 ms per image at 6,000 and
    1.516 ms at 60,000** (reported 2.416 and 1.535), so the gradient libraries' projection
    overestimates by **7-13%**, not "about half"; Nengo's by a factor of **5.9**, not 2.5; and the
    plasticity rules' band is **0.95 to 1.02**, not 0.84 to 1.16. ("Within 8%" for NEST is true and
    could be tightened to within 2.4%.) (para 600)
42. **Full-budget accuracy ranges are wrong.** Reported NEST 8.32-8.41% and Brian2 9.60-9.91%;
    correct **NEST 8.24-8.50%** (8.24 two threads, 8.32 four, 8.50 one) and **Brian2 9.57-9.61%**.
    (para 605)
43. **No fixed-budget accuracies exist in the fact base at all.** 94.10%, 93.20%, 85.50%, 7.40-7.50%
    and 7.70-7.80% cannot be checked, and with them the derived claims "gain three to four points",
    "Nengo does not move" and "the plasticity rules gain only 0.82 to 2.21 points" have no support.
    Either supply that table or restrict the accuracy discussion to the full budget. (paras 602,
    603, 604, 605)

### I. Material that has no counterpart in the fact base

44. **Every reference to an earlier campaign must be deleted, not restated.** "58.0% in the initial
    campaign" (para 541), "an earlier value (0.716 over 50 observations)" (para 655), "an earlier
    version reported 42%" (para 633), "1.4 to 2.8 times slower than in two earlier campaigns" and
    "-21% to +15%" (para 566), "which an earlier attempt could not complete" (para 527), and
    "four sessions" (paras 650, 657). The thesis may report only the 21-27 September 2026 campaign.
45. **The energy decomposition is unsupported.** Slope 1.141, R-squared 0.911 over "660 runs"
    (para 633) has no counterpart; regenerate the log-log regression on this campaign or drop the
    claim that runtime explains 91% of the proxy's variance.
46. **The TDP / exponent sensitivity is unsupported.** "Nine orderings at N = 10,000: six agree
    perfectly and three at tau = 0.964" (para 634) is not in the fact base, and the 0.964 that does
    appear there is session-to-session agreement, a different quantity. It also underpins "keeps its
    ordering under substantial error in its constants" (para 658).
47. **Per-run utilisation distribution is unsupported.** "Across the 660 runs ... median 100.4%
    (middle half 100.0-189.1%)" (para 581) has no counterpart; nor does the "629 MB" interpreter
    baseline (para 579).
48. **Condition and run counts are unsupported.** 150 conditions, 678 runs, 132 inference and
    scalability conditions, 660 runs, 18 training conditions, 462 excluded records (para 526). Note
    the fact base implies **21** training conditions if the partial hidden = 500 run is counted
    (9 + 9 + 3), so "18" is probably wrong as well as unsupported.
49. **The instrument-defect narrative is unsupported by the fact base.** Twelve defects, five plus
    seven, the sampling-thread mechanism, the replacement and validation, the append-only database
    and the run-group restriction (paras 523, 525, 612-619, 666) all need the defect register and
    run-group provenance as documented evidence.
50. **Brian2's and NEST's "dispersion" claim is undefined.** Read as run-to-run CV it is contradicted:
    Brian2's CVs (5.3 / 7.8 / 9.0%) are below the 11.7% median while NEST's (12.7 / 20.1 / 17.3%) are
    above it. Define the measure or drop the justification. (para 530)

### J. Now-measured material the chapter still omits

51. **The partial hidden = 500 run must be disclosed.** The fact base has nengo 4.95 s/epoch,
    spikingjelly 157.60 and snntorch 157.94 for the CCR-proposed width, with **six of nine backends
    not run**, and instructs that it be reported as a partial check and never as part of the main
    comparison. No sentence in Chapter 4 mentions it. Note also that the fact base's third column for
    that run ("88.38%" for Nengo) is ambiguous between utilisation and accuracy and must be resolved
    before it is quoted - it is the only width evidence bearing on the Nengo "ceiling" claim in
    para 603.
52. **Training utilisation, energy and memory are now measured for all nine backends at both
    budgets** (CPU %, peak MB and energy J columns; the utilisation cross-check passes at NEST/4
    349.9% vs 349.0% and NEST/2 190.9% vs 190.5%). Any statement anywhere in the thesis that these
    were not measured is obsolete, and Tables 11 and 12 should now carry them.
53. **The N = 500 equivalence check is reported nowhere in Chapter 4.** The fact base has 11 of 11
    backends passing within a 35% tolerance on firing rate, closest reference/scalar vs
    reference/vectorised at 0.0% and furthest nest/threads4 at 15.9%. If Chapter 4 is meant to carry
    it, it is missing; if not, no claim in these 139 sentences conflicts with it.


# Chapter 5 — The Dashboard

# Chapter 5 factual audit against FACT_BASE.md / ANALYSIS.md and the 27 September 2026 dashboard

Sources of truth: `/root/v3/FACT_BASE.md` and `/root/v3/ANALYSIS.md` for every measured value, plus the
recorded state of the dashboard after its 27 September 2026 revision. All 69 sentences of
`/root/v3/claims_ch5.json` were checked; none sampled.

| Verdict | Count |
|---|---|
| MUST CHANGE | 30 |
| CANNOT VERIFY | 22 |
| VERIFIED | 17 |
| **Total** | **69** |

Two things moved under this chapter and both matter for almost every sentence in it.

**The campaign was re-measured.** The values Chapter 5 quotes from the dashboard's cards and charts are
from the superseded run. The headline corrections are: fastest inference NEST/**threads2** at **2.13 ms**
(not NEST/threads4 at 2.12); flattest scaling **brian2/cython, k = 0.014**, 95% CI [-0.014, 0.043] (not
brian2/numpy at 0.023); largest peak memory at the reference size **reference/scalar, 696.4 MB** (not
SpikingJelly); best MNIST accuracy **SpikingJelly 97.46%**; steepest scaling **nengo, k = 1.544**;
largest memory at N = 10,000 **nengo, 2206.1 MB**.

**The dashboard was revised on 27 September 2026.** Light near-white surface in place of the dark navy
one; the six simulator colours unchanged except snnTorch's green, re-stepped #1fa989 -> #17997b to clear
3:1 contrast; every bar chart prints its value on the bar with units, so no figure depends on hovering;
every figure is followed by a compact results table with the same rows in the same order; the home page's
sensitivity blocks show their tau values and network sizes; the equivalence dots are captioned
"N of M backends pass the equivalence check"; nine routes are served (home, all-simulators, inference,
scalability, memory, training, sensitivity, provenance, about).

Conventions used below. Every screenshot reference and figure caption pointing at a dashboard page is
listed under MUST CHANGE, because a figure captured before 27 September 2026 shows chrome the dashboard
no longer has and values the campaign no longer reports; in those entries the fix is to re-capture or
redraw the figure (and add the companion results table), not to reword the sentence. Sentences that
describe a chart's *form* correctly are verified, with the regeneration noted. Per-simulator "fastest"
and "lowest" values are taken over that simulator's own backends; the reference/scalar and
reference/vectorised NumPy controls are not simulators and are named explicitly wherever they outrank
one. Inference times at N = 100 are the Experiment 1 simulate medians (n = 5); where the size sweep gives
a slightly different figure for the same size, both are given.

No sentence among the 69 describes the old dark theme in words, and none claims values are available only
on hover - so the theme and hover changes surface here as stale figures rather than as stale prose. The
chapter also nowhere mentions the new on-bar value labels, the per-figure results tables, the sensitivity
tau and size labels, or the equivalence-dot caption; see SUMMARY item 9.

---

## MUST CHANGE (30)

[para 676 | 5.1 Accessing and Reproducing the Dashboard] "The dashboard was built in three iterations alongside the measurement campaign: a single-p..."
MUST CHANGE - 'three iterations ... and a final version that fixed problems found while using it on real data' - the dashboard was changed again on 27 September 2026: light near-white surface in place of the dark navy one, snnTorch's series green re-stepped #1fa989 -> #17997b for 3:1 contrast, on-bar value labels with units on every bar chart, a compact results table after every figure, tau values and network sizes on the home page's sensitivity blocks, and the equivalence dots captioned 'N of M backends pass the equivalence check'. So the version described as final is not the current one. Correct to: the build history plus the 27 September 2026 revision (four stages, not three). Separately, the three earlier stages are themselves unsupported - evidence needed: a changelog or version-control history.

[para 682 | 5.3 The Home Page] "Figure 17 shows the home page with all simulators selected."
MUST CHANGE - Not the wording but the figure: any home-page screenshot taken before 27 September 2026 shows the dark navy surface, bars without on-bar value labels, no companion results table, sensitivity blocks without their tau values and network sizes, and uncaptioned equivalence dots. Re-capture Figure 17 from the current build, and note that every headline number on it has moved (fastest inference NEST/threads2 2.13 ms, flattest scaling brian2/cython k = 0.014, largest peak memory at the reference size reference/scalar 696.4 MB, best MNIST accuracy SpikingJelly 97.46%).

[para 684 | 5.3 The Home Page] "Figure 17 The home page of the dashboard, with its main elements numbered."
MUST CHANGE - Same stale-figure defect as the reference above, and the numbered-element list must be re-made: the current home page carries elements the old annotation cannot have numbered - on-bar value labels with units, the compact results table under each figure, the tau values and network sizes on the sensitivity blocks, and the 'N of M backends pass the equivalence check' caption under the equivalence dots.

[para 688 | 5.3 The Home Page] "Each card names the backend and the condition behind the number, for example “NEST / threa..."
MUST CHANGE - 'NEST / threads4, median over 5 runs at N=100' - the fastest inference in the re-measured campaign is NEST with TWO threads at 2.13 ms (0.00213 s); NEST/threads4 is 0.00220 s (2.20 ms). The example card must read 'NEST / threads2, median over 5 runs at N = 100'. 'median over 5 runs' and 'N = 100' are correct (n = 5 per backend in the Shapiro-Wilk table; Experiment 1 is at N = 100). Add that Holm does not separate the NEST thread counts (threads1 vs threads2 p = 0.723, threads2 vs threads4 p = 0.723, threads1 vs threads4 p = 0.419), so the card names a median, not a separated winner.

[para 696 | 5.4 Reading Each Simulator’s Results] "Figures 18 to 22 show this summary for each simulator, and Table 17 collects the same numb..."
MUST CHANGE - 'Table 17 collects the same numbers from Chapter 4' - as printed it does not, because every per-simulator value quoted in Section 5.4 disagrees with the re-measured campaign (see the twelve MUST CHANGE entries for paras 700-716 below). Figures 18-22 must also be re-captured from the post-27-September build. Regenerate Table 17 and the five screenshots together, then this cross-reference becomes true.

[para 699 | 5.4 Reading Each Simulator’s Results] "Figure 18 The home page with only Brian2 selected."
MUST CHANGE - Stale figure: re-capture with the light near-white surface, on-bar value labels with units, and the compact results table that now follows each figure. The Brian2 view's own numbers also moved - fastest Brian2 inference at N = 100 is NumPy at 133.18 ms, lowest Brian2 peak memory at N = 10,000 is 644.7 MB, flattest scaling is Cython at k = 0.014.

[para 700 | 5.4 Reading Each Simulator’s Results] "Its fastest inference at 100 neurons is 133.58 ms (Cython), far slower than NEST."
MUST CHANGE - '133.58 ms (Cython)' - wrong value and wrong backend. Brian2's fastest at N = 100 is NumPy at 133.18 ms (0.13318 s); Cython is 139.33 ms (0.13933 s), the slowest non-compiling backend in the study. Correct to: 'Its fastest inference at 100 neurons is 133.18 ms (NumPy)'. 'far slower than NEST' remains correct (NEST/threads2, 2.13 ms). Note also that Holm does not separate brian2/cython from brian2/numpy (p = 0.419), so the within-Brian2 ordering must not be presented as established.

[para 700 | 5.4 Reading Each Simulator’s Results] "Yet it has the lowest peak memory at 10,000 neurons (642 MB, NumPy) and the flattest scali..."
MUST CHANGE - Both numbers are wrong. Lowest peak memory at N = 10,000 is 644.7 MB for brian2/numpy, not 642 MB (642.8 MB is brian2/cpp_standalone at N = 100). Flattest scaling is brian2/CYTHON at k = 0.014, 95% CI [-0.014, 0.043], not k = 0.023 (0.023 is brian2/cpp_standalone; brian2/numpy is 0.017). Because the CI spans zero, report it as indistinguishable from zero rather than as a measured slope.

[para 703 | 5.4 Reading Each Simulator’s Results] "Figure 19 The home page with only NEST selected."
MUST CHANGE - Stale figure: re-capture in the light theme with on-bar value labels and the companion results table. NEST's own numbers moved too - 2.13 ms at two threads, 891.3 MB at N = 10,000, k = 1.133-1.159, best accuracy 8.50%.

[para 704 | 5.4 Reading Each Simulator’s Results] "It has the fastest inference of any simulator at 100 neurons: 2.12 ms with four threads."
MUST CHANGE - '2.12 ms with four threads' - the fastest inference is NEST with TWO threads at 2.13 ms (0.00213 s). NEST/threads4 is 2.20 ms and NEST/threads1 2.45 ms. Correct to '2.13 ms with two threads'. Two further points must be added: Holm does not separate the three thread counts at N = 100 (threads1 vs threads2 p = 0.723, threads2 vs threads4 p = 0.723, threads1 vs threads4 p = 0.419), so 'with two threads' is the median ranking and not a demonstrated difference; and 'fastest of any simulator' is right only because the vectorised NumPy control (1.30 ms) is a control. (If the card is instead fed from the size sweep rather than Experiment 1, NEST/threads4 reads 1.82 ms there - pick one source and say which.)

[para 704 | 5.4 Reading Each Simulator’s Results] "Its lowest peak memory at 10,000 neurons is 886 MB, and its scaling exponents of 1.151 to ..."
MUST CHANGE - '886 MB' and '1.151 to 1.199' are both wrong. NEST's lowest peak memory at N = 10,000 is 891.3 MB (threads1; threads2 897.8, threads4 925.0). Its exponents are k = 1.159 (one thread), 1.135 (two) and 1.133 (four), i.e. a range of 1.133 to 1.159. 'grows slightly faster than the network' still holds. Worth adding that NEST's memory growth over the sweep is the largest of any backend, about 9.8x.

[para 704 | 5.4 Reading Each Simulator’s Results] "The Scalability page shows that extra threads help at mid sizes, but four threads give no ..."
MUST CHANGE - 'four threads give no gain over two at 10,000 neurons' - contradicted. At N = 10,000 nest/threads4 is 0.35302 s against nest/threads2 at 0.40209 s, so four threads are about 14% faster; four threads are in fact faster than two at every measured size (0.00182/0.00207 at N = 100, 0.00778/0.00824 at 500, 0.01422/0.01770 at 1,000, 0.10609/0.11870 at 5,000). Correct to: the gain from doubling threads is small and sub-linear (about 1.14x at N = 10,000 for 2x the threads), and at N = 100 the Holm-corrected tests do not separate the thread counts at all (threads2 vs threads4 p = 0.723). Note the energy cost of the extra threads: 78.156 J against 44.335 J at N = 10,000.

[para 704 | 5.4 Reading Each Simulator’s Results] "Its best accuracy, 8.41%, is at chance for the same reason as Brian2."
MUST CHANGE - '8.41%' - NEST's best full-budget accuracy is 8.50% (threads1); threads4 is 8.32% and threads2 8.24%. Also 'at chance' is loose: 8.24-8.50% is below the 10% chance level for ten classes, so say 'at or below chance'. 'for the same reason as Brian2' inherits the unevidenced homeostasis explanation flagged for para 700 - use the fact base's wording (the simulators near chance are reporting the sample budget, not their learning capability).

[para 707 | 5.4 Reading Each Simulator’s Results] "Figure 20 The home page with only Nengo selected."
MUST CHANGE - Stale figure: re-capture in the light theme with on-bar value labels and the companion results table. Nengo's own numbers moved - 4.76 ms at N = 100, k = 1.544, 2206.1 MB at N = 10,000.

[para 708 | 5.4 Reading Each Simulator’s Results] "At 100 neurons it is fast (5.01 ms)."
MUST CHANGE - '5.01 ms' - nengo/reference's Experiment 1 simulate median at N = 100 is 4.76 ms (0.00476 s). (The size sweep reads 4.46 ms at the same size; 5.01 ms appears in neither.) Also 'fast' should be qualified: Nengo is fifth of eleven at N = 100 and eleventh of eleven at N = 10,000.

[para 708 | 5.4 Reading Each Simulator’s Results] "It also has the steepest scaling of all (k = 1.550) and the largest memory at 10,000 neuro..."
MUST CHANGE - Two of the three numbers are wrong. Steepest scaling is nengo/reference at k = 1.544 (95% CI [0.879, 2.210]), not 1.550. Largest peak memory at N = 10,000 is 2206.1 MB, not 2,204 MB. 'steepest of all', 'largest memory at 10,000' and 'slowest backend at that size' (4.15104 s, rank 11 of 11) are all correct.

[para 708 | 5.4 Reading Each Simulator’s Results] "This gives 85.44% accuracy in a few seconds, the cheapest route to a working classifier in..."
MUST CHANGE - 'in a few seconds' - Nengo's full budget is 2.90 s per EPOCH over 10 epochs, about 29 s of training, not a few seconds. Correct to '85.44% accuracy at 2.90 s per epoch, roughly 29 s for the full 10-epoch budget'. The 'cheapest route' superlative is supported on both axes (lowest s/epoch of the nine and lowest energy, 3586 J against SpikingJelly's 4922 J and snnTorch's 4984 J), but it should be qualified: Nengo's 85.44% is 12.0 points below SpikingJelly's 97.46%, and it reaches this with an NEF decoder at 2246.3% CPU, i.e. by using about 22 cores.

[para 711 | 5.4 Reading Each Simulator’s Results] "Figure 21 The home page with only snnTorch selected."
MUST CHANGE - Stale figure, and doubly so for snnTorch: besides the dark-to-light surface change, snnTorch's series colour was re-stepped from #1fa989 to #17997b to clear 3:1 contrast, so an old screenshot shows a colour the dashboard no longer uses. Re-capture with the new palette, on-bar value labels and the companion results table. snnTorch's numbers also moved - 13.07 ms, k = 0.921, 1071.8 MB.

[para 712 | 5.4 Reading Each Simulator’s Results] "Its inference at 100 neurons takes 14.42 ms, its scaling exponent is 0.895 and its peak me..."
MUST CHANGE - All three numbers are wrong. Inference at N = 100 is 13.07 ms (0.01307 s), not 14.42 ms. The scaling exponent is k = 0.921 (95% CI [0.245, 1.597]), not 0.895. Peak memory at N = 10,000 is 1071.8 MB, not 1,069 MB. The very wide CI on k should be quoted alongside it.

[para 712 | 5.4 Reading Each Simulator’s Results] "Its power-law fit is weaker (r² = 0.87), so the Scalability page advises reading the measu..."
MUST CHANGE - 'r2 = 0.87' - snntorch/cpu's power-law fit is R2 = 0.862, which rounds to 0.86. The substantive point is stronger than the chapter states: the 95% CI on k is [0.245, 1.597], so the exponent is compatible with anything from strongly sub-linear to strongly super-linear. What the Scalability page advises is a claim about the page's copy - check it against the current build, where the companion results table now supplies the measured points directly.

[para 715 | 5.4 Reading Each Simulator’s Results] "Figure 22 The home page with only SpikingJelly selected."
MUST CHANGE - Stale figure: re-capture in the light theme with on-bar value labels and the companion results table. SpikingJelly's numbers moved - 9.91 ms at N = 100, k = 0.960, 1077.2 MB at N = 10,000.

[para 716 | 5.4 Reading Each Simulator’s Results] "It is faster than snnTorch at 100 neurons (6.76 ms), scales with an exponent of 1.026 and ..."
MUST CHANGE - All three numbers are wrong. Inference at N = 100 is 9.91 ms (0.00991 s), not 6.76 ms. The exponent is k = 0.960 (95% CI [0.450, 1.470]), not 1.026 - so it is now slightly SUB-linear, and the chapter must drop any reading of 1.026 as growth faster than the network. Peak memory at N = 10,000 is 1077.2 MB, not 1,075 MB. 'faster than snnTorch at 100 neurons' survives (9.91 against 13.07 ms), but note the exponents have crossed: SpikingJelly's 0.960 is now slightly steeper than snnTorch's 0.921.

[para 716 | 5.4 Reading Each Simulator’s Results] "It has the best accuracy in the study, 97.46%, and trains slightly faster per epoch than s..."
MUST CHANGE - '13.79 against 14.50 seconds at the fixed budget' - neither number exists in the campaign. Per-epoch times are 89.94 s (SpikingJelly) against 90.94 s (snnTorch) at the full budget (60,000 / 10,000 / 10 epochs), and 9.6 s against 10.3 s at the repeat budget (6,000 / 1,000 / 3 epochs). Quote one pair and name the budget. 'best accuracy in the study, 97.46%' is correct.

[para 722 | 5.5 Reading All Simulators Together] "Figure 23 The All Simulators page: every simulator ranked on each headline measure."
MUST CHANGE - Stale figure: besides the theme change, every bar on this page now prints its value with units and is followed by a compact results table carrying the same rows in the same order - so an older screenshot both looks wrong and understates the page. Re-capture, and check the ranked values against the corrections to paras 723-724 below.

[para 723 | 5.5 Reading All Simulators Together] "For inference at 100 neurons the order is NEST (2.12 ms), Nengo (5.01 ms), SpikingJelly (6..."
MUST CHANGE - The ordering survives but every number is wrong. Correct: NEST 2.13 ms (threads2), Nengo 4.76 ms, SpikingJelly 9.91 ms, snnTorch 13.07 ms, Brian2 133.18 ms (NumPy). Add the two framing facts the list needs: the vectorised NumPy control at 1.30 ms is faster than all five, and brian2/cpp_standalone at 1700.39 ms is excluded as compile-dominated.

[para 723 | 5.5 Reading All Simulators Together] "For peak memory at 10,000 neurons it is Brian2 (642 MB), NEST (886 MB), snnTorch (1,069 MB..."
MUST CHANGE - The ordering survives but every number is wrong. Correct: Brian2 644.7 MB (NumPy), NEST 891.3 MB (threads1), snnTorch 1071.8 MB, SpikingJelly 1077.2 MB, Nengo 2206.1 MB. If the surrounding text or the memory page anywhere names SpikingJelly as the largest footprint, that is now wrong at the reference size too: at N = 100 the largest is reference/scalar at 696.4 MB.

[para 728 | 5.6 Chart Forms the Printed Page Does Not Use] "This carries the same information as the rank-agreement statistics in Section 4.10 but sho..."
MUST CHANGE - 'carries the same information as the rank-agreement statistics' - it does not. A two-column slope chart shows only N = 100 and N = 10,000, whereas the rank-agreement statistics cover four sizes against N = 10,000 (Kendall tau-b 0.309 / 0.236 / 0.491 / 0.745 in session A and 0.309 / 0.345 / 0.491 / 0.818 in session B) plus session-to-session agreement at five fixed sizes (0.964 / 0.927 / 0.818 / 0.964 / 0.964). Correct to: it shows which individual backends move between the two extreme sizes, which the aggregate tau does not, but it covers only those two sizes and carries no session-to-session information.

[para 730 | 5.6 Chart Forms the Printed Page Does Not Use] "Figure 24 The rank-order slope chart on the Sensitivity page."
MUST CHANGE - 'Sensitivity' is a genuine route, so the location is right, but the figure is stale on two counts: the light theme, and the ranks themselves, which come from the re-measured sweep. Re-capture/redraw and add the companion results table the redesign requires.

[para 733 | 5.6 Chart Forms the Printed Page Does Not Use] "Figure 25 Scatter and donut views on the Provenance page: measured-vs-reference rate (left..."
MUST CHANGE - Stale figure: re-capture on the light surface. Two additions the redesign requires - each of the two panels is now followed by a compact results table with the same rows in the same order, and the donut carries the caption 'N of M backends pass the equivalence check', which at N = 500 reads 11 of 11. Consider saying so in the caption, since 'pass/fail composition' invites the reader to expect a mixed donut.

[para 737 | 5.7 Evaluation and Benefits to Users] "To test effectiveness, five decisions a researcher choosing a simulator is likely to face ..."
MUST CHANGE - 'To test effectiveness' and 'a researcher ... is likely to face' - a walkthrough performed by the author is not a test of effectiveness, and no evidence establishes which decisions researchers are likely to face. Correct to: 'As a task walkthrough, five simulator-selection decisions were worked through on the dashboard by the author (Table 18)', and state explicitly that no user study was conducted. The count of five and the content of the tasks additionally need the Table 18 body; the tasks must be re-walked on the re-measured data, since every value they land on has moved.

---

## CANNOT VERIFY (22)

[para 674 | 5.1 Accessing and Reproducing the Dashboard] "The reader starts it with a single command (python RUN_DASHBOARD.py, Appendix A) and opens..."
CANNOT VERIFY - Neither the fact base nor the dashboard description records the launch command, the script name `RUN_DASHBOARD.py`, or the port 5000. Evidence needed: the dashboard entry-point script / Appendix A listing, showing the command and the bound host and port.

[para 675 | 5.1 Accessing and Reproducing the Dashboard] "It reads the results database that produced every figure in Chapter 4."
CANNOT VERIFY - ANALYSIS.md states only that the analysis itself was 'Generated from `benchmarks.db`'. That the dashboard reads that same database is not established. Evidence needed: the dashboard's data-access code naming `benchmarks.db` and the run-group filter it applies, so the identity of source between Chapter 4 and the dashboard can be shown rather than asserted.

[para 675 | 5.1 Accessing and Reproducing the Dashboard] "Absolute times will differ on another computer (Section 3.4), but the reader can check whe..."
CANNOT VERIFY - The campaign is one machine only (LT68, WSL2, CPU only). Nothing was measured on a second computer, so neither the claim that absolute times differ nor the claim that orderings and scaling trends survive a change of machine has any measured support here. Evidence needed: a second-machine run, or reword as an explicit expectation rather than something the reader 'can check'. Note that Experiment 4 already shows the ordering is NOT stable even on one machine (Kendall tau-b against N = 10,000 is 0.309 at N = 100 and 0.236 / 0.345 at N = 500).

[para 676 | 5.1 Accessing and Reproducing the Dashboard] "An exported file always contains exactly the rows shown on screen (Section 3.12.3)."
CANNOT VERIFY - The dashboard description says nothing about export behaviour, and the fact base has no export-parity check. 'Always' is an absolute over all filter states. Evidence needed: the Section 3.12.3 test record, or a row-count/row-content comparison between a filtered view and its export for each of the nine routes.

[para 687 | 5.3 The Home Page] "3 Simulator selector."
CANNOT VERIFY - The element numbering (which element is '3') is not established by the fact base or the dashboard description, and the numbering must be redone after the 27 September 2026 redesign in any case. Evidence needed: the re-captured annotated screenshot. That a simulator selector exists is implied by the per-simulator views (Figures 18-22).

[para 688 | 5.3 The Home Page] "4 Headline figures."
CANNOT VERIFY - As above: that headline-figure cards are element '4' is not established. Evidence needed: the re-captured annotated screenshot.

[para 690 | 5.3 The Home Page] "6 Study summary."
CANNOT VERIFY - The element numbering is not established, and must be redone after the redesign. Evidence needed: the re-captured annotated screenshot.

[para 691 | 5.3 The Home Page] "7 Preview cards."
CANNOT VERIFY - The element numbering is not established, and must be redone after the redesign. Evidence needed: the re-captured annotated screenshot.

[para 692 | 5.3 The Home Page] "8 Export all data."
CANNOT VERIFY - The element numbering is not established, and no export feature is documented in the fact base or the dashboard description. Evidence needed: the re-captured annotated screenshot plus the export implementation.

[para 693 | 5.3 The Home Page] "Counts the runs, conditions and backends behind the page: 678 runs, 150 conditions and 11 ..."
CANNOT VERIFY - '11 backends' is correct (the fact base lists exactly eleven). '678 runs' and '150 conditions' have no counterpart anywhere in FACT_BASE.md or ANALYSIS.md; the same two figures were already flagged as unsupported in the Chapter 4 audit. Evidence needed: a run/condition census from `benchmarks.db` restricted to the campaign's run groups. Note the fact base implies at least 21 training conditions (9 full + 9 repeat + 3 partial hidden = 500), so any census must state what it counts.

[para 700 | 5.4 Reading Each Simulator’s Results] "The dotted line at the top is the C++ standalone target, which recompiles on every run; th..."
CANNOT VERIFY - The fact base does call brian2/cpp_standalone 'the compile-dominated target' and does exclude it from the headline spread (106.88x is computed over the other ten), so the substance is consistent. But that the dashboard renders it as a dotted line and omits it from the headline cards is a rendering claim with no supporting evidence here. Evidence needed: the chart code or the re-captured figure. Re-check after the redesign, since every bar now carries a printed value and a companion table row, which a 'dotted line' treatment has to accommodate.

[para 700 | 5.4 Reading Each Simulator’s Results] "This reflects the missing homeostatic mechanisms in the learning setup, not a fault in Bri..."
CANNOT VERIFY - No ablation isolating homeostatic mechanisms exists in the fact base. The only explanation the fact base licenses is a different one: 'Simulators at or near chance are reporting the sample budget, not their learning capability.' Evidence needed: a run with the homeostatic mechanism added, or restate as the sample- budget explanation the fact base gives. Keep the exculpatory half ('not a fault in Brian2') only as the conclusion of whichever explanation is evidenced.

[para 716 | 5.4 Reading Each Simulator’s Results] "Both libraries use the same training procedure, so their close results also act as a check..."
CANNOT VERIFY - The two supporting facts are verified: both use the same surrogate-gradient procedure (the fact base's note column marks both 'Surrogat[e]'), and the results are close (97.46% vs 97.24%; 89.94 vs 90.94 s/epoch; 1322 vs 1311 peak MB; 4922 vs 4984 J). The inference drawn from them - that this 'acts as a check that the benchmark treats the tools fairly' - is not a test that was run. Evidence needed: a stated fairness criterion with a pass threshold, applied and reported; otherwise present the closeness as a consistency observation, and note it covers only the two PyTorch-based libraries, so it says nothing about fairness toward NEST, Brian2 or Nengo.

[para 717 | 5.4 Reading Each Simulator’s Results] "Table 17 Results of each simulator, summarized from Chapter 4."
CANNOT VERIFY - The table body is not in the extracted sentences, so its rows cannot be checked. Evidence needed: the table itself. Warning for the rebuild: every per-simulator value in Section 5.4 that this table summarises is wrong (see paras 700-716), and the caption's promise of agreement with Chapter 4 only holds once both are regenerated from the 21-27 September 2026 campaign.

[para 728 | 5.6 Chart Forms the Printed Page Does Not Use] "Chapter 4 uses bar and line charts throughout."
CANNOT VERIFY - A claim about Chapter 4's own figure inventory, which is outside both source documents. Evidence needed: Chapter 4's list of figures with each one's chart type.

[para 736 | 5.7 Evaluation and Benefits to Users] "Section 3.12.3 showed that the dashboard meets its functional requirements."
CANNOT VERIFY - Neither source document contains the functional requirements nor the record of a check against them. Evidence needed: the Section 3.12.3 requirement list with the pass/fail result per requirement, re-run against the post-27-September build (the redesign added on-bar value labels, per-figure results tables, sensitivity tau and size labels and the equivalence caption, any of which may bear on the requirements).

[para 736 | 5.7 Evaluation and Benefits to Users] "This section asks the questions raised by the dashboard literature in Section 2.8: does th..."
CANNOT VERIFY - Section 2.8's content is outside both source documents, so what the literature 'raised' cannot be checked. More importantly, the first question as posed - 'does the dashboard help users with their task' - is one this chapter cannot answer: no user study was run, only a task walkthrough by the author and a check against published dashboard criteria. Evidence needed: either a user study, or reword the question to what was actually done ('can the intended tasks be completed on the dashboard, and how does its design compare with published dashboard criteria').

[para 737 | 5.7 Evaluation and Benefits to Users] "Each was answered in at most two actions, a selection and a page, and every answer matched..."
CANNOT VERIFY - Two separate claims, neither supported. 'At most two actions' needs the walkthrough log (which action counted as an action, and for each of the five tasks). 'Every answer matched the corresponding table in Chapter 4' cannot stand on the old walkthrough at all: the campaign was re-measured and the Chapter 4 audit found 53 statements that must change, so both sides of the comparison have moved. Evidence needed: the walkthrough re-run against the current dashboard and the corrected Chapter 4 tables, with the action count and the matched value recorded per task.

[para 738 | 5.7 Evaluation and Benefits to Users] "Table 18 Representative simulator-selection tasks worked through on the dashboard."
CANNOT VERIFY - That a walkthrough was performed is established, but 'Representative' asserts that these five tasks stand for what real users need, which no user study or practitioner survey supports. Evidence needed: a source for the task set (a survey, a published task taxonomy, or supervisor-set tasks), or retitle to 'Five simulator-selection tasks worked through on the dashboard by the author'. The table body is also not in the extracted sentences and must be re-checked against the corrected values.

[para 739 | 5.7 Evaluation and Benefits to Users] "Section 2.8 found that users are most satisfied when a dashboard answers their own questio..."
CANNOT VERIFY - A literature claim attributed to Section 2.8, outside both source documents. Evidence needed: the cited studies, with the satisfaction findings they report. Keep the attribution explicit, because no satisfaction was measured for THIS dashboard - the sentence must not be allowed to read as a finding about it.

[para 739 | 5.7 Evaluation and Benefits to Users] "Compared with the benchmark dashboards of other fields (Table 5), it adds a test of whethe..."
CANNOT VERIFY - The rank-stability material itself is real (the Sensitivity page rests on Kendall tau-b values that are in the fact base), but 'compared with the benchmark dashboards of other fields ... it adds' is a novelty claim over a surveyed set. Evidence needed: the Table 5 survey, showing for each surveyed dashboard that it offers no rank-stability check. Without that, weaken to 'unlike the dashboards surveyed in Table 5, it also reports whether a ranking holds across network sizes'.

[para 740 | 5.7 Evaluation and Benefits to Users] "Checked against the dashboard criteria of Almasi et al. [86], the design supports usefulne..."
CANNOT VERIFY - The criteria check against Almasi et al. was performed, so the framing is legitimate, but every supporting clause needs evidence that is not in either source document: that the dashboard is read-only and reports problems in words, that one layout is used across all nine routes, and that a scope note and footer carry situational awareness. 'Usefulness and suitability for tasks (Table 18)' additionally rests on an author walkthrough, which cannot establish usefulness to users. Evidence needed: a criterion-by-criterion mapping to concrete dashboard features, re-checked against the post-27-September build, plus an explicit statement that no usability or user-satisfaction evaluation was carried out.

---

## VERIFIED (17)

[para 678 | 5.2 Navigating the Dashboard] "It lists nine pages (Table 16)."
VERIFIED - The dashboard serves nine routes: home, all-simulators, inference, scalability, memory, training, sensitivity, provenance, about. Check that Table 16's rows are exactly these nine and in this order.

[para 679 | 5.2 Navigating the Dashboard] "Table 16 Pages of the dashboard and the question each answers."
VERIFIED - Caption is accurate: there are nine pages to tabulate. The table body is not in the extracted sentences; check its rows name the nine routes above.

[para 694 | 5.3 The Home Page] "The fastest at 100 neurons (NEST) is not the most memory-efficient at 10,000 neurons (Bria..."
VERIFIED - All three hold on the new values. Fastest simulator at N = 100: NEST, 2.13 ms (the vectorised NumPy control at 1.30 ms is faster but is a control, not a simulator). Lowest peak memory at N = 10,000: Brian2, 644.7 MB (NEST 891.3, reference 696.4-696.7, snnTorch 1071.8, SpikingJelly 1077.2, Nengo 2206.1). Most accurate learner: SpikingJelly, 97.46%. Three different tools.

[para 700 | 5.4 Reading Each Simulator’s Results] "The training preview shows accuracies below 10%, the chance level."
VERIFIED - Brian2's full-budget accuracies are 9.61% (Cython), 9.61% (NumPy) and 9.57% (cpp_standalone), all below the 10% chance level for ten classes.

[para 700 | 5.4 Reading Each Simulator’s Results] "For a reader with a large network and a custom model, Brian2 is the fastest simulator meas..."
VERIFIED - At N = 10,000 brian2/cython is 0.14853 s and brian2/numpy 0.14868 s, ahead of every other simulator (nest/threads4 0.35302, nest/threads2 0.40209, nest/threads1 0.58103, spikingjelly 0.76422, snntorch 0.77200, nengo 4.15104). Only the vectorised NumPy control is faster (0.03572 s) and it is not a simulator. Brian2's 9.57-9.61% training accuracy supports 'not a ready-made learner'.

[para 712 | 5.4 Reading Each Simulator’s Results] "It reaches 97.24% on MNIST with surrogate-gradient training, the second-best accuracy in t..."
VERIFIED - snntorch/cpu reaches 97.24% at the full budget, second only to spikingjelly/cpu at 97.46%, and it is trained with a surrogate-gradient rule per the fact base's note column.

[para 720 | 5.5 Reading All Simulators Together] "The All Simulators page (Figure 23) puts every simulator side by side."
VERIFIED - 'all-simulators' is one of the nine routes the dashboard serves. Re-capture Figure 23 for the light theme, on-bar value labels and the companion results table.

[para 723 | 5.5 Reading All Simulators Together] "The four rankings in Figure 23 are all different."
VERIFIED - On the re-measured values all four candidate rankings are still distinct. Inference at N = 100: NEST, Nengo, SpikingJelly, snnTorch, Brian2. Peak memory at N = 10,000: Brian2, NEST, snnTorch, SpikingJelly, Nengo. Scaling exponent: Brian2 (0.014), snnTorch (0.921), SpikingJelly (0.960), NEST (1.133), Nengo (1.544). Best accuracy: SpikingJelly, snnTorch, Nengo, Brian2, NEST. No two agree.

[para 724 | 5.5 Reading All Simulators Together] "Nengo is second for inference but last for memory and scaling, while Brian2 is last for in..."
VERIFIED - Nengo: 2nd of the five simulators for inference at N = 100 (4.76 ms, behind NEST's 2.13 ms), last for memory at N = 10,000 (2206.1 MB) and steepest for scaling (k = 1.544). Brian2: last for inference at N = 100 (133.18 ms, and 1700.39 ms for the compiling target), first for memory at N = 10,000 (644.7 MB) and flattest for scaling (k = 0.014). The contrast holds on the new values.

[para 725 | 5.5 Reading All Simulators Together] "Its slope chart (Figure 24, Section 5.6) shows how each backend’s rank changes from the sm..."
VERIFIED - The rank reversal the slope chart shows is in the fact base: reference/vectorised leads at both ends, nengo falls from 5th at N = 100 to 11th at N = 10,000 and brian2/cython rises from 10th to 2nd. Redraw the figure from the new rank columns and, per the 27 September redesign, follow it with its compact results table.

[para 725 | 5.5 Reading All Simulators Together] "Together, these two pages carry the central finding of Chapter 4: the best simulator depen..."
VERIFIED - Supported twice over: the ranking reverses across the measured range (nengo 5th -> 11th, brian2/cython 10th -> 2nd), and the four headline rankings are mutually different, so no single backend wins on every measure.

[para 728 | 5.6 Chart Forms the Printed Page Does Not Use] "Figure 24 draws each backend's speed rank at the smallest network size on the left and at ..."
VERIFIED - The form matches the fact base's rank-at-the-extremes table (N = 100 on one side, N = 10,000 on the other). The figure must be redrawn from the new ranks - reference/vectorised 1 -> 1, nest/threads4 2 -> 4, brian2/cython 10 -> 2, nengo 5 -> 11 - and, per the redesign, followed by its results table.

[para 731 | 5.6 Chart Forms the Printed Page Does Not Use] "The remaining two forms appear together on the Provenance page (Figure 25)."
VERIFIED - 'provenance' is one of the nine routes, and the two remaining forms named in the section are the scatter and the donut (Figure 25, left and right). Re-capture the figure for the light theme and its companion tables.

[para 731 | 5.6 Chart Forms the Printed Page Does Not Use] "Here it plots each backend's measured firing rate against the plain-NumPy reference rate, ..."
VERIFIED - Consistent with the equivalence check as recorded: firing rate compared against a reference within a 35% tolerance, closest reference/scalar against reference/vectorised at 0.0% and furthest nest/threads4 at 15.9%. One tightening - the fact base has two NumPy controls (scalar and vectorised); say which one is the reference line, since the 0.0% pair is the two controls against each other.

[para 731 | 5.6 Chart Forms the Printed Page Does Not Use] "It shows how many selected backends passed the equivalence check and how many failed, at a..."
VERIFIED - Matches the redesign, where the equivalence dots are captioned 'N of M backends pass the equivalence check'. One caution for the surrounding text: at N = 500 the result is 11 of 11 passing within the 35% tolerance, so the failed count is zero and the donut is a single segment with every simulator selected. Do not let the phrasing imply that failures were observed.

[para 731 | 5.6 Chart Forms the Printed Page Does Not Use] "None of these three forms changes a number reported in Chapter 4."
VERIFIED - The three forms - rank-order slope chart, measured-vs-reference scatter, pass/fail donut - re-present values already in the campaign (rank columns at the two extreme sizes, the firing-rate equivalence deviations, the 11-of-11 pass count) and introduce none of their own. Note separately that Chapter 4's numbers have changed for a different reason: the campaign was re-measured.

[para 743 | 5.8 Conclusion] "The dashboard turns the measurements of Chapter 4 into something a researcher can explore."
VERIFIED - Supportable as written: the dashboard presents the campaign's measurements across nine routes with a simulator selector. Keep it descriptive - it must not be read as a usability or user-satisfaction finding, since neither was measured.

---

## SUMMARY

Deduplicated and in priority order. Numbers in brackets are the paragraphs affected.

1. **The fastest-inference headline is wrong wherever it appears.** It is NEST with **two** threads at
   **2.13 ms**, not NEST/threads4 at 2.12 ms - this hits the example card text, the NEST walkthrough and
   the All Simulators ranking. Add that Holm does not separate NEST's thread counts at N = 100
   (threads1 vs 2 p = 0.723, 2 vs 4 p = 0.723, 1 vs 4 p = 0.419), so the card reports a median, not a
   demonstrated winner. (paras 688, 704, 723)

2. **The flattest-scaling headline is wrong.** It is **brian2/cython at k = 0.014**, 95% CI
   [-0.014, 0.043], and the CI spans zero, so it must be reported as indistinguishable from zero. The
   quoted 0.023 is brian2/cpp_standalone; brian2/numpy is 0.017. (para 700)

3. **Every per-simulator inference time in Section 5.4 and 5.5 is wrong.** Correct at N = 100: NEST
   2.13 ms, Nengo 4.76 ms, SpikingJelly 9.91 ms, snnTorch 13.07 ms, Brian2 133.18 ms (NumPy - not
   Cython's 139.33 ms). The printed 2.12 / 5.01 / 6.76 / 14.42 / 133.58 must all change; the ordering
   itself survives. The vectorised NumPy control at 1.30 ms outranks all five, and
   brian2/cpp_standalone at 1700.39 ms is excluded as compile-dominated. (paras 700, 704, 708, 712,
   716, 723)

4. **Every per-simulator memory figure at N = 10,000 is wrong.** Correct: Brian2 644.7 MB, NEST
   891.3 MB, snnTorch 1071.8 MB, SpikingJelly 1077.2 MB, Nengo 2206.1 MB, against the printed 642 /
   886 / 1,069 / 1,075 / 2,204. Separately, the largest footprint at the reference size is
   **reference/scalar at 696.4 MB**, not SpikingJelly - check Table 17 and the memory page for that
   error. (paras 700, 704, 708, 712, 716, 723)

5. **Every scaling exponent quoted per simulator is wrong.** Correct: Brian2 0.014 (Cython), snnTorch
   0.921 (CI [0.245, 1.597]), SpikingJelly 0.960 (CI [0.450, 1.470]), NEST 1.133-1.159, Nengo 1.544,
   against the printed 0.023 / 0.895 / 1.026 / 1.151-1.199 / 1.550. Two consequences: SpikingJelly is
   now slightly SUB-linear, so any reading of 1.026 as growth faster than the network goes; and the
   exponents of the two gradient libraries have crossed. snnTorch's fit is R2 = **0.862**, not 0.87.
   (paras 700, 704, 708, 712, 716)

6. **"Four threads give no gain over two at 10,000 neurons" is contradicted by the data.** At
   N = 10,000 nest/threads4 is 0.35302 s against threads2 at 0.40209 s, and four threads are faster at
   every measured size. The defensible claim is that the gain is small and sub-linear (about 1.14x for
   2x the threads), that it costs energy (78.156 J against 44.335 J), and that at N = 100 the thread
   counts are not separated at all. (para 704)

7. **The training numbers for the two gradient libraries are wrong.** "13.79 against 14.50 seconds"
   exists nowhere: it is 89.94 against 90.94 s/epoch at the full budget, or 9.6 against 10.3 s/epoch at
   the repeat budget - name the budget. NEST's best accuracy is **8.50%** (threads1), not 8.41%, and
   8.24-8.50% is below the 10% chance level, not at it. Nengo's 85.44% comes at 2.90 s/epoch, about
   **29 s** for the 10-epoch budget, not "a few seconds". (paras 704, 708, 716)

8. **No user study was run, and three sentences currently imply otherwise.** "To test effectiveness"
   (para 737), "Representative ... tasks" (para 738) and the usefulness claim inside the Almasi et al.
   check (para 740) all rest on an author walkthrough. Say plainly that the evaluation consisted of a
   task walkthrough by the author plus a check against published dashboard criteria, and that no
   usability or user-satisfaction evaluation was carried out. The Section 2.8 framing question "does the
   dashboard help users with their task" (para 736) must be reworded to something the chapter can
   answer. (paras 736, 737, 738, 740)

9. **The 27 September 2026 redesign is undescribed and every figure is stale.** Ten figure references
   and captions (Figures 17-25, paras 682, 684, 699, 703, 707, 711, 715, 722, 730, 733) point at
   screenshots showing the dark navy surface, snnTorch's retired #1fa989 green, bars without printed
   values and figures without their companion tables. Re-capture all of them from the current build,
   and add prose for the four features the chapter never mentions: on-bar value labels with units (which
   also means no figure now needs hovering to be read), the compact results table after every figure,
   the tau values and network sizes on the home page's sensitivity blocks, and the
   "N of M backends pass the equivalence check" caption. Note that with 11 of 11 passing at N = 500 the
   equivalence donut is a single segment, so "pass/fail composition" should not imply observed failures.
   (paras 682, 684, 699, 703, 707, 711, 715, 722, 730, 731, 733)

10. **The walkthrough's verification claim has to be re-established.** "Every answer matched the
    corresponding table in Chapter 4" (para 737) rests on a walkthrough over superseded values, and the
    Chapter 4 audit found 53 statements needing change - both sides of that comparison have moved.
    Re-run the five tasks on the current dashboard against the corrected tables and record the action
    count and matched value per task. (para 737)

11. **"The slope chart carries the same information as the rank-agreement statistics" is false.** The
    chart covers only N = 100 and N = 10,000; the tau series covers four sizes against N = 10,000
    (0.309 / 0.236 / 0.491 / 0.745 and 0.309 / 0.345 / 0.491 / 0.818) plus session-to-session agreement
    at five sizes (0.964 / 0.927 / 0.818 / 0.964 / 0.964). Say instead that it shows which individual
    backends move between the extremes, which the aggregate tau does not. (para 728)

12. **The chance-accuracy explanation is not the one the evidence supports.** Chapter 5 attributes
    Brian2's and NEST's sub-chance results to "missing homeostatic mechanisms"; the fact base says only
    that simulators at or near chance are reporting the sample budget, not their learning capability.
    Either run the ablation or adopt the fact base's explanation. (paras 700, 704)

13. **The dashboard was revised a fourth time, so "three iterations" is wrong.** The 27 September 2026
    revision postdates the version the chapter calls final. The three earlier stages also need a
    changelog or version history to be citable at all. (para 676)

14. **The run and condition census is unsupported.** "678 runs, 150 conditions" has no counterpart in
    either source document (the same two numbers were flagged in the Chapter 4 audit); "11 backends" is
    correct. Note the fact base implies at least 21 training conditions (9 full + 9 repeat + 3 partial
    hidden = 500), so any census must state what it counts. (para 693)

15. **Dashboard behaviour asserted but nowhere evidenced.** The launch command and port (para 674), that
    the dashboard reads the Chapter 4 database (para 675), export-row parity "always" (para 676), the
    numbered element inventory 3-8 (paras 687, 688, 690, 691, 692), the dotted-line treatment of the
    compiling target (para 700), read-only operation, problem reporting in words, one layout across all
    nine routes, and the scope note and footer (para 740). Each needs the implementation or a test
    record; the element numbering has to be redone after the redesign regardless. (paras 674, 675, 676,
    687, 688, 690, 691, 692, 700, 740)

16. **Cross-machine generalisation is asserted without a second machine.** The campaign is LT68 only, so
    the reader cannot "check whether the orderings and scaling trends hold" elsewhere on this evidence -
    and Experiment 4 shows the ordering is unstable across sizes even on one machine (tau = 0.309 at
    N = 100 against N = 10,000). (para 675)

17. **Claims resting on material outside both source documents.** Chapter 4's chart inventory (para 728),
    the Section 3.12.3 requirements result (para 736), the Section 2.8 satisfaction literature
    (para 739), the Table 5 novelty comparison (para 739), and the bodies of Tables 17 and 18 (paras
    717, 738). These are checkable, just not from the fact base - supply the referenced material.
    (paras 717, 728, 736, 738, 739)

18. **What survives unchanged, and is worth keeping.** The nine-page count (para 678); the
    three-different-winners framing (para 694); Brian2 fastest of the simulators at N = 10,000
    (para 700); Brian2's sub-chance training accuracies (para 700); snnTorch 97.24%, second-best
    (para 712); all four headline rankings mutually different (para 723); the Nengo/Brian2 mirror-image
    contrast (para 724); the rank reversal across the sweep and the "it depends" conclusion (paras 725,
    728); the Provenance page's scatter and donut being re-presentations that introduce no new numbers
    (para 731). (paras 678, 694, 700, 712, 723, 724, 725, 728, 731, 743)

### Counts per class

| Verdict | Count |
|---|---|
| MUST CHANGE | 30 |
| CANNOT VERIFY | 22 |
| VERIFIED | 17 |
| **Total** | **69** |
