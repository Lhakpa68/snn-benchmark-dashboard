"""Part 3: sensitivity evaluation on EXISTING data (9 profiles x 5 sizes).
Calls the existing selection functions; adds no new algorithm. Writes only into review/."""
import csv, json, math
from _lib import *
import dashboard_data as data
import optimization as opt

TOL = 1e-9
W_ALL = {c: 0 for c in opt.CRITERIA}

# ---- D. which criteria exist in both sessions ------------------------------------------------
SER = {'A': load_series('A'), 'B': load_series('B')}
mod_default = data.get_scalability_series()
chk = []
for s in mod_default:                       # my independent loader must equal the dashboard's series (session A)
    m = next(x for x in SER['A'] if x['id'] == s['id'])
    for p, q_ in zip(s['points'], m['points']):
        assert p['n'] == q_['n'] and p['t'] == q_['t'] and p['mem'] == q_['mem'], s['id']
    assert abs(s['fit']['k'] - m['fit']['k']) < 1e-12 and abs(s['fit']['r2'] - m['fit']['r2']) < 1e-12, s['id']
lines = ['SESSION CRITERIA CHECK (scalability/simulate rows; run groups ' + ', '.join(f'{k}={v}' for k, v in SESSION_GROUPS.items()) + ')',
         'Loader check: independent session-A loader + own OLS fit == dashboard get_scalability_series() (medians, memory, k, R2): OK']
for ses in 'AB':
    ids = [s['id'] for s in SER[ses]]
    lines.append(f'Session {ses}: {len(ids)} series; runtime median + peak RSS present at all 5 sizes for: ' +
                 str(sum(all(any(p["n"] == n and p["t"] and p["mem"] for p in s["points"]) for n in SIZES) for s in SER[ses])) +
                 ' ; k refittable (>=3 sizes) for: ' + str(sum(s['fit'] is not None for s in SER[ses])))
rel_t = []; rel_g = []
for sa in SER['A']:
    sb = next(x for x in SER['B'] if x['id'] == sa['id'])
    for pa, pb in zip(sa['points'], sb['points']):
        rel_t.append((abs(pb['t'] - pa['t']) / pa['t'] * 100, sa['id'], pa['n']))
    ga = [p['mem'] - sa['points'][0]['mem'] for p in sa['points']]; gb = [p['mem'] - sb['points'][0]['mem'] for p in sb['points']]
    rel_g += [(abs(b - a), sa['id'], p['n']) for a, b, p in zip(ga, gb, sa['points'])]
