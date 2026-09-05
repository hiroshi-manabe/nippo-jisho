import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_clipping_campaign import fingerprint, propose
from audit_ocr_layout_geometry import align_audit_rows


class ClippingProposalTests(unittest.TestCase):
    def test_extra_marginal_detections_do_not_force_wrong_rows(self):
        texts = ['alpha first body row', 'bravo second body row', 'charlie last body row']
        references = [{'text': t} for t in texts]
        candidates = [{'recognition': 'unrelated marginal scribble'} for _ in range(18)]
        candidates += [{'recognition': t} for t in texts]
        matches = [(i, j) for i, j in align_audit_rows(references, candidates)
                   if i is not None and j is not None]
        self.assertEqual(matches, [(0, 18), (1, 19), (2, 20)])

    def setUp(self):
        self.line = {'crop': [20, 40, 100, 30], 'centre_y': 55,
                     'context_crop': [20, 10, 100, 100]}
        self.match = {'relaxed_cer': .05, 'flags': ['vertical_clip'],
                      'detected_bbox': [25, 30, 70, 55], 'ocr_centre_y': 56.5}

    def test_union_never_discards_existing_coverage(self):
        result, disposition = propose(self.line, self.match, [200, 200])
        self.assertEqual(result['crop'], [19, 24, 101, 67])
        self.assertEqual(disposition, 'inspect_proposal')
        self.assertEqual(self.line['crop'], [20, 40, 100, 30])

    def test_ambiguous_alignment_is_withheld(self):
        for match in (None, {**self.match, 'relaxed_cer': .4},
                      {**self.match, 'flags': ['vertical_clip', 'neighbor_conflict']}):
            result, disposition = propose(self.line, match, [200, 200])
            self.assertEqual(result, self.line)
            self.assertEqual(disposition, 'manual_alignment_required')

    def test_bounds_are_clamped(self):
        match = {**self.match, 'detected_bbox': [0, 0, 200, 200]}
        result, _ = propose(self.line, match, [200, 200])
        self.assertEqual(result['crop'], [0, 0, 200, 200])
        self.assertEqual(result['context_crop'], [0, 0, 200, 200])

    def test_no_flag_preserves_geometry(self):
        result, disposition = propose(self.line, {**self.match, 'flags': []}, [200, 200])
        self.assertEqual(result, self.line)
        self.assertEqual(disposition, 'inspect_existing')

    def test_fingerprint_detects_geometry_changes(self):
        self.assertEqual(fingerprint({'a': 1, 'b': 2}), fingerprint({'b': 2, 'a': 1}))
        self.assertNotEqual(fingerprint(self.line), fingerprint({**self.line, 'centre_y': 56}))
