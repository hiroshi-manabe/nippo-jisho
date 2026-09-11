#!/usr/bin/env python3
"""Versioned external-review packages, blind evaluation and guarded UI import."""
import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from compile_level1_markdown import parse_markdown, export_markdown, Level1MarkdownError
from kana_reading import reading_hint

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'pilot/format-v1-trial/level1-source'
COMPILED = 'pilot/format-v1-trial/level1'
GEOMETRY = 'pilot/human-review/line-geometry.json'
REGISTRY = 'pilot/human-review/commentary-reviews.json'
TERMS = 'pilot/human-review/typeface-toggle-terms.json'
REFS = ['transcription-cheat-sheet.md', 'historical-language-notes.md',
        'level1-markdown-candidate.md', 'headword-data.md']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def snapshot(ref, path):
    return git('show', f'{ref}:{path}')


def parse(data):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'page.md'
        p.write_bytes(data)
        return parse_markdown(p)


def lines(page, body=False):
    return {line['id']: line for zone in page['zones']
            if not body or zone['kind'] == 'column'
            for line in zone.get('lines', [])}


def plain(line):
    return ''.join(r['text'] for r in line['runs'])


def crops(geometry):
    return {lid: line['crop'] for col in geometry['columns'].values()
            for lid, line in col['lines'].items()}


