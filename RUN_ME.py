#!/usr/bin/env python3
"""Run the whole experiment. No arguments, no setup, no command line.

In PyCharm: right-click this file in the project tree and choose Run.
Anywhere else: python RUN_ME.py

It works out where it lives, so the working directory does not matter, and it
imports nothing before checking that the environment can support the import.
Every step writes a log into results/ as it goes, so a run that dies partway
still leaves evidence of how far it got.
"""
from __future__ import annotations

import os
import platform
import sys
import time
import traceback
from pathlib import Path

# NEST's own FAQ documents a real segfault when PyNEST shares a process with
# certain SciPy builds, and gives one fix: import scipy before nest, not
# after. https://nest-simulator.readthedocs.io/en/stable/faqs/faqs.html
# Every simulator here runs in one process (that is the whole point of this
# harness), and nest is probed/imported before nengo — the simulator that
# actually needs scipy — so on the unpatched import order scipy only enters
# the process *after* nest already has, which is precisely the bad order the
# FAQ warns about. This crashed nest.ResetKernel() itself, confirmed by a
# faulthandler C-level traceback (see below), on the very run it was added
# to fix. Importing scipy here, before anything else, fixes the order for
# every simulator this process will go on to run, not just nengo's own
# import of it.
try:
    import scipy  # noqa: F401
except ImportError:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.chdir(HERE)

# NEST has now crashed this campaign twice on this machine with no Python
# exception and no traceback — only a bare exit code (245), the signature of
# a native abort/segfault that Python's own try/except in section 3 below
# cannot catch. Per-call debug prints (SNNBENCH_NEST_DEBUG, added to the NEST
# adapter) pinned the second crash to nest.ResetKernel() itself, on the very
# first call, with local_num_threads=1 — so this is not a multi-threading or
# CPU-affinity problem (the OMP_PROC_BIND/KMP_AFFINITY/KMP_DUPLICATE_LIB_OK
# variables below were tried against that theory and did not stop it; they
# are left set since they are harmless no-ops if they are not the cause).
# faulthandler is Python's own tool for exactly this situation: it installs C
# signal handlers for SIGSEGV/SIGABRT/SIGBUS/SIGILL/SIGFPE and prints a
# low-level stack trace before the process dies, which is the only way left
# to see where inside ResetKernel() this is actually happening.
import faulthandler
faulthandler.enable()
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_PROC_BIND", "FALSE")
os.environ.setdefault("KMP_AFFINITY", "disabled")
# Turns on step-by-step prints inside the NEST adapter's setup(), so the
# console shows exactly which NEST call a crash happens on, rather than only
# a bare exit code. Harmless, and worth leaving on until NEST has completed
# cleanly at least once on this machine.
os.environ.setdefault("SNNBENCH_NEST_DEBUG", "1")
# One more mitigation for the same crash: NEST's debug counter shows it
# surviving several ResetKernel() cycles before dying (call #4 out of 10 in
# one run), which is the signature of memory corruption from repeated
# alloc/free cycling rather than a first-call problem — glibc's malloc arena
# behaviour is a documented source of exactly this under WSL2. Forcing a
# single arena and prompt trimming is a standard, safe mitigation.
os.environ.setdefault("MALLOC_ARENA_MAX", "1")

RESULTS = HERE / "results"
RESULTS.mkdir(exist_ok=True)

BAR = "=" * 70


def head(title):
    print(f"\n{BAR}\n {title}\n{BAR}", flush=True)


# ------------------------------------------------- 0. find a usable interpreter
#
# PyCharm creates its own virtual environment per project and selects it
# automatically. If that environment is empty, or is on a Python version the
# simulators publish no wheels for, pressing Run fails through no fault of the
# benchmark. Rather than ask the user to go and reconfigure PyCharm, this
# section looks for a better interpreter on the machine and re-launches itself
# with it. One hop only, guarded by an environment variable.

CORE = ("numpy", "psutil")
FRAMEWORKS = ("brian2", "nest", "nengo", "snntorch", "spikingjelly", "norse")

_PROBE = (
    "import sys, importlib.util as u;"
    "mods=%r;"
    "print('%%d.%%d' %% sys.version_info[:2], "
    "','.join(m for m in mods if u.find_spec(m) is not None))"
) % (list(CORE + FRAMEWORKS),)


