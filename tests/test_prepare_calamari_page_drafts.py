import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_calamari_page_drafts import (  # noqa: E402
    executable_command,
    inferred_column_band,
    position_alignment,
    split_candidates,
)


class PrepareCalamariPageDraftTests(unittest.TestCase):
    def test_arm64_workspace_runtime_is_forced_native_on_macos(self):
        from unittest.mock import patch

        with patch("prepare_calamari_page_drafts.platform.system", return_value="Darwin"):
            self.assertEqual(
                executable_command(Path("venv-arm64/bin/tool"), "arg"),
                ["arch", "-arm64", "venv-arm64/bin/tool", "arg"],
            )

    def test_split_candidates_uses_page_half_then_scan_order(self):
        segmentation = {
            "lines": [
                {"id": "r", "baseline": [[70, 15], [90, 15]]},
                {"id": "l2", "baseline": [[10, 25], [30, 25]]},
                {"id": "l1", "baseline": [[10, 10], [30, 10]]},
            ]
        }
        result = split_candidates(segmentation, (100, 100))
        self.assertEqual([line["source_id"] for line in result["column-1"]], ["l1", "l2"])
        self.assertEqual(result["column-1"][0]["id"], "column-1-k001")
        self.assertEqual([line["source_id"] for line in result["column-2"]], ["r"])

    def test_inferred_column_band_ignores_short_furniture(self):
        candidates = [
            {"baseline": [[100, 10], [800, 10]]},
            {"baseline": [[110, 20], [790, 20]]},
            {"baseline": [[5, 30], [15, 30]]},
        ]
        left, right = inferred_column_band(candidates, (1000, 1000), padding=20)
        self.assertEqual((left, right), (80, 821))

    def test_position_alignment_skips_header_and_footer_without_using_text(self):
        references = [{"centre_y": 100}, {"centre_y": 160}]
        candidates = [
            {"centre_y": 30, "text": "same as reference"},
            {"centre_y": 102, "text": "wrong"},
            {"centre_y": 158, "text": "wrong"},
            {"centre_y": 230, "text": "same as reference"},
        ]
        self.assertEqual(
            position_alignment(references, candidates, maximum_distance=30),
            [(None, 0), (0, 1), (1, 2), (None, 3)],
        )

    def test_position_alignment_reports_missing_row(self):
        references = [
            {"centre_y": 100},
            {"centre_y": 160},
            {"centre_y": 220},
        ]
        candidates = [{"centre_y": 101}, {"centre_y": 219}]
        self.assertEqual(
            position_alignment(references, candidates, maximum_distance=30),
            [(0, 0), (1, None), (2, 1)],
        )


if __name__ == "__main__":
    unittest.main()
