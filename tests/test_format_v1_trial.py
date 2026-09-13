import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
from unittest import mock


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
    def test_selected_render_preserves_other_page_views(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'level1').mkdir()
            for pid in ('page-a', 'page-b'):
                (root / 'level1' / (pid + '.json')).write_text(json.dumps({'id': pid}))
            (root / 'level2').mkdir()
            (root / 'level2/selected-structure.json').write_text('{}')
            output = root / 'generated'
            output.mkdir()
            (output / 'page-b-page.md').write_text('keep existing preview')
            with (mock.patch.object(module, 'validate_page', return_value={}),
                  mock.patch.object(module, 'validate_structure'),
                  mock.patch.object(module, 'render_page', side_effect=lambda p: p['id']),
                  mock.patch.object(module, 'render_sequences', return_value='shared'),
                  mock.patch.object(sys, 'argv', ['render', str(root), '--pages', 'page-a'])):
                self.assertEqual(module.main(), 0)
            self.assertEqual((output / 'page-a-page.md').read_text(), 'page-a')
            self.assertEqual((output / 'page-b-page.md').read_text(), 'keep existing preview')


    def test_complete_trial_validates(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(TRIAL), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"Validated \d+ page records, \d+ physical lines")

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


    def test_trial_records_have_complete_scope_and_explicit_lineation_state(self):
        pages = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((TRIAL / "level1").glob("*.json"))
        ]
        self.assertTrue(pages)
        self.assertEqual({page['id'] for page in pages},
                         {path.stem for path in (TRIAL / 'level1-source').glob('*.md')})
        for page in pages:
            self.assertEqual(page["scope"], "full_dictionary_text_and_furniture")
            self.assertIsInstance(page["review"]["physical_lineation_checked"], bool)



if __name__ == "__main__":
    unittest.main()
