"""Result storage.

Three tables rather than one:

  runs        one row per individual measured run. This is the table that makes
              the Chapter 3 statistical plan executable; summaries alone cannot
              support a normality or variance-homogeneity check.
  conditions  one row per condition, aggregated from `runs` at write time. This
              is what the dashboard reads.
  meta        the machine profile, package versions and parameter snapshot for
              this execution, captured programmatically rather than transcribed.
"""
from __future__ import annotations
import json, sqlite3, statistics, datetime
from pathlib import Path
import snnbench.config as C

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_group TEXT, created_at TEXT, machine_json TEXT,
  packages_json TEXT, config_json TEXT
);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_group TEXT, machine_id TEXT, framework TEXT, backend TEXT, task TEXT,
  network_size INTEGER, phase TEXT, run_index INTEGER,
  runtime_s REAL, peak_rss_mb REAL, rss_delta_mb REAL,
  cpu_pct REAL, n_cpu_samples INTEGER, spikes INTEGER, energy_j REAL,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS conditions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_group TEXT, machine_id TEXT, framework TEXT, backend TEXT, task TEXT,
  network_size INTEGER, phase TEXT, n_runs INTEGER,
  runtime_median_s REAL, runtime_mean_s REAL, runtime_sd_s REAL,
  runtime_min_s REAL, runtime_max_s REAL, cv_pct REAL,
  peak_rss_mb REAL, cpu_pct REAL, spikes INTEGER,
  energy_median_j REAL, energy_sd_j REAL,
  eflop INTEGER, compile_dominated INTEGER,
  accuracy_pct REAL, framework_version TEXT, notes TEXT,
  source TEXT DEFAULT 'measured', created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_cond ON conditions(framework, backend, task, network_size);
"""


def connect(path: Path = None) -> sqlite3.Connection:
    con = sqlite3.connect(path or C.DB_PATH)
    con.executescript(SCHEMA)
    return con


def write_meta(con, run_group, machine, packages):
    con.execute(
        "INSERT INTO meta (run_group, created_at, machine_json, packages_json, config_json)"
        " VALUES (?,?,?,?,?)",
        (run_group, _now(), json.dumps(machine), json.dumps(packages),
         json.dumps(config_snapshot())))
    con.commit()


def config_snapshot() -> dict:
    return {k: getattr(C, k) for k in dir(C)
            if k.isupper() and isinstance(getattr(C, k), (int, float, str, list, dict))}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def record_condition(con, *, run_group, machine_id, framework, backend, task,
                     network_size, phase, samples, eflop=None,
                     compile_dominated=False, accuracy=None,
                     framework_version="", notes=""):
    """Store every individual sample, then the aggregate derived from them."""
    now = _now()
    for i, s in enumerate(samples):
        con.execute(
            "INSERT INTO runs (run_group, machine_id, framework, backend, task,"
            " network_size, phase, run_index, runtime_s, peak_rss_mb, rss_delta_mb,"
            " cpu_pct, n_cpu_samples, spikes, energy_j, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (run_group, machine_id, framework, backend, task, network_size, phase,
             i, s.runtime_s, s.peak_rss_mb, s.rss_delta_mb, s.mean_cpu_pct,
             s.n_cpu_samples, s.spikes, s.energy_j(), now))

    rt = [s.runtime_s for s in samples]
    # Utilisation, and therefore the energy proxy, can legitimately be absent
    # for a run too short for the CPU clock to resolve. Such a run contributes
    # its runtime and its memory to the condition summary but must not
    # contribute an invented energy figure, so the energy aggregates are taken
    # over the runs that actually have one and are written as NULL when none
    # does. A NULL is readable downstream as "not measured"; a number is not.
    en = [e for e in (s.energy_j() for s in samples) if e is not None]
    cpu_measured = [s.mean_cpu_pct for s in samples if s.mean_cpu_pct is not None]
    sd = statistics.stdev(rt) if len(rt) > 1 else 0.0
    med = statistics.median(rt)
    con.execute(
        "INSERT INTO conditions (run_group, machine_id, framework, backend, task,"
        " network_size, phase, n_runs, runtime_median_s, runtime_mean_s, runtime_sd_s,"
        " runtime_min_s, runtime_max_s, cv_pct, peak_rss_mb, cpu_pct, spikes,"
        " energy_median_j, energy_sd_j, eflop, compile_dominated, accuracy_pct,"
        " framework_version, notes, source, created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'measured',?)",
        (run_group, machine_id, framework, backend, task, network_size, phase,
         len(rt), med, statistics.fmean(rt), sd, min(rt), max(rt),
         # Coefficient of variation in its conventional form, the standard
         # deviation over the MEAN. An earlier version divided by the median,
         # which is a different statistic carrying the same name and made the
         # dashboard and the analysis disagree on the same condition.
         100.0 * sd / statistics.fmean(rt) if rt and statistics.fmean(rt) else 0.0,
         max((s.peak_rss_mb for s in samples if s.peak_rss_mb is not None), default=None),
         statistics.fmean(cpu_measured) if cpu_measured else None,
         int(statistics.median([s.spikes for s in samples])),
         statistics.median(en) if en else None,
         (statistics.stdev(en) if len(en) > 1 else (0.0 if en else None)),
         eflop, int(bool(compile_dominated)), accuracy,
         framework_version, notes, now))
    con.commit()


def export_csv(con, out_dir: Path = None):
    import csv
    out_dir = out_dir or C.RESULTS_DIR
    for table in ("runs", "conditions"):
        cur = con.execute(f"SELECT * FROM {table}")
        cols = [d[0] for d in cur.description]
        path = out_dir / f"{table}.csv"
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(cur.fetchall())
        print(f"  wrote {path}")
