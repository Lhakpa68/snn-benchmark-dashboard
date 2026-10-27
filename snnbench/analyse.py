"""Statistics and result tables, computed from the stored per-run data.

Every number Chapter 4 reports comes out of this file. It writes:

  results/ANALYSIS.md      the tables, in the order the chapter uses them
  results/analysis.json    the same numbers, machine-readable

Because `runs` stores every individual measurement, the full plan in Chapter 3
is executable here: normality and variance-homogeneity checks run on the raw
values rather than being skipped for want of them.
"""
from __future__ import annotations
import json, math, sqlite3, itertools, pathlib
import numpy as np

try:
    from scipy import stats as st
except Exception:
    st = None

import snnbench.config as C

ALPHA = 0.05

# The database accumulates every campaign ever run against it, so reporting
# on "every row in the table" would silently mix smoke tests, restarted runs
# and superseded campaigns into the numbers. Every query below is therefore
# restricted to the explicit run_groups of ONE campaign.
#
# That campaign is the complete run of 21-27 September 2026 on the LT68
# laptop (Intel i9-14900HX, 32 logical cores, WSL2). It is the only campaign
# the thesis reports, and it is self-contained: it measured inference and
# scalability twice, trained every training-capable backend at two budgets,
# and measured processor utilisation, the energy proxy and peak memory on
# every row, training included. Earlier campaigns remain in their own
# archived databases for provenance and are not reported.
#
# Session A is canonical for inference and scalability; session B is the
# same protocol run again immediately afterwards and is used only to measure
# how far a repeat measurement agrees with the first.
CANONICAL_RUN_GROUPS = (
    "3dd09b61bd76-fb679a",          # session A
)
REPLICATION_RUN_GROUPS = (
    "3dd09b61bd76-0077ae",          # session B, the repeat
)

# Experiment 2 at the budget Chapter 4 reports: 60,000 train / 10,000 test /
# 10 epochs / hidden 256, one group per backend.
TRAINING_RUN_GROUPS = (
    "3dd09b61bd76-1be46c",   # nengo/reference
    "3dd09b61bd76-240c5e",   # spikingjelly/cpu
    "3dd09b61bd76-a41901",   # snntorch/cpu
    "3dd09b61bd76-86dc75",   # nest/threads4
    "3dd09b61bd76-3a9ac5",   # nest/threads2
    "3dd09b61bd76-b2cf40",   # nest/threads1
    "3dd09b61bd76-0bee0e",   # brian2/cython
    "3dd09b61bd76-077773",   # brian2/numpy
    "3dd09b61bd76-14a25b",   # brian2/cpp_standalone
)

# The cheaper budget, 6,000 train / 1,000 test / 3 epochs / hidden 256. It
# gives the training ordering a repeat measurement, which the full budget
# cannot afford, and cross-checks the utilisation figures: a backend should
# report much the same utilisation at both budgets even though the durations
# differ by an order of magnitude.
TRAINING_REPEAT_RUN_GROUPS = (
    "3dd09b61bd76-01ec46",   # nengo/reference
    "3dd09b61bd76-fedb55",   # spikingjelly/cpu
    "3dd09b61bd76-4ee008",   # snntorch/cpu
    "3dd09b61bd76-e6f7fa",   # nest/threads4
    "3dd09b61bd76-880471",   # nest/threads2
    "3dd09b61bd76-d7ed67",   # nest/threads1
    "3dd09b61bd76-11bfd9",   # brian2/cython
    "3dd09b61bd76-bc3e49",   # brian2/numpy
    "3dd09b61bd76-411615",   # brian2/cpp_standalone
)

# The width the Candidature Confirmation Report proposed, hidden 500, run as
# an optional tail after the reported campaign finished. It covers three of
# the nine backends and was stopped by request before the rest; it is
# reported as a partial check, never as part of the main comparison.
TRAINING_W500_RUN_GROUPS = (
    "3dd09b61bd76-cdf269",   # nengo/reference
    "3dd09b61bd76-28927c",   # spikingjelly/cpu
    "3dd09b61bd76-951336",   # snntorch/cpu
)
_TR_PLACEHOLDERS = ",".join("?" for _ in TRAINING_RUN_GROUPS)
_RG_PLACEHOLDERS = ",".join("?" for _ in CANONICAL_RUN_GROUPS)