def read_zip(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP members')
        if sum(i.file_size for i in z.infolist()) > 500_000_000:
            raise ValueError('ZIP too large')
        if any(n.startswith('/') or '..' in Path(n).parts for n in names):
            raise ValueError('Unsafe ZIP member')
        return {n: z.read(n) for n in names if not n.endswith('/')}


def write_zip(path, files):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError(f'Refusing to overwrite {path}')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            z.writestr(name, data)


def human_protected():
    from refresh_unreviewed_ocr import protected_pages
    return protected_pages()


def package(args):
    evaluation = args.evaluation
    targets = [202, 203, 204] if evaluation else args.pages
    if not targets or len(targets) != len(set(targets)):
        raise ValueError('Supply unique target pages')
    base = git('rev-parse', 'fa1b73ca' if evaluation else 'HEAD').decode().strip()
    reviewed = git('rev-parse', '6d59395e').decode().strip()
    human = git('rev-parse', 'a6b22a76').decode().strip()
    if not evaluation and git('status', '--porcelain', '--untracked-files=no').strip():
        raise ValueError('Production packaging requires a clean tracked worktree')
    pid = ('evaluation' if evaluation else 'production') + '-' + '-'.join(f'f{n:04}' for n in targets) + '-' + base[:8]
    files, private = {}, {}
    geo_all = json.loads(snapshot(base, GEOMETRY))
    geos = {p['id']: p for p in geo_all['pages']}
    manifest = {'schema': 1, 'package_id': pid, 'mode': 'evaluation' if evaluation else 'production',
                'baseline_commit': base, 'pages': {}, 'files': {}}
    for n in ([201] + targets):
        page_id = f'bnf-f{n:04}'
        ref = 'fa1b73ca' if n == 201 else base
        md = snapshot(ref, f'{SOURCE}/{page_id}.md')
        page = parse(md)
        geometry = geos[page_id] if n != 201 else next(p for p in json.loads(snapshot(ref, GEOMETRY))['pages'] if p['id'] == page_id)
        prefix = 'example/input' if n == 201 else f'targets/{page_id}'
        # Pre-existing notes may predate the refreshed OCR and must not be mistaken
        # for a completed review. Remove them from input only, not baseline hashes.
        draft = copy.deepcopy(page)
        for line in lines(draft).values():
            line.pop('note', None)
        files[f'{prefix}/page.md'] = export_markdown(draft).encode()
        files[f'{prefix}/geometry.json'] = encoded({'source_size': geometry['source_size'], 'crops': crops(geometry)})
        files[f'{prefix}/reading-hints.json'] = encoded({lid: reading_hint(l['runs']) for lid, l in lines(draft, True).items()})
        image_path = ROOT / f'build/nippo-jisho-images/scans/native/f{n:04}.jpg'
        files[f'{prefix}/scan.jpg'] = image_path.read_bytes()
        from PIL import Image
        with Image.open(image_path) as image:
            if list(image.size) != geometry['source_size']:
                raise ValueError(f'{page_id}: scan/geometry dimensions differ')
            image.verify()
        evidence_path = f'pilot/ocr-layout-evidence/v1/pages/{page_id}.json.gz'
        files[f'{prefix}/ocr-layout.json.gz'] = snapshot(ref, evidence_path)
        files[f'{prefix}/source.txt'] = f'Source gallica.bnf.fr / Bibliothèque nationale de France\n{page["source"]["url"]}\nNative JPEG bytes; do not use reduced chat previews.\n'.encode()
        if n == 201:
            files['example/reviewed/page.md'] = snapshot(reviewed, f'{SOURCE}/{page_id}.md')
            rg = next(p for p in json.loads(snapshot(reviewed, GEOMETRY))['pages'] if p['id'] == page_id)
            files['example/reviewed/geometry.json'] = encoded({'source_size': rg['source_size'], 'crops': crops(rg)})
            continue
        if not evaluation:
            if page_id in human_protected() or page['review']['status'] == 'human_checked':
                raise ValueError(f'Human-protected page: {page_id}')
        manifest['pages'][page_id] = {'source_sha256': sha(md), 'geometry_sha256': sha(encoded(geometry)),
                                     'input_prefix': prefix}
        files[f'result-template/pages/{page_id}.md'] = files[f'{prefix}/page.md']
        files[f'result-template/pages/{page_id}.geometry.json'] = files[f'{prefix}/geometry.json']
        if evaluation:
            for label, ref in [('ocr', base), ('local', reviewed), ('human', human)]:
                private[f'{label}/{page_id}.md'] = snapshot(ref, f'{SOURCE}/{page_id}.md')
                reference_geometry = next(p for p in json.loads(snapshot(ref, GEOMETRY))['pages'] if p['id'] == page_id)
                private[f'{label}/{page_id}.geometry.json'] = encoded({'source_size': reference_geometry['source_size'], 'crops': crops(reference_geometry)})
    for name in REFS:
        files[f'references/{name}'] = snapshot('fa1b73ca' if evaluation else base, f'docs/{name}')
    files['references/shared-ai-review-procedure.md'] = (ROOT / 'docs/shared-ai-review-procedure.md').read_bytes()
    dataset = ROOT / '.cache/external/ninjal-headwords/202510/unpacked/ew-nippo-202510/ew-nippo-202510.txt'
    rows = dataset.read_text().splitlines()
    selected = [r for r in rows[1:] if any(f'/f{n}.item' in r for n in [201] + targets)]
    files['references/ninjal-headwords.tsv'] = ('\n'.join([rows[0]] + selected) + '\n').encode()
    files['references/ninjal-attribution.txt'] = b'Entry Words Data of Nippojisho, NINJAL, Hideyuki Ohshima and Taichi Aida, version 202510. CC BY 4.0. Page subset only. https://www2.ninjal.ac.jp/textdb_dataset/en/nipp/index.html https://creativecommons.org/licenses/by/4.0/\n'
    files['README.md'] = (ROOT / 'docs/external-ai-package-instructions.md').read_bytes()
    # Hash substantive package members, excluding the manifest and result template
    # whose manifest hash would otherwise create a circular dependency.
    manifest['files'] = {n: sha(d) for n, d in files.items() if not n.startswith('result-template/')}
    mb = encoded(manifest)
    files['manifest.json'] = mb
    files['result-template/result.json'] = encoded({'schema': 1, 'package_id': pid, 'input_manifest_sha256': sha(mb),
        'reviewer': '', 'pages': {p: {'first_pass': False, 'second_pass': False, 'crops_inspected': False,
          'uncertainties': [], 'structural_changes': [], 'typeface_terms': {}} for p in manifest['pages']}})
    dest = args.output / f'{pid}-input.zip'
    write_zip(dest, files)
    if evaluation:
        private['evaluation.json'] = encoded({'package_id': pid, 'input_manifest_sha256': sha(mb),
          'ocr_commit': base, 'local_commit': reviewed, 'human_commit': human})
        write_zip(args.output / f'{pid}-EVALUATOR-DO-NOT-SEND.zip', private)
    print(dest.resolve())


def structure(page):
    p = copy.deepcopy(page)
    for z in p['zones']:
        for l in z.get('lines', []):
            if z['kind'] == 'column':
                l.pop('note', None)
                l['runs'] = [{k: v for k, v in r.items() if k not in ('text', 'typeface')} for r in l['runs']]
                # Typeface splits may split identical placement metadata too.
                l['runs'] = [r for i, r in enumerate(l['runs']) if i == 0 or r != l['runs'][i-1]]
    return p


def batches(args):
    """Package complete consecutive batches; report rather than hide omissions."""
    if args.start < 1 or args.end < args.start or args.size < 1:
        raise ValueError('Invalid batch range or size')
    candidates = list(range(args.start, args.end + 1))
    protected = human_protected()
    plans, omitted = [], []
    for offset in range(0, len(candidates), args.size):
        group = candidates[offset:offset + args.size]
        if len(group) != args.size:
            omitted.append({'pages': group, 'reason': 'Incomplete final batch; held for later'})
            continue
        reasons = []
        for n in group:
            pid = f'bnf-f{n:04}'
            path = ROOT / SOURCE / f'{pid}.md'
            if not path.exists():
                reasons.append(f'{pid}: unsupported noncanonical page')
            elif pid in protected or parse(path.read_bytes())['review']['status'] == 'human_checked':
                reasons.append(f'{pid}: human-protected')
        if reasons:
            omitted.append({'pages': group, 'reason': '; '.join(reasons)})
        else:
            plans.append(group)
    if (args.output / 'batch-index.json').exists():
        raise ValueError('Batch index already exists; use a new output directory')
    for group in plans:
        package(argparse.Namespace(evaluation=False, pages=group, output=args.output))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'batch-index.json').write_bytes(encoded({'schema': 1,
        'baseline_commit': git('rev-parse', 'HEAD').decode().strip(),
        'batches': plans, 'omitted': omitted,
        'input_archives': sorted(p.name for p in args.output.glob('*-input.zip'))}))
    print(f'{len(plans)} complete batches; omitted: {omitted}')


