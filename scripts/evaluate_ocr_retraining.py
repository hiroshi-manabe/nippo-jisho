#!/usr/bin/env python3
"""Evaluate diplomatic text and style independently from Calamari predictions."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from build_ocr_retraining_dataset import decode
from evaluate_line_ocr_predictions import evaluate, edit_alignment


def dual_style_words(records):
    """Training-only vocabulary for testing style independent of word identity."""
    found = {}
    for r in records:
        for match in re.finditer(r'[^\W\d_]+\.?', r['text'], re.UNICODE):
            word=match.group().casefold()
            styles=set(r['styles'][match.start():match.end()])
            if len(word.rstrip('.'))>=2 and len(styles)==1:
                found.setdefault(word,set()).update(styles)
    return {w for w,s in found.items() if len(s)==2}


def score(records, outputs, styled, ambiguous_words=frozenset()):
    if len(records) != len(outputs):
        raise ValueError('Reference/prediction count mismatch')
    predictions, combined_refs, combined_preds = [], [], []
    confusion = Counter()
    letter_confusion = Counter()
    boundaries = Counter()
    short_runs = Counter()
    ambiguous_tokens = Counter()
    glyphs = {c: Counter() for c in ('ß', 'ſ', 's', 'ô', 'ǒ', 'ũ', 'ã')}
    double_s = {c: Counter() for c in ('ß', 'ſſ', 'ſs')}
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
        aligned_positions = {}
        alignment=edit_alignment(r['text'], text)
        for left, right in alignment:
            if left in glyphs:
                glyphs[left]['reference'] += 1
                glyphs[left]['exact'] += left == right
            if styles is not None and left and left == right and not left.isspace():
                confusion[(r['styles'][ri], styles[hi])] += 1
                if left.isalpha():
                    letter_confusion[(r['styles'][ri], styles[hi])] += 1
                aligned_styles[ri] = styles[hi]
                aligned_positions[ri] = hi
                wrong_style += r['styles'][ri] != styles[hi]
            ri += bool(left)
            hi += bool(right)
        for match in re.finditer('ß|ſſ|ſs', r['text']):
            position=0
            span=[]
            for left,right in alignment:
                if match.start()<=position<match.end():
                    span.append(right)
                position+=bool(left)
            observed=''.join(span)
            feature=double_s[match.group()]
            feature['reference']+=1
            feature['exact']+=observed==match.group()
            if observed!=match.group():
                feature['as_'+observed if observed in double_s else 'missing_or_other']+=1
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
                    exact = all(aligned_styles.get(i) == r['styles'][i] for i in group)
                    if exact:
                        segment = text[aligned_positions[group[0]]:aligned_positions[group[-1]]+1]
                        exact = ''.join(c for c in segment if not c.isspace()) == ''.join(r['text'][i] for i in group)
                    short_runs['exact_text_and_style'] += exact
            for match in re.finditer(r'[^\W\d_]+\.?', r['text'], re.UNICODE):
                if match.group().casefold() not in ambiguous_words:
                    continue
                group=list(range(match.start(),match.end()))
                ambiguous_tokens['reference'] += 1
                exact=all(i in aligned_positions for i in group)
                if exact:
                    exact=text[aligned_positions[group[0]]:aligned_positions[group[-1]]+1]==match.group()
                ambiguous_tokens['text_exact'] += exact
                ambiguous_tokens['text_and_style_exact'] += exact and all(aligned_styles.get(i)==r['styles'][i] for i in group)
        if text != r['text'] or wrong_style:
            examples.append({'id': r['id'], 'reference': r['text'], 'prediction': text,
                             'wrong_style_on_correct_characters': wrong_style})
    out = {'text': evaluate(records, predictions), 'glyphs': glyphs, 'double_s':double_s,
           'examples': examples[:80]}
    if styled:
        out['combined'] = evaluate(combined_refs, combined_preds)
        out['style'] = {'conditional_on_correct_nonspace_characters': True,
            'characters': sum(confusion.values()),
            'accuracy': sum(n for (a,b),n in confusion.items() if a==b)/max(1,sum(confusion.values())),
            'confusion': {a+'->'+b: n for (a,b),n in confusion.items()}}
        out['style']['boundaries_on_correct_characters'] = boundaries
        out['style']['short_runs_up_to_three_nonspace_characters'] = short_runs
        out['style']['words_observed_in_both_styles_in_training'] = ambiguous_tokens
        out['style']['letters_only'] = {
            'characters':sum(letter_confusion.values()),
            'accuracy':sum(n for (a,b),n in letter_confusion.items() if a==b)/max(1,sum(letter_confusion.values())),
            'confusion':{a+'->'+b:n for (a,b),n in letter_confusion.items()}}
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', type=Path, default=Path('.cache/ocr-model/retraining-v2d'))
    p.add_argument('--predictions', type=Path, required=True)
    p.add_argument('--styled', action='store_true')
    p.add_argument('--split', choices=['dev','test'], default='dev')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    records = [json.loads(l) for l in (args.dataset/'records.jsonl').read_text().splitlines()]
    ambiguous_words=dual_style_words([r for r in records if r['split']=='train'])
    records = [r for r in records if r['split'] == args.split]
    outputs = [(args.predictions/(Path(r['image']).stem+'.pred.txt')).read_text().rstrip('\r\n') for r in records]
    result = {'split':args.split, 'styled':args.styled,
              'dual_style_training_words':sorted(ambiguous_words),
              'all':score(records,outputs,args.styled,ambiguous_words)}
    for name, selected in [('old_range', lambda n:n<=150), ('new_range', lambda n:n>150)]:
        pairs = [(r,o) for r,o in zip(records,outputs) if selected(int(r['page_id'][-4:]))]
        result[name] = score([r for r,o in pairs],[o for r,o in pairs],args.styled,ambiguous_words)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v['text']['character_error_rate'] for k,v in result.items() if isinstance(v,dict) and 'text' in v}))


if __name__ == '__main__':
    main()
