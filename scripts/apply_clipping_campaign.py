#!/usr/bin/env python3
"""Apply a visually reviewed clipping pilot; refuse stale geometry or missing coverage."""
import argparse
import copy
import json
from datetime import date
from pathlib import Path

from apply_ocr_layout_geometry_campaign import valid_xywh
from import_ocr_first_geometry import write_compact_pages
from prepare_clipping_campaign import fingerprint

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal-dir', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    proposals = read(args.proposal_dir / 'proposal.json')
    evidence = read(args.proposal_dir / 'coverage.json')
    decisions = read(args.decisions)
    paths = [ROOT / 'pilot/human-review/line-geometry.json',
             ROOT / 'pilot/human-review/line-calibration.json',
             ROOT / 'pilot/tile-config-v1-trial.json']
    documents = [read(p) for p in paths]
    geometry, calibration, tiles = [{p['id']: p for p in d['pages']} for d in documents]
    expected = set(range(decisions['pilot_range'][0], decisions['pilot_range'][1] + 1))
    if {int(p['id'].split('f')[-1]) for p in proposals['pages']} != expected:
        raise SystemExit('Proposal range does not cover the complete pilot')
    for column in evidence['columns']:
        leaf = int(column['page'].split('f')[-1])
        for line in column['lines']:
            key = f"{leaf}:{column['column']}:{line['id']}"
            if line['disposition'] == 'manual_alignment_required' and not decisions['notes'].get(key):
                raise SystemExit(f'Manual alignment decision missing: {key}')
    columns = []
    seen = set()
    today = date.today().isoformat()
    for proposed in proposals['pages']:
        page_id = proposed['id']
        leaf = int(page_id.split('f')[-1])
        old_page = geometry[page_id]
        if fingerprint(old_page) != evidence['baselines'][page_id]:
            raise SystemExit(f'Stale proposal: {page_id}; regenerate and recheck')
        carry = decisions.get('unchanged_prior_verification', {}).get(str(leaf))
        if leaf not in decisions['reviewed_pages'] and not carry:
            raise SystemExit(f'Visual review incomplete: {page_id}')
        if proposed['columns'].keys() != old_page['columns'].keys():
            raise SystemExit(f'Column coverage mismatch: {page_id}')
        for name, value in proposed['columns'].items():
            old = old_page['columns'][name]
            if value['lines'].keys() != old['lines'].keys():
                raise SystemExit(f'Line IDs changed: {page_id}/{name}')
            for line in value['lines'].values():
                for field in ('crop', 'context_crop'):
                    if not valid_xywh(line[field], old_page['source_size']):
                        raise SystemExit(f'Invalid {field}: {page_id}/{name}')
            changed = [key for key in old['lines'] if old['lines'][key]['crop'] != value['lines'][key]['crop']]
            if carry and changed:
                raise SystemExit(f'Prior verification cannot cover changed crops: {page_id}')
            notes = {k.split(':')[-1]: v for k, v in decisions['notes'].items()
                     if k.startswith(f'{leaf}:{name}:')}
            columns.append({'page': page_id, 'column': name,
                            'status': 'repaired_verified' if changed else 'checked_unchanged',
                            'line_count': len(old['lines']), 'changed_crop_count': len(changed),
                            'verification': carry or 'Every isolated crop inspected beside its canonical text.',
                            'notes': notes,
                            'geometry_fingerprint': fingerprint(value['lines'])})
            seen.add((page_id, name))
            if not changed:
                continue
            value = copy.deepcopy(value)
            value.update(visual_review='line_by_line_reverified', reviewed_at=today,
                         geometry_method='ocr_clipping_proposal_visual_crop_verification')
            old_page['columns'][name] = value
            cc = calibration[page_id]['columns'][name]
            cc.update(projection_snap=False, review_state='line_by_line_reverified',
                      reviewed_at=today, geometry_method=value['geometry_method'])
            cc['centre_overrides'] = {k: v['centre_y'] for k, v in value['lines'].items()}
            # Explicit rectangles are authoritative; don't leave stale crop overrides.
            if 'crop_overrides' in cc:
                cc['crop_overrides'] = {k: v['crop'] for k, v in value['lines'].items()}
            for zone in tiles[page_id]['zones']:
                if zone['id'] == name:
                    a, b, c, d = zone['box']
                    x, y, r, bottom = value['box']
                    zone['box'] = [min(a, x), min(b, y), max(c, r), max(d, bottom)]
    if seen != {(c['page'], c['column']) for c in evidence['columns']}:
        raise SystemExit('Coverage ledger mismatch')
    result = {'format': 'nippo-clipping-campaign-coverage', 'reviewed_at': today,
              'range': decisions['pilot_range'], 'scope': 'body columns only',
              'status': 'pilot_complete', 'unresolved_columns': [], 'columns': columns}
    print(f"{len(columns)} columns; {sum(c['line_count'] for c in columns)} lines; "
          f"{sum(c['changed_crop_count'] for c in columns)} adjusted crops")
    if args.apply:
        write(paths[0], documents[0])
        write_compact_pages(paths[1], documents[1])
        write(paths[2], documents[2])
        write(args.decisions.parent / 'coverage.json', result)
        print('Applied reviewed geometry without changing transcription.')
    else:
        print('Dry run; pass --apply to save.')


if __name__ == '__main__':
    main()
