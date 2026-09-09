#!/usr/bin/env python3
"""Freeze corrected f13–f200 pairs for plain/style-aware Calamari comparison.

Run in the Kraken environment. This never edits canonical text or geometry.
Italic characters have an internal private-use label; exported records retain
ordinary Unicode text and per-character style for independent evaluation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import unicodedata

from PIL import Image, ImageOps
from audit_ocr_layout_geometry import (
    EVIDENCE, GEOMETRY, LEVEL1, read_evidence, targets_for_geometry,
    column_candidates, align_audit_rows, normalized_distance,
)
from build_clean_ocr_pairs import normalized_line

ROOT = Path(__file__).resolve().parents[1]
OFFSET = 0xF0000


def styled_text(runs):
    chars, styles = [], []
    for run in runs:
        if run['typeface'] not in ('roman', 'italic'):
            raise ValueError('Non-body typeface')
        text = unicodedata.normalize('NFC', run['text'])
        chars.extend(text)
        styles.extend([run['typeface']] * len(text))
    text = ''.join(chars)
    left, right = len(text) - len(text.lstrip()), len(text.rstrip())
    return text[left:right], styles[left:right]


def encode(text, styles):
    if len(text) != len(styles):
        raise ValueError('Character/style length mismatch')
    result = []
    for char, style in zip(text, styles):
        if ord(char) >= 0xFFFE:
            raise ValueError(f'Unsupported training character {char!r}')
        result.append(chr(ord(char) + OFFSET) if style == 'italic' and not char.isspace() else char)
    return ''.join(result)


def decode(text):
    chars, styles = [], []
    for char in text:
        italic = OFFSET <= ord(char) < OFFSET + 0xFFFE
        chars.append(chr(ord(char) - OFFSET) if italic else char)
        styles.append('italic' if italic else 'roman')
    return ''.join(chars), styles


def page_splits():
    old = json.loads((ROOT / 'experiments/ocr/f13-f150-split.json').read_text())
    extra = list(range(151, 201))
    random.Random(1603).shuffle(extra)
    dev, test = set(old['dev'] + extra[5:10]), set(old['test'] + extra[:5])
    return {n: 'test' if n in test else 'dev' if n in dev else 'train' for n in range(13, 201)}


def full_text_candidates(candidates, column_geometry):
    """Do not pair full-band recognition with a margin speck's tiny polygon."""
    left, _, right, _ = column_geometry['box']
    tolerance = .03 * (right-left)
    in_body = [c for c in candidates if left-tolerance <= c['centre'][0] <= right+tolerance]
    def width(c):
        xs=[p[0] for p in c['boundary']]
        return max(xs)-min(xs)
    def length(c):
        return len(c['recognition'].replace(' ',''))
    pitches=[width(c)/length(c) for c in in_body if length(c)>=20 and width(c)>.5*(right-left)]
    minimum_pitch=.55*statistics.median(pitches) if pitches else 8
    return [c for c in in_body if length(c)<8 or width(c)/max(1,length(c))>=minimum_pitch]