def _walk_for_interpreters(root, max_depth=5, budget=4000):
    """Bounded search for */bin/python under root. Used only when the pattern
    list above finds nothing usable, because a virtual environment can live
    anywhere and guessing paths is not a search."""
    found, visited = [], 0
    root = str(root)
    skip = {".git", "__pycache__", "node_modules", ".cache", ".local",
            "snap", ".rustup", ".cargo", "mnt", ".pycharm_helpers"}
    base_depth = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root, topdown=True,
                                                onerror=lambda e: None):
        visited += 1
        if visited > budget:
            break
        if dirpath.count(os.sep) - base_depth >= max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in skip]
        if os.path.basename(dirpath) == "bin":
            # `python` and `python3` in one bin directory are the same
            # interpreter. Take the first that exists and stop.
            for name in ("python", "python3"):
                cand = os.path.join(dirpath, name)
                if os.path.isfile(cand) and os.access(cand, os.X_OK):
                    found.append(cand)
                    break
            dirnames[:] = []
    return found


def _candidate_interpreters():
    """Plausible interpreters, cheaply. find_spec is used rather than import,
    so probing does not pay the cost of loading torch."""
    import glob
    home = Path.home()
    seen, out = set(), []
    patterns = [
        str(home / ".virtualenvs" / "*" / "bin" / "python"),
        str(home / "*" / ".venv" / "bin" / "python"),
        str(home / "*" / "*" / ".venv" / "bin" / "python"),
        str(home / "projects" / "*" / ".venv" / "bin" / "python"),
        str(home / "venvs" / "*" / "bin" / "python"),
        str(home / "*" / "venv" / "bin" / "python"),
        str(home / "*" / "*" / "venv" / "bin" / "python"),
        str(home / "*" / "*" / "*" / ".venv" / "bin" / "python"),
        str(home / ".local" / "share" / "virtualenvs" / "*" / "bin" / "python"),
        str(home / "*env*" / "bin" / "python"),
        str(home / "miniconda3" / "envs" / "*" / "bin" / "python"),
        str(home / "anaconda3" / "envs" / "*" / "bin" / "python"),
        str(home / ".conda" / "envs" / "*" / "bin" / "python"),
        "/usr/bin/python3.*", "/usr/local/bin/python3.*",
        "/usr/bin/python3", "/usr/local/bin/python3",
    ]
    for pat in patterns:
        for p in glob.glob(pat):
            # Deduplicate on the literal path, not the resolved one. A virtual
            # environment's python is a symlink to the base interpreter, so
            # resolving would collapse every venv onto the system Python and
            # hide exactly the environments worth finding.
            ap = os.path.abspath(p)
            if ap not in seen and os.path.isfile(p) and os.access(p, os.X_OK):
                seen.add(ap)
                out.append(p)
    return out


def _probe(py, timeout=25):
    """Return (version_tuple, set_of_available_modules) or None."""
    import subprocess
    try:
        r = subprocess.run([py, "-c", _PROBE], capture_output=True, text=True,
                           timeout=timeout)
        if r.returncode != 0 or not r.stdout.strip():
            return None
        parts = r.stdout.split()
        ver = tuple(int(x) for x in parts[0].split("."))
        mods = set(parts[1].split(",")) if len(parts) > 1 and parts[1] else set()
        return ver, mods
    except Exception:
        return None


def _score(ver, mods):
    """Higher is better. Core packages are mandatory; simulator count decides
    between otherwise usable interpreters; a version the wheels exist for
    breaks ties."""
    if not all(m in mods for m in CORE):
        return -1
    n_fw = sum(1 for m in FRAMEWORKS if m in mods)
    version_ok = 1 if (3, 9) <= ver < (3, 13) else 0
    return n_fw * 10 + version_ok


def _launch(py):
    """Re-execute this same file under another interpreter. One hop only."""
    import subprocess
    env = dict(os.environ, SNNBENCH_NO_RELAUNCH="1")
    sys.exit(subprocess.run([py, str(Path(__file__).resolve())],
                            cwd=str(HERE), env=env).returncode)


