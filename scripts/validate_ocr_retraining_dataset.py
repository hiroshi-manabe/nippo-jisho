#!/usr/bin/env python3
"""Audit frozen OCR pairing coverage, labels, split isolation, and file hashes."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from PIL import Image
from build_ocr_retraining_dataset import ROOT, LEVEL1, styled_text, encode, decode


def audit(dataset):
    summary=json.loads((dataset/'summary.json').read_text())
    records=[json.loads(l) for l in (dataset/'records.jsonl').read_text().splitlines()]
    ids=[r['id'] for r in records]
    assert len(set(ids))==len(ids), 'Duplicate reference IDs'
    source={}
    for n in range(13,201):
        pid=f'bnf-f{n:04d}'
        page=json.loads((LEVEL1/f'{pid}.json').read_text())
        for z in page['zones']:
            if z['kind']=='column':
                for l in z['lines']:
                    source[f"{pid}/{l['id']}"]=l
    excluded={f"{r['page']}/{r['line']}" for r in summary['excluded']}
    missing=set(source)-set(ids)-excluded
    assert not missing, f'Unaccounted body lines: {sorted(missing)[:10]}'
    assert not set(ids)&excluded, 'Retained/excluded overlap'
    assert set(ids)<=set(source), 'Non-body record'
    page_splits=defaultdict(set)
    candidates=set()
    chars=Counter()
    for r in records:
        page_splits[r['page_id']].add(r['split'])
        key=(r['page_id'],r['candidate_id'])
        assert key not in candidates, f'Duplicate physical crop: {key}'
        candidates.add(key)
        text,styles=styled_text(source[r['id']]['runs'])
        assert (text,styles)==(r['text'],r['styles']), f'Reference drift: {r["id"]}'
        assert r['encoded']==encode(text,styles)
        assert decode(r['encoded'])[0]==text
        path=dataset/r['image']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==r['image_sha256']
        with Image.open(path) as im:
            assert im.height==48
            assert im.width>=4*len(text), f'Inadequate CTC width: {r["id"]}'
        stem=path.stem
        for mode,truth in [('plain',text),('styled',r['encoded'])]:
            image=dataset/mode/r['split']/(stem+'.png')
            assert image.resolve()==path.resolve()
            assert image.with_suffix('.gt.txt').read_text()==truth
        chars.update(text)
    assert all(len(s)==1 for s in page_splits.values()), 'Page leakage'
    result={'format':'nippo-ocr-dataset-audit','source_body_lines':len(source),
            'retained':len(records),'excluded':len(excluded),'unaccounted':len(missing),
            'split_lines':dict(Counter(r['split'] for r in records)),
            'split_pages':dict(Counter(next(iter(s)) for s in page_splits.values())),
            'glyph_counts':{c:chars[c] for c in ['ß','ſ','s','ẽ','ǒ','ô']},
            'hashes_and_labels_verified':True,'page_disjoint':True}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,default=ROOT/'.cache/ocr-model/retraining-v2c')
    args=p.parse_args()
    result=audit(args.dataset)
    (args.dataset/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
