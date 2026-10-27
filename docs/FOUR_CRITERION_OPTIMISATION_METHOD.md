# Four-criterion preference analysis: method, evidence, numerical examples

**Approved thesis title:** *Building a Benchmarking Dashboard for SNN Methods*.

## Correct interpretation of supervisor's four weights

A measured network size N is the **scenario**, not the weight. Each SNN execution backend is a candidate alternative. The importance sliders express four preference criteria: inference runtime I (seconds, minimise), peak resident memory M (MB, minimise), fitted scalability exponent K (minimise with fit-quality caveat), and optional MNIST accuracy A (percent, maximise). N selects a recorded workload size for I and M; K is fitted across the measured size sweep; A comes from a different training experiment.

The user enters q_I, q_M, q_K, q_A from 0 to 100. For q_sum > 0, relative weights are w_j = q_j/q_sum. The four importance controls do **not** need to be manually adjusted to sum to 100; the dashboard does that automatically.

## Reproducible calculation from the existing results

The selected backend must have valid, positive inference and memory measurements. The reference controls, compilation-dominated runs and missing readings are excluded. Under a positive accuracy priority, a missing training accuracy reading also excludes the candidate; missing numbers are never replaced by 0.

For each eligible backend i and metric j:

- Inference and memory cost: C_ij = [ln(x_ij)-min_h ln(x_hj)]/[max_h ln(x_hj)-min_h ln(x_hj)].
- Scalability cost: C_iK = [k_i-min_h(k_h)]/[max_h(k_h)-min_h(k_h)]. Smaller exponents are treated as preferable, **but weak R² or large fixed overhead can make k misleading**; both k and R² are shown.
- Exploratory accuracy cost: C_iA = [max_h(A_h)-A_i]/[max_h(A_h)-min_h(A_h)]. High recorded native accuracy is preferred under the declared but non-equivalent training protocols.
- If all eligible values are equal, the corresponding normalised cost is zero.
- Composite preference cost: S_i = w_I C_iI + w_M C_iM + w_K C_iK + w_A C_iA. Smaller S_i ranks earlier.

Pareto-efficient alternatives are calculated over the **currently positively weighted** criteria: no eligible candidate has cost no greater in every active criterion and strictly smaller in at least one. Sensitivity enumerates all weight vectors with 25-percentage-point increments that sum to 100: 15 vectors in the primary I/M/K model, 35 if accuracy is included. These grid counts are **not confidence, probabilities, or estimates of physical energy**.

## Observed examples, not new experiments

Measured size 100, illustrative equal-priority weights 33.3% inference / 33.3% memory / 33.3% scalability / 0% accuracy → **NEST/threads4**; median runtime 0.001822 s, peak RSS 93.57 MB.

Measured size 10,000, same weights → **Brian2/numpy**; runtime 0.148678 s, peak RSS approximately 644.7 MB.

For N=100, setting only one criterion to 100% produces the following **observed single-metric best in the eligible set**:

| Criterion weighted 100% | Lowest cost / highest recorded value | Important caveat |
|---|---|---|
| Inference | NEST/threads4 | Measured CPU runtime at N=100 |
| Memory | NEST/threads1 | Whole-process peak RSS, not just neural state |
| Scalability | Brian2/cython | k≈0.014, **poor R²≈0.454**, not a reliable claim of general scaling superiority |
| Accuracy | SpikingJelly/cpu | 97.46% native MNIST accuracy; other simulators used different learning paradigms and this is **not a fair like-for-like accuracy comparison** |

The “best” is conditional on the chosen output measure, eligible set, hardware and experimental workload. It is not proof of simulator code acceleration. Accuracy is **exploratory** and should not be treated as established cross-paradigm method quality.

## Interface changes

- Four sliders with automatically normalised effective priorities.
- Network-size filter and optional hard peak-memory limit.
- No Recalculate button; JavaScript requests the updated Flask fragment automatically. Streamlit also recalculates when a slider moves.
- Stacked horizontal bars show each criterion's contribution to the total weighted cost, with smaller costs ranking first.
- Inference–memory scatter graph shows measured alternatives, highlighting the currently recommended backend and Pareto points.
- Table contains inference, memory, scaling exponent, fit R², accuracy, weighted score, Pareto status, and grid sensitivity. A CSV export preserves the evidence.
- Plain NumPy control excluded, Brian2/NumPy retained.

## Verification completed and limitations

**Completed:** sixteen automated Python mathematical/database tests (eight prior two-cost compatibility tests and eight new four-criterion tests). Real-data template render succeeded with Jinja; new JavaScript passed syntactic checking with Node. The Word figure is an independently generated, data-derived analytical graphic and should **not** be called a tested browser screenshot.

**Not completed in authoring environment:** Flask runtime/route tests and interactive Streamlit/browser evaluation, because the necessary app dependencies could not be installed and local browser access was blocked. Independent usability evaluation, uncertainty-aware selection, experimental hyperparameter tuning, cross-hardware portability testing, and fair cross-method accuracy evaluation require further work. No new physical benchmark runs have been claimed.


## Why not 40:30:30?
The previously displayed allocation of 40/30/30/0 was an arbitrary UI example, not established in SNN studies or collected from researchers. It is removed. Equal relative importance among the three measurable cost dimensions is merely a reproducible, explicitly illustrative starting point; it has no claim to optimality or population preference. Multi-criteria decision analysis does not determine preference weights automatically. Researchers must choose weights aligned with their decisions or elicit them empirically, and report how rankings change when those weights change. Relevant open-access empirical precedents include Novoa-Hernández et al. (2025), doi: 10.1111/exsy.70031 (ranking sensitivity) and Khanal et al. (2023), doi: 10.3389/frhs.2023.1155523 (elicited stakeholder weights).
