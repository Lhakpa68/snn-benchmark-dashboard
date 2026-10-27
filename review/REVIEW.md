# Review: backend-selection code vs thesis V6

Status: REVIEW ONLY. No existing code, tests, database or result file was modified. All new files are in `review/`.
Run with `PYTHONDONTWRITEBYTECODE=1 python3 <script>` from inside `review/`.

| File | Purpose |
|---|---|
| `reproduce.py` / `reproduce_output.txt` | Regenerates Tables 19 and 20 with the existing functions |
| `worked_example.py` / `worked_example_N1000_balanced.csv` | N = 1,000, Balanced, both normalisations, plain arithmetic from raw DB rows |
| `sensitivity.py` / `sensitivity_detail.csv` (255 rows) / `sensitivity_summary.csv` (45 rows) / `sessions_criteria_check.txt` | Part 3 |
| `_lib.py` | Read-only independent loader (raw `conditions` rows of one run group) and own OLS fit |

All code references are to `dashboard/optimization.py` (O) unless stated; `dashboard_data.py` is (D).

---

## 1. Audit table

Selection path audited: `evaluate_four` (O:222) and `evaluate_profiles` (O:432), which is what the Flask page, CSV export and Streamlit use (`app.py:166-232`). The older `evaluate` (O:52) is legacy and not used by the pages.

