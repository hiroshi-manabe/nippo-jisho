import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_ocr_retraining_dataset import styled_text, encode, decode, page_splits


class RetrainingTests(unittest.TestCase):
    def test_text_and_style_errors_are_separated(self):
        from evaluate_ocr_retraining import score
        text = 'aſß'
        styles = ['roman', 'italic', 'italic']
        record = {'id': 'test', 'text': text, 'styles': styles, 'encoded': encode(text, styles)}
        result = score([record], [encode(text, ['roman'] * 3)], True)
        self.assertEqual(result['text']['character_error_rate'], 0)
        self.assertAlmostEqual(result['combined']['character_error_rate'], 2/3)
        self.assertAlmostEqual(result['style']['accuracy'], 1/3)
        self.assertNotIn('style', score([record], [text], False))

    def test_style_round_trip_and_diplomatic_characters(self):
        text, styles = styled_text([
            {'text': ' Fotoqe. ', 'typeface': 'roman'},
            {'text': 'paßa ſſ q̃ ǒ ô Itẽ hũa ', 'typeface': 'italic'}])
        decoded, restored = decode(encode(text, styles))
        self.assertEqual(decoded, text)
        for char, before, after in zip(text, styles, restored):
            if not char.isspace():
                self.assertEqual(before, after)

    def test_page_split_preserves_pretraining_holdouts(self):
        import json
        root = Path(__file__).resolve().parents[1]
        old = json.loads((root / 'experiments/ocr/f13-f150-split.json').read_text())
        splits = page_splits()
        self.assertEqual(len(splits), 188)
        for split in ('dev', 'test'):
            self.assertEqual(sum(s == split for s in splits.values()), 19)
            self.assertTrue(all(splits[n] == split for n in old[split]))
        self.assertEqual(splits, page_splits())


if __name__ == '__main__':
    unittest.main()
