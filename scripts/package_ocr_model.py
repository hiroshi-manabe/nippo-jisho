#!/usr/bin/env python3
"""Copy a selected checkpoint into a self-contained, hashed local model package."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def checkpoint_hashes(run):
    files = [run/'best.ckpt.json', *sorted((run/'best.ckpt').rglob('*'))]
    return {str(f.relative_to(run)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in files if f.is_file()}


def verify_selection(selection, run, mode, dataset):
    """Do not package a checkpoint different from the pre-test decision."""
    selected = selection['models'][mode]
    if selected['checkpoint_sha256'] != checkpoint_hashes(run):
        raise ValueError('Checkpoint differs from frozen selection')
    fingerprint = hashlib.sha256((dataset/'records.jsonl').read_bytes()).hexdigest()
    if selection['training_records_sha256'] != fingerprint:
        raise ValueError('Dataset differs from frozen selection')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--name',required=True)
    p.add_argument('--mode',choices=['plain','styled'],required=True)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True)
    p.add_argument('--upstream-repository',type=Path,
        default=ROOT/'.cache/ocr-model/calamari_models_experimental')
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
    experiment=json.loads((args.run/'experiment.json').read_text())
    if experiment['status']!='dev_ready' or experiment['mode']!=args.mode:
        raise ValueError('A completed run with matching mode is required')
    dataset=Path(experiment['dataset'])
    if not dataset.is_absolute():
        dataset=ROOT/dataset
    verify_selection(selection, args.run, args.mode, dataset)
    for source in (dataset/'summary.json',dataset/'audit.json',args.upstream_repository/'LICENSE'):
        if not source.is_file():
            raise FileNotFoundError(source)
    upstream_commit=subprocess.check_output(
        ['git','-C',str(args.upstream_repository),'rev-parse','HEAD'],text=True).strip()
    args.output.mkdir(parents=True)
    shutil.copytree(checkpoint,args.output/'best.ckpt')
    shutil.copy2(args.run/'best.ckpt.json',args.output/'best.ckpt.json')
    shutil.copy2(args.evaluation,args.output/'test-evaluation.json')
    shutil.copy2(args.selection,args.output/'selection.json')
    for name in ('experiment.json','dev-evaluation.json'):
        if (args.run/name).is_file():
            shutil.copy2(args.run/name,args.output/name)
    shutil.copy2(dataset/'summary.json',args.output/'dataset-summary.json')
    shutil.copy2(dataset/'audit.json',args.output/'dataset-audit.json')
    shutil.copy2(args.upstream_repository/'LICENSE',args.output/'UPSTREAM-LICENSE.txt')
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
        'upstream':{'repository':'https://github.com/Calamari-OCR/calamari_models_experimental',
            'commit':upstream_commit,'initial_checkpoint':'deep3_antiqua-15-16-cent/0.ckpt',
            'license_notice':'UPSTREAM-LICENSE.txt'},
        'training_records_sha256':hashlib.sha256((dataset/'records.jsonl').read_bytes()).hexdigest(),
        'selection':selection}
    (args.output/'model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
    print(args.output)


if __name__=='__main__':
    main()
