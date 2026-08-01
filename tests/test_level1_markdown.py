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
        self.assertIn("Validated 9 compact Level 1 page records", result.stdout)

    def test_all_source_pages_parse_and_retain_818_lines(self):
        module = load_module()
        pages = [module.parse_markdown(path) for path in sorted(SOURCE.glob("*.md"))]
        self.assertEqual(len(pages), 9)
        self.assertEqual(
            sum(len(zone.get("lines", [])) for page in pages for zone in page["zones"]),
            818,
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

    def test_line_division_sign_is_uniform_across_typefaces(self):
        source = (SOURCE / "bnf-f0013.md").read_text(encoding="utf-8")
        self.assertIn("Iaponi-*", source)
        self.assertNotIn("Iaponi=", source)

    def test_strengthened_f14_review_is_retained(self):
        source = (SOURCE / "bnf-f0014.md").read_text(encoding="utf-8")
        self.assertIn("status: human_checked", source)
        self.assertIn("mino xita ſaqi.", source)
        self.assertIn("Gordura, vnto, enxundia", source)
        self.assertIn("ate afiuela", source)
        self.assertIn("mino chicaragane", source)
        self.assertIn("mino ya-\n[c1-l010 >] naiba.", source)
        self.assertIn("parte de baxo", source)
        self.assertIn("touçinho", source)
        self.assertIn("Aburaga xi\n[c1-l022 >] mu.", source)
        self.assertIn("Aburauo ſumuru", source)
        self.assertIn("ou paſtas de", source)
        self.assertIn("q̃ vzão pera contra", source)
        self.assertIn("Aburauo tçugu", source)
        self.assertIn("Aburaſaxi, i, Abura tçugui", source)
        self.assertIn("que hum aprende", source)
        self.assertIn("Aquẽtarſe ao fogo", source)
        self.assertNotIn("mino xita laqi.", source)
        self.assertNotIn("Gordura, unto, enxundia", source)
        self.assertNotIn("q̃ vſão pera contra", source)

    def test_repeated_pass_f15_readings_are_retained(self):
        source = (SOURCE / "bnf-f0015.md").read_text(encoding="utf-8")
        self.assertIn("status: scan_confirmed", source)
        self.assertIn("Acano nuqeta te.", source)
        self.assertIn("la menhaã cedo", source)
        self.assertIn("Aca muſubu", source)
        self.assertIn("Per met.", source)
        self.assertIn("briguigoĩs", source)
        self.assertIn("Acagauauodoxi", source)
        self.assertIn("l, ruiuos da", source)
        self.assertIn("Huns rabos", source)
        self.assertIn("comballas", source)
        self.assertIn("Chegar com dedia", source)
        self.assertIn("Acajimi, u, jǔda.", source)
        self.assertIn("meuo faru.", source)
        self.assertIn("vermelho aſsi chamado", source)
        self.assertIn("¶* Vo\n[c2-l042 >] moteuo", source)
        self.assertNotIn("briguigõis", source)
        self.assertNotIn("Vo-", source)

    def test_independent_comparison_f16_readings_are_retained(self):
        source = (SOURCE / "bnf-f0016.md").read_text(encoding="utf-8")
        self.assertIn("status: scan_confirmed", source)
        self.assertIn("Acamidachi, tçu.", source)
        self.assertIn("Acarixǒji.", source)
        self.assertIn("acamiga ſa-", source)
        self.assertNotIn("acamiga fa-", source)
        self.assertIn("ou dẽpres*", source)
        self.assertNotIn("dẽpres-*", source)
        self.assertIn("bom lume. ¶* A-", source)
        self.assertIn("eſtaua tol*", source)
        self.assertIn("diante da cla-*", source)
        self.assertNotIn("A=", source)
        self.assertNotIn("cla=", source)
        self.assertIn("*entrar a claridade*\n[c1-l046]", source)
        self.assertIn("cobrem a ſel*", source)
        self.assertIn("Fiuo aca-", source)
        self.assertNotIn("Fito aca-", source)
        self.assertIn("Sagui yiqu tçuuji", source)
        self.assertNotIn("Saguiyiqu", source)
        self.assertIn("vazzurǒ. *Sõ-*", source)
        self.assertIn("[c2-l026 >] *fir o tempo", source)
        self.assertNotIn("*Sof-*", source)
        self.assertIn("Tçuyi,\n[c2-l047 >] fanani", source)
        self.assertNotIn("Tçuyi-", source)
        self.assertIn("Accô, Varucuchi.", source)
        self.assertIn("[catch-l001 >>] &", source)

    def test_contextual_and_edge_audit_f17_readings_are_retained(self):
        source = (SOURCE / "bnf-f0017.md").read_text(encoding="utf-8")
        self.assertIn("status: scan_confirmed", source)
        self.assertIn("conſideraçaõ", source)
        self.assertIn("da ſaluaçaõ", source)
        self.assertIn("Acuni fuqeru", source)
        self.assertIn("vocaſu. *Peccar", source)
        self.assertIn("ni quamaru.", source)
        self.assertIn("¶ Vt,* Acu\n[c1-l019", source)
        self.assertIn("Idẽ ¶* Acu\n[c1-l025", source)
        self.assertIn("Acuuo ta\n[c1-l030", source)
        self.assertIn("Acugaiuo ſuru", source)
        self.assertIn("ou cõ*\n[c1-l036", source)
        self.assertIn("Acuin. Acuno chinami", source)
        self.assertIn("ou nacimento,como", source)
        self.assertIn("[catch-l001 >>] *mar*", source)
        self.assertNotIn("conſideração", source)
        self.assertNotIn("Acuni fiqeru", source)
        self.assertNotIn("vocaſi.", source)
        self.assertNotIn("quamãru", source)
        self.assertNotIn("nascimento,como", source)

    def test_production_simulation_pages_are_scan_confirmed(self):
        f249 = (SOURCE / "bnf-f0249.md").read_text(encoding="utf-8")
        f250 = (SOURCE / "bnf-f0250.md").read_text(encoding="utf-8")
        self.assertIn("status: scan_confirmed", f249)
        self.assertIn("Gunameqi, u, eita.", f249)
        self.assertIn("Muragari vgoqu.", f249)
        self.assertNotIn("Muragari vgogu.", f249)
        self.assertIn("Icuſano macu.", f249)
        self.assertNotIn("Icuſano inacu.", f249)
        self.assertIn("diuiſa", f249)
        self.assertIn("adiuiſa", f249)
        self.assertIn("status: scan_confirmed", f250)
        self.assertIn("Gũxo.", f250)
        self.assertIn("Gururigururito.", f250)
        self.assertIn("enrrejeitados", f250)
        self.assertNotIn("enrejeitados", f250)
        self.assertIn("[catch-l001 >>] Gǔyô.", f250)


if __name__ == "__main__":
    unittest.main()