def validate(input_path, result_path, require_ready=False):
    incoming, result = read_zip(input_path), read_zip(result_path)
    m, r = json.loads(incoming['manifest.json']), json.loads(result['result.json'])
    if m['schema'] != 1 or r['schema'] != 1 or r['package_id'] != m['package_id'] or r['input_manifest_sha256'] != sha(incoming['manifest.json']):
        raise ValueError('Result does not match input manifest')
    if m['mode'] not in ('evaluation', 'production') or not m['pages'] or any(not re.fullmatch(r'bnf-f[0-9]{4}', pid) for pid in m['pages']):
        raise ValueError('Invalid package mode or page IDs')
    for n, digest in m['files'].items():
        if sha(incoming[n]) != digest:
            raise ValueError(f'Input hash mismatch: {n}')
    if set(r['pages']) != set(m['pages']) or not isinstance(r['reviewer'], str) or not r['reviewer'].strip():
        raise ValueError('Missing pages or reviewer')
    expected = {'result.json'} | {f'pages/{p}{suffix}' for p in m['pages'] for suffix in ('.md', '.geometry.json')}
    if set(result) != expected:
        raise ValueError('Unexpected or missing result members (no nested ZIP root)')
    pages = {}
    for pid, spec in m['pages'].items():
        old = parse(incoming[spec['input_prefix'] + '/page.md'])
        new = parse(result[f'pages/{pid}.md'])
        if old['id'] != pid or old['review']['status'] == 'human_checked':
            raise ValueError(f'{pid}: wrong page identity or human-checked input')
        info = r['pages'][pid]
        if structure(old) != structure(new):
            raise ValueError(f'{pid}: structural/metadata/furniture change needs adjudication')
        for key in ('uncertainties', 'structural_changes'):
            if not isinstance(info.get(key), list):
                raise ValueError(f'{pid}: {key} must be a list')
        for key in ('first_pass', 'second_pass', 'crops_inspected'):
            if info.get(key) is not True:
                raise ValueError(f'{pid}: incomplete {key}')
        if require_ready and (info['uncertainties'] or info['structural_changes']):
            raise ValueError(f'{pid}: unresolved reports need a decision')
        for lid, line in lines(new, True).items():
            if not isinstance(line.get('note'), str) or not line['note'].strip():
                raise ValueError(f'{pid}/{lid}: missing commentary')
        geom = json.loads(result[f'pages/{pid}.geometry.json'])
        before = json.loads(incoming[spec['input_prefix'] + '/geometry.json'])
        if geom['source_size'] != before['source_size'] or set(geom['crops']) != set(before['crops']):
            raise ValueError(f'{pid}: geometry identity mismatch')
        if not set(lines(new, True)) <= set(geom['crops']):
            raise ValueError(f'{pid}: body crop missing')
        width, height = geom['source_size']
        for lid, box in geom['crops'].items():
            if not isinstance(box, list) or len(box) != 4 or any(type(v) is not int for v in box):
                raise ValueError(f'{pid}/{lid}: invalid crop')
            x, y, w, h = box
            if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
                raise ValueError(f'{pid}/{lid}: crop outside image')
        for lid, terms in info.get('typeface_terms', {}).items():
            if lid not in lines(new, True) or not isinstance(terms, list) or any(not isinstance(t, str) or not t or t not in plain(lines(new)[lid]) for t in terms):
                raise ValueError(f'{pid}: invalid typeface terms')
        pages[pid] = (new, geom)
    return m, r, pages