| # | Item | Actual behaviour | Evidence | Test covering it | Does V6 agree? |
|---|---|---|---|---|---|
| 1 | Accuracy transformation | **Depends on normalisation.** Min-max: shortfall from the *best observed* accuracy, `(high - val)/(high - low)`. Share: shortfall from *100 %*, `100 - acc`. | O:156 (`benefit=True`), O:170 | `test_one_hot_weight_winner_matches_measurement` (winner = max accuracy only). No test of the transformed value. | **Partly.** §3.11.2 says "shortfall from the best value" (accuracy criterion paragraph) and, after Eq 17, "under both normalisations ... shortfall from 100 per cent". Each sentence is true for one path only. This is the known inconsistency. |
| 2 | Runtime: raw or log | Min-max: **log** (`math.log` before scaling). Share: **raw** seconds (no log). Memory growth and k are linear under both. | O:320 (`logarithmic=True`), O:316 (`_share_cost` has no log) | Share-raw: `test_share_cost_is_value_over_total`. Min-max log: none (indirect via Table 19 only). | **Partly.** "runtime enters as its logarithm" is attached to Eq 16 (min-max) so it is correct there; the text does not say the share form uses raw runtime. |
| 3 | Memory growth | `growth = mem(N) - mem(first point with truthy mem)`; `first` is the smallest measured size (100 here). **No clamping**; negative values would pass through. Min-max linear scale. Share shifts by the minimum if any value < 0. | O:284-289, O:156, O:172-174 | `test_memory_growth_not_absolute_footprint` (growth = mem - base; all zero at N = 100). Negative growth: none. | **Agrees** with Eq 15 for this data (base = N 100). Text says `N_0 = 100`; code says "smallest measured size with a non-zero reading". Data: no negative growth in either session (checked). **Exact zero growth at N > 100 does occur**: Brian2/Cython at 500 and 1,000 and snnTorch at 500, in both sessions. |
| 4 | Scalability k | k comes from **session A only** (`INFSCAL_RUN_GROUPS` has one group, `...-fb679a`; session B `...-0077ae` is a labelled replication, never mixed in). k = OLS of log10(median runtime) on log10(N) over the five sizes. **R² is never used in scoring**; it only sets `fit_caution` (R² < 0.8) for display. A missing fit (< 3 sizes) **excludes the backend even when the scalability weight is 0.** | D:118-120, D:136-138, D:184-208, D:396-433; O:271-278, O:304 | `test_one_hot...` (k winner). R²-not-used: none. Missing-fit exclusion: none. | **Agrees** (Eq 6, R² shown). The exclusion-on-zero-weight rule (O:274 comment) is **not stated** in V6. |
| 5 | Importance to weight | Each importance must be finite in [0, 100]; `W = q / sum(q)`. | O:138-149 | `test_normalisation_any_nonzero_four_raw`, `test_memory_cap_and_bad_weights` (negative rejected) | **Agrees** (Eq 18). |
| 6 | All priorities zero | `ValueError('At least one criterion must have a positive weight.')`. Flask page catches it and shows defaults with a message. | O:147-148; `app.py:187-190` | `test_memory_cap_and_bad_weights` | Not described in V6 (UI behaviour). |
| 7 | Constant criterion | **Min-max:** cost 0 for all, "contributes nothing" is exactly true. **Share:** constant *positive* value c gives c/(n c) = 1/n for every backend, so it adds `weight/n` to every score. Ranking is unchanged but **score magnitudes shift**; it does not "contribute nothing" numerically. Constant zero gives 0 under share. | O:156 (`if high > low else 0.0`), O:176 | Min-max, zero growth: `test_memory_growth_not_absolute_footprint`. Share, constant positive: none. | **Partly.** True for ranking under both, true for score under min-max only. Not occurring in the data under share (the only constant criterion is all-zero growth at N = 100). |
| 8 | Share corner cases | Sum 0: cost 0 (O:176). Any negative value: all values shifted by the minimum (O:172-174), so it is **no longer x/Σx** and the minimum backend gets cost 0. No epsilon for near-zero sums; no special handling of k near 0. | O:163-176 | None | **Not stated** in V6 (Eq 17 is plain x/Σx). Not triggered by the data (all k > 0, no negative growth). |
| 9 | Missing / NaN / inf | Runtime or memory None, NaN, inf or ≤ 0: excluded as `invalid`. k None/non-finite: excluded `missing_scaling`. Growth non-finite: excluded `invalid`. Accuracy missing: excluded only if accuracy weight > 0 (`missing_accuracy`); NaN or outside 0-100 accuracy rows are dropped before lookup. Nothing is imputed. Weights NaN/inf rejected. | O:242-246, O:263-267, O:273-278, O:287-293, O:144 | Only `test_missing_accuracy_is_not_filled_or_imputed`. | **Agrees** ("excluded, not scored zero"). |
| 10 | Memory cap | Applied **before** normalisation, as an eligibility filter on **absolute** peak RSS at size N (`mem > cap`), although scoring uses *growth*. Normalisation, rank sum, Pareto, grid and profiles are then all computed on the reduced set. | O:268-270 | `test_memory_cap_and_bad_weights` (cap = 50 MB leaves nothing). Cap that removes only some backends: tested only on the legacy `evaluate` (`test_memory_cap`). | **Agrees** with "removes backends above it"; V6 does not say the cap acts on absolute RSS while the score uses growth. |
| 11 | Eligibility in every path | Controls (`framework == 'reference'`) and compile-dominated rows are dropped in the single loop at O:252-257 **before** any criterion is computed, so scores, rank sum, Pareto, grid, every profile (each calls `evaluate_four`) and the CSV (`result['rows']`) inherit it. Eligible set = **8** backends (9 SNN backends minus Brian2 C++ standalone). The set can differ **per profile** (accuracy-weighted profiles need an accuracy row). | O:252-257, O:307-345; `app.py:217-232` | `test_baseline_and_compiler_excluded` tests the **legacy** `evaluate`, not `evaluate_four`. `test_controls_not_ranked` only counts series. | **Agrees.** Gap: no test asserts it for `evaluate_four`, `rank_sum`, grid, profiles or CSV. |
| 12 | Ties | Order key `(round(score, 12), runtime_s, memory_mb, id)`: ties at 12 decimals are broken **silently by lower runtime**, then memory, then id. `evaluate_four` returns one winner and no tie flag. `evaluate_profiles` marks a profile `tied` (winner `None`) **only when every backend ties** (spread ≤ 1e-12). Partial ties are not flagged. | O:206, O:449-454 | `test_memory_profile_tied_at_smallest_size` (all-tie only). | **Partly.** V6 says the low-memory profile "cannot choose" at N = 100 (correct, all 8 tie). **Table 20 shows snnTorch for Low-memory at N = 500, but snnTorch and Brian2/Cython tie exactly (growth 0.0 MB each); the code picks snnTorch by shorter runtime.** |
| 13 | No eligible candidates | `evaluate_four` returns `ok=False, rows=[], winner=None, notice=...`. `evaluate_profiles` skips that profile's column. | O:311-313, O:447-448 | `test_memory_cap_and_bad_weights` (evaluate_four). `evaluate_profiles` no-candidate path: none. | Not described in V6. |
| 14 | Rank sum | Sum over **active** criteria (weight > 0) of the rank on the **raw** value (runtime, growth, k; accuracy higher-is-better). Ties share the average rank (relative tolerance 1e-12). `rank_sum_position` breaks remaining ties by id. Not weighted. | O:179-198 | `test_rank_sum_is_sum_of_criterion_ranks` (total = 3·n(n+1)/2; min rank-sum = winner at default N = 10,000, a data-dependent check). | **Agrees** ("sum of ranks on the active criteria"). Tie rule not stated. Rank-sum and weighted winner **differ in 13 of 45** profile-size cells (section 4). |
| 15 | Priority grid | `product(range(5), repeat=m)` with sum 4 gives 15 compositions for 3 criteria, 35 for 4. The fourth criterion enters the grid only if the **reader's** accuracy weight > 0. The grid ignores the reader's weights otherwise. Winner per grid point uses the same tie-break as item 12. | O:210-219, O:340-342 | `test_default_three_metrics_accuracy_zero` (15, wins sum 15), `test_four_equal_weights_and_35_point_sensitivity` (35) | **Agrees** (15 / 35). Note: Pareto (O:331-336) is computed on the active *cost* criteria (incl. growth and k), whereas Figure 25 plots runtime against **absolute** memory with Pareto markers; the two are different notions. |

