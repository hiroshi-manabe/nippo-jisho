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
        self.assertIn("Validated 209 compact Level 1 page records", result.stdout)

    def test_all_source_pages_parse_and_retain_20421_lines(self):
        module = load_module()
        pages = [module.parse_markdown(path) for path in sorted(SOURCE.glob("*.md"))]
        self.assertEqual(len(pages), 209)
        self.assertEqual(
            sum(len(zone.get("lines", [])) for page in pages for zone in page["zones"]),
            20421,
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
        self.assertIn("algũa peſsoa", source)
        self.assertIn("cazados, ou amigos", source)
        self.assertIn("dẽpres*\n[c1-l024 >] *tado", source)
        self.assertIn("Acaraſama.", source)
        self.assertIn("Acaraſamana.", source)
        self.assertIn("Acaraſamani.", source)
        self.assertIn("Couſaleue", source)
        self.assertIn("Qinomiga acaramu", source)
        self.assertIn("Eſclarçeo", source)
        self.assertIn("Acariſaqi.", source)
        self.assertIn("Acariſaqini tatçu", source)
        self.assertIn("te menhaã", source)
        self.assertEqual(source.count("antemenhaã"), 2)
        self.assertIn("Paſsar anoite", source)
        self.assertIn("com difficuldade", source)
        self.assertIn("Sagui yuqu tçuuji", source)
        self.assertNotIn("Saguiyiqu", source)
        self.assertNotIn("Sagui yiqu", source)
        self.assertIn("vazzurǒ. *Sõ-*", source)
        self.assertIn("[c2-l026 >] *tir o tempo", source)
        self.assertNotIn("*fir o tempo", source)
        self.assertNotIn("*Sof-*", source)
        self.assertIn("Accô ſuru", source)
        self.assertIn("Adu. Alí, ou là", source)
        self.assertIn("Hũs melõẽs", source)
        self.assertIn("Tçuqi,\n[c2-l047 >] fanani", source)
        self.assertNotIn("Tçuyi,", source)
        self.assertNotIn("Tçuyi-", source)
        self.assertIn("Accô, Varucuchi.", source)
        self.assertIn("[catch-l001 >>] &", source)

    def test_contextual_and_edge_audit_f17_readings_are_retained(self):
        source = (SOURCE / "bnf-f0017.md").read_text(encoding="utf-8")
        self.assertIn("status: scan_confirmed", source)
        self.assertIn("conſideração", source)
        self.assertIn("da ſaluação", source)
        self.assertIn("Acuni fuqeru", source)
        self.assertIn("vocaſu. *Peccar", source)
        self.assertIn("ni quamaru.", source)
        self.assertIn("Acuni tongiacu ſuru", source)
        self.assertIn("Mao religioſo", source)
        self.assertIn("¶ Vt,* Acu\n[c1-l019", source)
        self.assertIn("& goſto de ver a lũa", source)
        self.assertIn("Idẽ. ¶* Acu\n[c1-l025", source)
        self.assertIn("Acuuo ta\n[c1-l030", source)
        self.assertIn("Acugaiuo ſuru", source)
        self.assertIn("ou cõ*\n[c1-l036", source)
        self.assertIn("Acuin. Acuno chinami", source)
        self.assertIn("Ruins penſamen-*", source)
        self.assertIn("ou nacimento,como", source)
        self.assertIn("Couſa danoſa, & preiudicial.*", source)
        self.assertIn("[catch-l001 >>] *mar*", source)
        self.assertEqual(source.count("conſideraçaõ"), 1)
        self.assertNotIn("Iulgar mal, ou errar na conſideraçaõ", source)
        self.assertNotIn("ſaluaçaõ", source)
        self.assertNotIn("toingiacu", source)
        self.assertNotIn("Maoreligioſo", source)
        self.assertNotIn("Acuni fiqeru", source)
        self.assertNotIn("vocaſi.", source)
        self.assertNotIn("quamãru", source)
        self.assertNotIn("nascimento,como", source)
        self.assertNotIn("& gosto de ver a lũa", source)
        self.assertNotIn("Idẽ ¶", source)
        self.assertNotIn("Ruins pensamen-*", source)
        self.assertNotIn("& prejudicial", source)

    def test_f18_human_issue_adjudications_are_retained(self):
        source = (SOURCE / "bnf-f0018.md").read_text(encoding="utf-8")
        accepted = [
            "dano a agluem",
            "acoriǔ. i. docuriû",
            "sǒga miyuru",
            "Acusǒ. Axij caſa",
            "como ladroĩs",
            "Varui sǒ",
            "mà vontade",
            "lugar de ladroĩs",
            "toſu. *Guiar",
            "vnião de vontades",
            "Adano naſaqe",
            "ita. ¶ Item",
            "Peſsoa mudauel",
            "Ruim cheiro",
            "Suſuqino facaina",
            "Acuxinuo ſaxifaſamu",
            "Axij coromo",
            "groſseiro",
        ]
        for reading in accepted:
            self.assertIn(reading, source)
        retained = ["Ruim tradição"]
        for reading in retained:
            self.assertIn(reading, source)
        rejected = [
            "Ruim iradição",
            "Ruim chero",
            "Suiugino facaina",
            "i. acuriû",
            "Acuxinno",
            "Axij coremo",
            "groſſeiro",
        ]
        for reading in rejected:
            self.assertNotIn(reading, source)

    def test_f19_rejected_proposals_reopened_by_glyph_comparison_are_retained(self):
        source = (SOURCE / "bnf-f0019.md").read_text(encoding="utf-8")
        self.assertEqual(source.count("couſa de paruoice"), 2)
        self.assertIn("mais do cus-*", source)
        self.assertNotIn("paruoiçe", source)
        self.assertNotIn("mais do cuſ-*", source)

    def test_sequential_30_60_batch_readings_are_retained(self):
        expected = {
            "bnf-f0023.md": ("dante mão", "Morax, ſu.", "adminiſtrarem"),
            "bnf-f0024.md": ("Padraſto,ou", "A. xirouo"),
            "bnf-f0025.md": ("Fucaqu", "Ajuocaqe", "Poëtas", "u, arta"),
            "bnf-f0026.md": ("beirasdoteihado", "galamiuo", "Amano fara"),
            "bnf-f0027.md": (
                "Bilho de ſaude",
                "Amatçumi iora",
                "Paſsante,ou",
                "comprido,ou",
            ),
        }
        for filename, readings in expected.items():
            source = (SOURCE / filename).read_text(encoding="utf-8")
            self.assertIn("status: scan_confirmed", source)
            for reading in readings:
                self.assertIn(reading, source, f"{reading!r} missing from {filename}")

    def test_normal_bounded_f28_f37_batch_readings_are_retained(self):
        f28 = (SOURCE / "bnf-f0028.md").read_text(encoding="utf-8")
        self.assertIn("Ameni nurete tçuyi voſoroxicarazu", f28)
        self.assertIn("Amey ſameto", f28)
        self.assertIn("Amiuo votçu", f28)
        self.assertIn("Amiuo ſuqu", f28)

        f29 = (SOURCE / "bnf-f0029.md").read_text(encoding="utf-8")
        self.assertIn("[c1-l001 initial=2] AN, iuori.", f29)
        self.assertNotIn("## page-number", f29)

        f31 = (SOURCE / "bnf-f0031.md").read_text(encoding="utf-8")
        self.assertIn("[c2p-l001 initial=2] APPare.", f31)
        self.assertIn("[c2q-l001 initial=2] AQE,", f31)

        f36 = (SOURCE / "bnf-f0036.md").read_text(encoding="utf-8")
        self.assertIn("[c2b-l001 initial=2] ASA.", f36)
        self.assertIn("Aſaboſa", f36)

        f37 = (SOURCE / "bnf-f0037.md").read_text(encoding="utf-8")
        self.assertIn("Aſagaſumi. *Nevoa", f37)
        self.assertIn("Campainha frol azul", f37)
        self.assertNotIn("[c1-l001] Asadachi", f37)

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
