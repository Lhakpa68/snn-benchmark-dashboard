# Chapter 4 revision — SCRIPTED AND VERIFIED, pending two Brian2 rows

## 15 Sep: Brian2/Cython landed at 9.91% and broke two drafted claims

Measured, clean run, no concurrency: **12,610.63 s/epoch, 35.03 h, 9.91%**,
38.2 h wall clock. Two sentences in the draft below are now false and have been
rewritten as data-derived text with guards:

1. **"Ten times the data buys about one percentage point and does not cross
   chance."** NEST gains 0.82-0.99 points. Brian2/Cython gains **2.21** — more
   than double — and lands at 9.91%, which on a 10,000-image test set is only
   **0.3 standard errors** below the 10% chance level. NEST sits 5.7-6.1 SE
   below. So "below chance" is right for NEST and wrong for Brian2, which is
   *indistinguishable from* chance. The text now derives the gain per family and
   switches the verb to "does not exceed ... though the closest of them now sits
   within measurement noise of it" whenever any row comes within 2 SE.

2. **"The projection is therefore a sound upper bound."** False. Brian2/Cython
   measured 35.03 h against a 29.50 h projection — the projection **undershoots
   by 19%**. The passage now says the projection is not a safe ceiling and names
   the backends where measurement exceeded it, which is a stronger and more
   useful finding than the one originally drafted.

Also fixed: the "within a tenth of a percentage point" claim was computing
spread across *both* plasticity families, which at the full budget are 1.5
points apart. It is now computed within each family, which is what the sentence
actually asserts.

My guards were too loose to catch either (gain threshold 3.0 vs an actual 2.21;
no guard at all on the upper-bound claim). Both are now tight.

**Watch:** Brian2/NumPy and cpp_standalone were both 7.80% at the fixed budget.
If they gain like Cython they land near 10.0 and may cross chance, which would
break the core Chapter 4 argument. The script aborts if any plasticity row
reaches 10.0.



**Status:** fully implemented as `apply_ch4_fullrun.py` and tested end-to-end
against synthetic data. Run it when the ninth training row lands:

```
python3 /root/work/thesis/apply_ch4_fullrun.py \
  "/mnt/user-data/uploads/MIT College/Last Edition/full_run_output/benchmarks.db" \
  /root/work/thesis/thesis.docx /root/work/thesis/thesis_fullrun.docx
```

The script refuses to run unless all nine rows are present, aborts if any
plasticity row reaches the 10% chance level, and aborts if the gradient
libraries did not improve — because the prose asserts all three.

**The draft below listed 7 edits. A whole-document search found 10 more places
the revision would have contradicted, so the script applies 17.** The ones the
draft missed:

| # | where | what was wrong |
|---|---|---|
| 8  | para 84 (abstract) | "Nine defects found and corrected" |
| 9  | para 235 (contributions) | "nine defects … four in the harness" |
| 10 | para 472 (ch.4 overview) | same count, stated again |
| 11 | para 608 (ch.4 summary) | same count, stated a third time |
| 12 | para 529 (Table 4.4 lead-in) | "it is that projection, **not an executed run**, that answers…" — would have contradicted the sentence appended to the same paragraph |
| 13 | para 530 (Table 4.4 caption) | "one row per framework/backend combination" — now two |
| 14 | para 533 | "at the same budget" — needed scoping to the fixed budget |
| 15 | para 534 | "it is the projection, not an executed run, that answers the design question" |
| 16 | para 535 (Table 4.5 caption) | did not mention the execution |
| 17 | para 543 | "What Table 4.4 captures … taken at three epochs" — now also ten |
| 18 | **para 661 (Section 6.5)** | proposed carrying out Experiment 2 at full scale as *future work* — the thesis now reports it. Rewritten so the remaining future work is the mechanisms-first version, and the section's own prediction ("a rule that cannot separate classes at 500 images will not separate them at 60 000") is noted as confirmed. |

Two rendering defects were also found and fixed: both tables shipped with
`tblW=auto` and a grid disagreeing with the per-cell widths (Table 4.5's cells
summed to 10,935 twips against an 8,750-twip text column), so cloned rows
rendered at different widths from the originals and the new columns were
crushed. `set_table_widths()` pins both to a fixed layout.

**Section 4.8's figures were wrong in the first draft and are now derived, not asserted.**
The draft claimed NEST at four threads "needs roughly two hundred and eighteen"
attempts and that the fixed-budget campaign "needed about twenty". Both traced
back to a docstring I had written myself — citing it would have been circular.
The log shows what actually happened:

- the cap stopped **threads1 and threads4**, not threads4 alone; threads2 never hit it
- threads4 failed during the labelling pass, *after* all ten epochs
  (`train readout, sample 500/60000` immediately precedes the failure)
