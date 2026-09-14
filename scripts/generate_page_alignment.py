"""Generate display-only alignment from current native line rectangles."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from difflib import SequenceMatcher
from PIL import Image
from build_character_alignment_pilot import align

ROOT=Path(__file__).resolve().parents[1]

def generate(pid, fingerprint):
    page=json.loads((ROOT/f'pilot/format-v1-trial/level1/{pid}.json').read_text())
    geometry=json.loads((ROOT/'pilot/human-review/line-geometry.json').read_text())
    geom=next(p for p in geometry['pages'] if p['id']==pid)
    boxes={k:v for col in geom['columns'].values() for k,v in col['lines'].items()}
    scans=list((ROOT/'build/nippo-jisho-images/scans/native').glob(f'{pid.removeprefix("bnf-")}.jpg'))
    if not scans:raise ValueError('Native scan unavailable: '+pid)
    scan=scans[0]
    if hashlib.sha256(scan.read_bytes()).hexdigest()!=page['source']['master_sha256']:raise ValueError('Scan hash mismatch')
    work=ROOT/'.cache/ocr-model/automatic-alignment'/pid/fingerprint
    work.mkdir(parents=True,exist_ok=True)
    rows=[];images=[]
    with Image.open(scan) as im:
        for zone in page['zones']:
            if zone['kind']!='column':continue
            for line in zone['lines']:
                row={'id':line['id'],'runs':line['runs'],'text':''.join(r['text'] for r in line['runs'])}
                rows.append(row)
                if any(r.get('layout') or r.get('span_id') for r in line['runs']) or line['id'] not in boxes:
                    row['unavailable']='special layout or missing rectangle';continue
                x,y,w,h=boxes[line['id']]['crop']
                if min(w,h)<=0 or x<0 or y<0 or x+w>im.width or y+h>im.height:raise ValueError('Invalid crop')
                dest=work/(line['id']+'.png');im.crop((x,y,x+w,y+h)).save(dest)
                images.append(str(dest));row['crop']=[x,y,w,h]
    if not images:raise ValueError('No ordinary lines')
    subprocess.run([sys.executable,str(ROOT/'scripts/recognize_nippo_calamari.py'),*images,'--positions','--model',str(ROOT/'models/local/nippo-calamari-v2-styled'),'--output',str(work/'predictions.json')],check=True)
    predictions={Path(r['image']).stem:r for r in json.loads((work/'predictions.json').read_text())['lines']}
    usable=0
    for row in rows:
        pred=predictions.get(row['id'])
        if not pred:continue
        spans,ocr=align(row['text'],pred)
        score=SequenceMatcher(None,ocr,row['text'],autojunk=False).ratio()
        if score<.85:
            row['unavailable']='OCR/text agreement below 0.85';continue
        x,y,w,h=row['crop'];pw,ph=pred['position_evidence']['prepared_size']
        row.update(alignment=spans,image_width=pw,scan_mapping={'origin':[x,y],'dx':[w/pw,0],'dy':[0,h/ph]})
        usable+=1
    if not usable:raise ValueError('No reliable alignments; evidence retained locally')
    output=ROOT/f'site/assets/alignment/{pid}.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'page':pid,'generation_fingerprint':fingerprint,'method':'native_rectangle_ocr_v1','rows':rows,'usable_lines':usable},ensure_ascii=False)+'\n')
    print(f'{pid}: {usable}/{len(rows)} lines')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('page');p.add_argument('fingerprint');a=p.parse_args();generate(a.page,a.fingerprint)
