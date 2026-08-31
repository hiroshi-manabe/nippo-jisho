import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_o_mark_fusion", ROOT / "scripts" / "evaluate_o_mark_fusion.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class OMarkFusionTest(unittest.TestCase):
    def test_alignment_map_handles_substitution_and_deletion(self):
        self.assertEqual(["V", "ǒ", "q"], MODULE.alignment_map("Vôq", "Vǒq"))
        self.assertEqual(["V", None, "q"], MODULE.alignment_map("Vôq", "Vq"))

    def test_occurrence_id_is_stable(self):
        self.assertEqual(
            "bnf-f0151/c1-l001/r0/t1",
            MODULE.occurrence_id(
                {
                    "page_id": "bnf-f0151",
                    "line_id": "c1-l001",
                    "run_index": 0,
                    "token_index": 1,
                }
            ),
        )

    def test_asymmetric_rule_only_overrides_weak_circumflex_prediction(self):
        records = [
            {"ngram_delta": 0.2, "ocr_delta": -2.0},
            {"ngram_delta": 0.8, "ocr_delta": -2.0},
            {"ngram_delta": -0.2, "ocr_delta": 2.0},
        ]
        self.assertEqual(
            ["ǒ", "ô", "ǒ"],
            MODULE.asymmetric_predictions(
                records,
                ocr_feature="ocr_delta",
                ocr_threshold=1.5,
                lm_maximum=0.5,
            ),
        )


if __name__ == "__main__":
    unittest.main()
