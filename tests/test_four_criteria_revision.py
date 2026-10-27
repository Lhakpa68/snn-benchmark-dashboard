"""Tests for the four-criterion selection path (evaluate_four / evaluate_profiles).

Added after the V6 review (review/REVIEW.md). They document what the code does today and
check the published Tables 19 and 20. Fixture tests use series= / training_rows= and need no
database. The two database tests open the results database read-only.
"""
import math
import sqlite3
import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dashboard'))
import optimization as opt
import dashboard_data as data

N = 1000
ZERO = dict.fromkeys(opt.CRITERIA, 0)


def w(**kw):
    return dict(ZERO, **kw)


def mk(id, t, mem_n, mem_base=100.0, k=1.0, r2=0.9, compile_dominated=False, fit=True, n=N):
    fw, be = id.split('/')
    return dict(id=id, framework=fw, backend=be, compile_dominated=compile_dominated,
                fit=dict(k=k, r2=r2) if fit else None,
                points=[dict(n=100, t=t, mem=mem_base, runs=5, cv=1.0),
                        dict(n=n, t=t, mem=mem_n, runs=5, cv=1.0)])


def acc(id, a):
    return dict(backend_id=id, accuracy_pct=a, **opt.ACCURACY_PRESET)


def costs(series, key, weights, **kw):
    r = opt.evaluate_four(N, weights, series=series, training_rows=kw.pop('training_rows', []), **kw)
    return [x[key] for x in sorted(r['rows'], key=lambda x: x['id'])]


class TestTransformations(unittest.TestCase):
    def test_minmax_runtime_uses_log(self):
        s = [mk('a/x', 0.001, 100), mk('b/x', 0.010, 100), mk('c/x', 0.100, 100)]
        self.assertEqual([round(c, 9) for c in costs(s, 'inference_cost', w(inference=100))], [0.0, 0.5, 1.0])

    def test_share_runtime_uses_raw_seconds(self):
        s = [mk('a/x', 1.0, 100), mk('b/x', 2.0, 100), mk('c/x', 7.0, 100)]
        got = costs(s, 'inference_cost', w(inference=100), normalisation='share')
        for g, e in zip(got, [0.1, 0.2, 0.7]):
            self.assertAlmostEqual(g, e)

    def test_accuracy_minmax_is_shortfall_from_best(self):
        s = [mk(i, 1, 100) for i in ('a/x', 'b/x', 'c/x')]
        tr = [acc('a/x', 97), acc('b/x', 90), acc('c/x', 80)]
        got = costs(s, 'accuracy_cost', w(accuracy=100), training_rows=tr)
        for g, e in zip(got, [0.0, 7 / 17, 1.0]):
            self.assertAlmostEqual(g, e)
        self.assertAlmostEqual(got[1], 0.4118, places=4)

    def test_accuracy_share_is_shortfall_from_100(self):
        s = [mk(i, 1, 100) for i in ('a/x', 'b/x', 'c/x')]
        tr = [acc('a/x', 97), acc('b/x', 90), acc('c/x', 80)]
        got = costs(s, 'accuracy_cost', w(accuracy=100), training_rows=tr, normalisation='share')
        for g, e in zip(got, [3 / 33, 10 / 33, 20 / 33]):
            self.assertAlmostEqual(g, e)

    def test_accuracy_minmax_same_under_either_convention(self):
        a = [97.0, 90.0, 80.0]
        best = max(a)
        def minmax(v):
            lo, hi = min(v), max(v)
            return [(x - lo) / (hi - lo) for x in v]
        from_100, from_best = minmax([100 - x for x in a]), minmax([best - x for x in a])
        for p, q in zip(from_100, from_best):
            self.assertAlmostEqual(p, q)
        s = [mk(i, 1, 100) for i in ('a/x', 'b/x', 'c/x')]
        tr = [acc(i, v) for i, v in zip(('a/x', 'b/x', 'c/x'), a)]
        for g, e in zip(costs(s, 'accuracy_cost', w(accuracy=100), training_rows=tr), from_100):
            self.assertAlmostEqual(g, e)

    def test_share_zero_sum_gives_zero_cost(self):
        s = [mk('a/x', 1, 100), mk('b/x', 2, 100)]          # growth 0 for both
        self.assertEqual(costs(s, 'memory_cost', w(memory=100), normalisation='share'), [0.0, 0.0])

    def test_share_constant_positive_gives_equal_costs(self):
        s = [mk('a/x', 5, 100), mk('b/x', 5, 100), mk('c/x', 5, 100), mk('d/x', 5, 100)]
        got = costs(s, 'inference_cost', w(inference=100), normalisation='share')
        for g in got:
            self.assertAlmostEqual(g, 0.25)
        self.assertEqual(costs(s, 'inference_cost', w(inference=100)), [0.0] * 4)   # min-max: zero


