import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.build_public_review import transcription_version


ROOT = Path(__file__).resolve().parents[1]


class PublicReviewRegressionTests(unittest.TestCase):
    def test_geometry_only_import_requires_explicit_opt_in(self):
        review = ROOT / "pilot" / "human-review" / "ai-geometry-work" / "bnf-f0042-reviewed.json"
        with tempfile.NamedTemporaryFile(suffix=".json") as geometry:
            geometry.write(
                (ROOT / "pilot" / "human-review" / "line-geometry.json").read_bytes()
            )
            geometry.flush()
            command = [
                "python3",
                str(ROOT / "scripts" / "import_ai_geometry_review.py"),
                str(review),
                "--geometry",
                geometry.name,
                "--reviewed-at",
                "2026-08-13",
            ]
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("AI review is not complete", rejected.stderr)
            accepted = subprocess.run(
                [*command, "--allow-geometry-only"], capture_output=True, text=True
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_edited_lines_preserve_typeface_and_submission_state(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("function styledVisualDiff(line, after)", app)
        self.assertIn("renderStyledSlice(line.runs", app)
        self.assertIn("persistSubmission(page, 'awaiting')", app)
        self.assertIn("persistSubmission(state.currentPage, 'submitted')", app)
        self.assertIn("Did you submit the GitHub Issue?", document)
        self.assertIn("Submit again", document)

    def test_line_editor_has_transcription_character_palette(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        for key, character in {
            "1": "ſ", "2": "ç", "3": "◌̃", "4": "◌̀", "5": "◌́",
            "6": "ǒ", "7": "ǔ", "8": "ô", "9": "û",
        }.items():
            self.assertIn(f"'{key}': {{label: '{character}'", app)
        self.assertIn("function applyDecoration(area, mark)", app)
        self.assertIn("data-character-key", app)
        self.assertIn("Literal digits", app)
        self.assertIn("event.preventDefault()", app)
        self.assertIn(".character-palette", styles)

    def test_line_editor_supports_lightweight_roman_spans(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        workflow = (ROOT / "docs" / "human-review-workflow.md").read_text(encoding="utf-8")
        issue_template = (ROOT / ".github" / "ISSUE_TEMPLATE" / "transcription-correction.md").read_text(encoding="utf-8")
        self.assertIn("function parseRomanNotation(value)", app)
        self.assertIn("function proposalMatchesLine(line, annotatedText)", app)
        self.assertIn("function styledRomanDiff(line, proposal)", app)
        self.assertIn("function applyRomanSpan(area)", app)
        self.assertIn('data-action="roman-span"', app)
        self.assertIn(".roman-span-key", styles)
        self.assertIn("`[Fotoqe]`", workflow)
        self.assertIn("`[Fotoqe]`", issue_template)

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

    def test_column_views_include_split_zone_names(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        self.assertIn("zone.id.includes(unit)", app)
        self.assertIn(
            "zonesFor(page, state.unit).filter(item => item.kind === 'column')",
            app,
        )

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

    def test_external_ai_geometry_has_complete_horizontal_coverage(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        pages = [
            page for page in record["pages"]
            if any(column.get("review_source") for column in page.get("columns", {}).values())
        ]
        self.assertEqual(
            [page["id"] for page in pages],
            [f"bnf-f{number:04d}" for number in range(31, 86)],
        )
        for page in pages:
            for column in page["columns"].values():
                leaf = int(page["id"].removeprefix("bnf-f"))
                if leaf <= 71:
                    self.assertEqual(
                        column["visual_review"], "external_ai_width_rechecked"
                    )
                    self.assertEqual(
                        column["horizontal_completeness_review"]["status"],
                        "complete_column_width_checked",
                    )
                else:
                    self.assertEqual(
                        column["visual_review"], "ai_bulk_geometry_sanity_checked"
                    )
                left, _, right, _ = column["box"]
                for line in column["lines"].values():
                    self.assertEqual(line["crop"][0], left)
                    self.assertEqual(line["crop"][0] + line["crop"][2], right)
                    self.assertEqual(line["context_crop"][0], left)
                    self.assertEqual(
                        line["context_crop"][0] + line["context_crop"][2], right
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
        self.assertEqual(page["distinct_lines"], 4)
        self.assertEqual(page["accepted_edits"], 4)
        self.assertEqual(page["issues"][0]["number"], 10)
        self.assertEqual(
            page["issues"][0]["lines"],
            ["c1-l025", "c2-l009", "c2-l011", "c2-l029"],
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

    def test_f28_issue_16_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0028")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 27)
        self.assertEqual(page["accepted_edits"], 27)
        self.assertEqual(page["issues"][0]["number"], 16)
        self.assertIn("c1-l009", page["issues"][0]["lines"])
        self.assertIn("c1-l036", page["issues"][0]["lines"])
        self.assertIn("c2-l033", page["issues"][0]["lines"])

    def test_f37_issue_25_history_and_typeface_corrections(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0037")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 25)
        self.assertEqual(page["accepted_edits"], 25)
        self.assertEqual(page["issues"][0]["number"], 25)
        self.assertEqual(len(page["issues"][0]["lines"]), 25)

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0037.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        self.assertIn({"typeface": "roman", "text": " Cha"}, lines["c1-l028"])
        self.assertIn({"typeface": "roman", "text": " Dairi"}, lines["c2-l016"])
        self.assertEqual(lines["c2-l030"][-1], {"typeface": "roman", "text": " P."})
        self.assertIn({"typeface": "italic", "text": " P. i."}, lines["c1-l010"])
        self.assertEqual(lines["c2-l046"][1]["typeface"], "italic")

    def test_f38_issue_26_history_override_and_typeface_corrections(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0038")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 32)
        self.assertEqual(page["accepted_edits"], 32)
        self.assertEqual(page["issues"][0]["number"], 26)
        self.assertNotIn("c2b-l007", page["issues"][0]["lines"])
        self.assertIn("c2b-l028", page["issues"][0]["lines"])

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0038.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        self.assertIn({"typeface": "roman", "text": " Qijis,"}, lines["c1-l005"])
        self.assertIn({"typeface": "roman", "text": " Ximo"}, lines["c1-l006"])
        self.assertIn({"typeface": "roman", "text": " i. Niuacani."}, lines["c2b-l020"])

    def test_f39_issue_27_partial_history_and_tilde_shorthand(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0039")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 14)
        self.assertEqual(page["accepted_edits"], 14)
        self.assertEqual(page["issues"][0]["number"], 27)
        self.assertIn("c2-l019", page["issues"][0]["lines"])
        self.assertNotIn("c1-l007", page["issues"][0]["lines"])

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0039.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: "".join(run["text"] for run in line["runs"])
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        self.assertIn("maõs", lines["c2-l019"])
        self.assertNotIn("*", lines["c2-l019"])

    def test_f29_issue_17_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0029")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 12)
        self.assertEqual(page["accepted_edits"], 12)
        self.assertEqual(page["issues"][0]["number"], 17)
        self.assertIn("c2-l007", page["issues"][0]["lines"])
        self.assertIn("c2-l026", page["issues"][0]["lines"])

    def test_f30_issue_18_correction_history_after_overrides(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0030")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 33)
        self.assertEqual(page["accepted_edits"], 33)
        self.assertEqual(page["issues"][0]["number"], 18)
        self.assertIn("c1-l004", page["issues"][0]["lines"])
        self.assertIn("c1-l034", page["issues"][0]["lines"])
        self.assertIn("c2-l006", page["issues"][0]["lines"])
        self.assertIn("c2-l034", page["issues"][0]["lines"])

    def test_f19_issue_3_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0019")
        self.assertEqual(page["issues_applied"], 2)
        self.assertEqual(page["distinct_lines"], 20)
        self.assertEqual(page["accepted_edits"], 21)
        self.assertEqual(page["issues"][0]["number"], 3)
        self.assertIn("c1b-l005", page["issues"][0]["lines"])
        self.assertIn("c2b-l011", page["issues"][0]["lines"])
        self.assertIn("c2b-l021", page["issues"][0]["lines"])
        self.assertEqual(page["issues"][1]["number"], 11)
        self.assertEqual(len(page["issues"][1]["lines"]), 12)
        self.assertIn("c1a-l030", page["issues"][1]["lines"])
        self.assertIn("c2a-l002", page["issues"][1]["lines"])
        self.assertIn("c2b-l034", page["issues"][1]["lines"])

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

    def test_f24_issue_12_correction_history(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0024")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 12)
        self.assertEqual(page["accepted_edits"], 12)
        self.assertEqual(page["issues"][0]["number"], 12)
        self.assertEqual(
            page["issues"][0]["lines"],
            [
                "c1-l001",
                "c1-l007",
                "c1-l014",
                "c1-l017",
                "c1-l020",
                "c1-l023",
                "c1-l031",
                "c2-l003",
                "c2-l006",
                "c2-l023",
                "c2-l028",
                "c2-l034",
            ],
        )


if __name__ == "__main__":
    unittest.main()
