import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh_unreviewed_ocr import associate, protected_pages
from build_public_review import is_fresh_machine_draft


class RefreshTests(unittest.TestCase):
    def test_human_protection_uses_review_evidence_not_page_numbers(self):
        # Isolate this test from the growing production correction history.
        with TemporaryDirectory() as directory:
            root = Path(directory)
            review = root / 'pilot/human-review'
            review.mkdir(parents=True)
            history = review / 'correction-history.json'
            pages = [
                {'id': 'bnf-f0201', 'issues_applied': 0, 'issues': []},
                {'id': 'bnf-f0202', 'issues_applied': 1},
                {'id': 'bnf-f0203', 'issues': [{'number': 1}]},
            ]
            history.write_text(json.dumps({'pages': pages}))
            (review / 'review-status.json').write_text(json.dumps({'pages': [
                {'id': 'bnf-f0201', 'units': {'column-1': {'status': 'pending'},
                                            'column-2': {}}},
                {'id': 'bnf-f0204', 'units': {'column-1': {'status': 'in_progress'}}},
            ]}))
            reference = root / 'pilot/ocr-bootstrap/reference-f0248-f0250/nested'
            reference.mkdir(parents=True)
            (reference / 'bnf-f0248.json').write_text('{}')

            with patch('refresh_unreviewed_ocr.ROOT', root):
                self.assertEqual(protected_pages(), {
                    'bnf-f0202': 'human_correction_history',
                    'bnf-f0203': 'human_correction_history',
                    'bnf-f0204': 'human_review_unit_touched',
                    'bnf-f0248': 'early_human_trial_reference',
                })
                # Applying an Issue must protect a previously eligible page.
                pages[0]['issues_applied'] = 1
                history.write_text(json.dumps({'pages': pages}))
                self.assertEqual(protected_pages()['bnf-f0201'],
                                 'human_correction_history')

    def test_duplicate_candidate_is_not_forced_into_two_lines(self):
        refs=[{'id':f'l{i}','runs':[{'text':'same word','typeface':'roman'}]} for i in range(2)]
        candidate={'id':'k','centre_y':100,'recognition':'same word'}
        geometry={'lines':{'l0':{'centre_y':100},'l1':{'centre_y':160}}}
        kept,rejected=associate(refs,[candidate],geometry)
        self.assertEqual(len(kept),1)
        self.assertEqual(rejected[0]['reason'],'duplicate_or_nonmonotonic_match')

    def test_decorated_line_is_retained_not_flattened(self):
        ref={'id':'l','runs':[{'text':'A','typeface':'roman','layout':'large-initial'}]}
        kept,rejected=associate([ref],[],{'lines':{'l':{'centre_y':100}}})
        self.assertFalse(kept)
        self.assertEqual(rejected[0]['reason'],'displaced_or_decorated_structure')

    def test_old_review_does_not_certify_replacement(self):
        review={'origin':'calamari_v2_machine_provisional','status':'visual_draft'}
        self.assertTrue(is_fresh_machine_draft({'review':review}))
        self.assertFalse(is_fresh_machine_draft({'review':{**review,'status':'scan_confirmed'}}))


if __name__=='__main__':unittest.main()
