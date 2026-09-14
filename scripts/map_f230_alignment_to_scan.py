"""Replay Kraken extraction on coordinate fields to recover scan positions."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from kraken.containers import BaselineLine, Segmentation
from kraken.lib.segmentation import extract_polygons
from ocr_line_images import prepare_rectified_line
import hashlib

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'site/assets/alignment/bnf-f0230.json'
data=json.loads(target.read_text())
manifest=json.loads((ROOT/'.cache/ocr-model/page-refresh-v2/prepared/bnf-f0230.json').read_text())
records={r['line']:r for r in manifest['records']}
scan=Image.open(ROOT/'build/nippo-jisho-images/scans/native/f0230.jpg').convert('RGB')
y,x=np.indices((scan.height,scan.width),dtype=np.float32)
fields=[Image.fromarray(x+1),Image.fromarray(y+1),Image.fromarray(np.ones_like(x))]
for row in data['rows']:
    if not row.get('image'):continue
    if row['id'] not in records:
        if row['id']=='c1b-l003':
            w=row['image_width'];row['scan_mapping']={'origin':[770,1811], 'dx':[665/w,0], 'dy':[0,78/48]}
        continue
    r=records[row['id']]
    seg=Segmentation(type='baselines',imagename='',text_direction='horizontal-lr',script_detection=False,lines=[BaselineLine(id=r['line'],baseline=r['baseline'],boundary=r['boundary'])])
    original_getbbox=Image.Image.getbbox
    boxes=[]
    def record_bbox(image,*args,**kwargs):
        box=original_getbbox(image,*args,**kwargs);boxes.append(box);return box
    Image.Image.getbbox=record_bbox
    try:crop=next(extract_polygons(ImageOps.invert(scan),seg))[0]
    finally:Image.Image.getbbox=original_getbbox
    prepared=prepare_rectified_line(ImageOps.invert(crop))
    saved=Image.open(ROOT/'.cache/ocr-model/page-refresh-v2'/r['image'])
    if prepared.size!=saved.size or not np.array_equal(np.asarray(prepared),np.asarray(saved)):
        raise ValueError('Replayed crop differs: '+row['id'])
    Image.Image.getbbox=lambda image,*args,**kwargs:boxes[-1]
    try:maps=[np.asarray(next(extract_polygons(f,seg))[0]) for f in fields]
    finally:Image.Image.getbbox=original_getbbox
    if any(a.shape!=(crop.height,crop.width) for a in maps):raise ValueError('Coordinate crop extent mismatch')
    # Exclude pixels blended with zero-valued polygon padding: otherwise the
    # coordinate values themselves are attenuated and yield spurious shears.
    valid=(maps[2]>.99999)
    yy,xx=np.nonzero(valid)
    # Sample the coordinate field, fitting local affine maps around each
    # character. This handles the piecewise warp without inverting guessed boxes.
    source=np.column_stack([maps[0][valid]-1,maps[1][valid]-1])
    points=np.column_stack([(xx+.5)*prepared.width/crop.width-.5,(yy+.5)*48/crop.height-.5])
    mappings=[]
    for a in row['alignment']:
        px=(a['left']+a['width']/2)*prepared.width/100
        dist=np.sum((points-[px,35])**2,axis=1)
        take=np.argpartition(dist,min(79,len(dist)-1))[:80]
        fit=np.linalg.lstsq(np.column_stack([np.ones(len(take)),points[take]]),source[take],rcond=None)[0]
        mappings.append({'origin':fit[0].tolist(),'dx':fit[1].tolist(),'dy':fit[2].tolist()})
    row['scan_mappings']=mappings
data['scan_mapping_source_sha256']=hashlib.sha256((ROOT/'build/nippo-jisho-images/scans/native/f0230.jpg').read_bytes()).hexdigest()
output=ROOT/'.cache/ocr-model/character-positions-v1/f230-native-mapping.json'
output.write_text(json.dumps(data,ensure_ascii=False)+'\n')
print('Mapped',sum('scan_mappings' in r or 'scan_mapping' in r for r in data['rows']),'lines')
