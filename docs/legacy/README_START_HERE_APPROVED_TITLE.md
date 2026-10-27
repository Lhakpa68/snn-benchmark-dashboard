# Building a Benchmarking Dashboard for SNN Methods

**Supervisor-approved thesis title (October 2026). This is the four-criterion optimisation update.**

## Open the latest deliverables

- **Updated thesis:** `thesis/Thesis_SNN_Methods_Four_Criteria_Optimisation_2026.docx`.
- **Flask dashboard:** `dashboard/app.py` → visit `/optimization`.
- **Streamlit dashboard:** `dashboard/streamlit_app.py` → select **Optimisation**.
- **Shared four-criterion calculation:** `dashboard/optimization.py`, function `evaluate_four()`.
- **Automated unit and data checks:** `python -m unittest discover -s tests -v` (16 checks passed in authoring environment).
- **Detailed methodology, numerical demonstrations and evidence boundaries:** `docs/FOUR_CRITERION_OPTIMISATION_METHOD.md`.
- **Data-derived research figure, not a browser screenshot:** `docs/dashboard_screenshots/optimisation_four_criteria_thesis_figure.png`.

## Run locally

From project root, install app requirements if not already installed:

```sh
python -m pip install -r dashboard/requirements.txt
python dashboard/app.py
```

Open `http://127.0.0.1:5000/optimization`.

Alternatively install `dashboard/requirements-streamlit.txt` and run
`streamlit run dashboard/streamlit_app.py`.

## What the four controls really mean

Network size selects the **measured inference workload**; it is **not** an optimisation weight. The four priorities are:

1. **Inference:** lower runtime at the selected network size.
2. **Memory:** lower peak process RSS at that size.
3. **Scalability:** lower fitted log–log runtime growth exponent across five sizes; consult fit R².
4. **Accuracy (exploratory):** higher MNIST accuracy at 60,000 training images, 10 epochs, hidden width 256.

Each priority can be entered as 0–100 importance. The app normalises them so their relative weights sum to 100%. **The charts and ranking update automatically as the weights or measured network size change: no Recalculate button.** The starting sliders use 50 / 50 / 50 / 0 raw importance points (33.3% each for the first three after normalisation). These are an illustrative equal-priority example, not scientific weights. The separate plain-NumPy reference cannot be recommended; Brian2/NumPy is a valid Brian2 backend and remains included.

**Research warning:** Accuracy is obtained using different native training mechanisms and is not a like-for-like comparison of algorithms. Adding accuracy weight is displayed as an *exploratory cross-paradigm preference scenario*, not the principal controlled inference recommendation. The selection routine does not speed up the simulation libraries or rerun physical experiments.

## Verification and limitations

In this build, the four-criterion Python method passed 16 unit/database tests (including the 8 original two-cost legacy checks), and Flask HTML templates were rendered with real stored measurement data using Jinja independently of Flask. The live-update JavaScript passed `node --check`. The authoring environment did not permit installing Flask/Streamlit or opening local browser pages; therefore an end-to-end running web-session/participant evaluation remains **unverified** here. Run the local app and test the sliders before using dashboard screenshots in the submitted thesis.

Existing experiment measurements were not edited. The old two-criterion `evaluate()` remains only for backwards compatibility and its original tests; the real Flask and Streamlit Optimisation pages now use `evaluate_four()`.
