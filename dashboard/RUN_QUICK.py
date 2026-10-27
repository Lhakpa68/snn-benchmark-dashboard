"""Quick end-to-end confirmation run — equivalent of `python run.py bench --quick`
(inference + scalability only, sizes 100 and 500, 1 warmup + 2 measured runs),
but self-relaunching under a working interpreter the same way RUN_ME.py does,
so it works regardless of which environment PyCharm currently has selected.

This file lives in dashboard/ (not the project root) purely so it shows up in
the PyCharm project that already has this folder open — it operates on the
project root one level up, exactly like run.py and RUN_ME.py do.

In PyCharm: open this file and press Run (the gutter arrow next to
`if __name__ == "__main__":`, or the toolbar Run button while this tab is
active). Anywhere else: python RUN_QUICK.py

Two to three minutes. Proves the pipeline works end to end before committing
to the long full run (RUN_ME.py). Writes real rows into the same
results/benchmarks.db the dashboard reads — it does not touch or clear
anything already there.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent      # .../SNN_CPU_Experiment
sys.path.insert(0, str(HERE))

CORE = ("numpy", "psutil")
FRAMEWORKS = ("brian2", "nest", "nengo", "snntorch", "spikingjelly", "norse")


def _available_modules():
    import importlib.util as u
    mods = set()
    for m in CORE + FRAMEWORKS:
        try:
            if u.find_spec(m) is not None:
                mods.add(m)
        except Exception:
            pass
    return mods


def _score(ver, mods):
    if not all(m in mods for m in CORE):
        return -1
    n_fw = sum(1 for m in FRAMEWORKS if m in mods)
    version_ok = 1 if (3, 9) <= ver < (3, 13) else 0
    return n_fw * 10 + version_ok


def _probe(py, timeout=25):
    probe = (
        "import sys, importlib.util as u;"
        "mods=%r;"
        "print('%%d.%%d' %% sys.version_info[:2], "
        "','.join(m for m in mods if u.find_spec(m) is not None))"
    ) % (list(CORE + FRAMEWORKS),)
    try:
        r = subprocess.run([py, "-c", probe], capture_output=True, text=True,
                            timeout=timeout)
        if r.returncode != 0 or not r.stdout.strip():
            return None
        parts = r.stdout.split()
        ver = tuple(int(x) for x in parts[0].split("."))
        mods = set(parts[1].split(",")) if len(parts) > 1 and parts[1] else set()
        return ver, mods
    except Exception:
        return None


def _candidate_interpreters():
    """The environment PYCHARM.md documents as already having everything,
    checked first, plus the same glob patterns RUN_ME.py searches."""
    home = Path.home()
    seen, out = set(), []
    patterns = [
        str(home / "projects" / "snn_benchmark_dashboard" / ".venv" / "bin" / "python"),
        str(home / ".virtualenvs" / "*" / "bin" / "python"),
        str(home / "*" / ".venv" / "bin" / "python"),
        str(home / "*" / "*" / ".venv" / "bin" / "python"),
        str(home / "projects" / "*" / ".venv" / "bin" / "python"),
        str(home / "venvs" / "*" / "bin" / "python"),
        str(home / "*" / "venv" / "bin" / "python"),
        str(home / "*" / "*" / "venv" / "bin" / "python"),
        str(home / "miniconda3" / "envs" / "*" / "bin" / "python"),
        str(home / "anaconda3" / "envs" / "*" / "bin" / "python"),
        str(home / ".conda" / "envs" / "*" / "bin" / "python"),
    ]
    for pat in patterns:
        for p in glob.glob(pat):
            ap = os.path.abspath(p)
            if ap not in seen and os.path.isfile(p) and os.access(p, os.X_OK):
                seen.add(ap)
                out.append(p)
    return out


def _relaunch_if_needed():
    if os.environ.get("SNNBENCH_NO_RELAUNCH"):
        return

    here_ver = sys.version_info[:2]
    here_mods = _available_modules()
    here_score = _score(here_ver, here_mods)
    if here_score >= 10:
        return  # already has core + at least one simulator

    print("This interpreter cannot run the benchmark as it stands.")
    print("Looking for a better one on this machine...", flush=True)

    best, best_score, best_path = None, here_score, None
    for py in _candidate_interpreters():
        if os.path.abspath(py) == os.path.abspath(sys.executable):
            continue
        got = _probe(py)
        if not got:
            continue
        ver, mods = got
        s = _score(ver, mods)
        if s > best_score:
            best, best_score, best_path = (ver, mods), s, py

    if best_path is None:
        print("No better interpreter found in the usual places; continuing "
              "with the current one (missing simulators will show as skips).")
        return

    ver, mods = best
    n_fw = sum(1 for m in FRAMEWORKS if m in mods)
    print(f"Found one: Python {ver[0]}.{ver[1]} with {n_fw} of "
          f"{len(FRAMEWORKS)} simulators")
    print(f"  {best_path}")
    print("Re-launching with it. Nothing is installed or changed.\n")
    env = dict(os.environ, SNNBENCH_NO_RELAUNCH="1")
    sys.exit(subprocess.run([best_path, str(Path(__file__).resolve())],
                             cwd=str(HERE), env=env).returncode)


if __name__ == "__main__":
    print(f"python      : {sys.version.split()[0]}  ({sys.executable})")
    _relaunch_if_needed()
    os.chdir(HERE)
    sys.argv = ["run.py", "bench", "--quick"]
    import run as run_module  # HERE/run.py
    run_module.main()
