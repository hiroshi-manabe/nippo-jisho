import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_o_mark_ngram", ROOT / "scripts" / "evaluate_o_mark_ngram.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class OMarkNgramTest(unittest.TestCase):
    def test_encode_text_uses_one_explicit_space_token(self):
        self.assertEqual(
            ["V", "ô", "q", "i", "n", "a", "▁", "m", "o", "n", "o"],
            MODULE.encode_text("Vôqina   mono"),
        )

    def test_word_signature_masks_both_mark_shapes(self):
        tokens = MODULE.encode_text("Daiuǒ. Vôqina vǒ.")
        index = tokens.index("ô")
        self.assertEqual(("Vôqina", "VOqina"), MODULE.word_at(tokens, index))

    def test_normalized_run_collapses_whitespace_and_uses_nfc(self):
        self.assertEqual("Vôqina mono", MODULE.normalized_run(" Vôqina\n mono "))

    def test_confidence_curve_abstains_below_margin(self):
        records = [
            {
                "truth": "ô",
                "prediction": "ô",
                "score_circumflex": -1.0,
                "score_caron": -2.0,
            },
            {
                "truth": "ǒ",
                "prediction": "ô",
                "score_circumflex": -1.0,
                "score_caron": -1.1,
            },
        ]
        point = MODULE.confidence_curve(records, thresholds=(0.5,))[0]
        self.assertEqual(point["retained"], 1)
        self.assertEqual(point["correct"], 1)
        self.assertEqual(point["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