- the verbatim message is `NEST subprocess isolation could not complete training
  for threads4 after 200 worker attempts -- giving up`
- original constants confirmed in the pre-patch runner: `chunk_seconds=60,
  max_attempts=200` → ceiling 3.33 h
- derived from measured data: full budget needs 3.89 h (exceeds ceiling);
  fixed budget needs 0.15 h (5% of ceiling, ~9 chunks — not "about twenty")

The script now also (a) re-reads Tables 4.4/4.5 from the thesis and aborts if the
hardcoded baseline disagrees, (b) asserts every quantitative claim the prose
makes, and (c) runs `PRAGMA integrity_check` plus an append-only monotonicity
check on the database, after a torn mirror copy was observed on 14 Sep.

NOTE: `/root/work/patch/runner.py`'s docstring still carries the unverified
218/20 figures. Harmless to execution; correct it after the campaign ends rather
than touching a live run.

Verified: 25 tables preserved, Table 4.4 → 19 rows, Table 4.5 → 7 columns,
Table 4.6 → 6 rows, +3 paragraphs, citations `[26][28][29]` intact, no
`[12][86]` field corruption, every change yellow-highlighted, 136 → 140 pages.

---


Numbers below are measured at hidden 256, 60,000 train / 10,000 test, 10 epochs,
on an idle machine. `<<B2>>` marks text that needs the Brian2 figures before it
can be inserted.

Measured so far, against the 6,000-image / 3-epoch campaign and against
Table 4.5's projection:

| backend | s/epoch | total | projected | ratio | accuracy | was |
|---|---|---|---|---|---|---|
| Nengo | 3.54 (one solve) | 3.54 s | 9.00 s | 2.54× | 85.44% | 85.50% |
| snnTorch | 92.11 | 15.4 m | 24.2 m | 1.58× | 97.24% | 93.20% |
| SpikingJelly | 89.23 | 14.9 m | 23.0 m | 1.55× | 97.46% | 94.10% |
| NEST / 4 threads | 1253.48 | 3.48 h | 3.64 h | 1.05× | 8.39% | 7.40% |
| NEST / 2 threads | 2308.04 | 6.41 h | 6.30 h | 0.98× | 8.32% | 7.50% |
| NEST / 1 thread | 4408.50 | 12.25 h | 11.33 h | 0.93× | 8.41% | 7.50% |
| Brian2 / Cython | 12610.63 | **35.03 h** | 29.5 h | **0.84x** | **9.91%** | 7.70% |
| Brian2 / NumPy | `<<B2>>` | | 44.2 h | | | 7.80% |
| Brian2 / C++ standalone | `<<B2>>` | | 44.6 h | | | 7.80% |

---

## 1. Paragraph 542 — REVISION REQUIRED, not merely an addition

Current text: *"The correct interpretation of these six rows is that they measure
the absence of those mechanisms **and the size of the sample budget** …"*

The full-scale run contradicts the second half of that. The budget was raised
tenfold and the epochs more than tripled, and the result did not move. Leaving
the clause in would assert something the campaign has now disproved.

**Replacement:**

> The correct interpretation of these six rows is that they measure the absence
> of those mechanisms, not the capability of NEST or Brian2, nor the difference
> between their thread counts or code-generation backends, all of which sit
> within a tenth of a percentage point of each other. An earlier version of this
> paragraph also named the sample budget as a cause. That explanation has since
> been tested and can be discarded: re-running the same configurations at the
> full reference budget of 60,000 training images over ten epochs moves NEST
> from 7.40–7.50 per cent to 8.32–8.41 per cent `<<B2>>`, which is still below
> the ten per cent chance level, and leaves the ordering among thread counts
> unchanged. Ten times the data buys about one percentage point and does not
> cross chance. Both frameworks implement spike-timing-dependent plasticity
> correctly; what is missing is the surrounding architecture that makes the rule
> discriminative, and a larger budget does not substitute for it.

## 2. Paragraph 541 — final clause

Current text ends: *"…together with **a significantly larger sample budget** [26], [28], [29]."*

The cited procedure does use a larger budget, so the citation stays accurate;
what changes is that a larger budget is now known to be insufficient on its own.

**Append:**

> The published procedure pairs those three mechanisms with a much larger sample
> budget, and it is worth separating the two. The budget alone was tested here
> by executing the full reference configuration, and it is not what carries the
> result: accuracy rises by roughly one percentage point and remains below
> chance. The mechanisms, not the budget, are what the rows are missing.

## 3. Paragraph 377 (Section 3.7) and paragraph 655 — projection becomes execution

Both currently say the full configuration is given "as a projection … rather
than an actual run". Once the campaign completes, both must say it was executed.
Paragraph 655's clause "because for the plasticity-based rules that
configuration implies between roughly three and a half and forty-five hours"
becomes the reason it was deferred rather than the reason it was never done.

