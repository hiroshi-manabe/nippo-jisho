#!/usr/bin/env python3
"""Generate (never apply) clipping repairs and complete column coverage ledger."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def propose(line, match, size):
    """A readable proposal, not proof that the OCR polygon contains all ink."""
    if not match or match['relaxed_cer'] > .25 or 'neighbor_conflict' in match['flags']:
        return copy.deepcopy(line), 'manual_alignment_required'
    if not any(f in match['flags'] for f in ('vertical_clip', 'horizontal_clip')):
        return copy.deepcopy(line), 'inspect_existing'
    result = copy.deepcopy(line)
    x, y, w, h = line['crop']
    dx, dy, dw, dh = match['detected_bbox']
    left, right = max(0, min(x, dx - 6)), min(size[0], max(x + w, dx + dw + 6))
    # Preserve existing readable coverage; inclusion of neighboring ink is
    # preferable to silently dropping a descender or a displaced fragment.
    top, bottom = max(0, min(y, dy - 6)), min(size[1], max(y + h, dy + dh + 6))
    result['crop'] = [left, top, right-left, bottom-top]
    result['centre_y'] = round(match['ocr_centre_y'])
    result['context_crop'] = [left, max(0, top-85), right-left,
                              min(size[1], bottom+85)-max(0, top-85)]
    return result, 'inspect_proposal'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(gzip.decompress(args.audit.read_bytes()))
    current = json.loads((ROOT/'pilot/human-review/line-geometry.json').read_text())
    by_id = {p['id']: p for p in current['pages']}
    pages, ledger, baselines = [], [], {}
    for record in audit['pages']:
        page = copy.deepcopy(by_id[record['id']])
        baselines[page['id']] = fingerprint(page)
        matches = {(m['column'], m['line_id']): m for m in record['lines']}
        for column_id, column in page['columns'].items():
            entries = []
            for line_id, line in list(column['lines'].items()):
                proposal, disposition = propose(line, matches.get((column_id, line_id)), page['source_size'])
                column['lines'][line_id] = proposal
                entries.append({'id': line_id, 'disposition': disposition,
                                'changed': proposal['crop'] != line['crop']})
            crops = [l['crop'] for l in column['lines'].values()]
            a,b,c,d = column['box']
            column['box'] = [min(a, *(r[0] for r in crops)), min(b, *(r[1] for r in crops)),
                             max(c, *(r[0]+r[2] for r in crops)), max(d, *(r[1]+r[3] for r in crops))]
            ledger.append({'page': page['id'], 'column': column_id,
                           'status': 'awaiting_visual_review', 'lines': entries})
        pages.append(page)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('proposal.json', {**current, 'pages': pages}),
                        ('coverage.json', {'format': 'nippo-clipping-campaign', 'baselines': baselines, 'columns': ledger})]:
        (args.output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
