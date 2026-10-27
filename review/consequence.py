"""Task 2: practical-consequence analysis. Reuses evaluate_four on the existing eligible set (8 backends).
Writes consequence_*.csv and consequence_section.md (assembled into PHASE2.md). Read-only on data."""
import csv, json
from _lib import *
import dashboard_data as data
import optimization as opt

PW = {lab: w for _, lab, w in opt.PROFILES}
cells = json.load(open('verify_cells.json'))
SER = {'A': data.get_scalability_series(), 'B': load_series('B')}      # A = what the dashboard serves
RAW = {s: {(x['id'], p['n']): p for x in load_series(s) for p in x['points']} for s in 'AB'}   # run ranges
ms = lambda v: v * 1000.0
def ev(n, w, ses='A', norm='minmax'):
    r = opt.evaluate_four(n, w, normalisation=norm, series=SER[ses])
    return {x['id']: x for x in r['rows']}, r
def dump(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
sec = ['## 2. Practical-consequence analysis\n',
       'Eligible set: the 8 backends of the dashboard (9 SNN backends minus Brian2 C++ standalone). Median runtimes are the values the selection uses (session A unless stated). Min-max ranges are the smallest and largest of the five runs of that cell and are shown for context only; overlap of ranges describes the runs, not uncertainty in a combined score.\n']

# ---- 2a --------------------------------------------------------------------------------------
fast = PW['Fast SNN']
win = {n: ev(n, fast)[1]['winner']['id'] for n in SIZES}
def reuse(src):
    base = win[src]; rows = []
    for n in SIZES:
        by, _ = ev(n, fast); best = win[n]
        a, b = by[base], by[best]; ra, rb = RAW['A'][(base, n)], RAW['A'][(best, n)]
        rows.append(dict(reused_from_N=src, N=n, reused_backend=base, reused_median_ms=round(ms(a['runtime_s']), 4),
                         reused_run_range_ms=f"{ms(ra['tmin']):.4g} to {ms(ra['tmax']):.4g}",
                         best_backend=best, best_median_ms=round(ms(b['runtime_s']), 4),
                         best_run_range_ms=f"{ms(rb['tmin']):.4g} to {ms(rb['tmax']):.4g}",
                         ratio_reused_over_best=round(a['runtime_s'] / b['runtime_s'], 4),
                         abs_difference_ms=round(ms(a['runtime_s'] - b['runtime_s']), 4),
                         same_backend='yes' if base == best else 'no',
                         run_ranges_overlap='yes' if (ra['tmin'] <= rb['tmax'] and rb['tmin'] <= ra['tmax']) else 'no'))
    return rows
f_rows, r_rows = reuse(100), reuse(10000)
dump('consequence_2a_forward.csv', f_rows); dump('consequence_2a_reverse.csv', r_rows)
sec.append(f"### 2a. Reusing a Fast-SNN choice across sizes (session A)\n\nFast SNN winners: " + ', '.join(f'N={n:,}: {win[n]}' for n in SIZES) + '.\n')
for title, rows in (('Forward: N = 100 winner reused at larger sizes', f_rows), ('Reverse: N = 10,000 winner reused at smaller sizes', r_rows)):
    sec.append(f'**{title}** ({rows[0]["reused_backend"]})\n')
    sec.append('| N | Reused median (ms) | Best at N | Best median (ms) | Ratio reused/best | Difference (ms) | Run ranges overlap |'); sec.append('|---|---|---|---|---|---|---|')
    for r in rows: sec.append(f"| {r['N']:,} | {r['reused_median_ms']:g} ({r['reused_run_range_ms']}) | {r['best_backend']} | {r['best_median_ms']:g} ({r['best_run_range_ms']}) | {r['ratio_reused_over_best']:g} | {r['abs_difference_ms']:g} | {r['run_ranges_overlap']} |")
    sec.append('')

# ---- 2b --------------------------------------------------------------------------------------
b_rows = []
for prof, n in [tuple(c) for c in cells['chg_ses']]:
    w = PW[prof]; a_by, _ = ev(n, w, 'A'); b_by, rb = ev(n, w, 'B')
    ca = rb and next(iter(opt.evaluate_four(n, w, series=SER['A'])['rows']))['id']
    cb = rb['winner']['id']
    acc = w['accuracy'] > 0
    for tag, bid in (('session-A choice', ca), ('session-B choice', cb)):
        x = b_by[bid]
        b_rows.append(dict(profile=prof, N=n, role=tag, backend=bid,
                           B_median_runtime_ms=round(ms(x['runtime_s']), 4), B_peak_rss_mb=round(x['memory_mb'], 2),
                           B_memory_growth_mb=round(x['memory_growth_mb'], 3), B_k=round(x['scaling_k'], 4), B_R2=round(x['scaling_r2'], 3),
                           B_cost_inference=round(x['inference_cost'], 4), B_cost_memory=round(x['memory_cost'], 4), B_cost_scalability=round(x['scalability_cost'], 4),
                           B_cost_accuracy=round(x['accuracy_cost'], 4) if acc else 'not in profile',
                           accuracy_pct=round(x['accuracy_pct'], 2) if acc else 'not in profile',
                           B_score=round(x['score'], 5), A_score=round(a_by[bid]['score'], 5),
                           B_run_range_ms=f"{ms(RAW['B'][(bid, n)]['tmin']):.4g} to {ms(RAW['B'][(bid, n)]['tmax']):.4g}"))
dump('consequence_2b_session.csv', b_rows)
sec.append('### 2b. Session transfer (cells whose choice differs between sessions)\n')
sec.append('Both backends are scored on session-B measurements. Accuracy comes from the training experiment and is **shared** by both sessions (accuracy-weighted profiles marked *). Score = weighted normalised cost, lower is better; a score difference is a distance under the stated weights, not a significance test.\n')
sec.append('| Profile | N | Backend | Role | B runtime (ms) | B peak RSS (MB) | B growth (MB) | k (R²) | B score | A score |'); sec.append('|---|---|---|---|---|---|---|---|---|---|')
for r in b_rows: sec.append(f"| {r['profile']} | {r['N']:,} | {r['backend']} | {r['role']} | {r['B_median_runtime_ms']:g} | {r['B_peak_rss_mb']:g} | {r['B_memory_growth_mb']:g} | {r['B_k']:g} ({r['B_R2']:g}) | {r['B_score']:g} | {r['A_score']:g} |")
sec.append('\nSide by side (session B): which backend is lower on each raw criterion, and the score difference (A-choice minus B-choice; negative would favour the A-choice).\n')
sec.append('| Profile | N | Faster | Lower growth | Lower k | Score diff (A-choice − B-choice) |'); sec.append('|---|---|---|---|---|---|')
for i in range(0, len(b_rows), 2):
    a, b = b_rows[i], b_rows[i + 1]
    cmp = lambda k, lo=True: ('equal' if a[k] == b[k] else (a['backend'] if (a[k] < b[k]) == lo else b['backend']))
    sec.append(f"| {a['profile']} | {a['N']:,} | {cmp('B_median_runtime_ms')} | {cmp('B_memory_growth_mb')} | {cmp('B_k')} | {a['B_score'] - b['B_score']:+.5f} |")
sec.append('')

# ---- 2c --------------------------------------------------------------------------------------
c_rows = []
def add_cell(kind, prof, n):
    w = PW[prof]; wns = dict(w, scalability=0)
    m_by, mres = ev(n, w); s_by, sres = ev(n, w, norm='share')
    ns_ok = w['scalability'] > 0 and sum(wns.values()) > 0
    ns_by, nres = ev(n, wns) if ns_ok else ({}, None); nsh_by, _ = ev(n, wns, norm='share') if ns_ok else ({}, None)
    cand = [mres['winner']['id']]
    other = sres['winner']['id'] if kind == 'normalisation' else nres['winner']['id']
    if other not in cand: cand.append(other)
    tied = ''
    if kind == 'scalability removal':
        sc = {r['id']: r['score'] for r in nres['rows']}; best = min(sc.values())
        tied = '|'.join(i for i, v in sc.items() if abs(v - best) <= 1e-9)
    for bid in cand:
        x = m_by[bid]
        c_rows.append(dict(change=kind, profile=prof, N=n, backend=bid,
                           role='min-max winner' if bid == mres['winner']['id'] else ('share winner' if kind == 'normalisation' else 'winner without scalability (tie-break pick)'),
                           runtime_ms=round(ms(x['runtime_s']), 4), memory_growth_mb=round(x['memory_growth_mb'], 3),
                           k=round(x['scaling_k'], 4), R2=round(x['scaling_r2'], 3),
                           accuracy_pct=round(x['accuracy_pct'], 2) if w['accuracy'] > 0 else 'not in profile',
                           score_minmax=round(x['score'], 5), score_share=round(s_by[bid]['score'], 5),
                           score_minmax_without_scalability=round(ns_by[bid]['score'], 5) if ns_ok else 'n/a',
                           score_share_without_scalability=round(nsh_by[bid]['score'], 5) if ns_ok else 'n/a',
                           tied_set_without_scalability=tied if tied.count('|') else ''))
for c in cells['chg_norm']: add_cell('normalisation', *c)
for c in cells['chg_ns']: add_cell('scalability removal', *c)
dump('consequence_2c_changes.csv', c_rows)
sec.append('### 2c. Cells that change with normalisation or with scalability removed\n')
sec.append('Raw values side by side and the score under each setting. Scores of different normalisations are on different scales and are not comparable in magnitude; only the ordering within a column is meaningful. Accuracy is shared across sessions (all values here are session A).\n')
sec.append('| Change | Profile | N | Backend | Role | Runtime (ms) | Growth (MB) | k | Score min-max | Score share | Score min-max, no scal. | Tied set without scalability |'); sec.append('|---|---|---|---|---|---|---|---|---|---|---|---|')
for r in c_rows: sec.append(f"| {r['change']} | {r['profile']} | {r['N']:,} | {r['backend']} | {r['role']} | {r['runtime_ms']:g} | {r['memory_growth_mb']:g} | {r['k']:g} | {r['score_minmax']:g} | {r['score_share']:g} | {r['score_minmax_without_scalability']} | {r['tied_set_without_scalability'] or '-'} |")
open('consequence_section.md', 'w').write('\n'.join(sec) + '\n')
print('\n'.join(sec))
