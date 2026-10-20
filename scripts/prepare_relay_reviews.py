#!/usr/bin/env python3
"""Convert outstanding review packages for prose-driven ChatGPT relay pickup.

Never enqueues jobs, overwrites source archives, or changes canonical pages.
"""
import argparse
import fcntl
import json
from pathlib import Path
import sqlite3
import zipfile

import external_ai_review as review

MODEL_SENTENCE = 'This package is intended to be processed using ChatGPT’s 6 Pro setting.'


def convert_members(files):
    files = dict(files)
    text = files['README.md'].decode('utf-8')
    if MODEL_SENTENCE not in text:
        heading, separator, rest = text.partition('\n\n')
        if not separator:
            raise ValueError('Expected a README heading followed by instructions')
        files['README.md'] = (heading + '\n\n' + MODEL_SENTENCE + '\n\n' + rest).encode()
    manifest = json.loads(files['manifest.json'])
    manifest['files']['README.md'] = review.sha(files['README.md'])
    files['manifest.json'] = review.encoded(manifest)
    template = json.loads(files['result-template/result.json'])
    template['input_manifest_sha256'] = review.sha(files['manifest.json'])
    files['result-template/result.json'] = review.encoded(template)
    for name, digest in manifest['files'].items():
        if review.sha(files[name]) != digest:
            raise ValueError(f'Invalid package member hash: {name}')
    return files


def metadata(path, member):
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read(member))


def plan(input_dir, relay_root):
    excluded = {pid: 'human-reviewed/protected' for pid in review.human_protected()}
    for pid in json.loads((review.ROOT / review.REGISTRY).read_bytes())['pages']:
        excluded.setdefault(pid, 'AI review already imported')
    # Returned results must not be resubmitted merely because they await import.
    for directory in (review.ROOT / 'exports/external-review', relay_root / 'output'):
        for path in directory.rglob('*result*.zip'):
            if 'backups' in path.parts:
                continue
            try:
                result = metadata(path, 'result.json')
            except (KeyError, ValueError, zipfile.BadZipFile):
                continue
            if result.get('package_id', '').startswith('production-'):
                for pid in result.get('pages', {}):
                    excluded.setdefault(pid, f'review result already returned: {path.name}')
    dbpath = relay_root / 'relay.sqlite3'
    if dbpath.exists():
        with sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True) as db:
            for name, status in db.execute('SELECT input_name, status FROM jobs'):
                # Include failed/uncertain submissions: retry needs explicit authority.
                for path in (relay_root / 'input' / name, *input_dir.rglob(name)):
                    if path.exists():
                        for pid in metadata(path, 'manifest.json')['pages']:
                            excluded.setdefault(pid, f'existing relay job: {status}')
                        break
    registry = {p['id']: p for p in json.loads((review.ROOT / review.GEOMETRY).read_bytes())['pages']}
    packages, omitted, seen = [], [], set()
    for archive in sorted(input_dir.rglob('*-input.zip')):
        manifest = metadata(archive, 'manifest.json')
        if manifest.get('mode') != 'production':
            continue
        targets = []
        for pid in manifest['pages']:
            if pid in seen or pid in excluded:
                omitted.append({'page': pid, 'source': str(archive), 'reason': excluded.get(pid, 'duplicate input')})
            else:
                targets.append(pid)
                seen.add(pid)
        if not targets:
            continue
        stale = targets != list(manifest['pages'])
        for pid in targets:
            path, raw, _, geo, kind = review.baseline(pid)
            spec = manifest['pages'][pid]
            rg = registry.get(pid)
            stale |= (path != spec['source_path'] or kind != spec['source_kind']
                      or review.sha(raw) != spec['source_sha256']
                      or review.sha(review.encoded(geo)) != spec['geometry_sha256']
                      or (review.sha(review.encoded(rg)) if rg else None) != spec.get('registry_geometry_sha256'))
        packages.append({'source': str(archive.resolve()), 'pages': targets,
                         'action': 'regenerate' if stale else 'convert',
                         'kind': 'supplemental' if targets[0].startswith('bodleian-') else 'ordinary'})
    return {'packages': packages, 'omitted': omitted}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=review.ROOT / 'exports/external-review/remaining-20260912')
    parser.add_argument('--relay', type=Path, default=review.ROOT.parent / 'chatgpt-relay')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Choose a new output directory; existing archives are never overwritten')
    inventory = plan(args.input.resolve(), args.relay.resolve())
    print(json.dumps({'batches': len(inventory['packages']), 'pages': sum(len(p['pages']) for p in inventory['packages']),
                      'regenerate': sum(p['action'] == 'regenerate' for p in inventory['packages']),
                      'omitted': len(inventory['omitted'])}), flush=True)
    if args.dry_run:
        for package in inventory['packages']:
            print(package['action'], ', '.join(package['pages']))
        return
    args.output.mkdir(parents=True)
    inventory['baseline_commit'] = review.git('rev-parse', 'HEAD').decode().strip()
    for item in inventory['packages']:
        source = Path(item['source'])
        if item['action'] == 'regenerate':
            generated = args.output / 'regenerated-originals' / item['kind']
            review.package(argparse.Namespace(evaluation=False, pages=item['pages'], output=generated))
            source = next(p for p in generated.glob('*-input.zip') if list(metadata(p, 'manifest.json')['pages']) == item['pages'])
        files = convert_members(review.read_zip(source))
        destination = args.output / 'ready' / item['kind'] / source.name
        review.write_zip(destination, files)
        item['output'] = str(destination.resolve())
        item['expected_result'] = json.loads(files['manifest.json'])['package_id'] + '-result.zip'
        (args.output / 'index.json').write_bytes(review.encoded(inventory))
        print('Prepared', destination.name, flush=True)


if __name__ == '__main__':
    # Share the importer lock so baselines cannot change halfway through a run.
    lock_path = review.ROOT / 'exports/review-inbox/lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        main()
