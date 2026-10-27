# Conditions for merging the new results into thesis V3

## The files (latest, after supervisor feedback, 23 Sep 2026)
`C:\Users\Tsher\OneDrive\Desktop\new updated Thesis\`
- `Final Thesis Draft_Lhakpa V4 (clean).docx` — **the authoritative version** (24 Sep fixes).
- `Final Thesis Draft_Lhakpa V3 (clean).docx` — its parent. New
  content only. 954 paragraphs, 29,187 words, 96 references.
- `Final Thesis Draft_Lhakpa V3 (revised).docx` — the same document with the old
  text struck through and the 14 supervisor comments intact. Reference copy only.

Every further change goes into the **clean** file and must be **red font**.
The `Final Thesis Edition - Rewritten.docx` in `thesis/` is superseded by these.

## Standing conditions for any edit
1. No duplicate content. Where an explanation already exists, point to the
   section that gives it in full.
2. Everything aligns with everything else — no statement contradicts another.
3. Every claim carries reasoning and evidence. Where a result could not be
   obtained, the reason is stated; an unexplained absence is invalid.
4. Gaps, research questions and objectives stay aligned with each other.
5. No absolute statements.
6. The whole reads fluently, like a narrative.
7. Nothing that should be included is missing.
8. Everything present serves a purpose, meets the thesis requirements and
   complies with the guidelines.

Also: human tone, few long or complex sentences; citations 100% genuine,
peer-reviewed, and free to read in full; citation and reference numbering
ascending; real measured data only, never fabricated.

## Supervisor's 14 comments (Belal Chowdhury, 23 Sep 2026)
1. Abstract too long — cut at least 20%; keep gap, method, major finding,
   dashboard contribution, energy-proxy contribution.
2. Too many numerical results in the abstract/intro — they belong in the results.
3. Split the contributions into bullet points.
4. Chapter 2 does not need an Introduction.
5. Incomplete dashboard literature review is a significant gap.
6. Move the dashboard layout into 3.12 The Interactive Dashboard.
7. State why Experiment 2 is a cost comparison, not an accuracy benchmark —
   add a short subsection on the differing learning paradigms and objectives.
8. Contents too long — reduce substantially without losing quality.
9. Excessive discussion of instrument defects — keep what affects validity,
   move the detail to an appendix.
10. The dashboard is not rigorously evaluated for usability, user satisfaction,
    effectiveness or decision support — address them.
11. Chapter 5 is the heart of the thesis but is a small proportion of it —
    strengthen substantially.
12. Show each simulator's result separately, and all simulators together, as an
    option on the dashboard.
13. Some findings are overstated; avoid absolute claims unless exhaustively
    verified. The conclusion has no citations.
14. The conclusion is long and repetitive — no more than one page.

## Defects found and fixed on 24 Sep

The authoritative file is now
`Final Thesis Draft_Lhakpa V4 (clean).docx`, beside the V3 pair. V3 is
untouched. Three real defects were fixed; every addition is red.

1. **The reference list was not in ascending order.** The labels were correct
   and every citation resolved, but the entries sat in the old physical order:
   [1], [6], [72], [73], [74], [7], [8], [2], [3], [4], ... The 96 entries are
   now sorted by label, 1..96.
2. **Reference [48] printed its label twice** ("[48][48] A. Martin-Martin ...").
   The stray leading copy, a hyperlink, was removed.
3. **The conclusion carried no citations**, which is supervisor comment 13. Its
   own earlier citations had been deleted in this revision (the struck-through
   "[16], [17], [18], [68]" line under the removed "6.2 Contributions and Their
   Status"). Eleven citations were added where the text genuinely rests on a
   source, all to entries already cited earlier in the body, so the
   first-appearance ordering is unchanged: [50] for the absence of a common
   benchmark across the five simulators, [9] and [75] for the energy proxy on
   ordinary computers, [88] and [89] for interactive exploration of benchmark
   results, [54] for a ranking being conditional on its measurement choices,
   [80] for making the conditions visible by design, [91] for validation by
   rank rather than against a power meter, [35] for the GPU next step, and
   [85] and [87] for collecting user feedback on a dashboard.

After the fixes: 96 references ascending 1..96; 191 citations, 96 distinct,
first appearance ascending 1..96; every reference cited; 190 hyperlinked
citations, none linked to the wrong entry.

### A warning for the next pass: the "clean" file still has tracked changes
It carries 38 tracked insertions and 13 tracked deletions. `python-docx`'s
`paragraph.text` does not read text inside `w:ins`, so a naive audit reports
headings as empty that Word renders perfectly. An earlier pass on 24 Sep
wrongly reported four defects for exactly this reason - CHAPTER 5 untitled,
section 2.8 unnumbered, 6.1 a number with no title, and Chapter 5 shorter than
it is. All four were false; nothing was changed for them. Any future audit must
read `w:ins` as present and `w:del` as absent. `readtext.py` in the working
copy does this.

## What is verified good in V3
- 96 references, all cited, none orphaned; citations ascend 1..96 by first
  appearance in the body.
- Abstract is 300 words.
- Conclusion is 359 words, within the one-page limit.
- 3.7.1 Learning Paradigms and Optimization Objectives answers comment 7.
- 2.8 answers comment 5; 5.7 answers comment 10 with a task-based evaluation
  against published dashboard criteria, and is honest that no user study was run.
- Chapter 5 now runs 5.1-5.8 with per-simulator and all-simulator pages
  (comments 11 and 12).

---

# Instructions added 27 Sep 2026 (for the post-results pass)

## Thesis
1. Update every result in the thesis from the new campaign, missing none.
2. Update the explanation of each result to match, with no mistakes.
3. Check the whole thesis for discrepancies.
4. No unrelated content or explanation anywhere.
5. Do not compromise content flow or quality.
6. After every change, re-check that everything still fits together - content,
   citations, references, cross-references, tables and figures.
7. **Hard cap: 30,000 words.** The draft stands at 29,120 (changes accepted),
   so new results text has to be paid for by cutting elsewhere. The supervisor's
   own comments 8 and 9 name the places: reduce over-long content, and move the
   detailed instrument-defect descriptions to an appendix, keeping only what
   bears on validity. Cut there first.
8. Dashboard changes, then reflect them in the thesis:
   a. Several home-page figures show no numbers until the cursor hovers, which
      makes them hard to read. Put the values on the marks themselves.
   b. Every figure gets its results table with it - table below the figure, or
      beside it when both are small enough.
   c. Lighten the theme, icons, menu and tabs. The supervisor finds the current
      palette too dark.
9. Then deliver: the final thesis, plus a complete working bundle of code,
   datasets and dashboard ready to upload to the institute repository and
   GitHub.

## Order of work
The dashboard changes (8a-8c) do not depend on the campaign and can be done
while it finishes. Re-capture the thesis figures from the changed dashboard
only after the numbers are final, so the screenshots show the final data and
the lighter theme together.

## Word-count decision, 27 Sep 2026
Confirmed: make room under the 30,000 cap by following the supervisor's own
comments rather than choosing sections independently.
- Comment 8: reduce the over-long content without losing quality.
- Comment 9: keep only the instrument defects that bear on validity in
  Section 4.8, and move the detailed descriptions to an appendix.
Do the cuts and the results update in ONE pass, so section numbers and every
cross-reference are renumbered once and checked once.

## Mandate widened, 27 Sep 2026
Beyond the supervisor's comments 8 and 9, cuts may be made from ANY chapter or
section whose content does not make a genuine contribution or sits loosely
against the thesis, provided the cut does not reduce quality. Judge each
candidate on whether removing it costs the reader anything: an argument, a
piece of evidence, a needed definition, or a link in the narrative. If it does,
keep it.

### Cut plan drafted 27 Sep, from a section-by-section survey of V4
The document stands at 29,131 words with changes accepted (3,261 of them the
reference list). Note that moving text into an appendix does NOT reduce the
total, so comment 9's move buys structure, not room; the room has to come from
real cuts. Budget needed: about 800-1,200 words, to pay for the new training
measurements and for strengthening Chapter 5.

| Section | Now | Target | Saves | Why it can go |
|---|---|---|---|---|
| 3.12.4 Dashboard Architecture | 799 | ~300 | ~500 | A module-by-module inventory of the code. The design *finding* earns its place under RQ3; the file listing belongs in the repository README, which ships with the code. |
| 2.3 The SNN Simulator Landscape | 1016 | ~850 | ~165 | Per-simulator description that Chapter 3 states again when it sets each one up. |
| 2.4 Comparative and Benchmarking Studies | 986 | ~850 | ~135 | Study-by-study description beyond what the gap argument needs. |
| 3.10 Statistical Analysis Plan | 743 | ~620 | ~120 | Restates what standard tests do; the choices and thresholds stay. |
| 2.7 Energy Measurement Approaches | 723 | ~640 | ~85 | Third-approach description overlaps 3.9. |
| 2.6 Application and Deployment Environment | 142 | ~90 | ~50 | The loosest fit in the review: application papers that motivate SNNs but bear on no gap, question or objective. |
| 4.4 / 4.5 narrative | — | — | ~150 | Sentences restating a table the reader is looking at. |

Rule for every cut: remove it only if the reader loses no argument, no
evidence, no definition and no link in the narrative. If any of those go with
it, keep it and find the words elsewhere.