lines.append(f'A vs B runtime median: max relative difference {max(rel_t)[0]:.1f}% at {max(rel_t)[1:]} ; median {sorted(x[0] for x in rel_t)[len(rel_t)//2]:.1f}%')
lines.append(f'A vs B memory growth: max absolute difference {max(rel_g)[0]:.1f} MB at {max(rel_g)[1:]}')
lines.append('Accuracy: measured in the training groups only (one run per condition, shared by both sessions) -> HELD CONSTANT across sessions; accuracy-bearing profiles are re-scored per session only for runtime/memory/scalability.')
lines.append('Not available per session: nothing else is held constant; runtime, peak RSS and k (refit from that session\'s five sizes) all exist in both.')
open('sessions_criteria_check.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

# ---- helpers -----------------------------------------------------------------------------------
def ranges(session):
    return {(s['id'], p['n']): p for s in SER[session] for p in s['points']}
RNG = {k: ranges(k) for k in 'AB'}

def excluded_list(series, rows):
    got = {r['id'] for r in rows}; out = []
    for s in series:
        if s['id'] in got: continue
        why = 'control (reference framework)' if s['framework'] == 'reference' else \
              'compile-dominated' if s.get('compile_dominated') else 'missing required criterion / invalid / over cap'
        out.append(f"{s['id']} ({why})")
    return out

def detail_row(profile, n, session, approach, norm, weights, res, series, extra=None):
    rows = res['rows']
    active = res['active']
    base = dict(profile=profile, size=n, session=session, approach=approach, normalisation=norm,
                active_criteria='+'.join(active), weights=json.dumps({k: round(v, 4) for k, v in res['weights'].items() if v > 0}),
                eligible='|'.join(r['id'] for r in rows), excluded='|'.join(excluded_list(series, rows)))
    if approach.startswith('weighted'):
        key = lambda r: r['score']; order = sorted(rows, key=lambda r: (round(r['score'], 12), r['runtime_s'], r['memory_mb'], r['id']))
    elif approach == 'rank_sum':
        key = lambda r: r['rank_sum']; order = sorted(rows, key=lambda r: (r['rank_sum'], r['id']))
    else:
        key = lambda r: r['runtime_s']; order = sorted(rows, key=lambda r: (r['runtime_s'], r['id']))
    best = key(order[0])
    tied = [r['id'] for r in order if abs(key(r) - best) <= TOL * max(1.0, abs(best))]
    nxt = next((r for r in order if r['id'] not in tied), None)
    pr = RNG[session]
    w = order[0]; ru = nxt
    overlap = ''
    if ru is not None and len(tied) == 1:
        a, b = pr[(w['id'], n)], pr[(ru['id'], n)]
        overlap = 'yes' if (a['tmin'] <= b['tmax'] and b['tmin'] <= a['tmax']) else 'no'
    row = dict(base, winner='|'.join(tied) if len(tied) > 1 else tied[0], tied_set_size=len(tied),
               module_tiebreak_pick=order[0]['id'],
               runner_up=ru['id'] if ru else '', winner_value=round(best, 6), runner_up_value=round(key(ru), 6) if ru else '',
               margin=round(key(ru) - best, 6) if ru else '',
               margin_rel_pct=round((key(ru) - best) / best * 100, 2) if (ru and best) else '',
               winner_runtime_cv_pct=round(pr[(w['id'], n)]['cv'], 2), runner_up_runtime_cv_pct=round(pr[(ru['id'], n)]['cv'], 2) if ru else '',
               runtime_min_max_ranges_overlap=overlap,
               memory_all_zero_growth='yes' if all(r['memory_growth_mb'] == 0 for r in rows) else 'no',
               memory_degenerate_flag='YES: memory-weighted profile at N=100' if (all(r['memory_growth_mb'] == 0 for r in rows) and res['weights']['memory'] > 0) else '',
               raw=json.dumps({r['id']: dict(runtime_s=r['runtime_s'], mem_growth_mb=r['memory_growth_mb'], k=round(r['scaling_k'], 5), r2=round(r['scaling_r2'], 3), acc=r['accuracy_pct']) for r in rows}),
               normalised=json.dumps({r['id']: {c: round(r[f'{c}_cost'], 5) for c in active} for r in rows}),
               contributions=json.dumps({r['id']: {c: round(v, 5) for c, v in r['contributions'].items() if v} for r in rows}) if approach.startswith('weighted') else '',
               rank_sums=json.dumps({r['id']: r['rank_sum'] for r in rows}) if approach == 'rank_sum' else '')
    row['_tied'] = frozenset(tied)
    return row

# ---- main loop ---------------------------------------------------------------------------------
detail = []; summary = []
for key, label, wts in opt.PROFILES:
    for n in SIZES:
        picks = {}
        def run(session, approach, norm, weights):
            series = mod_default if session == 'A' else SER['B']
            res = opt.evaluate_four(n, weights, normalisation=norm, series=series)
            if not res['ok']: return None
            r = detail_row(label, n, session, approach, norm, weights, res, series)
            detail.append(r); return r
        picks['w_mm'] = run('A', 'weighted', 'minmax', wts)
        picks['w_sh'] = run('A', 'weighted', 'share', wts)
        picks['rank'] = run('A', 'rank_sum', 'minmax', wts)
        picks['rt'] = run('A', 'runtime_only', 'minmax', wts)
        picks['w_B'] = run('B', 'weighted', 'minmax', wts)
        noscal = dict(wts, scalability=0)
        if wts['scalability'] > 0 and sum(noscal.values()) > 0:
            picks['ns_mm'] = run('A', 'weighted_without_scalability', 'minmax', noscal)
            picks['ns_sh'] = run('A', 'weighted_without_scalability', 'share', noscal)
        def chg(a, b):
            if a is None or b is None: return 'not assessable'
            return 'no' if a['_tied'] == b['_tied'] else 'yes'
        base = picks['w_mm']
        summary.append(dict(
            profile=label, size=n,
            weighted_pick=base['winner'], runtime_only_pick=picks['rt']['winner'], rank_sum_pick=picks['rank']['winner'],
            changes_under_share_normalisation=chg(base, picks['w_sh']), share_pick=picks['w_sh']['winner'],
            changes_without_scalability=chg(base, picks.get('ns_mm')),
            without_scalability_pick=picks['ns_mm']['winner'] if picks.get('ns_mm') else '',
            without_scalability_share_pick=picks['ns_sh']['winner'] if picks.get('ns_sh') else '',
            changes_by_session=chg(base, picks['w_B']), session_B_pick=picks['w_B']['winner'],
            weighted_vs_runtime_only='differ' if base['_tied'] != picks['rt']['_tied'] else 'same',
            weighted_vs_rank_sum='differ' if base['_tied'] != picks['rank']['_tied'] else 'same',
            margin_to_runner_up=base['margin'], margin_rel_pct=base['margin_rel_pct'],
            runtime_ranges_overlap_winner_vs_runner_up=base['runtime_min_max_ranges_overlap'],
            memory_degenerate_flag=base['memory_degenerate_flag'],
            tied_set_size=base['tied_set_size']))
for r in detail: r.pop('_tied')
def dump(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
dump('sensitivity_detail.csv', detail); dump('sensitivity_summary.csv', summary)
print(f'\ndetail rows {len(detail)}, summary rows {len(summary)}')
for col in ('changes_under_share_normalisation', 'changes_without_scalability', 'changes_by_session', 'weighted_vs_runtime_only', 'weighted_vs_rank_sum'):
    from collections import Counter
    print(col, dict(Counter(r[col] for r in summary)))
