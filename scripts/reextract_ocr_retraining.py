#!/usr/bin/env python3
"""Re-extract a frozen experiment's polygons with a paper-colored exterior.

No alignment or reference changes: each output record preserves the original
line, split, labels, polygon, and reference hash. Run in the Kraken environment.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps
from build_clean_ocr_pairs import normalized_line

ROOT = Path(__file__).resolve().parents[1]


def main():
    from kraken.containers import BaselineLine, Segmentation
    from kraken.lib.segmentation import extract_polygons
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT / '.cache/ocr-model/retraining-v2b')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--split', choices=['train', 'dev', 'test'])
    p.add_argument('--limit', type=int)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Output exists; choose a fresh directory')
    args.output.mkdir(parents=True)
    records = [json.loads(l) for l in (args.source/'records.jsonl').read_text().splitlines()]
    if args.split:
        records = [r for r in records if r['split']==args.split]
    if args.limit:
        # Systematic sample spans the whole split instead of its first pages.
        indices = [i*len(records)//args.limit for i in range(min(args.limit,len(records)))]
        records = [records[i] for i in indices]
    pages = defaultdict(list)
    for r in records:
        pages[r['page_id']].append(r)
    exported = []
    for pid, rows in pages.items():
        path = ROOT / 'build/nippo-jisho-images/scans/native' / f'f{int(pid[-4:]):04d}.jpg'
        seg = Segmentation(type='baselines', imagename=str(path), text_direction='horizontal-lr',
            script_detection=False, lines=[BaselineLine(id=r['line_id'], baseline=r['baseline'], boundary=r['boundary']) for r in rows])
        with Image.open(path) as scan:
            # Kraken fills outside the polygon with zero. Work in inverted
            # intensities so the exterior becomes paper-white after inversion.
            for (image, line), r in zip(extract_polygons(ImageOps.invert(scan.convert('RGB')), seg), rows):
                assert line.id==r['line_id']
                destination = args.output/r['image']
                destination.parent.mkdir(parents=True,exist_ok=True)
                normalized_line(ImageOps.invert(image),height=48,max_width=4096).save(destination)
                for mode, text in [('plain', r['text']), ('styled', r['encoded'])]:
                    folder = args.output/mode/r['split']
                    folder.mkdir(parents=True,exist_ok=True)
                    (folder/destination.name).symlink_to(destination.resolve())
                    (folder/(destination.stem+'.gt.txt')).write_text(text,encoding='utf-8')
                exported.append({**r,'image_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                    'original_image_sha256':r['image_sha256'], 'exterior':'paper-white'})
        print(pid,len(rows),flush=True)
    (args.output/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in exported))
    summary = json.loads((args.source/'summary.json').read_text())
    summary.update(source_dataset=str(args.source), crop='Same Kraken polygons, paper-white exterior, rectified, 48 px height',
        lines=dict(Counter(r['split'] for r in exported)), complete_training_dataset=not(args.split or args.limit))
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    main()
