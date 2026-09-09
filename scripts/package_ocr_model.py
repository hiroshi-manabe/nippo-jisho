#!/usr/bin/env python3
"""Copy a selected checkpoint into a self-contained, hashed local model package."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--name',required=True)
    p.add_argument('--mode',choices=['plain','styled'],required=True)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise ValueError('Package destination already exists')
    checkpoint=args.run/'best.ckpt'
    if not (checkpoint/'saved_model.pb').is_file():
        raise ValueError('A complete SavedModel checkpoint is required')
    evaluation=json.loads(args.evaluation.read_text())
    if evaluation['split']!='test':
        raise ValueError('Final test evaluation is required')
    if evaluation['styled'] != (args.mode == 'styled'):
        raise ValueError('Evaluation mode does not match package mode')
    selection=json.loads(args.selection.read_text())
    args.output.mkdir(parents=True)
    shutil.copytree(checkpoint,args.output/'best.ckpt')
    shutil.copy2(args.run/'best.ckpt.json',args.output/'best.ckpt.json')
    shutil.copy2(args.evaluation,args.output/'test-evaluation.json')
    shutil.copy2(args.selection,args.output/'selection.json')
    for name in ('experiment.json','dev-evaluation.json'):
        if (args.run/name).is_file():
            shutil.copy2(args.run/name,args.output/name)
    files={str(f.relative_to(args.output)):hashlib.sha256(f.read_bytes()).hexdigest()
           for f in sorted(args.output.rglob('*')) if f.is_file()}
    model={'format':'nippo-calamari-model-package','format_version':1,'name':args.name,
        'mode':args.mode,'checkpoint':'best.ckpt','source_run':str(args.run.resolve()),
        'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'calamari_version':'2.3.1','tensorflow_version':'2.15.1',
        'input':'isolated rectified lines; paper-white polygon exterior',
        'line_height':48,'max_width':4096,'normalization':'NFC',
        'style_encoding':'italic nonspace BMP character + U+F0000' if args.mode=='styled' else None,
        'whitespace_style':'unclassified','file_sha256':files,
        'selection':selection}
    (args.output/'model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
    print(args.output)


if __name__=='__main__':
    main()
