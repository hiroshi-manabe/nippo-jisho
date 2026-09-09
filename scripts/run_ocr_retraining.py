#!/usr/bin/env python3
"""Run matched plain/style experiments; never evaluate the final test implicitly."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', type=Path, default=ROOT / '.cache/ocr-model/retraining-v2b')
    p.add_argument('--mode', choices=['plain', 'styled'], required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--epochs', type=int, default=12)
    p.add_argument('--lr', type=float, default=.0001)
    p.add_argument('--seed', type=int, default=1603)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Choose a fresh run directory; existing runs are never overwritten')
    records = args.dataset / 'records.jsonl'
    if not records.exists():
        raise ValueError('Dataset has not finished building')
    args.output.mkdir(parents=True)
    binary = ROOT / '.cache/ocr-model/venv-calamari-arm64/bin'
    checkpoint = ROOT / '.cache/ocr-model/runs/calamari-antiqua-book-codec-v1/best.ckpt'
    command = ['arch', '-arm64', str(binary / 'calamari-train'),
        '--trainer.output_dir', str(args.output), '--warmstart.model', str(checkpoint),
        '--network', 'deep3', '--train.images', str(args.dataset / args.mode / 'train/*.png'),
        '--val.images', str(args.dataset / args.mode / 'dev/*.png'),
        '--trainer.epochs', str(args.epochs), '--early_stopping.n_to_go', '3',
        '--trainer.random_seed', str(args.seed), '--trainer.progress_bar_mode', '2',
        '--learning_rate.lr', str(args.lr), '--train.batch_size', '32', '--val.batch_size', '32',
        '--train.num_processes', '2', '--val.num_processes', '2',
        '--data.line_height', '48', '--codec.keep_loaded', 'false']
    meta = {'command': command, 'started': time.time(), 'mode': args.mode,
        'dataset': str(args.dataset), 'final_test_used': False, 'status': 'training'}
    def record():
        (args.output / 'experiment.json').write_text(json.dumps(meta, indent=2)+'\n')
    record()
    env = {**os.environ, 'CUDA_VISIBLE_DEVICES': '', 'PYTHONUNBUFFERED': '1'}
    with (args.output / 'console.log').open('w') as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        meta.update(status='failed', returncode=result.returncode)
        record()
        raise SystemExit(result.returncode)
    meta['status'] = 'predicting_dev'
    record()
    command = ['arch', '-arm64', str(binary / 'calamari-predict'), '--checkpoint',
        str(args.output / 'best.ckpt'), '--data.images', str(args.dataset / args.mode / 'dev/*.png'),
        '--output_dir', str(args.output / 'dev-predictions'), '--verbose', 'false',
        '--pipeline.batch_size', '32', '--pipeline.num_processes', '2']
    with (args.output / 'predict.log').open('w') as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    if not result.returncode:
        command = [sys.executable, str(ROOT / 'scripts/evaluate_ocr_retraining.py'),
            '--dataset', str(args.dataset), '--predictions', str(args.output / 'dev-predictions'),
            '--output', str(args.output / 'dev-evaluation.json')]
        if args.mode == 'styled':
            command.append('--styled')
        result = subprocess.run(command, cwd=ROOT)
    meta.update(status='dev_ready' if not result.returncode else 'prediction_failed', finished=time.time())
    record()
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
