#!/usr/bin/env python3
"""View the SNN benchmarking dashboard. No arguments, no setup.

Double-click this file (or run `python RUN_DASHBOARD.py`) and it opens
http://127.0.0.1:5000 in your browser, reading the results database bundled
in this same folder (results\\benchmarks.db). Everything the dashboard
needs - the app code and the data - lives under this one folder, so nothing
else needs to be present, connected, or moved.

If you want to point this at a different results database instead (for
example a newer run from elsewhere), set SNN_RESULTS_DIR before running:

    setx SNN_RESULTS_DIR "D:\\path\\to\\some\\results"

To stop the dashboard, close this window or press Ctrl+C.
"""
from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from threading import Timer

HERE = Path(__file__).resolve().parent
DASHBOARD_DIR = HERE / "dashboard"
BUNDLED_RESULTS = HERE / "results"


def _ensure_flask():
    try:
        import flask  # noqa: F401
        return
    except ImportError:
        pass
    print("Flask is not installed in this Python interpreter.")
    print(f"Installing it now with: {sys.executable} -m pip install flask\n")
    subprocess.run([sys.executable, "-m", "pip", "install", "flask"], check=False)
    try:
        import flask  # noqa: F401
    except ImportError:
        sys.exit(
            "\nCould not install Flask automatically. Install it yourself,\n"
            f"then run this file again:\n\n    {sys.executable} -m pip install flask\n")


def _candidate_results_dirs():
    """Every place a results database could reasonably live, best first.

    The previous version of this function named one absolute path on the
    machine the edition was cut from and, failing that, returned HERE/results
    whether or not it existed. Neither is present on a fresh machine, so the
    dashboard was started against a folder with no database in it; every query
    then raised inside the page and the browser showed Flask's empty 500 page.
    Nothing here is absolute, and nothing is returned without checking that the
    database is actually in it."""
    yield HERE / "results"
    # A self-contained edition keeps its data beside its own dashboard.
    for child in sorted(HERE.iterdir()) if HERE.is_dir() else []:
        if child.is_dir():
            yield child / "results"
    # Last resort: the live project this edition was cut from, if this happens
    # to be the machine it was cut on.
    yield Path(r"D:\Latest LT RF\SNN_CPU_Experiment\results")


def _pick_results_dir():
    override = os.environ.get("SNN_RESULTS_DIR")
    if override:
        # An override is honoured only if it holds a database. SNN_RESULTS_DIR
        # is documented above as something to set with `setx`, which makes it
        # permanent for the user account: a value set once for a folder that
        # has since moved would otherwise silently break every later run, with
        # no message saying why.
        chosen = Path(override)
        if (chosen / "benchmarks.db").exists():
            return chosen
        print(f"Note: SNN_RESULTS_DIR is set to\n  {chosen}\n"
              "but there is no benchmarks.db there. Ignoring it and looking "
              "for the bundled results instead.\n"
              "(To clear it permanently:  setx SNN_RESULTS_DIR \"\")\n")

    for cand in _candidate_results_dirs():
        try:
            if (cand / "benchmarks.db").exists():
                return cand
        except OSError:
            continue
    # Nothing found. Return the conventional location so the message the
    # dashboard prints names somewhere the user can actually put the file.
    return HERE / "results"

def _port_is_free(host, port):
    """True if this process can bind host:port. On Windows, ports used by
    Hyper-V/WSL (often including 5000) are reserved and refuse binding with
    WinError 10013 even though nothing appears to be listening."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _choose_port(host, preferred):
    for port in (preferred, 8050, 8765, 5050, 8000, 8080):
        if _port_is_free(host, port):
            return port
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))           # let the operating system choose
        return s.getsockname()[1]


def main():
    if not DASHBOARD_DIR.exists():
        sys.exit(f"\nCould not find the dashboard code at:\n  {DASHBOARD_DIR}\n"
                  "This script expects a dashboard\\ folder next to it.")

    results_dir = _pick_results_dir()
    os.environ["SNN_RESULTS_DIR"] = str(results_dir)
    db_path = results_dir / "benchmarks.db"
    if not db_path.exists():
        print(f"Note: no results database found yet at:\n  {db_path}")
        print("The dashboard will still open; it will say so instead of showing charts.\n")
    else:
        print(f"Reading results from:\n  {db_path}\n")

    _ensure_flask()

    sys.path.insert(0, str(DASHBOARD_DIR))
    os.chdir(DASHBOARD_DIR)
    import app as dashboard_app  # dashboard/app.py

    cfg = dashboard_app.config
    port = _choose_port(cfg.HOST, cfg.PORT)
    if port != cfg.PORT:
        print(f"Port {cfg.PORT} is busy or reserved on this computer "
              f"(common on Windows with WSL/Hyper-V); using port {port} instead.")
        cfg.PORT = port
    url = f"http://{cfg.HOST}:{cfg.PORT}"
    Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"Opening {url} - press Ctrl+C here to stop the dashboard.\n")
    dashboard_app.main()


if __name__ == "__main__":
    # Console output on Windows may use a legacy code page; never let a
    # dash or a Greek letter in a message stop the dashboard from starting.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass
    try:
        main()
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except Exception:
        import traceback
        log = HERE / "DASHBOARD_START_LOG.txt"
        text = traceback.format_exc()
        try:
            log.write_text(text, encoding="utf-8")
        except OSError:
            pass
        print("\nThe dashboard could not start. The error is below and was saved to")
        print(f"  {log}\n")
        print(text)
        if os.name == "nt" and sys.stdin and sys.stdin.isatty():
            input("Press Enter to close this window...")
        sys.exit(1)
