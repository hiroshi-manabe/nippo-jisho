"""Prepare the missing ordinary f230 pilot line; canonical data stays untouched."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
work=ROOT/'.cache/ocr-model/character-positions-v1/f230-gap'
work.mkdir(parents=True,exist_ok=True)
geometry=json.loads((ROOT/'pilot/human-review/line-geometry.json').read_text())
page=next(p for p in geometry['pages'] if p['id']=='bnf-f0230')
line=page['columns']['column-1']['lines']['c1b-l003']
x,y,w,h=line['crop']
# Visually isolate the ordinary row to the right of the six-line decorated G.
# The UI rectangle intentionally also includes that ornament and neighbouring ink.
x,y,w,h=770,1811,665,78
with Image.open(ROOT/'build/nippo-jisho-images/scans/native/f0230.jpg') as image:
    image.crop((x,y,x+w,y+h)).save(work/'bnf-f0230__c1b-l003.png')
print(work/'bnf-f0230__c1b-l003.png')
