import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_character_alignment_pilot import align


def prediction(text):
    return {'position_evidence': {'prepared_size':[100,48], 'raw':{'predictions':[
        {'id':'voted', 'positions':[{'chars':[{'char':c}], 'global_start':10+i*20,
        'global_end':10+i*20} for i,c in enumerate(text)]}]}}}


class AlignmentTest(unittest.TestCase):
    def test_matches(self):
        spans, raw=align('abc',prediction('abc'))
        self.assertEqual(raw,'abc')
        self.assertTrue(all(s['kind']=='matched' for s in spans))

    def test_edits(self):
        for text in ('axc','abxc','ac','xab','abcx'):
            spans,_=align(text,prediction('abc'))
            self.assertEqual(len(spans),len(text))
            self.assertTrue(all(0<=s['left']<=100 and 0<=s['width']<=100 for s in spans))
        spans,_=align('axc',prediction('abc'))
        self.assertEqual(spans[1]['kind'],'uncertain')

    def test_styled(self):
        spans,raw=align('ſ',prediction(chr(0xF0000+ord('ſ'))))
        self.assertEqual(raw,'ſ')
        self.assertEqual(spans[0]['kind'],'matched')
