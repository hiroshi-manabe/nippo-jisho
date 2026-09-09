#!/usr/bin/env python3
"""Paired page-level uncertainty for the plain/styled text comparison.

Resample pages, not individual lines: lines on a page share typography and scan
conditions. A positive difference means the styled model has more text errors.
This is descriptive uncertainty on the chosen holdout, not a guarantee about
unseen sections of the dictionary.
"""
import argparse
import json
from pathlib import Path
import random

from build_ocr_retraining_dataset import decode
from evaluate_line_ocr_predictions import edit_alignment


def bootstrap_difference(pages, draws=10000, seed=1603):
    if not pages:
        raise ValueError('No pages to compare')
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        selected = rng.choices(pages, k=len(pages))
        samples.append(sum(p['styled_errors']-p['plain_errors'] for p in selected)
                       /sum(p['characters'] for p in selected))
    samples.sort()
    return {'method':'paired page bootstrap', 'draws':draws, 'seed':seed,
            'difference':'styled text CER minus plain text CER',
            'estimate':sum(p['styled_errors']-p['plain_errors'] for p in pages)
                       /sum(p['characters'] for p in pages),
            'percentile_95_interval':[samples[int(.025*(draws-1))],
                                      samples[int(.975*(draws-1))]]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,default=Path('.cache/ocr-model/retraining-v2d'))
    p.add_argument('--plain',type=Path,required=True,help='Plain prediction directory')
    p.add_argument('--styled',type=Path,required=True,help='Styled prediction directory')
    p.add_argument('--split',choices=['dev','test'],default='dev')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    pages={}
    for line in (args.dataset/'records.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r['split']!=args.split:
            continue
        stem=Path(r['image']).stem+'.pred.txt'
        plain=(args.plain/stem).read_text().rstrip('\r\n')
        styled=decode((args.styled/stem).read_text().rstrip('\r\n'))[0]
        page=pages.setdefault(r['page_id'],{'id':r['page_id'],'lines':0,
            'characters':0,'plain_errors':0,'styled_errors':0})
        page['lines']+=1
        page['characters']+=len(r['text'])
        for name,text in [('plain',plain),('styled',styled)]:
            page[name+'_errors']+=sum(a!=b for a,b in edit_alignment(r['text'],text))
    ordered=[pages[key] for key in sorted(pages)]
    result={'split':args.split,'pages':ordered,'all':bootstrap_difference(ordered)}
    for label,subset in [('old_range',[p for p in ordered if int(p['id'][-4:])<=150]),
                         ('new_range',[p for p in ordered if int(p['id'][-4:])>150])]:
        if subset:
            result[label]=bootstrap_difference(subset)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['all']))


if __name__=='__main__':
    main()
