import csv
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import download_ninjal_headwords as headwords  # noqa: E402


class DownloadNinjalHeadwordsTests(unittest.TestCase):
    def write_tsv(self, path, rows):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=headwords.EXPECTED_COLUMNS, delimiter="\t"
            )
            writer.writeheader()
            writer.writerows(rows)

    def row(self, number, identifier, location="001a", bnf_url=""):
        row = dict.fromkeys(headwords.EXPECTED_COLUMNS, "")
        row.update(
            {
                "整理番号": str(number),
                "見出し語ID": identifier,
                "見出し語": f"Entry{number}.",
                "原本所在": location,
                "BnF画像": bnf_url,
            }
        )
        return row

    def test_release_constants(self):
        self.assertEqual(headwords.VERSION, "202510")
        self.assertEqual(headwords.EXPECTED_RECORDS, 32_878)
        self.assertTrue(headwords.DOWNLOAD_URL.endswith("ew-nippo-202510.zip"))
        self.assertEqual(len(headwords.EXPECTED_SHA256), 64)

    def test_validate_tsv_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.tsv"
            self.write_tsv(
                path,
                [
                    self.row(
                        1,
                        "001a01",
                        bnf_url=(
                            "https://gallica.bnf.fr/ark:/12148/"
                            "bpt6k852354j/f13.item"
                        ),
                    ),
                    self.row(2, "332a01", location="332a"),
                ],
            )
            self.assertEqual(
                headwords.validate_tsv(path, expected_records=2),
                {
                    "records": 2,
                    "unique_ids": 2,
                    "bnf_links": 1,
                    "supplement_records": 1,
                },
            )

    def test_rejects_duplicate_identifier(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.tsv"
            self.write_tsv(path, [self.row(1, "001a01"), self.row(2, "001a01")])
            with self.assertRaises(headwords.ValidationError):
                headwords.validate_tsv(path, expected_records=2)


if __name__ == "__main__":
    unittest.main()
