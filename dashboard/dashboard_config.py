"""Single configuration file for the SNN benchmark dashboard.

Every setting the dashboard needs is declared here, and nowhere else. Point
it at a different results file, change the port, or relabel the page, and
`app.py` itself never has to change — only this file does.

Edit a value below, save, and restart `python app.py` (or the
START_DASHBOARD script) for it to take effect.
"""
import os
import pathlib

# Directory this file lives in (dashboard/), so paths below are portable
# regardless of where the project folder is checked out.
HERE = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

# The results database written by the benchmark suite (run.py bench).
# SNN_RESULTS_DIR overrides the default sibling "results/" directory, so a
# copy of this dashboard checked out somewhere else (e.g. alongside a thesis
# edition) can still point at the one project's live results without editing
# this file — the same override snnbench/config.py already honours.
_RESULTS_DIR = pathlib.Path(os.environ["SNN_RESULTS_DIR"]) if os.environ.get(
    "SNN_RESULTS_DIR") else HERE.parent / "results"
DB_PATH = _RESULTS_DIR / "benchmarks.db"

# The equivalence-validation log written by run.py validate. Optional: if the
# file is missing, the dashboard's validation panel says so and the rest of
# the page still renders normally.
VALIDATE_PATH = _RESULTS_DIR / "validate.txt"

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

HOST = "127.0.0.1"   # 127.0.0.1 keeps the server reachable only from this
                      # machine. Set to "0.0.0.0" to allow other devices on
                      # the same network to reach it, e.g. http://<your-lan-ip>:5000
PORT = 5000

DEBUG = False         # Flask's auto-reloader. Leave off outside development;
                       # it restarts the process on every file save.

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

TITLE = "Building a Benchmarking Dashboard for SNN Methods"

# The subtitle states the study design positively. Benchmarking on one
# hardware platform is the controlled-experiment choice this research makes,
# not a reduced version of something larger: holding the machine fixed is
# what allows a difference in runtime to be attributed to a difference in the
# simulator rather than to the hardware it happened to run on.
SUBTITLE = ("Benchmark results, methodological evidence and transparent "
            "preference-based selection across five SNN simulators "
            "on a controlled CPU workload.")

# Shown under the title so a reader knows whose work this is without
# hunting for it.
AUTHOR = "Lhakpa Tshering"
INSTITUTION = ("School of Information Technology and Engineering, "
               "Melbourne Institute of Technology")
