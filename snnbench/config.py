"""Single source of truth for every benchmark parameter.

Every adapter imports these values. Nothing is duplicated in an adapter, so no
adapter can silently diverge from another -- that is the whole point of the file.
"""
from __future__ import annotations
import os
from pathlib import Path

# --- paths -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = Path(os.environ.get("SNN_RESULTS_DIR", BASE_DIR / "results"))
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = RESULTS_DIR / "benchmarks.db"

# --- the benchmark network (Experiment 1 and 3) ----------------------------
# N Poisson sources -> N leaky integrate-and-fire neurons, fixed in-degree.
FANIN         = 10      # synapses per target neuron
TAU_MS        = 10.0    # membrane time constant
V_THRESH      = 1.0     # firing threshold, normalised units
V_RESET       = 0.0     # reset potential
DT_MS         = 0.1     # integration timestep
SIM_MS        = float(os.environ.get("SNN_SIM_MS", 10.0))  # simulated duration -> 100 update steps by default;
                          # SNN_SIM_MS=1000 is the longer-duration check added for the journal revision
INPUT_RATE_HZ = 100.0   # Poisson rate per input source
SYN_WEIGHT    = 0.2     # normalised; scaled per simulator to match its units
SEED          = 1234

# --- protocol --------------------------------------------------------------
WARMUP_RUNS   = 5       # discarded
MEASURED_RUNS = 5       # kept, every individual value stored
SAMPLE_S      = 0.005   # resource sampler period

SIZES = [100, 500, 1000, 5000, 10000]

# --- Experiment 2: supervised MNIST ---------------------------------------
TRAIN_SIM_MS  = 25.0
TRAIN_DT_MS   = 1.0
MNIST_INPUTS  = 784
MNIST_CLASSES = 10
TRAIN_PRESETS = {
    "smoke":    dict(hidden=100, train_n=300,  test_n=100,  epochs=2),
    "paper":    dict(hidden=256, train_n=6000, test_n=1000, epochs=3),
    "extended": dict(hidden=500, train_n=20000, test_n=5000, epochs=5),
    "full":     dict(hidden=500, train_n=60000, test_n=10000, epochs=10),  # literal CCR/Chapter 3 spec
}
# This copy of the project is dedicated to the literal, uncompromised
# Chapter 3 specification (60,000 train / 10,000 test / 10 epochs,
# hidden=500), so "full" is the default here -- the other presets are kept
# only for reference and are not the intended preset for this folder.
DEFAULT_TRAIN_PRESET = "full"

# --- energy proxy ----------------------------------------------------------
# Vendor datasheet figures. Stated in the thesis, not buried here.
# Override for a different machine:  SNN_TDP_CPU_W=45 ./run_experiment.sh
TDP_CPU_W = float(os.environ.get("SNN_TDP_CPU_W", 55.0))
TDP_CPU_SOURCE = os.environ.get(
    "SNN_TDP_CPU_SOURCE",
    "Intel Core i9-14900HX processor base power, Intel ARK datasheet")
