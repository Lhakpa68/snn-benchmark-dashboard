"""Palette and simulator metadata.

Two things live here rather than in a template, because both dashboards need
them and neither may be allowed to state something the other does not:

  * colour, assigned to a SIMULATOR and never to a rank
  * what each simulator and each baseline actually is, in plain language

Supporting citations are deliberately NOT held here. Evidence belongs in the
thesis, under the claim it supports, where a reader can follow it properly.
On the dashboard it competed for attention with the measurements themselves,
so the interface explains what each entry is and leaves the argument to the
document.

Colour is assigned per framework, never per backend and never per rank. A
simulator keeps its colour whichever backends are on screen, so switching a
filter never repaints the survivors.

The palette is tuned for the LIGHT surface defined below. A hue picked for a
dark page is often too pale on a white one: it loses contrast against the
panel rather than gaining it. When the page moved to a light surface on
27 September 2026 the six hues were re-checked against it, and only snnTorch's
green needed re-stepping, from #1fa989 to #17997b, to clear 3:1. Keeping the
other five unchanged matters, because the thesis figures and text already tie
each colour to a simulator. The set passes every check on this surface:

    lightness band     all inside the L 0.43-0.77 band
    chroma floor       all >= 0.1          (none reads as grey)
    CVD separation     worst adjacent pair dE 8.7 (protan), 10.2 (tritan)
    normal vision      worst adjacent pair dE 20.9
    contrast           all >= 3:1 against the surface

Re-run after any edit:

    node scripts/validate_palette.js \\
      "#4f93ea,#d97038,#17997b,#9d78e6,#b58b23,#e15f96" --mode light
"""
from __future__ import annotations

# --------------------------------------------------------------- surfaces
# A light theme, adopted 27 Sep 2026. The earlier deep-navy surface was
# judged too dark to read comfortably. A near-white surface with a faint warm
# cast holds the accents without glare and keeps long sessions easy on the eye.
SURFACE = "#fcfcfb"        # page background
CARD = "#ffffff"           # panel background, one step lighter than the page
CARD_ALT = "#f3f5f9"       # secondary panel / table header
BORDER = "#e1e6ee"         # hairline
GRID = "#e9edf3"           # chart gridlines, fainter than the border

INK = "#182130"            # primary text - near-black, not pure black
INK_SOFT = "#46536a"       # secondary text
INK_MUTED = "#6e7c92"      # captions, axis labels, units

GOOD = "#17845f"
WARN = "#96690f"
BAD = "#c2453b"

# ----------------------------------------------------------- categorical
# Fixed order. A simulator's slot never changes, so adding a simulator
# appends rather than reshuffles.
FRAMEWORK_COLORS = {
    "brian2": "#4f93ea",        # blue
    "nest": "#d97038",          # orange
    "snntorch": "#17997b",      # green
    "spikingjelly": "#9d78e6",  # purple
    "nengo": "#b58b23",         # amber
    "reference": "#e15f96",     # magenta - the NumPy baseline, not a simulator
}

FRAMEWORK_LABELS = {
    "brian2": "Brian2",
    "nest": "NEST",
    "snntorch": "snnTorch",
    "spikingjelly": "SpikingJelly",
    "nengo": "Nengo",
    "reference": "NumPy baseline",
}

# The baseline is not a simulator under test. It is the control condition:
# the same network, same parameters, same protocol, written in plain NumPy
# with no simulator at all. Keeping it separate in the interface is what
# stops a reader mistaking a control for a competitor.
CONTROL_FRAMEWORKS = {"reference"}

# Backend -> dash pattern, so backends within one simulator stay separable
# without spending a second hue on them.
BACKEND_DASH = {
    "numpy": "solid", "cython": "dash", "cpp_standalone": "dot",
    "threads1": "solid", "threads2": "dash",
    "cpu": "solid", "reference": "solid",
    "scalar": "dot", "vectorised": "dash",
}


