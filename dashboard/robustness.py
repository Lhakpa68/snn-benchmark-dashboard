"""Tie, stability and robustness evidence for the Optimisation and Robustness pages.

Nothing here changes selection: every number comes from calling the existing
`optimization.evaluate_four` / `evaluate_profiles` (live checks) or from reading the verified
review outputs in robustness_data/ (static evidence). Pure Python, no Flask or Streamlit imports,
so both front ends share it.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import optimization as opt

DATA_DIR = Path(__file__).resolve().parent / 'robustness_data'
SIZES = (100, 500, 1000, 5000, 10000)
TAGS = (('N', 'Normalisation'), ('S', 'Session B'), ('R', 'Scalability removed'), ('T', 'Exact tie'))
EVIDENCE_CAPTION = ('Evaluation added during revision; session B and scalability-removal checks '
                    'computed offline from the stored runs. Accuracy profiles (*) are exploratory.')
MARGIN_NOTE = 'score difference, not a significance test'
NORM_LABEL = {'minmax': 'min–max', 'share': 'share-of-total'}


# ---------------------------------------------------------------- ties (live)
def _tied(rows):
    """Backends whose score equals the winner's at 12 decimals (the sort key the code itself uses)."""
    if not rows:
        return []
    best = round(rows[0]['score'], 12)
    return [r for r in rows if round(r['score'], 12) == best]


def tie_info(result):
    """Tied set for an evaluate_four result. `rows` is already ordered, so the winner is first."""
    if not result.get('ok'):
        return dict(is_tie=False, ids=[], others=[], reason='')
    tied = _tied(result['rows'])
    reason = ''
    if len(tied) > 1:
        a, b = tied[0], tied[1]
        if a['runtime_s'] != b['runtime_s']:
            reason = 'shorter runtime'
        elif a['memory_mb'] != b['memory_mb']:
            reason = 'lower peak memory'
        else:
            reason = 'alphabetical order'
    return dict(is_tie=len(tied) > 1, ids=[r['id'] for r in tied], others=[r['id'] for r in tied[1:]],
                reason=reason, all_tied=len(tied) == len(result['rows']))


def tie_sentence(info):
    if not info['is_tie']:
        return ''
    others = ', '.join(info['others'])
    return f"Tied with {others} — shown first because of {info['reason']} (tie rule)."


# ----------------------------------------------------------- ties (profiles)
def attach_profile_ties(P):
    """Add `ties` and `labels` to an evaluate_profiles result (in the app layer; the optimisation
    module's own return value is not edited). labels[key] is the text shown for each profile's choice."""
    ties, labels = {}, {}
    for pf in P['profiles']:
        key = pf['key']
        scored = [(b, v[key]) for b, v in P['scores'].items() if key in v]
        scored.sort(key=lambda x: x[1]['rank'])
        best = round(scored[0][1]['score'], 12) if scored else None
        ids = [b for b, v in scored if round(v['score'], 12) == best]
        all_tied = bool(scored) and len(ids) == len(scored)
        ties[key] = dict(ids=ids if len(ids) > 1 else [], all_tied=all_tied and len(ids) > 1)
        win = P['winners'].get(key)
        if all_tied and len(ids) > 1:
            labels[key] = f'no difference (all {len(ids)} tied)'
        elif len(ids) > 1:
            labels[key] = ' = '.join(ids) + ' (tied)'
        else:
            labels[key] = win or '—'
    P['ties'], P['labels'] = ties, labels
    return P


# ------------------------------------------------------------- stability (live)
def _outcome(base_ids, other_ids, label):
    b, o = set(base_ids), set(other_ids)
    show = ' = '.join(other_ids)
    if b == o:
        return 'same', f'Same {label}' if len(o) == 1 else f'Same tie {label}'
    if len(o) > 1 and len(b) == 1:
        return 'becomes_tie', f'Becomes a tie {label}: {show}'
    if len(b) > 1 and len(o) == 1:
        return 'resolves', f'The tie is resolved {label}: {show}'
    return 'changes', f'Changes to {show} {label}'


