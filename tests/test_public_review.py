import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.build_public_review import alternate_tilde_carrier, transcription_version


ROOT = Path(__file__).resolve().parents[1]


class PublicReviewRegressionTests(unittest.TestCase):
    def test_external_ai_assignment_stays_concise_and_links_references(self):
        work = ROOT / "pilot" / "human-review" / "ai-geometry-work"
        readme = (work / "README.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(readme.splitlines()), 60)
        for name in ("FORMAT.md", "GEOMETRY-GUIDE.md", "IMPORT-LOG.md"):
            self.assertTrue((work / name).is_file())
            self.assertIn(f"]({name})", readme)

    def test_external_ai_behavioral_example_is_a_real_completed_review(self):
        review_root = ROOT / "pilot" / "human-review"
        example_guide = (
            review_root / "ai-geometry-examples" / "README.md"
        ).read_text(encoding="utf-8")
        reviewed_path = (
            review_root / "ai-geometry-work" / "bnf-f0053-reviewed.json"
        )
        reviewed = json.loads(reviewed_path.read_text(encoding="utf-8"))
        lines = [
            line
            for column in reviewed["columns"].values()
            for line in column["lines"]
        ]

        self.assertIn("../ai-geometry-work/bnf-f0053-reviewed.json", example_guide)
        self.assertEqual(
            reviewed["response_status"], "completed_independent_ai_line_review"
        )
        self.assertTrue(lines)
        self.assertTrue(all(line["observed_text"] is not None for line in lines))
        self.assertTrue(any(line["assessment"] == "uncertain" for line in lines))
        self.assertTrue(any("note" in line for line in lines))

    def test_tilde_audit_covers_only_unreviewed_two_vowel_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "build_public_review.py"),
                    "--output",
                    directory,
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            output = Path(directory)
            audit = json.loads(
                (output / "tilde-audit.json").read_text(encoding="utf-8")
            )
            self.assertEqual(audit["task"], "tilde-carrier-audit")
            self.assertEqual(audit["scope"], "f39-f100")
            self.assertEqual(audit["review_basis"], "batch_review_unverified")
            self.assertEqual(
                [page["leaf"] for page in audit["pages"]], list(range(39, 101))
            )
            candidates = [
                (page["view"], candidate)
                for page in audit["pages"]
                for candidate in page["candidates"]
            ]
            self.assertEqual(len(candidates), 1016)
            keys = {
                f"{page}/{candidate['line']}#{candidate['occurrence']}"
                for page, candidate in candidates
            }
            self.assertEqual(len(keys), len(candidates))
            self.assertNotIn("f39/c2-l019#1", keys)
            self.assertNotIn("f100/c2-l020#1", keys)
            self.assertIn("f39/c1-l002#1", keys)
            first = audit["pages"][0]["candidates"][0]
            self.assertEqual((first["before"], first["after"]), ("não", "naõ"))
            for asset in ("tilde-audit.html", "tilde-audit.js", "tilde-audit.css"):
                self.assertTrue((output / asset).is_file())

    def test_tilde_carrier_swap_requires_exactly_two_adjacent_vowels(self):
        self.assertEqual(alternate_tilde_carrier("não", 1), "naõ")
        self.assertEqual(alternate_tilde_carrier("huã", 2), "hũa")
        self.assertEqual(alternate_tilde_carrier("poẽ", 2), "põe")
        self.assertIsNone(alternate_tilde_carrier("Gõye", 1))
        self.assertIsNone(alternate_tilde_carrier("casa", 1))

    def test_tilde_audit_has_keyboard_review_controls(self):
        script = (ROOT / "site" / "tilde-audit.js").read_text(encoding="utf-8")
        self.assertIn("event.key === 'ArrowDown'", script)
        self.assertIn("event.key === 'ArrowUp'", script)
        self.assertIn("event.code === 'Space'", script)
        self.assertIn("scrollIntoView({block: 'center'", script)
        self.assertIn("saved?.schema === 2", script)
        self.assertIn("candidate.occurrence", script)

    def test_tilde_audit_keeps_short_continuations_and_diacritics_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "build_public_review.py"),
                    "--output",
                    directory,
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            audit = json.loads(
                (Path(directory) / "tilde-audit.json").read_text(encoding="utf-8")
            )
            candidates = {
                f"{page['view']}/{candidate['line']}#{candidate['occurrence']}": candidate
                for page in audit["pages"]
                for candidate in page["candidates"]
            }
            # These indented continuations are printed at the left of their
            # columns; the former proportional estimate incorrectly cropped
            # them at the right edge.
            self.assertEqual(candidates["f49/c2-l027#1"]["crop"][0], 1205)
            self.assertLess(candidates["f51/c2-l005#1"]["crop"][0], 1400)
            self.assertEqual(candidates["f52/c2-l008#1"]["crop"][0], 1445)
            # The corrected f57 occurrence was individually adjudicated in
            # Issue #36 and therefore no longer appears in this unreviewed UI.
            self.assertNotIn("f57/c2-l003#1", candidates)
            # A final period is outside the token span but still belongs to
            # the printed line ending; retain the complete right edge.
            self.assertEqual(candidates["f58/c2b-l004#1"]["crop"], [1931, 2819, 720, 173])
            # From f60 onward the externally reviewed line geometry can be
            # displaced by about one printed line while remaining readable.
            # The specialist UI therefore retains an extra line above and
            # below. This nearby still-unreviewed line shares the displaced
            # f60 geometry that originally clipped the following target line.
            self.assertEqual(candidates["f60/c2-l034#1"]["crop"], [1727, 2287, 720, 311])

    def test_hyphen_audit_selections_survive_geometry_only_deployments(self):
        script = (ROOT / "site" / "hyphen-audit.js").read_text(encoding="utf-8")
        self.assertIn(
            "`nippo-hyphen-audit:${state.data.scope}`",
            script,
        )
        self.assertIn("saved?.schema === 2", script)
        self.assertIn("versions.get(key) === version", script)
        self.assertIn("Migrate the original commit-scoped array", script)

    def test_hyphen_audit_covers_f44_through_f100(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "build_public_review.py"),
                    "--output",
                    directory,
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            audit = json.loads(
                (Path(directory) / "hyphen-audit.json").read_text(encoding="utf-8")
            )
            self.assertEqual(audit["scope"], "f44-f100")
            self.assertEqual(
                [page["leaf"] for page in audit["pages"]], list(range(44, 101))
            )
            candidates = {
                f"{page['view']}/{candidate['line']}": candidate
                for page in audit["pages"]
                for candidate in page["candidates"]
            }
            expected = set()
            for leaf in range(44, 101):
                page = json.loads(
                    (
                        ROOT
                        / "pilot"
                        / "format-v1-trial"
                        / "level1"
                        / f"bnf-f{leaf:04d}.json"
                    ).read_text(encoding="utf-8")
                )
                for zone in page["zones"]:
                    if zone["kind"] != "column":
                        continue
                    for line in zone["lines"]:
                        text = "".join(run["text"] for run in line["runs"])
                        if text.rstrip().endswith("-"):
                            expected.add(f"f{leaf}/{line['id']}")
            self.assertEqual(set(candidates), expected)
            self.assertNotIn("f44/c1-l001", candidates)
            self.assertNotIn("f44/c2-l038", candidates)
            self.assertNotIn("f46/c1a-l013", candidates)
            self.assertTrue(
                all(candidate["before"].endswith("-") for candidate in candidates.values())
            )

    def test_outstanding_external_ai_tasks_are_complete_and_current(self):
        work = ROOT / "pilot" / "human-review" / "ai-geometry-work"
        expected_pages = [f"bnf-f{number:04d}" for number in range(101, 238)] + [
            "bnf-f0248",
            "bnf-f0249",
            "bnf-f0250",
            "bnf-f0643",
        ]
        expected_flags = {
            "bnf-f0149/c1b-l001",
            "bnf-f0153/c1b-l001",
            "bnf-f0155/c1b-l001",
            "bnf-f0160/c1f-l001",
            "bnf-f0181/c1b-l001",
            "bnf-f0186/c1b-l001",
            "bnf-f0204/c1b-l001",
            "bnf-f0216/c2b-l001",
            "bnf-f0230/c1b-l001",
        }
        line_count = 0
        actual_flags = set()
        for page_id in expected_pages:
            record = json.loads((work / f"{page_id}.json").read_text(encoding="utf-8"))
            self.assertEqual(record["page"], page_id)
            self.assertEqual(record["default_response_mode"], "geometry_and_text")
            self.assertEqual(
                record["response_status"], "pending_independent_ai_line_review"
            )
            self.assertIn("geometry_and_text", record["completion_statuses"])
            self.assertIn("geometry_only_fallback", record["completion_statuses"])
            source = ROOT / record["transcription_source"]["page_file"]
            self.assertEqual(
                hashlib.sha256(source.read_bytes()).hexdigest(),
                record["transcription_source"]["page_file_sha256"],
            )
            seen = set()
            for column in record["columns"].values():
                for line in column["lines"]:
                    self.assertNotIn(line["id"], seen)
                    seen.add(line["id"])
                    self.assertIsNone(line["observed_text"])
                    self.assertEqual(line["match"], "pending")
                    self.assertEqual(line["assessment"], "pending")
                    if line.get("validation_flags"):
                        actual_flags.add(f"{page_id}/{line['id']}")
            line_count += len(seen)
        self.assertEqual(line_count, 13_253)
        self.assertEqual(actual_flags, expected_flags)

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

    def test_manually_corrected_columns_reach_past_the_right_rule(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        pages = {page["id"]: page for page in record["pages"]}
        corrected_columns = {
            ("bnf-f0070", "column-1"): 1560,
            ("bnf-f0072", "column-1"): 1560,
            ("bnf-f0072", "column-2"): 2660,
        }
        for number in range(73, 86):
            corrected_columns[(f"bnf-f{number:04d}", "column-2")] = (
                2422 if number % 2 else 2660
            )
        for number in (74, 76, 78, 80, 82, 84, 86, 88):
            corrected_columns[(f"bnf-f{number:04d}", "column-1")] = 1560
        for (page_id, column_id), right_edge in corrected_columns.items():
            with self.subTest(page=page_id, column=column_id):
                column = pages[page_id]["columns"][column_id]
                self.assertEqual(column["box"][2], right_edge)
                for line in column["lines"].values():
                    self.assertEqual(
                        line["crop"][0] + line["crop"][2], right_edge
                    )
                    self.assertEqual(
                        line["context_crop"][0] + line["context_crop"][2],
                        right_edge,
                    )

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
            [f"bnf-f{number:04d}" for number in range(31, 106)],
        )
        for page in pages:
            for column in page["columns"].values():
                horizontal_review = column.get("horizontal_completeness_review")
                if horizontal_review:
                    self.assertEqual(
                        column["visual_review"], "external_ai_width_rechecked"
                    )
                    self.assertEqual(
                        horizontal_review["status"],
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

        f105 = next(page for page in record["pages"] if page["id"] == "bnf-f0105")
        self.assertTrue(
            all(
                column.get("review_source", "").endswith("-reviewed-redone.json")
                for column in f105["columns"].values()
            )
        )
        final_line = f105["columns"]["column-2"]["lines"]["c2-l047"]
        self.assertGreaterEqual(final_line["crop"][1] + final_line["crop"][3], 3380)

    def test_f86_f100_external_review_text_and_f94_lineation(self):
        def plain_lines(page_id):
            record = json.loads(
                (ROOT / "pilot" / "format-v1-trial" / "level1" / f"{page_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            return {
                line["id"]: "".join(run["text"] for run in line["runs"])
                for zone in record["zones"]
                for line in zone.get("lines", [])
            }

        f91 = plain_lines("bnf-f0091")
        self.assertIn("taſucatta", f91["c1-l034"])

        f94 = plain_lines("bnf-f0094")
        self.assertEqual(len([line for line in f94 if line.startswith("c1-")]), 47)
        self.assertTrue(f94["c1-l017"].endswith("Ajũtar, & acumu"))
        self.assertNotIn("c1-l048", f94)

        f98 = plain_lines("bnf-f0098")
        self.assertIn("Catçura", f98["c1-l017"])
        self.assertIn("tçumaru", f98["c1-l035"])
        self.assertIn("Neuoeiro", f98["c2-l044"])

        f99 = plain_lines("bnf-f0099")
        self.assertIn("Cauaij", f99["c1-l005"])
        self.assertIn("Xiqigauara", f99["c1-l019"])
        self.assertIn("Cauarabuqi", f99["c1-l022"])
        self.assertIn("me nadouo", f99["c2-l025"])

        f100 = plain_lines("bnf-f0100")
        self.assertIn("yerabu", f100["c1-l030"])
        self.assertIn("trauão", f100["c2-l020"])
        self.assertIn("Caxiqe", f100["c2-l023"])
        self.assertIn("Fanamo", f100["c2-l024"])
        self.assertIn("Caxiqeta", f100["c2-l027"])

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
        self.assertEqual(page["distinct_lines"], 21)
        self.assertEqual(page["accepted_edits"], 21)
        self.assertEqual(page["issues"][0]["number"], 27)
        self.assertIn("c2-l019", page["issues"][0]["lines"])
        self.assertIn("c1-l007", page["issues"][0]["lines"])
        self.assertIn("c1-l031", page["issues"][0]["lines"])

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
        self.assertIn("alijunto", lines["c1-l007"])
        self.assertIn("Serde", lines["c1-l031"])

    def test_f40_issue_28_history_typeface_and_tilde_shorthand(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0040")
        self.assertEqual(page["issues_applied"], 1)
        self.assertEqual(page["distinct_lines"], 24)
        self.assertEqual(page["accepted_edits"], 24)
        self.assertEqual(page["issues"][0]["number"], 28)
        self.assertIn("c1-l003", page["issues"][0]["lines"])
        self.assertIn("c2-l040", page["issues"][0]["lines"])

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0040.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        plain = {
            line_id: "".join(run["text"] for run in runs)
            for line_id, runs in lines.items()
        }
        self.assertIn({"typeface": "roman", "text": " Myaco catana."}, lines["c1-l001"])
        self.assertIn({"typeface": "roman", "text": " Torinoco"}, lines["c1-l002"])
        self.assertEqual(lines["c2-l017"][1], {"typeface": "italic", "text": " P. Imitar, ou ſeguir al-"})
        self.assertIn({"typeface": "roman", "text": " Fitono"}, lines["c2-l036"])
        self.assertIn("muniçoẽs", plain["c1-l036"])
        self.assertIn("dalgũa", plain["c2-l009"])
        self.assertIn("algũa", plain["c2-l039"])
        self.assertIn("naõ", plain["c2-l040"])
        self.assertNotIn("*", "".join(plain.values()))

    def test_f41_issue_29_history_typeface_and_tilde_shorthand(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0041")
        self.assertEqual(page["issues_applied"], 2)
        self.assertEqual(page["distinct_lines"], 29)
        self.assertEqual(page["accepted_edits"], 29)
        self.assertEqual(page["issues"][0]["number"], 29)
        self.assertIn("c1-l043", page["issues"][0]["lines"])
        self.assertIn("c2-l047", page["issues"][0]["lines"])
        self.assertEqual(page["issues"][1]["number"], 36)
        self.assertEqual(page["issues"][1]["lines"], ["c1-l009"])

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0041.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        plain = {
            line_id: "".join(run["text"] for run in runs)
            for line_id, runs in lines.items()
        }
        self.assertTrue(any(run["typeface"] == "roman" and "Cami" in run["text"] for run in lines["c1-l018"]))
        self.assertTrue(any(run["typeface"] == "roman" and "Fotoqe" in run["text"] for run in lines["c1-l018"]))
        self.assertTrue(any(run["typeface"] == "roman" and "Buppô" in run["text"] for run in lines["c1-l019"]))
        self.assertEqual(lines["c2-l038"][1], {"typeface": "italic", "text": "ù"})
        self.assertTrue(any(run["typeface"] == "roman" and "i. Auatatax" in run["text"] for run in lines["c2-l045"]))
        self.assertIn("ẽcarnaçaõ", plain["c1-l020"])
        self.assertIn("cõpaixaõ", plain["c2-l021"])
        self.assertIn("algũa", plain["c2-l036"])
        self.assertTrue(plain["c2-l047"].endswith("com pertur"))
        self.assertNotIn("*", "".join(plain.values()))

    def test_f42_issues_30_and_31_history_typeface_and_tilde_shorthand(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0042")
        self.assertEqual(page["issues_applied"], 2)
        self.assertEqual(page["distinct_lines"], 28)
        self.assertEqual(page["accepted_edits"], 28)
        self.assertEqual(page["issues"][0]["number"], 30)
        self.assertIn("c1-l034", page["issues"][0]["lines"])
        self.assertIn("c1-l047", page["issues"][0]["lines"])
        self.assertEqual(page["issues"][1]["number"], 31)
        self.assertEqual(len(page["issues"][1]["lines"]), 12)
        self.assertIn("c2-l004", page["issues"][1]["lines"])
        self.assertIn("c2-l046", page["issues"][1]["lines"])

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0042.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        plain = {
            line_id: "".join(run["text"] for run in runs)
            for line_id, runs in lines.items()
        }
        self.assertIn("algũas", plain["c1-l004"])
        self.assertIn("maõs", plain["c1-l009"])
        self.assertIn("feiçoẽs", plain["c1-l038"])
        self.assertIn("auaſuru Cotejar", plain["c1-l034"])
        self.assertIn("jutamente", plain["c1-l017"])
        self.assertIn("Concodar", plain["c1-l022"])
        self.assertTrue(any(run["typeface"] == "roman" and "Curo" in run["text"] for run in lines["c1-l047"]))
        self.assertIn("couſas çujas", plain["c2-l004"])
        self.assertIn("alguã", plain["c2-l033"])
        self.assertIn("reuerẽ-", plain["c2-l034"])
        self.assertEqual(plain["c2-l046"], "Auǒ. Auoſa.")
        self.assertTrue(any(run["typeface"] == "roman" and "Tatami" in run["text"] for run in lines["c2-l008"]))
        self.assertNotIn("*", "".join(plain.values()))

    def test_f43_issue_history_typeface_tilde_and_terminal_marks(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0043")
        self.assertEqual(page["issues_applied"], 2)
        self.assertEqual(page["distinct_lines"], 27)
        self.assertEqual(page["accepted_edits"], 27)
        self.assertEqual(page["issues"][0]["number"], 32)
        self.assertIn("c1-l004", page["issues"][0]["lines"])
        self.assertIn("c2b-l025", page["issues"][0]["lines"])
        self.assertEqual(page["issues"][1]["number"], 37)
        self.assertEqual(
            page["issues"][1]["lines"],
            ["c1-l034", "c1-l037", "c2b-l021", "c2b-l024"],
        )

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0043.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        plain = {
            line_id: "".join(run["text"] for run in runs)
            for line_id, runs in lines.items()
        }
        self.assertIn("graõs", plain["c1-l007"])
        self.assertIn("botaõ", plain["c1-l016"])
        self.assertIn("abanão", plain["c1-l033"])
        self.assertIn("dalgũa", plain["c2b-l007"])
        self.assertIn("algũa", plain["c2b-l025"])
        self.assertTrue(any(run["typeface"] == "roman" and "Catana" in run["text"] for run in lines["c1-l004"]))
        self.assertTrue(any(run["typeface"] == "roman" and "Cami" in run["text"] for run in lines["c1-l033"]))
        self.assertEqual(plain["c2b-l003"], "xe mizzuni naru. Banharſe em ſuor.")
        self.assertTrue(plain["c2b-l025"].endswith("não pode bu"))
        self.assertTrue(plain["c1-l034"].endswith("Idem"))
        self.assertTrue(plain["c1-l037"].endswith("ceo"))
        self.assertTrue(plain["c2b-l021"].endswith("na"))
        self.assertTrue(plain["c2b-l024"].endswith("totalmẽ"))
        self.assertNotIn("*", "".join(plain.values()))

    def test_f44_issue_38_after_human_overrides(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0044")
        self.assertEqual(page["issues_applied"], 3)
        self.assertEqual(page["distinct_lines"], 27)
        self.assertEqual(page["accepted_edits"], 30)
        self.assertEqual(page["issues"][-1]["number"], 38)
        self.assertEqual(len(page["issues"][-1]["lines"]), 23)

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0044.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        plain = {
            line_id: "".join(run["text"] for run in runs)
            for line_id, runs in lines.items()
        }
        self.assertEqual(plain["c1-l003"], "amimar alguem.")
        self.assertIn("Tçunogumu axi", plain["c1-l022"])
        self.assertTrue(
            any(run["typeface"] == "italic" and run["text"].strip() == "i." for run in lines["c1-l022"])
        )
        self.assertTrue(
            any(run["typeface"] == "italic" and run["text"].strip() == "ſ" for run in lines["c1-l029"])
        )
        self.assertEqual(plain["c2-l020"], "motoni firefuſu. Botarſe aos pès de outro.")
        self.assertIn("omeſmo paralitico", plain["c2-l032"])

        self.assertTrue(plain["c1-l046"].endswith("alojarte."))
        self.assertIn("Macho, ou grilhoẽs de pao", plain["c2-l012"])
        self.assertTrue(plain["c2-l037"].endswith("Peito do pè. (lhos."))
        self.assertTrue(plain["c2-l038"].endswith("dos arte"))
        self.assertNotIn("c2-l039", plain)

        geometry = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        geometry_page = next(page for page in geometry["pages"] if page["id"] == "bnf-f0044")
        geometry_lines = geometry_page["columns"]["column-2"]["lines"]
        self.assertNotIn("c2-l039", geometry_lines)
        self.assertEqual(geometry_lines["c2-l017"]["centre_y"], 1461)
        self.assertEqual(geometry_lines["c2-l032"]["centre_y"], 2386)
        self.assertEqual(geometry_lines["c2-l037"]["centre_y"], 2689)
        self.assertEqual(geometry_lines["c2-l038"]["centre_y"], 2758)
        self.assertEqual(geometry_lines["c2-l040"]["centre_y"], 2821)
        self.assertEqual(geometry_lines["c2-l048"]["centre_y"], 3319)

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

    def test_f45_issue_39_verified_corrections(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0045")
        self.assertEqual(page["issues_applied"], 2)
        self.assertEqual(page["distinct_lines"], 17)
        self.assertEqual(page["accepted_edits"], 17)
        self.assertEqual(page["issues"][-1]["number"], 39)
        self.assertEqual(len(page["issues"][-1]["lines"]), 16)

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0045.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        plain = {
            line_id: "".join(run["text"] for run in runs)
            for line_id, runs in lines.items()
        }
        self.assertEqual(plain["c1a-l010"], "Axitazzu. i. tçuru. Grou.")
        self.assertIn("õdinhas creſpas como adamaſcadas", plain["c1b-l005"])
        self.assertEqual(plain["c2-l003"], "Bunxǒno ayadoru. Idem.")
        self.assertIn("dalgũa couſa", plain["c2-l020"])
        self.assertEqual(plain["c1a-l014"], "o montante. ¶ Item, Peòzes de a çor, ou")
        self.assertTrue(
            any(run["typeface"] == "roman" and run["text"].endswith("B") for run in lines["c2-l018"])
        )
        self.assertTrue(
            any(run["typeface"] == "italic" and run["text"].startswith("em, ou") for run in lines["c2-l018"])
        )

    def test_f46_issue_40_verified_corrections(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0046")
        self.assertEqual(page["issues_applied"], 3)
        self.assertEqual(page["distinct_lines"], 23)
        self.assertEqual(page["accepted_edits"], 25)
        self.assertEqual(page["issues"][-1]["number"], 40)
        self.assertEqual(len(page["issues"][-1]["lines"]), 14)

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0046.json").read_text(
                encoding="utf-8"
            )
        )
        lines = {
            line["id"]: line["runs"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        plain = {
            line_id: "".join(run["text"] for run in runs)
            for line_id, runs in lines.items()
        }
        self.assertEqual(plain["c1a-l002"], "Ayaxiſa.")
        self.assertIn("diſtĩ tamẽ-", plain["c2-l002"])
        self.assertIn("azaazato", plain["c2-l003"])
        self.assertTrue(plain["c2-l004"].endswith("diſtincta"))
        self.assertEqual(plain["c2-l005"], "mente.")
        self.assertIn("chǒriǒuomo", plain["c2-l014"])
        self.assertIn("aq̃l-", plain["c2-l030"])
        self.assertIn("uerſo quelhe", plain["c2-l034"])
        self.assertIn("yxǒ", plain["c2-l041"])
        self.assertTrue(
            any(run["typeface"] == "italic" and run["text"].strip() == "e" for run in lines["c1a-l015"])
        )
        self.assertTrue(
            any(run["typeface"] == "roman" and run["text"].endswith("H") for run in lines["c2-l008"])
        )
        self.assertTrue(
            any(run["typeface"] == "italic" and run["text"].strip() == "S. Paulo" for run in lines["c2-l022"])
        )
        self.assertTrue(
            any(run["typeface"] == "italic" and run["text"].strip() == "Saulo" for run in lines["c2-l022"])
        )

    def test_f47_issue_41_after_human_confirmation(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0047")
        self.assertEqual(page["issues_applied"], 3)
        self.assertEqual(page["distinct_lines"], 17)
        self.assertEqual(page["accepted_edits"], 19)
        self.assertEqual(page["issues"][-1]["number"], 41)
        self.assertEqual(len(page["issues"][-1]["lines"]), 14)

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0047.json").read_text(
                encoding="utf-8"
            )
        )
        plain = {
            line["id"]: "".join(run["text"] for run in line["runs"])
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        self.assertIn("Oq̃ toma", plain["c1a-l007"])
        self.assertIn("metelas", plain["c1a-l012"])
        self.assertIn("Azzuſayumi", plain["c1a-l029"])
        self.assertTrue(plain["c1b-l009"].startswith("àde fazer"))
        self.assertTrue(plain["c2-l013"].endswith("da carri"))
        self.assertIn("Hom em que", plain["c2-l018"])
        self.assertIn("descortez", plain["c2-l036"])
        self.assertIn("Yafan bacarini", plain["c2-l042"])
        self.assertIn("acçoẽs", plain["c2-l020"])

    def test_f48_issue_42_applies_only_scan_supported_corrections(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in history["pages"] if page["id"] == "bnf-f0048")
        self.assertEqual(page["issues_applied"], 2)
        self.assertEqual(page["distinct_lines"], 38)
        self.assertEqual(page["accepted_edits"], 43)
        self.assertEqual(page["issues"][-1]["number"], 42)
        self.assertEqual(len(page["issues"][-1]["lines"]), 33)

        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0048.json").read_text(
                encoding="utf-8"
            )
        )
        plain = {
            line["id"]: "".join(run["text"] for run in line["runs"])
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        self.assertIn("fodoyorimo", plain["c1-l005"])
        self.assertIn("votonaxǔmiyuru", plain["c1-l006"])
        self.assertEqual(plain["c1-l032"], "Bacubeô. Miguinonaye. Trigo, ou ce-")
        self.assertIn("Vǒmuguinoco", plain["c1-l044"])
        self.assertEqual(plain["c1-l046"], "Bacugue. i. Vǒmuguino moyaxi. Fazer")
        self.assertEqual(plain["c2-l027"], "Bafá. Ir a furtar fora de Iapão a China, ou a")
        self.assertIn("Vricǒ", plain["c2-l042"])
        self.assertIn("vẽder", plain["c2-l042"])
        self.assertTrue(plain["c2-l042"].endswith("mer-"))
        self.assertEqual(plain["c2-l046"], "Bai, o, ǒta. Tomar por força.")

        # The damaged initial is retained by contextual reconstruction rather than
        # represented as a literal full stop.
        self.assertIn("Baccani", plain["c1-l002"])
        self.assertIn("tãbor", plain["c1-l022"])
        self.assertIn("trata en", plain["c2-l006"])
        self.assertIn("ou uender caualos", plain["c2-l007"])
        self.assertTrue(plain["c2-l037"].endswith("poſtu-"))


if __name__ == "__main__":
    unittest.main()
