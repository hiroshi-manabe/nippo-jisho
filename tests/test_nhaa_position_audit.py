import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "pilot" / "format-v1-trial" / "level1-source"


class NhaaPositionAuditTests(unittest.TestCase):
    def test_no_audited_leftward_tilde_forms_remain(self):
        corpus = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(SOURCE_DIR.glob("bnf-f*.md"))
        )
        self.assertIsNone(re.search("nhãa", corpus, re.IGNORECASE))

    def test_scan_confirmed_anchor_and_double_occurrence(self):
        f37 = (SOURCE_DIR / "bnf-f0037.md").read_text(encoding="utf-8")
        self.assertIn("O partirſe de manhaã.", f37)

        f38 = (SOURCE_DIR / "bnf-f0038.md").read_text(encoding="utf-8")
        line = re.search(r"^\[c2a-l011\]\s+(.+)$", f38, re.MULTILINE)
        self.assertIsNotNone(line)
        self.assertEqual(len(re.findall("amanhaã", line.group(1), re.IGNORECASE)), 2)


if __name__ == "__main__":
    unittest.main()