def distance(a, b):
    row = list(range(len(b)+1))
    for i, ac in enumerate(a, 1):
        nxt = [i]
        for j, bc in enumerate(b, 1):
            nxt.append(min(nxt[-1]+1, row[j]+1, row[j-1]+(ac != bc)))
        row = nxt
    return row[-1]


def category(a, b):
    if a == b:
        return 'typeface_or_layout_only'
    if a.replace('ſ', 's') == b.replace('ſ', 's'):
        return 'long_short_s'
    if ''.join(a.split()) == ''.join(b.split()):
        return 'spacing'
    if a.rstrip('-= ') == b.rstrip('-= '):
        return 'terminal_hyphen'
    strip_marks = lambda s: ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c))
    if strip_marks(a) == strip_marks(b):
        return 'diacritics'
    return 'other_or_mixed'


def evaluate(args):
    m, r, pages = validate(args.input, args.result)
    input_files = read_zip(args.input)
    refs = read_zip(args.evaluator)
    identity = json.loads(refs['evaluation.json'])
    if identity['package_id'] != m['package_id'] or identity['input_manifest_sha256'] != r['input_manifest_sha256']:
        raise ValueError('Wrong evaluator package')
    report = {'package_id': m['package_id'], 'warning': 'Human reference is not infallible. Metrics do not certify crops or substantive commentary.', 'pages': {}}
    for pid, (external, geom) in pages.items():
        versions = {label: lines(parse(refs[f'{label}/{pid}.md']), True) for label in ('ocr', 'local', 'human')}
        versions['external'] = lines(external, True)
        gold = versions['human']
        scores, diffs = {}, []
        for label in ('ocr', 'local', 'external'):
            v = versions[label]
            common = set(v) & set(gold)
            edits = sum(distance(plain(v[k]), plain(gold[k])) for k in common)
            total = sum(len(plain(gold[k])) for k in common)
            scores[label] = {'character_edits': edits, 'reference_characters': total,
                'cer': edits / max(total, 1), 'exact_text_lines': sum(plain(v[k]) == plain(gold[k]) for k in common),
                'missing_ids': sorted(set(gold)-set(v)), 'extra_ids': sorted(set(v)-set(gold)),
                'exact_text_but_different_runs': sum(plain(v[k]) == plain(gold[k]) and v[k]['runs'] != gold[k]['runs'] for k in common),
                'closer_than_ocr_lines': sum(distance(plain(v[k]), plain(gold[k])) < distance(plain(versions['ocr'][k]), plain(gold[k])) for k in common & set(versions['ocr'])),
                'farther_than_ocr_lines': sum(distance(plain(v[k]), plain(gold[k])) > distance(plain(versions['ocr'][k]), plain(gold[k])) for k in common & set(versions['ocr']))}
        for lid in sorted(set().union(*(set(v) for v in versions.values()))):
            values = {label: plain(v[lid]) if lid in v else None for label, v in versions.items()}
            if len(set(values.values())) > 1 or any(versions[label].get(lid, {}).get('runs') != gold.get(lid, {}).get('runs') for label in ('local', 'external')):
                diffs.append({'id': lid, 'text': values,
                    'external_difference_category': category(values['external'], values['human']) if values['external'] is not None and values['human'] is not None else 'line_inventory',
                    'runs': {label: v.get(lid, {}).get('runs') for label, v in versions.items()}})
        input_geometry = json.loads(input_files[m['pages'][pid]['input_prefix'] + '/geometry.json'])
        changed_crops = {lid: {'input': input_geometry['crops'][lid], 'external': box}
                         for lid, box in geom['crops'].items() if box != input_geometry['crops'][lid]}
        reference_geometry = {label: json.loads(refs[f'{label}/{pid}.geometry.json'])
                              for label in ('local', 'human') if f'{label}/{pid}.geometry.json' in refs}
        report['pages'][pid] = {'scores': scores, 'differences': diffs,
           'changed_crops_not_error_counts': changed_crops, 'reference_geometry': reference_geometry,
           'external_reports': r['pages'][pid]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded(report))
    print(args.output.resolve())


