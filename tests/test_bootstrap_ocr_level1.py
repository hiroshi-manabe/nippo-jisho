import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bootstrap_ocr_level1 import (  # noqa: E402
    TypefaceModel,
    cluster_rows,
    display_heading,
    heading_letter,
    ordinary_two_column_assessment,
    repair_entry_initial,
    resolve_heading_letter,
)


class BootstrapOcrLevel1Tests(unittest.TestCase):
    @staticmethod
    def ordinary_package(column_width=900, body_lines=45):
        lines = [
            {
                "id": f"c1-l{index:03d}",
                "runs": [{"typeface": "roman", "text": "Abc."}],
            }
            for index in range(1, body_lines + 1)
        ]
        second_lines = [
            {
                "id": f"c2-l{index:03d}",
                "runs": [{"typeface": "roman", "text": "Def."}],
            }
            for index in range(1, body_lines + 1)
        ]
        return {
            "page": {
                "zones": [
                    {
                        "kind": "running_header",
                        "lines": [
                            {
                                "id": "running-header-l001",
                                "runs": [
                                    {"typeface": "roman", "text": "A ANTES DO B."}
                                ],
                            }
                        ],
                    },
                    {"kind": "column", "lines": lines},
                    {"kind": "column", "lines": second_lines},
                ]
            },
            "geometry": {
                "columns": {
                    "column-1": {
                        "box": [100, 200, 100 + column_width, 3000],
                        "lines": {line["id"]: {} for line in lines},
                    },
                    "column-2": {
                        "box": [1200, 200, 1200 + column_width, 3000],
                        "lines": {line["id"]: {} for line in second_lines},
                    },
                }
            },
            "audit": {
                "expected_main_letter": "A",
                "columns": {
                    "column-1": {
                        "body_lines": body_lines,
                        "line_spacing": 60,
                        "internal_heading_lines": 0,
                    },
                    "column-2": {
                        "body_lines": body_lines,
                        "line_spacing": 60,
                        "internal_heading_lines": 0,
                    },
                },
            },
        }

    def test_display_heading_requires_display_like_capitals(self):
        self.assertTrue(display_heading("DOS VOCABVLOS QVE CO-"))
        self.assertTrue(display_heading("G ANTES DO A."))
        self.assertFalse(display_heading("antes de correr a carreira."))
        self.assertFalse(display_heading("Cachi. Pollamòr parte, ou frequentemente."))

    def test_duplicate_baselines_keep_one_complete_row(self):
        common = {
            "centre": [100, 500],
            "ocr_crop": [20, 460, 300, 72],
            "baseline": [[30, 500], [300, 500]],
        }
        rows = cluster_rows(
            [
                {**common, "id": "fragment", "text": "texto", "crop": [30, 480, 80, 40]},
                {
                    **common,
                    "id": "complete",
                    "text": "texto da linha",
                    "crop": [30, 480, 270, 40],
                },
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["text"], "texto da linha")
        self.assertEqual(rows[0]["duplicate_candidates"], 1)

    def test_decorated_g_header_confusion_uses_section_context(self):
        self.assertEqual(heading_letter("Ci ANTES DO I."), "C")
        self.assertEqual(resolve_heading_letter("C", "G"), "G")
        self.assertEqual(resolve_heading_letter("I", "G"), "I")
        self.assertEqual(resolve_heading_letter("N", "G"), "G")

    def test_entry_initial_repair_is_limited_to_unindented_lines(self):
        self.assertEqual(
            repair_entry_initial("Cacuguei.", "G", 0),
            ("Gacuguei.", "C→G"),
        )
        self.assertEqual(
            repair_entry_initial("Com muita pressa.", "G", 1),
            ("Com muita pressa.", None),
        )

    def test_typeface_model_separates_seen_lexical_domains(self):
        page = {
            "zones": [
                {
                    "kind": "column",
                    "lines": [
                        {
                            "id": "c1-l001",
                            "runs": [
                                {"typeface": "roman", "text": "Fotoqe."},
                                {"typeface": "italic", "text": " Homem religioso."},
                            ],
                        }
                    ],
                }
            ]
        }
        model = TypefaceModel.train([page] * 8)
        runs, _ = model.runs("Fotoqe. Homem religioso.", indent=0)
        self.assertEqual(runs[0]["typeface"], "roman")
        self.assertEqual(runs[-1]["typeface"], "italic")

    def test_ordinary_page_assessment_accepts_wide_columns(self):
        assessment = ordinary_two_column_assessment(self.ordinary_package())
        self.assertTrue(assessment["eligible_for_provisional_review_queue"])

    def test_ordinary_page_assessment_measures_width_not_right_coordinate(self):
        assessment = ordinary_two_column_assessment(
            self.ordinary_package(column_width=650)
        )
        self.assertFalse(assessment["eligible_for_provisional_review_queue"])
        self.assertIn("column-1:narrow_geometry=650", assessment["reasons"])
        self.assertIn("column-2:narrow_geometry=650", assessment["reasons"])


if __name__ == "__main__":
    unittest.main()
