"""Conversion fixtures, not assertions that the diplomatic source is infallible."""
import json
from pathlib import Path
import unittest

from scripts.kana_reading import transliterate_token


class KanaCorpusTests(unittest.TestCase):
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
