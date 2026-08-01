import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "pilot" / "correction-corpus"
CORPORA = [CORPUS_DIR / "f0013-f0016.tsv", CORPUS_DIR / "f0017.tsv"]


class CorrectionCorpusTest(unittest.TestCase):
    def test_schema_ids_and_values(self):
        rows = []
        schemas = []
        for corpus in CORPORA:
            with corpus.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                schemas.append(reader.fieldnames)
                rows.extend(reader)

        self.assertEqual(len(rows), 106)
        self.assertEqual(
            schemas[0],
            [
                "event_id", "page", "line", "phase", "step", "before", "after",
                "outcome", "finder", "categories", "provenance", "note",
            ],
        )
        self.assertTrue(all(schema == schemas[0] for schema in schemas))
        self.assertEqual(len({row["event_id"] for row in rows}), len(rows))

        allowed_outcomes = {"accepted", "intermediate", "reverted", "rejected"}
        for row in rows:
            self.assertRegex(row["event_id"], r"^f1[3-7]-\d{3}$")
            self.assertIn(row["page"], {"f0013", "f0014", "f0015", "f0016", "f0017"})
            self.assertTrue(row["line"])
            self.assertGreaterEqual(int(row["step"]), 1)
            self.assertNotEqual(row["before"], row["after"])
            self.assertIn(row["outcome"], allowed_outcomes)
            self.assertTrue(row["categories"])
            self.assertTrue(row["provenance"])


if __name__ == "__main__":
    unittest.main()
