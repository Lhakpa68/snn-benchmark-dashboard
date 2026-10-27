"""Read-only helpers for the review scripts. Nothing here writes outside review/."""
import math, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dashboard'))
DB = ROOT / 'results' / 'benchmarks.db'
SESSION_GROUPS = {'A': '3dd09b61bd76-fb679a', 'B': '3dd09b61bd76-0077ae'}
SIZES = [100, 500, 1000, 5000, 10000]


def con():
    return sqlite3.connect(f'file:{DB}?mode=ro', uri=True)


def fit(ns, ts):
    """OLS of log10 T on log10 N (Eq 6), plain arithmetic. Returns (k, r2) or None."""
    n = len(ns)
    if n < 3 or any(t <= 0 for t in ts):
        return None
    xs = [math.log10(v) for v in ns]; ys = [math.log10(v) for v in ts]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    b = my - k * mx
    sse = sum((y - (k * x + b)) ** 2 for x, y in zip(xs, ys))
    sst = sum((y - my) ** 2 for y in ys)
    return k, (1 - sse / sst) if sst else 1.0


def load_series(session):
    """Independent loader: raw scalability/simulate rows of one run group -> the
    series format the selection module accepts through its `series=` argument.
    Duplicate (backend,size) rows keep MAX(id), as the dashboard's _LATEST does."""
    g = SESSION_GROUPS[session]
    c = con()
    rows = c.execute(
        "SELECT framework, backend, network_size, runtime_median_s, runtime_min_s, runtime_max_s,"
        " CASE WHEN runtime_mean_s>0 THEN 100.0*runtime_sd_s/runtime_mean_s ELSE 0 END,"
        " peak_rss_mb, compile_dominated, n_runs, id FROM conditions"
        " WHERE run_group=? AND task='scalability' AND phase='simulate' ORDER BY id", (g,)).fetchall()
    c.close()
    latest = {}
    for r in rows:
        latest[(r[0], r[1], r[2])] = r          # later id overwrites earlier
    series = {}
    for (fw, be, n), r in sorted(latest.items()):
        s = series.setdefault(f'{fw}/{be}', dict(id=f'{fw}/{be}', framework=fw, backend=be,
                                                  compile_dominated=bool(r[8]), points=[]))
        s['points'].append(dict(n=n, t=r[3], tmin=r[4], tmax=r[5], cv=r[6], mem=r[7], runs=r[9]))
    out = []
    for s in series.values():
        s['points'].sort(key=lambda p: p['n'])
        f = fit([p['n'] for p in s['points']], [p['t'] for p in s['points']])
        s['fit'] = dict(k=f[0], r2=f[1]) if f else None
        out.append(s)
    return out
