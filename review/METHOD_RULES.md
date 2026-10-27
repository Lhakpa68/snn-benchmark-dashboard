# Method rules: what `evaluate_four` / `evaluate_profiles` do today

Each rule describes the code as it is (no behaviour was changed in this review). `O` = `dashboard/optimization.py`, `D` = `dashboard/dashboard_data.py`. Line numbers are for the files as reviewed.

## Eligibility and data handling

1. **Eligible set (8 backends).** Of the nine SNN backends (Brian2 NumPy, Cython and C++ standalone; NEST with 1, 2 and 4 threads; Nengo; snnTorch; SpikingJelly), the Brian2 C++ standalone target is dropped because its runtime is compile-dominated, leaving eight; the two plain-NumPy controls (`reference` framework) are never candidates. (O:17, O:252-257)
2. **Missing or non-finite values.** A backend whose runtime or peak memory at the chosen size is missing, NaN, infinite or not greater than zero is excluded; it is never scored as zero and nothing is imputed. A non-finite memory growth is excluded the same way. (O:263-267, O:287-289)
3. **Missing exponent.** A backend with no fitted scaling exponent k (fewer than three sizes) is excluded **even when the scalability weight is zero**, because the sensitivity grid always varies that weight. (O:271-278; D:184-188)
4. **Missing accuracy.** A backend with no accuracy value is excluded only when the accuracy weight is above zero; accuracy rows must match the preset (60,000 images, 10 epochs, hidden 256) and lie in 0-100. (O:242-246, O:291-293)

## Criteria

5. **Memory growth.** Growth is the backend's peak resident memory at size N minus its own peak resident memory at the smallest measured size with a reading (100 neurons in this data), with no clamping; it is zero for every backend at N = 100. (O:284-289)
6. **Exponent k.** k is the least-squares slope of log10 median runtime on log10 N over the five sizes of the **session A** scalability run group (`3dd09b61bd76-fb679a`); session B is a labelled replication and is not used. (D:118-120, D:184-208, D:396-433)
7. **R² is display-only.** R² never enters a score; it only sets a caution flag when it is below 0.80. (O:304)
8. **Memory cap.** The optional cap compares **absolute** peak resident memory at size N with the cap, removes backends above it **before** any normalisation, and everything downstream (costs, rank sum, Pareto, grid, profiles) is then computed on the survivors. (O:268-270)

## Normalisation

9. **Min-max, runtime.** Runtime enters as its natural logarithm and is rescaled so the best eligible value is 0 and the worst is 1. (O:152-157, O:320)
10. **Min-max, other criteria.** Memory growth and k are rescaled linearly; a criterion on which every eligible backend is equal gets cost 0 for all. (O:152-157, O:321-322)
11. **Share-of-total, runtime.** Runtime enters as raw seconds divided by the sum over the eligible backends (no logarithm); memory growth and k are treated the same way. (O:163-176, O:316-318)
12. **Accuracy, min-max.** Accuracy cost is the shortfall from the best observed accuracy, rescaled to 0-1; this equals min-max of (100 − accuracy), because subtracting from a different constant does not change a min-max rescaling. (O:156 with `benefit=True`, O:324)
13. **Accuracy, share-of-total.** Accuracy cost is the shortfall from 100 per cent divided by the sum of the shortfalls. (O:170, O:324)
14. **Share-of-total edge cases.** If a criterion's sum is zero its cost is 0 for all; if any value is negative, all values are first shifted by the minimum so the smallest becomes zero (the form is then no longer a plain x/Σx); a constant positive criterion gives every backend the cost 1/n. (O:170-176)
15. **Constant criteria do not change the ranking.** Under min-max a constant criterion contributes exactly zero; under share-of-total it adds the same amount (weight/n) to every backend, so the order is unchanged but the score values shift. (O:156, O:176)

## Weights and scoring

16. **Importance to weight.** Each importance must be a finite number from 0 to 100, and each weight is that importance divided by the sum of the four importances (Eq 18). (O:138-149)
17. **All-zero priorities.** Four zero importances are rejected with an error; the Flask page shows a message and the default scenario. (O:147-148; `app.py:187-190`)
18. **Score.** A backend's score is the sum over criteria of weight × normalised cost, with no bias and no activation (Eq 19); the lowest score is recommended. Accuracy cost is set to 0 when its weight is 0. (O:201-207, O:323-329)
19. **Tie-break order.** Candidates are ordered by score rounded to 12 decimals, then by median runtime, then by absolute peak memory, then by backend id. A tie is not reported by `evaluate_four`; `evaluate_profiles` reports a tie (no winner) only when **all** eligible backends have the same score. (O:206, O:449-454)
20. **No eligible backend.** The result has `ok = False`, no rows and no winner; in `evaluate_profiles` that profile is left out. (O:311-313, O:447-448)

## Reported alongside the score

21. **Rank sum.** For each active criterion (weight above zero) backends are ranked 1 = best on the **raw** value (higher is better for accuracy), tied backends share the average rank (relative tolerance 1e-12), and the ranks are added without weights; remaining ties are ordered by id. (O:179-198)
22. **Priority grid.** The ranking is recomputed for every combination of weights in steps of 25 per cent: 15 combinations over inference, memory and scalability, and 35 when the reader's accuracy weight is above zero; the grid does not use the reader's own weights otherwise. (O:210-219, O:340-342)
23. **Pareto set.** A backend is Pareto-efficient if no other backend is at least as good on every **active normalised cost** and strictly better on one, with a 1e-12 tolerance; this uses memory growth and k, not the two axes (runtime and absolute memory) of Figure 25. (O:331-336)
24. **Profiles.** The nine fixed profiles are scored by calling `evaluate_four` once per profile, so each profile can have its own eligible set (accuracy-weighted profiles need accuracy values). (O:419-430, O:432-475)

## Pseudocode of `evaluate_four` (O:222-410)

```
evaluate_four(N, importances, cap, normalisation, series, training_rows):
    W = importances / sum(importances)          # each 0..100, finite, sum > 0, else error
    acc = {backend: accuracy} for rows matching preset (60000, 10, 256) with 0..100
    for each series s:
        skip if s is a control or compile-dominated                      # rules 1
        skip if no point at N, or runtime/memory not finite and > 0      # rule 2
        skip if cap and memory(N) > cap                                  # rule 8
        skip if s has no fitted k                                        # rule 3
        growth = memory(N) - memory(first point with a reading)         # rule 5
        skip if growth not finite; skip if W[acc] > 0 and no accuracy[s] # rule 4
        keep candidate {runtime, growth, k, accuracy}
    if none kept: return ok=False
    cost[c][i] = share(...)  or  minmax(...) per normalisation           # rules 9-15
        (minmax: runtime on log scale; accuracy cost = shortfall; share: shortfall from 100)
    accuracy cost = 0 when W[acc] == 0
    rank_sum over criteria with W > 0; pareto over their costs           # rules 21, 23
    score[i] = sum_c W[c] * cost[c][i]                                   # rule 18
    order by (round(score, 12), runtime, memory, id)                     # rule 19
    grid wins: repeat scoring for 15 (or 35) weight combinations         # rule 22
    return rows, winner = first row, pareto set, grid wins
```
