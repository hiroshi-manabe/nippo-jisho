"""Recognize saved rectified crops and replay their inverse scan mappings."""
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
    manifest_path=ROOT/f'.cache/ocr-model/page-refresh-v2/prepared/{pid}.json'
    if not manifest_path.exists():raise ValueError('Rectified extraction manifest unavailable; refusing broad UI crops')
    records={r['line']:r for r in json.loads(manifest_path.read_text())['records']}
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
                record=records.get(line['id'])
                if record:
                    source=ROOT/'.cache/ocr-model/page-refresh-v2'/record['image']
                    if hashlib.sha256(source.read_bytes()).hexdigest()!=record['image_sha256']:
                        raise ValueError('Saved rectified image hash mismatch')
                    dest=work/(line['id']+'.png');dest.write_bytes(source.read_bytes())
                elif pid=='bnf-f0230' and line['id']=='c1b-l003':
                    # The visually verified supplemental crop from the pilot.
                    from ocr_line_images import prepare_rectified_line
                    dest=work/(line['id']+'.png')
                    prepare_rectified_line(im.crop((770,1811,1435,1889))).save(dest)
                else:
                    row['unavailable']='no saved rectified extraction';continue
                images.append(str(dest));row['crop']=[x,y,w,h]
    if not images:raise ValueError('No ordinary lines')
    subprocess.run([sys.executable,str(ROOT/'scripts/recognize_nippo_calamari.py'),*images,'--prepared','--positions','--model',str(ROOT/'models/local/nippo-calamari-v2-styled'),'--output',str(work/'predictions.json')],check=True)
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
        row.update(alignment=spans,image_width=pw)
        usable+=1
    if not usable:raise ValueError('No reliable alignments; evidence retained locally')
    output=ROOT/f'site/assets/alignment/{pid}.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    intermediate=work/'aligned.json'
    intermediate.write_text(json.dumps({'page':pid,'generation_fingerprint':fingerprint,'method':'rectified_replay_v2','rows':rows,'usable_lines':usable},ensure_ascii=False)+'\n')
    mapped=work/'mapped.json'
    subprocess.run(['arch','-arm64',str(ROOT/'.cache/ocr-model/venv-kraken-arm64/bin/python'),str(ROOT/'scripts/map_f230_alignment_to_scan.py'),'--page',pid,'--input',str(intermediate),'--output',str(mapped)],check=True)
    output.write_bytes(mapped.read_bytes())
    print(f'{pid}: {usable}/{len(rows)} lines')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('page');p.add_argument('fingerprint');a=p.parse_args();generate(a.page,a.fingerprint)