def _report_no_interpreter(surveyed):
    """Nothing on this machine can run the benchmark. Say exactly what is here
    and exactly what to type, rather than pointing at another document."""
    print("\n No interpreter on this machine can run the benchmark yet.")
    print("\n Everything I found:\n")
    print("   simulators  core  python  interpreter")
    print("   " + "-" * 66)
    for py, ver, mods in surveyed:
        n_fw = sum(1 for m in FRAMEWORKS if m in mods)
        core_ok = " ok " if all(m in mods for m in CORE) else "MISS"
        print(f"   {n_fw} of {len(FRAMEWORKS)}      {core_ok}  "
              f"{ver[0]}.{ver[1]:<4}  {py}")

    # Prefer a version the wheels actually exist for.
    installable = [(py, ver) for py, ver, _ in surveyed
                   if (3, 9) <= ver < (3, 13)]
    print("\n" + BAR)
    if installable:
        target, tver = installable[0]
        print(f"\n Install into the Python {tver[0]}.{tver[1]} above. Copy this line:\n")
        print(f'   "{target}" -m pip install -r requirements-frameworks.txt')
        print("\n Then run this file again. It will find that environment by itself.")
    else:
        print("\n Every interpreter here is 3.13 or newer, and nest-simulator and")
        print(" norse publish no wheels for those, so pip would compile them from")
        print(" source and fail. Install an older one first:\n")
        print("   sudo apt update && sudo apt install python3.11 python3.11-venv")
        print("   python3.11 -m venv ~/snnbench-env")
        print("   ~/snnbench-env/bin/pip install -r requirements-frameworks.txt")
        print("\n Then run this file again.")
    print("\n If an environment already exists somewhere I did not look, name it:\n")
    print("   SNNBENCH_PYTHON=/full/path/to/python python3 RUN_ME.py")
    print()


def _relaunch_if_better():
    if os.environ.get("SNNBENCH_NO_RELAUNCH"):
        return

    # An explicit choice always wins over anything found by searching.
    pinned = os.environ.get("SNNBENCH_PYTHON", "").strip()
    if pinned:
        if os.path.abspath(pinned) != os.path.abspath(sys.executable):
            print(f"\n SNNBENCH_PYTHON is set. Re-launching with:\n   {pinned}\n")
            _launch(pinned)

    here_ver = sys.version_info[:2]
    here_mods = set()
    import importlib.util as u
    for m in CORE + FRAMEWORKS:
        try:
            if u.find_spec(m) is not None:
                here_mods.add(m)
        except Exception:
            pass
    here_score = _score(here_ver, here_mods)

    # Good enough already: core present and at least one simulator.
    if here_score >= 10:
        return

    print("\n This interpreter cannot run the benchmark as it stands.")
    print(" Looking for a better one on this machine, which takes a moment...",
          flush=True)

    surveyed = [(sys.executable, here_ver, here_mods)]

    def survey(paths):
        best, best_score, best_info = None, here_score, None
        for py in paths:
            if os.path.abspath(py) == os.path.abspath(sys.executable):
                continue
            if any(os.path.abspath(py) == os.path.abspath(q)
                   for q, _, _ in surveyed):
                continue
            got = _probe(py)
            if not got:
                continue
            ver, mods = got
            surveyed.append((py, ver, mods))
            s = _score(ver, mods)
            if s > best_score:
                best, best_score, best_info = py, s, (ver, mods)
        return best, best_info

    best, best_info = survey(_candidate_interpreters())

    if best is None:
        # The pattern list is a guess. A virtual environment can live anywhere,
        # so fall back to an actual bounded search of the home directory before
        # concluding that nothing here works.
        print(" Nothing in the usual places. Searching your home directory...",
              flush=True)
        best, best_info = survey(_walk_for_interpreters(Path.home()))

    if best is None:
        surveyed.sort(key=lambda t: -_score(t[1], t[2]))
        _report_no_interpreter(surveyed)
        return

    ver, mods = best_info
    n_fw = sum(1 for m in FRAMEWORKS if m in mods)
    print(f"\n Found one: Python {ver[0]}.{ver[1]} with {n_fw} of "
          f"{len(FRAMEWORKS)} simulators")
    print(f"   {best}")
    print(f"   has: {', '.join(sorted(mods))}")
    print("\n Re-launching with it. Nothing is installed or changed; this just")
    print(" runs the same file under an interpreter that can support it.")
    print(f"\n{BAR}\n", flush=True)

    try:
        _launch(best)
    except FileNotFoundError:
        print(f" Could not launch {best}. Continuing with the current one.\n")