**Replacement for the second half of paragraph 655:**

> The cost of the full reference configuration — 60,000 training and 10,000 test
> images over ten epochs — was originally reported in Table 4.5 as a projection
> from measured per-image cost, because for the plasticity-based rules that
> configuration implies between roughly three and a half and forty-five hours of
> machine time per backend. It has since been executed in full, and Table 4.5
> now carries the measured cost beside the projection it replaces.

## 4. Table 4.5 — add measured and ratio columns

Retitle from *"…and the cost of the full reference specification extrapolated
from it"* to *"…and the cost of the full reference specification, projected and
then measured"*, and add two columns: measured total, and projected ÷ measured.

**New passage to follow the table:**

> Setting the projection beside the execution shows where per-image
> extrapolation is trustworthy. For NEST it is accurate to within seven per cent
> at every thread count, and the three ratios fall on both sides of unity — the
> cost of that rule genuinely is one simulation call per image, so multiplying a
> per-image figure by the image count is the right model, and the measured
> per-image cost barely moves between budgets. For the two gradient libraries
> the projection overestimates by about half again, and for Nengo's closed-form
> solve by a factor of two and a half, because in both cases a share of the
> measured per-image cost at the smaller budget is fixed overhead that does not
> recur: snnTorch costs 2.417 milliseconds per image at 6,000 images and 1.535
> at 60,000. The projection is therefore a sound upper bound rather than an
> estimate, and it is least conservative exactly where a practitioner is most
> likely to rely on it — for the expensive plasticity rules, where the number
> decides whether the run is attempted at all.

## 5. Accuracy at the larger budget — new passage for Section 4.6

> Raising the budget separates the rules by what limits them. The two
> surrogate-gradient libraries gain three to four percentage points, SpikingJelly
> reaching 97.46 and snnTorch 97.24, and converge on each other: 0.22 points
> apart at the full budget against 0.90 at the reduced one, which is further
> evidence that the harness is measuring the shared procedure rather than two
> implementations of it. Nengo does not move at all — 85.44 against 85.50 — which
> is the expected behaviour for a closed-form solve whose ceiling is set by how
> well an ensemble of a given width can represent a 784-dimensional space, not by
> how many examples it is shown. The plasticity rules gain about a point and stay
> below chance. Three different limits are visible in one table: sample
> efficiency for the gradient rules, representational capacity for the decoder
> solve, and a missing homeostatic mechanism for the plasticity rules.

## 6. Paragraph 477 — coverage

Add after the existing sentence about training covering nine backends:

> That coverage describes the fixed-budget campaign. The full reference
> configuration was subsequently executed for the same nine backends `<<B2>>`,
> and both budgets are reported: the fixed-budget rows because they are what
> makes the cross-framework comparison controlled, and the full-budget rows
> because they are what the specification asks for.

## 7. Section 4.8 — new defect entry

> A fourth defect belongs with the three above, and it was found only by running
> the experiment at its full size. The harness isolates each NEST training
> attempt in a disposable subprocess, for the reason Section 3.9 gives, and caps
> the number of attempts. The cap was two hundred, and each attempt ends at a
> sixty-second deadline, so the ceiling on total work was three and a third
> hours. That was ample for the fixed-budget campaign, which needed about twenty
> attempts. At the full reference budget NEST at four threads needs roughly two
> hundred and eighteen, and it stopped one step short of finishing, reporting
> that subprocess isolation "could not complete training after 200 worker
> attempts". The message names NEST, and a reader would reasonably conclude that
> NEST had failed. Nothing had failed except the instrument's own retry budget,
> which had been sized against the old sample count and never revisited when the
> sample count changed. The ceiling was raised to a thousand attempts of five
> minutes and the three NEST configurations then completed normally. The general
> form of this defect is worth stating, because it is not specific to NEST: a
> resilience mechanism whose limits are tuned to one problem size will, at a
> larger size, fail in a way that attributes the fault to the system under test
> rather than to the measuring apparatus.

---

## Insertion mechanics

- Work on a fresh stage of `Final Thesis Edition.docx`.
- Insert paragraphs by creating an empty `w:p` and copying only the anchor's
  `w:pPr`. Never deep-copy the anchor's whole `w:p` — it drags citation fields
  in, which produced a `[12][86][10][41][42]` prefix on the first attempt at the
  Section 3.7 edit.
- Every inserted or altered run gets `WD_COLOR_INDEX.YELLOW`.
- Verify before committing: difflib paragraph diff showing only intended
  changes, and a table count of 25.
- Anchors (indices in the current staged file, which already contains the
  Section 3.7 insertion at 375): 377, 477, 529, 536, 541, 542, 548, 655.
