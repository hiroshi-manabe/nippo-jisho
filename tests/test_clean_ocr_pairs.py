import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_clean_ocr_pairs  # noqa: E402
import apply_kraken_supplement  # noqa: E402


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

    def test_normalized_line_is_idempotent_at_model_height(self):
        array = np.full((67, 260), 255, dtype=np.uint8)
        array[20:48, 40:215] = 0
        once = build_clean_ocr_pairs.normalized_line(
            Image.fromarray(array), height=48, max_width=1024
        )
        twice = build_clean_ocr_pairs.normalized_line(
            once, height=48, max_width=1024
        )
        self.assertEqual(once.size, twice.size)
        np.testing.assert_array_equal(np.asarray(once), np.asarray(twice))

    def test_kraken_supplement_preserves_identity_and_replaces_geometry(self):
        base = {
            "id": "bnf-f0013/c1-l001",
            "text": "A NOME",
            "review_crop": [1, 2, 3, 4],
            "reasons": ["isolated_crop_recognition_mismatch"],
        }
        match = {
            "kraken_crop": [10, 20, 30, 40],
            "kraken_baseline": [[10, 50], [40, 50]],
            "kraken_boundary": [[10, 20], [40, 60]],
            "kraken_width": 300,
            "kraken_height": 48,
            "kraken_sha256": "abc",
            "recognition": "A NOME",
            "recognition_cer": 0.0,
            "alignment_displacement": 1,
            "kraken_candidate_id": "bnf-f0013/column-1-k001",
        }
        pair = apply_kraken_supplement.supplemental_pair(
            base, match, "kraken-images/bnf-f0013/c1-l001.png"
        )
        self.assertEqual(pair["id"], base["id"])
        self.assertEqual(pair["source_crop"], match["kraken_crop"])
        self.assertEqual(pair["quality_tier"], "kraken-rectified")
        self.assertNotIn("reasons", pair)


if __name__ == "__main__":
    unittest.main()
