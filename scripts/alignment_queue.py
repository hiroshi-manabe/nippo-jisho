"""Low-priority overlay jobs; caller holds the review-inbox lock."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def discover():
    def load(path):return json.loads((ROOT/path).read_text())
    ai=load('pilot/human-review/commentary-reviews.json')['pages']
    human={p['id'] for p in load('pilot/human-review/correction-history.json')['pages'] if p.get('issues_applied',0)}
    geometry={p['id']:p for p in load('pilot/human-review/line-geometry.json')['pages']}
    code=b''.join((ROOT/'scripts'/name).read_bytes() for name in ('generate_page_alignment.py','prepare_alignment_records.py','recognize_nippo_calamari.py','build_character_alignment_pilot.py','map_f230_alignment_to_scan.py'))
    model=(ROOT/'models/local/nippo-calamari-v2-styled/model.json').read_bytes()
    jobs=[]
    for pid in sorted(set(ai)|human):
        page=ROOT/f'pilot/format-v1-trial/level1/{pid}.json'
        if not page.exists() or pid not in geometry:continue
        manifest=ROOT/f'.cache/ocr-model/page-refresh-v2/prepared/{pid}.json'
        fingerprint=hashlib.sha256(page.read_bytes()+json.dumps(geometry[pid],sort_keys=True).encode()+code+model+(manifest.read_bytes() if manifest.exists() else b'no-manifest')).hexdigest()
        target=ROOT/f'site/assets/alignment/{pid}.json'
        if target.exists():
            old=json.loads(target.read_text())
            if old.get('generation_fingerprint')==fingerprint:continue
            # Keep the validated f230 pilot until its baseline changes.
            if pid=='bnf-f0230' and old.get('baseline_sha256')==hashlib.sha256(page.read_bytes()).hexdigest():continue
        jobs.append((f'alignment:{pid}:{fingerprint}',{'kind':'alignment','page':pid,'fingerprint':fingerprint,'human_reviewed':pid in human}))
    return sorted(jobs,key=lambda j:(j[1]['human_reviewed'],j[1]['page']))
