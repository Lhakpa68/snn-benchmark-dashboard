# THESIS NUMBERS

Every value the revised thesis will quote. Source paths are relative to the project root. "Section" is where the number most naturally goes (proposed).

## Table 19 (session A, min-max, equal priorities 50/50/50/0)

Source: `optimization.evaluate_four(N)` (rows[0], rows[1], `scenario_wins`, `pareto`), reproduced in `review/reproduce_output.txt` and `review/VERIFY.md` §3. Section: 5.7.

| N | Winner | Score | Runner-up | Score | Winner grid wins (of 15) | Brian2/Cython grid wins | Pareto-efficient backends |
|---|---|---|---|---|---|---|---|
| 100 | nest/threads4 | 0.2438 | nest/threads2 | 0.2542 | 9 | 6 | 5 |
| 500 | snntorch/cpu | 0.2770 | spikingjelly/cpu | 0.3215 | 6 | 4 | 7 |
| 1,000 | snntorch/cpu | 0.2546 | spikingjelly/cpu | 0.2826 | 5 | 7 | 4 |
| 5,000 | brian2/numpy | 0.0445 | brian2/cython | 0.0453 | 7 | 7 | 4 |
| 10,000 | brian2/cython | 0.0000 | brian2/numpy | 0.0019 | 15 | 15 | 1 |

Published Table 19 rounds scores to 3 d.p. (0.244, 0.277, 0.255, 0.044, 0.000; runner-ups 0.254, 0.322, 0.283, 0.045, 0.002). Note the 500 runner-up is 0.3215 (0.322 rounded). All match.

## Agreement and stability counts

| Number | Value | Source | Section |
|---|---|---|---|
| Min-max vs share-of-total agreement | 41 of 45 profile-size cells | `review/reproduce_output.txt`; `VERIFY.md` §2; function `evaluate_profiles` winners | 5.7 |
| Cells unchanged under all applicable checks (rule in `VERIFY.md` §1) | 26 of 45 | `review/verify.py` from `sensitivity_detail.csv` | 5.7 / limitations |
| Weighted pick differs from runtime-only pick | 33 of 45 | `sensitivity_summary.csv`, column `weighted_vs_runtime_only` | 5.7 |
| Weighted pick differs from rank-sum pick | 13 of 45 | column `weighted_vs_rank_sum` | 5.7 |
| Pick changes under share-of-total | 4 of 45 | column `changes_under_share_normalisation` | 5.7 |
| Pick changes when scalability is removed | 7 of 15 applicable (30 not applicable) | column `changes_without_scalability` | 5.7 |
| Pick changes on session B data | 7 of 45 | column `changes_by_session` | 5.7 |
| Exact ties in the weighted result | 2 cells | column `tied_set_size` | 5.7 |
| Eligible backends | 8 (nine SNN backends minus Brian2 C++ standalone) | `optimization.py:252-257` | 3.11.2 |
| Priority-grid size | 15 (three criteria), 35 (four) | `optimization.py:210-219` | 3.11.2 |
| Cells where winner and runner-up run ranges overlap | 32 of 43 unique-winner cells (11 do not) | `sensitivity_summary.csv` column `runtime_ranges_overlap_winner_vs_runner_up` | 5.7 (descriptive only) |
| Weighted margins below 0.01 cost units | 24 of 45 | `sensitivity_summary.csv` column `margin_to_runner_up` | 5.7 |

## Cell lists

**Changes under share-of-total normalisation** (`review/VERIFY.md` §4; `verify_cells.json`; section 5.7): Accuracy + speed* @ 100; Balanced @ 100; Balanced @ 5,000; Speed + memory @ 5,000.

**Changes on session B** (`review/VERIFY.md` §4; `verify_cells.json`; section 5.7): Accuracy + speed* @ 100; Accuracy + speed* @ 500; Speed + memory @ 500; Accuracy + speed* @ 1,000; Speed + memory @ 1,000; Accuracy + speed* @ 5,000; Fast SNN @ 10,000.

**Changes when scalability is removed (become ties for Memory+scaling)** (`review/VERIFY.md` §4; `verify_cells.json`; section 5.7): Memory + scaling @ 100; Scaling + accuracy* @ 100; Memory + scaling @ 500; Scaling + accuracy* @ 500; Scaling + accuracy* @ 1,000; Scaling + accuracy* @ 5,000; Scaling + accuracy* @ 10,000.

**Exact ties** (`review/VERIFY.md` §4; `verify_cells.json`; section 5.7): Low-memory SNN @ 100; Low-memory SNN @ 500.

**Cells unchanged under all applicable checks:** Accuracy + speed* @ 10,000; Accurate SNN* @ 100; Accurate SNN* @ 500; Accurate SNN* @ 1,000; Accurate SNN* @ 5,000; Accurate SNN* @ 10,000; Balanced @ 500; Balanced @ 1,000; Balanced @ 10,000; Fast SNN @ 100; Fast SNN @ 500; Fast SNN @ 1,000; Fast SNN @ 5,000; Low-memory SNN @ 1,000; Low-memory SNN @ 5,000; Low-memory SNN @ 10,000; Memory + scaling @ 1,000; Memory + scaling @ 5,000; Memory + scaling @ 10,000; Scalable SNN @ 100; Scalable SNN @ 500; Scalable SNN @ 1,000; Scalable SNN @ 5,000; Scalable SNN @ 10,000; Speed + memory @ 100; Speed + memory @ 10,000.

## Worked example: N = 1,000, Balanced (50/50/50/0), session A

