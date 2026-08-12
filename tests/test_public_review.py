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

    def test_page_view_has_explicit_overview_control(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="back-to-overview"', document)
        self.assertIn("← All pages", document)
        self.assertIn("$('#back-to-overview').addEventListener('click', () => showOverview())", app)

    def test_column_views_have_continuous_top_and_bottom_navigation(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="column-nav-top"', document)
        self.assertIn("function columnSequence()", app)
        self.assertIn("← Previous column", app)
        self.assertIn("Next column →", app)
        self.assertIn("columnNavigationHTML('column-nav-bottom')", app)
        self.assertIn("[data-column-leaf][data-column-unit]", app)
        self.assertIn("window.scrollTo(0, 0)", app)

    def test_f18_acuxocu_crop_is_centered_and_has_overlap(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in record["pages"] if page["id"] == "bnf-f0018")
        line = page["columns"]["column-2"]["lines"]["c2a-l018"]
        self.assertEqual(line["centre_y"], 1498)
        self.assertEqual(line["crop"], [1460, 1438, 1200, 120])

    def test_f24_folgar_descender_is_not_clipped(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in record["pages"] if page["id"] == "bnf-f0024")
        line = page["columns"]["column-2"]["lines"]["c2-l023"]
        self.assertEqual(line["crop"], [1540, 1790, 1080, 150])

    def test_f24_aixiri_is_the_crop_focus(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in record["pages"] if page["id"] == "bnf-f0024")
        column = page["columns"]["column-2"]
        self.assertEqual(column["visual_review"], "text_image_sanity_checked")
        self.assertEqual(column["lines"]["c2-l041"]["crop"], [1540, 2938, 1080, 122])

    def test_f25_through_f30_received_text_image_sanity_check(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        pages = {page["id"]: page for page in record["pages"]}
        for number in range(25, 31):
            with self.subTest(page=number):
                page = pages[f"bnf-f{number:04d}"]
                for column in page["columns"].values():
                    self.assertEqual(
                        column["visual_review"], "text_image_sanity_checked"
                    )

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
            "bnf-f0029": [("column-1", "c1-l001")],
            "bnf-f0031": [
                ("column-2", "c2p-l001"),
                ("column-2", "c2q-l001"),
            ],
            "bnf-f0033": [("column-1", "c1b-l001")],
            "bnf-f0036": [("column-2", "c2b-l001")],
            "bnf-f0038": [("column-2", "c2b-l001")],
            "bnf-f0041": [("column-2", "c2-l001")],
            "bnf-f0043": [("column-2", "c2b-l001")],
            "bnf-f0045": [("column-1", "c1b-l001")],
            "bnf-f0046": [("column-1", "c1b-l001")],
            "bnf-f0047": [("column-1", "c1b-l001")],
            "bnf-f0053": [("column-1", "c1b-l001")],
            "bnf-f0055": [("column-1", "c1b-l001")],
            "bnf-f0058": [("column-2", "c2b-l001")],
            "bnf-f0062": [("column-2", "c2b-l001")],
            "bnf-f0068": [("column-2", "c2b-l001")],
            "bnf-f0248": [("column-2", "c2b-l001")],
        }
        pages = {page["id"]: page for page in record["pages"]}
        for page_id, lines in expected.items():
            for column_id, line_id in lines:
                crop = pages[page_id]["columns"][column_id]["lines"][line_id]["crop"]
                self.assertGreaterEqual(crop[3], 158)

    def test_f13_issue_10_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0013")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 3)
        self.assertEqual(page["accepted_edits"], 3)
        self.assertEqual(page["issues"][0]["number"], 10)
        self.assertEqual(
            page["issues"][0]["lines"],
            ["c1-l025", "c2-l009", "c2-l011"],
        )

    def test_f18_issue_2_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0018")
        self.assertEqual(page["issues_applied"], 2)
        self.assertEqual(page["distinct_lines"], 18)
        self.assertEqual(page["accepted_edits"], 18)
        self.assertEqual(page["issues"][0]["number"], 2)
        self.assertIn("c1-l019", page["issues"][0]["lines"])
        self.assertIn("c2a-l020", page["issues"][0]["lines"])
        self.assertIn("c2b-l011", page["issues"][0]["lines"])
        self.assertEqual(page["issues"][1]["number"], 4)
        self.assertEqual(
            page["issues"][1]["lines"],
            ["c2a-l009", "c2a-l025", "c2a-l026"],
        )

    def test_f19_issue_3_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0019")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 9)
        self.assertEqual(page["accepted_edits"], 9)
        self.assertEqual(page["issues"][0]["number"], 3)
        self.assertIn("c1b-l005", page["issues"][0]["lines"])
        self.assertIn("c2b-l011", page["issues"][0]["lines"])
        self.assertIn("c2b-l021", page["issues"][0]["lines"])

    def test_f20_issue_5_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0020")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 22)
        self.assertEqual(page["accepted_edits"], 22)
        self.assertEqual(page["issues"][0]["number"], 5)
        self.assertIn("c1-l046", page["issues"][0]["lines"])
        self.assertIn("c2-l037", page["issues"][0]["lines"])
        self.assertIn("c2-l043", page["issues"][0]["lines"])
        self.assertIn("c2-l047", page["issues"][0]["lines"])

    def test_f21_issue_6_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0021")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 34)
        self.assertEqual(page["accepted_edits"], 34)
        self.assertEqual(page["issues"][0]["number"], 6)
        self.assertIn("c1-l024", page["issues"][0]["lines"])
        self.assertIn("c2b-l006", page["issues"][0]["lines"])
        self.assertIn("c2b-l009", page["issues"][0]["lines"])
        self.assertIn("c2b-l041", page["issues"][0]["lines"])

    def test_f22_issue_7_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0022")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 12)
        self.assertEqual(page["accepted_edits"], 12)
        self.assertEqual(page["issues"][0]["number"], 7)
        self.assertIn("c1-l013", page["issues"][0]["lines"])
        self.assertIn("c2-l006", page["issues"][0]["lines"])
        self.assertIn("c2-l047", page["issues"][0]["lines"])

    def test_f23_issue_8_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0023")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 18)
        self.assertEqual(page["accepted_edits"], 18)
        self.assertEqual(page["issues"][0]["number"], 8)
        self.assertIn("c1-l002", page["issues"][0]["lines"])
        self.assertIn("c1-l042", page["issues"][0]["lines"])
        self.assertIn("c2-l017", page["issues"][0]["lines"])
        self.assertIn("c2-l036", page["issues"][0]["lines"])
        self.assertIn("c2-l047", page["issues"][0]["lines"])


if __name__ == "__main__":
    unittest.main()
