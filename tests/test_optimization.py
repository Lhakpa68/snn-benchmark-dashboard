"""Reproducible mathematical checks independent of SNN runtime libraries."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dashboard'))
import optimization


def s(id, t, mem, **kw):
    fw,backend=id.split('/')
    return {'id':id,'framework':fw,'backend':backend,'compile_dominated':kw.get('compile_dominated',False),
            'points':[{'n':100,'t':t,'mem':mem,'runs':5,'cv':2.0}]}

class TestSelection(unittest.TestCase):
    def setUp(self):
        self.rows=[s('brian2/numpy',1,100),s('nest/threads1',2,20),
                   s('nengo/cpu',3,120),s('reference/numpy',0.01,1),
                   s('brian2/cpp',.5,10,compile_dominated=True)]

    def test_baseline_and_compiler_excluded(self):
        r=optimization.evaluate(100,.5,series=self.rows)
        self.assertTrue(r['ok']); self.assertEqual(len(r['rows']),3)
        self.assertEqual(r['exclusions']['baseline'],1)
        self.assertEqual(r['exclusions']['compile_dominated'],1)

    def test_fastest_and_lowest_memory_are_different(self):
        self.assertEqual(optimization.evaluate(100,1,series=self.rows)['winner']['id'],'brian2/numpy')
        self.assertEqual(optimization.evaluate(100,0,series=self.rows)['winner']['id'],'nest/threads1')

    def test_dominated_backend(self):
        r=optimization.evaluate(100,.5,series=self.rows)
        self.assertFalse(next(x for x in r['rows'] if x['id']=='nengo/cpu')['pareto'])
        self.assertTrue(next(x for x in r['rows'] if x['id']=='nest/threads1')['pareto'])

    def test_memory_cap(self):
        r=optimization.evaluate(100,1,max_memory_mb=50,series=self.rows)
        self.assertEqual(r['winner']['id'],'nest/threads1')
        self.assertEqual(r['exclusions']['memory_limit'],2)

    def test_grid_tally_and_data_immutability(self):
        before=str(self.rows)
        r=optimization.evaluate(100,.5,series=self.rows)
        self.assertEqual(sum(x['weight_grid_wins'] for x in r['rows']),21)
        self.assertEqual(str(self.rows),before)

    def test_no_eligible_returns_readable_result(self):
        r=optimization.evaluate(100,.5,max_memory_mb=1,series=self.rows)
        self.assertFalse(r['ok']); self.assertEqual(r['rows'],[])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):optimization.evaluate(100,1.4,series=self.rows)
        with self.assertRaises(ValueError):optimization.evaluate(100,.5,0,series=self.rows)

    def test_real_database_matches_available_sweep(self):
        self.assertEqual(optimization.available_sizes(),[100,500,1000,5000,10000])
        self.assertEqual(optimization.evaluate(100,.5)['winner']['id'],'nest/threads4')
        self.assertEqual(optimization.evaluate(10000,.5)['winner']['id'],'brian2/numpy')

if __name__=='__main__': unittest.main()
