import json
import sys
import unittest
from pathlib import Path

from PIL import Image


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_ocr_dataset  # noqa: E402


class BuildOcrDatasetTests(unittest.TestCase):
    def test_page_split_is_deterministic_and_disjoint(self):
        pages = [f"bnf-f{number:04d}" for number in range(13, 151)]
        first = build_ocr_dataset.split_pages(
            pages, seed=1603, dev_fraction=0.1, test_fraction=0.1
        )
        second = build_ocr_dataset.split_pages(
            pages, seed=1603, dev_fraction=0.1, test_fraction=0.1
        )
        self.assertEqual(first, second)
        self.assertEqual({name: len(items) for name, items in first.items()}, {
            "train": 110,
            "dev": 14,
            "test": 14,
        })
        all_pages = [page for split in first.values() for page in split]
        self.assertEqual(len(all_pages), len(set(all_pages)))
        self.assertEqual(set(all_pages), set(pages))

        recorded = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "experiments"
                / "ocr"
                / "f13-f150-split.json"
            ).read_text(encoding="utf-8")
        )
        for split in ("dev", "test"):
            expected = [f"bnf-f{number:04d}" for number in recorded[split]]
            self.assertEqual(first[split], expected)

    def test_prepared_crop_has_fixed_height_and_keeps_aspect_ratio(self):
        scan = Image.new("L", (400, 100), "white")
        prepared = build_ocr_dataset.prepare_crop(
            scan, [50, 10, 300, 60], height=48, max_width=1024
        )
        self.assertEqual(prepared.size, (240, 48))

if __name__ == "__main__":
    unittest.main()
