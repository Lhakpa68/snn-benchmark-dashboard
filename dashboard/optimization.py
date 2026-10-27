"""Evidence-aware preference selection for measured SNN execution methods.

The current dashboard uses evaluate_four(): inference, memory, scalability,
and optional exploratory native-training accuracy, with network size as a
workload selector rather than a score weight. The old evaluate() two-criterion
function is retained solely for reproducibility and legacy regression tests.
No function tunes, accelerates or retrains an SNN simulator. All measurements
come from the original controlled CPU campaign and shared canonical data layer.
"""
from __future__ import annotations

import math
from collections import Counter

import dashboard_data as data

CONTROL_FRAMEWORKS = {'reference'}


def available_sizes():
    """Return measured sweep sizes common to available simulator backends."""
    sizes = set()
    for series in data.get_scalability_series():
        if series['framework'] in CONTROL_FRAMEWORKS or series.get('compile_dominated'):
            continue
        sizes.update(int(p['n']) for p in series['points'] if p['t'] and p['mem'])
    return sorted(sizes)


def _rank(rows, w):
    # Min-max costs are computed on the eligible set ONCE per scenario, before
    # ranking. They use exact observed min/max, never fill in missing values.
    log_t = [math.log(r['runtime_s']) for r in rows]
    log_m = [math.log(r['memory_mb']) for r in rows]
    lo_t, hi_t = min(log_t), max(log_t)
    lo_m, hi_m = min(log_m), max(log_m)
    for r in rows:
        r['runtime_cost'] = ((math.log(r['runtime_s']) - lo_t)/(hi_t - lo_t)) if hi_t > lo_t else 0.0
        r['memory_cost'] = ((math.log(r['memory_mb']) - lo_m)/(hi_m - lo_m)) if hi_m > lo_m else 0.0
        r['score'] = w * r['runtime_cost'] + (1-w) * r['memory_cost']
    return sorted(rows, key=lambda r: (r['score'], r['runtime_s'], r['memory_mb'], r['id']))


def _pareto(rows):
    for r in rows:
        r['pareto'] = not any(
            (other['runtime_s'] <= r['runtime_s'] and other['memory_mb'] <= r['memory_mb'])
            and (other['runtime_s'] < r['runtime_s'] or other['memory_mb'] < r['memory_mb'])
            for other in rows if other is not r)


def evaluate(network_size, runtime_weight=0.5, max_memory_mb=None, *, series=None):
    """Rank observed candidates and report deterministic weight sensitivity.

    Sensitivity ``wins`` are fractions of an equally spaced 0..1 *weight grid*,
    NOT confidence/probabilities. We do not claim these are simulator energy
    measurements, uncertainty intervals, or hardware-independent optima.
    """
    n = int(network_size)
    w = float(runtime_weight)
    if not math.isfinite(w) or not 0 <= w <= 1:
        raise ValueError('Runtime weight must be between 0 and 1.')
    if max_memory_mb in ('', None):
        cap = None
    else:
        cap = float(max_memory_mb)
        if not math.isfinite(cap) or cap <= 0:
            raise ValueError('Memory limit must be a positive number of MB.')

    candidates = []
    exclusions = {'baseline': 0, 'compile_dominated': 0, 'not_measured': 0,
                  'invalid': 0, 'memory_limit': 0}
    for s in (series if series is not None else data.get_scalability_series()):
        fw = s['framework']
        if fw in CONTROL_FRAMEWORKS:
            exclusions['baseline'] += 1
            continue
        if s.get('compile_dominated'):
            exclusions['compile_dominated'] += 1
            continue
        pt = next((p for p in s['points'] if int(p['n']) == n), None)
        if pt is None:
            exclusions['not_measured'] += 1
            continue
        t, mem = pt.get('t'), pt.get('mem')
        if t is None or mem is None or not all(
                isinstance(v, (int, float)) and math.isfinite(v) and v > 0
                for v in (t, mem)):
            exclusions['invalid'] += 1
            continue
        if cap is not None and mem > cap:
            exclusions['memory_limit'] += 1
            continue
        candidates.append(dict(
            id=s['id'], framework=fw, backend=s['backend'],
            runtime_s=float(t), memory_mb=float(mem),
            n_runs=int(pt.get('runs') or 0), cv_pct=pt.get('cv'),
            unstable=(pt.get('cv') is not None and pt.get('cv') > 15),
        ))
    if not candidates:
        return dict(ok=False, network_size=n, runtime_weight=w, memory_weight=1-w, memory_limit_mb=cap,
                    exclusions=exclusions, rows=[], winner=None,
                    message='No eligible measured backends for this condition and memory limit.')
    _pareto(candidates)
    rows = _rank(candidates, w)
    grid = [i / 20 for i in range(21)]
    # Use deep copies: normalization and scoring must not mutate the selected view.
    wins = Counter(_rank([dict(r) for r in candidates], weight)[0]['id'] for weight in grid)
    by_id = {r['id']: r for r in rows}
    for r in rows:
        r['weight_grid_wins'] = wins[r['id']]
        r['weight_grid_share_pct'] = 100 * wins[r['id']] / len(grid)
    winner = rows[0]
    return dict(ok=True, network_size=n, runtime_weight=w,
                memory_weight=1-w, memory_limit_mb=cap, rows=rows,
                winner=winner, pareto=[r for r in rows if r['pareto']],
                exclusions=exclusions, grid_weights=grid,
                n_grid_points=len(grid),
                message='Preference-conditioned recommendation, not a universal best simulator.')

