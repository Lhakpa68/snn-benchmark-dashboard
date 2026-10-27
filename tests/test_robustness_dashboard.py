"""Tie, stability and robustness evidence added to the dashboard (dashboard/robustness.py).

The selection method is unchanged; these tests check the new evidence layer and that it does not
alter any score, order or winner. Flask page tests are skipped if Flask is not installed. The
Streamlit front end calls the same robustness functions (tested here); Streamlit itself is not
needed.
"""
import copy
import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dashboard'))
import optimization as opt
import robustness as rb

LOWMEM = dict(inference=0, memory=100, scalability=0, accuracy=0)
BALANCED = dict(inference=50, memory=50, scalability=50, accuracy=0)
MEM_SCAL = dict(inference=0, memory=50, scalability=50, accuracy=0)


class TestTies(unittest.TestCase):
    def test_lowmem_500_tie_is_snntorch_and_brian2_cython(self):
        t = rb.tie_info(opt.evaluate_four(500, LOWMEM))
        self.assertTrue(t['is_tie'])
        self.assertEqual(set(t['ids']), {'snntorch/cpu', 'brian2/cython'})
        self.assertEqual(t['ids'][0], 'snntorch/cpu')                # shown first: shorter runtime
        self.assertEqual(t['reason'], 'shorter runtime')
        self.assertIn('Tied with brian2/cython', rb.tie_sentence(t))
        self.assertIn('tie rule', rb.tie_sentence(t))

    def test_lowmem_100_all_eight_tie(self):
        r = opt.evaluate_four(100, LOWMEM)
        t = rb.tie_info(r)
        self.assertEqual(len(t['ids']), 8)
        self.assertTrue(t['all_tied'])

    def test_no_tie_for_default_scenarios(self):
        for n in rb.SIZES:
            self.assertFalse(rb.tie_info(opt.evaluate_four(n))['is_tie'], n)

    def test_profile_labels_mark_ties(self):
        p500 = rb.attach_profile_ties(opt.evaluate_profiles(500))
        self.assertEqual(p500['labels']['lowmem'], 'snntorch/cpu = brian2/cython (tied)')
        self.assertEqual(set(p500['ties']['lowmem']['ids']), {'snntorch/cpu', 'brian2/cython'})
        p100 = rb.attach_profile_ties(opt.evaluate_profiles(100))
        self.assertEqual(p100['labels']['lowmem'], 'no difference (all 8 tied)')
        self.assertTrue(p100['ties']['lowmem']['all_tied'])
        self.assertEqual(p500['labels']['fast'], p500['winners']['fast'])      # untied profiles unchanged

    def test_evidence_layer_does_not_change_selection(self):
        for n in rb.SIZES:
            before = opt.evaluate_four(n)
            snap = [(r['id'], r['score'], r['rank_sum'], r['scenario_wins'], r['pareto']) for r in before['rows']]
            after = rb.decorate(copy.deepcopy(before), n, None, None, 'minmax')
            self.assertEqual(snap, [(r['id'], r['score'], r['rank_sum'], r['scenario_wins'], r['pareto']) for r in after['rows']])
            self.assertEqual(before['winner']['id'], after['winner']['id'])
        a = opt.evaluate_profiles(500)
        winners, scores = copy.deepcopy(a['winners']), copy.deepcopy(a['scores'])
        rb.attach_profile_ties(a)
        self.assertEqual((winners, scores), (a['winners'], a['scores']))


