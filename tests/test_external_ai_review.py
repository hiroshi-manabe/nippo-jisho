import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import external_ai_review as review

MD = '''---
format: nippo-level1-markdown
version: 1
id: bnf-f0216
source: BnF Gallica
view: f216
url: https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f216.item
sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
scope: full_dictionary_text_and_furniture
origin: calamari_v2_machine_provisional
wikisource: false
lineation: checked
status: visual_draft
---

## column-1 [column] Column 1

[c1-l001] Fito. *Homem.*
'''.encode()


class ExternalReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pid = 'bnf-f0216'
        self.geometry = {'id': self.pid, 'source_size': [100, 200], 'columns': {
            'column-1': {'lines': {'c1-l001': {'crop': [0, 0, 100, 20]}}}}}
        self.geom = {'source_size': [100, 200], 'crops': {'c1-l001': [0, 0, 100, 20]}}
        self.inputs = {'targets/page.md': MD, 'targets/geometry.json': review.encoded(self.geom)}
        m = {'schema': 1, 'package_id': 'test', 'mode': 'production', 'baseline_commit': 'abc',
             'pages': {self.pid: {'input_prefix': 'targets', 'source_sha256': review.sha(MD),
                 'geometry_sha256': review.sha(review.encoded(self.geometry))}},
             'files': {k: review.sha(v) for k, v in self.inputs.items()}}
        self.inputs['manifest.json'] = review.encoded(m)
        self.result = {'schema': 1, 'package_id': 'test', 'input_manifest_sha256': review.sha(self.inputs['manifest.json']),
            'reviewer': 'Test reviewer', 'pages': {self.pid: {'first_pass': True, 'second_pass': True,
            'crops_inspected': True, 'uncertainties': [], 'structural_changes': [], 'typeface_terms': {}}}}
        self.outputs = {f'pages/{self.pid}.md': MD + b'[c1-l001 note] Fito is a person; the Portuguese gloss is homem.\n',
                        f'pages/{self.pid}.geometry.json': review.encoded(self.geom)}
        self.input = self.root / 'input.zip'
        self.output = self.root / 'result.zip'
        review.write_zip(self.input, self.inputs)

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.outputs['result.json'] = review.encoded(self.result)
        review.write_zip(self.output, self.outputs)

    def check(self):
        self.save()
        return review.validate(self.input, self.output, True)

    def test_valid_and_roundtrip(self):
        _, _, pages = self.check()
        page = pages[self.pid][0]
        self.assertEqual(review.parse(review.export_markdown(page).encode()), page)

    def test_wrong_manifest(self):
        self.result['input_manifest_sha256'] = 'bad'
        with self.assertRaisesRegex(ValueError, 'manifest'):
            self.check()

    def test_missing_pass(self):
        self.result['pages'][self.pid]['second_pass'] = False
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.check()

    def test_missing_note(self):
        self.outputs[f'pages/{self.pid}.md'] = MD
        with self.assertRaisesRegex(ValueError, 'commentary'):
            self.check()

    def test_bad_crop(self):
        self.geom['crops']['c1-l001'] = [0, 0, 101, 20]
        self.outputs[f'pages/{self.pid}.geometry.json'] = review.encoded(self.geom)
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.check()

    def test_structure(self):
        self.outputs[f'pages/{self.pid}.md'] = self.outputs[f'pages/{self.pid}.md'].replace(b'c1-l001', b'c1-l002')
        with self.assertRaisesRegex(ValueError, 'structural'):
            self.check()

    def test_typeface_change_allowed(self):
        self.outputs[f'pages/{self.pid}.md'] = self.outputs[f'pages/{self.pid}.md'].replace(b'Fito. *Homem.*', b'*Fito.* Homem.')
        self.check()

    def test_pending_blocks_application(self):
        self.result['pages'][self.pid]['uncertainties'] = ['c1-l001: unclear']
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            self.check()

    def setup_repo(self):
        for p, data in {f'{review.SOURCE}/{self.pid}.md': MD,
                        f'{review.COMPILED}/{self.pid}.json': review.encoded(review.parse(MD)),
                        review.GEOMETRY: review.encoded({'pages': [self.geometry]}),
                        review.REGISTRY: review.encoded({'pages': {}}),
                        review.TERMS: review.encoded({'pages': {}})}.items():
            dest = self.root / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)

    def test_apply_and_rollback(self):
        self.save()
        self.setup_repo()
        args = argparse.Namespace(input=self.input, result=self.output, publish=False)
        with patch.object(review, 'ROOT', self.root), patch.object(review, 'human_protected', return_value={}), \
             patch.object(review, 'git', side_effect=lambda *a: b'' if a[0] == 'status' else b'abc'), \
             patch.object(review.subprocess, 'run', side_effect=RuntimeError('build failed')):
            with self.assertRaisesRegex(RuntimeError, 'build failed'):
                review.apply(args)
        self.assertEqual((self.root / review.SOURCE / f'{self.pid}.md').read_bytes(), MD)
        self.assertFalse((self.root / 'pilot/external-review/imports/test.json').exists())

    def test_apply_success(self):
        self.save()
        self.setup_repo()
        args = argparse.Namespace(input=self.input, result=self.output, publish=False)
        with patch.object(review, 'ROOT', self.root), patch.object(review, 'human_protected', return_value={}), \
             patch.object(review, 'git', side_effect=lambda *a: b'' if a[0] == 'status' else b'abc'), \
             patch.object(review.subprocess, 'run') as run:
            review.apply(args)
            self.assertEqual(run.call_count, 2)
        compiled = json.loads((self.root / review.COMPILED / f'{self.pid}.json').read_bytes())
        self.assertEqual(compiled, review.parse((self.root / review.SOURCE / f'{self.pid}.md').read_bytes()))
        self.assertEqual(compiled['review']['status'], 'context_reviewed')

    def test_stale_stops_before_write(self):
        self.save()
        self.setup_repo()
        path = self.root / review.SOURCE / f'{self.pid}.md'
        path.write_bytes(MD + b'\n')
        with patch.object(review, 'ROOT', self.root), patch.object(review, 'human_protected', return_value={}), \
             patch.object(review, 'git', return_value=b''):
            with self.assertRaisesRegex(ValueError, 'stale'):
                review.apply(argparse.Namespace(input=self.input, result=self.output, publish=False))
        self.assertEqual(path.read_bytes(), MD + b'\n')

    def test_protected_stops(self):
        self.save()
        self.setup_repo()
        with patch.object(review, 'ROOT', self.root), patch.object(review, 'human_protected', return_value={self.pid: 'human'}), \
             patch.object(review, 'git', return_value=b''):
            with self.assertRaisesRegex(ValueError, 'protected'):
                review.apply(argparse.Namespace(input=self.input, result=self.output, publish=False))

    def test_categories(self):
        self.assertEqual(review.category('ſt', 'st'), 'long_short_s')
        self.assertEqual(review.category('ã', 'a'), 'diacritics')
        self.assertEqual(review.distance('abc', 'adc'), 1)

    def v2(self):
        m = json.loads(self.inputs['manifest.json']); m['schema'] = 2
        self.inputs['manifest.json'] = review.encoded(m)
        self.input.unlink()
        review.write_zip(self.input, self.inputs)
        self.result['schema'] = 2
        self.result['input_manifest_sha256'] = review.sha(self.inputs['manifest.json'])
        self.result['pages'][self.pid]['decision_requests'] = []

    def insert_row(self):
        self.outputs[f'pages/{self.pid}.md'] += b'[c1-l001a] *Idem.*\n[c1-l001a note] Refers back to the preceding gloss.\n'
        self.geom['crops']['c1-l001a'] = [0,20,100,20]
        self.outputs[f'pages/{self.pid}.geometry.json'] = review.encoded(self.geom)

    def test_v2_insertion_and_renderer(self):
        self.v2(); self.insert_row()
        self.result['pages'][self.pid]['structural_changes'] = [{'before': [], 'after': ['c1-l001a'], 'reason': 'Missing row recovered.'}]
        _,_,pages = self.check()
        page,geo = pages[self.pid]
        integrated = review.integrated_geometry(self.geometry,page,geo)
        from build_public_review import processed_page
        rendered = processed_page(page,{}, {}, integrated, {})
        self.assertEqual(len(rendered['zones'][0]['lines']),2)
        self.assertIn('context_crop',rendered['zones'][0]['lines'][1])

    def test_v2_unaccounted_insertion(self):
        self.v2(); self.insert_row()
        with self.assertRaisesRegex(ValueError,'Unaccounted'):
            self.check()

    def test_v2_nonblocking_uncertainty(self):
        self.v2()
        self.result['pages'][self.pid]['uncertainties'] = ['Worn letter; chosen reading retained.']
        self.check()

    def test_v2_decision_request_blocks(self):
        self.v2()
        self.result['pages'][self.pid]['decision_requests'] = ['Cannot determine page identity.']
        with self.assertRaisesRegex(ValueError,'unresolved'):
            self.check()

    def test_v2_move_to_furniture(self):
        self.v2(); self.insert_row()
        self.outputs[f'pages/{self.pid}.md'] = self.outputs[f'pages/{self.pid}.md'].replace(b'[c1-l001a]', b'\n## catch [catchword] Catchword\n\n[c1-l001a]')
        self.result['pages'][self.pid]['structural_changes'] = [{'before': [], 'after':['c1-l001a'], 'reason':'New catchword.'}]
        _,_,pages=self.check(); page,geo=pages[self.pid]
        integrated=review.integrated_geometry(self.geometry,page,geo)
        self.assertEqual(set(integrated['columns']['column-1']['lines']),{'c1-l001'})

    def test_v2_orphan_crop(self):
        self.v2()
        self.geom['crops']['unknown']=[0,0,10,10]
        self.outputs[f'pages/{self.pid}.geometry.json']=review.encoded(self.geom)
        with self.assertRaisesRegex(ValueError,'orphan'):
            self.check()

    def test_v2_changed_source_rejected(self):
        self.v2()
        self.outputs[f'pages/{self.pid}.md']=self.outputs[f'pages/{self.pid}.md'].replace(b'view: f216',b'view: f217')
        with self.assertRaisesRegex(ValueError,'immutable'):
            self.check()

    def test_v2_merge_mapping(self):
        old=review.parse(MD)
        new=review.parse(self.outputs[f'pages/{self.pid}.md'])
        old['zones'][0]['lines'].append({'id':'c1-l002','runs':[{'text':'Continuation.','typeface':'roman'}]})
        review.validate_structure_v2(old,new,{'structural_changes':[{'before':['c1-l001','c1-l002'],'after':['c1-l001'],'reason':'One physical row; continuation merged into retained ID.'}]})
        with self.assertRaisesRegex(ValueError,'Unaccounted'):
            review.validate_structure_v2(old,new,{'structural_changes':[]})

    def test_v2_header_correction_requires_declaration(self):
        old=review.parse(MD);new=review.parse(MD)
        for page,text in [(old,'O.'),(new,'V.')]:
            page['zones'].append({'id':'header','kind':'running_header','label':'Header','lines':[{'id':'h1-l001','runs':[{'typeface':'display','text':text}]}]})
        with self.assertRaisesRegex(ValueError,'undeclared'):
            review.validate_structure_v2(old,new,{'structural_changes':[]})
        review.validate_structure_v2(old,new,{'structural_changes':[{'before':['h1-l001'],'after':['h1-l001'],'reason':'Scan reads V.'}]})

    def setup_provisional(self):
        self.v2(); self.setup_repo()
        for folder,suffix in [(review.SOURCE,'.md'),(review.COMPILED,'.json')]:
            (self.root/folder/(self.pid+suffix)).unlink()
        self.candidate_path=f'pilot/ocr-bootstrap/f0238-f0247/{self.pid}.json'
        page=review.parse(MD); page['review']['physical_lineation_checked']=False
        candidate={'format':'nippo-ocr-level1-bootstrap-candidate','id':self.pid,'page':page,'geometry':self.geometry}
        self.candidate_bytes=review.encoded(candidate)
        path=self.root/self.candidate_path;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(self.candidate_bytes)
        (self.root/review.GEOMETRY).write_bytes(review.encoded({'pages':[]}))
        self.inputs['targets/page.md']=review.export_markdown(page).encode()
        self.outputs[f'pages/{self.pid}.md']=self.inputs['targets/page.md']+b'[c1-l001 note] A person is explained by the Portuguese homem.\n'
        m=json.loads(self.inputs['manifest.json'])
        m['files']['targets/page.md']=review.sha(self.inputs['targets/page.md'])
        m['pages'][self.pid].update(source_kind='provisional',source_path=self.candidate_path,
            source_sha256=review.sha(self.candidate_bytes),registry_geometry_sha256=None)
        self.inputs['manifest.json']=review.encoded(m)
        self.result['input_manifest_sha256']=review.sha(self.inputs['manifest.json'])
        self.input.unlink();review.write_zip(self.input,self.inputs)

    def test_provisional_promotion_and_ui(self):
        self.setup_provisional();self.save()
        with patch.object(review,'ROOT',self.root),patch.object(review,'human_protected',return_value={}), \
             patch.object(review,'git',side_effect=lambda *a:b'' if a[0]=='status' else b'abc'),patch.object(review.subprocess,'run'):
            review.apply(argparse.Namespace(input=self.input,result=self.output,publish=False))
            self.assertEqual(review.baseline(self.pid)[4],'canonical')
        page=json.loads((self.root/review.COMPILED/(self.pid+'.json')).read_bytes())
        self.assertTrue(page['review']['physical_lineation_checked'])
        self.assertEqual((self.root/self.candidate_path).read_bytes(),self.candidate_bytes)
        from build_public_review import processed_page
        g=json.loads((self.root/review.GEOMETRY).read_bytes())['pages'][0]
        self.assertTrue(processed_page(page,{}, {},g,{})['processed'])

    def test_provisional_failed_build_removes_promotion(self):
        self.setup_provisional();self.save()
        with patch.object(review,'ROOT',self.root),patch.object(review,'human_protected',return_value={}), \
             patch.object(review,'git',side_effect=lambda *a:b'' if a[0]=='status' else b'abc'),patch.object(review.subprocess,'run',side_effect=RuntimeError('failed build')):
            with self.assertRaises(RuntimeError):review.apply(argparse.Namespace(input=self.input,result=self.output,publish=False))
            self.assertEqual(review.baseline(self.pid)[4],'provisional')
        self.assertFalse((self.root/review.COMPILED/(self.pid+'.json')).exists())
        self.assertEqual((self.root/self.candidate_path).read_bytes(),self.candidate_bytes)
        self.assertEqual(json.loads((self.root/review.GEOMETRY).read_bytes())['pages'],[])

    def test_unchecked_roundtrip_and_style_preservation(self):
        p=review.parse(MD);p['review']['physical_lineation_checked']=False
        self.assertEqual(review.parse(review.export_markdown(p).encode()),p)
        q=review.parse(MD)
        self.assertFalse(review.interchange_equivalent(p,q))

    def test_provisional_stale_source(self):
        self.setup_provisional();self.save()
        (self.root/self.candidate_path).write_bytes(self.candidate_bytes+b'\n')
        with patch.object(review,'ROOT',self.root),patch.object(review,'human_protected',return_value={}),patch.object(review,'git',return_value=b''):
            with self.assertRaisesRegex(ValueError,'stale'):
                review.apply(argparse.Namespace(input=self.input,result=self.output,publish=False))

    def test_provisional_intervening_canonical(self):
        self.setup_provisional();self.save()
        (self.root/review.COMPILED/(self.pid+'.json')).write_bytes(b'{}')
        with patch.object(review,'ROOT',self.root),patch.object(review,'human_protected',return_value={}),patch.object(review,'git',return_value=b''):
            with self.assertRaisesRegex(ValueError,'already exists'):
                review.apply(argparse.Namespace(input=self.input,result=self.output,publish=False))

    def test_complete_batches_and_remainder(self):
        for n in range(216, 223):
            path = self.root / review.SOURCE / f'bnf-f{n:04}.md'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(MD)
        dest = self.root / 'packages'
        with patch.object(review, 'ROOT', self.root), patch.object(review, 'human_protected', return_value={}), \
             patch.object(review, 'baseline', return_value=('',MD,review.parse(MD),{},'canonical')), \
             patch.object(review, 'package') as pack, patch.object(review, 'git', return_value=b'abc'):
            review.batches(argparse.Namespace(start=216, end=222, size=3, output=dest))
            self.assertEqual([c.args[0].pages for c in pack.call_args_list], [[216,217,218], [219,220,221]])
        self.assertEqual(json.loads((dest / 'batch-index.json').read_bytes())['omitted'][0]['pages'], [222])

    def test_batch_skips_protected_group_without_regrouping(self):
        for n in range(216, 222):
            path = self.root / review.SOURCE / f'bnf-f{n:04}.md'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(MD)
        with patch.object(review, 'ROOT', self.root), patch.object(review, 'human_protected', return_value={'bnf-f0217': 'human'}), \
             patch.object(review, 'baseline', return_value=('',MD,review.parse(MD),{},'canonical')), \
             patch.object(review, 'package') as pack, patch.object(review, 'git', return_value=b'abc'):
            review.batches(argparse.Namespace(start=216, end=221, size=3, output=self.root / 'packages'))
            self.assertEqual([c.args[0].pages for c in pack.call_args_list], [[219,220,221]])

    def test_real_evaluation_package_smoke(self):
        path = SCRIPTS.parent / 'exports/external-review/ready/evaluation-f0202-f0203-f0204-fa1b73ca-input.zip'
        if not path.exists():
            self.skipTest('Local evaluation archive not generated')
        incoming = review.read_zip(path)
        m = json.loads(incoming['manifest.json'])
        output = {k.removeprefix('result-template/'): v for k, v in incoming.items() if k.startswith('result-template/')}
        result = json.loads(output['result.json'])
        result['reviewer'] = 'SYNTHETIC PIPELINE TEST, NOT A REVIEW'
        for pid, info in result['pages'].items():
            info.update(first_pass=True, second_pass=True, crops_inspected=True)
            page = review.parse(output[f'pages/{pid}.md'])
            for line in review.lines(page, True).values():
                line['note'] = 'Synthetic pipeline fixture only; no visual review performed.'
            output[f'pages/{pid}.md'] = review.export_markdown(page).encode()
        output['result.json'] = review.encoded(result)
        result_path = self.root / 'synthetic.zip'
        review.write_zip(result_path, output)
        review.validate(path, result_path)
        evaluator = path.with_name(path.name.replace('-input.zip', '-EVALUATOR-DO-NOT-SEND.zip'))
        report = self.root / 'report.json'
        review.evaluate(argparse.Namespace(input=path, result=result_path, evaluator=evaluator, output=report))
        self.assertEqual(set(json.loads(report.read_bytes())['pages']), set(m['pages']))
        with self.assertRaisesRegex(ValueError, 'Evaluation results'):
            review.apply(argparse.Namespace(input=path, result=result_path, publish=False))


if __name__ == '__main__':
    unittest.main()