### 1.1 The 26 existing tests and what they cover

`python3 -m unittest discover -s tests` runs **26 tests, all pass**. They are 8 in `test_optimization.py` (all on the **legacy** two-criterion `evaluate`, 1 real-DB), 10 in `TestFourCriteria`, 1 in `TestSensitivityScope`, 7 in `TestNetworkFormulation`.

| Item | Tests |
|---|---|
| 1 accuracy | `test_one_hot...` (weak) |
| 2 runtime log/raw | `test_share_cost_is_value_over_total` (share only) |
| 3 growth | `test_memory_growth_not_absolute_footprint` |
| 4 k / R² | `test_one_hot...` (k winner only) |
| 5 weights | `test_normalisation_any_nonzero_four_raw`, `test_memory_cap_and_bad_weights`, `test_contributions_sum_to_score` |
| 6 all-zero | `test_memory_cap_and_bad_weights` |
| 7 constant | `test_memory_growth_not_absolute_footprint` (min-max, zero case) |
| 9 missing | `test_missing_accuracy_is_not_filled_or_imputed` |
| 10 cap | `test_memory_cap_and_bad_weights`; legacy `test_memory_cap` |
| 11 eligibility | legacy `test_baseline_and_compiler_excluded`; `test_controls_not_ranked` |
| 12 ties | `test_memory_profile_tied_at_smallest_size` |
| 13 no candidates | `test_memory_cap_and_bad_weights`; legacy `test_no_eligible_returns_readable_result` |
| 14 rank sum | `test_rank_sum_is_sum_of_criterion_ranks` |
| 15 grid | `test_default_three_metrics_accuracy_zero`, `test_four_equal_weights_and_35_point_sensitivity` |
| profiles | `test_profiles_single_criterion_winner_is_best_measurement`, `test_custom_profile_matches_main_result` |
| Misc | `test_network_size_changes_input...`, `test_bad_normalisation_rejected`, `test_share_costs_sum_to_one`, `test_plot_ticks_inside_axes` |

**Gaps (no test):** min-max log runtime; accuracy transformation values under either normalisation (item 1); negative growth; share with negative / zero-sum / constant-positive values; R² not affecting score; missing-fit exclusion at zero scalability weight; eligibility exclusions on the `evaluate_four` path (controls and compile-dominated); partial memory cap; partial ties (the N = 500 low-memory case); tie-break rule; `evaluate_profiles` no-candidate path; Table 19 / Table 20 values themselves (the real-data test checks only the legacy two-criterion winners at N = 100 and 10,000). Note: 8 of the 26 tests exercise only the superseded `evaluate()`, so the "26 of 26" statement in §5.8.2 overstates coverage of the four-criterion method.

---

## 2. Reproduction of published numbers (`reproduce.py`)

**All published values reproduce. Mismatches: none.**

| N | Reproduced winner (score) | Runner-up (score) | Published | Match |
|---|---|---|---|---|
| 100 | NEST/4 threads 0.2438 | NEST/2 threads 0.2542 | 0.244 / 0.254 | yes |
| 500 | snnTorch 0.2770 | SpikingJelly 0.3215 | 0.277 | yes |
| 1,000 | snnTorch 0.2546 | SpikingJelly 0.2826 | 0.255 | yes |
| 5,000 | Brian2/NumPy 0.0445 | Brian2/Cython 0.0453 | 0.044 / 0.045 | yes |
| 10,000 | Brian2/Cython 0.0000 | Brian2/NumPy 0.0019 | 0.000 | yes |

