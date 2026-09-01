import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_line_ocr_predictions import evaluate  # noqa: E402


class EvaluateLineOcrPredictionsTests(unittest.TestCase):
    def test_diplomatic_features_and_terminal_hyphen(self):
        references = [
            {"id": "a", "text": "coſa-"},
            {"id": "b", "text": "mǒũ."},
        ]
        predictions = [
            {"id": "a", "text": "cosa"},
            {"id": "b", "text": "môu."},
        ]
        result = evaluate(references, predictions)
        self.assertEqual(result["character_errors"], 4)
        self.assertEqual(result["features"]["short_s_or_long_s"]["other_member"], 1)
        self.assertEqual(result["features"]["marked_vowel"]["same_base_wrong_mark"], 2)
        self.assertEqual(result["features"]["tilde_vowel"]["same_base_wrong_mark"], 1)
        self.assertEqual(result["terminal_hyphen"]["false_negative"], 1)

    def test_prediction_ids_must_match(self):
        with self.assertRaisesRegex(ValueError, "prediction ID mismatch"):
            evaluate([{"id": "a", "text": "a"}], [])


if __name__ == "__main__":
    unittest.main()
