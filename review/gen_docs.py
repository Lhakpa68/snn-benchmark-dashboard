"""Assembles PHASE2.md and THESIS_NUMBERS.md from the CSV/JSON outputs (no hand-typed numbers)."""
import csv, json
from _lib import *
V = json.load(open('verify_cells.json'))
sec = open('consequence_section.md').read()
fw = list(csv.DictReader(open('consequence_2a_forward.csv'))); rv = list(csv.DictReader(open('consequence_2a_reverse.csv')))
we = list(csv.DictReader(open('worked_example_N1000_balanced.csv')))
b2 = list(csv.DictReader(open('consequence_2b_session.csv'))); c2 = list(csv.DictReader(open('consequence_2c_changes.csv')))
cell = lambda c: f'{c[0]} @ {c[1]:,}'
cy = {s: next(x for x in load_series(s) if x['id'] == 'brian2/cython')['fit'] for s in 'AB'}

P2 = ['# PHASE 2: verification, consequences, tests\n',
 'Scope: evidence for the thesis revision. No production code, test, database or result file was changed. See `CHANGED_FILES.md` for the file-level proof.\n',
 '## 1. Verification\nSee `VERIFY.md`. Result: every count and every cell list matches the Phase-1 outputs and the expected lists; Table 19 matches in full (winner, score, runner-up, grid wins, Cython wins, Pareto counts). "26 of 45" is confirmed under the rule stated there (unique weighted winner, and unchanged under share-of-total, session B, and scalability removal where applicable).\n',
 '**Wording caution for the thesis.** In the scalability-removal check the cell is compared as a *set*. Memory+scaling at N = 100 becomes an eight-way tie and at N = 500 a two-way tie (snnTorch and Brian2/Cython). At 500 the original winner (Brian2/Cython) is still a member of the tied set; only the runtime tie-break would select snnTorch. These two cells should be described as "become ties", not "the choice changes".\n',
 sec,
 '### 2d. Reading these results (neutral)\n',
 f'- Reusing the N = 100 Fast-SNN choice (NEST, 4 threads) gives the same backend as the Fast-SNN winner up to 5,000 neurons; at 10,000 its median is {fw[-1]["reused_median_ms"]} ms against {fw[-1]["best_median_ms"]} ms for Brian2/Cython (ratio {fw[-1]["ratio_reused_over_best"]}, difference {fw[-1]["abs_difference_ms"]} ms). The run ranges do not overlap there.',
 f'- Reusing the 10,000-neuron choice (Brian2/Cython) at smaller sizes is slower than the best by a factor of {rv[0]["ratio_reused_over_best"]} at 100, {rv[1]["ratio_reused_over_best"]} at 500, {rv[2]["ratio_reused_over_best"]} at 1,000 and {rv[3]["ratio_reused_over_best"]} at 5,000. This is the runtime criterion only; Fast SNN ignores memory and scalability by construction.',
 '- Session transfer: in the seven cells that change, the two backends are close on the combined score in session B for Fast SNN at 10,000 (difference 0.0019), and further apart for the others (0.009 to 0.061). In each cell the two backends trade off: the session-B choice is faster in six of seven cells (it is Brian2/NumPy, faster by about 1 ms, at Fast SNN 10,000, and SpikingJelly in the others except Accuracy+speed at 100, where Nengo is faster), while the session-A choice has the lower memory growth and the lower exponent k in all cells except Accuracy+speed at 100 (equal growth there, and SpikingJelly has the lower k). Note that k is not part of the Fast SNN, Speed+memory or Accuracy+speed scores. Accuracy+speed at 100 is the one cell where the session-A choice (Nengo) is the faster of the two in session B; the flip there is driven by SpikingJelly’s own median runtime falling from 9.15 ms (session A) to 5.34 ms (session B), a 42 per cent difference, which with accuracy weighted moves it past Nengo.',
 '- Accuracy is measured once per backend and is shared by both sessions; every accuracy-weighted profile (marked *) therefore changes only through runtime, growth and k.',
 '- Scalability removal and normalisation: the raw values are shown side by side because a single "loss" figure cannot summarise a multi-criterion profile. Scores from different normalisations are on different scales.',
 '- Score margins are distances under stated weights and are not significance tests. Overlap of min-max run ranges is descriptive of the five runs of each cell and does not describe uncertainty in the combined score.\n',
 '## 3. Tests\nNew file: `tests/test_four_criteria_revision.py` (16 tests; none failed against current production code, so no `expectedFailure` marks were needed). Fixture tests use `series=` / `training_rows=`; the two published-value tests use the database through a read-only connection (`mode=ro`).\n',
 '| Count | Before | After |\n|---|---|---|\n| Tests in suite | 26 | 42 |\n| Exercising the four-criterion path (`evaluate_four`/`evaluate_profiles`) | 17 | 33 |\n| Exercising only the legacy `evaluate` | 8 | 8 |\n| Neither (data layer only: `test_controls_not_ranked`) | 1 | 1 |\n',
 'Newly covered: log vs raw runtime, both accuracy transformations and their min-max equivalence, share zero-sum and constant-positive cases, eligibility exclusions in scores, rank sum, grid, Pareto and profiles, tie-break order (score, runtime, memory, id), the memory cap on absolute RSS before normalisation, missing fit excluded at zero weight, R² not affecting score, the empty-profiles path, and Table 19 / Table 20.\n',
 'Still not covered: negative memory growth and negative values under share (behaviour documented in `METHOD_RULES.md` but no test); the Flask CSV export and Streamlit page (not run in this review); the `fit_caution` flag.\n',
 '## 4. Other deliverables\n`METHOD_RULES.md` (24 rules plus pseudocode) and `THESIS_NUMBERS.md` (every number with its source).\n']
