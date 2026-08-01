import importlib.util
import json
from pathlib import Path
import shutil
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
    def test_review_record_has_all_transcribed_pages_and_f14_confirmation(self):
        module = load_module()
        record = module.load_review_record(REVIEW)
        self.assertEqual(
            [page["id"] for page in record["pages"]],
            [
                "bnf-f0013",
                "bnf-f0014",
                "bnf-f0015",
                "bnf-f0016",
                "bnf-f0017",
                "bnf-f0018",
                "bnf-f0019",
                "bnf-f0020",
                "bnf-f0021",
                "bnf-f0022",
                "bnf-f0248",
                "bnf-f0249",
                "bnf-f0250",
                "bnf-f0643",
            ],
        )
        states = {
            (page["id"], unit_id): unit["status"]
            for page in record["pages"]
            for unit_id, unit in page["units"].items()
        }
        self.assertEqual(states[("bnf-f0014", "column-1")], "checked")
        self.assertEqual(states[("bnf-f0014", "column-2")], "checked")
        self.assertEqual(states[("bnf-f0015", "column-1")], "needs_correction")
        self.assertEqual(states[("bnf-f0015", "column-2")], "needs_correction")
        self.assertEqual(states[("bnf-f0015", "furniture")], "pending")
        self.assertEqual(states[("bnf-f0016", "column-1")], "needs_correction")
        self.assertEqual(states[("bnf-f0016", "column-2")], "needs_correction")
        self.assertEqual(states[("bnf-f0016", "furniture")], "pending")
        self.assertEqual(states[("bnf-f0017", "column-1")], "pending")
        self.assertEqual(states[("bnf-f0017", "column-2")], "pending")
        self.assertEqual(states[("bnf-f0017", "furniture")], "pending")
        self.assertEqual(
            [
                status
                for key, status in states.items()
                if key[0] not in {"bnf-f0014", "bnf-f0015", "bnf-f0016"}
            ],
            ["pending"] * 33,
        )
        self.assertEqual(states[("bnf-f0014", "furniture")], "checked")

    def test_generator_builds_dictionary_wide_shell(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            masters = temporary / "masters"
            output = temporary / "output"
            trial = temporary / "trial"
            (trial / "level1").mkdir(parents=True)
            (trial / "level1-source").mkdir()
            masters.mkdir()
            for leaf in (249, 250, 251):
                Image.new("RGB", (240, 320), "#eee3cc").save(
                    masters / f"f{leaf:04d}.jpg", "JPEG"
                )
            for page_id in ("bnf-f0249", "bnf-f0250"):
                shutil.copy(TRIAL / "level1" / f"{page_id}.json", trial / "level1")
                shutil.copy(
                    TRIAL / "level1-source" / f"{page_id}.md",
                    trial / "level1-source",
                )

            full_review = json.loads(REVIEW.read_text(encoding="utf-8"))
            full_review["pages"] = [
                page
                for page in full_review["pages"]
                if page["id"] in {"bnf-f0249", "bnf-f0250"}
            ]
            review_path = temporary / "review.json"
            review_path.write_text(json.dumps(full_review), encoding="utf-8")

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

            stats = module.generate(
                review_path, trial, tile_config, masters, output
            )
            self.assertEqual(
                stats, {"pages": 3, "processed": 2, "unprocessed": 1}
            )
            corpus = json.loads((output / "corpus.json").read_text(encoding="utf-8"))
            self.assertEqual(len(corpus["pages"]), 3)
            self.assertEqual(corpus["pages"][2]["status"], "unprocessed")
            f249_column_2 = corpus["pages"][0]["units"]["column-2"]["html"]
            self.assertIn('data-reference="f249/c2-l040"', f249_column_2)
            self.assertIn(
                'data-current="Gunpacu. Icuſano macu. Certas cortinas q̃"',
                f249_column_2,
            )
            self.assertIn('class="line-review"', f249_column_2)
            self.assertIn('data-scan-unit="column-2"', f249_column_2)
            self.assertIn("Show context", f249_column_2)

            document = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Not yet processed", document)
            self.assertIn("Reload latest", document)
            self.assertIn('id="leaf-input"', document)
            self.assertIn("Current: ${button.dataset.current}", document)
            self.assertIn("line-paired-mode", document)
            self.assertIn("Line-by-line comparison", document)
            self.assertIn("async function copyText", document)
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

    def test_master_sequence_must_be_contiguous(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            masters = Path(directory)
            for leaf in (1, 3):
                Image.new("RGB", (10, 10), "white").save(
                    masters / f"f{leaf:04d}.jpg", "JPEG"
                )
            with self.assertRaises(module.HumanReviewError):
                module.discover_masters(masters)


if __name__ == "__main__":
    unittest.main()
