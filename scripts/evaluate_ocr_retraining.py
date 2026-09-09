#!/usr/bin/env python3
"""Evaluate diplomatic text and style independently from Calamari predictions."""
import argparse
from collections import Counter
import json
from pathlib import Path

from build_ocr_retraining_dataset import decode
from evaluate_line_ocr_predictions import evaluate, edit_alignment


def score(records, outputs, styled):
    if len(records) != len(outputs):
        raise ValueError('Reference/prediction count mismatch')
    predictions, combined_refs, combined_preds = [], [], []
    confusion = Counter()
    boundaries = Counter()
    short_runs = Counter()
    glyphs = {c: Counter() for c in ('ß', 'ſ', 's', 'ô', 'ǒ', 'ũ', 'ã')}
    examples = []
    for r, raw in zip(records, outputs):
        text, styles = decode(raw) if styled else (raw, None)
        predictions.append({'id': r['id'], 'text': text})
        if styled:
            combined_refs.append({'id': r['id'], 'text': r['encoded']})
            combined_preds.append({'id': r['id'], 'text': raw})
        ri = hi = 0
        wrong_style = 0
        aligned_styles = {}
        for left, right in edit_alignment(r['text'], text):
            if left in glyphs:
                glyphs[left]['reference'] += 1
                glyphs[left]['exact'] += left == right
            if styles is not None and left and left == right and not left.isspace():
                confusion[(r['styles'][ri], styles[hi])] += 1
                aligned_styles[ri] = styles[hi]
                wrong_style += r['styles'][ri] != styles[hi]
            ri += bool(left)
            hi += bool(right)
        if styled:
            positions = [i for i,c in enumerate(r['text']) if not c.isspace()]
            for a,b in zip(positions, positions[1:]):
                if a not in aligned_styles or b not in aligned_styles:
                    boundaries['unscorable_text_error'] += 1
                    continue
                expected = r['styles'][a] != r['styles'][b]
                predicted = aligned_styles[a] != aligned_styles[b]
                boundaries['true_positive' if expected and predicted else
                           'false_negative' if expected else 'false_positive' if predicted else 'true_negative'] += 1
            groups = []
            for i in positions:
                if not groups or r['styles'][groups[-1][-1]] != r['styles'][i]:
                    groups.append([])
                groups[-1].append(i)
            for group in groups:
                if len(group) <= 3:
                    short_runs['reference'] += 1
                    short_runs['exact_text_and_style'] += all(aligned_styles.get(i) == r['styles'][i] for i in group)
        if text != r['text'] or wrong_style:
            examples.append({'id': r['id'], 'reference': r['text'], 'prediction': text,
                             'wrong_style_on_correct_characters': wrong_style})
    out = {'text': evaluate(records, predictions), 'glyphs': glyphs,
           'examples': examples[:80]}
    if styled:
        out['combined'] = evaluate(combined_refs, combined_preds)
        out['style'] = {'conditional_on_correct_nonspace_characters': True,
            'characters': sum(confusion.values()),
            'accuracy': sum(n for (a,b),n in confusion.items() if a==b)/max(1,sum(confusion.values())),
            'confusion': {a+'->'+b: n for (a,b),n in confusion.items()}}
        out['style']['boundaries_on_correct_characters'] = boundaries
        out['style']['short_runs_up_to_three_nonspace_characters'] = short_runs
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', type=Path, default=Path('.cache/ocr-model/retraining-v2b'))
    p.add_argument('--predictions', type=Path, required=True)
    p.add_argument('--styled', action='store_true')
    p.add_argument('--split', choices=['dev','test'], default='dev')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    records = [json.loads(l) for l in (args.dataset/'records.jsonl').read_text().splitlines()]
    records = [r for r in records if r['split'] == args.split]
    outputs = [(args.predictions/(Path(r['image']).stem+'.pred.txt')).read_text().rstrip('\r\n') for r in records]
    result = {'split':args.split, 'styled':args.styled, 'all':score(records,outputs,args.styled)}
    for name, selected in [('old_range', lambda n:n<=150), ('new_range', lambda n:n>150)]:
        pairs = [(r,o) for r,o in zip(records,outputs) if selected(int(r['page_id'][-4:]))]
        result[name] = score([r for r,o in pairs],[o for r,o in pairs],args.styled)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v['text']['character_error_rate'] for k,v in result.items() if isinstance(v,dict) and 'text' in v}))


if __name__ == '__main__':
    main()