# ---------------------------------------------------------------------------
# Four-criterion preference analysis (October 2026 supervisor clarification)
# ---------------------------------------------------------------------------
# Network size is a WORKLOAD FILTER. It is not a weighting criterion.
# The displayed ranking combines independent measured outputs, not hardware
# changes. Accuracy is a separate MNIST training task, on unequal native
# learning paradigms; including it produces EXPLORATORY rather than validated
# cross-method recommendations.

CRITERIA = ('inference', 'memory', 'scalability', 'accuracy')
# Equal raw importance for the three benchmark-cost criteria is a display
# starting point, NOT a preference elicitation or empirically optimal weight.
# The accuracy criterion is exploratory because native learning differs.
DEFAULT_WEIGHTS = {'inference': 50, 'memory': 50, 'scalability': 50, 'accuracy': 0}
ACCURACY_PRESET = {'train_n': 60000, 'epochs': 10, 'hidden': 256}


def _validated_weights(weights):
    raw = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(raw) != set(CRITERIA):
        raise ValueError('All four named weights are required.')
    for key in CRITERIA:
        raw[key] = float(raw[key])
        if not math.isfinite(raw[key]) or raw[key] < 0 or raw[key] > 100:
            raise ValueError(f'Invalid {key} weight; use 0–100.')
    total = sum(raw.values())
    if total <= 0:
        raise ValueError('At least one criterion must have a positive weight.')
    return {key: raw[key] / total for key in CRITERIA}, raw


def _minmax_cost(rows, field, logarithmic=False, benefit=False):
    values = [(math.log(row[field]) if logarithmic else row[field]) for row in rows]
    low, high = min(values), max(values)
    for row, val in zip(rows, values):
        c = ((high-val) if benefit else (val-low)) / (high-low) if high > low else 0.0
        row[f'{field}_cost'] = c


NORMALISATIONS = ('minmax', 'share')


def _share_cost(rows, field, benefit=False):
    """Share-of-total normalisation: each backend's value divided by the sum
    over the eligible backends (the supervisor's w = m_i / sum m form). For the
    benefit criterion (accuracy) the shortfall from 100% is shared instead, so
    that, as for every other criterion, a smaller share is better. Values are
    shifted to be non-negative first, which leaves a strictly positive set
    unchanged."""
    values = [((100.0 - row[field]) if benefit else row[field]) for row in rows]
    low = min(values)
    if low < 0:
        values = [v - low for v in values]
    total = sum(values)
    for row, val in zip(rows, values):
        row[f'{field}_cost'] = val / total if total > 0 else 0.0


def _rank_sums(rows, active):
    """Unweighted rank sum over the active criteria (1 = best on a criterion,
    ties share the average rank), as a weight-free cross-check of the score."""
    for row in rows:
        row['rank_sum'] = 0.0
    for key in active:
        better_high = key == 'accuracy'
        vals = sorted(rows, key=lambda r: -r[key] if better_high else r[key])
        i = 0
        while i < len(vals):
            j = i
            while j + 1 < len(vals) and abs(vals[j + 1][key] - vals[i][key]) <= 1e-12 * max(1.0, abs(vals[i][key])):
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                vals[k]['rank_sum'] += avg
            i = j + 1
    order = sorted(rows, key=lambda r: (r['rank_sum'], r['id']))
    for pos, row in enumerate(order, start=1):
        row['rank_sum_position'] = pos


