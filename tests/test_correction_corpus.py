import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "pilot" / "correction-corpus" / "f0013-f0016.tsv"


class CorrectionCorpusTest(unittest.TestCase):
    def test_schema_ids_and_values(self):
        with CORPUS.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))

        self.assertEqual(len(rows), 97)
        self.assertEqual(
            list(rows[0]),
            [
                "event_id", "page", "line", "phase", "step", "before", "after",
                "outcome", "finder", "categories", "provenance", "note",
            ],
        )
        self.assertEqual(len({row["event_id"] for row in rows}), len(rows))

        allowed_outcomes = {"accepted", "intermediate", "reverted", "rejected"}
        for row in rows:
            self.assertRegex(row["event_id"], r"^f1[3-6]-\d{3}$")
            self.assertIn(row["page"], {"f0013", "f0014", "f0015", "f0016"})
            self.assertTrue(row["line"])
            self.assertGreaterEqual(int(row["step"]), 1)
            self.assertNotEqual(row["before"], row["after"])
            self.assertIn(row["outcome"], allowed_outcomes)
            self.assertTrue(row["categories"])
            self.assertTrue(row["provenance"])


if __name__ == "__main__":
    unittest.main()
