import csv
import unicodedata
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPARISON_DIR = ROOT / "pilot" / "wikisource-comparison"
AUDIT = COMPARISON_DIR / "bnf-f0014.csv"
REPORT = COMPARISON_DIR / "bnf-f0014.md"


class WikisourceComparisonTests(unittest.TestCase):
    def setUp(self):
        with AUDIT.open(encoding="utf-8", newline="") as stream:
            self.rows = list(csv.DictReader(stream))

    def test_expected_finding_counts(self):
        self.assertEqual(len(self.rows), 13)
        self.assertEqual(
            Counter(row["incremental_value"] for row in self.rows),
            Counter(
                {
                    "none": 5,
                    "new correction": 4,
                    "confirmation only": 2,
                    "format correction": 1,
                    "format evidence": 1,
                }
            ),
        )

    def test_rows_are_complete_and_ordered(self):
        for sequence, row in enumerate(self.rows, start=1):
            self.assertEqual(row["id"], f"WS-{sequence:03d}")
            for value in row.values():
                self.assertTrue(value)

    def test_report_pins_revision_and_preserves_nfc(self):
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("wikisource_revision: 532710", report)
        self.assertIn("baseline_status: independent_draft_frozen", report)
        for path in (AUDIT, REPORT):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text, unicodedata.normalize("NFC", text))


if __name__ == "__main__":
    unittest.main()