Source: `review/worked_example_N1000_balanced.csv` (independent arithmetic from `conditions` rows; module score alongside). Section: 3.11.2 or appendix.

| Normalisation | Backend | Runtime (s) | Growth (MB) | k | Score | Rank | Module score |
|---|---|---|---|---|---|---|---|
| minmax | snntorch/cpu | 0.02243 | 0.062 | 0.9212 | 0.25462 | 1 | 0.25462 |
| minmax | spikingjelly/cpu | 0.02563 | 0.723 | 0.9598 | 0.28258 | 2 | 0.28258 |
| minmax | brian2/cython | 0.13828 | 0.000 | 0.0142 | 0.28337 | 3 | 0.28337 |
| minmax | brian2/numpy | 0.13988 | 1.305 | 0.0173 | 0.29120 | 4 | 0.29120 |
| minmax | nest/threads4 | 0.01422 | 75.914 | 1.1335 | 0.57715 | 5 | 0.57715 |
| minmax | nest/threads2 | 0.01770 | 73.789 | 1.1353 | 0.59548 | 6 | 0.59548 |
| minmax | nest/threads1 | 0.02808 | 72.906 | 1.1586 | 0.65420 | 7 | 0.65420 |
| minmax | nengo/reference | 0.20652 | 41.582 | 1.5444 | 0.84925 | 8 | 0.84925 |
| share | snntorch/cpu | 0.02243 | 0.062 | 0.9212 | 0.05729 | 1 | 0.05729 |
| share | spikingjelly/cpu | 0.02563 | 0.723 | 0.9598 | 0.06179 | 2 | 0.06179 |
| share | brian2/cython | 0.13828 | 0.000 | 0.0142 | 0.07846 | 3 | 0.07846 |
| share | brian2/numpy | 0.13988 | 1.305 | 0.0173 | 0.08113 | 4 | 0.08113 |
| share | nest/threads2 | 0.01770 | 73.789 | 1.1353 | 0.15729 | 5 | 0.15729 |
| share | nest/threads4 | 0.01422 | 75.914 | 1.1335 | 0.15791 | 6 | 0.15791 |
| share | nest/threads1 | 0.02808 | 72.906 | 1.1586 | 0.16315 | 7 | 0.16315 |
| share | nengo/reference | 0.20652 | 41.582 | 1.5444 | 0.24297 | 8 | 0.24297 |

Maximum absolute difference between the independent calculation and the module: 2.78e-17; rank mismatches: 0.

## Consequence results (`review/consequence_*.csv`; section 5.7 or discussion)

| Reuse | N | Reused (ms) | Best at N | Best (ms) | Ratio | Difference (ms) |
|---|---|---|---|---|---|---|
| N=100 choice (NEST/4 threads) | 100 | 1.8223 | nest/threads4 | 1.8223 | 1.0 | 0.0 |
| N=100 choice (NEST/4 threads) | 500 | 7.7752 | nest/threads4 | 7.7752 | 1.0 | 0.0 |
| N=100 choice (NEST/4 threads) | 1,000 | 14.2158 | nest/threads4 | 14.2158 | 1.0 | 0.0 |
| N=100 choice (NEST/4 threads) | 5,000 | 106.0866 | nest/threads4 | 106.0866 | 1.0 | 0.0 |
| N=100 choice (NEST/4 threads) | 10,000 | 353.0154 | brian2/cython | 148.5345 | 2.3767 | 204.4809 |
| N=10,000 choice (Brian2/Cython) | 100 | 137.621 | nest/threads4 | 1.8223 | 75.5218 | 135.7988 |
| N=10,000 choice (Brian2/Cython) | 500 | 148.3041 | nest/threads4 | 7.7752 | 19.074 | 140.5289 |
| N=10,000 choice (Brian2/Cython) | 1,000 | 138.2838 | nest/threads4 | 14.2158 | 9.7275 | 124.0679 |
| N=10,000 choice (Brian2/Cython) | 5,000 | 147.3146 | nest/threads4 | 106.0866 | 1.3886 | 41.228 |
| N=10,000 choice (Brian2/Cython) | 10,000 | 148.5345 | brian2/cython | 148.5345 | 1.0 | 0.0 |

Session-transfer table: `review/consequence_2b_session.csv` (14 rows, two per changed cell). Normalisation and scalability-removal side-by-side: `review/consequence_2c_changes.csv` (22 rows).

## Fit quality and sessions

| Number | Value | Source |
|---|---|---|
| Brian2/Cython R² (reported session A) | 0.454 (k = 0.0142) | `review/_lib.py` refit; `dashboard_data.get_scalability_series()` |
| Brian2/Cython R² (session B) | 0.970 (k = 0.0206) | same, run group `3dd09b61bd76-0077ae` |
| A vs B median runtime difference | median 5.7 %, maximum 41.7 % (SpikingJelly, N = 100) | `review/sessions_criteria_check.txt` |
| A vs B memory growth, maximum absolute difference | 6.3 MB (NEST 2 threads, N = 10,000) | same |
| Exact-zero growth beyond N = 100 | Brian2/Cython at 500 and 1,000; snnTorch at 500 (both sessions) | `review/` check in Phase 1 |

## Tests

| Number | Value |
|---|---|
| Tests before this phase | 26 (8 legacy `evaluate`, 17 four-criterion, 1 data-layer only) |
| Tests now | 42, all passing, 0 expected failures |
| New file | `tests/test_four_criteria_revision.py`, 16 tests |
| Exercising the four-criterion path now | 33 |
| Legacy only | 8 |
