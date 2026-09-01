import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "collect_calamari_predictions.py"


class CollectCalamariPredictionsTest(unittest.TestCase):
    def test_collects_the_requested_split_in_manifest_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = root / "records.jsonl"
            rows = [
                {
                    "id": "bnf-f0001/c1-l001",
                    "split": "dev",
                    "image": "dev/bnf-f0001__c1-l001.png",
                },
                {
                    "id": "bnf-f0002/c1-l001",
                    "split": "test",
                    "image": "test/bnf-f0002__c1-l001.png",
                },
            ]
            records.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            predictions = root / "predictions"
            predictions.mkdir()
            (predictions / "bnf-f0001__c1-l001.pred.txt").write_text(
                "Gǒyô.\n", encoding="utf-8"
            )
            output = root / "dev.jsonl"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--records",
                    str(records),
                    "--split",
                    "dev",
                    "--prediction-dir",
                    str(predictions),
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                {"id": "bnf-f0001/c1-l001", "text": "Gǒyô."},
            )


if __name__ == "__main__":
    unittest.main()