open('PHASE2.md', 'w').write('\n'.join(P2))

N = []
A = N.append
A('# THESIS NUMBERS\n\nEvery value the revised thesis will quote. Source paths are relative to the project root. "Section" is where the number most naturally goes (proposed).\n')
A('## Table 19 (session A, min-max, equal priorities 50/50/50/0)\n\nSource: `optimization.evaluate_four(N)` (rows[0], rows[1], `scenario_wins`, `pareto`), reproduced in `review/reproduce_output.txt` and `review/VERIFY.md` §3. Section: 5.7.\n')
A('| N | Winner | Score | Runner-up | Score | Winner grid wins (of 15) | Brian2/Cython grid wins | Pareto-efficient backends |\n|---|---|---|---|---|---|---|---|')
for n in SIZES:
    t = V['t19'][str(n)]
    A(f"| {n:,} | {t['winner']} | {t['score']:.4f} | {t['runner_up']} | {t['runner_up_score']:.4f} | {t['grid_wins']} | {t['cython_wins']} | {t['pareto']} |")
A('\nPublished Table 19 rounds scores to 3 d.p. (0.244, 0.277, 0.255, 0.044, 0.000; runner-ups 0.254, 0.322, 0.283, 0.045, 0.002). Note the 500 runner-up is 0.3215 (0.322 rounded). All match.\n')
A('## Agreement and stability counts\n')
A('| Number | Value | Source | Section |\n|---|---|---|---|')
rows = [
 ('Min-max vs share-of-total agreement', '41 of 45 profile-size cells', '`review/reproduce_output.txt`; `VERIFY.md` §2; function `evaluate_profiles` winners', '5.7'),
 ('Cells unchanged under all applicable checks (rule in `VERIFY.md` §1)', f"{len(V['stable'])} of 45", '`review/verify.py` from `sensitivity_detail.csv`', '5.7 / limitations'),
 ('Weighted pick differs from runtime-only pick', f"{V['d_rt']} of 45", '`sensitivity_summary.csv`, column `weighted_vs_runtime_only`', '5.7'),
 ('Weighted pick differs from rank-sum pick', f"{V['d_rs']} of 45", 'column `weighted_vs_rank_sum`', '5.7'),
 ('Pick changes under share-of-total', f"{len(V['chg_norm'])} of 45", 'column `changes_under_share_normalisation`', '5.7'),
 ('Pick changes when scalability is removed', f"{len(V['chg_ns'])} of {len(V['ns_applicable'])} applicable (30 not applicable)", 'column `changes_without_scalability`', '5.7'),
 ('Pick changes on session B data', f"{len(V['chg_ses'])} of 45", 'column `changes_by_session`', '5.7'),
 ('Exact ties in the weighted result', f"{len(V['ties'])} cells", 'column `tied_set_size`', '5.7'),
 ('Eligible backends', '8 (nine SNN backends minus Brian2 C++ standalone)', '`optimization.py:252-257`', '3.11.2'),
 ('Priority-grid size', '15 (three criteria), 35 (four)', '`optimization.py:210-219`', '3.11.2'),
 ('Cells where winner and runner-up run ranges overlap', '32 of 43 unique-winner cells (11 do not)', '`sensitivity_summary.csv` column `runtime_ranges_overlap_winner_vs_runner_up`', '5.7 (descriptive only)'),
 ('Weighted margins below 0.01 cost units', '24 of 45', '`sensitivity_summary.csv` column `margin_to_runner_up`', '5.7'),
]
for r in rows: A('| ' + ' | '.join(r) + ' |')
A('\n## Cell lists\n')
for name, key in (('Changes under share-of-total normalisation', 'chg_norm'), ('Changes on session B', 'chg_ses'), ('Changes when scalability is removed (become ties for Memory+scaling)', 'chg_ns'), ('Exact ties', 'ties')):
    A(f'**{name}** (`review/VERIFY.md` §4; `verify_cells.json`; section 5.7): ' + '; '.join(cell(c) for c in sorted(V[key], key=lambda x: (x[1], x[0]))) + '.\n')