- Table 19 wins: 9/15 at N = 100 (published 9), Brian2/Cython wins 15/15 at 10,000 and is the only Pareto-efficient backend (published).
- Table 20: min-max and share agree on **41 of 45**; the four that differ are exactly the published set (Balanced and Accuracy+speed at 100; Balanced and Speed+memory at 5,000). All 45 min-max cells equal the published Table 20 entries (compared against the table as extracted from the .docx text).
- Brian2/Cython fit: k = 0.0142, **R² = 0.454** (published 0.45), session A.
- The Table 20 "Low-memory, N = 500, snnTorch" cell reproduces only because of the silent tie-break (item 12).

## 3. Worked example: N = 1,000, Balanced (50/50/50/0), session A

Independent arithmetic from raw `conditions` rows (own loader, own OLS fit; no selection module). Full table in `worked_example_N1000_balanced.csv` (raw, transformed, cost, weight, contribution, score, rank, module score).

**Result: maximum absolute difference to the module = 2.8e-17; 0 rank mismatches, both normalisations.**

Weights: q = (50, 50, 50) so W = 1/3 each. Eligible: 8 backends. Memory growth = peak RSS(1,000) − peak RSS(100).

| Backend (min-max) | score | rank | | Backend (share) | score | rank |
|---|---|---|---|---|---|---|
| snnTorch | 0.2546 | 1 | | snnTorch | 0.0573 | 1 |
| SpikingJelly | 0.2826 | 2 | | SpikingJelly | 0.0618 | 2 |
| Brian2/Cython | 0.2834 | 3 | | Brian2/Cython | 0.0785 | 3 |
| Brian2/NumPy | 0.2912 | 4 | | Brian2/NumPy | 0.0811 | 4 |

