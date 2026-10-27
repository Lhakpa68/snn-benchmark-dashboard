> **SUPERSEDED by `FOUR_CRITERION_OPTIMISATION_METHOD.md`.** This document describes the archived two-criterion runtime–memory design. It is retained only to document the project history; the current Flask and Streamlit tabs use inference, memory, scalability and optional exploratory accuracy.

# Implemented method-selection module: method, reproducibility and limits

**Thesis title:** Building a Benchmarking Dashboard for SNN Methods.

## Scientific question and boundary

For a selected *measured* feedforward LIF network size on the existing single CPU platform, which eligible measured SNN simulator backend matches the declared balance between low simulation runtime and low peak process memory? This is **optimisation of the choice**, not optimisation of the simulator source or neuron algorithms.

The five actual simulator families are Brian2, NEST, Nengo, snnTorch and SpikingJelly. Brian2/NumPy is an eligible Brian2 backend. The separate plain-NumPy control is excluded from this decision. Compilation-dominated backends are not treated as comparable execution-cost choices. Training accuracy is not included, because the native learning paradigms have incompatible optimisation objectives; no runtime-derived energy proxy is counted as a separate energy measurement.

## Algorithm implemented in `dashboard/optimization.py`

1. Choose network size N from 100, 500, 1,000, 5,000, 10,000 neurons. Retrieve median simulation runtime t_i > 0 and peak RSS m_i > 0 from canonical `dashboard_data.get_scalability_series()`; drop missing/invalid controls, compilation-dominated configurations and rows above the optional memory cap.
2. For each cost x_ij in {t_i,m_i}, define c_ij = [ln(x_ij)-min_k ln(x_kj)]/[max_k ln(x_kj)-min_k ln(x_kj)], with c_ij=0 if all eligible values are equal. All costs are dimensionless between 0 and 1.
3. For a declared runtime priority w ∈ [0,1], minimise S_i(w) = w c_i,runtime + (1-w) c_i,memory. Report raw costs and this score together, not just a winner.
4. Mark backend i as Pareto-efficient when no competing eligible backend has <= runtime AND <= peak memory with at least one strict improvement.
5. Re-evaluate the winner for the 21 weights w = 0, 0.05, ..., 1.00. Report the count of weights that select each backend. These counts describe *preference sensitivity*, not probability/confidence.

## Observed, reproducible examples (50% runtime / 50% memory)

| Measured network size | Recommended backend | Median runtime | Peak RSS | Weight-grid winner count |
|---|---|---:|---:|---:|
| 100 neurons | NEST / 4 threads | 0.001822 s | 93.57 MB | 16/21 |
| 500 neurons | NEST / 4 threads | 0.007775 s | 127.09 MB | 13/21 |
| 1,000 neurons | NEST / 4 threads | 0.014216 s | 169.49 MB | 17/21 |
| 5,000 neurons | NEST / 4 threads | 0.106087 s | 506.69 MB | 12/21 |
| 10,000 neurons | Brian2 / NumPy | 0.148678 s | 644.7 MB | 19/21 |

These are derived analyses of the original benchmark campaign, not new experimental measurements, speed-ups, independent external benchmarks or generally optimal simulator recommendations. NEST/1, NEST/2, NEST/4 are the two-criterion Pareto options at 100 neurons; Brian2/NumPy and Brian2/Cython are the Pareto options at 10,000 neurons.

## Verification carried out

`python -m unittest discover -s tests -v` passed eight independent mathematical and data-path checks: exclusions, extreme weights, Pareto dominance, memory constraints, unchanged input records, complete 21-weight tally, invalid user inputs and exact canonical-database outcomes. Flask test-client GET requests to `/`, `/all-simulators`, `/optimization`, and the optimisation CSV endpoint returned HTTP 200 with non-empty content. The new screenshot was rendered from actual Flask template output with CSS applied; it is not a speculative mock-up. Python syntax compilation passed for the Streamlit source, but interactive Streamlit runtime testing was not possible in the current environment.

## Remaining research work (not claimed as completed)

- Add per-condition equivalence gating and propagate errors/measurement uncertainty to selection rather than treating medians as perfect values.
- Test alternative metric normalisations, correlated feature exclusion, training-specific comparable subsets, scenario boundaries and different CPU/GPU platforms.
- Evaluate recommendation stability under bootstrap/per-run resampling and potential near ties.
- Conduct heuristic evaluation, participant usability and decision-quality comparisons under appropriate approvals.
- Do not claim new neural optimisation or energy savings without changing simulator implementations and rerunning controlled experiments.
