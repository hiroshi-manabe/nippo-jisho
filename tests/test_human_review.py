import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_human_review.py"
REVIEW = ROOT / "pilot" / "human-review" / "review-status.json"
TRIAL = ROOT / "pilot" / "format-v1-trial"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_human_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class HumanReviewTests(unittest.TestCase):
    def test_review_record_has_six_pending_units(self):
        module = load_module()
        record = module.load_review_record(REVIEW)
        self.assertEqual([page["id"] for page in record["pages"]], ["bnf-f0249", "bnf-f0250"])
        self.assertEqual(
            [unit["status"] for page in record["pages"] for unit in page["units"].values()],
            ["pending"] * 6,
        )

    def test_generator_builds_side_by_side_interface(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            masters = temporary / "masters"
            output = temporary / "output"
            masters.mkdir()
            for name in ("f0249.jpg", "f0250.jpg"):
                Image.new("RGB", (240, 320), "#eee3cc").save(masters / name, "JPEG")
            tile_config = temporary / "tiles.json"
            tile_config.write_text(
                json.dumps(
                    {
                        "format": "nippo-tile-config",
                        "format_version": 0,
                        "pages": [
                            {
                                "id": page,
                                "zones": [
                                    {"id": "column-1", "box": [10, 10, 120, 300]},
                                    {"id": "column-2", "box": [120, 10, 230, 300]},
                                ],
                            }
                            for page in ("bnf-f0249", "bnf-f0250")
                        ],
                    }
                ),
                encoding="utf-8",
            )
            count = module.generate(REVIEW, TRIAL, tile_config, masters, output)
            self.assertEqual(count, 6)
            document = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('class="comparison"', document)
            self.assertIn("Muragari vgoqu.", document)
            self.assertIn("Show Markdown", document)
            self.assertIn("Download session summary", document)
            self.assertIn("hashchange", document)
            self.assertEqual(len(list((output / "assets").glob("*.jpg"))), 6)

    def test_checked_unit_requires_provenance(self):
        module = load_module()
        record = json.loads(REVIEW.read_text(encoding="utf-8"))
        record["pages"][0]["units"]["column-1"]["status"] = "checked"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(module.HumanReviewError):
                module.load_review_record(path)


if __name__ == "__main__":
    unittest.main()
