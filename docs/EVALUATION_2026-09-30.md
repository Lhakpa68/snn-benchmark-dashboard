# Formal evaluation of the benchmarking dashboard

**Build evaluated:** 30 September 2026, light-theme build, nine routes, reading `results/benchmarks.db` (campaign of 21–27 September 2026).
**Method:** analytical (expert-inspection) evaluation. No study with participants was run. Every number below was recorded from the running build by an instrumented browser session; none is estimated.
**Instrument:** `evaluate.js`, driving Chromium through Playwright at a 1440 × 1000 viewport. Raw output: `evaluation_raw.json`.

---

## 1. Why an analytical evaluation

Munzner's nested model separates the levels at which a visualisation design can be validated and pairs each with the validation that suits it; several of those validations are *immediate* and need no users at all — the design's encoding and its algorithmic performance among them. Tory and Möller show that expert review is a recognised method in its own right rather than a poor substitute for a user study, and report what it does and does not detect. Farzandipour, Nabovati and Sadeqi Jabali apply heuristic evaluation and cognitive walkthrough side by side to the same interface with five evaluators, and find 104 problems (mean severity 2.34) by heuristic evaluation against 24 (mean severity 2.77) by cognitive walkthrough, with only 33.3 per cent overlap — evidence that the two methods surface different problems and that running both is worthwhile.

Wall et al.'s ICE-T instrument supplies a validated structure for scoring a visualisation against four value components — Insight, Confidence, Essence and Time — through 21 heuristics, and reports acceptable reliability from about five raters.

This evaluation therefore has four strands: a task-based analytical walkthrough with recorded interaction counts and answers verified against the database; a heuristic inspection; an ICE-T scoring; and a comparative feature analysis against published benchmark-reporting systems. Its limitation is stated plainly in §7.

---

## 2. Task-based analytical walkthrough

Ten questions a researcher choosing a simulator would actually ask. For each, the instrument recorded the route or routes visited, the number of interactions beyond opening the page, the wall-clock time from first navigation to the answer being on screen, and the answer text as the interface rendered it. Each answer was then checked against the campaign database independently of the dashboard.

| Task | Question | Routes | Interactions | Time to answer | Answer correct against the database |
|---|---|---|---|---|---|
| T1 | Fastest inference at the reference size? | 1 | 0 | 2.0 s | Yes — NEST / threads2, 2.13 ms |
| T2 | Does that hold at 10,000 neurons? | 2 | 1 | 3.8 s | Yes — the ordering changes; exponents shown per backend |
| T3 | Whose runtime grows most slowly? | 1 | 0 | 2.2 s | Yes — brian2/cython, k = 0.014, CI [−0.014, 0.043] |
| T4 | Smallest peak memory at the largest size? | 1 | 0 | 2.2 s | Yes — brian2/numpy, 645 MB |
| T5 | Cheaper gradient-trained library, at what accuracy? | 2 | 5 | 4.0 s | Yes — SpikingJelly 97.46% against snnTorch 97.24% |
| T6 | Are all backends simulating the same network? | 1 | 0 | 2.2 s | Yes — 11 of 11 pass; worst deviation 15.89% |
| T7 | How repeatable is the quoted median? | 2 | 1 | 4.6 s | Yes — tightest CV 5.2%, loosest 18.6% |
| T8 | Does the ranking survive a change of size or metric? | 1 | 0 | 2.2 s | Yes — brian2/cython moves #10 → #2 |
| T9 | What machine and versions produced these numbers? | 1 | 1 | 2.8 s | Yes — i9-14900HX, Python 3.11.15 |
| T10 | Compare only Brian2 and NEST on inference. | 1 | 3 | 3.2 s | Yes — filtered to five rows, ordering preserved |

**Results.** Ten of ten tasks were completed and every answer matched the database. Eight of the ten needed one interaction or none. The median interaction count was 0.5 and the maximum 5, for the task that required de-selecting four simulators before changing page. The median time from opening the page to the answer being on screen was 2.5 s.

Three of these ten answers appear nowhere in the printed thesis as a single statement — T7's repeatability comparison, T8's per-backend rank movement and T10's filtered two-simulator view — which is the case for the dashboard as a contribution rather than as an illustration of Chapter 4.

---

## 3. Two defects found, and what was done about them

The walkthrough was run twice: once on the build as it stood, and once after correcting what the first pass exposed. Both defects were real inconsistencies, not preferences.

**D1 — Two views of the dashboard disagreed on the flattest-scaling result.** *Severity: major (an incorrect answer, not merely an awkward one).* The headline card on the home page reported brian2/cython at k = 0.014; the Scalability page reported brian2/numpy at k = 0.017. The cause was two different eligibility rules for the same question: the headline admitted any fit with r² ≥ 0.25, the page required r² ≥ 0.5, and brian2/cython's fit (r² = 0.45) fell between them. **Corrected** by applying one rule in both places and by printing the fitted interval beside the exponent, so a weak fit is visible rather than hidden behind a stricter cut-off. The Scalability page now reads: *brian2/cython scales flattest at k = 0.014 (r² = 0.45), 95% CI [−0.014, 0.043] — an interval that includes zero, so the slope is not distinguishable from flat.*

**D2 — The repeatability of the inference medians was not on the Inference page.** *Severity: moderate (the answer existed but was not where the question is asked).* The card titled *Repeatability of the quoted medians*, whose own text describes the runs behind the inference figure, sits on the Memory page because it is drawn from the same run set as the memory figures. A reader asking "can I trust this median?" looks on Inference. **Corrected** by adding a named pointer on the Inference page to that card. T7 now completes in one interaction.

