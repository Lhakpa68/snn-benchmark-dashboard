"""Part 2b: N=1000, Balanced (50/50/50/0), both normalisations, from raw DB rows with plain
arithmetic (own loader + own OLS fit, no selection module). Then compared with the module."""
import csv, math
from _lib import *
import optimization as opt

N = 1000; Q = {'inference': 50, 'memory': 50, 'scalability': 50}
ser = [s for s in load_series('A') if s['framework'] != 'reference' and not s['compile_dominated']]
raw = []
for s in ser:
    p = next(p for p in s['points'] if p['n'] == N)
    base = s['points'][0]['mem']                       # smallest measured size (N=100)
    raw.append(dict(id=s['id'], T=p['t'], M=p['mem'], M100=base, G=p['mem'] - base, k=s['fit']['k'], r2=s['fit']['r2']))
tot = sum(Q.values()); W = {c: v / tot for c, v in Q.items()}
vals = {'inference': [r['T'] for r in raw], 'memory': [r['G'] for r in raw], 'scalability': [r['k'] for r in raw]}
rows = []
for norm in ('minmax', 'share'):
    cost = {}
    for c, v in vals.items():
        x = [math.log(t) for t in v] if (c == 'inference' and norm == 'minmax') else list(v)
        if norm == 'minmax':
            lo, hi = min(x), max(x); cost[c] = [(a - lo) / (hi - lo) if hi > lo else 0.0 for a in x]
        else:
            lo = min(x); y = [a - lo for a in x] if lo < 0 else x
            s_ = sum(y); cost[c] = [a / s_ if s_ > 0 else 0.0 for a in y]
        cost[c + '_x'] = x
    score = [sum(W[c] * cost[c][i] for c in W) for i in range(len(raw))]
    order = sorted(range(len(raw)), key=lambda i: (round(score[i], 12), raw[i]['T'], raw[i]['M'], raw[i]['id']))
    rank = {i: r + 1 for r, i in enumerate(order)}
    mod = {r['id']: r for r in opt.evaluate_four(N, dict(inference=50, memory=50, scalability=50, accuracy=0), normalisation=norm)['rows']}
    for i, r in enumerate(raw):
        row = dict(normalisation=norm, backend=r['id'], runtime_median_s=r['T'], peak_rss_mb_N=r['M'], peak_rss_mb_N100=r['M100'],
                   memory_growth_mb=r['G'], k=r['k'], r2=r['r2'])
        for c in W:
            row[f'{c}_transformed'] = cost[c + '_x'][i]
            row[f'{c}_cost'] = cost[c][i]
            row[f'{c}_weight'] = W[c]
            row[f'{c}_contribution'] = W[c] * cost[c][i]
        row['score'] = score[i]; row['rank'] = rank[i]
        m = mod[r['id']]
        row['module_score'] = m['score']; row['module_rank'] = [x['id'] for x in opt.evaluate_four(N, dict(inference=50, memory=50, scalability=50, accuracy=0), normalisation=norm)['rows']].index(r['id']) + 1
        row['abs_diff'] = abs(m['score'] - score[i])
        rows.append(row)
with open('worked_example_N1000_balanced.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('max |independent - module| =', max(r['abs_diff'] for r in rows), '| rank mismatches =', sum(r['rank'] != r['module_rank'] for r in rows))
for norm in ('minmax', 'share'):
    print(norm, [(r['backend'], round(r['score'], 4), r['rank']) for r in sorted(rows, key=lambda r: r['rank']) if r['normalisation'] == norm][:4])
