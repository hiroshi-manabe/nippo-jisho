import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_ocr_page_data import (  # noqa: E402
    align_column,
    character_alignment,
    line_text,
    replace_line_text,
)


class BuildOcrPageDataTests(unittest.TestCase):
    def test_alignment_ignores_furniture_and_matches_body_rows(self):
        references = {
            "c1-l001": {"centre_y": 100},
            "c1-l002": {"centre_y": 160},
        }
        candidates = [
            {"id": "header", "centre": [20, 30]},
            {"id": "first", "centre": [20, 112]},
            {"id": "second", "centre": [20, 172]},
            {"id": "footer", "centre": [20, 250]},
        ]
        result = align_column(references, candidates)
        self.assertEqual(result["matches"]["c1-l001"]["id"], "first")
        self.assertEqual(result["matches"]["c1-l002"]["id"], "second")
        self.assertEqual(result["missing"], [])

    def test_character_alignment_retains_every_new_character(self):
        alignment = character_alignment("fiuo narafu", "fauo naraſu")
        self.assertEqual(
            [new for _, new in alignment if new is not None],
            list(range(len("fauo naraſu"))),
        )

    def test_replacement_projects_roman_and_italic_spans(self):
        line = {
            "id": "c1-l001",
            "runs": [
                {"typeface": "roman", "text": "rino fiuo narafu."},
                {"typeface": "italic", "text": " Baterem, ou ſacudirem"},
            ],
        }
        replacement = replace_line_text(
            line, "rino fauo naraſu. Baterem, ou ſacudirẽ"
        )
        self.assertEqual(
            line_text(replacement),
            "rino fauo naraſu. Baterem, ou ſacudirẽ",
        )
        self.assertEqual(replacement["runs"][0]["typeface"], "roman")
        self.assertEqual(replacement["runs"][-1]["typeface"], "italic")
        self.assertTrue(replacement["runs"][-1]["text"].startswith(" Baterem"))

    def test_replacement_preserves_large_initial_layout(self):
        line = {
            "id": "c1-l001",
            "runs": [
                {
                    "typeface": "roman",
                    "text": "F",
                    "layout": "large-initial",
                    "line_span": 2,
                },
                {"typeface": "roman", "text": "ei."},
            ],
        }
        replacement = replace_line_text(line, "Feiq.")
        self.assertEqual(replacement["runs"][0]["layout"], "large-initial")
        self.assertEqual(replacement["runs"][0]["line_span"], 2)
        self.assertEqual(line_text(replacement), "Feiq.")

    def test_replacement_keeps_a_named_far_right_span_single(self):
        line = {
            "id": "c1-l001",
            "runs": [
                {"typeface": "roman", "text": "main"},
                {
                    "typeface": "italic",
                    "text": " aside",
                    "placement": "far-right",
                    "span_id": "word",
                },
            ],
        }
        replacement = replace_line_text(line, "main aside")
        named = [run for run in replacement["runs"] if "span_id" in run]
        self.assertEqual(len(named), 1)
        self.assertEqual(named[0]["span_id"], "word")

    def test_replacement_does_not_erase_a_far_right_cell(self):
        line = {
            "id": "c1-l001",
            "runs": [
                {"typeface": "italic", "text": "pouco."},
                {"typeface": "roman", "text": " Bup"},
                {"typeface": "italic", "text": "."},
                {"typeface": "italic", "text": " ( tardeira.", "placement": "far-right"},
            ],
        }
        replacement = replace_line_text(line, "pouco. Bup.")
        self.assertEqual(line_text(replacement), "pouco. Bup. ( tardeira.")
        self.assertEqual(replacement["runs"][-1]["placement"], "far-right")


if __name__ == "__main__":
    unittest.main()