def fail(msg, detail=""):
    head("STOPPED")
    print(f" {msg}\n")
    if detail:
        print(detail)
    print("\n Nothing was measured. Fix the above and run this file again.\n")
    sys.exit(1)


# --------------------------------------------------------------- 0. sanity
head("SNN CPU benchmark")
print(f" python      : {sys.version.split()[0]}  ({sys.executable})")
print(f" platform    : {platform.system()} {platform.release()} {platform.machine()}")
print(f" working dir : {HERE}")

_relaunch_if_better()

if sys.version_info < (3, 9):
    fail(f"Python {sys.version_info.major}.{sys.version_info.minor} is too old. "
         "This suite needs 3.9 or newer.")

if sys.version_info >= (3, 13):
    print(f"\n {'!' * 68}")
    print(f" Python {sys.version_info.major}.{sys.version_info.minor} is newer than"
          f" the simulators have wheels for.")
    print(f" {'!' * 68}")
    print("\n nest-simulator and norse publish no wheel for this version, so pip")
    print(" compiles them from source. That needs CMake, GSL and a C++ toolchain,")
    print(" takes a long time, and usually fails. torch and snnTorch are often")
    print(" missing here too.")
    print("\n Use Python 3.11 or 3.12 instead. To find one that already has the")
    print(" simulators installed:\n")
    print("     bash find_interpreter.sh\n")
    print(" Continuing anyway, in case this interpreter is better provisioned")
    print(" than expected. Whatever is missing is reported below.\n")

missing = []
for mod, why in (("numpy", "the benchmark model and all analysis"),
                 ("psutil", "measuring runtime, memory and CPU utilisation")):
    try:
        __import__(mod)
    except ImportError:
        missing.append((mod, why))

if missing:
    lines = "\n".join(f"   {m:<10} needed for {w}" for m, w in missing)
    fail("Required packages are missing from this interpreter.",
         f"{lines}\n\n"
         f"   Install them into THIS interpreter, not another one:\n\n"
         f"     {sys.executable} -m pip install " +
         " ".join(m for m, _ in missing) + "\n\n"
         f"   In PyCharm, check which interpreter is selected:\n"
         f"     File > Settings > Project > Python Interpreter\n"
         f"   The path shown there must match the one printed above.")

# ------------------------------------------- 0b. install what is missing
#
# spikingjelly is pip-installable and pure-Python (unlike NEST, it needs no
# system toolchain), so a missing copy is fixed here rather than left for the
# person running this to notice and do by hand. Anything that cannot be
# fixed this way (NEST outside WSL, a version with no wheel) still falls
# through to the per-simulator skip below, unchanged.
def _ensure_installed(mods):
    import importlib.util as u
    import subprocess
    missing = [m for m in mods if u.find_spec(m) is None]
    if not missing:
        return
    print(f"\n Installing missing packages into this interpreter: {', '.join(missing)}")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", *missing],
                       timeout=600, check=False)
    except Exception as e:
        print(f" Install attempt failed ({e}); continuing without it.")
    importlib.invalidate_caches()

import importlib
_ensure_installed(["spikingjelly"])

try:
    from snnbench import registry, runner, analyse
    import snnbench.config as C
except Exception:
    fail("The snnbench package could not be imported.",
         traceback.format_exc() +
         "\n   This normally means PyCharm's working directory is set "
         "somewhere else.\n   Run configuration > Working directory should be:\n"
         f"     {HERE}")

# ------------------------------------------------------- 1. what will run
head("1 of 4   Environment and available simulators")
inv = registry.inventory()
runnable = []
for row in inv:
    mark = "OK " if row["importable"] else "-- "
    print(f" {mark}{row['label']:<16} {row['version_or_reason']}")
    for b in row["backends"]:
        if b["available"]:
            runnable.append(f"{row['framework']}/{b['key']}")
            print(f"      {b['key']:<18} available")
        else:
            print(f"      {b['key']:<18} UNAVAILABLE: {b['reason']}")

