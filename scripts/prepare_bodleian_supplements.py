#!/usr/bin/env python3
"""Segment, recognize and structurally prepare all acquired gap supplements.

Run with the project's Kraken Python. Existing output is protected unless
--replace-draft is explicitly supplied; never use it after human corrections.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
from PIL import Image, ImageOps
from kraken.containers import Segmentation
from kraken.lib.segmentation import extract_polygons
from ocr_line_images import prepare_rectified_line
from compile_level1_markdown import export_markdown

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.cache/ocr-model/bodleian-supplements'
SOURCE = ROOT / '.cache/sources/bodleian/supplements'
OBJECT = 'https://digital.bodleian.ox.ac.uk/objects/462146c4-dadb-4aa5-b324-2d45e30e5ddd/'


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replace-draft', action='store_true')
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    sources = json.loads((ROOT/'sources/bodleian-supplement-sources.json').read_text())['pages']
    sides = [s['printed_page'] for s in sources]
    history = json.loads((ROOT/'pilot/human-review/correction-history.json').read_text())
    protected = {p['id'] for p in history['pages']}
    for source in sources:
        pid = source['id']
        target = ROOT/f'pilot/format-v1-trial/level1-source/{pid}.md'
        if pid in protected:
            raise ValueError(f'Refusing to replace human-corrected {pid}')
        if target.exists():
            existing = json.loads((ROOT/f'pilot/format-v1-trial/level1/{pid}.json').read_text())
            if existing['review'].get('origin') != 'calamari_v2_machine_provisional' or existing['review'].get('status') != 'visual_draft':
                raise ValueError(f'Refusing to replace reviewed {pid}')
            backup = WORK/'before-structural-preparation'/target.name
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copy2(target, backup)
    for side in sides:
        pid = f'bodleian-f{int(side[:-1]):04d}{side[-1]}'
        target = ROOT / f'pilot/format-v1-trial/level1-source/{pid}.md'
        if target.exists() and not args.replace_draft:
            raise ValueError(f'Refusing to replace existing {pid}')
        scan = SOURCE / f'{pid}.jpg'
        source = next(s for s in sources if s['id']==pid)
        if hashlib.sha256(scan.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f'Source checksum changed: {pid}')
        if (WORK/f'{pid}-lines.json').exists():
            # Existing detection order is also the published stable-ID order.
            continue
        seg_path = WORK / f'{pid}-segmentation.json'
        if not seg_path.exists():
            subprocess.run(['arch', '-arm64', str(ROOT / '.cache/ocr-model/venv-kraken-arm64/bin/kraken'),
                            '-i', str(scan), str(seg_path), 'segment', '-bl'], check=True)
        raw = json.loads(seg_path.read_text())
        seg = Segmentation(**raw)
        # Source-page bands exclude the ruler and the sliver of the facing leaf.
        # Individual boundaries/baselines come from Kraken, not old Gallica data.
        left, middle, right = (390, 1450, 2530) if side.endswith('r') else (970, 2025, 3130)
        records = []
        with Image.open(scan) as image:
            for crop, line in extract_polygons(ImageOps.invert(image.convert('RGB')), seg):
                xs, ys = zip(*line.baseline)
                x, y = sum(xs)/len(xs), sum(ys)/len(ys)
                if not (left < x < right and 480 < y < 3460):
                    continue
                col = 1 if x < middle else 2
                path = WORK / f'{pid}__{line.id}.png'
                prepare_rectified_line(ImageOps.invert(crop)).save(path)
                records.append({'image': str(path), 'column': col, 'y': y,
                                'boundary': line.boundary, 'baseline': line.baseline})
        records.sort(key=lambda r: (r['column'], r['y']))
        save(WORK / f'{pid}-lines.json', records)
    legacy = WORK/'predictions.json'
    by_image = {r['image']:r for r in json.loads(legacy.read_text())['lines']} if legacy.exists() else {}
    for source in sources:
        pid = source['id']
        records = json.loads((WORK/f'{pid}-lines.json').read_text())
        missing = [r['image'] for r in records if r['image'] not in by_image]
        if missing:
            predictions = WORK/f'{pid}-predictions.json'
            if not predictions.exists():
                subprocess.run(['python3', str(ROOT/'scripts/recognize_nippo_calamari.py'),
                                *missing, '--prepared', '--model', str(ROOT/'models/local/nippo-calamari-v2-styled'),
                                '--output', str(predictions)], check=True)
            by_image.update({r['image']:r for r in json.loads(predictions.read_text())['lines']})
        print('recognized', pid, flush=True)
    geometry_path = ROOT/'pilot/human-review/line-geometry.json'
    geometry = json.loads(geometry_path.read_text())
    for side in sides:
        pid = f'bodleian-f{int(side[:-1]):04d}{side[-1]}'
        scan = SOURCE / f'{pid}.jpg'
        with Image.open(scan) as image:
            width, height = image.size
        page = {'format': 'nippo-level1-page', 'format_version': 1, 'id': pid,
                'source': {'repository': 'Bodleian Library Arch. B d.13', 'view': pid,
                           'url': OBJECT, 'master_sha256': hashlib.sha256(scan.read_bytes()).hexdigest()},
                'scope': 'full_dictionary_text_and_furniture',
                'review': {'origin': 'calamari_v2_machine_provisional',
                           'wikisource_used_for_this_trial': False,
                           'physical_lineation_checked': False, 'status': 'visual_draft'}, 'zones': []}
        geo = {'id': pid, 'source_size': [width, height], 'columns': {}}
        rows = json.loads((WORK/f'{pid}-lines.json').read_text())
        for col in (1, 2):
            zone = {'id': f'column-{col}', 'kind': 'column', 'label': f'Column {col}', 'lines': []}
            g = {'visual_review': 'ocr_bootstrap_unreviewed', 'lines': {}}
            for index, row in enumerate((r for r in rows if r['column']==col), 1):
                lid = f'c{col}-l{index:03d}'
                prediction = by_image[row['image']]
                zone['lines'].append({'id': lid, 'runs': prediction['runs'] or [{'typeface':'roman','text':'[unreadable]'}]})
                xs, ys = zip(*row['boundary'])
                crop = [max(0, int(min(xs))-15), max(0, int(min(ys))-12),
                        min(width, int(max(xs))+20), min(height, int(max(ys))+12)]
                context = [crop[0], max(0,crop[1]-80), crop[2], min(height,crop[3]+80)]
                # Public geometry uses x/y/width/height, not opposite corners.
                g['lines'][lid] = {
                    'crop': [crop[0], crop[1], crop[2]-crop[0], crop[3]-crop[1]],
                    'context_crop': [context[0], context[1], context[2]-context[0], context[3]-context[1]]}
            page['zones'].append(zone)
            geo['columns'][zone['id']] = g
        from structure_bodleian_supplement import structure_page
        page, geo = structure_page(page, geo, rows)
        save(ROOT/f'pilot/format-v1-trial/level1/{pid}.json', page)
        (ROOT/f'pilot/format-v1-trial/level1-source/{pid}.md').write_text(export_markdown(page))
        geometry['pages'] = [g for g in geometry['pages'] if g['id'] != pid] + [geo]
        print(pid, len(rows), 'machine-only lines', flush=True)
    save(geometry_path, geometry)
    save(ROOT/'sources/supplemental-pages.json', {'pages': sources})


if __name__ == '__main__':
    main()