def _multi_rank(rows, weights):
    result = [dict(row) for row in rows]
    for row in result:
        row['contributions'] = {k: weights[k] * row[f'{k}_cost'] for k in CRITERIA}
        row['score'] = sum(row['contributions'].values())
    result.sort(key=lambda r: (round(r['score'], 12), r['runtime_s'], r['memory_mb'], r['id']))
    return result


def _weight_grid(active):
    # All 0/25/50/75/100% simplex configurations; 15 with three active
    # criteria, 35 with four. A deterministic sensitivity audit, not a sample
    # distribution or a probability of optimality.
    from itertools import product
    for parts in product(range(5), repeat=len(active)):
        if sum(parts) == 4:
            w = dict.fromkeys(CRITERIA, 0.0)
            w.update({name: parts[i]/4 for i, name in enumerate(active)})
            yield w


def evaluate_four(network_size, weights=None, max_memory_mb=None, *,
                  series=None, training_rows=None, normalisation='minmax'):
    """Score inference runtime, memory, scaling slope and optional accuracy.

    Accuracy is MNIST native-learning accuracy at 60k/10-epoch/256-hidden,
    NOT accuracy on the selected inference workload. Because learning rules
    differ by simulator, a positive accuracy weight is strictly exploratory.
    """
    n = int(network_size)
    if normalisation not in NORMALISATIONS:
        raise ValueError('Normalisation must be minmax or share.')
    norm, raw = _validated_weights(weights)
    if max_memory_mb in (None, ''):
        cap = None
    else:
        cap = float(max_memory_mb)
        if not math.isfinite(cap) or cap <= 0:
            raise ValueError('Memory cap must be positive MB.')

    tr = data.get_training() if training_rows is None else training_rows
    acc_rows = [t for t in tr if all(t.get(key) == val for key, val in ACCURACY_PRESET.items())
                and t.get('accuracy_pct') is not None
                and math.isfinite(float(t['accuracy_pct']))
                and 0 <= float(t['accuracy_pct']) <= 100]
    acc_map = {t['backend_id']: float(t['accuracy_pct']) for t in acc_rows}

    candidates = []
    excluded = dict(control=0, compilation=0, missing=0, invalid=0, memory_cap=0,
                    missing_accuracy=0, missing_scaling=0)
    for s in (data.get_scalability_series() if series is None else series):
        if s['framework'] in CONTROL_FRAMEWORKS:
            excluded['control'] += 1
            continue
        if s.get('compile_dominated'):
            excluded['compilation'] += 1
            continue
        pt = next((p for p in s['points'] if int(p['n']) == n), None)
        if pt is None:
            excluded['missing'] += 1
            continue
        t, mem = pt.get('t'), pt.get('mem')
        if (t is None or mem is None or
            any(not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0
                for v in [t, mem])):
            excluded['invalid'] += 1
            continue
        if cap is not None and mem > cap:
            excluded['memory_cap'] += 1
            continue
        fit = s.get('fit')
        k = fit.get('k') if fit else None
        if k is None or not math.isfinite(k):
            # The sensitivity grid always varies the scalability weight, so a
            # backend without a fitted exponent cannot be scored fairly even
            # when the reader's own scalability weight is zero.
            excluded['missing_scaling'] += 1
            continue
        # Memory criterion: growth of the measured process footprint above the
        # same backend's footprint at the smallest measured size. Absolute
        # peak RSS mostly reflects which process was measured (NEST runs in a
        # separate worker; the others share the interpreter process), so
        # ranking on it would reward process scope rather than the simulation.
        first = next((p for p in s['points'] if p.get('mem')), None)
        base_mem = float(first['mem']) if first else None
        growth = (float(mem) - base_mem) if base_mem is not None else None
        if growth is None or not math.isfinite(growth):
            excluded['invalid'] += 1
            continue
        accuracy = acc_map.get(s['id'])
        if norm['accuracy'] > 0 and accuracy is None:
            excluded['missing_accuracy'] += 1
            continue
        candidates.append(dict(
            id=s['id'], framework=s['framework'], backend=s['backend'],
            inference=float(t), memory=growth, scalability=float(k),
            memory_growth_mb=growth, memory_base_mb=base_mem,
            memory_base_n=int(first['n']) if first else None,
            accuracy=accuracy, runtime_s=float(t), memory_mb=float(mem),
            scaling_k=float(k), scaling_r2=fit.get('r2') if fit else None,
            accuracy_pct=accuracy, cv_pct=pt.get('cv'),
            n_runs=int(pt.get('runs') or 0),
            unstable=pt.get('cv') is not None and pt['cv'] > 15,
            fit_caution=fit is not None and fit.get('r2') is not None and fit['r2'] < 0.8,
        ))

    base = dict(network_size=n, weights=norm, raw_weights=raw, normalisation=normalisation,
                memory_limit_mb=cap, excluded=excluded,
                exploratory=norm['accuracy'] > 0, accuracy_preset=ACCURACY_PRESET,
                message='Accuracy comes from a different MNIST native-learning task and cannot establish a fair cross-paradigm winner.')
    if not candidates:
        return dict(base, ok=False, rows=[], winner=None,
                    notice='No measured backend satisfies this scenario and its required criteria.')

    if normalisation == 'share':
        _share_cost(candidates, 'inference')
        _share_cost(candidates, 'memory')
        _share_cost(candidates, 'scalability')
    else:
        _minmax_cost(candidates, 'inference', logarithmic=True)
        _minmax_cost(candidates, 'memory')   # growth can be zero: linear scale
        _minmax_cost(candidates, 'scalability')
    if norm['accuracy'] > 0:
        (_share_cost if normalisation == 'share' else _minmax_cost)(candidates, 'accuracy', benefit=True)
    else:
        # Accuracy has NO impact on the primary recommendation. The reported
        # value in the table is context only (separate training experiment).
        for r in candidates:
            r['accuracy_cost'] = 0.0

    active = [name for name in CRITERIA if norm[name] > 0]
    for row in candidates:
        row['pareto'] = not any(
            all(other[f'{k}_cost'] <= row[f'{k}_cost'] + 1e-12 for k in active)
            and any(other[f'{k}_cost'] < row[f'{k}_cost'] - 1e-12 for k in active)
            for other in candidates if other is not row)

    _rank_sums(candidates, active)
    ranked = _multi_rank(candidates, norm)
    grid = list(_weight_grid(['inference', 'memory', 'scalability'] +
                              (['accuracy'] if norm['accuracy'] > 0 else [])))
    wins = Counter(_multi_rank(candidates, w)[0]['id'] for w in grid)
    for row in ranked:
        row['scenario_wins'] = wins[row['id']]
        row['scenario_share_pct'] = 100 * wins[row['id']] / len(grid)
    # Positive runtimes and RSS => logarithmic plot coordinates. Bounds use
    # the eligible set (padded so no point sits on an axis) and are
    # independent from the recommendation weights.
    X0, X1, Y0, Y1 = 70, 610, 250, 40
    tx = [math.log10(r['runtime_s']) for r in ranked]
    my = [math.log10(r['memory_mb']) for r in ranked]
    lo_t, hi_t = min(tx) - 0.08, max(tx) + 0.08
    lo_m, hi_m = min(my) - 0.05, max(my) + 0.05
    def px(v): return X0 + (X1 - X0) * (math.log10(v) - lo_t) / (hi_t - lo_t)
    def py(v): return Y0 - (Y0 - Y1) * (math.log10(v) - lo_m) / (hi_m - lo_m)
    for r in ranked:
        r['plot_x'] = round(px(r['runtime_s']), 1)
        r['plot_y'] = round(py(r['memory_mb']), 1)
    # Labels: to the right of a point, or to the left near the right edge,
    # nudged vertically (inside the plot) so that no label covers another
    # label or any plotted point.
    obstacles = [(r['plot_x'] - 8, r['plot_x'] + 8, r['plot_y']) for r in ranked]
    placed = []
    for r in sorted(ranked, key=lambda r: (r['plot_x'], r['plot_y'])):
        left = r['plot_x'] > X1 - 170
        r['label_anchor'] = 'end' if left else 'start'
        r['label_x'] = round(r['plot_x'] + (-12 if left else 12), 1)
        width = 6.2 * (len(r['id']) + 2)
        x0 = r['label_x'] - width if left else r['label_x']
        best = None
        for d in (0, -13, 13, -26, 26, -39, 39, -52, 52, -65, 65):
            ly = r['plot_y'] + 4 + d
            if not (Y1 + 8 <= ly <= Y0 - 3):
                continue
            clash_label = any(abs(ly - y) < 12 and x0 < bx1 and bx0 < x0 + width
                              for bx0, bx1, y in placed)
            clash_point = any(abs(ly - 4 - y) < 9 and x0 < bx1 and bx0 < x0 + width
                              for bx0, bx1, y in obstacles)
            if not clash_label and not clash_point:
                best = ly
                break
        if best is None:
            best = r['plot_y'] + 4
        placed.append((x0, x0 + width, best))
        r['label_y'] = round(best, 1)
    def ticks(lo, hi, unit):
        out = []
        for e in range(math.floor(lo) - 1, math.ceil(hi) + 1):
            for m in (1, 2, 5):
                v = m * 10 ** e
                if lo <= math.log10(v) <= hi:
                    out.append(v)
        if len(out) > 7:
            out = [v for v in out if str(v).lstrip('0.').startswith(('1', '5'))] or out
        return out
    def fmt_t(v):
        return f"{v*1000:g} ms" if v < 1 else f"{v:g} s"
    xt = [dict(pos=round(px(v), 1), label=fmt_t(v)) for v in ticks(lo_t, hi_t, 's')]
    yt = [dict(pos=round(py(v), 1), label=f"{v:g}") for v in ticks(lo_m, hi_m, 'MB')]
    return dict(base, ok=True, rows=ranked, winner=ranked[0],
                pareto=[r for r in ranked if r['pareto']],
                active=active, n_grid_points=len(grid),
                scenario_grid=grid, plot=dict(
                    xticks=xt, yticks=yt, x0=X0, x1=X1, y0=Y0, y1=Y1,
                    min_runtime=min(r['runtime_s'] for r in ranked),
                    max_runtime=max(r['runtime_s'] for r in ranked),
                    min_memory=min(r['memory_mb'] for r in ranked),
                    max_memory=max(r['memory_mb'] for r in ranked)))