**D3 — The coefficient of variation had two definitions in the same project.** *Severity: major (a statistic silently redefined between two views).* The analysis pipeline and the thesis tables compute CV as the standard deviation over the **median**; the dashboard's run-spread card computes it over the **mean**. For nest/threads2 at the reference size the two give 20.11 per cent and 18.55 per cent. **Corrected** by adopting the conventional definition, standard deviation over the mean, in the pipeline, the thesis tables and the dashboard alike, and by stating the definition explicitly where the statistic is introduced, so the reader is not left to assume which one is meant.

Finding defects is what an evaluation is for; all three are reported here rather than quietly repaired, and the corrected build is the one the thesis describes.

---

## 4. Heuristic inspection

Nielsen's ten usability heuristics, applied by inspection of all nine routes. Severity on the conventional 0–4 scale (0 = not a problem, 4 = catastrophic). One evaluator; see §7.

| Heuristic | Assessment | Severity of the worst issue found |
|---|---|---|
| Visibility of system status | Every page carries a load timestamp and a Refresh control; the selector states what is currently shown in a scope line naming the selected simulators. | 0 |
| Match with the real world | Labels use the terms of the domain — backend, network size, epoch, peak resident set size — and each is defined on the *What the baselines are* page. | 1 — "EFLOP" is used before it is defined on three pages. |
| User control and freedom | The selector has *Select all* and *Clear*; every filter is reversible in one interaction; no action destroys anything. | 0 |
| Consistency and standards | One selector, in the same position, on every page; one colour per simulator everywhere. **D1 was a consistency failure and is corrected.** | 2 (was 3 before D1 was fixed) |
| Error prevention | The interface is read-only, so there is no destructive action to prevent; selecting no simulator yields an explicit empty-state message rather than a blank chart. | 0 |
| Recognition over recall | Values are printed on the bars and repeated in a table beneath every figure, so nothing has to be remembered from a tooltip. | 0 |
| Flexibility and efficiency | Eight of ten evaluation tasks needed one interaction or none; the selection persists across pages. | 1 — no keyboard shortcut for the selector. |
| Aesthetic and minimalist design | Detail tables are held in expanders; each page answers one question, named in its subtitle. | 1 — the Memory page carries three cards and reads as the densest. |
| Help users recognise and recover from errors | Not applicable to a read-only view; where data are absent the page says which condition is missing and why. | 0 |
| Help and documentation | A dedicated reference page explains each simulator, each control and what the dashboard does not claim. | 1 — no inline help on the statistics themselves. |

No issue above severity 2 remains. The severity-2 item is the residue of D1: the two views now agree, but they reach agreement through a shared threshold that is itself a judgement, and the interface states it rather than hiding it.

---

## 5. ICE-T scoring

Wall et al.'s four value components, scored 1–7 by a single rater against the 21 ICE-T heuristics. Single-rater scores are indicative only; the instrument's reported reliability assumes about five raters.

| Component | Score | Basis |
|---|---|---|
| **Insight** — does it afford discoveries the data would not otherwise yield? | 5 | The rank-movement view and the metric-agreement view make the instability finding visible directly; neither has a counterpart in a static table. |
| **Confidence** — does it promote trust in the data and the findings? | 6 | Every figure is backed by a table with the same rows, the individual runs are retained and inspectable, the provenance record is on its own page, and the equivalence check is reported before any timing comparison. |
| **Essence** — does it convey an overall sense of the data? | 5 | Four headline figures and six preview cards give the shape of the campaign on one page; the per-simulator views narrow it without changing the layout. |
| **Time** — does it minimise the time to answer a question? | 6 | Median 2.5 s and a median of 0.5 interactions per task across the ten tasks in §2. |

---

## 6. Measured performance and structure

Recorded for each of the nine routes at a cold load, over ten runs of the instrument.

| Measure | Result |
|---|---|
| Median time to network idle | 686 ms (range 614–725 ms) |
| Median time to first byte | 17 ms (range 13–26 ms) |
| Median transferred payload | 216 kB (range 215–219 kB) |
| Requests per page | 11 on every route |
| Figures carrying a companion results table | 19 of 19 |
| Result sentences stating what a figure shows | 15 across the seven data pages |

Liu and Heer show that an added 500 ms of latency in an interactive visualisation measurably reduces the rate at which users make observations and form generalisations. Every route here settles well inside that budget, and the filter operates in the page without a round trip.

**Colour.** The six simulator colours were re-checked on the light surface with a scripted validator. All five checks pass: every hue sits inside the intended lightness band, all clear the chroma floor, the worst adjacent pair under simulated protanopia is snnTorch against NEST at ΔE 8.7 (tritan 10.2), the worst adjacent pair in normal vision is the NumPy reference against Nengo at ΔE 20.9, and all six reach at least 3:1 contrast against the surface. Because the worst CVD separation sits in the 6–8 band, colour is never the only encoding: every series is also directly labelled and repeated in a table.

---

## 7. What this evaluation does not establish

No study with participants was conducted, so nothing here reports how anyone other than the author finds the interface. The walkthrough, the heuristic inspection and the ICE-T scoring were carried out by the dashboard's own developer, which is the least independent position an evaluator can occupy: Tory and Möller's finding that reviewer composition changes what expert review detects applies directly, and Farzandipour et al.'s comparison assumes five evaluators where this has one. The task set is the author's own construction and may favour the paths the design anticipates.

What the evaluation does establish is narrower and checkable: that ten realistic questions can be answered from the interface, that every answer agrees with the database, how many interactions and how much time each took, that three real defects were found and corrected, and that the build meets stated latency and colour criteria. A study with participants, drawn from the population the dashboard is for, remains the necessary next step and is named as such in the thesis.
