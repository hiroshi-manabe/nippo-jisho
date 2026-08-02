import json
from pathlib import Path
import unittest

from scripts.build_public_review import transcription_version


ROOT = Path(__file__).resolve().parents[1]


class PublicReviewRegressionTests(unittest.TestCase):
    def test_edited_lines_preserve_typeface_and_submission_state(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("function styledVisualDiff(line, after)", app)
        self.assertIn("renderStyledSlice(line.runs", app)
        self.assertIn("persistSubmission(page, 'awaiting')", app)
        self.assertIn("persistSubmission(state.currentPage, 'submitted')", app)
        self.assertIn("Did you submit the GitHub Issue?", document)
        self.assertIn("Submit again", document)

    def test_f18_acuxocu_crop_is_centered_and_has_overlap(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in record["pages"] if page["id"] == "bnf-f0018")
        line = page["columns"]["column-2"]["lines"]["c2a-l018"]
        self.assertEqual(line["centre_y"], 1498)
        self.assertEqual(line["crop"], [1460, 1450, 1200, 96])

    def test_transcription_versions_and_rebase_controls(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        builder = (ROOT / "scripts" / "build_public_review.py").read_text(encoding="utf-8")
        self.assertIn('"transcription_version": transcription_version(zones)', builder)
        self.assertIn("const WORKSPACE_SCHEMA = 3", app)
        self.assertIn("function reconcileEdits(page, edits)", app)
        self.assertIn("comment_review_needed", app)
        self.assertIn("base_line_version", app)
        self.assertIn("base_transcription_version", app)
        self.assertIn("Saved corrections updated", document)
        self.assertIn("Copy orphaned corrections", document)
        self.assertIn("Discard orphaned corrections", document)

    def test_transcription_version_ignores_geometry_but_tracks_text_and_style(self):
        zones = [{"lines": [{
            "id": "c1-l001",
            "text": "Abc def",
            "runs": [
                {"typeface": "roman", "text": "Abc "},
                {"typeface": "italic", "text": "def"},
            ],
            "crop": [1, 2, 3, 4],
        }]}]
        baseline = transcription_version(zones)
        zones[0]["lines"][0]["crop"] = [9, 8, 7, 6]
        self.assertEqual(transcription_version(zones), baseline)
        zones[0]["lines"][0]["runs"][1]["typeface"] = "roman"
        self.assertNotEqual(transcription_version(zones), baseline)

    def test_transcription_version_tracks_large_initial_layout(self):
        zones = [{"lines": [{
            "id": "c1-l001",
            "text": "AFIru.",
            "runs": [
                {"typeface": "roman", "text": "A"},
                {"typeface": "roman", "text": "FIru."},
            ],
        }]}]
        baseline = transcription_version(zones)
        zones[0]["lines"][0]["runs"][0].update(
            {"layout": "large-initial", "line_span": 2}
        )
        self.assertNotEqual(transcription_version(zones), baseline)

    def test_large_initial_crops_contain_the_complete_two_line_glyph(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            "bnf-f0018": [("column-2", "c2b-l001")],
            "bnf-f0019": [
                ("column-1", "c1b-l001"),
                ("column-2", "c2b-l001"),
            ],
            "bnf-f0021": [("column-2", "c2b-l001")],
            "bnf-f0025": [("column-2", "c2b-l001")],
            "bnf-f0248": [("column-2", "c2b-l001")],
        }
        pages = {page["id"]: page for page in record["pages"]}
        for page_id, lines in expected.items():
            for column_id, line_id in lines:
                crop = pages[page_id]["columns"][column_id]["lines"][line_id]["crop"]
                self.assertGreaterEqual(crop[3], 158)

    def test_f18_issue_2_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0018")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 15)
        self.assertEqual(page["accepted_edits"], 15)
        self.assertEqual(page["issues"][0]["number"], 2)
        self.assertIn("c1-l019", page["issues"][0]["lines"])
        self.assertIn("c2a-l020", page["issues"][0]["lines"])
        self.assertIn("c2b-l011", page["issues"][0]["lines"])


if __name__ == "__main__":
    unittest.main()