def stability(n, weights, cap, normalisation, base=None):
    """Re-run evaluate_four with (i) the other normalisation and (ii) scalability weight 0.
    Session B is deliberately not part of the live page (the dashboard serves session A only)."""
    base = base or opt.evaluate_four(n, weights, cap, normalisation=normalisation)
    if not base.get('ok'):
        return None
    base_ids = tie_info(base)['ids']
    checks = []
    other = 'share' if normalisation == 'minmax' else 'minmax'
    r = opt.evaluate_four(n, weights, cap, normalisation=other)
    if r.get('ok'):
        st, text = _outcome(base_ids, tie_info(r)['ids'], 'under ' + NORM_LABEL[other])
        checks.append(dict(key='normalisation', status=st, text=text))
    raw = base['raw_weights']
    if raw['scalability'] > 0:
        rest = dict(raw, scalability=0)
        if sum(rest.values()) > 0:
            r = opt.evaluate_four(n, rest, cap, normalisation=normalisation)
            if r.get('ok'):
                st, text = _outcome(base_ids, tie_info(r)['ids'], 'without scalability')
                checks.append(dict(key='scalability', status=st, text=text))
        else:
            checks.append(dict(key='scalability', status='n/a', text='Scalability removal not applicable: scalability is the only criterion'))
    rows = base['rows']
    margin = None
    if len(rows) > 1 and not tie_info(base)['is_tie']:
        margin = dict(value=rows[1]['score'] - rows[0]['score'], runner_up=rows[1]['id'], note=MARGIN_NOTE)
    return dict(checks=checks, margin=margin, note='Session B is not checked live; see the Robustness page.')


def decorate(result, n, weights, cap, normalisation):
    """Attach tie and stability evidence to an evaluate_four result (app layer)."""
    result['tie'] = tie_info(result)
    result['stability'] = stability(n, weights, cap, normalisation, base=result) if result.get('ok') else None
    return result


