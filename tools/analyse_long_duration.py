"""Analyse the 1 s long-duration scalability check (journal revision, Paper 1).
Compares it with the 10 ms session-A sweep in results/benchmarks.db: medians, fitted exponents (OLS on
log10 T vs log10 N), runtime rank at each size and Kendall's tau-b (100 vs 10,000 neurons; each size vs
10,000). Standard library only. Usage:  python tools/analyse_long_duration.py [long_duration_output/benchmarks.db]"""
import sqlite3, sys, os, math, itertools, statistics, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LONG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "long_duration_output", "benchmarks.db")
SHORT, SESSION_A = os.path.join(ROOT, "results", "benchmarks.db"), "3dd09b61bd76-fb679a"
SIZES = [100, 500, 1000, 5000, 10000]
def tau_b(x, y):
    nc = nd = tx = ty = 0
    for i, j in itertools.combinations(range(len(x)), 2):
        dx, dy = x[i] - x[j], y[i] - y[j]
        if dx == 0 and dy == 0: continue
        if dx == 0: tx += 1
        elif dy == 0: ty += 1
        elif dx * dy > 0: nc += 1
        else: nd += 1
    return (nc - nd) / math.sqrt((nc + nd + tx) * (nc + nd + ty))
def ols(ns, ts):
    u = [math.log10(n) for n in ns]; y = [math.log10(t) for t in ts]
    ub, yb = statistics.mean(u), statistics.mean(y)
    sxx = sum((a - ub) ** 2 for a in u); k = sum((a - ub) * (b - yb) for a, b in zip(u, y)) / sxx
    res = [b - (yb + k * (a - ub)) for a, b in zip(u, y)]
    sst = sum((b - yb) ** 2 for b in y); r2 = 1 - sum(r * r for r in res) / sst if sst else float("nan")
    se = math.sqrt(sum(r * r for r in res) / (len(u) - 2) / sxx)
    return k, se, r2
def load(db, group=None):
    con = sqlite3.connect(db); q = ("select framework, backend, network_size, runtime_median_s from conditions "
          "where task='scalability' and phase='simulate' and framework!='reference'")
    args = ()
    if group: q += " and run_group=?"; args = (group,)
    m = {}
    for fw, be, n, t in con.execute(q, args): m[(f"{fw}/{be}", n)] = t
    runs = dict(con.execute("select framework||'/'||backend||'@'||network_size, n_runs from conditions "
                            "where task='scalability' and phase='simulate'" + (" and run_group=?" if group else ""), args).fetchall())
    return m, runs
long_m, long_runs = load(LONG); short_m, _ = load(SHORT, SESSION_A)
backends = sorted({b for b, n in long_m if all((b, s) in long_m for s in SIZES)})
out = {"backends": backends, "sizes": SIZES, "long": {}, "short": {}, "n_runs": long_runs}
for label, m in (("short", short_m), ("long", long_m)):
    for b in backends:
        k, se, r2 = ols(SIZES, [m[(b, s)] for s in SIZES])
        out[label][b] = dict(medians=[m[(b, s)] for s in SIZES], k=k, se=se, r2=r2)
    ranks = {}
    for s in SIZES:
        order = sorted(backends, key=lambda b: m[(b, s)]); ranks[s] = {b: order.index(b) + 1 for b in backends}
    out[label + "_ranks"] = ranks
    out[label + "_tau_vs_10000"] = {s: tau_b([m[(b, s)] for b in backends], [m[(b, 10000)] for b in backends]) for s in SIZES[:-1]}
    nocpp = [b for b in backends if b != "brian2/cpp_standalone"]
    out[label + "_tau_vs_10000_no_cpp"] = {s: tau_b([m[(b, s)] for b in nocpp], [m[(b, 10000)] for b in nocpp]) for s in SIZES[:-1]}
out["tau_long_vs_short_at_size"] = {s: tau_b([short_m[(b, s)] for b in backends], [long_m[(b, s)] for b in backends]) for s in SIZES}
print(f"Backends: {len(backends)}  (long-duration db: {LONG})\n")
print(f"{'Backend':24s} {'k 10ms':>7s} {'k 1s':>7s} {'R2 1s':>6s}   " + "   ".join(f"T1s@{s}" for s in SIZES))
for b in backends:
    L, S = out["long"][b], out["short"][b]
    print(f"{b:24s} {S['k']:7.3f} {L['k']:7.3f} {L['r2']:6.3f}   " + "  ".join(f"{t:8.4f}" for t in L["medians"]))
for lab in ("short", "long"):
    print(f"\n{lab:5s} rank 100 -> 10000:", {b: (out[lab+'_ranks'][100][b], out[lab+'_ranks'][10000][b]) for b in backends})
    print(f"{lab:5s} tau vs 10000:", {s: round(v, 3) for s, v in out[lab+'_tau_vs_10000'].items()},
          " without C++:", {s: round(v, 3) for s, v in out[lab+'_tau_vs_10000_no_cpp'].items()})
print("\ntau(10 ms ordering, 1 s ordering) at each size:", {s: round(v, 3) for s, v in out["tau_long_vs_short_at_size"].items()})
json.dump(out, open(os.path.join(os.path.dirname(LONG), "long_duration_analysis.json"), "w"), indent=1, default=str)
