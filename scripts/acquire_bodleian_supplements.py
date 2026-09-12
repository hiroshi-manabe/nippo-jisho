#!/usr/bin/env python3
"""Acquire all 28 missing-leaf sides by explicit Bodleian signature labels."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import time
from urllib.request import urlopen
from PIL import Image
from download_bodleian_gap_pilot import MANIFEST

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/sources/bodleian/supplements'
# Printed folio pair, signature gathering, preceding Gallica view.
GAPS = ((90, 'Z', 190), (110, 'Ee', 226), (158, 'Rr', 318),
        (222, 'Kkk', 442), (234, 'Nnn', 462), (286, 'c', 562), (310, 'i', 606))
OBJECT = 'https://digital.bodleian.ox.ac.uk/objects/462146c4-dadb-4aa5-b324-2d45e30e5ddd/'


def acquire(record):
    target = ROOT / record['cache_path']
    legacy = ROOT / '.cache/sources/bodleian/pilot-110-111' / f"{record['printed_page']}-native.jpg"
    if not target.exists() and legacy.exists():
        shutil.copy2(legacy, target)
    for attempt in range(3):
        try:
            data = target.read_bytes() if target.exists() else urlopen(record['image_url'], timeout=180).read()
            with Image.open(BytesIO(data)) as image:
                image.load()
                width, height = image.size
            if not target.exists():
                target.write_bytes(data)
            record.update(width=width, height=height, sha256=hashlib.sha256(data).hexdigest())
            print(record['id'], width, height, flush=True)
            return record
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    with urlopen(MANIFEST, timeout=120) as response:
        raw = response.read()
    (CACHE/'manifest.json').write_bytes(raw)
    canvases = json.loads(raw)['sequences'][0]['canvases']
    records = []
    for start, gathering, after in GAPS:
        for offset in (0, 1):
            for side in ('r', 'v'):
                folio = start + offset
                label = f'fol. {gathering}{offset+2}{side}'
                matches = [c for c in canvases if c['label'] == label]
                if len(matches) != 1:
                    raise ValueError(f'Ambiguous/missing canvas: {label}')
                canvas = matches[0]
                pid = f'bodleian-f{folio:04d}{side}'
                records.append({'id': pid, 'leaf': pid, 'view': pid,
                    'printed_page': f'{folio}{side}', 'canvas_label': label,
                    'canvas': canvas['@id'], 'insert_after': f'bnf-f{after:04d}',
                    'source_url': OBJECT, 'image_url': canvas['images'][0]['resource']['service']['@id']+'/full/full/0/default.jpg',
                    'source_credit': 'Bodleian Library, Arch. B d.13. Photo: © Bodleian Libraries, University of Oxford. CC BY-NC 4.0.',
                    'image_stem': f'supplements/{pid}',
                    'cache_path': str((CACHE/f'{pid}.jpg').relative_to(ROOT))})
    with ThreadPoolExecutor(max_workers=3) as pool:
        completed = list(pool.map(acquire, records))
    (ROOT/'sources/bodleian-supplement-sources.json').write_text(
        json.dumps({'manifest': MANIFEST, 'pages': completed}, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
