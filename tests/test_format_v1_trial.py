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
    def test_complete_trial_validates(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(TRIAL), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("18462 physical lines", result.stdout)

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

    def test_source_evidence_remains_distinct_from_structure(self):
        f14 = json.loads(
            (TRIAL / "level1" / "bnf-f0014.json").read_text(encoding="utf-8")
        )
        f14_lines = {
            line["id"]: line
            for zone in f14["zones"]
            for line in zone.get("lines", [])
        }
        self.assertEqual(
            "".join(run["text"] for run in f14_lines["c1-l046"]["runs"]),
            "aburamono. Couſa frita.",
        )
        self.assertEqual(
            "".join(run["text"] for run in f14_lines["catch-l001"]["runs"]),
            "Aburico",
        )

        f248 = json.loads(
            (TRIAL / "level1" / "bnf-f0248.json").read_text(encoding="utf-8")
        )
        f248_lines = {
            line["id"]: line
            for zone in f248["zones"]
            for line in zone.get("lines", [])
        }
        displaced = f248_lines["c1-l037"]["runs"]
        self.assertEqual(displaced[0]["text"], "gũ ſenhor principal.")
        self.assertEqual(displaced[1]["text"], " (")
        self.assertEqual(displaced[1]["span_id"], "mark")
        self.assertEqual(displaced[2]["text"], "grande.")
        self.assertEqual(displaced[2]["span_id"], "word")
        self.assertEqual(displaced[1]["placement"], "far-right")
        self.assertEqual(displaced[2]["placement"], "far-right")

        reading_view = (TRIAL / "generated" / "selected-reading-views.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Gozadocoro. Lugar onde eſtá algum ſenhor grande.", reading_view)
        self.assertNotIn("ſenhor (grande", reading_view)
        page_view = (TRIAL / "generated" / "bnf-f0248-page.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("|  *(grande.* |", page_view)

    def test_representative_trial_records_are_complete_and_reviewed(self):
        expected_corrections = {
            "bnf-f0019": [
                "AFIru. Adem.",
                "Agaqi, u, aita.",
                "Te, dãgui, tçuzzumi, gacumon, cu-",
                "l, yǔ yori agaru.",
            ],
            "bnf-f0020": [
                "Fouo",
                "Faitçuge, l. tatamono ni",
                "Gacumõ nadeno irouo aguru.",
                "Aguetçire. i. l. catune.",
            ],
            "bnf-f0021": [
                "cobertoura de baixo",
                "Aguejitomi.",
                "Ameſma tinta.",
                "Vide Varifu.",
                "Noriai. Nauegar",
            ],
            "bnf-f0022": [
                "Vide Cacoi. ô.",
                "Pedroto Ioãoua",
                "aicuchi de gozaru.",
            ],
            "bnf-f0248": [
                "Goxǒuo taſucaru.",
                "Gǒyen. Tçuyoi yen.",
                "Gǒyẽuo motte tanomu.",
                "Guchina.",
                "Gǔcon. Faluno ne.",
                "por erro ſepos na",
            ],
            "bnf-f0643": [
                "Zzuqiǒ.",
                "Zzuſocu. Atama, axi.",
                "Zzuſu.",
                "Zzutçǔ. Caxira itamu.",
            ],
        }
        for page_id, required_strings in expected_corrections.items():
            page = json.loads(
                (TRIAL / "level1" / f"{page_id}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(page["scope"], "full_dictionary_text_and_furniture")
            self.assertTrue(page["review"]["physical_lineation_checked"])
            text = "\n".join(
                "".join(run["text"] for run in line["runs"])
                for zone in page["zones"]
                for line in zone.get("lines", [])
            )
            for required in required_strings:
                self.assertIn(required, text)

        f643 = json.loads(
            (TRIAL / "level1" / "bnf-f0643.json").read_text(encoding="utf-8")
        )
        self.assertTrue(any(zone["kind"] == "later_copy_mark" for zone in f643["zones"]))
        self.assertTrue(any(zone["kind"] == "terminus" for zone in f643["zones"]))

        f249 = json.loads(
            (TRIAL / "level1" / "bnf-f0249.json").read_text(encoding="utf-8")
        )
        f250 = json.loads(
            (TRIAL / "level1" / "bnf-f0250.json").read_text(encoding="utf-8")
        )
        self.assertEqual(f249["review"]["status"], "scan_confirmed")
        self.assertEqual(f250["review"]["status"], "scan_confirmed")
        f249_lines = {
            line["id"]: line
            for zone in f249["zones"]
            for line in zone.get("lines", [])
        }
        displaced = f249_lines["c2-l028"]["runs"]
        self.assertEqual(displaced[1]["span_id"], "mark")
        self.assertEqual(displaced[2]["span_id"], "word")
        self.assertEqual(displaced[2]["text"], "o homem.")

    def test_contextually_confirmed_fold_reading_is_unmarked(self):
        f13 = json.loads(
            (TRIAL / "level1" / "bnf-f0013.json").read_text(encoding="utf-8")
        )
        line = next(
            line
            for zone in f13["zones"]
            for line in zone.get("lines", [])
            if line["id"] == "c1-l010"
        )
        self.assertEqual(line["runs"][0]["text"], "vobitataxiya.")
        self.assertNotIn("uncertainty", line)


if __name__ == "__main__":
    unittest.main()
