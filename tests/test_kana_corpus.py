"""Conversion fixtures, not assertions that the diplomatic source is infallible."""
import json
from pathlib import Path
import unittest

from scripts.kana_reading import transliterate_token, phrase_hint, reading_hint, reading_hint_applicable


class KanaCorpusTests(unittest.TestCase):
    def test_initial_v_before_u_keeps_its_mora(self):
        for token, kana in [('vuo', 'ウヲ'), ('Vuo', 'ウヲ'),
                            ('uo', 'ヲ'), ('vma', 'ウマ'),
                            ('vaqete', 'ワケテ'), ('vonaji', 'オナジ')]:
            with self.subTest(token=token):
                self.assertEqual(transliterate_token(token), kana)
        self.assertEqual(phrase_hint('vuo curuximu'), 'vuo curuximu/ウヲ クルシム')

    def test_nasal_vowels_survive_word_splitting(self):
        for token, expected in [('Fã', 'ハン'), ('Fĩ', 'ヒン'),
                                ('Fũ', 'フン'), ('Fẽ', 'ヘン'), ('Fõ', 'ホン'),
                                ('Fẽbẽ', 'ヘンベン')]:
            with self.subTest(token=token):
                self.assertEqual(phrase_hint(token), f'{token}/{expected}')
        self.assertEqual(phrase_hint('Fe\u0303be\u0303'), 'Fẽbẽ/ヘンベン')
        self.assertEqual(reading_hint([
            {'typeface': 'italic', 'text': 'Vt, '},
            {'typeface': 'roman', 'text': 'Fẽbẽ ſurù.'},
        ]), 'Fẽbẽ ſurù/ヘンベン スルゥ')

    def test_accented_words_do_not_collide_with_labels(self):
        for token in ['xǔ', 'Xǔ', 'xu\u030c', 'xû']:
            with self.subTest(token=token):
                self.assertEqual(transliterate_token(token), 'シュゥ')
        self.assertEqual(phrase_hint('xǔ gozatte'), 'xǔ gozatte/シュゥ ゴザッテ')
        self.assertTrue(reading_hint_applicable([{'typeface': 'roman', 'text': 'xǔ'}]))
        for label in ['X', 'x', 'i', 'S', 'Feiq']:
            with self.subTest(label=label):
                self.assertIsNone(transliterate_token(label))
                self.assertIsNone(phrase_hint(label))
                self.assertFalse(reading_hint_applicable([{'typeface': 'roman', 'text': label}]))

    def test_initial_ii_is_consonantal(self):
        cases = {'Iitai': 'ジタイ', 'iitai': 'ジタイ', 'Jitai': 'ジタイ',
                 'Iiguiuo': 'ジギヲ', 'Iiji': 'ジジ', 'Iiyoni': 'ジヨニ',
                 'Iibucu': 'ジブク', 'Iibucuuo': 'ジブクヲ', 'Iin': 'ジン'}
        for token, expected in cases.items():
            with self.subTest(token=token):
                self.assertEqual(transliterate_token(token), expected)

    def test_internal_ii_and_vocalic_iy_are_unchanged(self):
        for token, expected in [('mochiiru', 'モチイル'),
                                ('catariidaita', 'カタリイダイタ'),
                                ('curiidaſu', 'クリイダス'), ('Iy', 'イイ')]:
            with self.subTest(token=token):
                self.assertEqual(transliterate_token(token), expected)

    def test_attested_spelling_patterns(self):
        cases = json.loads((Path(__file__).parent / 'fixtures/kana-corpus-cases.json').read_text())
        for case in cases:
            with self.subTest(reference=case['ref'], token=case['text']):
                self.assertEqual(transliterate_token(case['text']), case['kana'])

    def test_neighboring_rules_and_unresolved_forms(self):
        for token, expected in [('yama', 'ヤマ'), ('yǔ', 'ユゥ'), ('yô', 'ヨゥ'),
                                ('ye', 'エ'), ('ji', 'ジ'), ('faji', 'ハジ'),
                                ('mame', 'マメ'), ('fumi', 'フミ'),
                                ('xiroi', 'シロイ'), ('coco', 'ココ')]:
            with self.subTest(token=token):
                self.assertEqual(transliterate_token(token), expected)
        # Do not conceal fragments or Portuguese plurals to boost coverage.
        for token in ['cuz', 'Fotoqes', 'c', 'jnaya']:
            with self.subTest(token=token):
                self.assertIsNone(transliterate_token(token))

    def test_vocalic_rules_do_not_override_existing_doubled_consonants(self):
        # Compatibility guards only; these provisional later-page spellings
        # still need contextual review, not silent reinterpretation here.
        self.assertEqual(transliterate_token('Iyyari'), 'イッヤリ')
        self.assertEqual(transliterate_token('Xijjô'), 'シッジョゥ')