# --------------------------------------------------------- static evidence
def _read(name):
    with open(DATA_DIR / name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _flt(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _log_axis(ratios, y0=250, y1=30, top=100.0):
    frac = lambda r: math.log10(max(r, 1.0)) / math.log10(top)
    ticks = [dict(v=v, y=round(y0 - (y0 - y1) * frac(v), 1), label=f'{v:g}×') for v in (1, 2, 5, 10, 20, 50, 100)]
    return frac, ticks


def load_robustness():
    """Everything the Robustness page, its exports and the Streamlit tab show. Read, never recomputed."""
    S = _read('sensitivity_summary.csv')
    profiles = list(dict.fromkeys(r['profile'] for r in S))
    cells, grid = [], {p: {} for p in profiles}
    for r in S:
        n = int(r['size'])
        tags = [t for t, flag in (('N', r['changes_under_share_normalisation'] == 'yes'),
                                  ('S', r['changes_by_session'] == 'yes'),
                                  ('R', r['changes_without_scalability'] == 'yes'),
                                  ('T', int(r['tied_set_size']) > 1)) if flag]
        status = 'tie' if 'T' in tags else ('changes' if tags else 'stable')
        members = r['weighted_pick'].split('|')
        cell = dict(profile=r['profile'], size=n, status=status, tags=tags, pick=r['weighted_pick'].replace('|', ' = '),
                    pick_label=(f'all {len(members)} tied' if len(members) > 3 else ' = '.join(members)),
                    share_pick=r['share_pick'], session_b_pick=r['session_B_pick'],
                    without_scalability_pick=r['without_scalability_pick'], margin=_flt(r['margin_to_runner_up']),
                    exploratory=r['profile'].endswith('*'))
        cells.append(cell)
        grid[r['profile']][n] = cell
    stable = sum(c['status'] == 'stable' for c in cells)
    by = lambda t: [c for c in cells if t in c['tags']]
    sj = [r for r in S if r['changes_by_session'] == 'yes' and 'spikingjelly' in r['session_B_pick']]
    causes = [
        dict(tag='S', name='Session B (repeat run)', count=len(by('S')),
             text=(f"Runtime-order flips between the two sessions' medians; {len(sj)} of {len(by('S'))} involve SpikingJelly. "
                   "Runtime, memory growth and k are re-scored on session B; accuracy is shared.")),
        dict(tag='R', name='Scalability removed', count=len(by('R')),
             text=(f"{sum(c['profile'].startswith('Scaling + accuracy') for c in by('R'))} reduce to accuracy-only (Scaling + accuracy*); "
                   f"{sum(c['profile'].startswith('Memory + scaling') for c in by('R'))} become ties (Memory + scaling at N = 100 and 500).")),
        dict(tag='N', name='Normalisation', count=len(by('N')),
             text=(f"At N = 100 ({sum(c['size'] == 100 for c in by('N'))} cells) the change comes from raw runtime entering share-of-total; "
                   f"at N = 5,000 ({sum(c['size'] == 5000 for c in by('N'))} cells) it is a Brian2 NumPy versus Cython trade-off.")),
        dict(tag='T', name='Exact ties', count=len(by('T')),
             text='Low-memory at N = 100 (all eight backends) and N = 500 (snnTorch = Brian2 Cython, both with zero memory growth).'),
    ]
    fwd, rev = _read('consequence_2a_forward.csv'), _read('consequence_2a_reverse.csv')
    frac, ticks = _log_axis([float(r['ratio_reused_over_best']) for r in fwd + rev])
    chart = dict(ticks=ticks, x0=70, x1=640, y0=250, y1=30, bars=[])
    slot = (chart['x1'] - chart['x0']) / len(SIZES)
    for i, (f, r) in enumerate(zip(fwd, rev)):
        for j, (series, row) in enumerate((('fwd', f), ('rev', r))):
            ratio = float(row['ratio_reused_over_best'])
            h = (chart['y0'] - chart['y1']) * frac(ratio)
            x = chart['x0'] + slot * i + slot * (0.14 + 0.36 * j)
            chart['bars'].append(dict(series=series, size=int(row['N']), ratio=ratio, x=round(x, 1), w=round(slot * 0.32, 1),
                                      y=round(chart['y0'] - h, 1), h=round(h, 1),
                                      label=f"{ratio:.3g}×", diff_ms=float(row['abs_difference_ms']),
                                      same=row['same_backend'] == 'yes'))
    chart['slot'] = slot
    chart['labels'] = [dict(x=round(chart['x0'] + slot * (i + 0.5), 1), text=f'{n:,}') for i, n in enumerate(SIZES)]
    wrong = dict(chart=chart, forward=fwd, reverse=rev,
                 forward_backend=fwd[0]['reused_backend'], reverse_backend=rev[0]['reused_backend'])
    return dict(headline=dict(stable=stable, total=len(cells)), profiles=profiles, sizes=SIZES, grid=grid,
                cells=cells, causes=causes, wrong_size=wrong, session=_read('consequence_2b_session.csv'),
                caption=EVIDENCE_CAPTION)


def export_rows():
    """Flat rows (with a `dataset` column) for the CSV export and the all-datasets export."""
    d = load_robustness()
    out = []
    for c in d['cells']:
        out.append(dict(dataset='robustness_grid', profile=c['profile'], size=c['size'], status=c['status'],
                        tags=''.join(c['tags']), weighted_pick=c['pick'], share_pick=c['share_pick'],
                        session_b_pick=c['session_b_pick'], without_scalability_pick=c['without_scalability_pick'],
                        margin=c['margin'] if c['margin'] is not None else ''))
    for name, rows in (('robustness_wrong_size_forward', d['wrong_size']['forward']),
                       ('robustness_wrong_size_reverse', d['wrong_size']['reverse']),
                       ('robustness_session_transfer', d['session'])):
        out += [dict(dataset=name, **r) for r in rows]
    return out


def export_json():
    d = load_robustness()
    return json.dumps(dict(
        caption=d['caption'], headline=d['headline'],
        causes=[dict(tag=c['tag'], name=c['name'], count=c['count'], text=c['text']) for c in d['causes']],
        grid=d['cells'], wrong_size=dict(forward=d['wrong_size']['forward'], reverse=d['wrong_size']['reverse']),
        session_transfer=d['session']), indent=1, ensure_ascii=False)


# ------------------------------------------------- plain-language layer (wording only)
# Nothing below affects scoring: it re-states results that evaluate_four already returned.
FRIENDLY = {'brian2/numpy': 'Brian2 (NumPy)', 'brian2/cython': 'Brian2 (Cython)', 'brian2/cpp_standalone': 'Brian2 (C++ standalone)',
            'nengo/reference': 'Nengo', 'snntorch/cpu': 'snnTorch', 'spikingjelly/cpu': 'SpikingJelly'}
SMALL_MARGIN = 0.01          # descriptive threshold used for the "close call" wording only


def friendly(backend_id):
    if backend_id in FRIENDLY:
        return FRIENDLY[backend_id]
    if backend_id.startswith('nest/threads'):
        k = backend_id[len('nest/threads'):]
        return f"NEST ({k} thread{'' if k == '1' else 's'})"
    return backend_id


# (profile key in optimization.PROFILES, plain-language button label)
PRESET_LABELS = (('fast', 'I need it fast'), ('lowmem', 'I need low memory'), ('speed_mem', 'Fast and low memory'),
                 ('balanced', 'Balanced'), ('accurate', 'Accuracy matters (exploratory)'))


def presets():
    """Preset buttons: each one is an existing reader profile (same weights as Table 6), not a new method."""
    by = {k: (label, w) for k, label, w in opt.PROFILES}
    out = []
    for key, text in PRESET_LABELS:
        label, w = by[key]
        out.append(dict(key=key, label=text, profile=label, weights=dict(w), exploratory=w['accuracy'] > 0))
    return out


GLOSSARY = (
    ('Inference speed', 'Median time the benchmark network takes to run at the chosen size. Lower is better.'),
    ('Memory growth', 'How many MB more peak memory the backend uses at this size than at 100 neurons (peak resident memory). It is zero for every backend at 100 neurons, so memory cannot separate them there.'),
    ('Scalability (exponent k)', 'How quickly runtime grows as the network gets bigger: the slope of a straight-line fit on log–log axes across the five measured sizes. Smaller means slower growth. R² says how well a straight line fits; a low R² means k should be read with caution.'),
    ('Accuracy (exploratory)', 'MNIST test accuracy from a separate training experiment in which each simulator uses its own learning rule. It is not a like-for-like comparison, so any accuracy weight is labelled exploratory.'),
    ('Min–max / share of total', 'Two ways to put the criteria on a common scale. Min–max sets the best eligible backend to 0 and the worst to 1. Share of total divides each value by the sum over eligible backends.'),
    ('Score', 'The weighted sum of the scaled criteria. Lower is better. It is a ranking index for the stated priorities, not a measured quantity.'),
    ('Tie rule', 'If two backends have exactly the same score, the one with the shorter runtime (then lower peak memory, then name) is listed first. Both are equally good under the score.'),
    ('Pareto-efficient', 'No other backend is at least as good on every criterion in use and strictly better on at least one.'),
    ('Priority grid', 'The ranking recomputed for weight combinations in steps of 25 per cent, counting how often each backend wins. It describes sensitivity to the weights and is not a probability.'),
    ('Rank sum', 'A weight-free cross-check: each backend\'s ranks on the criteria in use, added up.'),
)
HOW_TO_READ = ('The answer line gives the best-scoring measured backend for your priorities. '
               'The badge says whether that answer holds when the scaling method or the scalability criterion is changed. '
               'Everything below shows how the score was built.')


ELIGIBLE_IDS = ('brian2/numpy', 'brian2/cython', 'nest/threads1', 'nest/threads2', 'nest/threads4',
                'nengo/reference', 'snntorch/cpu', 'spikingjelly/cpu')


def names():
    """(table id, plain name) pairs for the eligible backends, shown as a one-line key."""
    return [(i, friendly(i)) for i in ELIGIBLE_IDS]


def _plain(text):
    import re
    return re.sub(r'[a-z0-9]+/[a-z0-9_]+', lambda m: friendly(m.group(0)), text)


def answer(result):
    """Answer-first summary of an already-decorated evaluate_four result (tie + stability attached)."""
    if not result.get('ok'):
        return None
    w, tie, st, n = result['winner'], result['tie'], result['stability'] or dict(checks=[], margin=None), result['network_size']
    name = friendly(w['id'])
    notes, level = [], 'holds'
    if tie['is_tie']:
        level = 'tie'
        if tie.get('all_tied'):
            lead = (f"For {n:,} neurons and these priorities, all {len(tie['ids'])} eligible backends have exactly the same score, "
                    "so these priorities cannot separate them.")
        else:
            lead = (f"For {n:,} neurons and these priorities, {name} ties with "
                    + ', '.join(friendly(o) for o in tie['others']) + ': exactly the same score. '
                    f"{name} is listed first because of {tie['reason']}.")
    else:
        lead = f"For {n:,} neurons and these priorities, the best-scoring measured backend is {name}."
    moved = [c for c in st['checks'] if c['status'] in ('changes', 'becomes_tie', 'resolves')]
    if moved and level != 'tie':
        level = 'depends'
    for c in moved:
        notes.append(_plain(c['text']) + '.')
    if not moved and st['checks'] and level == 'holds':
        notes.append('The same answer holds under the other scaling method' +
                     (' and without the scalability criterion' if any(c['key'] == 'scalability' and c['status'] == 'same' for c in st['checks']) else '') + '.')
    close = False
    if st['margin'] and st['margin']['value'] < SMALL_MARGIN:
        close = True
        notes.append(f"Small score margin: {friendly(st['margin']['runner_up'])} is only {st['margin']['value']:.4f} behind ({st['margin']['note']}).")
    if result.get('exploratory'):
        notes.append('Exploratory: the accuracy weight uses a different training task with different learning rules.')
    badge = {'holds': 'Holds under the checks shown' + (' (close call)' if close else ''),
             'depends': 'Depends on a setting', 'tie': 'Tie'}[level]
    return dict(lead=lead, notes=notes, level=level, badge=badge, close=close, winner=name)


# ----------------------------------------------------- reviewer reading path (wording only)
READING_PATH = (
    ('1', 'Ask', 'Which simulator suits my needs?', '/optimization', 'Optimisation',
     'Pick a quick choice (fast, low memory, balanced) and read the one-sentence answer.'),
    ('2', 'Check', 'How far can I trust that answer?', '/robustness', 'Robustness',
     'See which recommendations hold under every check, and what a wrong-size choice costs.'),
    ('3', 'Look', 'Where do the numbers come from?', '/inference', 'Inference, Scalability, Memory, Training',
     'Every score is built from these measured experiments, with run-to-run spread shown.'),
    ('4', 'Know the limits', 'What does this not show?', '/about', 'Methods & limitations',
     'One machine, one workload, five network sizes; accuracy comes from a different task and is exploratory.'),
)


def takeaways():
    """Three computed take-away lines for the Home page. Each re-states a result the dashboard already
    produces (Fast SNN winners, the wrong-size ratios, the robustness count); nothing is added."""
    fast = dict(inference=100, memory=0, scalability=0, accuracy=0)
    r_small, r_large = (opt.evaluate_four(n, fast) for n in (100, 10000))
    a, b = r_small['winner'], r_large['winner']
    gap_ms = (r_large['rows'][1]['runtime_s'] - b['runtime_s']) * 1000
    d = load_robustness()
    fwd, rev = d['wrong_size']['forward'], d['wrong_size']['reverse']
    unstable = d['headline']['total'] - d['headline']['stable']
    return [
        dict(title='No simulator is best everywhere',
             text=(f"The fastest backend at 100 neurons is {friendly(a['id']).split(' (')[0]} (its thread counts are not separated by the tests); "
                   f"at 10,000 neurons {friendly(b['id'])} has the lowest median runtime ({b['runtime_s']:.3f} s), with "
                   f"{friendly(r_large['rows'][1]['id'])} " + ('less than 1 ms behind.' if gap_ms < 1 else f'{gap_ms:.1f} ms behind.'))),
        dict(title='Choosing at the wrong size has a cost',
             text=(f"Reusing the 100-neuron pick at 10,000 neurons is {float(fwd[-1]['ratio_reused_over_best']):.2f}× slower than the best; "
                   f"reusing the 10,000-neuron pick at 100 neurons is {float(rev[0]['ratio_reused_over_best']):.1f}× slower (runtime only).")),
        dict(title='Recommendations are conditional',
             text=(f"{d['headline']['stable']} of {d['headline']['total']} profile-and-size recommendations hold under every check; "
                   f"the other {unstable} change with the scaling method, the repeat run, the criteria used, or are exact ties.")),
    ]


def robustness_lead(d):
    c = {x['tag']: x['count'] for x in d['causes']}
    h = d['headline']
    return (f"{h['stable']} of {h['total']} recommendations hold under every check. The other {h['total'] - h['stable']} depend on something: "
            f"the scaling method ({c['N']} cells), which of the two measurement runs is used ({c['S']}), whether scalability is counted ({c['R']}), "
            f"or an exact tie ({c['T']}); a cell can be counted under more than one.")
