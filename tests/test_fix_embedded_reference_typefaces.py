import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fix_embedded_reference_typefaces.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "fix_embedded_reference_typefaces", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EmbeddedReferenceTypefaceTests(unittest.TestCase):
    def test_standalone_s_is_italic_and_absorbs_the_boundary_space(self):
        module = load_module()
        self.assertEqual(
            module.rewrite_content("*Mõte ſolitario.* S."),
            "*Mõte ſolitario. S.*",
        )

    def test_standalone_s_only_mode_does_not_run_other_normalizations(self):
        module = load_module()
        self.assertEqual(
            module.rewrite_content(
                "Adu. Feiq. S.",
                only_standalone_s=True,
            ),
            "Adu. Feiq. *S.*",
        )

    def test_non_body_heading_is_not_restyled_by_process(self):
        module = load_module()
        source = "[h1-l001] **A ANTES DO S.**\n[c1-l001] *Raro.* S.\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bnf-f0001.md"
            path.write_text(source, encoding="utf-8")
            self.assertEqual(
                module.process(path, apply=True, only_standalone_s=True),
                1,
            )
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "[h1-l001] **A ANTES DO S.**\n[c1-l001] *Raro. S.*\n",
            )


if __name__ == "__main__":
    unittest.main()
