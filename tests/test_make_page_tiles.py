from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import make_page_tiles  # noqa: E402


class MakePageTilesTests(unittest.TestCase):
    def test_four_tiles_cover_zone_with_exact_overlap(self):
        boxes = make_page_tiles.vertical_tiles((10, 100, 210, 1100), 4, 40)
        self.assertEqual(boxes[0], (10, 100, 210, 370))
        self.assertEqual(boxes[-1], (10, 830, 210, 1100))
        for previous, following in zip(boxes, boxes[1:]):
            self.assertEqual(previous[3] - following[1], 40)

    def test_rejects_invalid_box(self):
        with self.assertRaises(make_page_tiles.TileConfigError):
            make_page_tiles.validate_box((0, 0, 101, 100), (100, 100))

    def test_rejects_excessive_overlap(self):
        with self.assertRaises(make_page_tiles.TileConfigError):
            make_page_tiles.vertical_tiles((0, 0, 100, 100), 4, 25)


if __name__ == "__main__":
    unittest.main()
