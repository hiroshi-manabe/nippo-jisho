"""Show mapped OCR character positions on unrectified canonical scan crops."""
import base64, io, json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'.cache/ocr-model/character-positions-v1/f230-native-mapping.json').read_text())
geometry=json.loads((ROOT/'pilot/human-review/line-geometry.json').read_text())
page=next(p for p in geometry['pages'] if p['id']==data['page'])
lines={k:v for col in page['columns'].values() for k,v in col['lines'].items()}
scan=Image.open(ROOT/'build/nippo-jisho-images/scans/native/f0230.jpg')
for row in data['rows']:
    if not row.get('image'):continue
    x,y,w,h=lines[row['id']]['crop'];row['crop']=[x,y,w,h]
    out=io.BytesIO();scan.crop((x,y,x+w,y+h)).save(out,format='PNG')
    row['image']='data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()
template=(ROOT/'scripts/native_alignment_pilot.html').read_text()
(ROOT/'exports/character-alignment/f230-native.html').write_text(template.replace('/*DATA*/',json.dumps(data,ensure_ascii=True)))
