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

    def test_f46_displaced_bottom_right_continuation_has_its_own_crop(self):
        geometry = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in geometry["pages"] if page["id"] == "bnf-f0046")
        column = page["columns"]["column-2"]
        crop = column["lines"]["c2-l047"]["crop"]

        self.assertEqual(
            column["review_source"],
            "pilot/human-review/ai-geometry-work/bnf-f0046-centered-rereviewed.json",
        )
        self.assertEqual(crop, [1445, 3290, 1206, 108])

        transcription = json.loads(
            (
                ROOT
                / "pilot"
                / "format-v1-trial"
                / "level1"
                / "bnf-f0046.json"
            ).read_text(encoding="utf-8")
        )
        zones = {zone["id"]: zone for zone in transcription["zones"]}
        final_line = zones["column-2"]["lines"][-1]
        self.assertEqual(final_line["id"], "c2-l047")
        self.assertEqual(final_line["indent"], 1)
        self.assertEqual(
            final_line["runs"], [{"typeface": "italic", "text": "poſito"}]
        )
        self.assertNotIn("catchword", zones)


if __name__ == "__main__":
    unittest.main()
