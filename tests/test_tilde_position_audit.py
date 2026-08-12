import csv
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pilot" / "tilde-position-audit.tsv"
SOURCE_DIR = ROOT / "pilot" / "format-v1-trial" / "level1-source"


class TildePositionAuditTests(unittest.TestCase):
    def setUp(self):
        with LEDGER.open(encoding="utf-8", newline="") as handle:
            self.rows = list(csv.DictReader(handle, delimiter="\t"))

    def test_complete_occurrence_inventory(self):
        self.assertEqual(len(self.rows), 388)
        self.assertEqual(
            {mark: sum(row["mark_on"] == mark for row in self.rows) for mark in ("u", "a")},
            {"u": 220, "a": 168},
        )
        self.assertEqual(len({(row["page"], row["line"]) for row in self.rows}), 387)

    def test_every_adjudicated_form_is_in_its_source_line(self):
        pages = {}
        for row in self.rows:
            page_text = pages.setdefault(
                row["page"], (SOURCE_DIR / f'{row["page"]}.md').read_text(encoding="utf-8")
            )
            match = re.search(
                rf"^\[{re.escape(row['line'])}(?:\s[^\]]*)?\]\s+(.+)$",
                page_text,
                re.MULTILINE,
            )
            self.assertIsNotNone(match, f"missing {row['page']}:{row['line']}")
            self.assertIn(row["source"], match.group(1))

    def test_f19_anchor_and_f14_comparators(self):
        decisions = {(row["page"], row["line"]): row for row in self.rows}
        self.assertEqual(decisions[("bnf-f0019", "c2b-l011")]["source"], "alguã")
        for line in ("c1-l044", "c2-l029", "c2-l039", "c2-l042"):
            self.assertEqual(decisions[("bnf-f0014", line)]["source"], "algũa")


if __name__ == "__main__":
    unittest.main()
