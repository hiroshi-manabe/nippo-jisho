import csv
import unicodedata
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "pilot" / "diacritic-audit.csv"


class DiacriticAuditTests(unittest.TestCase):
    def setUp(self):
        with AUDIT.open(encoding="utf-8", newline="") as stream:
            self.rows = list(csv.DictReader(stream))

    def test_expected_occurrence_counts(self):
        self.assertEqual(len(self.rows), 37)
        self.assertEqual(
            Counter(row["classification"] for row in self.rows),
            Counter({"caron": 30, "circumflex": 5, "grave": 1, "no_mark": 1}),
        )

        by_page = defaultdict(Counter)
        for row in self.rows:
            by_page[row["page"]][row["classification"]] += 1
        self.assertEqual(
            by_page["bnf-f0248"],
            Counter({"caron": 23, "circumflex": 4, "no_mark": 1}),
        )
        self.assertEqual(
            by_page["bnf-f0643"],
            Counter({"caron": 7, "circumflex": 1, "grave": 1}),
        )

    def test_sequences_and_required_evidence(self):
        by_page = defaultdict(list)
        for row in self.rows:
            by_page[row["page"]].append(int(row["sequence"]))
            self.assertTrue(row["context"])
            self.assertTrue(row["frozen"])
            self.assertTrue(row["reviewed"])
            self.assertTrue(row["evidence"])
        for sequences in by_page.values():
            self.assertEqual(sequences, list(range(1, len(sequences) + 1)))

    def test_text_is_nfc(self):
        text = AUDIT.read_text(encoding="utf-8")
        self.assertEqual(text, unicodedata.normalize("NFC", text))

    def test_full_page_reviewed_forms_are_recorded(self):
        reviewed = {row["reviewed"] for row in self.rows}
        self.assertIn("Gǒyen", reviewed)
        self.assertIn("Gǒyenuo", reviewed)
        self.assertIn("Gǔcon", reviewed)
        self.assertIn("Zzuqiǒ", reviewed)
        self.assertIn("Zzutçǔ", reviewed)


if __name__ == "__main__":
    unittest.main()
