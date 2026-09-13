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



if __name__ == "__main__":
    unittest.main()