class TestEligibilityAndRules(unittest.TestCase):
    def setUp(self):
        self.series = [mk('brian2/numpy', 1.0, 150, k=0.5), mk('nest/threads1', 2.0, 120, k=1.1),
                       mk('nengo/reference', 3.0, 300, k=1.5),
                       mk('reference/vectorised', 0.001, 110, k=0.1),            # control
                       mk('brian2/cpp_standalone', 0.5, 110, k=0.1, compile_dominated=True)]
        self.tr = [acc(i, a) for i, a in (('brian2/numpy', 10.0), ('nest/threads1', 8.0), ('nengo/reference', 85.0),
                                           ('reference/vectorised', 99.0), ('brian2/cpp_standalone', 99.0))]
        self.bad = {'reference/vectorised', 'brian2/cpp_standalone'}

    def test_evaluate_four_excludes_controls_and_compile_dominated(self):
        r = opt.evaluate_four(N, series=self.series, training_rows=self.tr)
        ids = {x['id'] for x in r['rows']}
        self.assertEqual(ids, {'brian2/numpy', 'nest/threads1', 'nengo/reference'})
        self.assertEqual((r['excluded']['control'], r['excluded']['compilation']), (1, 1))
        # rank sum: assigned only to eligible rows and sums to criteria x n(n+1)/2
        self.assertAlmostEqual(sum(x['rank_sum'] for x in r['rows']), 3 * 3 * 4 / 2)
        # priority grid: 15 points, every win goes to an eligible backend
        self.assertEqual(sum(x['scenario_wins'] for x in r['rows']), r['n_grid_points'])
        # Pareto set only contains eligible backends
        self.assertTrue({x['id'] for x in r['pareto']} <= ids)
        # profiles (incl. accuracy ones) and the reader's own profile
        p = opt.evaluate_profiles(N, series=self.series, training_rows=self.tr, extra=dict(inference=50, memory=50, scalability=0, accuracy=20))
        self.assertEqual(set(p['backends']), ids)
        self.assertEqual(set(p['scores']), ids)
        self.assertTrue(set(p['goodness']) <= ids)
        self.assertFalse(self.bad & {v for v in p['winners'].values() if v})

    def test_exact_tie_broken_by_runtime(self):
        # equal growth (50 MB) for all three; a third, larger-growth backend keeps min-max defined
        s = [mk('x/slow', 2.0, 150, 100), mk('y/fast', 1.0, 140, 90), mk('z/big', 1.5, 400, 100)]
        r = opt.evaluate_four(N, w(memory=100), series=s, training_rows=[])
        scores = {x['id']: x['score'] for x in r['rows']}
        self.assertEqual(round(scores['x/slow'], 12), round(scores['y/fast'], 12))
        self.assertEqual(r['winner']['id'], 'y/fast')                        # runtime decides

    def test_exact_tie_broken_by_memory_then_id(self):
        # same score and runtime; absolute memory decides, then id
        s = [mk('b/two', 1.0, 150, 100), mk('a/one', 1.0, 90, 40), mk('z/big', 1.0, 400, 100)]
        r = opt.evaluate_four(N, w(memory=100), series=s, training_rows=[])
        self.assertEqual([x['id'] for x in r['rows']][:2], ['a/one', 'b/two'])    # 90 MB before 150 MB
        s = [mk('b/two', 1.0, 150, 100), mk('a/one', 1.0, 150, 100), mk('z/big', 1.0, 400, 100)]
        r = opt.evaluate_four(N, w(memory=100), series=s, training_rows=[])
        self.assertEqual([x['id'] for x in r['rows']][:2], ['a/one', 'b/two'])    # id last

    def test_memory_cap_applies_to_absolute_rss_before_normalisation(self):
        s = [mk('a/x', 1, 100), mk('b/x', 1, 200), mk('c/x', 1, 400), mk('d/x', 1, 520, 500)]
        free = dict(zip('abcd', costs(s, 'memory_cost', w(memory=100))))
        self.assertAlmostEqual(free['b'], 100 / 300)                      # growth 0, 100, 300, 20
        capped = opt.evaluate_four(N, w(memory=100), max_memory_mb=250, series=s, training_rows=[])
        self.assertEqual(capped['excluded']['memory_cap'], 2)             # c (400) and d (520, small growth)
        cost = {x['id']: x['memory_cost'] for x in capped['rows']}
        self.assertEqual(set(cost), {'a/x', 'b/x'})
        self.assertAlmostEqual(cost['b/x'], 1.0)                          # renormalised on survivors

    def test_missing_fit_excluded_even_at_zero_scalability_weight(self):
        s = [mk('a/x', 1, 100), mk('b/x', 2, 110, fit=False)]
        r = opt.evaluate_four(N, w(inference=100), series=s, training_rows=[])
        self.assertEqual([x['id'] for x in r['rows']], ['a/x'])
        self.assertEqual(r['excluded']['missing_scaling'], 1)

    def test_r2_does_not_change_score(self):
        a = [mk('a/x', 1, 100, k=0.5, r2=0.99), mk('b/x', 2, 110, k=1.0, r2=0.95)]
        b = [mk('a/x', 1, 100, k=0.5, r2=0.10), mk('b/x', 2, 110, k=1.0, r2=0.20)]
        self.assertEqual(costs(a, 'score', opt.DEFAULT_WEIGHTS), costs(b, 'score', opt.DEFAULT_WEIGHTS))

    def test_evaluate_profiles_skips_profiles_with_no_eligible_backend(self):
        s = [mk('a/x', 1, 100)]
        p = opt.evaluate_profiles(N, max_memory_mb=1, series=s, training_rows=[])
        self.assertEqual((p['profiles'], p['backends']), ([], []))


