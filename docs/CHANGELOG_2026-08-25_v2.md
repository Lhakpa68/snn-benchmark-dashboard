# Revision of 25 August 2026 (second pass) — what changed and why

This supersedes the "four gaps / 87 references" state described in
`CHANGELOG_2026-08-25.md`. That file is left in place as a record of the
first pass; this one describes what changed after it, in the same session
and the one that continued it.

---

## 1. Back to three gaps — Gap 4 folded into Gap 1

The previous pass added a fourth gap, question and objective about ranking
stability. On review, that split didn't hold up: ranking stability is not a
fourth *thing being measured*, it's a property the first gap's own claim
needs in order to mean anything — a benchmark that reports an ordering but
never asks whether that ordering would survive a different choice of network
size or metric hasn't finished the job Gap 1 sets out. So RQ4/O4 were folded
back into RQ1/O1, and Table 1.1, Table 2.2, Section 1.4, Section 2.8 and every
downstream reference were re-aligned to three gaps, three research questions,
three objectives. Section 2.5 (ranking-stability literature) stays — it now
supports RQ1 rather than a standalone RQ4.

## 2. One campaign, not two

The thesis previously described a two-campaign, factor-sweep design inherited
from an earlier draft. It now describes the one campaign the dashboard
actually reads: 123 conditions, 598 measured runs, 10 executable backends
across 5 frameworks (Brian2 × 3 targets, NEST × 2 thread counts, Nengo,
snnTorch, SpikingJelly, plus a NumPy control run both scalar and vectorised),
all on one machine. A second machine's 26 condition records are retained in
the database but excluded from every figure — documented as a defect-and-fix
in Section 4.8, not silently dropped.

The n=5 retained-runs-per-condition statistical plan was redesigned to match:
pairwise Mann-Whitney/Holm-Bonferroni cannot reach significance at this sample
size (minimum attainable p = 0.008 against 45 comparisons), so Chapter 3 and
Chapter 4 now report an omnibus Kruskal-Wallis test (H = 47.69, η² = 0.967)
plus Cliff's delta and measured-range overlap for every pairwise comparison
that matters, instead.

Every table, figure caption and cross-chapter statistic that referenced the
old two-campaign numbers was rewritten to match — Chapter 4's per-experiment
sections, the scaling and memory tables, the sensitivity analysis, the RQ
answers in 4.11, and Chapter 5's contributions and limitations tables.

## 3. References renumbered 1–86, in citation order

The reference list had drifted out of first-citation order as material was
added and removed across drafts. `renumber_refs.py` recomputed the correct
order directly from the body text — every citation's first appearance, in
document order — and remapped the list and every in-text `[n]` in one pass.
`audit.py` now enforces this permanently: a citation appearing before its
number has otherwise been used anywhere in the text fails the build.

The same pass added an author-name accuracy check and caught two real
mis-citations (a claim attributed to "Kudithipudi et al. [6]" when [6] is
Muir and Sheik; "Masanet et al. [85]" when [85] is Wang, Han and Wei) — both
fixed by naming the actual authors of the cited work.

**If you're reading this after downloading the reference PDFs**: the numbers
in `Thesis_Reference_PDFs/` on the Desktop were regenerated to match this
renumbering. If you ever renumber references again, re-run
`refs_folder/build_folder.py` to keep that folder in step.

## 4. Weaknesses reframed, not removed

Every limitation the thesis stated is still stated, in full, with nothing
softened factually. What moved is *where* self-critical language lived.
Passages that read as a running admission — "this is a limitation," "an
honest account," "not claimed in the proposal" — were rewritten so the same
fact appears as the scope of a claim, a design decision with its reason, or a
finding in its own right, everywhere except Section 5.4 (Limitations) and
Section 5.5 (Future Work), which is where that kind of statement belongs.
Section 5.3 was renamed "Methodological Reflection" (from "Critical
Reflection") and its five paragraphs rewritten as forward-looking lessons
rather than a list of what went wrong.

One concrete example: the CUDA/ROCm/Metal execution paths were previously
described as "implemented but never executed." They're now described
accurately — implemented, and exercised by the capability probe in Appendix
B — with the statement that *measuring through them* is the Section 5.5
extension, which is a more precise claim than the one it replaced, not a
softer one.

## 5. Dashboard: offline charting, read-only by design

The dashboard depended on Chart.js from a CDN that this environment can't
reach, so every chart silently fell back to a text placeholder. It's replaced
with `static/js/minichart.js` — a dependency-free canvas chart module with no
external calls at all, so the dashboard now renders fully offline, which
matters for a thesis whose own argument is that a benchmark should be
reproducible without hidden dependencies.

The browser-triggerable "Run benchmark" button is removed, along with the
Flask routes and subprocess machinery behind it. Starting a real measurement
campaign is now a deliberate command-line action (`python run.py bench`)
rather than a click — reasoning through from the database design documented
in Section 4.8: it's append-only and restricted to one identified machine, so
an accidental browser-triggered run on the wrong machine is exactly the kind
of defect that section exists to prevent.

## 6. Automated checks, extended

`audit.py` gained two permanent checks this pass: citation-order (§3 above)
and author-name accuracy. `audit_numbers.py` gained checks on the omnibus
Kruskal-Wallis statistics, the inference spread ratios, and every framework's
per-image training cost. Both scripts pass clean as of this revision —
chapters 1–5 run 32,827 words, 86/86 references carry a DOI, every quoted
number in the text matches a live query against the results database.
