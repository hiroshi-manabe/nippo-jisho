#!/usr/bin/env python3
"""Recognize isolated line images using a packaged Nippo Calamari model.

Input lines must already be segmented/rectified. This program does not guess
page layout, edit canonical files, or turn model predictions into human review.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unicodedata

from PIL import Image
from build_clean_ocr_pairs import normalized_line
from build_ocr_retraining_dataset import decode

ROOT = Path(__file__).resolve().parents[1]


def decode_prediction(raw, styled):
    if not styled:
        return {'text': unicodedata.normalize('NFC', raw)}
    text, styles = decode(raw)
    # Whitespace is deliberately unclassified. Attach it to the preceding
    # visible run (or the following one when leading), without claiming that
    # it was visually classified by the model.
    runs = []
    for i, char in enumerate(text):
        style = styles[i]
        if char.isspace():
            style = runs[-1]['typeface'] if runs else next(
                (styles[j] for j in range(i+1,len(text)) if not text[j].isspace()), 'roman')
        if runs and runs[-1]['typeface'] == style:
            runs[-1]['text'] += char
        else:
            runs.append({'typeface': style, 'text': char})
    # Normalize within a run, preserving attachment of combining characters.
    for run in runs:
        run['text'] = unicodedata.normalize('NFC', run['text'])
    return {'text': ''.join(run['text'] for run in runs), 'runs': runs,
            'whitespace_style': 'attached_for_serialization_not_classified'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('images', nargs='+', type=Path)
    p.add_argument('--model', type=Path, required=True, help='Packaged directory containing model.json')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--prepared', action='store_true', help='Inputs already have the training preprocessing')
    p.add_argument('--calamari', type=Path, default=ROOT / '.cache/ocr-model/venv-calamari-arm64/bin/calamari-predict')
    args = p.parse_args()
    model = json.loads((args.model/'model.json').read_text())
    if model['format'] != 'nippo-calamari-model-package':
        raise ValueError('Unrecognized package')
    if model['mode'] not in ('plain', 'styled'):
        raise ValueError('Unrecognized model mode')
    for path in args.images:
        if not path.is_file():
            raise FileNotFoundError(path)
    with tempfile.TemporaryDirectory(prefix='nippo-recognize-') as temporary:
        work = Path(temporary)
        output = work/'predictions'
        output.mkdir()
        for i,path in enumerate(args.images):
            destination = work/f'line-{i:06d}.png'
            with Image.open(path) as image:
                if args.prepared:
                    image.save(destination)
                else:
                    normalized_line(image,height=48,max_width=4096).save(destination)
        command = [str(args.calamari), '--checkpoint', str((args.model/model['checkpoint']).resolve()),
            '--data.images',str(work/'line-*.png'), '--output_dir',str(output),
            '--verbose','false','--pipeline.batch_size','32','--pipeline.num_processes','2']
        if 'arm64' in str(args.calamari) and os.uname().sysname=='Darwin':
            command = ['arch','-arm64',*command]
        log_path = work/'predict.log'
        with log_path.open('w') as log:
            result = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,
                                    env={**os.environ,'CUDA_VISIBLE_DEVICES':''})
        if result.returncode:
            raise RuntimeError(log_path.read_text()[-8000:])
        records = []
        for i,path in enumerate(args.images):
            raw = (output/f'line-{i:06d}.pred.txt').read_text().rstrip('\r\n')
            records.append({'image':str(path.resolve()), **decode_prediction(raw,model['mode']=='styled')})
    document = {'format':'nippo-calamari-line-predictions','model':model['name'],
        'mode':model['mode'],'review_status':'machine-provisional','lines':records}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
    print(f'Wrote {len(records)} line predictions to {args.output}')


if __name__=='__main__':
    main()