# ---------------------------------------------------------------------------
# Preference profiles: the output layer of the selection network
# ---------------------------------------------------------------------------
# Supervisory review (October 2026) framed selection as a small network:
# backends -> measured criteria (normalised values) -> one output node per user
# profile, each output being a weighted sum y = W x (+ b). The profiles below are
# illustrative readers with different needs ("I need a fast SNN", "I need an
# accurate SNN", pairs of criteria). They are NOT elicited preferences.
PROFILES = (
    ('fast', 'Fast SNN', dict(inference=100, memory=0, scalability=0, accuracy=0)),
    ('lowmem', 'Low-memory SNN', dict(inference=0, memory=100, scalability=0, accuracy=0)),
    ('scalable', 'Scalable SNN', dict(inference=0, memory=0, scalability=100, accuracy=0)),
    ('accurate', 'Accurate SNN*', dict(inference=0, memory=0, scalability=0, accuracy=100)),
    ('balanced', 'Balanced', dict(inference=50, memory=50, scalability=50, accuracy=0)),
    ('speed_mem', 'Speed + memory', dict(inference=50, memory=50, scalability=0, accuracy=0)),
    ('mem_scal', 'Memory + scaling', dict(inference=0, memory=50, scalability=50, accuracy=0)),
    ('scal_acc', 'Scaling + accuracy*', dict(inference=0, memory=0, scalability=50, accuracy=50)),
    ('acc_speed', 'Accuracy + speed*', dict(inference=50, memory=0, scalability=0, accuracy=50)),
)