def _mean_or_none(values):
    """Mean over the values that exist, or None if none do.

    Utilisation and the energy proxy derived from it are NULL for any run whose
    measured region was too short for the CPU clock to resolve. Averaging over
    them would either raise or silently treat an absence as a zero; both are
    worse than reporting that the quantity was not measured, which is the rule
    the rest of this study follows."""
    vals = [v for v in values if v is not None]
    return float(np.mean(vals)) if vals else None


def _median_or_none(values):
    vals = [v for v in values if v is not None]
    return float(np.median(vals)) if vals else None


def _fmt(value, spec):
    """Format a number, or an em dash when the quantity was not measured."""
    return format(value, spec) if value is not None else "-"




# --------------------------------------------------------------------------- helpers
def _fetch(con, sql, *args):
    cur = con.execute(sql, args)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _runs(con, task, phase="simulate"):
    return _fetch(con,
                  f"SELECT * FROM runs WHERE task=? AND phase=? "
                  f"AND run_group IN ({_RG_PLACEHOLDERS}) ORDER BY framework,"
                  " backend, network_size, run_index",
                  task, phase, *CANONICAL_RUN_GROUPS)


def _by(rows, *keys):
    out = {}
    for r in rows:
        out.setdefault(tuple(r[k] for k in keys), []).append(r)
    return out


def fit_exponent(sizes, times):
    """Least-squares fit of log10(runtime) on log10(N). Returns the slope with
    its standard error, 95% interval and coefficient of determination."""
    x, y = np.log10(np.asarray(sizes, float)), np.log10(np.asarray(times, float))
    n = len(x)
    if n < 3:
        return None
    if st is not None:
        r = st.linregress(x, y)
        tcrit = st.t.ppf(0.975, n - 2)
        return dict(k=r.slope, se=r.stderr, r2=r.rvalue ** 2,
                    ci=(r.slope - tcrit * r.stderr, r.slope + tcrit * r.stderr), n=n)
    A = np.vstack([x, np.ones(n)]).T
    slope, icpt = np.linalg.lstsq(A, y, rcond=None)[0]
    resid = y - (slope * x + icpt)
    se = math.sqrt((resid @ resid) / (n - 2) / ((x - x.mean()) @ (x - x.mean())))
    r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    return dict(k=slope, se=se, r2=r2, ci=(slope - 3.182 * se, slope + 3.182 * se), n=n)


def welch_anova(groups):
    """Welch's one-way ANOVA. Chosen over the classical test because equal
    variances are untenable here on structural grounds, not merely unobserved."""
    means = np.array([np.mean(g) for g in groups])
    vars_ = np.array([np.var(g, ddof=1) for g in groups])
    ns = np.array([len(g) for g in groups], float)
    w = ns / vars_
    mw = (w * means).sum() / w.sum()
    k = len(groups)
    lam = (((1 - w / w.sum()) ** 2) / (ns - 1)).sum()
    F = ((w * (means - mw) ** 2).sum() / (k - 1)) / (1 + 2 * (k - 2) / (k ** 2 - 1) * lam)
    df2 = (k ** 2 - 1) / (3 * lam)
    p = float(st.f.sf(F, k - 1, df2)) if st is not None else float("nan")
    grand = np.concatenate(groups)
    ssb = (ns * (means - grand.mean()) ** 2).sum()
    ssw = ((ns - 1) * vars_).sum()
    return dict(F=float(F), df1=k - 1, df2=float(df2), p=p,
                eta_sq=float(ssb / (ssb + ssw)))


def holm(pvals):
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvals[idx])
        adj[idx] = min(1.0, running)
    return adj


def cohens_d(a, b):
    na, nb = len(a), len(b)
    s = math.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1))
                  / (na + nb - 2))
    return float((np.mean(a) - np.mean(b)) / s) if s else float("nan")


def spearman_exact(x, y):
    """Exact two-sided permutation p-value. Feasible for the five-point sweeps
    used here (120 orderings), where the asymptotic approximation is unreliable."""
    if st is None:
        return float("nan"), float("nan")
    rho = st.spearmanr(x, y).statistic
    n = len(x)
    if n > 8:
        return float(rho), float(st.spearmanr(x, y).pvalue)
    hits = tot = 0
    for perm in itertools.permutations(range(n)):
        r = st.spearmanr([x[i] for i in perm], y).statistic
        tot += 1
        hits += abs(r) >= abs(rho) - 1e-12
    return float(rho), hits / tot


