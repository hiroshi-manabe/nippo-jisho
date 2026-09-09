import unittest
from scripts.expand_ss_review import expand


class DoubleSReviewTests(unittest.TestCase):
    def setUp(self):
        self.manifest = dict(baseline='frozen', commit='abc', page_versions={'13':'v1'},
            items=[dict(leaf=13, line='c1-l001', text='aſſ bſſ', position=p) for p in [1, 5]])
        self.payload = dict(format='nippo-italic-ss-review', version=1,
                            baseline='frozen', total=2, default='ß', keep=[])

    def test_multiple_occurrences_do_not_shift_positions(self):
        changes = expand(self.payload, self.manifest)['pages'][0]['changes']
        self.assertEqual(changes, [dict(line='c1-l001', before='aſſ bſſ', after='aß bß')])

    def test_checked_exception_stays_double_long(self):
        self.payload['keep'] = [1]
        self.assertEqual(expand(self.payload, self.manifest)['pages'][0]['changes'][0]['after'], 'aß bſſ')

    def test_invalid_exports_rejected(self):
        for field, value in [('keep', [True]), ('keep', [2]), ('keep', [0,0]),
                             ('baseline','changed'), ('total',3), ('version',2)]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                expand({**self.payload, field:value}, self.manifest)

    def test_scope_guard(self):
        self.manifest['items'][0]['leaf'] = 201
        with self.assertRaises(ValueError):
            expand(self.payload, self.manifest)

    def test_ligature_keeps_italic_style(self):
        from scripts.process_correction_issue import apply_change, apply_resolved
        line = dict(id='c1-l001', runs=[dict(typeface='italic', text='aſſ bſſ')])
        change = expand(self.payload, self.manifest)['pages'][0]['changes'][0]
        item, _ = apply_change(line, change)
        apply_resolved(line, item)
        self.assertEqual(line['runs'], [dict(typeface='italic', text='aß bß')])
