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
    def test_json_writer_preserves_semantically_identical_bytes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'record.json'
            original = '{"z": 1, "a": {"y": 2, "b": 3}}\n'
            path.write_text(original)
            module.write_json({'a': {'b': 3, 'y': 2}, 'z': 1}, path)
            self.assertEqual(path.read_text(), original)
            module.write_json({'z': 2}, path)
            self.assertEqual(json.loads(path.read_text()), {'z': 2})

    def test_durable_line_notes_round_trip_without_entering_text_runs(self):
        module = load_module()
        page = json.loads(next(JSON_DIR.glob('*.json')).read_text(encoding="utf-8"))
        line = next(line for zone in page["zones"] for line in zone.get("lines", []))
        line["note"] = "The reading is mechanically useful.\nIt remains provisional."
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.md"
            path.write_text(module.export_markdown(page), encoding="utf-8")
            parsed = module.parse_markdown(path)
        parsed_line = next(item for zone in parsed["zones"] for item in zone.get("lines", []) if item['id'] == line['id'])
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
        self.assertIn(f"Validated {len(list(SOURCE.glob('*.md')))} compact Level 1 page records", result.stdout)

    def test_all_source_pages_parse_and_round_trip(self):
        module = load_module()
        pages = [module.parse_markdown(path) for path in sorted(SOURCE.glob("*.md"))]
        self.assertTrue(pages)
        self.assertEqual({page['id'] for page in pages}, {path.stem for path in JSON_DIR.glob('*.json')})
        for page in pages:
            committed = json.loads((JSON_DIR / f"{page['id']}.json").read_text(encoding="utf-8"))
            self.assertEqual(page, committed)
            self.assertEqual(
                module.export_markdown(page),
                (SOURCE / f"{page['id']}.md").read_text(encoding="utf-8"),
            )



    def test_line_division_sign_is_uniform_across_typefaces(self):
        for path in SOURCE.glob("*.md"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("[") and "] " in line and not line.split("] ", 1)[0].endswith(" note"):
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
