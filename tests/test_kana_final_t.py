import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from kana_reading import transliterate_token


class FinalTTests(unittest.TestCase):
    def test_unambiguous_coda(self):
        for source, expected in {'giqiſatua': 'ヂキサッワ', 'facufatuo': 'ハクハッヲ',
                                 'Xitin': 'シッイン', 'Ietiqi': 'ゼッイキ',
                                 'Butuon': 'ブッヲン', 'Vtut': 'ウッウッ'}.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate_token(source), expected)

    def test_ordinary_syllables_unchanged(self):
        for source, expected in {'chi': 'チ', 'tçu': 'ツ', 'tate': 'タテ',
                                 'tori': 'トリ', 'Batacu': 'バタク'}.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate_token(source), expected)
