import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.build_public_review import alternate_tilde_carrier, transcription_version


ROOT = Path(__file__).resolve().parents[1]


class PublicReviewRegressionTests(unittest.TestCase):
    def test_public_corpus_exposes_ocr_candidates_without_promoting_them(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "build_public_review.py"),
                    "--output",
                    directory,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            corpus = json.loads(
                (Path(directory) / "corpus.json").read_text(encoding="utf-8")
            )
            reference = (
                Path(directory) / "reference" / "cheat-sheet.html"
            ).read_text(encoding="utf-8")
        pages = {page["page_id"]: page for page in corpus["pages"]}
        self.assertIn("href='../reference.css'", reference)
        states = [page["data_state"] for page in corpus["pages"]]
        self.assertEqual(states.count("canonical_level1"), 229)
        self.assertEqual(states.count("machine_provisional"), 402)
        self.assertEqual(states.count("scan_only"), 20)
        self.assertTrue(
            all(
                line.get("reading_hint_status") in {"available", "unavailable", "not_applicable"}
                for page in corpus["pages"] if page["processed"]
                for zone in page["zones"] for line in zone["lines"]
            )
        )

        initial = pages["bnf-f0238"]
        self.assertTrue(initial["processed"])
        self.assertTrue(initial["machine_provisional"])
        self.assertEqual(initial["provisional_classification"], "initial_batch")
        self.assertEqual(initial["source_label"], "Candidate JSON")

        ordinary = pages["bnf-f0251"]
        self.assertEqual(ordinary["status"], "visual_draft")
        self.assertEqual(ordinary["provisional_classification"], "ordinary_two_column")
        self.assertFalse(ordinary["structural_review_required"])
        self.assertTrue(
            all(
                line.get("crop") and line.get("context_crop")
                for zone in ordinary["zones"]
                if zone["kind"] == "column"
                for line in zone["lines"]
            )
        )

        quarantined = pages["bnf-f0376"]
        self.assertTrue(quarantined["structural_review_required"])
        self.assertIn("page:internal_heading_lines=10", quarantined["provisional_reasons"])

        canonical_control = pages["bnf-f0248"]
        self.assertEqual(canonical_control["data_state"], "canonical_level1")
        self.assertFalse(canonical_control["machine_provisional"])
        self.assertEqual(canonical_control["source_label"], "Source Markdown")
        checked = pages["bnf-f0162"]
        self.assertTrue(checked["ai_checked"])
        self.assertRegex(checked["baseline_commit"], r"^[0-9a-f]{40}$")
        self.assertIn("T", checked["baseline_updated_at"])
        self.assertIn("Fotoqe", corpus["known_roman_terms"])

    def test_external_ai_assignment_stays_concise_and_links_references(self):
        work = ROOT / "pilot" / "human-review" / "ai-geometry-work"
        readme = (work / "README.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(readme.splitlines()), 60)
        for name in ("FORMAT.md", "GEOMETRY-GUIDE.md", "IMPORT-LOG.md"):
            self.assertTrue((work / name).is_file())
            self.assertIn(f"]({name})", readme)

    def test_external_ai_behavioral_example_is_a_real_completed_review(self):
        review_root = ROOT / "pilot" / "human-review"
        example_guide = (
            review_root / "ai-geometry-examples" / "README.md"
        ).read_text(encoding="utf-8")
        reviewed_path = (
            review_root / "ai-geometry-work" / "bnf-f0053-reviewed.json"
        )
        reviewed = json.loads(reviewed_path.read_text(encoding="utf-8"))
        lines = [
            line
            for column in reviewed["columns"].values()
            for line in column["lines"]
        ]

        self.assertIn("../ai-geometry-work/bnf-f0053-reviewed.json", example_guide)
        self.assertEqual(
            reviewed["response_status"], "completed_independent_ai_line_review"
        )
        self.assertTrue(lines)
        self.assertTrue(all(line["observed_text"] is not None for line in lines))
        self.assertTrue(any(line["assessment"] == "uncertain" for line in lines))
        self.assertTrue(any("note" in line for line in lines))

    def test_tilde_carrier_swap_requires_exactly_two_adjacent_vowels(self):
        self.assertEqual(alternate_tilde_carrier("não", 1), "naõ")
        self.assertEqual(alternate_tilde_carrier("huã", 2), "hũa")
        self.assertEqual(alternate_tilde_carrier("poẽ", 2), "põe")
        self.assertIsNone(alternate_tilde_carrier("Gõye", 1))
        self.assertIsNone(alternate_tilde_carrier("casa", 1))

    def test_legacy_external_ai_archive_has_inputs_for_every_return(self):
        work = ROOT / "pilot" / "human-review" / "ai-geometry-work"
        returned = sorted(
            work.glob("bnf-f[0-9][0-9][0-9][0-9]-*.json")
        )
        self.assertTrue(returned)
        returned_pages = {path.name[:9] for path in returned}
        self.assertEqual(
            returned_pages,
            {f"bnf-f{number:04d}" for number in range(31, 126)},
        )
        base_pages = {
            path.stem
            for path in work.glob("bnf-f[0-9][0-9][0-9][0-9].json")
        }
        self.assertEqual(base_pages, returned_pages)
        for page_id in returned_pages:
            record = json.loads((work / f"{page_id}.json").read_text(encoding="utf-8"))
            self.assertEqual(record["page"], page_id)
            self.assertEqual(record["default_response_mode"], "geometry_and_text")

    def test_geometry_only_import_requires_explicit_opt_in(self):
        review = ROOT / "pilot" / "human-review" / "ai-geometry-work" / "bnf-f0042-reviewed.json"
        with tempfile.NamedTemporaryFile(suffix=".json") as geometry:
            geometry.write(
                (ROOT / "pilot" / "human-review" / "line-geometry.json").read_bytes()
            )
            geometry.flush()
            command = [
                "python3",
                str(ROOT / "scripts" / "import_ai_geometry_review.py"),
                str(review),
                "--geometry",
                geometry.name,
                "--reviewed-at",
                "2026-08-13",
            ]
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("AI review is not complete", rejected.stderr)
            accepted = subprocess.run(
                [*command, "--allow-geometry-only"], capture_output=True, text=True
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_completed_review_requires_explicit_transcription_drift_opt_in(self):
        review = ROOT / "pilot" / "human-review" / "ai-geometry-work" / "bnf-f0053-reviewed.json"
        with tempfile.NamedTemporaryFile(suffix=".json") as geometry:
            geometry.write(
                (ROOT / "pilot" / "human-review" / "line-geometry.json").read_bytes()
            )
            geometry.flush()
            command = [
                "python3",
                str(ROOT / "scripts" / "import_ai_geometry_review.py"),
                str(review),
                "--geometry",
                geometry.name,
                "--reviewed-at",
                "2026-08-19",
            ]
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn(
                "canonical transcription differs from the version reviewed by the AI",
                rejected.stderr,
            )
            accepted = subprocess.run(
                [*command, "--allow-transcription-drift"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_edited_lines_preserve_typeface_and_submission_state(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("function styledVisualDiff(line, after)", app)
        self.assertIn("renderStyledSlice(line.runs", app)
        self.assertIn("persistSubmission(page, 'awaiting')", app)
        self.assertIn("persistSubmission(state.currentPage, 'submitted')", app)
        self.assertIn("Did you submit the GitHub Issue?", document)
        self.assertIn("Submit again", document)

    def test_line_editor_has_transcription_character_palette(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        for key, character in {
            "1": "ſ", "2": "ç", "3": "◌̃", "4": "◌̀", "5": "◌́",
            "6": "ǒ", "7": "ǔ", "8": "ô", "9": "û",
        }.items():
            self.assertIn(f"'{key}': {{label: '{character}'", app)
        self.assertIn("function applyDecoration(area, mark)", app)
        self.assertIn("data-character-key", app)
        self.assertIn("Literal digits", app)
        self.assertIn("event.preventDefault()", app)
        self.assertIn(".character-palette", styles)

    def test_automatic_kana_guide_is_build_generated_and_dictionary_aware(self):
        from scripts.kana_reading import reading_hint, transliterate_token

        self.assertEqual(transliterate_token("Aqiraca"), "アキラカ")
        self.assertEqual(transliterate_token("Fanauo"), "ハナヲ")
        self.assertEqual(transliterate_token("cutçuuauo"), "クツワヲ")
        self.assertEqual(transliterate_token("Vmani"), "ウマニ")
        self.assertEqual(transliterate_token("Vôqina"), "オゥキナ")
        self.assertEqual(transliterate_token("canaxij"), "カナシイ")
        self.assertEqual(transliterate_token("Xiraſagui"), "シラサギ")
        self.assertEqual(transliterate_token("Fague"), "ハゲ")
        self.assertIsNone(transliterate_token("i"))
        self.assertIsNone(transliterate_token("Vt"))
        self.assertIsNone(reading_hint([{"typeface": "roman", "text": "i."}]))
        self.assertEqual(
            reading_hint([{"typeface": "roman", "text": "i, Cami."}]),
            "Cami/カミ",
        )
        self.assertEqual(
            reading_hint([
                {"typeface": "roman", "text": "Facuran. Firoqu miru. "},
                {"typeface": "italic", "text": "Grande estudo, ou"},
            ]),
            "Facuran/ハクラン, Firoqu miru/ヒロク ミル",
        )
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        self.assertIn("line.reading_hint", app)
        self.assertIn("Automatic reading unavailable", app)

    def test_collapsed_line_quick_edits_are_reversible_and_schema_neutral(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        helper = (ROOT / "site" / "quick-edit.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        builder = (ROOT / "scripts" / "build_public_review.py").read_text(encoding="utf-8")
        workflow = (ROOT / "docs" / "human-review-workflow.md").read_text(encoding="utf-8")
        self.assertIn('<script src="quick-edit.js"></script>', document)
        self.assertIn('"quick-edit.js",', builder)
        self.assertIn("const DELETABLE = new Set([' ', '-', ',', '.'])", helper)
        self.assertIn("function applyQuickEdit(row, control)", app)
        self.assertIn('data-quick-action="restore"', app)
        self.assertIn(".quick-deleted", styles)
        self.assertIn("copied schema-2 correction JSON", workflow)

        script = r"""
const q = require('./site/quick-edit.js');
function equal(actual, expected) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${JSON.stringify(actual)} !== ${JSON.stringify(expected)}`);
  }
}
equal([q.nextSForm('s', 's'), q.nextSForm('ſ', 's')], ['ſ', 's']);
equal([q.nextSForm('ſ', 'ſ'), q.nextSForm('s', 'ſ'), q.nextSForm('f', 'ſ')], ['s', 'f', 'ſ']);
equal([q.nextSForm('f', 'f'), q.nextSForm('ſ', 'f')], ['ſ', 'f']);
equal([q.nextGQ('g'), q.nextGQ('q'), q.nextGQ('G'), q.nextGQ('Q')], ['q', 'g', 'Q', 'G']);
equal([q.nextNM('n'), q.nextNM('m'), q.nextNM('N'), q.nextNM('M')], ['m', 'n', 'N', 'M']);
equal(q.nextPostvocalicNasal('n', 'n', 'a', 't'), {kind: 'replace', value: 'm'});
equal(q.nextPostvocalicNasal('m', 'n', 'a', 't'), {kind: 'contract', value: 'ã'});
equal(q.nextPostvocalicNasal('m', 'm', 'e', 'b'), {kind: 'replace', value: 'n'});
equal(q.nextPostvocalicNasal('n', 'm', 'e', 'b'), {kind: 'contract', value: 'ẽ'});
equal(q.nextPostvocalicNasal('n', 'n', 'a', 'i'), {kind: 'replace', value: 'm'});
equal([q.nextCedilla('c'), q.nextCedilla('ç'), q.nextCedilla('C'), q.nextCedilla('Ç')], ['ç', 'c', 'C', 'Ç']);
equal(['u', 'v', 'ũ', 'ù', 'ú', 'û', 'ǔ'].map(value => q.nextUV(value, 'u')), ['v', 'ũ', 'ù', 'ú', 'û', 'ǔ', 'u']);
equal(['v', 'u'].map(value => q.nextUV(value, 'v')), ['u', 'v']);
equal([q.nextUV('U', 'U'), q.nextUV('V', 'V')], ['U', 'V']);
equal(['i', 'j', 'ĩ', 'ì', 'í', 'î'].map(value => q.nextIJ(value, 'i')), ['j', 'ĩ', 'ì', 'í', 'î', 'i']);
equal(['j', 'i'].map(value => q.nextIJ(value, 'j')), ['i', 'j']);
equal([q.nextIJ('I', 'I'), q.nextIJ('J', 'J')], ['I', 'J']);
equal([q.nextVowel('o', 'o'), q.nextVowel('õ', 'o'), q.nextVowel('ò', 'o')], ['õ', 'ò', 'ó']);
equal(['ǒ', 'ô', 'o', 'õ', 'ò', 'ó'].map(value => q.nextVowel(value, 'ǒ')), ['ô', 'o', 'õ', 'ò', 'ó', 'ǒ']);
equal(['ô', 'ǒ', 'o', 'õ', 'ò', 'ó'].map(value => q.nextVowel(value, 'ô')), ['ǒ', 'o', 'õ', 'ò', 'ó', 'ô']);
equal(['ǔ', 'û', 'u', 'ũ', 'ù', 'ú'].map(value => q.nextVowel(value, 'ǔ')), ['û', 'u', 'ũ', 'ù', 'ú', 'ǔ']);
equal(['û', 'ǔ', 'u', 'ũ', 'ù', 'ú'].map(value => q.nextVowel(value, 'û')), ['ǔ', 'u', 'ũ', 'ù', 'ú', 'û']);
equal([q.nextVowel('Ǒ', 'Ǒ'), q.nextVowel('Ô', 'Ô')], ['Ô', 'Ǒ']);
equal(q.replace('[F]oo, bar.', 3, 4, ''), '[F]oo bar.');
equal(q.replace('[F]oo bar.', 3, 3, ',', null), '[F]oo, bar.');
const knownRoman = new Set(['Fotoqe', 'Dairi']);
equal(q.knownTypefaceTokenRange('do Fotoqe.', 3, knownRoman), {start: 3, end: 9});
equal(q.knownTypefaceTokenRange('do Fotoqe.', 7, knownRoman), {start: 3, end: 9});
equal(q.knownTypefaceTokenRange('do Unknown.', 4, knownRoman), null);
equal(q.typefaceTokenRange('i. l. word.', 0), {start: 0, end: 2});
equal(q.typefaceTokenRange('i. l. word.', 3), {start: 3, end: 5});
equal(q.typefaceTokenRange('i. l. word.', 1), null);
equal(q.typefaceTokenRange('word.', 0), null);
equal(q.typefaceTokenRange('i, l, word', 0), {start: 0, end: 1});
equal(q.typefaceTokenRange('i, l, word', 3), {start: 3, end: 4});
equal(q.typefaceTokenRange('word l', 5), {start: 5, end: 6});
equal(q.typefaceTokenRange('a, l', 0), null);
equal(q.typefaceTokenRange('word', 3), null);
equal(q.typefaceTokenRange('S. X. a.', 0), {start: 0, end: 2});
equal(q.typefaceTokenRange('S. X. a.', 3), {start: 3, end: 5});
equal(q.typefaceTokenRange('S. X. a.', 6), null);
equal(q.toggleTypefaceRange('S.', 0, 2, ['italic', 'italic']), '[S.]');
equal(q.toggleTypefaceRange('[S.]', 0, 2, ['italic', 'italic']), 'S.');
equal(q.toggleTypefaceRange('i.', 0, 2, ['roman', 'roman']), '{i.}');
equal(q.toggleTypefaceRange('{i.}', 0, 2, ['roman', 'roman']), 'i.');
equal(q.toggleTypefaceRange('l', 0, 1, ['roman']), '{l}');
equal(q.toggleTypefaceRange('{l}', 0, 1, ['roman']), 'l');
equal(q.align('foo, bar.', 'foo bar.').deletions.map(item => [item.character, item.currentIndex]), [[',', 3]]);
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_page_status_and_known_roman_typeface_controls_are_data_driven(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        helper = (ROOT / "site" / "quick-edit.js").read_text(encoding="utf-8")
        builder = (ROOT / "scripts" / "build_public_review.py").read_text(encoding="utf-8")
        styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("function renderReviewStatus(page)", app)
        self.assertIn("function checkCorpusFreshness()", app)
        self.assertIn("knownTypefaceTokenRange", app)
        self.assertNotIn("isItalicWordInitial", app)
        self.assertNotIn("uppercasePeriodTokenRange", helper)
        self.assertIn("known_roman_terms", builder)
        self.assertIn("baseline_updated_at", builder)
        self.assertIn(".review-status", styles)

    def test_qualified_ocr_hyphen_suggestions_seed_reversible_edits(self):
        suggestions = json.loads(
            (
                ROOT
                / "pilot"
                / "human-review"
                / "ocr-hyphen-suggestions.json"
            ).read_text(encoding="utf-8")
        )
        counts = {
            page["id"]: len(page["suggestions"])
            for page in suggestions["pages"]
        }
        self.assertEqual(
            counts,
            {
                "bnf-f0154": 8,
                "bnf-f0155": 3,
                "bnf-f0156": 9,
                "bnf-f0157": 13,
                "bnf-f0158": 1,
                "bnf-f0159": 5,
                "bnf-f0160": 3,
            },
        )
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        workflow = (ROOT / "docs" / "human-review-workflow.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("function seedMachineSuggestions(page)", app)
        self.assertIn("dismissed_suggestions", app)
        self.assertIn("OCR: no hyphen", app)
        self.assertIn("quick-suggested", styles)
        self.assertIn("ordinary correction", workflow)

        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "build_public_review.py"),
                    "--output",
                    directory,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            corpus = json.loads(
                (Path(directory) / "corpus.json").read_text(encoding="utf-8")
            )
        pages = {page["page_id"]: page for page in corpus["pages"]}
        f155_lines = {
            line["id"]: line
            for zone in pages["bnf-f0155"]["zones"]
            for line in zone["lines"]
        }
        self.assertEqual(
            f155_lines["c1a-l007"]["machine_suggestions"],
            ["ocr_terminal_hyphen"],
        )
        f154_lines = {
            line["id"]: line
            for zone in pages["bnf-f0154"]["zones"]
            for line in zone["lines"]
        }
        self.assertNotIn("machine_suggestions", f154_lines["c1-l014"])

    def test_line_editor_supports_paired_lightweight_typeface_spans(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        workflow = (ROOT / "docs" / "human-review-workflow.md").read_text(encoding="utf-8")
        issue_template = (ROOT / ".github" / "ISSUE_TEMPLATE" / "transcription-correction.md").read_text(encoding="utf-8")
        self.assertIn("function parseTypefaceNotation(value)", app)
        self.assertIn("function proposalMatchesLine(line, annotatedText)", app)
        self.assertIn("function styledTypefaceDiff(line, proposal)", app)
        self.assertIn("function applyTypefaceSpan(area, typeface)", app)
        self.assertIn('data-action="typeface-span"', app)
        self.assertIn('data-typeface="roman"', app)
        self.assertIn('data-typeface="italic"', app)
        self.assertIn(".typeface-span-key", styles)
        self.assertIn("`[Fotoqe]`", workflow)
        self.assertIn("`{P.}`", workflow)
        self.assertIn("`[Fotoqe]`", issue_template)
        self.assertIn("`{P.}`", issue_template)

    def test_opening_another_line_saves_the_active_editor(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        workflow = (ROOT / "docs" / "human-review-workflow.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("function saveEditor(form)", app)
        self.assertIn("const activeForm = document.querySelector('.edit-form')", app)
        self.assertIn("if (!saveEditor(activeForm)) return", app)
        self.assertIn("if (saveEditor(form)) renderPageContent()", app)
        self.assertIn("Opening another line has the same save-and-collapse effect", workflow)

    def test_enter_confirms_the_physical_line_editor(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        workflow = (ROOT / "docs" / "human-review-workflow.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("if (event.key === 'Enter')", app)
        self.assertIn("if (saveEditor(area.form)) renderPageContent()", app)
        self.assertIn("Pressing **Enter** in the transcription field", workflow)

    def test_correction_submission_separates_notes_and_ai_messages(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "site" / "styles.css").read_text(encoding="utf-8")
        workflow = (ROOT / "docs" / "human-review-workflow.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('name="note"', app)
        self.assertIn('name="message"', app)
        self.assertNotIn('name="second-opinion"', app)
        self.assertIn("note_before", app)
        self.assertIn("note_after", app)
        self.assertIn("{ schema: 3, page: page.view", app)
        self.assertIn("Any nonempty message requires AI inspection", workflow)

    def test_page_view_has_explicit_overview_control(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="back-to-overview"', document)
        self.assertIn("← All pages", document)
        self.assertIn("$('#back-to-overview').addEventListener('click', () => showOverview())", app)

    def test_column_views_have_continuous_top_and_bottom_navigation(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="column-nav-top"', document)
        self.assertIn("function columnSequence()", app)
        self.assertIn("← Previous column", app)
        self.assertIn("Next column →", app)
        self.assertIn("columnNavigationHTML('column-nav-bottom')", app)
        self.assertIn("[data-column-leaf][data-column-unit]", app)
        self.assertIn("window.scrollTo(0, 0)", app)

    def test_column_views_include_split_zone_names(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        self.assertIn("zone.id.includes(unit)", app)
        self.assertIn(
            "zonesFor(page, state.unit).filter(item => item.kind === 'column')",
            app,
        )

    def test_f18_acuxocu_crop_is_centered_and_has_overlap(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in record["pages"] if page["id"] == "bnf-f0018")
        line = page["columns"]["column-2"]["lines"]["c2a-l018"]
        self.assertEqual(line["centre_y"], 1498)
        self.assertEqual(line["crop"], [1581, 1438, 1041, 120])

    def test_f24_folgar_descender_is_not_clipped(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in record["pages"] if page["id"] == "bnf-f0024")
        line = page["columns"]["column-2"]["lines"]["c2-l023"]
        self.assertEqual(line["crop"], [1537, 1790, 1085, 150])

    def test_f24_aixiri_is_the_crop_focus(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in record["pages"] if page["id"] == "bnf-f0024")
        column = page["columns"]["column-2"]
        self.assertEqual(column["visual_review"], "text_image_sanity_checked")
        self.assertEqual(column["lines"]["c2-l041"]["crop"], [1535, 2938, 1091, 122])

    def test_f138_column_2_final_line_descenders_are_not_clipped(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in record["pages"] if page["id"] == "bnf-f0138")
        column = page["columns"]["column-2"]
        self.assertEqual(column["visual_review"], "line_by_line_reverified")
        self.assertEqual(column["lines"]["c2-l001"]["crop"], [1500, 405, 1120, 100])
        self.assertEqual(column["lines"]["c2-l024"]["crop"], [1500, 1878, 1120, 100])
        self.assertEqual(column["lines"]["c2-l047"]["crop"], [1500, 3350, 1120, 100])

    def test_f135_bottom_right_fragment_is_the_catchword(self):
        page = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0135.json").read_text(
                encoding="utf-8"
            )
        )
        zones = {zone["id"]: zone for zone in page["zones"]}
        self.assertEqual(zones["column-2"]["lines"][-1]["id"], "c2-l047")
        self.assertEqual(zones["catchword"]["lines"][0]["id"], "cw-l001")
        self.assertEqual(zones["catchword"]["lines"][0]["runs"][0]["text"], "riuo")

        geometry = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        geometry_page = next(item for item in geometry["pages"] if item["id"] == "bnf-f0135")
        self.assertNotIn("c2-l048", geometry_page["columns"]["column-2"]["lines"])

    def test_manually_corrected_columns_reach_past_the_right_rule(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        pages = {page["id"]: page for page in record["pages"]}
        corrected_columns = {
            ("bnf-f0070", "column-1"): 1560,
            ("bnf-f0072", "column-1"): 1560,
            ("bnf-f0072", "column-2"): 2660,
        }
        for number in range(73, 86):
            corrected_columns[(f"bnf-f{number:04d}", "column-2")] = (
                2422 if number % 2 else 2660
            )
        for number in (74, 76, 78, 80, 82, 84, 86, 88):
            corrected_columns[(f"bnf-f{number:04d}", "column-1")] = 1560
        for (page_id, column_id), right_edge in corrected_columns.items():
            with self.subTest(page=page_id, column=column_id):
                column = pages[page_id]["columns"][column_id]
                self.assertEqual(column["box"][2], right_edge)
                for line in column["lines"].values():
                    self.assertEqual(
                        line["crop"][0] + line["crop"][2], right_edge
                    )
                    self.assertEqual(
                        line["context_crop"][0] + line["context_crop"][2],
                        right_edge,
                    )

    def test_f25_through_f30_received_text_image_sanity_check(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        pages = {page["id"]: page for page in record["pages"]}
        for number in range(25, 31):
            with self.subTest(page=number):
                page = pages[f"bnf-f{number:04d}"]
                for column in page["columns"].values():
                    self.assertEqual(
                        column["visual_review"], "text_image_sanity_checked"
                    )

    def test_external_ai_geometry_has_complete_horizontal_coverage(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        pages = [
            page for page in record["pages"]
            if any(column.get("review_source") for column in page.get("columns", {}).values())
        ]
        self.assertEqual(
            [page["id"] for page in pages],
            [f"bnf-f{number:04d}" for number in range(31, 126)],
        )
        for page in pages:
            for column in page["columns"].values():
                if not column.get("review_source"):
                    continue
                horizontal_review = column.get("horizontal_completeness_review")
                if horizontal_review:
                    self.assertIn(
                        column["visual_review"],
                        {"external_ai_width_rechecked", "ai_line_by_line_checked"},
                    )
                    self.assertEqual(
                        horizontal_review["status"],
                        "complete_column_width_checked",
                    )
                else:
                    self.assertIn(
                        column["visual_review"],
                        {"ai_bulk_geometry_sanity_checked", "ai_line_by_line_checked"},
                    )
                left, _, right, _ = column["box"]
                for line in column["lines"].values():
                    self.assertEqual(line["crop"][0], left)
                    self.assertEqual(line["crop"][0] + line["crop"][2], right)
                    self.assertEqual(line["context_crop"][0], left)
                    self.assertEqual(
                        line["context_crop"][0] + line["context_crop"][2], right
                    )

        f105 = next(page for page in record["pages"] if page["id"] == "bnf-f0105")
        self.assertTrue(
            all(
                column.get("review_source", "").endswith("-reviewed-redone.json")
                for column in f105["columns"].values()
            )
        )
        final_line = f105["columns"]["column-2"]["lines"]["c2-l047"]
        self.assertGreaterEqual(final_line["crop"][1] + final_line["crop"][3], 3380)

    def test_f94_external_review_preserves_adjudicated_lineation(self):
        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0094.json").read_text(
                encoding="utf-8"
            )
        )
        line_ids = {
            line["id"]
            for zone in record["zones"]
            for line in zone.get("lines", [])
        }
        self.assertEqual(len([line for line in line_ids if line.startswith("c1-")]), 47)
        self.assertNotIn("c1-l048", line_ids)

    def test_f125_displaced_continuation_is_not_a_fictitious_line(self):
        record = json.loads(
            (ROOT / "pilot" / "format-v1-trial" / "level1" / "bnf-f0125.json").read_text(
                encoding="utf-8"
            )
        )
        column = next(zone for zone in record["zones"] if zone["id"] == "column-2")
        self.assertEqual(len(column["lines"]), 47)
        displaced_line = next(line for line in column["lines"] if line["id"] == "c2-l008")
        displaced = [run for run in displaced_line["runs"] if run.get("placement") == "far-right"]
        self.assertEqual([run.get("span_id") for run in displaced], ["mark", "word"])
        self.assertEqual("".join(run["text"] for run in displaced), " (midade.")
        self.assertEqual(column["lines"][-1]["id"], "c2-l047")

    def test_transcription_versions_and_rebase_controls(self):
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        document = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        builder = (ROOT / "scripts" / "build_public_review.py").read_text(encoding="utf-8")
        self.assertIn('"transcription_version": transcription_version(zones)', builder)
        self.assertIn("const WORKSPACE_SCHEMA = 5", app)
        self.assertIn("function reconcileEdits(page, edits)", app)
        self.assertIn("comment_review_needed", app)
        self.assertIn("base_line_version", app)
        self.assertIn("base_transcription_version", app)
        self.assertIn("Saved corrections updated", document)
        self.assertIn("Copy orphaned corrections", document)
        self.assertIn("Discard orphaned corrections", document)

    def test_transcription_version_ignores_geometry_but_tracks_text_and_style(self):
        zones = [{"lines": [{
            "id": "c1-l001",
            "text": "Abc def",
            "runs": [
                {"typeface": "roman", "text": "Abc "},
                {"typeface": "italic", "text": "def"},
            ],
            "crop": [1, 2, 3, 4],
        }]}]
        baseline = transcription_version(zones)
        zones[0]["lines"][0]["crop"] = [9, 8, 7, 6]
        self.assertEqual(transcription_version(zones), baseline)
        zones[0]["lines"][0]["runs"][1]["typeface"] = "roman"
        self.assertNotEqual(transcription_version(zones), baseline)

    def test_transcription_version_tracks_large_initial_layout(self):
        zones = [{"lines": [{
            "id": "c1-l001",
            "text": "AFIru.",
            "runs": [
                {"typeface": "roman", "text": "A"},
                {"typeface": "roman", "text": "FIru."},
            ],
        }]}]
        baseline = transcription_version(zones)
        zones[0]["lines"][0]["runs"][0].update(
            {"layout": "large-initial", "line_span": 2}
        )
        self.assertNotEqual(transcription_version(zones), baseline)

    def test_large_initial_crops_contain_the_complete_two_line_glyph(self):
        record = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            "bnf-f0018": [("column-2", "c2b-l001")],
            "bnf-f0019": [
                ("column-1", "c1b-l001"),
                ("column-2", "c2b-l001"),
            ],
            "bnf-f0021": [("column-2", "c2b-l001")],
            "bnf-f0025": [("column-2", "c2b-l001")],
            "bnf-f0029": [("column-1", "c1-l001")],
            "bnf-f0031": [
                ("column-2", "c2p-l001"),
                ("column-2", "c2q-l001"),
            ],
            "bnf-f0033": [("column-1", "c1b-l001")],
            "bnf-f0036": [("column-2", "c2b-l001")],
            "bnf-f0038": [("column-2", "c2b-l001")],
            "bnf-f0041": [("column-2", "c2-l001")],
            "bnf-f0043": [("column-2", "c2b-l001")],
            "bnf-f0045": [("column-1", "c1b-l001")],
            "bnf-f0046": [("column-1", "c1b-l001")],
            "bnf-f0047": [("column-1", "c1b-l001")],
            "bnf-f0053": [("column-1", "c1b-l001")],
            "bnf-f0055": [("column-1", "c1b-l001")],
            "bnf-f0058": [("column-2", "c2b-l001")],
            "bnf-f0062": [("column-2", "c2b-l001")],
            "bnf-f0068": [("column-2", "c2b-l001")],
            "bnf-f0248": [("column-2", "c2b-l001")],
        }
        pages = {page["id"]: page for page in record["pages"]}
        for page_id, lines in expected.items():
            for column_id, line_id in lines:
                crop = pages[page_id]["columns"][column_id]["lines"][line_id]["crop"]
                self.assertGreaterEqual(crop[3], 158)

    def test_f49_c1_l039_has_its_own_line_crop(self):
        geometry = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in geometry["pages"] if page["id"] == "bnf-f0049")
        lines = page["columns"]["column-1"]["lines"]
        line_39 = lines["c1-l039"]
        line_40 = lines["c1-l040"]
        self.assertEqual(line_39["centre_y"], 2781)
        self.assertEqual(line_39["crop"], [140, 2732, 1125, 98])
        self.assertGreaterEqual(line_40["centre_y"] - line_39["centre_y"], 50)

    def test_f49_column_2_opening_crops_follow_distinct_lines(self):
        geometry = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in geometry["pages"] if page["id"] == "bnf-f0049")
        lines = page["columns"]["column-2"]["lines"]
        centres = [lines[f"c2-l{number:03d}"]["centre_y"] for number in range(1, 10)]
        self.assertEqual(centres, [447, 509, 571, 633, 695, 757, 819, 881, 943])
        self.assertTrue(all(right - left == 62 for left, right in zip(centres, centres[1:])))

    def test_f50_column_1_late_crops_follow_the_printed_lines(self):
        geometry = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        page = next(page for page in geometry["pages"] if page["id"] == "bnf-f0050")
        lines = page["columns"]["column-1"]["lines"]
        centres = [lines[f"c1-l{number:03d}"]["centre_y"] for number in range(29, 48)]
        self.assertEqual(
            centres,
            [
                2207,
                2269,
                2329,
                2408,
                2473,
                2538,
                2600,
                2663,
                2726,
                2789,
                2855,
                2918,
                2981,
                3045,
                3098,
                3163,
                3220,
                3285,
                3346,
            ],
        )
        self.assertTrue(
            all(right - left >= 50 for left, right in zip(centres, centres[1:]))
        )

        reviewed = json.loads(
            (
                ROOT
                / "pilot"
                / "human-review"
                / "ai-geometry-work"
                / "bnf-f0050-reviewed.json"
            ).read_text(encoding="utf-8")
        )
        reviewed_lines = {
            line["id"]: line
            for column in reviewed["columns"].values()
            for line in column["lines"]
        }
        self.assertEqual(
            [reviewed_lines[f"c1-l{number:03d}"]["centre_y"] for number in range(29, 48)],
            centres,
        )

        column_2_lines = page["columns"]["column-2"]["lines"]
        column_2_centres = [
            column_2_lines[f"c2-l{number:03d}"]["centre_y"]
            for number in range(35, 48)
        ]
        self.assertEqual(
            column_2_centres,
            [2578, 2637, 2702, 2763, 2832, 2889, 2950, 3013, 3078, 3138, 3200, 3263, 3328],
        )
        self.assertTrue(
            all(
                right - left >= 50
                for left, right in zip(column_2_centres, column_2_centres[1:])
            )
        )
        self.assertEqual(
            [reviewed_lines[f"c2-l{number:03d}"]["centre_y"] for number in range(35, 48)],
            column_2_centres,
        )

    def test_f56_f60_line_by_line_geometry_reviews_are_recorded(self):
        geometry = json.loads(
            (ROOT / "pilot" / "human-review" / "line-geometry.json").read_text(
                encoding="utf-8"
            )
        )
        reviewed_pages = {
            page["id"]: page
            for page in geometry["pages"]
            if page["id"] in {f"bnf-f{leaf:04d}" for leaf in range(56, 61)}
        }
        self.assertEqual(
            sum(
                len(column["lines"])
                for page in reviewed_pages.values()
                for column in page["columns"].values()
            ),
            470,
        )
        for page in reviewed_pages.values():
            for column in page["columns"].values():
                self.assertEqual(column["visual_review"], "ai_line_by_line_checked")
                self.assertRegex(
                    column["review_source"],
                    r"bnf-f00(?:56|57|58|59|60)-reviewed\.json$",
                )

if __name__ == "__main__":
    unittest.main()
