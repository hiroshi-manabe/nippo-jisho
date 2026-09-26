#!/usr/bin/env python3
"""One durable, serialized discovery/application cycle; scheduling is external."""
import argparse
import fcntl
import hashlib
import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'exports/review-inbox'
INCOMING = ROOT / 'exports/external-review/incoming'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True)


def discover_results(incoming, ledger, now):
    jobs = []
    for path in sorted(incoming.glob('*.zip')):
        stat = path.stat()
        signature = [stat.st_size, stat.st_mtime_ns]
        previous = ledger['observed'].get(str(path))
        ledger['observed'][str(path)] = {'signature': signature, 'since': now if not previous or previous['signature'] != signature else previous['since']}
        if not previous or previous['signature'] != signature or now - previous['since'] < 60:
            continue
        key = 'zip:' + digest(path.read_bytes())
        jobs.append((key, {'kind': 'external', 'path': str(path)}))
    return jobs


def find_input(result, directory):
    with zipfile.ZipFile(result) as z:
        info = json.loads(z.read('result.json'))
    for path in sorted(directory.rglob('*-input.zip')):
        if 'backups' in path.parts:
            continue
        with zipfile.ZipFile(path) as z:
            manifest = z.read('manifest.json')
        if digest(manifest) == info['input_manifest_sha256']:
            return path
    raise ValueError('No matching input package found')


def needs_human(value):
    if isinstance(value, dict):
        if any(value.get(k) for k in ('message', 'comment', 'second_opinion')):
            return True
        return any(needs_human(v) for v in value.values())
    return isinstance(value, list) and any(needs_human(v) for v in value)


def recover_closures(ledger, open_numbers, reports):
    """Retry only the remote tail of committed Issues, not their corrections."""
    from process_correction_issue import resume_publication

    closures = ledger.setdefault('closures', {})
    def was_failed_application(number):
        return any(
            job.get('kind') == 'issue' and job.get('number') == number
            and job.get('status') == 'failed'
            for job in ledger.get('jobs', {}).values()
        )

    def mark_recovered(number):
        for job in ledger.get('jobs', {}).values():
            if job.get('kind') == 'issue' and job.get('number') == number and job.get('status') == 'failed':
                job.update(status='succeeded', recovered_after_closure=True)

    for path in sorted(reports.glob('issue-*.json')):
        try:
            report = json.loads(path.read_text())
            number = int(path.stem.removeprefix('issue-'))
            if report.get('status') == 'closed' and number in open_numbers and was_failed_application(number):
                # A prior, incomplete closure must not hide an open Issue.
                report['status'] = 'publication_pending'
                save(path, report)
            if report.get('status') != 'publication_pending':
                continue
            record = closures.setdefault(str(number), {})
            record['commit'] = report.get('commit')
            if number not in open_numbers:
                # A list response may omit an Issue transiently. Confirm its
                # actual state before considering publication complete.
                try:
                    issue = json.loads(run('gh', 'api', f'repos/hiroshi-manabe/nippo-jisho/issues/{number}'))
                    if issue['state'] != 'closed':
                        raise ValueError('Issue is still open')
                    report['status'] = 'closed'
                    save(path, report)
                    record.update(status='closed', reason='Already closed on GitHub')
                    mark_recovered(number)
                except Exception as exc:
                    record.update(status='retry_pending', last_error=str(exc))
            elif not report.get('pushed'):
                record.update(status='manual_publication_check', reason='Push was not confirmed')
            else:
                record['attempts'] = record.get('attempts', 0) + 1
                record['last_attempted_at'] = time.time()
                try:
                    resume_publication(number)
                    record.update(status='closed', reason='Deployment verified and Issue closed')
                    record.pop('last_error', None)
                    mark_recovered(number)
                except Exception as exc:
                    record.update(status='retry_pending', last_error=str(exc))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            ledger.setdefault('closure_discovery_errors', {})[str(path)] = str(exc)