def evaluate_profiles(network_size, max_memory_mb=None, normalisation='minmax',
                      extra=None, **kw):
    """Score every eligible backend for every preference profile.

    Returns the score matrix (backend x profile), the recommended backend of
    each profile and, for the network diagram, each backend's normalised
    goodness on each criterion (1 = best eligible value). ``extra`` adds the
    reader's own weights as a final 'Your priorities' column."""
    profiles = list(PROFILES)
    if extra is not None:
        profiles.append(('custom', 'Your priorities', dict(extra)))
    cols, scores, winners, ids = [], {}, {}, None
    goodness = {}
    for key, label, weights in profiles:
        res = evaluate_four(network_size, weights, max_memory_mb, normalisation=normalisation, **kw)
        if not res['ok']:
            continue
        spread = max(r['score'] for r in res['rows']) - min(r['score'] for r in res['rows'])
        tied = spread <= 1e-12
        cols.append(dict(key=key, label=label, weights=res['weights'],
                         exploratory=res['exploratory'], tied=tied))
        winners[key] = None if tied else res['winner']['id']
        for pos, r in enumerate(res['rows'], start=1):
            scores.setdefault(r['id'], {})[key] = dict(score=r['score'], rank=pos)
        if key == 'balanced' or ids is None:
            ids = [r['id'] for r in res['rows']]
        if key == 'accurate' or not goodness:
            for r in res['rows']:
                g = goodness.setdefault(r['id'], {})
                for c in CRITERIA:
                    if f'{c}_cost' in r and (c != 'accuracy' or key == 'accurate'):
                        g[c] = r[f'{c}_cost']
    # goodness in [0, 1] from the costs (1 - cost / largest cost)
    for c in CRITERIA:
        top = max((g.get(c, 0.0) for g in goodness.values()), default=0.0)
        for g in goodness.values():
            if c in g:
                g[c] = 1.0 - (g[c] / top if top > 0 else 0.0)
    order = ids or sorted(scores)
    return dict(network_size=int(network_size), normalisation=normalisation,
                profiles=cols, backends=order, scores=scores, winners=winners,
                goodness=goodness, criteria=list(CRITERIA))


