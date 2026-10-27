"""Plain-language layer of the Optimisation page: answer-first sentence, confidence badge, quick choices,
glossary. These only re-state results that evaluate_four already returned; the tests check the wording
stays faithful to them (no new claims) and that no score, order or winner moves."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dashboard'))
import optimization as opt
import robustness as rb

LOWMEM = dict(inference=0, memory=100, scalability=0, accuracy=0)


def answered(n, weights=None, norm='minmax'):
    res = opt.evaluate_four(n, weights, normalisation=norm)
    rb.decorate(res, n, weights, None, norm)
    return res, rb.answer(res)


class TestAnswer(unittest.TestCase):
    def test_tie_is_reported_as_tie(self):
        _, a = answered(500, LOWMEM)
        self.assertEqual((a['level'], a['badge']), ('tie', 'Tie'))
        self.assertIn('snnTorch ties with Brian2 (Cython)', a['lead'])
        self.assertIn('shorter runtime', a['lead'])

    def test_all_tied_cannot_separate(self):
        _, a = answered(100, LOWMEM)
        self.assertEqual(a['level'], 'tie')
        self.assertIn('all 8 eligible backends have exactly the same score', a['lead'])

    def test_change_under_share_is_flagged_with_plain_names(self):
        _, a = answered(5000)
        self.assertEqual(a['level'], 'depends')
        self.assertEqual(a['badge'], 'Depends on a setting')
        self.assertIn('Brian2 (NumPy)', a['lead'])
        self.assertTrue(any('Changes to Brian2 (Cython) under share-of-total' in n for n in a['notes']))
        self.assertTrue(any('not a significance test' in n for n in a['notes']))

    def test_becomes_tie_wording_is_kept(self):
        _, a = answered(500, dict(inference=0, memory=50, scalability=50, accuracy=0))
        self.assertTrue(any(n.startswith('Becomes a tie without scalability') for n in a['notes']))
        self.assertEqual(a['level'], 'depends')

    def test_holds_when_nothing_changes(self):
        _, a = answered(1000)
        self.assertEqual(a['level'], 'holds')
        self.assertIn('snnTorch', a['lead'])
        self.assertTrue(any('The same answer holds' in n for n in a['notes']))

    def test_close_call_is_labelled_not_upgraded(self):
        _, a = answered(10000)                      # same under every live check, margin 0.0019
        self.assertEqual(a['level'], 'holds')
        self.assertTrue(a['close'])
        self.assertIn('(close call)', a['badge'])

    def test_exploratory_note_when_accuracy_weighted(self):
        _, a = answered(500, dict(inference=50, memory=0, scalability=0, accuracy=50))
        self.assertTrue(any(n.startswith('Exploratory') for n in a['notes']))

    def test_no_overclaiming_words(self):
        for n in rb.SIZES:
            for w in (None, LOWMEM):
                _, a = answered(n, w)
                text = ' '.join([a['lead'], a['badge']] + a['notes']).lower()
                for bad in ('significant', 'universal', 'proves', 'definitely', 'always'):
                    self.assertNotIn(bad, text.replace('not a significance test', ''), (n, bad))

    def test_answer_changes_nothing_in_the_selection(self):
        for n in rb.SIZES:
            res = opt.evaluate_four(n)
            rb.decorate(res, n, None, None, 'minmax')
            snap = copy.deepcopy([(r['id'], r['score']) for r in res['rows']])
            rb.answer(res)
            self.assertEqual(snap, [(r['id'], r['score']) for r in res['rows']])


class TestPresetsAndTerms(unittest.TestCase):
    def test_presets_are_existing_profiles(self):
        by = {k: w for k, _, w in opt.PROFILES}
        for p in rb.presets():
            self.assertEqual(p['weights'], by[p['key']])
        self.assertEqual([p['label'] for p in rb.presets()],
                         ['I need it fast', 'I need low memory', 'Fast and low memory', 'Balanced', 'Accuracy matters (exploratory)'])
        self.assertEqual(next(p for p in rb.presets() if p['key'] == 'balanced')['weights'], opt.DEFAULT_WEIGHTS)
        self.assertEqual([p['exploratory'] for p in rb.presets()], [False, False, False, False, True])

    def test_friendly_names_cover_eligible_backends(self):
        names = dict(rb.names())
        self.assertEqual(len(names), 8)
        self.assertEqual(len(set(names.values())), 8)
        self.assertEqual(names['nest/threads1'], 'NEST (1 thread)')
        self.assertEqual(names['nest/threads4'], 'NEST (4 threads)')

    def test_glossary_covers_the_technical_terms(self):
        terms = ' '.join(t for t, _ in rb.GLOSSARY).lower()
        for needle in ('memory growth', 'exponent', 'accuracy', 'min–max', 'score', 'tie rule', 'pareto', 'priority grid', 'rank sum'):
            self.assertIn(needle, terms)
        grid = dict(rb.GLOSSARY)['Priority grid']
        self.assertIn('not a probability', grid)


try:
    import flask  # noqa: F401
    import app as dashboard_app
except Exception:                                    # pragma: no cover
    dashboard_app = None


@unittest.skipIf(dashboard_app is None, 'Flask not installed')
class TestPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = dashboard_app.app.test_client()
        cls.page = cls.c.get('/optimization?n=5000').data.decode()

    def test_answer_comes_before_the_controls(self):
        self.assertLess(self.page.index('id="optAnswerCard"'), self.page.index('id="multiOptForm"'))
        self.assertEqual(self.page.count('id="optAnswerCard"'), 1)

    def test_quick_choices_present_and_valid(self):
        buttons = re.findall(r"class=\"rb-preset\" data-preset='([^']+)'", self.page)
        self.assertEqual(len(buttons), 5)
        for b in buttons:
            w = json.loads(b.replace('&#34;', '"'))
            self.assertEqual(set(w), set(opt.CRITERIA))

    def test_fragment_carries_the_answer_first(self):
        t = self.c.get('/api/optimization/fragment?n=500&inference=0&memory=100&scalability=0&accuracy=0').data.decode()
        self.assertTrue(t.lstrip().startswith('<div id="optAnswerCard"'))
        self.assertIn('Tie', t)

    def test_glossary_and_names_present(self):
        self.assertIn('Terms used on this page', self.page)
        self.assertIn('nest/threads4</code> = NEST (4 threads)', self.page)

    def test_original_claims_still_on_the_page(self):
        for phrase in ('not a weight', 'exploratory cross-paradigm scenario', 'not simulator acceleration',
                       'illustrative starting values', 'not established or elicited research preferences'):
            self.assertIn(phrase, self.page)
        self.assertIn('score difference, not a significance test', self.page)

    def test_recommended_backend_unchanged(self):
        self.assertIn(opt.evaluate_four(5000)['winner']['id'], self.page)
        self.assertRegex(self.page, r'class="opt-winner">brian2/numpy\s')


@unittest.skipIf(dashboard_app is None, 'Flask not installed')
class TestReviewerGuide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = dashboard_app.app.test_client()
        cls.home = cls.c.get('/').data.decode()

    def test_home_has_reading_path_in_order(self):
        self.assertIn('Start here: a four-step reading path', self.home)
        order = [self.home.index(x) for x in ('Ask: Which simulator', 'Check: How far', 'Look: Where do', 'Know the limits: What')]
        self.assertEqual(order, sorted(order))
        for href in ('/optimization', '/robustness', '/inference', '/about'):
            self.assertIn(f'href="{href}"', self.home)

    def test_takeaways_are_computed_from_the_data(self):
        t = ' '.join(x['text'] for x in rb.takeaways())
        self.assertIn('fastest backend at 100 neurons is NEST (its thread counts are not separated', t)
        self.assertIn('Brian2 (Cython) has the lowest median runtime', t)
        self.assertIn('2.38× slower', t)
        self.assertIn('75.5× slower', t)
        self.assertIn('26 of 45', t)
        self.assertNotIn(' ms)', t)                                       # no absolute runtime quoted at 100 neurons
        self.assertIn('less than 1 ms behind', t)
        self.assertIn('Reusing', self.home)

    def test_start_here_sits_next_to_backend_detail_and_shares_its_area(self):
        pages = ('/', '/optimization', '/robustness', '/inference', '/sensitivity', '/about')
        for url in pages:
            t = self.c.get(url).data.decode()
            self.assertLess(t.index('id="guideBtn"'), t.index('id="detailBtn"'), url)           # side by side in the bar
            self.assertIn('aria-controls="guidePanel"', t, url)
            self.assertRegex(t, r'id="guidePanel" hidden', url)                                    # closed by default
            self.assertRegex(t, r'id="backendPanel" hidden', url)
            self.assertLess(t.index('id="backendPanel"'), t.index('id="guidePanel"'), url)        # same area, one below the other
            self.assertLess(t.index('id="guidePanel"'), t.index('class="page-content"'), url)
            self.assertIn('Start here: a four-step reading path', t, url)
        self.assertNotIn('id="startHere"', self.home)                                              # no separate card on Home any more

    def test_guide_script_makes_the_two_panels_exclusive(self):
        js = (Path(__file__).resolve().parents[1] / 'dashboard' / 'static' / 'js' / 'dashboard.js').read_text()
        self.assertIn('getElementById("guideBtn")', js)
        self.assertIn('other === item ? open : false', js)
        self.assertIn('show: "Guide Open &#9662;", hide: "Guide Close &#9652;"', js)
        self.assertIn('Guide Open &#9662;</button>', self.home)             # closed-state label in the page

    def test_page_still_renders_if_the_takeaways_fail(self):
        from unittest import mock
        with mock.patch.object(rb, 'takeaways', side_effect=RuntimeError('boom')):
            r = self.c.get('/')
        self.assertEqual(r.status_code, 200)
        t = r.data.decode()
        self.assertIn('Start here: a four-step reading path', t)
        self.assertNotIn('Three things to take away', t)

    def test_takeaways_state_their_limits(self):
        self.assertIn('one machine and one workload', self.home)

    def test_robustness_page_leads_with_a_sentence(self):
        t = self.c.get('/robustness').data.decode()
        self.assertIn('26 of 45 recommendations hold under every check. The other 19 depend on something', t)
        self.assertLess(t.index('class="rb-lead"'), t.index('id="robustnessGrid"'))

    def test_optimisation_plain_words_and_friendly_winner(self):
        t = self.c.get('/optimization?n=5000').data.decode()
        self.assertEqual(t.count('In plain words:'), 4)   # + softmax priority card
        self.assertIn('<span class="rb-friendly">Brian2 (NumPy)</span>', t)
        self.assertIn('not only these two axes', t)           # Pareto note matches METHOD_RULES rule 23


if __name__ == '__main__':
    unittest.main()
