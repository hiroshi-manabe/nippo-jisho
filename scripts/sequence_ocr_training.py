#!/usr/bin/env python3
"""Temporarily pause an owned OCR trainer until another owned run exits.

Keeps optimizer state in the live process. PID identity is checked before any
signal; no completed or missing process is restarted.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def identity(pid):
    result=subprocess.run(['ps','-p',str(pid),'-o','lstart=,command='],text=True,capture_output=True)
    return result.stdout.strip() if result.returncode==0 else None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wait-pid',type=int,required=True)
    p.add_argument('--pause-pid',type=int,required=True)
    p.add_argument('--status',type=Path,required=True)
    args=p.parse_args()
    waited,paused=identity(args.wait_pid),identity(args.pause_pid)
    if not waited or 'run_ocr_retraining.py' not in waited:
        raise ValueError('Wait target is not a live retraining runner')
    if not paused or 'train_styled_calamari.py' not in paused:
        raise ValueError('Pause target is not a live styled trainer')
    status={'wait_pid':args.wait_pid,'pause_pid':args.pause_pid,'wait_identity':waited,
            'pause_identity':paused,'started':time.time(),'status':'paused_waiting_for_plain_run'}
    def record():
        args.status.write_text(json.dumps(status,indent=2)+'\n')
    os.kill(args.pause_pid,signal.SIGSTOP)
    signal.signal(signal.SIGTERM,lambda signum,frame:sys.exit(128+signum))
    record()
    print(f'Paused styled trainer {args.pause_pid}; waiting for runner {args.wait_pid}',flush=True)
    try:
        while identity(args.wait_pid)==waited:
            if identity(args.pause_pid)!=paused:
                raise RuntimeError('Paused trainer disappeared; no automatic restart')
            time.sleep(30)
    finally:
        if identity(args.pause_pid)==paused:
            os.kill(args.pause_pid,signal.SIGCONT)
            status.update(status='resumed',resumed=time.time())
            record()
            print(f'Resumed styled trainer {args.pause_pid}',flush=True)


if __name__=='__main__':
    main()
