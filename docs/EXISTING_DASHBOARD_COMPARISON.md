# Existing dashboard comparison for thesis Chapter 5

The approved title is **Building a Benchmarking Dashboard for SNN Methods**.

Chapter 5, Section 5.10 now includes an original comparison diagram (Figure 28), an evidence-based feature matrix (Table 21), literature/official-source discussion and a bounded design argument. This comparison was previously buried in Appendix H; its key evidence is now in the main chapter.

Official public interfaces reviewed in October 2026:
- [beNNch](https://inm-6.github.io/beNNch/) — standardized plots, flip-book, benchmark metadata.
- [NeuroBench](https://neurobench.ai/) and [leaderboard documentation](https://github.com/NeuroBench/neurobench/blob/main/leaderboard.rst) — algorithm/system track and task-specific metrics.
- [MLPerf Inference Datacenter](https://mlcommons.org/benchmarks/inference-datacenter/) and [visualization dashboard](https://mlcommons.org/visualizer) — filtering, interactive result visualization, scenarios, transparency.
- [HELM](https://crfm.stanford.edu/helm/) — many scenarios and metrics with inspectable benchmark records.

The figure is a **conceptual wireframe**, not screenshots, copied artwork, published model performance figures, or proof of superiority. Example scores in miniature panels are illustrative only.

**Research conclusion**: the SNN dashboard combines run-level traceability, simulator-specific comparison, rank sensitivity and priority-conditioned recommendations for a narrower SNN software-selection task; it has not been proven globally better than these established systems. A controlled user task study would be needed for measured superiority.

The ZIP's **START_DASHBOARD_WINDOWS.bat** is a native-Windows launcher; **OPEN_DASHBOARD_OFFLINE.html** is a no-install reading fallback. This comparative thesis change does not change benchmark results or re-run simulations.
