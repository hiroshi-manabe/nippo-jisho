import json
from pathlib import Path
import subprocess
import unittest

from scripts.process_correction_issue import validate_payload, page_id, source_path, load_editable_page, apply_change, apply_resolved

ROOT = Path(__file__).resolve().parents[1]


class SupplementalPagesTests(unittest.TestCase):
    def test_structural_preparation_and_column_scale(self):
        registry=json.loads((ROOT/'sources/supplemental-pages.json').read_text())['pages']
        self.assertEqual(len(registry),28)
        geometry={p['id']:p for p in json.loads((ROOT/'pilot/human-review/line-geometry.json').read_text())['pages']}
        for record in registry:
            page=json.loads((ROOT/f"pilot/format-v1-trial/level1/{record['id']}.json").read_text())
            self.assertEqual(sum(z['kind']=='running_header' for z in page['zones']),2)
            ids=[l['id'] for z in page['zones'] for l in z['lines']]
            self.assertEqual(len(ids),len(set(ids)))
            self.assertFalse(page['review']['physical_lineation_checked'])
            for column in geometry[record['id']]['columns'].values():
                widths={l['crop'][2] for l in column['lines'].values()}
                self.assertEqual(len(widths),1)
                self.assertGreater(min(widths),900)
        pilot=json.loads((ROOT/'pilot/format-v1-trial/level1/bodleian-f0110r.json').read_text())
        self.assertTrue(any(z['kind']=='running_header' and any(l['id']=='c1-l001' for l in z['lines']) for z in pilot['zones']))

    def test_crops_use_bounded_xywh(self):
        geometry = json.loads((ROOT/'pilot/human-review/line-geometry.json').read_text())
        for page in geometry['pages']:
            if not page['id'].startswith('bodleian-'):
                continue
            width, height = page['source_size']
            for column in page['columns'].values():
                for line in column['lines'].values():
                    for key in ('crop', 'context_crop'):
                        x, y, w, h = line[key]
                        self.assertGreater(w, 0)
                        self.assertGreater(h, 0)
                        self.assertLessEqual(x+w, width)
                        self.assertLessEqual(y+h, height)

    def test_ids_and_ordinary_correction_path(self):
        for record in json.loads((ROOT/'sources/supplemental-pages.json').read_text())['pages']:
            view = record['id']
            self.assertEqual(page_id(view), view)
            self.assertTrue(source_path(ROOT, view).exists())
            page, storage = load_editable_page(ROOT, view)
            line = page['zones'][0]['lines'][0]
            before = ''.join(run['text'] for run in line['runs'])
            change = {'line': line['id'], 'before': before, 'after': before+' test'}
            validate_payload({'schema': 3, 'page': view, 'base_commit': 'test',
                              'base_transcription_version': 'test', 'changes': [change]})
            resolved, _ = apply_change(line, change)
            apply_resolved(line, resolved)
            self.assertEqual(''.join(run['text'] for run in line['runs']), before+' test')
            self.assertFalse(page['review']['physical_lineation_checked'])
        self.assertEqual(page_id('f226'), 'bnf-f0226')

    def test_navigation_keys_and_sequence(self):
        script = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('site/app.js','utf8');
const context={}; vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function pageKey'),source.indexOf('function adjacentPage')),context);
assert.equal(context.pageKey('f226'),226);
assert.equal(context.pageKey('226'),226);
assert.equal(context.pageKey('bodleian-f0110r'),'bodleian-f0110r');
const pages=[{leaf:226},{leaf:'bodleian-f0110r'},{leaf:'bodleian-f0110v'},{leaf:227}];
context.state={corpus:{pages},currentPage:pages[1],unit:'column-1'};
context.showPage=(leaf,unit)=>{context.result=[leaf,unit]};
vm.runInContext(source.slice(source.indexOf('function adjacentPage'),source.indexOf('\n}',source.indexOf('function adjacentPage'))+2),context);
context.adjacentPage(-1); assert.deepEqual(context.result,[226,'column-1']);
context.adjacentPage(1); assert.deepEqual(context.result,['bodleian-f0110v','column-1']);
"""
        subprocess.run(['node','-e',script],cwd=ROOT,check=True)