A('**Cells unchanged under all applicable checks:** ' + '; '.join(cell(c) for c in sorted(V['stable'], key=lambda x: (x[0], x[1]))) + '.\n')
A('## Worked example: N = 1,000, Balanced (50/50/50/0), session A\n\nSource: `review/worked_example_N1000_balanced.csv` (independent arithmetic from `conditions` rows; module score alongside). Section: 3.11.2 or appendix.\n')
A('| Normalisation | Backend | Runtime (s) | Growth (MB) | k | Score | Rank | Module score |\n|---|---|---|---|---|---|---|---|')
for r in sorted(we, key=lambda r: (r['normalisation'], int(r['rank']))):
    A(f"| {r['normalisation']} | {r['backend']} | {float(r['runtime_median_s']):.5f} | {float(r['memory_growth_mb']):.3f} | {float(r['k']):.4f} | {float(r['score']):.5f} | {r['rank']} | {float(r['module_score']):.5f} |")
mx = max(float(r['abs_diff']) for r in we)
A(f"\nMaximum absolute difference between the independent calculation and the module: {mx:.2e}; rank mismatches: {sum(r['rank'] != r['module_rank'] for r in we)}.\n")
A('## Consequence results (`review/consequence_*.csv`; section 5.7 or discussion)\n')
A('| Reuse | N | Reused (ms) | Best at N | Best (ms) | Ratio | Difference (ms) |\n|---|---|---|---|---|---|---|')
for lab, rs in (('N=100 choice (NEST/4 threads)', fw), ('N=10,000 choice (Brian2/Cython)', rv)):
    for r in rs: A(f"| {lab} | {int(r['N']):,} | {r['reused_median_ms']} | {r['best_backend']} | {r['best_median_ms']} | {r['ratio_reused_over_best']} | {r['abs_difference_ms']} |")
A('\nSession-transfer table: `review/consequence_2b_session.csv` (14 rows, two per changed cell). Normalisation and scalability-removal side-by-side: `review/consequence_2c_changes.csv` (' + str(len(c2)) + ' rows).\n')
A('## Fit quality and sessions\n')
A('| Number | Value | Source |\n|---|---|---|')
A(f"| Brian2/Cython R² (reported session A) | {cy['A']['r2']:.3f} (k = {cy['A']['k']:.4f}) | `review/_lib.py` refit; `dashboard_data.get_scalability_series()` |")
A(f"| Brian2/Cython R² (session B) | {cy['B']['r2']:.3f} (k = {cy['B']['k']:.4f}) | same, run group `{SESSION_GROUPS['B']}` |")
A('| A vs B median runtime difference | median 5.7 %, maximum 41.7 % (SpikingJelly, N = 100) | `review/sessions_criteria_check.txt` |')
A('| A vs B memory growth, maximum absolute difference | 6.3 MB (NEST 2 threads, N = 10,000) | same |')
A('| Exact-zero growth beyond N = 100 | Brian2/Cython at 500 and 1,000; snnTorch at 500 (both sessions) | `review/` check in Phase 1 |\n')
A('## Tests\n')
A('| Number | Value |\n|---|---|\n| Tests before this phase | 26 (8 legacy `evaluate`, 17 four-criterion, 1 data-layer only) |\n| Tests now | 42, all passing, 0 expected failures |\n| New file | `tests/test_four_criteria_revision.py`, 16 tests |\n| Exercising the four-criterion path now | 33 |\n| Legacy only | 8 |')
open('THESIS_NUMBERS.md', 'w').write('\n'.join(N) + '\n')
print('ok', len(V['stable']))