(Min-max runtime uses log; share uses raw seconds, so the score scales differ by construction. Do not compare the two columns' magnitudes.)

## 4. Sensitivity (existing data only; `sensitivity_summary.csv`)

**D. Session feasibility (`sessions_criteria_check.txt`).** Sessions A (`...-fb679a`) and B (`...-0077ae`) both contain scalability runtime median and peak RSS for all 11 series at all five sizes (k is refit from each session's own five medians). Therefore runtime, growth and k can be recomputed per session. **Accuracy is measured once in the training groups and is shared** by both sessions, so accuracy-bearing profiles in session B hold accuracy constant. Differences A to B: median runtime differs by a median 5.7 %, up to 41.7 % (SpikingJelly at N = 100); memory growth differs by up to 6.3 MB. The dashboard and V6 use session A only; session B is a replication.

| Check (45 profile-size cells) | Result |
|---|---|
| Weighted pick vs **runtime-only** pick | differ in **33**, same in 12 |
| Weighted pick vs **rank-sum** pick | differ in **13**, same in 32 |
| Min-max vs share (session A) | pick changes in **4**, unchanged in 41 |
| Without scalability (profiles with a scalability weight and something left: Balanced, Memory+scaling, Scaling+accuracy; 15 cells) | pick changes in **7**, unchanged in 8; **30 cells not assessable** (25 have no scalability weight, 5 are the scalability-only profile, which has nothing left) |
| Session B instead of A (min-max) | pick changes in **7**, unchanged in 38 |
| Weighted result is a tie of ≥ 2 backends | 2 cells (Low-memory N = 100: all 8; N = 500: snnTorch and Brian2/Cython) |
| Memory-weighted profile at N = 100 with all-zero growth (degenerate) | flagged in `memory_degenerate_flag` (Low-memory, Speed+memory, Memory+scaling at N = 100) |

Cells that change under session B: Fast SNN at 10,000 (Brian2/Cython to Brian2/NumPy; margin between them is 0.0003 in cost units); Speed+memory at 500 and 1,000 (snnTorch to SpikingJelly); Accuracy+speed at 100, 500, 1,000 and 5,000 (to SpikingJelly).

Cells that change without scalability: Scaling+accuracy at all five sizes (snnTorch becomes SpikingJelly, because it reduces to accuracy-only); Memory+scaling at 100 and 500. The latter two are **tie-break artefacts**: without scalability the profile is memory-only, which is all-tied at 100 and tied between snnTorch and Brian2/Cython at 500 (growth 0.0 each), and the runtime tie-break chooses. Balanced and the 10,000 cells do not change when scalability is dropped, so Brian2/Cython's weak fit (session A R² = 0.454) does not by itself drive the Balanced results at 5,000 or 10,000. In session B the same series refits to k = 0.0206, **R² = 0.97**, so the "R² = 0.45" in V6 is a session-A property of that series, not a stable one.

Margins and uncertainty (reported separately, not combined): of 43 cells with a unique weighted winner, the runtime min-max ranges of winner and runner-up **overlap in 32** and do not in 11 (column `runtime_ranges_overlap_winner_vs_runner_up`; five runs per cell, `n_runs` in the data). 24 of 45 weighted margins are below 0.01 in normalised cost units. Margins are score distances under the stated weights, not significance statements, and I do not call any of them significant. Where both the winner and the runner-up fall inside overlapping run ranges, the ordering by median is not separated by this data.

**Interpretation (neutral).** 26 of the 45 cells are stable under all checks that apply (unique winner, no change under share, session or scalability removal). Single-criterion profiles (Accurate, Scalable, and Fast at sizes ≤ 5,000) are stable. Profiles that mix criteria, and everything at 5,000-10,000 where margins are 0.0003-0.003, are fragile to at least one of normalisation, session, or the tie-break. The weighted method often disagrees with the runtime-only pick (33/45), which is expected, since memory and scalability weights are what the method adds. These are valid findings about the robustness of the recommendations and are consistent with V6's own caution that the answer depends on the stated priorities.

---

## 5. Approval table

| Proposed change | Already implemented? | Evidence | Necessary? | Risk | Needs regeneration |
|---|---|---|---|---|---|
| Resolve accuracy wording: min-max = shortfall from best observed, share = shortfall from 100 % | Code implements both; text inconsistent | O:156, O:170; V6 §3.11.2 | Yes, **documentation only** | None | None |
| State runtime is log under min-max, raw under share | Behaviour exists | O:316, O:320 | Documentation only | None | None |
| Describe tie behaviour; footnote Table 20 Low-memory N = 500 as an exact tie broken by runtime | Behaviour exists, not stated | O:206; sensitivity_detail.csv | **Required correction** (a table cell hides a tie) | Low | Table 20 footnote only; no numbers change |
| Describe share edge rules (negative shift, constant positive gives 1/n, zero sum gives 0) | Behaviour exists | O:163-176 | Documentation only (not triggered by the data) | None | None |
| Say the memory cap acts on absolute peak RSS while scoring uses growth | Behaviour exists | O:268, O:284-289 | Documentation only | None | None |
| State that a backend without a fitted k is excluded even at scalability weight 0 | Behaviour exists | O:271-278 | Documentation only | None | None |
| Say eligible set is 8 backends (9 minus Brian2 C++ standalone) | Behaviour exists | O:252-257 | Documentation only | None | None |
| Clarify Pareto set (cost criteria incl. growth and k) vs Figure 25 axes (runtime vs absolute memory) | Behaviour exists | O:331-336; V6 Fig 25 | Documentation only | None | None |
| Report R² = 0.45 as session-A value (session B: 0.97) | Data exist | sessions check; refit | Documentation only | None | None |
| Sensitivity evaluation (approach, normalisation, ablation, session) | **Done here** from existing data | `review/sensitivity_*.csv` | New evaluation (adds a table and a paragraph to §5.7 / limitations) | Low; some picks are fragile, which the text must say | New table only |
| Per-session recomputation for runtime, growth and k | Done here | sessions check | New evaluation; feasible | None | New table only |
| Per-session accuracy | Not possible | Accuracy has one run per condition | **Not feasible from existing data** | n/a | n/a |
| Selections beyond 100-10,000 | Not possible | Five measured sizes | **Not feasible** (and out of scope per brief) | n/a | n/a |
| Expose tied sets in `evaluate_four` / `evaluate_profiles` | No | O:449-454 flags only all-tied | **Optional dashboard improvement** | Low; touches Table 20 display logic | Figures 24-26 if the UI changes |
| Add the tests in section 6 | No | Gaps in 1.1 | Recommended (new tests) | None (test-only) | None |

## 6. Proposed new tests (not added)

Names are proposals; all use `series=` fixtures so they do not depend on the DB unless stated.

1. `test_minmax_runtime_uses_log` : two backends whose runtimes differ by 10× and 100× give a log-scaled midpoint cost of 0.5.
2. `test_share_runtime_uses_raw_seconds` : share cost equals t/Σt exactly (already similar; assert it is not the log form).
3. `test_accuracy_minmax_is_shortfall_from_best` : accuracies (97, 90, 80) give costs (0, 0.41, 1).
4. `test_accuracy_share_is_shortfall_from_100` : same fixture gives (3, 10, 20)/33.
5. `test_negative_memory_growth_minmax_linear`, `test_negative_values_share_shift_documented` : assert the current shift behaviour so a change is deliberate.
6. `test_share_constant_positive_criterion_gives_equal_costs` : cost 1/n each; ranking unchanged.
7. `test_share_zero_sum_gives_zero_cost`.
8. `test_r2_does_not_change_score` : same k, different R² gives identical scores.
9. `test_missing_fit_excluded_even_at_zero_scalability_weight`.
10. `test_evaluate_four_excludes_controls_and_compile_dominated` and the same assertion for rank sum, grid and profile output.
11. `test_memory_cap_applies_to_absolute_rss_before_normalisation` : partial cap changes the normalised costs of survivors.
12. `test_exact_tie_is_broken_by_runtime_and_reported` : two backends with equal score; asserts the documented rule (and, if implemented, a `tied_ids` field).
13. `test_profiles_no_eligible_candidates_returns_empty`.
14. `test_rank_sum_ties_average_rank_and_ignore_inactive_criteria`.
15. `test_published_table19_values` (DB): the five winners and scores to 3 d.p.; `test_published_table20_agreement_41_of_45` (DB).
16. `test_grid_includes_accuracy_only_when_reader_weight_positive`.

## 7. Exact thesis text that must change

| Where | Current wording | What the code does | Suggested nature of change |
|---|---|---|---|
| §3.11.2, accuracy criterion paragraph | "entered as a shortfall from the best value" | Min-max: from best observed. Share: from 100 %. | Make consistent: state both forms, or state one and amend the code later (not decided here). |
| §3.11.2, after Eq 17 | "Under both normalisations every criterion is a cost ... accuracy therefore enters as its shortfall from 100 per cent." | Only share uses 100 %. | Same as above. |
| §3.11.2, after Eq 16 | "runtime, which spans several orders of magnitude, enters as its logarithm" | True for min-max; share uses raw runtime. | Add "under min-max; share-of-total uses the raw value". |
| §3.11.2, after Eq 17 | "A criterion on which all eligible backends are equal carries no information and contributes nothing." | True for ranking in both; for share a constant positive criterion adds weight/n to every score. | Qualify ("does not change the ranking"). |
| §3.11.2, Eq 17 | Plain x / Σx | If any value is negative, values are first shifted by the minimum. | Add one sentence (not triggered by this data). |
| §3.11.2, Eq 15 text | "N_0 = 100 neurons is the smallest size measured" | Uses the smallest measured size with a non-zero reading (100 here). | Optional wording. |
| §3.11.2 / §5.7 | Eligibility ("excluded, not scored zero"; "optional peak-memory cap") | Cap is on absolute peak RSS; a missing fitted k excludes the backend even at weight 0; eligible set is 8. | Add these three facts. |
| §5.7, Table 20 (Low-memory, N = 500, "snnTorch") | Shown as a single choice | Exact tie with Brian2/Cython (both growth 0.0 MB), broken by shorter runtime. | Footnote the tie. |
| §5.7, text about Table 20 | "At 100 neurons the low-memory profile cannot choose at all" | Correct (all 8 tied). Same applies, partially, at N = 500. | Add the N = 500 case. |
| §5.7, Fig 25 caption / text | Trade-off plot "marking the recommendation and the Pareto-efficient alternatives" | Pareto set is computed on active cost criteria (growth, k included), not on the plotted runtime vs absolute memory. | Clarify. |
| §5.8.2 / evaluation table | "26 of 26 tests pass" | True, but 8 of the 26 exercise only the legacy two-criterion function; four-criterion gaps in 1.1. | Say how many cover the four-criterion method, or add tests. |
| §4.4 / §5.7 | "R² = 0.45" for Brian2/Cython | Session A value; session B refits to 0.97. | Say "in the reported session". |

## 8. Smallest implementation package

No code correction is required for the V6 numbers: every published table value reproduces and the independent calculation agrees to 1e-17.

1. **Text-only (required):** the accuracy wording, the Table 20 N = 500 tie footnote, and the eligibility/cap/share/log clarifications in section 7.
2. **One new table (new evaluation):** the sensitivity summary (section 4) as a compact table in §5.7 or the limitations section, with a two-sentence neutral reading and the session-B caveat.
3. **Optional, if time allows:** tests 1-4, 10, 12 and 15 from section 6 (test-only; no behaviour change), and, only on approval, exposing `tied_ids`.

Not decided here: which accuracy convention (best observed or 100 %) is intended; that is a thesis decision.
