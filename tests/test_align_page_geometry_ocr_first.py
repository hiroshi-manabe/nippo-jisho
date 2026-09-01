import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from align_page_geometry_ocr_first import (  # noqa: E402
    comparison_text,
    ordered_targets,
    rescue_sandwiched_gaps,
    sequence_alignment,
    split_candidates,
)


class OcrFirstGeometryTests(unittest.TestCase):
    def test_ordered_targets_uses_document_order_without_geometry(self):
        page = {
            "zones": [
                {"id": "header-column-1", "kind": "running_header", "lines": []},
                {
                    "id": "column-1",
                    "kind": "column",
                    "lines": [
                        {"id": "c1-l002", "runs": [{"text": " second "}]},
                        {"id": "c1-l001", "runs": [{"text": "first"}]},
                    ],
                },
            ]
        }
        targets = ordered_targets(page)
        self.assertEqual([line["id"] for line in targets["column-1"]], ["c1-l002", "c1-l001"])
        self.assertEqual(targets["column-1"][0]["text"], "second")

    def test_split_candidates_uses_only_page_half_and_baseline_order(self):
        segmentation = {
            "lines": [
                {"id": "right", "baseline": [[70, 10], [90, 10]]},
                {"id": "left-late", "baseline": [[10, 30], [30, 30]]},
                {"id": "left-early", "baseline": [[10, 20], [30, 20]]},
            ]
        }
        result = split_candidates(segmentation, 100)
        self.assertEqual([line["id"] for line in result["column-1"]], ["left-early", "left-late"])
        self.assertEqual([line["id"] for line in result["column-2"]], ["right"])

    def test_comparison_normalization_ignores_review_only_glyph_distinctions(self):
        self.assertEqual(comparison_text("Vôqiſa, Jũto."), "uoqisaiuto")

    def test_sequence_alignment_skips_furniture_candidate(self):
        references = [{"text": "abc"}, {"text": "def"}]
        candidates = [
            {"recognition": "header"},
            {"recognition": "abc"},
            {"recognition": "def"},
        ]
        alignment = sequence_alignment(
            references,
            candidates,
            gap_cost=0.55,
            position_cost=0.0,
            maximum_displacement=4,
        )
        self.assertEqual(alignment, [(None, 0), (0, 1), (1, 2)])

    def test_sandwiched_garbled_line_is_positionally_rescued(self):
        alignment = [(0, 0), (1, None), (None, 1), (2, 2)]
        result, rescued = rescue_sandwiched_gaps(alignment, 3, 3)
        self.assertEqual(result, [(0, 0), (1, 1), (2, 2)])
        self.assertEqual(rescued, [(1, 1)])

    def test_multiple_gap_is_not_positionally_rescued(self):
        alignment = [(0, 0), (1, None), (2, None), (None, 1), (None, 2), (3, 3)]
        result, rescued = rescue_sandwiched_gaps(alignment, 4, 4)
        self.assertEqual(result, alignment)
        self.assertEqual(rescued, [])


if __name__ == "__main__":
    unittest.main()
