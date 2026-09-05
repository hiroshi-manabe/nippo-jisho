import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.process_correction_issue import (
    IssueProcessingError,
    corrected_runs,
    extract_payload,
    finalize,
    parse_correction_notation,
    prepare,
    report_path,
    update_history,
    validate_payload,
)
from scripts.compile_level1_markdown import export_markdown, parse_markdown


class CorrectionIssueProcessorTests(unittest.TestCase):
    def test_omitted_note_is_preserved_and_explicit_empty_note_is_deleted(self):
        from scripts.process_correction_issue import apply_change, apply_resolved
        for fields, expected in [({}, "Existing note"),
                                 ({"note_before": "Existing note", "note_after": ""}, None),
                                 ({"note_before": "Existing note", "note_after": "New note"}, "New note")]:
            with self.subTest(fields=fields):
                line = {"id": "c1-l001", "runs": [{"typeface": "roman", "text": "Alpha."}], "note": "Existing note"}
                item, _ = apply_change(line, {"line": line["id"], "before": "Alpha.", "after": "Beta.", **fields})
                apply_resolved(line, item)
                self.assertEqual(line.get("note"), expected)
                self.assertEqual("".join(run["text"] for run in line["runs"]), "Beta.")

    def test_batch_validates_all_pages_then_applies_and_finalizes_per_page(self):
        import copy
        from scripts.process_correction_issue import write_json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = {"zones": [{"lines": [{"id": "c1-l001", "runs": [{"typeface": "roman", "text": "Alpha."}]}]}]}
            records = [{"schema": 3, "page": f"f{n}", "base_commit": "abc",
                        "base_transcription_version": "old", "changes": [{"line": "c1-l001", "before": "Alpha.", "after": "Beta."}]} for n in (14, 15)]
            payload = {"schema": 4, "pages": records}
            issue = {"url": "https://example.test/9", "body": json.dumps(payload)}
            stored = {p["page"]: copy.deepcopy(original) for p in records}
            def load(root, view):
                return copy.deepcopy(stored[view]), {"source_kind": "canonical_markdown", "source_path": view}
            def save(root, storage, page):
                stored[storage["source_path"]] = copy.deepcopy(page)
            with (mock.patch("scripts.process_correction_issue.fetch_issue", return_value=issue),
                  mock.patch("scripts.process_correction_issue.validate_base_commit"),
                  mock.patch("scripts.process_correction_issue.load_editable_page", side_effect=load),
                  mock.patch("scripts.process_correction_issue.save_editable_page", side_effect=save) as writer,
                  mock.patch("scripts.process_correction_issue.current_transcription_version", return_value="old"),
                  mock.patch("scripts.process_correction_issue.changed_paths", return_value=set()),
                  mock.patch("scripts.process_correction_issue.regenerate_and_test"),
                  mock.patch("scripts.process_correction_issue.storage_from_report", side_effect=lambda p: {"source_kind": p["source_kind"], "source_path": p["source_path"]}),
                  mock.patch("scripts.process_correction_issue.update_history") as history):
                records[1]["changes"][0]["line"] = "missing"
                issue["body"] = json.dumps(payload)
                with self.assertRaisesRegex(IssueProcessingError, "unknown line"):
                    prepare(9, root=root)
                writer.assert_not_called()
                records[1]["changes"][0]["line"] = "c1-l001"
                records[1]["changes"][0]["second_opinion"] = True
                records[1]["changes"][0]["after"] = "Alpha."
                issue["body"] = json.dumps(payload)
                report = prepare(9, root=root)
                self.assertEqual(report["status"], "awaiting_second_opinion")
                self.assertTrue(report["pages"][1]["second_opinions"][0]["second_opinion"])
                self.assertEqual(stored["f14"]["zones"][0]["lines"][0]["runs"][0]["text"], "Beta.")
                self.assertEqual(stored["f15"]["zones"][0]["lines"][0]["runs"][0]["text"], "Alpha.")
                with self.assertRaisesRegex(IssueProcessingError, "f15/c1-l001"):
                    finalize(9, root=root, local_only=True)
                history.assert_not_called()
                report["pages"][1]["second_opinions"][0]["decision"] = "accept"
                write_json(report_path(9, root), report)
                result = finalize(9, root=root, local_only=True)
                self.assertEqual(result["accepted_lines"], ["f14/c1-l001", "f15/c1-l001"])
                self.assertEqual(history.call_count, 2)
            with self.assertRaisesRegex(IssueProcessingError, "duplicate page"):
                validate_payload({"schema": 4, "pages": [records[0], records[0]]})

    def test_prepare_can_apply_an_unflagged_edit_to_an_ocr_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = (
                root
                / "pilot"
                / "ocr-bootstrap"
                / "f0251-f0642"
                / "pages"
                / "bnf-f0251.json"
            )
            candidate.parent.mkdir(parents=True)
            page = {
                "format": "nippo-level1-page",
                "format_version": 1,
                "id": "bnf-f0251",
                "review": {
                    "origin": "independent_ocr_scan_bootstrap",
                    "physical_lineation_checked": False,
                    "status": "visual_draft",
                },
                "zones": [
                    {
                        "id": "column-1",
                        "kind": "column",
                        "label": "Column 1",
                        "lines": [
                            {
                                "id": "c1-l001",
                                "runs": [
                                    {"typeface": "roman", "text": "Alpha."},
                                    {"typeface": "italic", "text": " Firſt line."},
                                ],
                            }
                        ],
                    }
                ],
            }
            candidate.write_text(
                json.dumps(
                    {
                        "format": "nippo-ocr-level1-bootstrap-candidate",
                        "format_version": 1,
                        "id": "bnf-f0251",
                        "page": page,
                        "geometry": {},
                        "audit": {},
                    }
                ),
                encoding="utf-8",
            )
            payload = {
                "schema": 3,
                "page": "f251",
                "base_commit": "abc",
                "base_transcription_version": "sha256:old",
                "changes": [
                    {
                        "line": "c1-l001",
                        "before": "Alpha. Firſt line.",
                        "after": "Alpha. Firſt lines.",
                        "note_before": "",
                        "note_after": "A durable test annotation.",
                    }
                ],
            }
            issue = {
                "number": 251,
                "url": "https://example.test/issues/251",
                "body": f"```json\n{json.dumps(payload)}\n```",
            }
            with (
                mock.patch(
                    "scripts.process_correction_issue.validate_base_commit"
                ),
                mock.patch(
                    "scripts.process_correction_issue.fetch_issue", return_value=issue
                ),
                mock.patch("scripts.process_correction_issue.regenerate_and_test"),
                mock.patch(
                    "scripts.process_correction_issue.changed_paths", return_value=set()
                ),
            ):
                report = prepare(251, root=root, repository="example/test")
            updated = json.loads(candidate.read_text(encoding="utf-8"))
            updated_text = "".join(
                run["text"]
                for run in updated["page"]["zones"][0]["lines"][0]["runs"]
            )
            self.assertEqual(updated_text, "Alpha. Firſt lines.")
            self.assertEqual(
                updated["page"]["zones"][0]["lines"][0]["note"],
                "A durable test annotation.",
            )
            self.assertEqual(report["source_kind"], "ocr_candidate")
            self.assertEqual(
                report["source_path"],
                "pilot/ocr-bootstrap/f0251-f0642/pages/bnf-f0251.json",
            )
            self.assertEqual(report["status"], "ready_to_finalize")

    def test_schema_one_is_rejected(self):
        with self.assertRaisesRegex(IssueProcessingError, "unsupported correction schema 1"):
            validate_payload(
                {
                    "schema": 1,
                    "page": "f14",
                    "base_commit": "abc",
                    "base_transcription_version": "sha256:abc",
                    "changes": [{"line": "c1-l001", "before": "a", "after": "b"}],
                }
            )

    def test_payload_accepts_plain_json_or_one_json_block(self):
        payload = {
            "schema": 2,
            "page": "f14",
            "base_commit": "abc",
            "base_transcription_version": "sha256:abc",
            "changes": [{"line": "c1-l001", "before": "a", "after": "b"}],
        }
        body = f"Before\n```json\n{json.dumps(payload)}\n```\nAfter"
        self.assertEqual(extract_payload(body), payload)
        self.assertEqual(extract_payload("\n" + json.dumps(payload) + "\n"), payload)
        with self.assertRaisesRegex(IssueProcessingError, "exactly one"):
            extract_payload(body + "\n```json\n{}\n```")
        with self.assertRaisesRegex(IssueProcessingError, "must be an object"):
            extract_payload("[]")
        with self.assertRaisesRegex(IssueProcessingError, "invalid correction JSON"):
            extract_payload(json.dumps(payload) + "\n" + json.dumps(payload))

    def test_lightweight_notation_resolves_without_leaking_markers(self):
        text, roman_ranges, italic_ranges = parse_correction_notation(
            "Aburemono. Homem audaz, & que *não tẽ"
        )
        self.assertEqual(text, "Aburemono. Homem audaz, & que naõ tẽ")
        self.assertEqual(roman_ranges, [])
        self.assertEqual(italic_ranges, [])
        text, roman_ranges, italic_ranges = parse_correction_notation(
            "zinha, ou [cha], {P.}"
        )
        self.assertEqual(text, "zinha, ou cha, P.")
        self.assertEqual(roman_ranges, [(10, 13)])
        self.assertEqual(italic_ranges, [(15, 17)])
        self.assertNotIn("*", text)
        self.assertNotIn("[", text)
        self.assertNotIn("{", text)

    def test_typeface_annotations_reject_nesting_and_mismatched_delimiters(self):
        for value in ("[{cha}]", "{[P.]}"):
            with self.assertRaisesRegex(IssueProcessingError, "cannot be nested"):
                parse_correction_notation(value)
        with self.assertRaisesRegex(IssueProcessingError, "mismatched"):
            parse_correction_notation("{P.]")

    def test_ambiguous_tilde_marker_is_rejected(self):
        with self.assertRaisesRegex(IssueProcessingError, "no unique"):
            parse_correction_notation("*Gõye")

    def test_text_edits_preserve_typeface_and_roman_override(self):
        line = {
            "id": "c2-l043",
            "runs": [{"typeface": "italic", "text": "zinha, ou cha, &c."}],
        }
        text, roman_ranges, italic_ranges = parse_correction_notation(
            "zinha, ou [cha], &c."
        )
        self.assertEqual(
            corrected_runs(line, text, roman_ranges, italic_ranges),
            [
                {"typeface": "italic", "text": "zinha, ou "},
                {"typeface": "roman", "text": "cha"},
                {"typeface": "italic", "text": ", &c."},
            ],
        )

    def test_italic_override_is_applied_to_roman_source_text(self):
        line = {
            "id": "c1-l001",
            "runs": [{"typeface": "roman", "text": "Adu. P. Vide."}],
        }
        text, roman_ranges, italic_ranges = parse_correction_notation(
            "Adu. {P.} Vide."
        )
        self.assertEqual(
            corrected_runs(line, text, roman_ranges, italic_ranges),
            [
                {"typeface": "roman", "text": "Adu. "},
                {"typeface": "italic", "text": "P."},
                {"typeface": "roman", "text": " Vide."},
            ],
        )

    def test_italic_override_merges_invisible_plain_space_between_italic_runs(self):
        line = {
            "id": "c1-l002",
            "runs": [
                {"typeface": "italic", "text": "Ou. Vt,"},
                {"typeface": "roman", "text": " Pedro ca Ioão ca mairetomǒxe."},
            ],
        }
        text, roman_ranges, italic_ranges = parse_correction_notation(
            "Ou. Vt, {Pedro} ca {Ioão} ca mairetomǒxe."
        )
        self.assertEqual(
            corrected_runs(line, text, roman_ranges, italic_ranges),
            [
                {"typeface": "italic", "text": "Ou. Vt, Pedro"},
                {"typeface": "roman", "text": " ca "},
                {"typeface": "italic", "text": "Ioão"},
                {"typeface": "roman", "text": " ca mairetomǒxe."},
            ],
        )

    def test_typeface_override_keeps_named_far_right_span_serializable(self):
        line = {
            "id": "c2-l044",
            "runs": [
                {"typeface": "italic", "text": "o poo."},
                {
                    "typeface": "roman",
                    "text": " X.",
                    "placement": "far-right",
                    "span_id": "usage",
                },
            ],
        }
        text, roman_ranges, italic_ranges = parse_correction_notation(
            "o poo. {X.}"
        )
        self.assertEqual(
            corrected_runs(line, text, roman_ranges, italic_ranges),
            [
                {"typeface": "italic", "text": "o poo."},
                {
                    "typeface": "italic",
                    "text": " X.",
                    "placement": "far-right",
                    "span_id": "usage",
                },
            ],
        )

    def test_export_treats_whitespace_only_italic_run_as_plain_space(self):
        page = {
            "format": "nippo-level1-page",
            "format_version": 1,
            "id": "bnf-f9999",
            "source": {
                "repository": "test",
                "view": "f9999",
                "url": "https://example.invalid/",
                "master_sha256": "0" * 64,
            },
            "scope": "test",
            "review": {
                "origin": "test",
                "wikisource_used_for_this_trial": False,
                "physical_lineation_checked": True,
                "status": "scan_confirmed",
            },
            "zones": [
                {
                    "id": "column-1",
                    "kind": "column",
                    "label": "Column 1",
                    "lines": [
                        {
                            "id": "c1-l001",
                            "runs": [
                                {"typeface": "italic", "text": "before"},
                                {"typeface": "roman", "text": " word."},
                                {"typeface": "italic", "text": " "},
                                {"typeface": "roman", "text": "i"},
                                {"typeface": "italic", "text": "."},
                            ],
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.md"
            path.write_text(export_markdown(page), encoding="utf-8")
            parsed = parse_markdown(path)
        self.assertEqual(
            "".join(run["text"] for run in parsed["zones"][0]["lines"][0]["runs"]),
            "before word. i.",
        )

    def test_text_edits_retain_layout_metadata(self):
        line = {
            "id": "c1-l001",
            "runs": [
                {
                    "typeface": "display",
                    "text": "A",
                    "layout": "large-initial",
                    "line_span": 2,
                },
                {"typeface": "roman", "text": "FIru."},
                {"typeface": "display", "text": " 3", "placement": "far-right"},
            ],
        }
        runs = corrected_runs(line, "AFIru! 3", [])
        self.assertEqual(runs[0]["layout"], "large-initial")
        self.assertEqual(runs[0]["line_span"], 2)
        self.assertEqual(runs[-1]["placement"], "far-right")

    def test_history_counts_overlapping_lines_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "pilot" / "human-review" / "correction-history.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "format": "nippo-correction-history",
                        "format_version": 1,
                        "pages": [
                            {
                                "id": "bnf-f0014",
                                "issues_applied": 1,
                                "distinct_lines": 2,
                                "accepted_edits": 2,
                                "last_applied": "2026-01-01",
                                "issues": [
                                    {
                                        "number": 1,
                                        "url": "https://example.test/1",
                                        "applied_at": "2026-01-01",
                                        "lines": ["c1-l001", "c1-l002"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "issue": 2,
                "issue_url": "https://example.test/2",
                "page_id": "bnf-f0014",
            }
            update_history(report, ["c1-l002", "c1-l003"], root)
            page = json.loads(path.read_text(encoding="utf-8"))["pages"][0]
            self.assertEqual(page["issues_applied"], 2)
            self.assertEqual(page["accepted_edits"], 4)
            self.assertEqual(page["distinct_lines"], 3)
            update_history(report, ["c1-l002", "c1-l003"], root)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["pages"][0], page
            )
            with self.assertRaisesRegex(IssueProcessingError, "already present"):
                update_history(report, ["c1-l002"], root)

    def test_prepare_applies_only_unflagged_then_finalize_resumes_decisions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = (
                root
                / "pilot"
                / "format-v1-trial"
                / "level1-source"
                / "bnf-f0014.md"
            )
            source.parent.mkdir(parents=True)
            source.write_text(
                """---
format: nippo-level1-markdown
version: 1
id: bnf-f0014
source: Test
view: f14
url: https://example.test/f14
sha256: 0000000000000000000000000000000000000000000000000000000000000000
scope: full_dictionary_text_and_furniture
origin: test
wikisource: false
lineation: checked
status: scan_confirmed
---

## column-1 [column] Column 1

[c1-l001] Alpha. *First line.*
[c1-l002] Beta. *Second line.*
""",
                encoding="utf-8",
            )
            compiled = (
                root
                / "pilot"
                / "format-v1-trial"
                / "level1"
                / "bnf-f0014.json"
            )
            compiled.parent.mkdir(parents=True)
            compiled.write_text("{}\n", encoding="utf-8")
            history = root / "pilot" / "human-review" / "correction-history.json"
            history.parent.mkdir(parents=True)
            history.write_text(
                json.dumps(
                    {
                        "format": "nippo-correction-history",
                        "format_version": 1,
                        "pages": [],
                    }
                ),
                encoding="utf-8",
            )
            payload = {
                "schema": 3,
                "page": "f14",
                "base_commit": "abc",
                "base_transcription_version": "sha256:old",
                "changes": [
                    {
                        "line": "c1-l001",
                        "before": "Alpha. First line.",
                        "after": "Alpha. First lines.",
                        "note_before": "",
                        "note_after": "",
                    },
                    {
                        "line": "c1-l002",
                        "before": "Beta. Second line.",
                        "after": "Beta. Second lines.",
                        "note_before": "",
                        "note_after": "",
                        "message": "Please inspect this line.",
                    },
                ],
            }
            issue = {
                "number": 9,
                "url": "https://example.test/issues/9",
                "body": f"```json\n{json.dumps(payload)}\n```",
            }
            with (
                mock.patch(
                    "scripts.process_correction_issue.validate_base_commit"
                ),
                mock.patch(
                    "scripts.process_correction_issue.fetch_issue", return_value=issue
                ),
                mock.patch(
                    "scripts.process_correction_issue.regenerate_and_test",
                    side_effect=IssueProcessingError("test failure"),
                ),
                mock.patch(
                    "scripts.process_correction_issue.changed_paths", return_value=set()
                ),
            ):
                with self.assertRaisesRegex(IssueProcessingError, "test failure"):
                    prepare(9, root=root, repository="example/test")
            failed = json.loads(report_path(9, root).read_text(encoding="utf-8"))
            self.assertEqual(failed["status"], "validation_failed")
            self.assertIn("test failure", failed["validation_error"])
            prepared = source.read_text(encoding="utf-8")
            self.assertIn("First lines.", prepared)
            self.assertIn("Second line.", prepared)
            self.assertNotIn("Second lines.", prepared)

            with (
                mock.patch(
                    "scripts.process_correction_issue.validate_base_commit"
                ),
                mock.patch(
                    "scripts.process_correction_issue.fetch_issue", return_value=issue
                ),
                mock.patch("scripts.process_correction_issue.regenerate_and_test"),
                mock.patch(
                    "scripts.process_correction_issue.changed_paths",
                    return_value={
                        "pilot/format-v1-trial/level1-source/bnf-f0014.md"
                    },
                ),
            ):
                recovered = prepare(9, root=root, repository="example/test")
            self.assertTrue(recovered["applied_unflagged"][0]["recovered"])
            self.assertEqual(recovered["status"], "awaiting_second_opinion")
            self.assertEqual(recovered["second_opinions"][0]["decision"], "pending")

            saved = json.loads(report_path(9, root).read_text(encoding="utf-8"))
            saved["second_opinions"][0]["decision"] = "accept"
            report_path(9, root).write_text(json.dumps(saved), encoding="utf-8")
            with (
                mock.patch("scripts.process_correction_issue.regenerate_and_test"),
                mock.patch(
                    "scripts.process_correction_issue.changed_paths", return_value=set()
                ),
            ):
                finalized = finalize(9, root=root, local_only=True)
            self.assertEqual(finalized["status"], "locally_finalized")
            self.assertIn("Second lines.", source.read_text(encoding="utf-8"))
            applied = json.loads(history.read_text(encoding="utf-8"))["pages"][0]
            self.assertEqual(applied["accepted_edits"], 2)

            retry = json.loads(report_path(9, root).read_text(encoding="utf-8"))
            retry["status"] = "awaiting_second_opinion"
            report_path(9, root).write_text(json.dumps(retry), encoding="utf-8")
            with (
                mock.patch("scripts.process_correction_issue.regenerate_and_test"),
                mock.patch(
                    "scripts.process_correction_issue.changed_paths", return_value=set()
                ),
            ):
                retried = finalize(9, root=root, local_only=True)
            self.assertEqual(retried["status"], "locally_finalized")
            self.assertEqual(
                json.loads(history.read_text(encoding="utf-8"))["pages"][0], applied
            )


if __name__ == "__main__":
    unittest.main()
