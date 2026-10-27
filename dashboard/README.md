# Building a Benchmarking Dashboard for SNN Methods

Interactive dashboard for the MR604 thesis of the same name.

**Lhakpa Tshering** · School of Information Technology and Engineering,
Melbourne Institute of Technology

Five spiking neural network simulators — **Brian2**, **NEST**, **snnTorch**,
**SpikingJelly** and **Nengo** — are benchmarked against each other on a
controlled CPU workload. The dashboard reads the measured results and lets a reader filter
them by simulator, see the individual runs behind every median, and export the
exact rows any figure was drawn from.

---

## Scope

**A single hardware platform, by design.** This is a controlled comparison:
the machine is held fixed so that a difference in runtime can be attributed to
a difference in the simulator rather than to the hardware it happened to run
on. That is why there is no hardware selector — every row was measured under
identical conditions, and that is the property which makes the comparison
valid. The consequence is that the absolute timings belong to this platform;
the rankings and the scaling behaviour are the transferable results. Running
the same harness on GPU hardware is set out as future work in the thesis.

---

## Quick start

Two front ends read the same data. Pick either.

```bash
pip install -r requirements.txt        # Flask version — one dependency
python app.py                          # http://127.0.0.1:5000
```

```bash
pip install -r requirements-streamlit.txt   # pure-Python version
streamlit run streamlit_app.py              # http://127.0.0.1:8501
```

`run_streamlit.py` starts the second one from an IDE's Run button, without
needing a terminal command typed.

Neither front end requires the six benchmark packages to be installed. They
read the results database; they do not run the simulators.

---

## What it shows

| View | Question it answers |
|---|---|
| **All Simulators** | Peer-level comparison of the five actual simulators |
| **Optimisation** | Conditional inference/memory/scalability selection with exploratory native-accuracy option, score chart, trade-off plot and weight-grid sensitivity |
| **Inference** | What does one forward pass cost — runtime, memory, energy proxy, processor utilisation |
| **Scalability** | How does cost grow from 100 to 10 000 neurons, and what is the fitted exponent |
| **Memory** | How much memory is the network, and how much is the Python interpreter |
| **Training** | What does learning cost, and did the learning rule converge at all |
| **Sensitivity** | Does the ranking survive a change of network size or metric (Experiment 4) |
| **Equivalence & provenance** | Are the simulators computing the same thing, and on what machine |
| **What the baselines are** | What every entry in the study is, with the published source for each |

Selecting a simulator filters the original benchmark-analysis views. The
Optimisation page intentionally considers all eligible measured backends,
subject to the chosen workload, metric weights and optional memory cap.

---

## Architecture

```
dashboard_config.py    every setting: database path, host, port, title
dashboard_theme.py     palette, simulator metadata, backend descriptions
dashboard_data.py      ALL data access and statistics — no web framework
app.py                 Flask front end  ─┐
templates/, static/                       ├─ both read dashboard_data.py
streamlit_app.py       Streamlit front end ┘
```

`dashboard_data.py` performs every query, computes the scaling regression and
the rank statistics, and derives every ranking. It imports neither Flask nor
Streamlit, so its functions can be exercised from a plain interpreter:

```python
import dashboard_data as d
d.get_kpis()          # the four headline figures
d.get_sensitivity()   # Experiment 4
```

Because both front ends call the same functions, a figure quoted in the
thesis, a figure shown in either interface and a row in an exported CSV all
originate from one implementation of one query. They cannot disagree.

---

## Two rules the interface follows

1. **Nothing is displayed without a value.** A panel that renders a dash, a
   zero or an empty cell for a quantity that was never measured is
   indistinguishable from one reporting a genuine zero. Every absence is
   labelled in words with its reason.

2. **Nothing that mutates stored results is exposed.** An earlier version had
   a control that cleared the measured rows before re-running, and it
   destroyed a full result set once. The **Run benchmark** control starts the
   command-line harness as a separate process; the harness appends, and the
   dashboard reads the newest row per condition.