class TestPublishedValues(unittest.TestCase):
    """Read-only database checks of Tables 19 and 20 in thesis V6 (session A, min-max)."""

    @classmethod
    def setUpClass(cls):
        real = sqlite3.connect
        def ro(path, *a, **k):
            return real(f'file:{path}?mode=ro', uri=True)
        cls._patch = mock.patch.object(data.sqlite3, 'connect', ro)
        cls._patch.start()

    @classmethod
    def tearDownClass(cls):
        cls._patch.stop()

    def test_published_table19_values(self):
        pub = {100: ('nest/threads4', .244, 'nest/threads2', .254, 9, 5), 500: ('snntorch/cpu', .277, 'spikingjelly/cpu', .322, 6, 7),
               1000: ('snntorch/cpu', .255, 'spikingjelly/cpu', .283, 5, 4), 5000: ('brian2/numpy', .044, 'brian2/cython', .045, 7, 4),
               10000: ('brian2/cython', .000, 'brian2/numpy', .002, 15, 1)}
        for n, (win, sc, ru, rs, wins, par) in pub.items():
            r = opt.evaluate_four(n)
            self.assertEqual(r['winner']['id'], win, n)
            self.assertAlmostEqual(r['winner']['score'], sc, places=3, msg=n)
            self.assertEqual(r['rows'][1]['id'], ru, n)
            self.assertAlmostEqual(r['rows'][1]['score'], rs, places=3, msg=n)
            self.assertEqual(r['winner']['scenario_wins'], wins, n)
            self.assertEqual(len(r['pareto']), par, n)
            self.assertEqual(r['n_grid_points'], 15)

    def test_published_table20_minmax_matches_and_41_of_45_agree(self):
        NE4, SN, SJ, BC, BN, NG = ('nest/threads4', 'snntorch/cpu', 'spikingjelly/cpu', 'brian2/cython', 'brian2/numpy', 'nengo/reference')
        pub = {  # profile key -> published winner at N = 100, 500, 1000, 5000, 10000 (None = no choice possible)
            'fast': [NE4, NE4, NE4, NE4, BC], 'lowmem': [None, SN, BC, BC, BC], 'scalable': [BC] * 5, 'accurate': [SJ] * 5,
            'balanced': [NE4, SN, SN, BN, BC], 'speed_mem': [NE4, SN, SN, BN, BC], 'mem_scal': [BC] * 5,
            'scal_acc': [SN] * 5, 'acc_speed': [NG, SN, SN, SN, SJ]}
        differ = set()
        total = 0
        for i, n in enumerate((100, 500, 1000, 5000, 10000)):
            mm = opt.evaluate_profiles(n)
            sh = opt.evaluate_profiles(n, normalisation='share')
            for key, _, _ in opt.PROFILES:
                self.assertEqual(mm['winners'][key], pub[key][i], (key, n))
                total += 1
                if mm['winners'][key] != sh['winners'][key]:
                    differ.add((key, n))
        self.assertEqual(total, 45)
        self.assertEqual(differ, {('balanced', 100), ('acc_speed', 100), ('balanced', 5000), ('speed_mem', 5000)})


if __name__ == '__main__':
    unittest.main()