# ------------------------------------------------------- what things are
# Every entry below is shown in the interface next to the data it describes,
# in plain language. These are descriptions, not arguments: the case for each
# design decision, with its sources, is made in the thesis.
FRAMEWORK_INFO = {
    "brian2": dict(
        kind="simulator",
        one_line="Equation-based simulator for computational neuroscience.",
        detail="Neuron and synapse dynamics are written as differential "
               "equations in a notation close to the textbook form, then "
               "translated to executable code. Three code-generation targets "
               "are measured here (NumPy, Cython, C++ standalone) because the "
               "choice moves runtime by more than an order of magnitude, and "
               "reporting one target as though it characterised the simulator "
               "would be reporting the target.",
        best_for="Custom neuron models and exploratory biological modelling",
    ),
    "nest": dict(
        kind="simulator",
        one_line="Simulator built for large, sparsely connected networks.",
        detail="Targets cortical-scale simulation with thread and MPI "
               "parallelism. Its kernel allocates per-neuron and per-synapse "
               "structures up front, which is why its memory footprint is "
               "flat and unremarkable at small networks and the largest in "
               "this study once the network grows. Two thread counts are "
               "measured to test whether thread parallelism pays at these "
               "sizes.",
        best_for="Large sparse networks at cortical scale",
    ),
    "snntorch": dict(
        kind="training library",
        one_line="PyTorch-native surrogate-gradient training.",
        detail="Trains spiking networks by backpropagation-through-time with "
               "a surrogate gradient standing in for the non-differentiable "
               "spike. It evaluates a discrete recurrence over a fixed number "
               "of timesteps rather than integrating a differential equation, "
               "which is a materially different computation and is why the "
               "equivalence check in this study exists.",
        best_for="Supervised training from a conventional deep-learning workflow",
    ),
    "spikingjelly": dict(
        kind="training library",
        one_line="PyTorch-based simulator aimed at deeper spiking networks.",
        detail="Also surrogate-gradient based, with a broader layer library "
               "aimed at deeper architectures and event-driven vision. Run "
               "here under an identical training procedure to snnTorch, which "
               "is what makes the near-identical accuracy a check on the "
               "harness rather than a coincidence.",
        best_for="Deeper spiking architectures and event-driven vision",
    ),
    "nengo": dict(
        kind="simulator",
        one_line="Neural Engineering Framework (NEF); solves decoders in closed form.",
        detail="Represents values in populations of neurons and solves for "
               "decoding weights in a single least-squares step. There is no "
               "epoch and no gradient, so its training figure is the cost of "
               "one solve. Its accuracy is bounded by how well an ensemble of "
               "a given width can represent the input space, which is a "
               "property of the method rather than a defect.",
        best_for="Neuromorphic deployment and closed-form function approximation",
    ),
    "reference": dict(
        kind="control",
        one_line="Plain NumPy implementation of the identical network — the "
                 "experimental control, not a simulator.",
        detail="This is the baseline against which every simulator is read. "
               "It implements exactly the same network — same neuron count, "
               "same fan-in, same time constant, threshold, timestep and "
               "input rate — in plain NumPy, with no simulator involved. It "
               "answers the question a simulator comparison cannot answer on "
               "its own: what does this model cost with no simulator at all? "
               "Two variants are measured. The SCALAR variant loops over "
               "neurons one at a time and shows the cost of the naive "
               "implementation anyone would write first. The VECTORISED "
               "variant expresses the same update as array operations and "
               "shows what the same machine achieves when the arithmetic is "
               "handed to optimised numerical libraries. A simulator slower "
               "than the vectorised baseline is buying its abstractions at a "
               "measurable price; a simulator faster than it is earning its "
               "overhead. Neither variant competes for a ranking, and both "
               "are drawn dashed throughout so they never read as "
               "competitors.",
        best_for="Establishing the floor and ceiling of the same model without a simulator",
    ),
}

# Backend-level notes, shown on demand rather than crowding the main view.
BACKEND_INFO = {
    "brian2/numpy": "Brian2's interpreted target. No compilation step, so no "
                    "first-run penalty, and the slowest of Brian2's three at "
                    "large networks.",
    "brian2/cython": "Brian2 compiled through Cython. Faster inner loop, at "
                     "the cost of a compilation step on first use.",
    "brian2/cpp_standalone": "Brian2 generating and compiling a standalone C++ "
                             "program. Rebuilds on every invocation here, so "
                             "the measured time is the toolchain's rather than "
                             "the simulator's — flagged compile-dominated and "
                             "excluded from rankings.",
    "nest/threads1": "NEST with a single thread. The baseline NEST "
                     "configuration.",
    "nest/threads2": "NEST with two threads, one of three thread counts "
                     "measured to test whether thread parallelism pays at "
                     "these network sizes.",
    "nest/threads4": "NEST with four threads, the largest thread count "
                     "measured. On this machine it is the fastest of the "
                     "three at the largest network size, though only "
                     "modestly ahead of two threads.",
    "snntorch/cpu": "snnTorch running on the processor, the single hardware "
                    "platform used throughout this study.",
    "spikingjelly/cpu": "SpikingJelly on the processor.",
    "nengo/reference": "Nengo's own built-in simulator, which Nengo itself "
                       "calls the reference simulator. Despite the name this "
                       "is Nengo, not the NumPy control — the naming collision "
                       "is Nengo's, and the interface labels it as Nengo "
                       "everywhere to avoid it.",
    "reference/scalar": "The NumPy control, written as an explicit per-neuron "
                        "loop. The naive implementation, and the slow floor.",
    "reference/vectorised": "The NumPy control, written as array operations. "
                            "The fast ceiling for this model without a "
                            "simulator.",
}


def color_for(framework: str) -> str:
    return FRAMEWORK_COLORS.get(framework, "#5c6470")


def label_for(framework: str) -> str:
    return FRAMEWORK_LABELS.get(framework, framework)


def dash_for(framework: str, backend: str) -> str:
    """Controls are always dashed so they read as a reference line rather
    than as another simulator in the race."""
    if framework in CONTROL_FRAMEWORKS:
        return "dash"
    return BACKEND_DASH.get(backend, "solid")


def backend_note(framework: str, backend: str) -> str:
    return BACKEND_INFO.get(f"{framework}/{backend}", "")


def info_for(framework: str) -> dict:
    return FRAMEWORK_INFO.get(framework, {})