def cycle():
    from process_correction_issue import extract_payload
    STATE.mkdir(parents=True, exist_ok=True)
    INCOMING.mkdir(parents=True, exist_ok=True)
    with (STATE / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another application cycle is active.')
            return
        path = STATE / 'ledger.json'
        ledger = json.loads(path.read_text()) if path.exists() else {'jobs': {}, 'observed': {}}
        # Clear a resolved pause even if every discovered item was already
        # attempted. This does not retry any failed job.
        if (not run('git', 'status', '--porcelain', '--untracked-files=no').strip()
                and run('git', 'rev-list', '--count', '@{upstream}..HEAD').strip() == '0'):
            ledger.pop('paused', None)
        # A crash after recording an attempt never silently repeats external writes.
        for job in ledger['jobs'].values():
            if job['status'] == 'running':
                job['status'] = 'interrupted_needs_manual_check'
        jobs = discover_results(INCOMING, ledger, time.time())
        open_numbers = None
        try:
            issues = json.loads(run('gh', 'api', '--paginate', '--slurp', 'repos/hiroshi-manabe/nippo-jisho/issues?state=open&sort=created&direction=asc&per_page=100'))
            open_issues = [i for page in issues for i in page if 'pull_request' not in i]
            open_numbers = {issue['number'] for issue in open_issues}
            for issue in open_issues:
                # Our own comments/status edits do not create a new attempt.
                identity = digest((issue['title'] + '\n' + (issue['body'] or '')).encode())
                jobs.insert(0, (f'issue:{issue["number"]}:{identity}', {'kind': 'issue', 'number': issue['number'], 'body': issue['body'] or ''}))
            ledger.pop('discovery_error', None)
        except Exception as exc:
            ledger['discovery_error'] = str(exc)
        if open_numbers is not None:
            recover_closures(ledger, open_numbers, ROOT / 'build/correction-issues')
        jobs.sort(key=lambda item: (item[1]['kind'] != 'issue', item[1].get('number', 0), item[0]))
        # Overlay jobs are appended only after discovery of higher-priority work.
        # At most one page per cycle, and never retry an unchanged failed input.
        from alignment_queue import discover as discover_alignments
        overlay_jobs=discover_alignments()
        jobs.extend(next(([job] for job in overlay_jobs if job[0] not in ledger['jobs']), []))
        save(path, ledger)
        for key, spec in jobs:
            if key in ledger['jobs']:
                continue
            if spec['kind']=='alignment' and key not in dict(discover_alignments()):
                continue  # Higher-priority applications changed its input.
            if run('git', 'status', '--porcelain', '--untracked-files=no').strip():
                ledger['paused'] = 'Tracked changes exist; applications paused, discovery continues.'
                break
            # A clean checkout can still contain an unpushed failed publication.
            if run('git', 'rev-list', '--count', '@{upstream}..HEAD').strip() != '0':
                ledger['paused'] = 'Unpushed commits exist; manual publication check required.'
                break
            ledger.pop('paused', None)
            record = {k: v for k, v in spec.items() if k != 'body'}
            record.update(status='running', attempted_at=time.time())
            ledger['jobs'][key] = record
            save(path, ledger)
            log = STATE / (digest(key.encode()) + '.log')
            record['log'] = str(log)
            overlay_path=ROOT/f'site/assets/alignment/{spec["page"]}.json' if spec['kind']=='alignment' else None
            previous_overlay=overlay_path.read_bytes() if overlay_path and overlay_path.exists() else None
            original_head=run('git','rev-parse','HEAD').strip()
            try:
                if spec['kind'] == 'issue':
                    payload = extract_payload(spec['body'])
                    command = [sys.executable, 'scripts/process_correction_issue.py', 'process', str(spec['number'])]
                elif spec['kind'] == 'external':
                    source = find_input(spec['path'], ROOT / 'exports/external-review')
                    command = [sys.executable, 'scripts/external_ai_review.py', 'apply', str(source), spec['path'], '--publish']
                else:
                    command = ['arch','-arm64',str(ROOT/'.cache/ocr-model/venv-calamari-arm64/bin/python'), 'scripts/generate_page_alignment.py', spec['page'], spec['fingerprint']]
                with log.open('w') as output:
                    result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
                record['status'] = 'succeeded' if result.returncode == 0 else 'awaiting_human' if result.returncode == 3 else 'failed'
                record['returncode'] = result.returncode
                if result.returncode == 0 and spec['kind']=='alignment':
                    with log.open('a') as output:
                        subprocess.run([sys.executable,'scripts/build_public_review.py'],cwd=ROOT,check=True,stdout=output,stderr=subprocess.STDOUT)
                    asset=f'site/assets/alignment/{spec["page"]}.json'
                    run('git','add','--',asset)
                    run('git','commit','-m',f'Generate aligned baseline display for {spec["page"]}','--',asset)
                    run('git','push')
                if result.returncode == 0 and spec['kind'] == 'external':
                    from process_correction_issue import wait_for_deployment
                    # The importer deliberately does not own deployment polling.
                    record['deployment'] = wait_for_deployment(run('git', 'rev-parse', 'HEAD').strip(), 'hiroshi-manabe/nippo-jisho', ROOT)
            except Exception as exc:
                record.update(status='failed', reason=str(exc))
            finally:
                if overlay_path and record['status']!='succeeded' and run('git','rev-parse','HEAD').strip()==original_head:
                    if previous_overlay is None:
                        overlay_path.unlink(missing_ok=True)
                    else:
                        overlay_path.write_bytes(previous_overlay)
                    subprocess.run(['git','restore','--staged','--',str(overlay_path.relative_to(ROOT))],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                save(path, ledger)
        save(path, ledger)
        summary = {k: v['status'] for k, v in ledger['jobs'].items()}
        questions_path = ROOT / 'pilot/human-review/pending-questions.json'
        questions = json.loads(questions_path.read_text())['pages'] if questions_path.exists() else {}
        pending = {pid: len([q for q in items if q.get('status') == 'pending']) for pid, items in questions.items()}
        pending = {pid: count for pid, count in pending.items() if count}
        save(STATE / 'status.json', {'jobs': summary, 'closures': ledger.get('closures', {}), 'pending_questions': pending, 'paused': ledger.get('paused'), 'discovery_error': ledger.get('discovery_error')})
        print(json.dumps({'jobs': summary, 'paused': ledger.get('paused'), 'discovery_error': ledger.get('discovery_error')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    cycle()