---

## Two measurement-integrity safeguards

Both were found while building the interface, and both would have affected the
figures rather than the measurements.

**Duplicate condition records.** The database is append-only by design, so
re-running one simulator leaves the earlier rows in place — which is what
makes a partial re-run safe. The cost is that a condition measured three times
appears three times, drawing as three overlapping series and weighting that
backend three times in any aggregate. Every query resolves to the newest row
per `(framework, backend, task, network_size, phase)`, by insertion order
rather than timestamp. Superseded rows stay in the database for audit.

**Compile-dominated backends.** Brian2's standalone target regenerates and
recompiles the model on each invocation, so its measured time is a C++
toolchain's rather than a simulator's. It posts the slowest runtime, a
*negative* scaling exponent and one of the smallest footprints — three
misleading figures from one cause. Compile-dominated rows and the NumPy
control are excluded from every headline ranking, while staying visible and
labelled in every chart and table.

---

## Exporting

- **Export CSV** (top right) — every result set in one self-describing file,
  with a `dataset` column naming the experiment each row came from.
- Per-table exports sit beneath each table.
- `GET /api/export/<kind>.csv` for `inference`, `scalability`, `memory`,
  `training`, `validation`, `runs`, `all`.

---

## API

Every view is backed by a JSON route, so the data is reusable without the
interface:

```
/api/meta         /api/frameworks    /api/backends
/api/inference    /api/scalability   /api/memory
/api/training     /api/validation    /api/sensitivity
/api/spread       /api/runs          /api/kpis
```

---

## Requirements

`requirements.txt` — Flask only.
`requirements-streamlit.txt` — Streamlit, Plotly, pandas.

Python 3.9 or newer. The simulator packages themselves are listed in
`../requirements-frameworks.txt` and are needed only to *produce* results, not
to read them.

---

## Reproducing the measurements

```bash
cd ..                       # the benchmark project root
python run.py check         # what is installed and what will run
python run.py validate      # equivalence check against the NumPy control
python run.py bench --quick # short confirmation sweep
python run.py bench         # the full protocol
```

The dashboard's **Run benchmark** button invokes the same entry point.

---

## Citing the statistics

The sensitivity analysis uses Kendall's τ-b for ordering stability and
Spearman's ρ for the energy-proxy comparison, both implemented in
`dashboard_data.py` without a SciPy dependency. Method follows Dey and
Dimitrov (2023) for sensitivity analysis of point-neuron simulations, and
Demšar (2006), *Statistical Comparisons of Classifiers over Multiple Data
Sets*, JMLR 7, 1–30, for rank-based comparison across conditions. The EFLOP
metric is Narduzzi et al. (2025). Energy-reporting practice follows Henderson
et al. (2020), *Towards the Systematic Reporting of the Energy and Carbon
Footprints of Machine Learning*, JMLR 21, 1–43.

---

## Licence

Academic work submitted for MR604. Please cite the thesis if you use the
benchmark suite or the dashboard.


## New preference-aware selection module (October 2026)

The approved project title is **Building a Benchmarking Dashboard for SNN Methods**.
The read-only `/optimization` page and the corresponding Streamlit **Optimisation**
tab use the shared `optimization.py` module. At each measured network size,
the module excludes the plain-NumPy control, compile-dominated backends and
invalid/incomplete conditions; log-normalises runtime and peak RSS within the
eligible alternatives; computes a weighted cost; identifies the Pareto frontier;
and checks 21 equally spaced runtime preference weights. `/api/optimization.csv`
exports the selected scenario. The output is **method selection**, not a claimed
acceleration of simulator internals or a new benchmark measurement.

The original training accuracy is not combined with the inference score
because learning objectives are different. The runtime-derived energy proxy
is not treated as independent measured energy. Independent usability/decision-
quality evaluation, uncertainty resampling and a per-record equivalence gate
remain future tasks.

Unit verification: `python -m unittest discover -s tests -v` from the project root.
That command does not install or execute any SNN simulator.
