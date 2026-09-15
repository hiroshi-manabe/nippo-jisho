"""Recover missing alignment crops from archived OCR polygons, never UI boxes.

Run in the Kraken environment. Canonical text and geometry are read-only.
"""
import argparse
import json
import re
from PIL import Image, ImageOps
from kraken.containers import BaselineLine, Segmentation
from kraken.lib.segmentation import extract_polygons
from refresh_unreviewed_ocr import ROOT, WORK, associate, body, save, sha
from audit_ocr_layout_geometry import read_evidence, column_candidates
from build_ocr_retraining_dataset import full_text_candidates
from ocr_line_images import prepare_rectified_line


def prepare(pid):
    output=WORK/'prepared'/f'{pid}.json'
    if output.exists():
        return
    page=json.loads((ROOT/f'pilot/format-v1-trial/level1/{pid}.json').read_text())
    geometry=next(p for p in json.loads((ROOT/'pilot/human-review/line-geometry.json').read_text())['pages'] if p['id']==pid)
    evidence=read_evidence(pid, ROOT/'pilot/ocr-layout-evidence/v1')
    lines=body(page)
    selected=[]; rejected=[]
    for col,g in geometry['columns'].items():
        refs=[lines[k] for k in g['lines'] if k in lines]
        physical=re.match(r'column-\d+',col)
        evidence_column=col if col in evidence['columns'] else physical.group() if physical else col
        matched,failed=associate(refs,full_text_candidates(column_candidates(evidence,evidence_column),g),g)
        selected.extend(matched); rejected.extend(failed)
    accounted={r['id'] for r,_,_ in selected}|{r['line'] for r in rejected}
    rejected.extend({'line':k,'reason':'missing_geometry'} for k in lines if k not in accounted)
    scan=ROOT/f'build/nippo-jisho-images/scans/native/{pid.removeprefix("bnf-")}.jpg'
    if sha(scan)!=page['source']['master_sha256']:
        raise ValueError('Scan checksum mismatch')
    folder=WORK/'images'/pid
    folder.mkdir(parents=True,exist_ok=True)
    records=[]
    with Image.open(scan) as original:
        inverted=ImageOps.invert(original.convert('RGB'))
        for ref,candidate,distance in selected:
            lid=ref['id']
            try:
                seg=Segmentation(type='baselines',imagename=str(scan),text_direction='horizontal-lr',script_detection=False,
                    lines=[BaselineLine(id=lid,baseline=candidate['baseline'],boundary=candidate['boundary'])])
                crop,_=next(extract_polygons(inverted,seg))
                prepared=prepare_rectified_line(ImageOps.invert(crop))
                dest=folder/f'{pid}__{lid}.png'
                prepared.save(dest)
                records.append({'line':lid,'candidate_id':candidate['id'],'image':str(dest.relative_to(WORK)),
                    'image_sha256':sha(dest),'boundary':candidate['boundary'],'baseline':candidate['baseline'],
                    'association_distance':distance})
            except Exception as exc:
                rejected.append({'line':lid,'reason':'extraction_failed','detail':str(exc)})
    if not records:
        raise ValueError('No reliable OCR polygon associations; no manifest saved')
    save(output,{'id':pid,'records':records,'retained_lines':rejected,'body_lines':len(lines),
        'origin':'automatic_alignment_recovery','source_sha256':sha(scan)})
    print(f'{pid}: recovered {len(records)} crops; skipped {len(rejected)} lines',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('page')
    prepare(parser.parse_args().page)