def apply(args):
    m, r, pages = validate(args.input, args.result, require_ready=True)
    if m['mode'] != 'production':
        raise ValueError('Evaluation results cannot be applied')
    if args.publish and git('branch', '--show-current').decode().strip() != 'main':
        raise ValueError('Publishing requires main; no automatic branch switching')
    if git('status', '--porcelain', '--untracked-files=no').strip():
        raise ValueError('Tracked worktree is not clean')
    geometry = json.loads((ROOT / GEOMETRY).read_bytes())
    lookup = {p['id']: p for p in geometry['pages']}
    protected_ids = human_protected()
    for pid, spec in m['pages'].items():
        if pid in protected_ids or sha((ROOT / f'{SOURCE}/{pid}.md').read_bytes()) != spec['source_sha256'] or sha(encoded(lookup[pid])) != spec['geometry_sha256']:
            raise ValueError(f'{pid}: stale or human-protected baseline')
    writes = {}
    registry = json.loads((ROOT / REGISTRY).read_bytes())
    terms = json.loads((ROOT / TERMS).read_bytes())
    for pid, (page, geo) in pages.items():
        page['review']['status'] = 'context_reviewed'
        writes[f'{SOURCE}/{pid}.md'] = export_markdown(page).encode()
        if parse(writes[f'{SOURCE}/{pid}.md']) != page:
            raise ValueError(f'{pid}: Markdown round-trip changed the page')
        writes[f'{COMPILED}/{pid}.json'] = encoded(page)
        for col in lookup[pid]['columns'].values():
            for lid, line in col['lines'].items():
                line['crop'] = geo['crops'][lid]
                line['centre_y'] = line['crop'][1] + line['crop'][3] / 2
                line.pop('context_crop', None)
            col['visual_review'] = 'external_line_by_line_review'
            col['reviewed_at'] = datetime.now(timezone.utc).date().isoformat()
        registry['pages'][pid] = {'completed_at': datetime.now(timezone.utc).date().isoformat(),
          'procedure': 'commentary_and_second_pass_v1', 'reviewer': r['reviewer'],
          'provenance': 'external', 'input_manifest_sha256': r['input_manifest_sha256'],
          'baseline_commit': m['baseline_commit'], 'result_sha256': sha(args.result.read_bytes())}
        terms['pages'][pid] = {lid: {'source_text': plain(lines(page)[lid]), 'terms': ts}
                              for lid, ts in r['pages'][pid].get('typeface_terms', {}).items()}
    writes[GEOMETRY], writes[REGISTRY] = encoded(geometry), encoded(registry)
    writes[TERMS] = encoded(terms)
    # An input package ID is untrusted metadata, never a filesystem path.
    receipt_name = sha(m['package_id'].encode())[:24]
    receipt_path = f'pilot/external-review/imports/{receipt_name}.json'
    if (ROOT / receipt_path).exists():
        raise ValueError('Import receipt already exists; do not overwrite a prior import')
    writes[receipt_path] = encoded(r)
    backup = ROOT / 'exports/external-review/backups' / (receipt_name + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    backup.mkdir(parents=True)
    originals = {p: (ROOT / p).read_bytes() if (ROOT / p).exists() else None for p in writes}
    for p, data in originals.items():
        if data is not None:
            dest = backup / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    (backup / 'before.json').write_bytes(encoded({'head': git('rev-parse', 'HEAD').decode().strip(), 'files': list(writes)}))
    (backup / 'input.zip').write_bytes(args.input.read_bytes())
    (backup / 'result.zip').write_bytes(args.result.read_bytes())
    try:
        for path, data in writes.items():
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_bytes(data)
        subprocess.run([sys.executable, 'scripts/compile_level1_markdown.py', 'compile', SOURCE, COMPILED, '--check'], cwd=ROOT, check=True)
        subprocess.run([sys.executable, 'scripts/build_public_review.py'], cwd=ROOT, check=True)
    except Exception:
        for p, data in originals.items():
            if data is None:
                (ROOT / p).unlink(missing_ok=True)
            else:
                (ROOT / p).write_bytes(data)
        raise
    if args.publish:
        git('add', '--', *writes)
        git('commit', '-m', f'Apply external review {m["package_id"]}')
        git('push')
    print(f'Applied; backup: {backup}. ' + ('Pushed; deployment still needs verification.' if args.publish else 'Not committed or pushed.'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    pack = sub.add_parser('package')
    pack.add_argument('--evaluation', action='store_true')
    pack.add_argument('--pages', type=int, nargs='+')
    pack.add_argument('--output', type=Path, required=True)
    batch = sub.add_parser('batches')
    batch.add_argument('--start', type=int, required=True)
    batch.add_argument('--end', type=int, required=True)
    batch.add_argument('--size', type=int, default=3)
    batch.add_argument('--output', type=Path, required=True)
    for name in ('validate', 'evaluate', 'apply'):
        s = sub.add_parser(name)
        s.add_argument('input', type=Path)
        s.add_argument('result', type=Path)
        if name == 'evaluate':
            s.add_argument('evaluator', type=Path)
            s.add_argument('--output', type=Path, required=True)
        if name == 'apply':
            s.add_argument('--publish', action='store_true')
    args = p.parse_args()
    try:
        if args.command == 'validate':
            validate(args.input, args.result)
            print('Structurally valid; this does not certify reading or crop quality.')
        else:
            globals()[args.command](args)
    except (ValueError, KeyError, OSError, Level1MarkdownError, zipfile.BadZipFile, subprocess.CalledProcessError) as e:
        p.exit(1, f'error: {e}\n')


if __name__ == '__main__':
    main()
