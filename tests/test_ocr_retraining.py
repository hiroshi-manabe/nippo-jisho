import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_ocr_retraining_dataset import styled_text, encode, decode, page_splits


class RetrainingTests(unittest.TestCase):
    def test_style_initialization_preserves_character_probability_mass(self):
        import numpy as np
        from train_styled_calamari import duplicate_logits
        old=['','a','ſ']; new=['','a','ſ',chr(0xF0000+ord('a')),chr(0xF0000+ord('ſ'))]
        kernel=np.array([[1.,2.,3.],[4.,5.,6.]])
        bias=np.array([.5,1.,-.5])
        initialized=np.zeros((2,5)); initialized[:,-1]=kernel[:,-1]
        ibias=np.zeros(5); ibias[-1]=bias[-1]
        k,b,n=duplicate_logits(kernel,bias,initialized,ibias,old,new)
        self.assertEqual(n,4)
        x=np.array([.2,.3])
        old_prob=np.exp(x@kernel+bias);old_prob/=old_prob.sum()
        new_prob=np.exp(x@k+b);new_prob/=new_prob.sum()
        np.testing.assert_allclose(old_prob,[new_prob[0]+new_prob[2],new_prob[1]+new_prob[3],new_prob[4]])

    def test_dark_paper_does_not_cause_horizontal_text_trimming(self):
        from PIL import Image, ImageDraw
        from ocr_line_images import prepare_rectified_line
        image=Image.new('L',(1000,100),255)
        draw=ImageDraw.Draw(image)
        draw.rectangle((0,10,999,90),fill=150)
        draw.rectangle((20,25,30,75),fill=0)
        draw.rectangle((900,25,910,75),fill=0)
        result=prepare_rectified_line(image)
        self.assertEqual(result.size,(480,48))
        self.assertLess(result.getpixel((12,24)),100)
        self.assertLess(result.getpixel((434,24)),100)

    def test_ligature_sequence_confusions_are_reported(self):
        from evaluate_ocr_retraining import score
        r={'id':'test','text':'paßa paſſa'}
        result=score([r],['paſſa paßa'],False)
        self.assertEqual(result['double_s']['ß']['as_ſſ'],1)
        self.assertEqual(result['double_s']['ſſ']['as_ß'],1)

    def test_margin_and_fragment_polygons_are_not_full_line_pairs(self):
        from build_ocr_retraining_dataset import full_text_candidates
        def c(x,width):
            return {'centre':[x+width/2,100], 'boundary':[[x,50],[x+width,50],[x+width,120],[x,120]],
                    'recognition':'A'*40}
        dust, fragment, full = c(30,20),c(220,180),c(220,1000)
        self.assertEqual(full_text_candidates([dust,fragment,full],{'box':[140,0,1300,4000]}),[full])

    def test_insertions_do_not_count_as_exact_short_runs(self):
        from evaluate_ocr_retraining import score
        r={'id':'test','text':'Ab','styles':['roman']*2,'encoded':'Ab'}
        result=score([r],['Acb'],True)
        self.assertEqual(result['style']['short_runs_up_to_three_nonspace_characters']['exact_text_and_style'],0)

    def test_dual_style_vocabulary_and_word_score(self):
        from evaluate_ocr_retraining import dual_style_words, score
        records=[{'id':str(i),'text':'Fotoqe','styles':[style]*6,
                  'encoded':encode('Fotoqe',[style]*6)}
                 for i,style in enumerate(['roman','italic'])]
        words=dual_style_words(records)
        self.assertEqual(words, {'fotoqe'})
        result=score(records,['Fotoqe','Fotoqe'],True,words)
        self.assertEqual(result['style']['words_observed_in_both_styles_in_training'],
                         {'reference':2,'text_exact':2,'text_and_style_exact':1})

    def test_inference_decodes_runs_without_exposing_private_labels(self):
        from recognize_nippo_calamari import decode_prediction
        text = 'Fotoqe. Itẽ, paßa.'
        styles = ['roman'] * 8 + ['italic'] * (len(text)-8)
        result = decode_prediction(encode(text, styles), True)
        self.assertEqual(result['text'], text)
        self.assertEqual(result['runs'], [
            {'text': 'Fotoqe. ', 'typeface': 'roman'},
            {'text': 'Itẽ, paßa.', 'typeface': 'italic'},
        ])
        self.assertNotIn('runs', decode_prediction(text, False))

    def test_short_runs_and_boundaries_are_measured(self):
        from evaluate_ocr_retraining import score
        text = 'Ab i. cd'
        styles = ['roman']*3 + ['italic']*3 + ['roman']*2
        record={'id':'test','text':text,'styles':styles,'encoded':encode(text,styles)}
        result=score([record],[record['encoded']],True)
        boundary=result['style']['boundaries_on_correct_characters']
        self.assertEqual(boundary['true_positive'], 2)
        self.assertEqual(boundary['false_negative'], 0)
        self.assertEqual(result['style']['short_runs_up_to_three_nonspace_characters']['exact_text_and_style'],3)

    def test_text_and_style_errors_are_separated(self):
        from evaluate_ocr_retraining import score
        text = 'aſß'
        styles = ['roman', 'italic', 'italic']
        record = {'id': 'test', 'text': text, 'styles': styles, 'encoded': encode(text, styles)}
        result = score([record], [encode(text, ['roman'] * 3)], True)
        self.assertEqual(result['text']['character_error_rate'], 0)
        self.assertAlmostEqual(result['combined']['character_error_rate'], 2/3)
        self.assertAlmostEqual(result['style']['accuracy'], 1/3)
        self.assertNotIn('style', score([record], [text], False))

    def test_style_round_trip_and_diplomatic_characters(self):
        text, styles = styled_text([
            {'text': ' Fotoqe. ', 'typeface': 'roman'},
            {'text': 'paßa ſſ q̃ ǒ ô Itẽ hũa ', 'typeface': 'italic'}])
        decoded, restored = decode(encode(text, styles))
        self.assertEqual(decoded, text)
        for char, before, after in zip(text, styles, restored):
            if not char.isspace():
                self.assertEqual(before, after)

    def test_page_split_preserves_pretraining_holdouts(self):
        import json
        root = Path(__file__).resolve().parents[1]
        old = json.loads((root / 'experiments/ocr/f13-f150-split.json').read_text())
        splits = page_splits()
        self.assertEqual(len(splits), 188)
        for split in ('dev', 'test'):
            self.assertEqual(sum(s == split for s in splits.values()), 19)
            self.assertTrue(all(splits[n] == split for n in old[split]))
        self.assertEqual(splits, page_splits())


if __name__ == '__main__':
    unittest.main()