class TestStability(unittest.TestCase):
    def check(self, st, key):
        return next(c for c in st['checks'] if c['key'] == key)

    def test_balanced_5000_changes_under_share_to_brian2_cython(self):
        st = rb.stability(5000, BALANCED, None, 'minmax')
        c = self.check(st, 'normalisation')
        self.assertEqual(c['status'], 'changes')
        self.assertEqual(c['text'], 'Changes to brian2/cython under share-of-total')

    def test_memory_scaling_500_becomes_tie_without_scalability(self):
        st = rb.stability(500, MEM_SCAL, None, 'minmax')
        c = self.check(st, 'scalability')
        self.assertEqual(c['status'], 'becomes_tie')
        self.assertTrue(c['text'].startswith('Becomes a tie without scalability'))
        self.assertNotIn('Changes to', c['text'])

    def test_same_is_reported_as_same(self):
        st = rb.stability(10000, BALANCED, None, 'minmax')
        self.assertEqual(self.check(st, 'normalisation')['text'], 'Same under share-of-total')
        self.assertEqual(self.check(st, 'scalability')['status'], 'same')

    def test_scalability_check_only_when_weight_positive(self):
        st = rb.stability(1000, dict(inference=50, memory=50, scalability=0, accuracy=0), None, 'minmax')
        self.assertEqual([c['key'] for c in st['checks']], ['normalisation'])

    def test_scalability_only_profile_not_applicable(self):
        st = rb.stability(1000, dict(inference=0, memory=0, scalability=100, accuracy=0), None, 'minmax')
        self.assertEqual(self.check(st, 'scalability')['status'], 'n/a')

    def test_normalisation_check_flips_direction_when_share_selected(self):
        st = rb.stability(5000, BALANCED, None, 'share')
        self.assertEqual(self.check(st, 'normalisation')['text'], 'Changes to brian2/numpy under min–max')

    def test_margin_is_score_distance_with_wording_and_absent_on_tie(self):
        st = rb.stability(5000, BALANCED, None, 'minmax')
        self.assertAlmostEqual(st['margin']['value'], 0.0008065, places=6)
        self.assertEqual(st['margin']['note'], 'score difference, not a significance test')
        self.assertIsNone(rb.stability(500, LOWMEM, None, 'minmax')['margin'])

    def test_session_b_not_in_live_checks(self):
        st = rb.stability(500, BALANCED, None, 'minmax')
        self.assertFalse(any('session' in c['text'].lower() for c in st['checks']))
        self.assertIn('Session B is not checked live', st['note'])


class TestRobustnessData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = rb.load_robustness()

    def test_headline_26_of_45(self):
        self.assertEqual((self.d['headline']['stable'], self.d['headline']['total']), (26, 45))

    def test_cause_counts_7_7_4_2(self):
        self.assertEqual({c['tag']: c['count'] for c in self.d['causes']}, {'S': 7, 'R': 7, 'N': 4, 'T': 2})
        text = {c['tag']: c['text'] for c in self.d['causes']}
        self.assertIn('6 of 7 involve SpikingJelly', text['S'])
        self.assertIn('5 reduce to accuracy-only', text['R'])
        self.assertIn('2 become ties', text['R'])

    def test_grid_has_45_cells_and_expected_tags(self):
        self.assertEqual(len(self.d['cells']), 45)
        g = self.d['grid']
        self.assertEqual(g['Low-memory SNN'][100]['tags'], ['T'])
        self.assertEqual(g['Low-memory SNN'][500]['status'], 'tie')
        self.assertEqual(g['Balanced'][5000]['tags'], ['N'])
        self.assertEqual(g['Fast SNN'][10000]['tags'], ['S'])
        self.assertEqual(g['Memory + scaling'][500]['tags'], ['R'])
        self.assertEqual(g['Scalable SNN'][1000]['status'], 'stable')
        self.assertTrue(g['Accurate SNN*'][100]['exploratory'])

    def test_wrong_size_ratios(self):
        W = self.d['wrong_size']
        fwd = [round(float(r['ratio_reused_over_best']), 2) for r in W['forward']]
        rev = [round(float(r['ratio_reused_over_best']), 2) for r in W['reverse']]
        self.assertEqual(fwd, [1.0, 1.0, 1.0, 1.0, 2.38])
        self.assertEqual(rev, [75.52, 19.07, 9.73, 1.39, 1.0])
        self.assertEqual((W['forward_backend'], W['reverse_backend']), ('nest/threads4', 'brian2/cython'))

    def test_session_transfer_has_seven_cells(self):
        self.assertEqual(len(self.d['session']), 14)

    def test_exports_contain_all_datasets(self):
        sets = {r['dataset'] for r in rb.export_rows()}
        self.assertEqual(sets, {'robustness_grid', 'robustness_wrong_size_forward', 'robustness_wrong_size_reverse', 'robustness_session_transfer'})
        self.assertEqual(sum(r['dataset'] == 'robustness_grid' for r in rb.export_rows()), 45)
        self.assertIn('"stable": 26', rb.export_json())

    def test_static_inputs_match_review_outputs(self):
        for name in ('sensitivity_summary.csv', 'consequence_2a_forward.csv', 'consequence_2a_reverse.csv', 'consequence_2b_session.csv'):
            src = ROOT / 'review' / name
            if src.exists():
                self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),
                                 hashlib.sha256((rb.DATA_DIR / name).read_bytes()).hexdigest(), name)