# --------------------------------------------------------------------------- report
def main(db_path: pathlib.Path = None):
    db_path = db_path or C.DB_PATH
    con = sqlite3.connect(db_path)
    L, J = [], {}

    def P(s=""):
        L.append(s)

    # Report the measurement machine from a canonical run_group specifically
    # (most recent of the two, i.e. the one that measured everything but
    # brian2), not just "whatever meta row is newest" -- a stray smoke test
    # run after this one would otherwise silently retitle the whole report.
    meta = _fetch(con, f"SELECT * FROM meta WHERE run_group IN"
                       f" ({_RG_PLACEHOLDERS}) ORDER BY id DESC LIMIT 1",
                  *CANONICAL_RUN_GROUPS)
    mach = json.loads(meta[0]["machine_json"]) if meta else {}
    pkgs = json.loads(meta[0]["packages_json"]) if meta else {}
    J["machine"], J["packages"] = mach, pkgs

    P("# Analysis: every number Chapter 4 is written from")
    P()
    P(f"Generated from `{db_path.name}`. Single machine, CPU only.")
    P()
    P("## Measurement machine")
    P()
    P("| Property | Value |")
    P("|---|---|")
    for k in ("hostname", "os", "arch", "cpu", "logical_cores", "ram_gb",
              "python", "wsl", "accelerator"):
        if k in mach:
            P(f"| {k} | {mach[k]} |")
    P()
    P("## Package versions, captured at run time")
    P()
    P("| Package | Version |")
    P("|---|---|")
    for k, v in pkgs.items():
        P(f"| {k} | {v} |")
    P()

    # ---- Experiment 1 ----------------------------------------------------
    inf = _runs(con, "inference", "simulate")
    setup = _runs(con, "inference", "setup")
    if inf:
        P("## Experiment 1: inference at N = 100")
        P()
        P("Setup and simulation are timed separately, so a simulator that is slow "
          "to build is distinguishable from one that is slow to run.")
        P()
        P("| Backend | Simulate median (s) | SD | CV (%) | Setup median (s) | "
          "Peak RSS (MB) | CPU (%) | Spikes | Energy (J) |")
        P("|---|---|---|---|---|---|---|---|---|")
        g = _by(inf, "framework", "backend")
        gs = _by(setup, "framework", "backend")
        table = []
        for key in sorted(g, key=lambda k: np.median([r["runtime_s"] for r in g[k]])):
            rs = g[key]
            t = np.array([r["runtime_s"] for r in rs])
            e = [r["energy_j"] for r in rs]
            su = np.median([r["runtime_s"] for r in gs.get(key, [])]) if gs.get(key) else float("nan")
            row = dict(backend=f"{key[0]}/{key[1]}", median=float(np.median(t)),
                       sd=float(t.std(ddof=1)) if len(t) > 1 else 0.0,
                       cv=float(100 * t.std(ddof=1) / t.mean()) if len(t) > 1 else 0.0,
                       setup=float(su),
                       rss=float(max(r["peak_rss_mb"] for r in rs)),
                       cpu=_mean_or_none([r["cpu_pct"] for r in rs]),
                       spikes=int(np.median([r["spikes"] for r in rs])),
                       energy=_median_or_none(e))
            table.append(row)
            P(f"| {row['backend']} | {row['median']:.5f} | {row['sd']:.5f} | "
              f"{row['cv']:.1f} | {row['setup']:.5f} | {row['rss']:.1f} | "
              f"{_fmt(row['cpu'], '.1f')} | {row['spikes']} | {_fmt(row['energy'], '.4f')} |")
        J["inference"] = table
        cpu_only = [r for r in table if "cpp_standalone" not in r["backend"]]
        if len(cpu_only) > 1:
            hi = max(r["median"] for r in cpu_only)
            lo = min(r["median"] for r in cpu_only)
            P()
            P(f"Spread across backends excluding the compile-dominated target: "
              f"**{hi/lo:.2f}x** ({hi:.5f} s / {lo:.5f} s).")
            rssmax = max(r["rss"] for r in table); rssmin = min(r["rss"] for r in table)
            P(f"Peak memory spread: **{rssmax/rssmin:.2f}x** "
              f"({rssmax:.1f} MB / {rssmin:.1f} MB).")
            J["spread_runtime"] = hi / lo
            J["spread_memory"] = rssmax / rssmin
        P()

        # --- distributional checks and inference --------------------------
        P("### Distributional checks on the raw runs")
        P()
        P("Chapter 3 specifies these before any parametric test. They are "
          "computable here because every individual run is stored.")
        P()
        P("| Backend | n | Shapiro-Wilk W | p | normal at 0.05 |")
        P("|---|---|---|---|---|")
        norm = {}
        for key, rs in g.items():
            t = [r["runtime_s"] for r in rs]
            if st is not None and len(t) >= 3:
                W, p = st.shapiro(t)
                norm[key] = p
                P(f"| {key[0]}/{key[1]} | {len(t)} | {W:.4f} | {p:.4f} | "
                  f"{'yes' if p > ALPHA else 'no'} |")
        J["shapiro"] = {f"{k[0]}/{k[1]}": v for k, v in norm.items()}
        P()
        if st is not None and len(g) > 1:
            groups = [[r["runtime_s"] for r in rs] for rs in g.values()]
            W, plev = st.levene(*groups, center="median")
            P(f"Levene's test for homogeneity of variance across "
              f"{len(groups)} backends: W = {W:.2f}, p = {plev:.3e}. "
              f"{'Variances differ' if plev < ALPHA else 'No evidence of unequal variance'}"
              f", so Welch's ANOVA is used.")
            J["levene"] = dict(W=float(W), p=float(plev))
            P()
            a = welch_anova(groups)
            P(f"Welch's one-way ANOVA across all backends: "
              f"F({a['df1']}, {a['df2']:.2f}) = {a['F']:.2f}, p = {a['p']:.3e}, "
              f"eta-squared = {a['eta_sq']:.4f}.")
            J["anova"] = a
            P()
            P("#### Pairwise Welch comparisons, Holm-corrected")
            P()
            keys = list(g)
            pairs, praw = [], []
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    A = [r["runtime_s"] for r in g[keys[i]]]
                    B = [r["runtime_s"] for r in g[keys[j]]]
                    tt = st.ttest_ind(A, B, equal_var=False)
                    pairs.append((f"{keys[i][0]}/{keys[i][1]}",
                                  f"{keys[j][0]}/{keys[j][1]}",
                                  float(tt.statistic), cohens_d(A, B)))
                    praw.append(float(tt.pvalue))
            padj = holm(np.array(praw))
            P("| Pair | t | p (raw) | p (Holm) | Cohen's d | separated |")
            P("|---|---|---|---|---|---|")
            pw = []
            for (a1, b1, tstat, d), pr, pa in sorted(
                    zip(pairs, praw, padj), key=lambda z: z[1]):
                P(f"| {a1} vs {b1} | {tstat:.2f} | {pr:.2e} | {pa:.2e} | "
                  f"{d:.2f} | {'yes' if pa < ALPHA else 'no'} |")
                pw.append(dict(a=a1, b=b1, t=tstat, p_raw=pr, p_holm=float(pa), d=d))
            J["pairwise"] = pw
            ns = [r for r in pw if r["p_holm"] >= ALPHA]
            P()
            if ns:
                P("Pairs the data does not separate: "
                  + "; ".join(f"{r['a']} vs {r['b']} (p = {r['p_holm']:.3f})" for r in ns)
                  + ". Report these as a failure to detect a difference, not as "
                    "evidence of equivalence.")
            else:
                P("Every pair separates at the 0.05 level after Holm correction.")
            P()

    # ---- Experiment 3 ----------------------------------------------------
    sc = _runs(con, "scalability", "simulate")
    if sc:
        P("## Experiment 3: scalability")
        P()
        g = _by(sc, "framework", "backend")
        sizes_all = sorted({r["network_size"] for r in sc})
        hdr = " | ".join(f"N={n}" for n in sizes_all)
        P(f"| Backend | {hdr} | k | SE(k) | 95% CI | R2 |")
        P("|---|" + "---|" * (len(sizes_all) + 4))
        fits = {}
        for key, rs in sorted(g.items()):
            per_n = _by(rs, "network_size")
            xs = [n for n in sizes_all if (n,) in per_n]
            ys = [float(np.median([r["runtime_s"] for r in per_n[(n,)]])) for n in xs]
            f = fit_exponent(xs, ys)
            if not f:
                continue
            fits[key] = dict(f, times=dict(zip(xs, ys)))
            cells = " | ".join(f"{ys[xs.index(n)]:.5f}" if n in xs else "-"
                               for n in sizes_all)
            P(f"| {key[0]}/{key[1]} | {cells} | **{f['k']:.3f}** | {f['se']:.3f} | "
              f"[{f['ci'][0]:.3f}, {f['ci'][1]:.3f}] | {f['r2']:.3f} |")
        J["scaling"] = {f"{k[0]}/{k[1]}": {kk: (list(vv) if isinstance(vv, tuple) else vv)
                                           for kk, vv in v.items()}
                        for k, v in fits.items()}
        P()
        ranked = sorted(fits.items(), key=lambda kv: -kv[1]["k"])
        if len(ranked) >= 2:
            steep, flat = ranked[0], ranked[-1]
            P(f"Steepest: {steep[0][0]}/{steep[0][1]} at k = {steep[1]['k']:.3f}. "
              f"Flattest: {flat[0][0]}/{flat[0][1]} at k = {flat[1]['k']:.3f}.")
            P()
        # ranking reversal
        if len(sizes_all) >= 2 and len(fits) >= 2:
            lo, hi = sizes_all[0], sizes_all[-1]
            def at(key, n):
                return fits[key]["times"].get(n)
            order_lo = sorted([k for k in fits if at(k, lo)], key=lambda k: at(k, lo))
            order_hi = sorted([k for k in fits if at(k, hi)], key=lambda k: at(k, hi))
            P(f"### Ranking at the extremes of the sweep")
            P()
            P(f"| Rank | Fastest at N={lo} | s | Fastest at N={hi} | s |")
            P("|---|---|---|---|---|")
            for i in range(max(len(order_lo), len(order_hi))):
                a = order_lo[i] if i < len(order_lo) else None
                b = order_hi[i] if i < len(order_hi) else None
                P(f"| {i+1} | {a[0]+'/'+a[1] if a else '-'} | "
                  f"{at(a,lo):.5f} | {b[0]+'/'+b[1] if b else '-'} | "
                  f"{at(b,hi):.5f} |" if a and b else f"| {i+1} | - | - | - | - |")
            P()
            reversed_ = order_lo != order_hi
            P(f"The ranking {'reverses' if reversed_ else 'is stable'} across the "
              f"measured range.")
            if reversed_ and order_lo and order_hi:
                a, b = order_lo[0], order_hi[0]
                if a != b:
                    P(f"At N={lo} the fastest backend is {a[0]}/{a[1]}; at N={hi} it is "
                      f"{b[0]}/{b[1]}. The ratio between them moves from "
                      f"{at(a,lo)/at(b,lo):.2f}x to {at(a,hi)/at(b,hi):.2f}x, a swing of "
                      f"{(at(a,hi)/at(b,hi))/(at(a,lo)/at(b,lo)):.1f}x.")
            J["reversal"] = dict(reversed=bool(reversed_),
                                 order_low=[f"{k[0]}/{k[1]}" for k in order_lo],
                                 order_high=[f"{k[0]}/{k[1]}" for k in order_hi])
            P()

        # memory
        P("### Peak process memory (MB)")
        P()
        P(f"| Backend | {hdr} | growth |")
        P("|---|" + "---|" * (len(sizes_all) + 1))
        mem = {}
        for key, rs in sorted(g.items()):
            per_n = _by(rs, "network_size")
            vals = {n: float(max(r["peak_rss_mb"] for r in per_n[(n,)]))
                    for n in sizes_all if (n,) in per_n}
            if not vals:
                continue
            mem[f"{key[0]}/{key[1]}"] = vals
            # A backend may not cover every size (Nengo is killed by the
            # memory limit at the largest N), so the growth ratio spans
            # the sizes that backend actually ran, not the global range.
            have = sorted(vals)
            growth = (vals[have[-1]] / vals[have[0]]
                      if len(have) > 1 and vals[have[0]] else float("nan"))
            cells = " | ".join(f"{vals[n]:.1f}" if n in vals else "-" for n in sizes_all)
            P(f"| {key[0]}/{key[1]} | {cells} | {growth:.2f}x |")
        J["memory"] = mem
        P()

        # energy + RQ2
        P("## Energy proxy and RQ2")
        P()
        P(f"E = t x (u_cpu / 100) x {C.TDP_CPU_W:g} W")
        P()
        P(f"TDP source: {C.TDP_CPU_SOURCE}")
        P()
        P(f"| Backend | {hdr} | (J) |")
        P("|---|" + "---|" * (len(sizes_all) + 1))
        energies = {}
        for key, rs in sorted(g.items()):
            per_n = _by(rs, "network_size")
            vals = {n: _median_or_none([r["energy_j"] for r in per_n[(n,)]])
                    for n in sizes_all if (n,) in per_n}
            vals = {n: v for n, v in vals.items() if v is not None}
            energies[key] = vals
            cells = " | ".join(f"{vals[n]:.3f}" if n in vals else "-" for n in sizes_all)
            P(f"| {key[0]}/{key[1]} | {cells} | |")
        J["energy"] = {f"{k[0]}/{k[1]}": v for k, v in energies.items()}
        P()

        ef_rows = _fetch(con, "SELECT network_size, eflop, spikes FROM conditions"
                              " WHERE task='scalability' AND phase='simulate'"
                              f" AND eflop IS NOT NULL AND run_group IN"
                              f" ({_RG_PLACEHOLDERS})", *CANONICAL_RUN_GROUPS)
        ef = {r["network_size"]: r["eflop"] for r in ef_rows}
        P("### Effective operation count for the model")
        P()
        P("| N | EFLOP | measured output spikes (median across backends) |")
        P("|---|---|---|")
        for n in sizes_all:
            sp = [r["spikes"] for r in ef_rows if r["network_size"] == n]
            P(f"| {n} | {ef.get(n, '-'):,} | {int(np.median(sp)) if sp else '-'} |")
        P()
        P("### Rank agreement between the proxy and EFLOP")
        P()
        P("| Backend | rho | exact p | compile-dominated |")
        P("|---|---|---|---|")
        cd = {(r["framework"], r["backend"]) for r in _fetch(
            con, "SELECT DISTINCT framework, backend FROM conditions "
                 f"WHERE compile_dominated=1 AND run_group IN"
                 f" ({_RG_PLACEHOLDERS})", *CANONICAL_RUN_GROUPS)}
        rq2, pooled_e, pooled_f = [], [], []
        for key, vals in sorted(energies.items()):
            ns = [n for n in sizes_all if n in vals and n in ef]
            if len(ns) < 3:
                continue
            e = [vals[n] for n in ns]
            f = [ef[n] for n in ns]
            rho, p = spearman_exact(e, f)
            P(f"| {key[0]}/{key[1]} | {rho:.2f} | {p:.4f} | "
              f"{'yes' if key in cd else 'no'} |")
            rq2.append(dict(backend=f"{key[0]}/{key[1]}", rho=rho, p=p,
                            compile_dominated=key in cd))
            if key not in cd:
                pooled_e += e
                pooled_f += f
        J["rq2"] = rq2
        if st is not None and len(pooled_e) >= 4:
            rho = st.spearmanr(pooled_e, pooled_f)
            P()
            P(f"Pooled across compute-bound backends ({len(pooled_e)} runs): "
              f"**rho = {rho.statistic:.3f}**, p = {rho.pvalue:.2e}.")
            J["rq2_pooled"] = dict(rho=float(rho.statistic), p=float(rho.pvalue),
                                   n=len(pooled_e))
        P()

    # ---- Experiment 2 ----------------------------------------------------
    tr = _fetch(con, "SELECT * FROM conditions WHERE task='training' "
                     f"AND run_group IN ({_TR_PLACEHOLDERS})",
                *TRAINING_RUN_GROUPS)
    if tr:
        P("## Experiment 2: training")
        P()
        P("| Simulator / backend | Hidden | s per epoch | Accuracy (%) | Note |")
        P("|---|---|---|---|---|")
        for r in sorted(tr, key=lambda r: r["runtime_median_s"]):
            P(f"| {r['framework']}/{r['backend']} | {r['network_size']} | "
              f"{r['runtime_median_s']:.2f} | "
              f"{r['accuracy_pct']:.2f} | {(r['notes'] or '')[:110]} |")
        J["training"] = tr
        P()
        P(f"Chance accuracy on {C.MNIST_CLASSES} classes is "
          f"{100/C.MNIST_CLASSES:.0f}%. Simulators at or near chance are reporting "
          f"the sample budget, not their learning capability.")
        P()

    out = C.RESULTS_DIR / "ANALYSIS.md"
    out.write_text("\n".join(L), encoding="utf-8")
    (C.RESULTS_DIR / "analysis.json").write_text(
        json.dumps(J, indent=1, default=str), encoding="utf-8")
    print("\n".join(L))
    print(f"\nwrote {out} and analysis.json")
    con.close()
