"""All Chapter-4 inference/scalability/energy/sensitivity numbers for one campaign."""
import sys, json, pathlib, io, contextlib
sys.path.insert(0, "/sessions/rcw-016pwamzgppdna2nbd8kbru6/mnt/MIT College/Last Edition/SNN Simulator Benchmark - Final")
sys.path.insert(0, ".")
from lib import *
db = sys.argv[1]; groups = tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 and sys.argv[2] else None
out = sys.argv[3]
import snnbench.config as C
import snnbench.analyse as A
if groups is None:
    c = sqlite3.connect(db)
    groups = tuple(r[0] for r in c.execute("select distinct run_group from conditions where task in ('inference','scalability')"))
A.CANONICAL_RUN_GROUPS = groups
A._RG_PLACEHOLDERS = ",".join("?" for _ in groups)
tmp = pathlib.Path(out + "_an"); tmp.mkdir(exist_ok=True)
C.RESULTS_DIR = tmp
with contextlib.redirect_stdout(io.StringIO()):
    A.main(pathlib.Path(db))
J = json.load(open(tmp / "analysis.json"))
runs, cond = load(db, groups)
B = backends(cond)
R = {}
R["groups"] = groups
R["n_runs"] = len(runs); R["n_cond"] = len(cond)
R["cpu_null_runs"] = sum(r["cpu"] is None for r in runs)
# inference table
inf = []
for b in B:
    k = (b, "inference", 100, "simulate"); s = (b, "inference", 100, "setup")
    rs = [r for r in runs if r["fb"] == b and r["task"] == "inference" and r["phase"] == "simulate"]
    cpu = [r["cpu"] for r in rs if r["cpu"] is not None]
    inf.append(dict(b=b, med=cond[k]["med"], mn=min(r["t"] for r in rs), mx=max(r["t"] for r in rs),
                    cv=cond[k]["cv"], rss=cond[k]["rss"], cpu=float(np.mean(cpu)) if cpu else None,
                    spikes=cond[k]["spikes"], e=cond[k]["e"], setup=cond[s]["med"], cd=cond[k]["cd"]))
worst = max((x["e"] or 0) for x in inf)
for x in inf: x["eidx"] = 100 * x["e"] / worst if x["e"] is not None else None
R["inference"] = sorted(inf, key=lambda x: x["med"])
R["shapiro"] = J.get("shapiro"); R["levene"] = J.get("levene"); R["anova"] = J.get("anova")
pw = J.get("pairwise", []); R["pairwise"] = pw
R["pairs_separated"] = sum(1 for p in pw if p["p_holm"] < 0.05); R["pairs_total"] = len(pw)
R["pairs_not_separated"] = [(p["a"], p["b"], p["p_holm"]) for p in pw if p["p_holm"] >= 0.05]
# scalability
R["times"] = {b: {n: sc(cond, b, n) for n in SIZES} for b in B}
R["fits"] = {}
for b in B:
    f = J["scaling"][b]; R["fits"][b] = dict(k=f["k"], se=f["se"], r2=f["r2"], ci=f["ci"])
t10 = [sc(cond, b, 10000) for b in B]
R["tau_size"] = {n: ktau([sc(cond, b, n) for b in B], t10) for n in SIZES}
R["ranks"] = {n: {b: 1 + sorted(B, key=lambda x: sc(cond, x, n)).index(b) for b in B} for n in SIZES}
en = [sc(cond, b, 10000, "e") for b in B]
R["tau_metric"] = dict(energy=ktau(en, t10) if None not in en else None,
                       memory=ktau([sc(cond, b, 10000, "rss") for b in B], t10),
                       exponent=ktau([R["fits"][b]["k"] for b in B], t10))
R["mem"] = {b: {n: sc(cond, b, n, "rss") for n in SIZES} for b in B}
R["cpu_sc"] = {b: {n: sc(cond, b, n, "cpu") for n in SIZES} for b in B}
R["energy_sc"] = {b: {n: sc(cond, b, n, "e") for n in SIZES} for b in B}
# RQ2
pairs = [(sc(cond, b, n, "e"), sc(cond, b, n, "eflop")) for b in B for n in SIZES if sc(cond, b, n, "e") is not None]
rr = stats.spearmanr([p[0] for p in pairs], [p[1] for p in pairs])
R["rho_pooled"] = dict(rho=rr.statistic, p=rr.pvalue, n=len(pairs))
R["rho_backend"] = {}
for b in B:
    ns = [n for n in SIZES if sc(cond, b, n, "e") is not None]
    rb, pb = A.spearman_exact([sc(cond, b, n, "e") for n in ns], [sc(cond, b, n, "eflop") for n in ns])
    R["rho_backend"][b] = dict(rho=rb, p=pb, n=len(ns))
# decomposition
m = [r for r in runs if r["cpu"] is not None and r["e"] and r["e"] > 0]
lr = stats.linregress(np.log([r["t"] for r in m]), np.log([r["e"] for r in m]))
u = [r["cpu"] for r in m]
R["decomp"] = dict(n=len(m), slope=lr.slope, r2=lr.rvalue ** 2, u_med=float(np.median(u)),
                   u_q1=float(np.percentile(u, 25)), u_q3=float(np.percentile(u, 75)), u_min=min(u), u_max=max(u))
# TDP / exponent sensitivity at N = 10000 (11 backends)
def E(b, a, tdp):
    rs = [r for r in runs if r["fb"] == b and r["task"] == "scalability" and r["n"] == 10000 and r["phase"] == "simulate" and r["cpu"] is not None]
    return float(np.median([r["t"] * (r["cpu"] / 100) ** a * tdp for r in rs]))
nom = [E(b, 1, 55) for b in B]
sens = []
for tdp in (38.5, 55, 71.5):
    for a in (0.8, 1.0, 1.2):
        v = [E(b, a, tdp) for b in B]
        o0 = sorted(B, key=lambda x: nom[B.index(x)]); o1 = sorted(B, key=lambda x: v[B.index(x)])
        sw = [(o0[i], o0[i+1]) for i in range(len(B)-1) if o1.index(o0[i]) > o1.index(o0[i+1])]
        sens.append(dict(tdp=tdp, a=a, tau=ktau(v, nom), swaps=sw))
R["tdp_exp_sens"] = sens
json.dump(R, open(out, "w"), indent=1, default=float)
print("ok", out, R["n_runs"], "cpu null", R["cpu_null_runs"])
