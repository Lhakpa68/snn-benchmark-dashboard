"""Four-criterion optimisation: real campaign and constructed counterexamples."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dashboard'))
import optimization


class TestFourCriteria(unittest.TestCase):
    def test_network_size_changes_input_not_number_of_weights(self):
        a = optimization.evaluate_four(100)
        b = optimization.evaluate_four(10000)
        self.assertEqual(len(a['weights']), 4)
        self.assertEqual(len(b['weights']), 4)
        self.assertNotEqual(a['winner']['id'], b['winner']['id'])

    def test_default_three_metrics_accuracy_zero(self):
        a = optimization.evaluate_four(100)
        self.assertFalse(a['exploratory'])
        self.assertEqual(a['weights']['accuracy'], 0)
        self.assertEqual(a['n_grid_points'], 15)
        self.assertEqual(sum(x['scenario_wins'] for x in a['rows']), 15)

    def test_four_equal_weights_and_35_point_sensitivity(self):
        a = optimization.evaluate_four(100, dict.fromkeys(optimization.CRITERIA, 25))
        self.assertTrue(a['exploratory'])
        self.assertEqual(a['n_grid_points'], 35)
        self.assertEqual(sum(x['scenario_wins'] for x in a['rows']), 35)
        self.assertEqual(sum(a['weights'].values()), 1)

    def test_one_hot_weight_winner_matches_measurement(self):
        for metric in optimization.CRITERIA:
            w = {k: (100 if k==metric else 0) for k in optimization.CRITERIA}
            # Memory growth is zero for every backend at the smallest size,
            # so the memory check is made at the largest size.
            result=optimization.evaluate_four(10000 if metric=='memory' else 100, w)
            rows=result['rows']
            key={'inference':'runtime_s','memory':'memory_growth_mb','scalability':'scaling_k','accuracy':'accuracy_pct'}[metric]
            values=[r[key] for r in rows]
            if metric == 'accuracy':
                self.assertAlmostEqual(rows[0][key], max(values))
            else:
                self.assertAlmostEqual(rows[0][key], min(values))

    def test_normalisation_any_nonzero_four_raw(self):
        a=optimization.evaluate_four(500, dict(inference=70, memory=10, scalability=10, accuracy=10))
        self.assertAlmostEqual(sum(a['weights'].values()),1)
        self.assertAlmostEqual(a['weights']['inference'],0.7)

    def test_missing_accuracy_is_not_filled_or_imputed(self):
        s=[dict(id='brian2/numpy',framework='brian2',backend='numpy',
                compile_dominated=False,fit={'k':1,'r2':.9},
                points=[dict(n=100,t=1,mem=30,runs=5,cv=1)])]
        w=dict(inference=0,memory=0,scalability=0,accuracy=100)
        r=optimization.evaluate_four(100,w,series=s,training_rows=[])
        self.assertFalse(r['ok'])
        self.assertEqual(r['excluded']['missing_accuracy'],1)

    def test_memory_cap_and_bad_weights(self):
        a=optimization.evaluate_four(100,max_memory_mb=50)
        self.assertFalse(a['ok'])
        with self.assertRaises(ValueError):
            optimization.evaluate_four(100,dict.fromkeys(optimization.CRITERIA,0))
        with self.assertRaises(ValueError):
            optimization.evaluate_four(100,dict(inference=-1,memory=30,scalability=30,accuracy=40))

    def test_contributions_sum_to_score(self):
        a=optimization.evaluate_four(10000,dict(inference=30,memory=20,scalability=25,accuracy=25))
        for row in a['rows']:
            self.assertAlmostEqual(row['score'],sum(row['contributions'].values()))
            self.assertTrue(0<=row['score']<=1)

    def test_memory_growth_not_absolute_footprint(self):
        # At the smallest size every backend's growth is zero, so memory
        # cannot favour a backend merely because it ran in a smaller process.
        a=optimization.evaluate_four(100,dict(inference=0,memory=100,scalability=0,accuracy=0))
        self.assertTrue(all(r['memory_growth_mb']==0 for r in a['rows']))
        self.assertTrue(all(r['memory_cost']==0 for r in a['rows']))
        for row in optimization.evaluate_four(10000)['rows']:
            self.assertAlmostEqual(row['memory_growth_mb'],
                                   row['memory_mb']-row['memory_base_mb'])

    def test_plot_ticks_inside_axes(self):
        a=optimization.evaluate_four(1000)
        p=a['plot']
        for t in p['xticks']:
            self.assertTrue(p['x0']<=t['pos']<=p['x1'])
        for t in p['yticks']:
            self.assertTrue(p['y1']<=t['pos']<=p['y0'])
        for r in a['rows']:
            self.assertTrue(p['x0']<r['plot_x']<p['x1'] and p['y1']<r['plot_y']<p['y0'])


class TestSensitivityScope(unittest.TestCase):
    def test_controls_not_ranked(self):
        import dashboard_data as data
        s=data.get_sensitivity()
        self.assertTrue(s['ok'])
        # nine SNN backends, no reference controls
        ids=[x['id'] for x in data.get_scalability_series() if x['framework']!='reference']
        self.assertEqual(len(ids),9)


if __name__ == '__main__': unittest.main()


class TestNetworkFormulation(unittest.TestCase):
    """Share-of-total normalisation, rank sums and reader profiles."""

    def test_share_costs_sum_to_one(self):
        r = optimization.evaluate_four(10000, normalisation='share')
        for key in ('inference', 'memory', 'scalability'):
            self.assertAlmostEqual(sum(x[f'{key}_cost'] for x in r['rows']), 1.0)

    def test_share_cost_is_value_over_total(self):
        r = optimization.evaluate_four(10000, normalisation='share')
        total = sum(x['runtime_s'] for x in r['rows'])
        for x in r['rows']:
            self.assertAlmostEqual(x['inference_cost'], x['runtime_s'] / total)

    def test_bad_normalisation_rejected(self):
        with self.assertRaises(ValueError):
            optimization.evaluate_four(100, normalisation='zscore')

    def test_rank_sum_is_sum_of_criterion_ranks(self):
        r = optimization.evaluate_four(10000)
        n = len(r['rows'])
        self.assertAlmostEqual(sum(x['rank_sum'] for x in r['rows']), 3 * n * (n + 1) / 2)
        best = min(r['rows'], key=lambda x: x['rank_sum'])
        self.assertEqual(best['id'], r['winner']['id'])

    def test_profiles_single_criterion_winner_is_best_measurement(self):
        p = optimization.evaluate_profiles(10000)
        r = optimization.evaluate_four(10000)
        self.assertEqual(p['winners']['fast'], min(r['rows'], key=lambda x: x['runtime_s'])['id'])
        self.assertEqual(p['winners']['scalable'], min(r['rows'], key=lambda x: x['scaling_k'])['id'])

    def test_memory_profile_tied_at_smallest_size(self):
        p = optimization.evaluate_profiles(100)
        col = next(c for c in p['profiles'] if c['key'] == 'lowmem')
        self.assertTrue(col['tied'])
        self.assertIsNone(p['winners']['lowmem'])

    def test_custom_profile_matches_main_result(self):
        w = dict(inference=70, memory=10, scalability=20, accuracy=0)
        p = optimization.evaluate_profiles(1000, extra=w)
        r = optimization.evaluate_four(1000, w)
        self.assertEqual(p['winners']['custom'], r['winner']['id'])
