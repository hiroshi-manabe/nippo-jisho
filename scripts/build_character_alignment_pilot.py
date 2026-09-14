#!/usr/bin/env python3
"""Build a standalone, read-only OCR/text alignment experiment."""
import argparse
import base64
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import unicodedata


def align(text, prediction):
    evidence = prediction['position_evidence']
    predictions = evidence['raw']['predictions']
    voted = next((p for p in predictions if p['id'] == 'voted'), predictions[0])
    symbols, points = [], []
    width = evidence['prepared_size'][0]
    for pos in voted['positions']:
        raw = pos['chars'][0]['char'] if pos['chars'] else ''
        if not raw:
            continue
        char = ''.join(chr(ord(c)-0xF0000) if 0xF0000 <= ord(c) < 0xFFFFE else c for c in raw)
        point = max(0, min(width, (pos['global_start']+pos['global_end'])/2))
        for c in unicodedata.normalize('NFC', char):
            symbols.append(c)
            points.append(point)
    # Midpoints are estimated highlight boundaries, not glyph segmentation.
    edges = [0] + [(a+b)/2 for a,b in zip(points, points[1:])] + [width]
    result = [None]*len(text)
    for tag,a,b,c,d in SequenceMatcher(None, ''.join(symbols), text, autojunk=False).get_opcodes():
        if tag == 'delete':
            continue
        left, right = edges[a], edges[b]
        if tag == 'insert':
            left, right = edges[max(0,a-1)], edges[min(len(symbols),a+1)]
        for j in range(c,d):
            if tag == 'equal':
                lo,hi = edges[a+j-c], edges[a+j-c+1]
            else:
                lo,hi = left,right
            result[j] = {'left':lo/width*100, 'width':max(0,hi-lo)/width*100,
                         'kind': 'matched' if tag=='equal' else 'uncertain'}
    return result, ''.join(symbols)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--page', type=Path, required=True)
    p.add_argument('--predictions', type=Path, required=True)
    p.add_argument('--extra-predictions', type=Path, nargs='*', default=[],
                   help='Supplementary crops; duplicate line IDs are rejected')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--data-output', type=Path)
    args=p.parse_args()
    page=json.loads(args.page.read_text())
    predictions=json.loads(args.predictions.read_text())
    by_id={Path(r['image']).stem.split('__')[-1]:r for r in predictions['lines']}
    for extra in args.extra_predictions:
        for record in json.loads(extra.read_text())['lines']:
            key=Path(record['image']).stem.split('__')[-1]
            if key in by_id:
                raise ValueError(f'Duplicate supplemental line: {key}')
            by_id[key]=record
    rows=[]; stats=Counter()
    for zone in page['zones']:
        if zone['kind']!='column':
            continue
        for line in zone['lines']:
            text=''.join(r['text'] for r in line['runs'])
            pred=by_id.get(line['id'])
            row={'id':line['id'], 'text':text, 'runs':line['runs']}
            if pred:
                path=Path(pred['image'])
                if hashlib.sha256(path.read_bytes()).hexdigest()!=pred['position_evidence']['source_sha256']:
                    raise ValueError(f'Image changed: {path}')
                row['alignment'], row['ocr']=align(text,pred)
                row['image_width']=pred['position_evidence']['prepared_size'][0]
                row['image']='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
                stats.update(a['kind'] for a in row['alignment'])
                stats['lines']+=1
            else:
                stats['missing_lines']+=1
            rows.append(row)
    data={'page':page['id'], 'baseline_sha256':hashlib.sha256(args.page.read_bytes()).hexdigest(),
          'stats':dict(stats), 'rows':rows}
    if args.data_output:
        args.data_output.parent.mkdir(parents=True,exist_ok=True)
        args.data_output.write_text(json.dumps(data,ensure_ascii=False)+'\n')
    template=Path(__file__).with_name('character_alignment_pilot.html').read_text()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(template.replace('/*DATA*/',json.dumps(data,ensure_ascii=True).replace('</','<\\/')))
    print(json.dumps(stats))


if __name__=='__main__':
    main()