def build(output):
    from kraken.containers import BaselineLine, Segmentation
    from kraken.lib.segmentation import extract_polygons
    if (output / 'records.jsonl').exists():
        raise ValueError('Frozen dataset exists; choose a new output directory')
    output.mkdir(parents=True, exist_ok=True)
    geometry = {p['id']: p for p in json.loads(GEOMETRY.read_text())['pages']}
    splits = page_splits()
    records, excluded = [], []
    for number, split in splits.items():
        pid = f'bnf-f{number:04d}'
        page = json.loads((LEVEL1 / f'{pid}.json').read_text())
        lines = {l['id']: l for z in page['zones'] if z['kind'] == 'column' for l in z['lines']}
        evidence = read_evidence(pid, EVIDENCE)
        selected = []
        for column, refs in targets_for_geometry(page, geometry[pid]).items():
            candidates = full_text_candidates(column_candidates(evidence, column), geometry[pid]['columns'][column])
            for ri, ci in align_audit_rows(refs, candidates):
                if ri is None:
                    continue
                ref = refs[ri]
                reason = None
                candidate = candidates[ci] if ci is not None else None
                distance = normalized_distance(ref['text'], candidate['recognition']) if candidate else 1
                if candidate is None or distance > .35:
                    reason = 'uncertain_correspondence'
                elif any(normalized_distance(refs[j]['text'], candidate['recognition']) < distance - .05
                         for j in (ri-1, ri+1) if 0 <= j < len(refs)):
                    reason = 'neighbor_conflict'
                try:
                    text, styles = styled_text(lines[ref['id']]['runs'])
                    target = encode(text, styles)
                except ValueError:
                    reason = reason or 'non_body_style_or_character'
                if reason:
                    excluded.append({'page': pid, 'line': ref['id'], 'reason': reason, 'distance': distance})
                    continue
                selected.append((ref, candidate, text, styles, target))
        scan_path = ROOT / 'build/nippo-jisho-images/scans/native' / f'f{number:04d}.jpg'
        seg = Segmentation(type='baselines', imagename=str(scan_path), text_direction='horizontal-lr',
            script_detection=False, lines=[BaselineLine(id=r['id'], baseline=c['baseline'], boundary=c['boundary'])
                                          for r,c,*_ in selected])
        with Image.open(scan_path) as scan:
            for (image, line), (ref, candidate, text, styles, target) in zip(extract_polygons(ImageOps.invert(scan.convert('RGB')), seg), selected):
                assert line.id == ref['id']
                prepared = normalized_line(ImageOps.invert(image), height=48, max_width=4096)
                required = max(len(text)+sum(a==b for a,b in zip(text,text[1:])),
                               len(target)+sum(a==b for a,b in zip(target,target[1:])))
                if prepared.width < 4*required:
                    excluded.append({'page':pid,'line':ref['id'],'reason':'crop_too_narrow_for_ctc',
                                     'width':prepared.width,'required_ctc_steps':required})
                    continue
                stem = f'{pid}__{line.id}'
                image_path = output / 'images' / (stem + '.png')
                image_path.parent.mkdir(exist_ok=True)
                prepared.save(image_path)
                for mode, truth in [('plain', text), ('styled', target)]:
                    folder = output / mode / split
                    folder.mkdir(parents=True, exist_ok=True)
                    dest = folder / (stem + '.png')
                    if not dest.exists():
                        dest.symlink_to(image_path.resolve())
                    (folder / (stem + '.gt.txt')).write_text(truth, encoding='utf-8')
                records.append({'id': f'{pid}/{line.id}', 'page_id': pid, 'line_id': line.id,
                    'split': split, 'text': text, 'styles': styles, 'encoded': target,
                    'image': str(image_path.relative_to(output)), 'candidate_id': candidate['id'],
                    'boundary': candidate['boundary'], 'baseline': candidate['baseline'],
                    'width': prepared.width, 'height': prepared.height,
                    'exterior': 'paper-white',
                    'image_sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(),
                    'reference_sha256': hashlib.sha256(json.dumps(lines[line.id], ensure_ascii=False).encode()).hexdigest()})
        print(pid, split, len(selected), flush=True)
    (output / 'records.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in records))
    summary = {'format': 'nippo-ocr-retraining-v2', 'commit': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'splits': {s: [n for n,v in splits.items() if v==s] for s in ('train','dev','test')},
        'lines': dict(Counter(r['split'] for r in records)), 'excluded': excluded,
        'encoding': 'Italic non-whitespace character code point + U+F0000; NFC; spaces unstyled',
        'crop': 'Full-text Kraken polygons rectified with paper-white exterior, 48 px height',
        'complete_training_dataset': True,
        'canonical_modified': False}
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    print(summary['lines'], 'excluded', len(excluded))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/ocr-model/retraining-v2c')
    build(parser.parse_args().output)
