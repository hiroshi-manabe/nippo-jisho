"""Display grouping only: no assertions about canonical transcription truth."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AlignedWordTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required')
    def test_word_bounds_and_displaced_fragments(self):
        subprocess.run(['node', '-e', r"""
const assert = require('assert');
const fs = require('fs');
const source = fs.readFileSync('site/assets/aligned-text.js', 'utf8');
eval(source.slice(source.indexOf('  function wordSegments('), source.indexOf('  function apply(')));
const m = {origin:[0,0],dx:[1,0],dy:[0,1]};
const row = {image_width:100,runs:[{text:'T',typeface:'roman'},{text:'er ab',typeface:'italic'}],
  alignment:[{left:0,width:3},{left:3,width:1},{left:4,width:2},{left:6,width:2},{left:8,width:4},{left:12,width:3}],
  scan_mapping:m};
let segments = wordSegments(row);
assert.deepStrictEqual(segments.map(s => s.characters.map(c => c.character).join('')), ['Ter',' ','ab']);
assert.deepStrictEqual(segments.map(s => [s.left,s.right]), [[0,6],[6,8],[8,15]]);
assert.deepStrictEqual(segments[0].characters.map(c => c.typeface), ['roman','italic','italic']);
row.scan_mappings = row.alignment.map(() => m);
row.scan_mappings[1] = {...m,origin:[0.00001,0]};
assert.strictEqual(wordSegments(row).length,3);
row.scan_mappings[1] = {...m,origin:[80,0]};
assert.strictEqual(wordSegments(row).length,5);
row.scan_mappings[1] = null;delete row.scan_mapping;
assert.strictEqual(wordSegments(row).map(s => s.characters.map(c => c.character).join('')).join(''),'Tr ab');
const data = JSON.parse(fs.readFileSync('site/assets/alignment/bnf-f0230.json','utf8'));
for (const row of data.rows.filter(r => r.scan_mapping || r.scan_mappings)) {
  const expected = row.runs.flatMap(r => Array.from(r.text)).filter((c,i) => row.scan_mappings?.[i] || row.scan_mapping).join('');
  assert.strictEqual(wordSegments(row).flatMap(s => s.characters.map(c => c.character)).join(''), expected);
}
"""], cwd=ROOT, check=True)
