"""Recompute the 45 profile-and-size recommendations of the dashboard paper with the
scaling exponents from the 1 s longer-duration check (Paper 2, Section 4.2).

Every input except the scalability exponents is kept as in the main campaign
(session A, 10 ms window). Run from the repository root:

    python review/scalability_with_long_exponents.py

Writes review/scalability_with_long_exponents.json and prints the changed cells.
"""
import sqlite3, math, json, statistics, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "dashboard")); import optimization as opt
DB = os.path.join(ROOT, "results", "benchmarks.db")
LJ = os.path.join(ROOT, "long_duration_output", "long_duration_analysis.json")
OUT = os.path.join(ROOT, "review", "scalability_with_long_exponents.json")
con = sqlite3.connect(DB); SIZES = [100, 500, 1000, 5000, 10000]
pts = {}
for fw, be, n, t, mem, cv, runs, cd in con.execute("select framework, backend, network_size, runtime_median_s, peak_rss_mb, cv_pct, n_runs, compile_dominated from conditions where run_group='3dd09b61bd76-fb679a' and task='scalability' and phase='simulate'"):
    pts.setdefault(f"{fw}/{be}", {"fw": fw, "be": be, "cd": bool(cd), "p": {}})["p"][n] = dict(n=n, t=t, mem=mem, cv=cv, runs=runs)
def ols(ns, ts):
    u = [math.log10(x) for x in ns]; y = [math.log10(x) for x in ts]; ub, yb = statistics.mean(u), statistics.mean(y)
    k = sum((a-ub)*(b-yb) for a, b in zip(u, y)) / sum((a-ub)**2 for a in u)
    res = [b-(yb+k*(a-ub)) for a, b in zip(u, y)]; sst = sum((b-yb)**2 for b in y)
    return k, 1-sum(r*r for r in res)/sst
long = json.load(open(LJ))["long"]
def series(use_long):
    out = []
    for bid, d in sorted(pts.items()):
        ps = [d["p"][n] for n in SIZES]; k, r2 = ols(SIZES, [p["t"] for p in ps])
        if use_long and bid in long: k, r2 = long[bid]["k"], long[bid]["r2"]
        out.append(dict(id=bid, framework=d["fw"], backend=d["be"], compile_dominated=d["cd"] or bid == "brian2/cpp_standalone", points=ps, fit=dict(k=k, r2=r2)))
    return out
# full-budget native MNIST test accuracy (Paper 1, Table 6)
acc = {"nengo/reference": 85.44, "spikingjelly/cpu": 97.46, "snntorch/cpu": 97.24, "nest/threads4": 8.32, "nest/threads2": 8.24, "nest/threads1": 8.50, "brian2/cython": 9.61, "brian2/numpy": 9.61}
tr = [dict(backend_id=b, accuracy_pct=a, train_n=60000, epochs=10, hidden=256) for b, a in acc.items()]
res = {}
for label, use_long in (("10ms", False), ("1s", True)):
    ser = series(use_long); res[label] = {}
    for n in SIZES:
        pr = opt.evaluate_profiles(n, series=ser, training_rows=tr)
        sm = opt.softmax_priorities(pr)
        res[label][n] = dict(winners=pr["winners"], prio={p["key"]: p["priority"] for p in sm["profiles"]})
json.dump(res, open(OUT, "w"), indent=1)
changed = 0
for n in SIZES:
    a, b = res["10ms"][n]["winners"], res["1s"][n]["winners"]
    for prof in (a if isinstance(a, dict) else {}):
        if a[prof] != b.get(prof):
            changed += 1; print(f"N={n:>6} {prof}: {a[prof]} -> {b.get(prof)}")
print(f"{changed} of {len(SIZES) * len(opt.PROFILES)} recommendations changed")
