"""Compare derived kana coverage over Roman body text; not an accuracy score."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import types

from kana_reading import transliterate_token, reading_tokens


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=Path('build/human-review/corpus.json'))
    parser.add_argument('--last-leaf', type=int, default=180)
    parser.add_argument('--baseline-ref', required=True)
    parser.add_argument('--output', type=Path, default=Path('build/kana-coverage.json'))
    args = parser.parse_args()
    baseline = types.ModuleType('baseline_kana')
    exec(subprocess.check_output(['git', 'show', f'{args.baseline_ref}:scripts/kana_reading.py'], text=True), baseline.__dict__)
    counts = Counter()
    changes, failures = [], {}
    pages = set()
    for page in json.loads(args.corpus.read_text())['pages']:
        if page['leaf'] > args.last_leaf:
            continue
        for zone in page['zones']:
            if zone['kind'] != 'column':
                continue
            for line in zone['lines']:
                for run in line['runs']:
                    if run['typeface'] != 'roman':
                        continue
                    for phrase in re.split(r'[.¶]+', run['text']):
                        for token in reading_tokens(phrase):
                            pages.add(page['view'])
                            old, new = baseline.transliterate_token(token), transliterate_token(token)
                            counts['tokens'] += 1
                            counts['before_converted'] += old is not None
                            counts['after_converted'] += new is not None
                            ref = f"{page['view']}/{line['id']}"
                            if old != new:
                                changes.append(dict(reference=ref, token=token, before=old, after=new))
                            if new is None:
                                item = failures.setdefault(token, dict(token=token, count=0, examples=[]))
                                item['count'] += 1
                                if ref not in item['examples'] and len(item['examples']) < 3:
                                    item['examples'].append(ref)
    report = dict(scope=f'Roman body runs through f{args.last_leaf}; labels filtered; includes Portuguese and fragments',
                  baseline_ref=args.baseline_ref, pages=len(pages), counts=dict(counts),
                  changed=changes, unconverted=sorted(failures.values(), key=lambda x: -x['count']))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(pages=len(pages), **counts), ensure_ascii=False))
    print(f'Changed occurrences: {len(changes)}; report: {args.output}')


if __name__ == '__main__':
    main()