# ---------------------------------------------------------------------------
# Softmax activation: priority of each simulator for each reader profile
# ---------------------------------------------------------------------------
# Supervisory review (15 October 2026) added an activation stage to the output
# layer of the selection network. The weighted-sum outputs y (lower is better)
# are turned into priorities that are positive and sum to one for each profile.
# A simulator is represented by its best eligible backend for that profile,
# so a simulator with several backends is not favoured simply because it has
# more of them. Softmax is monotone: the simulator with the highest priority is
# always the simulator of the recommended backend, so no recommendation changes.
SOFTMAX_TAU = 0.1


def softmax_priorities(profiles, tau=SOFTMAX_TAU):
    """Softmax priorities of the simulators for every profile of
    ``evaluate_profiles``.

    For profile p and simulator s, y_sp = min over the eligible backends of s
    of y_ip, and pi_sp = exp(-y_sp / tau) / sum_s' exp(-y_s'p / tau). The
    smallest score is subtracted before exponentiating, which leaves the
    result unchanged and avoids overflow. Returns, per profile, the simulators
    in order of priority with the backend that represents each."""
    tau = float(tau)
    if not math.isfinite(tau) or tau <= 0:
        raise ValueError('Softmax temperature must be positive.')
    out = []
    for pf in profiles['profiles']:
        key = pf['key']
        best = {}
        for b, cells in profiles['scores'].items():
            cell = cells.get(key)
            if cell is None:
                continue
            sim = b.split('/')[0]
            here = (round(cell['score'], 12), cell['rank'])
            if sim not in best or here < (round(best[sim][1], 12), best[sim][2]):
                best[sim] = (b, cell['score'], cell['rank'])
        if not best:
            continue
        low = min(v[1] for v in best.values())
        expo = {s: math.exp(-(v[1] - low) / tau) for s, v in best.items()}
        total = sum(expo.values())
        rows = sorted(({'simulator': s, 'backend': best[s][0], 'score': best[s][1],
                        'priority': expo[s] / total} for s in best),
                      key=lambda r: (-r['priority'], best[r['simulator']][2]))
        out.append(dict(key=key, label=pf['label'], exploratory=pf['exploratory'],
                        tied=pf['tied'], rows=rows,
                        priority={r['simulator']: r['priority'] for r in rows}))
    sims = sorted({r['simulator'] for p in out for r in p['rows']})
    return dict(tau=tau, profiles=out, simulators=sims,
                network_size=profiles['network_size'],
                normalisation=profiles['normalisation'])


def softmax_curve(profile, tau=SOFTMAX_TAU, n=121):
    """The activation curve behind one profile of ``softmax_priorities``.

    With the normaliser Z = sum_s exp(-y_sp / tau) of the profile held fixed,
    pi(y) = exp(-y / tau) / Z for scores y from 0 to 1, so every simulator of
    the profile lies on the curve at (y_sp, pi_sp). Returns the curve samples
    and the simulator points, in order of priority."""
    tau = float(tau)
    if not math.isfinite(tau) or tau <= 0:
        raise ValueError('Softmax temperature must be positive.')
    low = min(r['score'] for r in profile['rows'])
    z = sum(math.exp(-(r['score'] - low) / tau) for r in profile['rows'])
    xs = [i / (n - 1) for i in range(n)]
    curve = [(x, math.exp(-(x - low) / tau) / z) for x in xs]
    points = [dict(simulator=r['simulator'], backend=r['backend'], score=r['score'],
                   priority=r['priority']) for r in profile['rows']]
    return dict(curve=curve, points=points, tau=tau)
