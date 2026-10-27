# Showing the full-scale campaign in the dashboard

Written 14 Sep 2026 while the campaign was still running. Everything below was
verified against the real databases. Nothing here is assumed.

## What I got wrong first

I predicted the two budgets would land in one database and mix inside the
rankings. They do not, because **the two campaigns live in two different
databases**:

| database | contents |
|---|---|
| `Last Edition/SNN Benchmark Dashboard/results/benchmarks.db` | fixed budget (6,000 / 1,000, 3 epochs) plus stale partial runs at 50000/1, 800/2, 300/1 |
| `Last Edition/full_run_output/benchmarks.db` (mirror of the WSL original) | full reference budget (60,000 / 10,000, 10 epochs) |

I started building a fix before checking that. The check should have come first.

## The real blocker

`dashboard_data.CANONICAL_RUN_GROUPS` is hardcoded to the two run-groups of the
**original** campaign:

    "3dd09b61bd76-fb0ab3"   brian2
    "3dd09b61bd76-1ca062"   nest, nengo, snntorch, spikingjelly, reference

Every query is restricted to those — the Section 4.8 defect-#3 remedy,
"restrict every query to one verified campaign". The full-scale campaign has
entirely different run-groups, so **pointing the dashboard at the full-run
database displays nothing at all.** Verified: the training API returned `[]`.

This is the thing that would otherwise have looked like "the dashboard is
broken" once the campaign finished.

## Two defects found and fixed

**1. The de-duplication treated a different sample budget as a duplicate.**
`_LATEST` grouped by `(framework, backend, task, network_size, phase)` keeping
`MAX(id)`. Both budgets sit at hidden width 256, so if the campaigns were ever
merged, one entire budget would vanish silently. Proven: 12 rows in the table,
6 served. Fixed by making the budget (`train_n/epochs`, parsed out of `notes`)
part of the key. Non-training rows key to `''` — verified 0 false positives
across every non-training row in both databases.

**2. Every training figure assumed one row per backend.** The headline accuracy
KPI, the All Simulator ranking, the accuracy bar chart, the cost/accuracy
scatter and the home teaser all took `max(accuracy)` or plotted every row. A
budget selector now gates all of them through `trainRows()`, defaulting to the
largest budget present and collapsing to a plain "Sample budget: ..." label
when only one budget exists.

Worth recording why this mattered: because Nengo's closed-form solve scores
marginally *lower* at the larger budget (85.44 against 85.50), a plain
"highest accuracy per simulator" ranked Nengo on its 6,000-image row while
every other simulator was ranked on its 60,000-image row.

## No regression

The patched data layer returns byte-identical output to the original against
the currently delivered database: 9 training rows, same values, same order.
The stale 50000/800/300 rows stay hidden because they fall outside the
canonical run-groups.

## To do when the campaign finishes

1. Merge the fixed-budget rows into the full-run database:

       python3 tools/merge_fixed_budget.py \
         "<Last Edition>/SNN Benchmark Dashboard/results/benchmarks.db" \
         "<full-run>/results/benchmarks.db" --budget 6000/3 --apply

   Dry-run first by omitting `--apply`. The script refuses to merge across
   machines, refuses a budget already present, and copies only the named
   budget so the stale partial runs are left behind. It also collapses
   brian2/numpy's four duplicate rows to 1591.98 — the Table 4.5 value.
   Both campaigns ran on LT68, so the single-machine control holds; checked.

2. Add the full-run campaign's run-groups to `CANONICAL_RUN_GROUPS`.

3. Deploy the JS, CSS and template changes to the device copy.

Verified end to end on a merged copy: 15 training rows served, 9 at 6000/3 and
6 at 60000/10, correctly separated by budget.

## Not deployed

None of this has been copied to the device. The campaign is mid-flight and the
changes want reviewing together with the merge and the canonical-group update,
which cannot happen until it finishes.

## 19 Sep 2026 — campaign complete; merge direction CORRECTED

The plan above said to merge the fixed-budget rows INTO the full-run database.
That was wrong, and was caught before anything was deployed: the full-run
campaign also re-measured inference and scalability, and those figures differ
from the ones Chapter 4 reports by -22% to +43% (NEST at N=100: 2.242 / 2.068 /
2.175 ms in the thesis against 1.748 / 1.701 / 1.691 ms in the re-measurement).
Pointing the dashboard at the full-run database would have made it contradict
the thesis.

What was done instead, and verified:

1. Started from the thesis campaign's own database (the one the dashboard
   already uses) and added ONLY the nine full-budget training rows:
       merge_fixed_budget.py <full_run.db> <thesis.db copy> --budget 60000/10 --apply
2. Added the nine full-run training run-groups to CANONICAL_RUN_GROUPS.
3. The merge tool's machine check now mirrors the dashboard's own campaign-
   machine rule (majority machine), because the thesis database also holds
   123 old rows from a 2-core instance that the dashboard already excludes.
   A wrong-machine merge is still refused - tested.

Verified, every data endpoint hashed before and after:
    identical: backends, frameworks, gaps, inference, kpis, memory,
               scalability_series, selection_guide, sensitivity, validation
    changed:   training (9 -> 18 rows, both budgets), meta (counts +9/+9)

Rendered in a real browser: no page errors; toggle switches the whole
training ranking between budgets with no mixing.

Bug found by rendering, fixed: setBudget() called render(), which does not
exist; the dashboard's dispatcher is renderCurrentPage(). The toggle threw
"render is not defined" and did nothing until fixed.

Device files were confirmed byte-identical to the pre-change baseline before
proposing deployment, so deploying overwrites no edits made on the machine.
NOT YET DEPLOYED - awaiting Lhakpa's go-ahead.
