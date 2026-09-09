import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh_unreviewed_ocr import associate, protected_pages
from build_public_review import is_fresh_machine_draft


class RefreshTests(unittest.TestCase):
    def test_historical_human_pages_are_protected(self):
        protected=protected_pages()
        self.assertTrue(all(f'bnf-f{n:04d}' in protected for n in range(13,201)))
        self.assertTrue(all(f'bnf-f{n:04d}' in protected for n in (248,249,250)))
        self.assertNotIn('bnf-f0201',protected)

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
