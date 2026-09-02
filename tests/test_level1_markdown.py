import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / "pilot" / "format-v1-trial"
SOURCE = TRIAL / "level1-source"
JSON_DIR = TRIAL / "level1"
SCRIPT = ROOT / "scripts" / "compile_level1_markdown.py"


def load_module():
    spec = importlib.util.spec_from_file_location("compile_level1_markdown", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Level1MarkdownTests(unittest.TestCase):
    def test_durable_line_notes_round_trip_without_entering_text_runs(self):
        module = load_module()
        page = json.loads((JSON_DIR / "bnf-f0163.json").read_text(encoding="utf-8"))
        line = next(line for zone in page["zones"] for line in zone.get("lines", []) if line["id"] == "c1-l012")
        line["note"] = "The reading is mechanically useful.\nIt remains provisional."
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.md"
            path.write_text(module.export_markdown(page), encoding="utf-8")
            parsed = module.parse_markdown(path)
        parsed_line = next(line for zone in parsed["zones"] for line in zone.get("lines", []) if line["id"] == "c1-l012")
        self.assertEqual(parsed_line["note"], line["note"])
        self.assertEqual(parsed_line["runs"], line["runs"])

    def test_human_checked_is_a_supported_production_status(self):
        module = load_module()
        self.assertIn("human_checked", module.ALLOWED_STATUSES)

    def test_committed_json_is_generated_from_compact_source(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "compile", str(SOURCE), str(JSON_DIR), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 229 compact Level 1 page records", result.stdout)

    def test_all_source_pages_parse_and_retain_22376_lines(self):
        module = load_module()
        pages = [module.parse_markdown(path) for path in sorted(SOURCE.glob("*.md"))]
        self.assertEqual(len(pages), 229)
        self.assertEqual(
            sum(len(zone.get("lines", [])) for page in pages for zone in page["zones"]),
            22376,
        )
        for page in pages:
            committed = json.loads((JSON_DIR / f"{page['id']}.json").read_text(encoding="utf-8"))
            self.assertEqual(page, committed)
            self.assertEqual(
                module.export_markdown(page),
                (SOURCE / f"{page['id']}.md").read_text(encoding="utf-8"),
            )

    def test_exceptional_placement_is_addressable(self):
        page = json.loads((JSON_DIR / "bnf-f0248.json").read_text(encoding="utf-8"))
        line = next(
            line
            for zone in page["zones"]
            for line in zone.get("lines", [])
            if line["id"] == "c1-l037"
        )
        displaced = [run for run in line["runs"] if run.get("placement") == "far-right"]
        self.assertEqual([run["span_id"] for run in displaced], ["mark", "word"])

    def test_recurring_large_initials_are_explicit_and_round_trip(self):
        expected = {
            "bnf-f0018": {"c2b-l001": 2},
            "bnf-f0019": {"c1b-l001": 2, "c2b-l001": 2},
            "bnf-f0021": {"c2b-l001": 2},
            "bnf-f0025": {"c2b-l001": 2},
            "bnf-f0029": {"c1-l001": 2},
            "bnf-f0031": {"c2p-l001": 2, "c2q-l001": 2},
            "bnf-f0033": {"c1b-l001": 2},
            "bnf-f0036": {"c2b-l001": 2},
            "bnf-f0038": {"c2b-l001": 2},
            "bnf-f0041": {"c2-l001": 2},
            "bnf-f0043": {"c2b-l001": 2},
            "bnf-f0045": {"c1b-l001": 2},
            "bnf-f0046": {"c1b-l001": 2},
            "bnf-f0047": {"c1b-l001": 4},
            "bnf-f0053": {"c1b-l001": 2},
            "bnf-f0055": {"c1b-l001": 2},
            "bnf-f0058": {"c2b-l001": 2},
            "bnf-f0062": {"c2b-l001": 2},
            "bnf-f0068": {"c2b-l001": 5},
            "bnf-f0181": {"c1b-l001": 2},
            "bnf-f0186": {"c1b-l001": 2},
            "bnf-f0248": {"c2b-l001": 2},
        }
        for page_id, line_ids in expected.items():
            source = (SOURCE / f"{page_id}.md").read_text(encoding="utf-8")
            page = json.loads((JSON_DIR / f"{page_id}.json").read_text(encoding="utf-8"))
            lines = {
                line["id"]: line
                for zone in page["zones"]
                for line in zone.get("lines", [])
            }
            for line_id, line_span in line_ids.items():
                self.assertIn(f"[{line_id} initial={line_span}]", source)
                first = lines[line_id]["runs"][0]
                self.assertEqual(first["layout"], "large-initial")
                self.assertEqual(first["line_span"], line_span)
                self.assertEqual(len(first["text"]), 1)

    def test_line_division_sign_is_uniform_across_typefaces(self):
        for path in SOURCE.glob("*.md"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("[") and "] " in line:
                    self.assertNotIn("=", line.split("] ", 1)[1], path.name)

    def test_correction_history_aggregates_are_self_consistent(self):
        history = json.loads(
            (ROOT / "pilot" / "human-review" / "correction-history.json").read_text(
                encoding="utf-8"
            )
        )
        page_ids = [page["id"] for page in history["pages"]]
        self.assertEqual(len(page_ids), len(set(page_ids)))
        for page in history["pages"]:
            issues = page["issues"]
            issue_numbers = [issue["number"] for issue in issues]
            lines = [line for issue in issues for line in issue["lines"]]
            self.assertEqual(page["issues_applied"], len(issues))
            self.assertEqual(page["distinct_lines"], len(set(lines)))
            self.assertGreaterEqual(page["accepted_edits"], page["distinct_lines"])
            self.assertEqual(len(issue_numbers), len(set(issue_numbers)))


if __name__ == "__main__":
    unittest.main()
