"""Softmax activation of the selection network (supervisory review, 15 October 2026)."""
import math
import re
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard'))
import optimization as opt  # noqa: E402


@pytest.fixture(scope='module')
def prof1000():
    return opt.evaluate_profiles(1000)


def test_priorities_sum_to_one_and_are_positive(prof1000):
    res = opt.softmax_priorities(prof1000)
    assert res['tau'] == pytest.approx(0.1)
    for pf in res['profiles']:
        vals = list(pf['priority'].values())
        assert sum(vals) == pytest.approx(1.0, abs=1e-12)
        assert all(v > 0 for v in vals)


def test_top_simulator_matches_recommended_backend(prof1000):
    res = opt.softmax_priorities(prof1000)
    for pf in res['profiles']:
        winner = prof1000['winners'][pf['key']]
        if winner is not None:
            assert pf['rows'][0]['simulator'] == winner.split('/')[0]


def test_simulator_uses_its_best_backend(prof1000):
    res = opt.softmax_priorities(prof1000)
    bal = next(p for p in res['profiles'] if p['key'] == 'balanced')
    by = {r['simulator']: r for r in bal['rows']}
    assert by['brian2']['backend'] == 'brian2/cython'
    assert by['nest']['backend'] == 'nest/threads4'
    # Balanced at N=1,000 (Table 40): snnTorch 0.2546, SpikingJelly 0.2826, Brian2 0.2834
    assert by['snntorch']['priority'] == pytest.approx(0.392, abs=0.001)
    ys = {s: r['score'] for s, r in by.items()}
    z = sum(math.exp(-y / 0.1) for y in ys.values())
    assert by['spikingjelly']['priority'] == pytest.approx(math.exp(-ys['spikingjelly'] / 0.1) / z)


def test_tied_profile_gives_equal_priorities():
    res = opt.softmax_priorities(opt.evaluate_profiles(100))
    low = next(p for p in res['profiles'] if p['key'] == 'lowmem')
    assert low['tied']
    assert all(v == pytest.approx(0.2) for v in low['priority'].values())


def test_temperature_must_be_positive(prof1000):
    with pytest.raises(ValueError):
        opt.softmax_priorities(prof1000, tau=0)


def test_every_simulator_lies_on_its_activation_curve(prof1000):
    res = opt.softmax_priorities(prof1000)
    for pf in res['profiles']:
        c = opt.softmax_curve(pf, res['tau'])
        z = sum(math.exp(-p['score'] / res['tau']) for p in c['points'])
        for p in c['points']:
            assert math.exp(-p['score'] / res['tau']) / z == pytest.approx(p['priority'])
        ys = [y for _, y in c['curve']]
        assert all(a > b for a, b in zip(ys, ys[1:]))  # better score, higher priority


def test_optimisation_page_draws_curve_without_bars():
    flask = pytest.importorskip('flask')  # noqa: F841
    import app
    html = app.app.test_client().get('/api/optimization/fragment?n=1000').get_data(as_text=True)
    assert 'opt-softmax-svg' in html and 'softmaxProfile' in html
    assert "opt-softmax-bar" not in html
    assert all(d.startswith("M") for d in re.findall(r'<path d="([^"]*)"', html))