try:
    import flask  # noqa: F401
    import app as dashboard_app
except Exception:                                    # pragma: no cover
    dashboard_app = None


@unittest.skipIf(dashboard_app is None, 'Flask not installed')
class TestFlaskPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = dashboard_app.app.test_client()

    def get(self, url):
        r = self.c.get(url)
        self.assertEqual(r.status_code, 200, url)
        return r.data.decode()

    def test_robustness_page(self):
        t = self.get('/robustness')
        self.assertIn('26 of 45 recommendations unchanged under all checks', t)
        self.assertIn('Evaluation added during revision; session B and scalability-removal checks computed offline from the stored runs.', t)
        for tag in 'NSRT':
            self.assertIn(f'rb-tag-{tag}', t)
        counts = re.findall(r'class="rb-count">(\d+)<', t)
        self.assertEqual(counts, ['7', '7', '4', '2'])
        self.assertIn('75.5×', t)
        self.assertIn('2.38×', t)

    def test_nav_has_robustness_link(self):
        self.assertIn('href="/robustness"', self.get('/'))

    def test_optimisation_shows_tie_and_stability(self):
        t = self.get('/optimization?n=500&inference=0&memory=100&scalability=0&accuracy=0')
        self.assertIn('Tied with', t)
        self.assertIn('snntorch/cpu = brian2/cython (tied)', t)
        t = self.get('/optimization?n=5000&inference=50&memory=50&scalability=50&accuracy=0')
        self.assertIn('Stability of this recommendation', t)
        self.assertIn('Changes to brian2/cython under share-of-total', t)
        self.assertIn('score difference, not a significance test', t)

    def test_fragment_includes_stability_and_becomes_tie(self):
        t = self.get('/api/optimization/fragment?n=500&inference=0&memory=50&scalability=50&accuracy=0')
        self.assertIn('Becomes a tie without scalability', t)

    def test_profile_table_marks_tied_cells_at_100_and_500(self):
        t = self.get('/optimization?n=100')
        self.assertIn('no difference (all 8 tied)', t)
        self.assertIn('rb-tied', t)

    def test_exports(self):
        self.assertIn('robustness_grid', self.get('/api/robustness.csv'))
        self.assertIn('"headline"', self.get('/api/robustness.json'))
        allcsv = self.get('/api/export/all.csv')
        self.assertIn('robustness_grid', allcsv)
        self.assertIn('inference', allcsv)                      # existing datasets still present

    def test_pages_make_no_external_requests(self):
        for url in ('/robustness', '/optimization', '/sensitivity', '/'):
            t = self.get(url)
            for ref in re.findall(r'(?:src|href)="(https?://[^"]+)"', t):
                self.fail(f'{url} references external resource {ref}')
            self.assertNotIn('cdn.', t)


if __name__ == '__main__':
    unittest.main()
