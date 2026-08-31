import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_clean_ocr_pairs  # noqa: E402


class CleanOcrPairTests(unittest.TestCase):
    def test_block_name_preserves_structural_subcolumn(self):
        self.assertEqual(build_clean_ocr_pairs.block_name("c2b-l014"), "c2b")
        self.assertEqual(build_clean_ocr_pairs.block_name("c1-l003"), "c1")

    def test_isolated_crop_uses_neighbour_midpoints(self):
        line = {"centre_y": 160, "crop": [80, 100, 1100, 120]}
        previous = {"centre_y": 100}
        following = {"centre_y": 220}
        self.assertEqual(
            build_clean_ocr_pairs.isolated_crop(
                line,
                previous,
                following,
                fallback_gap=60,
                source_height=1000,
                padding=10,
            ),
            [80, 120, 1100, 80],
        )

    def test_high_recall_crop_can_expand_beyond_review_rectangle(self):
        line = {"centre_y": 160, "crop": [80, 140, 1100, 60]}
        previous = {"centre_y": 100}
        following = {"centre_y": 220}
        self.assertEqual(
            build_clean_ocr_pairs.isolated_crop(
                line,
                previous,
                following,
                fallback_gap=60,
                source_height=1000,
                padding=10,
                respect_review_crop=False,
            ),
            [80, 120, 1100, 80],
        )

    def test_visual_metrics_find_a_single_straight_band(self):
        array = np.full((60, 240), 255, dtype=np.uint8)
        array[22:34, 20:220] = 0
        metrics, reasons, band = build_clean_ocr_pairs.visual_metrics(
            Image.fromarray(array), "abcdefghij", target_center_y=28
        )
        self.assertEqual(reasons, [])
        self.assertEqual(band, (21, 35))
        self.assertAlmostEqual(metrics["skew_degrees"], 0.0)

    def test_high_recall_profile_keeps_a_short_legible_band(self):
        array = np.full((60, 240), 255, dtype=np.uint8)
        array[22:34, 20:40] = 0
        image = Image.fromarray(array)
        _, strict_reasons, _ = build_clean_ocr_pairs.visual_metrics(
            image, "a", target_center_y=28
        )
        _, recall_reasons, _ = build_clean_ocr_pairs.visual_metrics(
            image, "a", target_center_y=28, high_recall=True
        )
        self.assertIn("skew_unmeasurable", strict_reasons)
        self.assertEqual(recall_reasons, [])


if __name__ == "__main__":
    unittest.main()