print(f"\n {len(runnable)} execution backends will be measured.")

frameworks_present = sum(1 for r in inv
                         if r["importable"] and r["framework"] != "reference")
if frameworks_present == 0:
    fail("None of the six simulators is installed in this interpreter.",
         "   The NumPy reference control would run, but a benchmark of one\n"
         "   control and no simulators is not worth the time.\n\n"
         f"     {sys.executable} -m pip install brian2 nest-simulator nengo "
         "snntorch spikingjelly norse\n\n"
         "   NEST does not install on native Windows. If this interpreter is a\n"
         "   Windows one, use your WSL interpreter instead, where NEST works.\n"
         "   In PyCharm: Settings > Project > Python Interpreter > Add >\n"
         "   WSL, then point it at the Python inside your WSL environment.")

if frameworks_present < 4:
    print(f"\n Only {frameworks_present} of the six simulators are importable here.")
    print(" The run will go ahead and the missing ones are recorded as skips")
    print(" with a stated reason, which is a valid smaller experiment.")

# ------------------------------------------------- 2. equivalence check
head("2 of 4   Equivalence validation")
print(" Every backend runs once and its output firing rate is compared against")
print(" a plain-NumPy reference implementation of the same network.\n")
rows = registry.validate(n=500)
lines = [f"  {'simulator/backend':<28} {'status':<16} {'rate Hz':>9} {'ref Hz':>9}"]
for r in rows:
    name = f"{r['framework']}/{r.get('backend') or '-'}"
    lines.append(f"  {name:<28} {r['status']:<16} "
                 f"{r.get('rate_hz', '-'):>9} {r.get('ref_rate_hz', '-'):>9}"
                 + (f"   {r['reason'][:70]}" if r.get("reason") else ""))
report = "\n".join(lines)
print(report)
(RESULTS / "validate.txt").write_text(report, encoding="utf-8")

bad = [r for r in rows if r["status"] in ("rate mismatch", "error")]
if bad:
    print(f"\n {len(bad)} backend(s) need attention, listed above with a reason.")
    print(" The run continues; those backends are recorded with their status.")

# ------------------------------------------------------ 3. the experiment
head("3 of 4   The experiment")
print(" Inference, a five-point scalability sweep, and training.")
print(f" Warm-up {C.WARMUP_RUNS}, measured {C.MEASURED_RUNS}, sizes {C.SIZES}.")
print("\n This is the long part. Leave the machine alone while it runs:")
print(" background load inflates the timings and that cannot be repaired")
print(" afterwards.\n")

t0 = time.perf_counter()
# The campaign that mattered for this thesis is complete: brian2's three
# backends (run_group 3dd09b61bd76-fb0ab3) and nest/nengo/snntorch/
# spikingjelly/reference (run_group 3dd09b61bd76-1ca062) each have their full
# WARMUP_RUNS + MEASURED_RUNS on this machine, with the NEST subprocess-
# isolation fix (see snnbench/nest_worker.py and nest_train_worker.py)
# verified working end to end. The `only=` restriction that was here for the
# one resumed run is gone; a fresh invocation of this file now measures
# everything from a clean start, as it did before that restriction was added.
try:
    runner.run()
except KeyboardInterrupt:
    print("\n Interrupted. Rows already written are kept; re-run to continue.")
    sys.exit(1)
except Exception:
    print("\n The run stopped with an error. Rows already written are kept.\n")
    traceback.print_exc()
    sys.exit(1)
print(f"\n Elapsed: {(time.perf_counter() - t0) / 60:.1f} minutes")

# ----------------------------------------------------------- 4. analysis
head("4 of 4   Analysis")
analyse.main(C.DB_PATH)

head("Done")
print(f" Everything is in: {RESULTS}\n")
for f in sorted(RESULTS.iterdir()):
    if f.is_file() and f.name != ".gitkeep":
        print(f"   {f.name:<24} {f.stat().st_size / 1024:>9,.0f} KB")
print("\n Send that whole folder back.")
print("\n To look at the results:  cd dashboard && python app.py")
print(" then open http://127.0.0.1:5000\n")
