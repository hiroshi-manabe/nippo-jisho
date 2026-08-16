import json
from pathlib import Path
import unittest

from scripts.recheck_external_geometry_width import horizontal_bounds


ROOT = Path(__file__).resolve().parents[1]


class ExternalGeometryWidthTests(unittest.TestCase):
    def test_existing_audited_bounds_are_reused_without_drift(self):
        page = {
            "source_size": [2721, 3893],
            "columns": {
                "column-1": {
                    "box": [300, 300, 1505, 3410],
                    "horizontal_completeness_review": {
                        "status": "complete_column_width_checked",
                        "audited_box": [300, 300, 1505, 3410],
                    },
                },
                "column-2": {
                    "box": [1445, 300, 2651, 3410],
                    "horizontal_completeness_review": {
                        "status": "complete_column_width_checked",
                        "audited_box": [1445, 300, 2651, 3410],
                    },
                },
            },
        }

        self.assertEqual(
            horizontal_bounds(page),
            {"column-1": (300, 1505), "column-2": (1445, 2651)},
        )

    def test_f46_displaced_bottom_right_continuation_is_visible(self):
        geometry = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in geometry["pages"] if page["id"] == "bnf-f0046")
        column = page["columns"]["column-2"]
        crop = column["lines"]["c2-l046"]["crop"]

        self.assertEqual(
            column["review_source"],
            "pilot/human-review/ai-geometry-work/bnf-f0046-centered-rereviewed.json",
        )
        self.assertGreaterEqual(crop[3], 180)


if __name__ == "__main__":
    unittest.main()
