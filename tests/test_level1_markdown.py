import importlib.util
import json
from pathlib import Path
import subprocess
import sys
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
    def test_committed_json_is_generated_from_compact_source(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "compile", str(SOURCE), str(JSON_DIR), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 4 compact Level 1 page records", result.stdout)

    def test_all_source_pages_parse_and_retain_330_lines(self):
        module = load_module()
        pages = [module.parse_markdown(path) for path in sorted(SOURCE.glob("*.md"))]
        self.assertEqual(len(pages), 4)
        self.assertEqual(
            sum(len(zone.get("lines", [])) for page in pages for zone in page["zones"]),
            330,
        )
        for page in pages:
            committed = json.loads((JSON_DIR / f"{page['id']}.json").read_text(encoding="utf-8"))
            self.assertEqual(page, committed)
            self.assertEqual(
                module.export_markdown(page),
                (SOURCE / f"{page['id']}.md").read_text(encoding="utf-8"),
            )

    def test_exceptional_placement_is_readable_and_addressable(self):
        source = (SOURCE / "bnf-f0248.md").read_text(encoding="utf-8")
        self.assertIn("bodaino tçutomeuo naſu.", source)
        self.assertNotIn("tçutomemo", source)
        self.assertIn(
            "[c1-l037 >] *gũ ſenhor principal.* || {mark} *(* || {word}*grande.*",
            source,
        )
        self.assertIn("[c1-l022 >] *amizade. Vt,* Gǒyẽuo motte tanomu.", source)

    def test_contextual_review_corrections_are_retained(self):
        source = (SOURCE / "bnf-f0643.md").read_text(encoding="utf-8")
        self.assertIn("Certa bocetinha de cha.", source)
        self.assertIn("Couſas deſiguaes: vſaſe em", source)
        self.assertNotIn("bocezinha", source)
        self.assertNotIn("deſiguais", source)


if __name__ == "__main__":
    unittest.main()
