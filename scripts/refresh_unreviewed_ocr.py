#!/usr/bin/env python3
"""Resume-safe v2 OCR refresh: plan/backup, extract, recognize, then apply.

Run prepare in the native Kraken environment. Prediction uses the packaged
styled Calamari model. No reviewed page or UI rectangle is overwritten.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageOps
from audit_ocr_layout_geometry import read_evidence, column_candidates
from align_page_geometry_ocr_first import normalized_distance
from build_ocr_retraining_dataset import full_text_candidates, styled_text
from compile_level1_markdown import export_markdown, parse_markdown
from ocr_line_images import prepare_rectified_line
from recognize_nippo_calamari import decode_prediction

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT/'.cache/ocr-model/page-refresh-v2'
MODEL = ROOT/'models/local/nippo-calamari-v2-styled'
LEVEL = ROOT/'pilot/format-v1-trial/level1'
SOURCE = ROOT/'pilot/format-v1-trial/level1-source'
REGISTRY = ROOT/'pilot/human-review/ocr-refresh-v2.json'


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    temp.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_pages():
    reasons = {}
    for page in load(ROOT/'pilot/human-review/correction-history.json')['pages']:
        if page.get('issues_applied') or page.get('issues'):
            reasons[page['id']] = 'human_correction_history'
    for page in load(ROOT/'pilot/human-review/review-status.json')['pages']:
        if any(u.get('status') not in ('pending',None) for u in page['units'].values()):
            reasons[page['id']] = 'human_review_unit_touched'
    # These reference artifacts preserve early conversational corrections not
    # represented by the later Issue counter. Preserve them conservatively.
    reference=ROOT/'pilot/ocr-bootstrap/reference-f0248-f0250'
    for path in reference.rglob('bnf-f*.json'):
        if path.stem.startswith('bnf-f'):
            reasons[path.stem] = 'early_human_trial_reference'
    return reasons


def page_sources():
    found = {}
    for directory in [ROOT/'pilot/ocr-bootstrap/f0238-f0247',
                      ROOT/'pilot/ocr-bootstrap/f0251-f0642/pages']:
        for path in directory.glob('bnf-f*.json'):
            found[path.stem] = path
    for path in LEVEL.glob('bnf-f*.json'):
        found[path.stem] = path
    return found


def body(page):
    return {l['id']:l for z in page['zones'] if z['kind']=='column' for l in z['lines']}


def text(line):
    return ''.join(r['text'] for r in line['runs']).strip()


def visible_style(line):
    value, styles=styled_text(line['runs'])
    return [(c,s) for c,s in zip(value,styles) if not c.isspace()]


def annotate_package(obj, report):
    if 'page' in obj:
        obj.setdefault('audit',{})['recognition_refresh']={
            'model':'nippo-calamari-v2-styled','prior_recognition_annotations':'historical_before_v2_refresh',
            'recognized_lines':report['recognized_lines'],'retained_lines':report['retained_lines'],
            'structural_assessment':'unchanged_not_revalidated_by_recognition'}


def plan(work):
    if (work/'plan.json').exists():
        return load(work/'plan.json')
    excluded=protected_pages(); items=[]; geometries={p['id']:p for p in load(ROOT/'pilot/human-review/line-geometry.json')['pages']}
    for pid,path in sorted(page_sources().items()):
        obj=load(path); page=obj.get('page',obj)
        if page['review']['status']=='human_checked':excluded[pid]='human_checked'
        if pid in excluded:continue
        if not (ROOT/'pilot/ocr-layout-evidence/v1/pages'/f'{pid}.json.gz').exists():
            excluded[pid]='no_preserved_ocr_layout';continue
        if not body(page):excluded[pid]='no_body_columns';continue
        geometry=obj.get('geometry',geometries.get(pid))
        if not geometry:excluded[pid]='no_stable_geometry';continue
        backup=work/'backup'/path.relative_to(ROOT)
        backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup)
        md=SOURCE/f'{pid}.md'
        if path.parent==LEVEL and md.exists():
            dst=work/'backup'/md.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(md,dst)
        save(work/'geometry'/f'{pid}.json',geometry)
        items.append({'id':pid,'path':str(path.relative_to(ROOT)),'source_sha256':sha(path),
                      'markdown_sha256':sha(md) if path.parent==LEVEL else None,
                      'geometry_sha256':sha(work/'geometry'/f'{pid}.json')})
    manifest={'format':'nippo-ocr-refresh-plan','created_at':datetime.now(timezone.utc).isoformat(),
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'model_manifest_sha256':sha(MODEL/'model.json'),'pages':items,'excluded':excluded}
    save(work/'plan.json',manifest);return manifest


def associate(refs,candidates,geometry):
    """Conservative position-assisted association; no forced missing-row match."""
    selected=[]; rejected=[]; used=set();last_y=-1
    for ref in refs:
        line_id=ref['id']; runs=ref['runs']; g=geometry['lines'][line_id]
        if any(r.get('layout') or r.get('span_id') for r in runs) or len({r.get('placement','normal') for r in runs})>1:
            rejected.append({'line':line_id,'reason':'displaced_or_decorated_structure'});continue
        y=g['centre_y']; ranked=[]
        nearby=sorted(candidates,key=lambda c:abs(c['centre_y']-y))[:5]
        for c in nearby:
            distance=normalized_distance(text(ref),c['recognition'])
            if abs(c['centre_y']-y)>160:continue
            ranked.append((distance+.0005*abs(c['centre_y']-y),distance,c))
        ranked.sort(key=lambda x:x[0])
        reason=None
        if not ranked or ranked[0][1]>.35:reason='uncertain_row_correspondence'
        elif len(ranked)>1 and ranked[1][0]-ranked[0][0]<.08:reason='ambiguous_row_correspondence'
        elif ranked[0][2]['id'] in used or ranked[0][2]['centre_y']<=last_y:reason='duplicate_or_nonmonotonic_match'
        if reason:rejected.append({'line':line_id,'reason':reason});continue
        _,dist,c=ranked[0];used.add(c['id']);last_y=c['centre_y']
        selected.append((ref,c,dist))
    return selected,rejected


def prepare(item,work):
    from kraken.containers import BaselineLine, Segmentation
    from kraken.lib.segmentation import extract_polygons
    pid=item['id']; output=work/'prepared'/f'{pid}.json'
    if output.exists():return
    obj=load(work/'backup'/item['path']);page=obj.get('page',obj);lines=body(page)
    geometry=load(work/'geometry'/f'{pid}.json');evidence=read_evidence(pid,ROOT/'pilot/ocr-layout-evidence/v1')
    if sha(work/'geometry'/f'{pid}.json')!=item['geometry_sha256']:raise ValueError('Geometry snapshot changed')
    selected=[];rejected=[]
    for col,g in geometry['columns'].items():
        refs=[lines[k] for k in g['lines'] if k in lines]
        matched,failed=associate(refs,full_text_candidates(column_candidates(evidence,col),g),g)
        selected+=matched;rejected+=failed
    accounted={r['id'] for r,_,_ in selected}|{r['line'] for r in rejected}
    rejected += [{'line':k,'reason':'missing_geometry'} for k in lines if k not in accounted]
    scan=ROOT/'build/nippo-jisho-images/scans/native'/f'f{int(pid[-4:]):04d}.jpg'
    if sha(scan)!=page['source']['master_sha256']:raise ValueError(f'{pid}: scan checksum mismatch')
    seg=Segmentation(type='baselines',imagename=str(scan),text_direction='horizontal-lr',script_detection=False,
        lines=[BaselineLine(id=r['id'],baseline=c['baseline'],boundary=c['boundary']) for r,c,_ in selected])
    records=[];folder=work/'images'/pid;folder.mkdir(parents=True,exist_ok=True)
    with Image.open(scan) as original:
        for (image,line),(ref,candidate,distance) in zip(extract_polygons(ImageOps.invert(original.convert('RGB')),seg),selected):
            assert line.id==ref['id']
            prepared=prepare_rectified_line(ImageOps.invert(image))
            old=text(ref);required=len(old)+sum(a==b for a,b in zip(old,old[1:]))
            if prepared.width<4*required:
                rejected.append({'line':line.id,'reason':'crop_too_narrow'});continue
            dest=folder/f'{pid}__{line.id}.png';prepared.save(dest)
            records.append({'line':line.id,'candidate_id':candidate['id'],'image':str(dest.relative_to(work)),
                'image_sha256':sha(dest),'boundary':candidate['boundary'],'baseline':candidate['baseline'],
                'association_distance':distance})
    assert len(records)+len(rejected)==len(lines)
    save(output,{'id':pid,'records':records,'retained_lines':rejected,'body_lines':len(lines)})
    print(pid,'prepared',len(records),'retained',len(rejected),flush=True)


def predict(items,work):
    folder=work/'predict-input';folder.mkdir(exist_ok=True)
    output=work/'predictions';output.mkdir(exist_ok=True)
    # Temporary links only; already recognized outputs are never rerun.
    for f in folder.glob('*.png'):f.unlink()
    count=0
    for item in items:
        for r in load(work/'prepared'/f"{item['id']}.json")['records']:
            image=work/r['image']
            if (output/(image.stem+'.pred.txt')).exists():continue
            if sha(image)!=r['image_sha256']:raise ValueError('Prepared image changed')
            (folder/image.name).symlink_to(image.resolve());count+=1
    if not count:return
    binary=ROOT/'.cache/ocr-model/venv-calamari-arm64/bin/calamari-predict'
    command=['arch','-arm64',str(binary),'--checkpoint',str(MODEL/'best.ckpt'),
        '--data.images',str(folder/'*.png'),'--output_dir',str(output),'--verbose','false',
        '--pipeline.batch_size','32','--pipeline.num_processes','2']
    print('Recognizing',count,'lines',flush=True)
    with (work/'predict.log').open('a') as log:
        subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'CUDA_VISIBLE_DEVICES':''})


def apply(items,work,commit):
    registry=load(REGISTRY) if REGISTRY.exists() else {'format':'nippo-ocr-refresh-v2','pages':{}}
    protected=protected_pages()
    for item in items:
        pid=item['id'];path=ROOT/item['path']
        if pid in protected:raise ValueError(f'{pid}: now human reviewed; refusing refresh')
        if sha(path)!=item['source_sha256']:
            if registry['pages'].get(pid,{}).get('applied_sha256')==sha(path):
                if path.parent==LEVEL:
                    proposed_md=work/'proposed'/(SOURCE/f'{pid}.md').relative_to(ROOT)
                    if sha(SOURCE/f'{pid}.md')!=sha(proposed_md):raise ValueError('Applied Markdown changed')
                elif commit and 'recognition_refresh' not in load(path).get('audit',{}):
                    # Upgrade the initial pilot's provenance annotation only.
                    current=load(path);annotate_package(current,registry['pages'][pid]);save(path,current)
                    registry['pages'][pid]['applied_sha256']=sha(path);save(REGISTRY,registry)
                continue
            raise ValueError(f'{pid}: source changed since backup')
        obj=load(work/'backup'/item['path']);page=obj.get('page',obj);lines=body(page)
        prepared=load(work/'prepared'/f'{pid}.json');retained=deepcopy(prepared['retained_lines']);changed=[];recognized=[]
        for r in prepared['records']:
            raw=(work/'predictions'/(Path(r['image']).stem+'.pred.txt')).read_text().rstrip('\r\n')
            new=decode_prediction(raw,True);line=lines[r['line']]
            if not new['text'].strip() or normalized_distance(text(line),new['text'])>.4:
                retained.append({'line':r['line'],'reason':'new_reading_large_disagreement','proposed':new['text']});continue
            if any(ord(c)>=0xF0000 for c in new['text']):raise ValueError('Private labels leaked')
            runs=new['runs'];placement=line['runs'][0].get('placement')
            if placement:
                for run in runs:run['placement']=placement
            if runs!=line['runs']:changed.append(r['line'])
            line['runs']=runs;recognized.append(r['line'])
            if line.get('note') and not line['note'].startswith('[Possibly stale after OCR v2 refresh]'):
                line['note']='[Possibly stale after OCR v2 refresh] '+line['note']
        page['review']['origin']='calamari_v2_machine_provisional'
        page['review']['status']='visual_draft'
        report={'id':pid,'recognized_lines':len(recognized),'changed_lines':len(changed),
            'changed_ids':changed,'retained_lines':retained,'body_lines':len(lines),
            'model_manifest_sha256':sha(MODEL/'model.json'),'source_sha256':item['source_sha256']}
        assert len(recognized)+len(retained)==len(lines)
        annotate_package(obj,report)
        out=work/'proposed'/item['path'];save(out,obj)
        if path.parent==LEVEL:
            md=work/'proposed'/(SOURCE/f'{pid}.md').relative_to(ROOT)
            md.parent.mkdir(parents=True,exist_ok=True);md.write_text(export_markdown(page))
            # Canonical Markdown/JSON must be the same structure, including
            # placement, notes, and stable IDs. Whitespace-only runs normalize.
            parsed=parse_markdown(md)
            if {k:text(v) for k,v in body(parsed).items()}!={k:text(v) for k,v in lines.items()}:
                raise ValueError(f'{pid}: Markdown text round-trip failed')
            if any(visible_style(v)!=visible_style(body(parsed)[k]) for k,v in lines.items()):
                raise ValueError(f'{pid}: Markdown typeface round-trip failed')
            if export_markdown(parsed)!=md.read_text():
                raise ValueError(f'{pid}: Markdown export is not stable')
            save(out,parsed)
        save(work/'reports'/f'{pid}.json',report)
        if commit:
            if path.parent==LEVEL:
                target_md=SOURCE/f'{pid}.md'
                if sha(target_md)!=item['markdown_sha256']:raise ValueError('Markdown changed since backup')
                shutil.copy2(md,target_md)
            shutil.copy2(out,path)
            report['applied_sha256']=sha(path);report['applied_at']=datetime.now(timezone.utc).isoformat()
            registry['pages'][pid]=report;save(REGISTRY,registry)
        print(pid,'applied' if commit else 'proposed',len(changed),'changed;',len(retained),'retained',flush=True)


def verify(manifest, work):
    registry=load(REGISTRY)['pages']
    if set(registry)!={i['id'] for i in manifest['pages']}:raise ValueError('Incomplete application')
    changed_paths=subprocess.check_output(['git','diff',manifest['source_commit'],'--name-only'],cwd=ROOT,text=True).splitlines()
    protected=set(manifest['excluded'])
    if any(Path(p).stem in protected and p.startswith('pilot/') for p in changed_paths):
        raise ValueError('An excluded page has changed')
    geometries={p['id']:p for p in load(ROOT/'pilot/human-review/line-geometry.json')['pages']}
    totals=Counter();reasons=Counter()
    for item in manifest['pages']:
        pid=item['id'];path=ROOT/item['path'];old=load(work/'backup'/item['path']);new=load(path)
        if sha(work/'backup'/item['path'])!=item['source_sha256']:raise ValueError('Backup changed')
        if sha(path)!=registry[pid]['applied_sha256']:raise ValueError('Applied data changed')
        before=old.get('page',old);after=new.get('page',new);old_lines=body(before);new_lines=body(after)
        if set(old_lines)!=set(new_lines):raise ValueError('Body IDs changed')
        if [z for z in before['zones'] if z['kind']!='column']!=[z for z in after['zones'] if z['kind']!='column']:
            raise ValueError('Furniture or headings changed')
        if new.get('geometry',geometries.get(pid))!=load(work/'geometry'/f'{pid}.json'):
            raise ValueError('UI geometry changed')
        record=registry[pid];retained={r['line'] for r in record['retained_lines']}
        if len(new_lines)!=record['recognized_lines']+len(retained):raise ValueError('Line accounting mismatch')
        for key in retained:
            if new_lines[key]!=old_lines[key]:raise ValueError('Retained line changed')
        prepared={r['line']:r for r in load(work/'prepared'/f'{pid}.json')['records']}
        for key in set(new_lines)-retained:
            raw=(work/'predictions'/(Path(prepared[key]['image']).stem+'.pred.txt')).read_text().rstrip('\r\n')
            expected=decode_prediction(raw,True)
            if text(new_lines[key])!=expected['text'].strip():raise ValueError('Text differs from new OCR')
            if visible_style(new_lines[key])!=visible_style({'runs':expected['runs']}):raise ValueError('Typeface differs from new OCR')
        totals.update(pages=1,body_lines=len(new_lines),recognized_lines=record['recognized_lines'],
                      retained_lines=len(retained),changed_lines=record['changed_lines'])
        reasons.update(r['reason'] for r in record['retained_lines'])
    summary={'format':'nippo-ocr-refresh-verification','verified_at':datetime.now(timezone.utc).isoformat(),
        'original_commit':manifest['source_commit'],'model_manifest_sha256':manifest['model_manifest_sha256'],
        'totals':dict(totals),'retained_reasons':dict(reasons),'excluded':manifest['excluded'],
        'verified':['original_backup_hashes','excluded_pages_unchanged','stable_body_ids','furniture_unchanged',
                    'ui_geometry_unchanged','retained_lines_unchanged','applied_file_hashes',
                    'all_replaced_text_and_typeface_match_v2_predictions','complete_line_accounting']}
    save(ROOT/'pilot/human-review/ocr-refresh-v2-summary.json',summary)
    print(json.dumps(summary['totals']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['plan','prepare','predict','propose','apply','verify'])
    p.add_argument('--pages',nargs='*',type=int)
    p.add_argument('--work',type=Path,default=WORK)
    args=p.parse_args();manifest=plan(args.work)
    if sha(MODEL/'model.json')!=manifest['model_manifest_sha256']:raise ValueError('Model changed')
    for name,digest in load(MODEL/'model.json')['file_sha256'].items():
        if sha(MODEL/name)!=digest:raise ValueError(f'Model package changed: {name}')
    items=[i for i in manifest['pages'] if args.pages is None or int(i['id'][-4:]) in args.pages]
    if args.stage=='plan':print(len(items),'eligible pages; protected/excluded',len(manifest['excluded']));return
    if args.stage=='verify':verify(manifest,args.work);return
    if args.stage=='prepare':
        for item in items:prepare(item,args.work)
    elif args.stage=='predict':
        with (args.work/'predict.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            predict(items,args.work)
    else:apply(items,args.work,args.stage=='apply')


if __name__=='__main__':main()
