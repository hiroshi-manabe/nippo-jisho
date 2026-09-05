import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / "pilot" / "format-v1-trial"
SCRIPT = ROOT / "scripts" / "render_format_trial.py"


def load_module():
    spec = importlib.util.spec_from_file_location("render_format_trial", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FormatV1TrialTests(unittest.TestCase):
    def test_f13_internal_heading_is_furniture_not_body_text(self):
        page = json.loads(
            (TRIAL / "level1" / "bnf-f0013.json").read_text(encoding="utf-8")
        )
        zones = {zone["id"]: zone for zone in page["zones"]}
        self.assertEqual(zones["section-column-1"]["kind"], "section_heading")
        body_lines = {
            line["id"]
            for zone in page["zones"]
            if zone["kind"] == "column"
            for line in zone["lines"]
        }
        self.assertNotIn("c1-l019", body_lines)
        self.assertIn("c1-l018", body_lines)
        self.assertIn("c1-l020", body_lines)

    def test_complete_trial_validates(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(TRIAL), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("22375 physical lines", result.stdout)

    def test_generated_views_are_current(self):
        module = load_module()
        registry = {}
        pages = []
        for path in sorted((TRIAL / "level1").glob("*.json")):
            page = json.loads(path.read_text(encoding="utf-8"))
            registry.update(module.validate_page(page, path))
            pages.append(page)
        structure_path = TRIAL / "level2" / "selected-structure.json"
        structure = json.loads(structure_path.read_text(encoding="utf-8"))
        module.validate_structure(structure, registry, structure_path)

        for page in pages:
            generated = (TRIAL / "generated" / f"{page['id']}-page.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(generated, module.render_page(page))
        generated = (TRIAL / "generated" / "selected-reading-views.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(generated, module.render_sequences(structure, registry))

    def test_exceptional_span_placement_remains_structural(self):
        page = json.loads(
            (TRIAL / "level1" / "bnf-f0248.json").read_text(encoding="utf-8")
        )
        line = next(
            line
            for zone in page["zones"]
            for line in zone.get("lines", [])
            if line["id"] == "c1-l037"
        )
        displaced = [run for run in line["runs"] if run.get("placement") == "far-right"]
        self.assertEqual([run["span_id"] for run in displaced], ["mark", "word"])

    def test_trial_records_have_complete_scope_and_checked_lineation(self):
        pages = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((TRIAL / "level1").glob("*.json"))
        ]
        self.assertEqual(len(pages), 229)
        for page in pages:
            self.assertEqual(page["scope"], "full_dictionary_text_and_furniture")
            self.assertTrue(page["review"]["physical_lineation_checked"])

        final_page = next(page for page in pages if page["id"] == "bnf-f0643")
        self.assertTrue(
            any(zone["kind"] == "later_copy_mark" for zone in final_page["zones"])
        )
        self.assertTrue(any(zone["kind"] == "terminus" for zone in final_page["zones"]))


if __name__ == "__main__":
    unittest.main()
