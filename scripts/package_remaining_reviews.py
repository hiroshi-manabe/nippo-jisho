#!/usr/bin/env python3
"""Create separate self-contained ordinary/supplemental batches, remainders included."""
import argparse
import json
from pathlib import Path
import external_ai_review as review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='Reuse matching packages with unchanged baselines')
    args = parser.parse_args()
    if args.output.exists() and not args.resume:
        raise ValueError('Use a new output directory')
    protected = review.human_protected()
    checked = json.loads((review.ROOT / review.REGISTRY).read_bytes())['pages']
    ids = {p.stem for p in (review.ROOT / review.SOURCE).glob('*.md')}
    for folder in ('pilot/ocr-bootstrap/f0238-f0247', 'pilot/ocr-bootstrap/f0251-f0642/pages'):
        ids.update(p.stem for p in (review.ROOT / folder).glob('bnf-f*.json'))
    groups = {'ordinary': [], 'supplemental': []}
    omitted = []
    for pid in sorted(ids):
        if pid in protected or pid in checked:
            omitted.append({'id': pid, 'reason': 'human protected or commentary reviewed'})
            continue
        try:
            _, _, page, _, _ = review.baseline(pid)
            if not review.lines(page, True):
                omitted.append({'id': pid, 'reason': 'no body columns'})
                continue
        except ValueError as exc:
            omitted.append({'id': pid, 'reason': str(exc)})
            continue
        groups['supplemental' if pid.startswith('bodleian-') else 'ordinary'].append(pid)
    index = {'baseline_commit': review.git('rev-parse', 'HEAD').decode().strip(), 'batches': [], 'omitted': omitted}
    args.output.mkdir(parents=True, exist_ok=True)
    for kind, pages in groups.items():
        for offset in range(0, len(pages), 3):
            targets = pages[offset:offset + 3]
            existing = []
            for archive in (args.output / kind).glob('*-input.zip'):
                import zipfile
                with zipfile.ZipFile(archive) as z:
                    manifest = json.loads(z.read('manifest.json'))
                if list(manifest['pages']) == targets:
                    for pid, spec in manifest['pages'].items():
                        _, raw, _, geo, _ = review.baseline(pid)
                        if review.sha(raw) != spec['source_sha256'] or review.sha(review.encoded(geo)) != spec['geometry_sha256']:
                            raise ValueError(f'Stale existing package: {archive}')
                    existing.append(archive)
            if not existing:
                review.package(argparse.Namespace(evaluation=False, pages=targets, output=args.output / kind))
            index['batches'].append({'kind': kind, 'pages': targets})
            (args.output / 'batch-index.json').write_bytes(review.encoded(index))
    print({kind: len(pages) for kind, pages in groups.items()})


if __name__ == '__main__':
    main()
