# Thesis rewrite and "simulator" terminology — 20 September 2026

## What changed

### 1. Thesis rewritten for readability
`thesis/Final Thesis Edition - Rewritten.docx/.pdf` replaces
`Final Thesis Edition - CPU corrected.docx/.pdf` (moved to
`_duplicates_to_delete/superseded - thesis before rewrite/`).

* 312 body paragraphs were rewritten in a plainer voice. Average sentence length
  fell from 29 to 17 words; sentences over 35 words fell from 346 to 21.
* Every rewritten paragraph keeps its original numbers, citations and meaning.
  An automated check compared the digit multiset and the citation set of each
  paragraph before and after, and refused any paragraph that differed.
* 49 paragraphs that repeated an explanation given elsewhere were cut down to a
  pointer to the section that explains it in full (8,869 characters removed).
  A check confirmed that every number removed still exists in the section named.
* All added or changed text is highlighted yellow.

### 2. Citations renumbered in order of first appearance
* 172 in-text citations, 87 references.
* Numbers now ascend 1..87 in order of first appearance in the body.
* Every citation hyperlink points at a bookmark on the reference entry its label
  names; 0 citations link to the wrong entry.
* Two adjacent citation groups were re-sorted into ascending order.
* No reference is uncited, and no plain-text "[n]" is left unlinked.

### 3. "Framework" replaced by "simulator"
Applied to the thesis and to the dashboard's user-visible text. Identifiers were
deliberately left alone: the `framework` database column, the `/api/frameworks`
route, the `r.framework` row key, `FRAMEWORK_COLORS`, `allFrameworks`, and the
`snn-dashboard-active-frameworks` storage key all keep their names, because
renaming them would break stored reader selections and the exported CSV headers.
Proper names are also unchanged: Nengo's "Neural Engineering Framework (NEF)",
the NeuroBench framework, and reference titles. "No web framework" (meaning Flask)
also stands.

Files changed: `dashboard/templates/*.html`, `dashboard/static/js/dashboard.js`,
`dashboard/static/css/dashboard.css`, `dashboard/dashboard_theme.py`,
`dashboard/dashboard_data.py`, `dashboard/app.py`, `dashboard/streamlit_app.py`,
`dashboard/RUN_QUICK.py`, `dashboard/README.md`.
Originals: `docs/evidence/dashboard_before_simulator_wording/`.

### 4. Dashboard corrections found while doing this
* The navigation label "All Simulator" is now "All Simulators".
* `home.html` said "ten execution backends"; the campaign has eleven
  (nine simulator backends plus the two NumPy control backends). Corrected here,
  and in two code comments.

### 5. Figures refreshed
* Figures 5.1, 5.2 and 5.3 in the thesis were re-captured from the updated
  dashboard, so the screenshots show the corrected CPU and energy numbers and the
  new wording. Display width is unchanged; height was recomputed from each new
  image's aspect ratio so nothing is stretched.
* `docs/dashboard_screenshots/` was re-captured for all nine pages. The
  4 September set is preserved in `docs/evidence/dashboard_screenshots_2026-09-04/`.

### 6. Three factual corrections in Chapter 5 and Appendix A
* Section 5.4 said "all eight routes"; the dashboard has nine
  (home, all-simulators, inference, scalability, memory, training, sensitivity,
  provenance, about). Re-verified: all nine return HTTP 200, all nine carry the
  simulator selector, and none raises a console error when a simulator is
  de-selected and re-selected.
* Section 5.4 had a dangling sentence ("For verifying this thesis's own results,
  it is."), now "…it is useful."
* Appendix A said the network specification would otherwise be "re-specified four
  times"; there are five simulators.

## Verification performed
* Every dashboard Python module parses; `get_frameworks()` returns 6 entries and
  `get_backends()` returns 11, unchanged from before the rename.
* All nine routes rendered under Chromium with the full backend set: HTTP 200,
  6 simulator chips, 0 page errors, 0 console errors.
* No user-visible "framework" remains in any rendered page.
* Thesis PDF rebuilt (132 pages) and the figure pages inspected.
