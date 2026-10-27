# Start the SNN benchmarking dashboard (Windows, Mac or Linux)

**What changed in this edition (V6, 9 October 2026):** the launcher no longer assumes port 5000. On many Windows computers port 5000 is reserved by Hyper-V/WSL and Python reports `WinError 10013`, so the dashboard silently failed to start. `RUN_DASHBOARD.py` now tries 5000, then 8050, 8765, 5050, 8000 and 8080, then any free port, prints the address it uses and opens the browser itself. If anything still goes wrong, the error is written to `DASHBOARD_START_LOG.txt` and the window stays open so you can read it.

**Three ways to start it**

1. **Windows, double-click:** extract the folder to a short path (for example `C:\SNN_Dashboard`) and double-click `START_DASHBOARD_WINDOWS.bat`. The first start creates `.dashboard_venv` and installs Flask (internet needed once).
2. **PyCharm or VS Code:** open this folder as a project, select any Python 3.10–3.12 interpreter, run `pip install flask` once in the terminal, then right-click `RUN_DASHBOARD.py` → *Run*. The address appears in the run window (usually http://127.0.0.1:5000, or the fallback port).
3. **Command line:** `python RUN_DASHBOARD.py` from this folder.

Only Flask is needed to view the dashboard; NEST, Brian2 and the other simulators are not required because the dashboard reads the stored results in `results/benchmarks.db`.

---

**Windows (recommended):** Extract the ZIP completely to a short normal folder, for example `C:\SNN_Dashboard`. Open that folder and double-click **`START_DASHBOARD_WINDOWS.bat`** at the top level. The launcher uses native Windows Python, builds `.dashboard_venv`, installs Flask if necessary, checks the included results database and opens <http://127.0.0.1:5000>. It does **not** require WSL, NEST, Brian2 or any SNN framework to display the existing benchmark measurements.

**Mac/Linux:** Open Terminal in the extracted top-level folder and run `bash START_DASHBOARD_MAC_LINUX.sh`. The URL is <http://127.0.0.1:5000>.

**No installation or unable to download Flask?** Double-click **`OPEN_DASHBOARD_OFFLINE.html`** for a self-contained visual exploration of the five SNN simulators and the selection calculations, including interactive priorities and charts. This offline edition is a reading/selection fallback, *not* the whole Flask application and does not execute new benchmarks.

**If startup still fails:** Do not run `RUN_ME.py` or `run.py bench` to fix the dashboard; those launch new simulations. Open `DASHBOARD_START_LOG.txt` from the extracted folder and report its last lines. If the dashboard is already running from an earlier start, close that window first (the new start will otherwise pick another port). Verify `results/benchmarks.db` is present. Install Python from python.org and select **Add Python to PATH**. On managed computers you may need a proxy or administrative assistance for the first Flask download.

**Important scientific distinction:** All ranking candidates are Brian2, NEST, Nengo, snnTorch and SpikingJelly execution methods. Brian2/NumPy is a legitimate Brian2 backend. The separate internal implementation control is not a simulator candidate.

**What the weight sliders mean:** The initial raw importance values `50 / 50 / 50 / 0` yield 33.3% relative importance each for inference, memory and scalability, and 0% for non-comparable native training accuracy. They are only an equal-importance demonstrative scenario, not experimentally elicited or theory-derived optimal weights. All recommendations are conditional on the priorities the reader selects.
