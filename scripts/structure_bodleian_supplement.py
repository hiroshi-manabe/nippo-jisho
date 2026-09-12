"""Source adapter to the ordinary automated column/heading/furniture inference."""
from bootstrap_ocr_level1 import infer_column, furniture_zone


class Styles:
    def runs(self, text, **kwargs):
        return [{'typeface':'roman','text':text}], []


def structure_page(page, geometry, rows):
    width,height=geometry['source_size']
    edges=(370,1450,2545) if page['id'].endswith('r') else (955,2040,3180)
    draft={'source':{'source_size':[width,height]}, 'columns':{},
           'header_window':(0.10,0.17),'row_tolerance':-1,'preserve_ocr':True}
    originals={}
    for col in (1,2):
        name=f'column-{col}'
        colrows=[r for r in rows if r['column']==col]
        lines=next(z['lines'] for z in page['zones'] if z['id']==name)
        left=max(0,min(edges[col-1],int(min(p[0] for r in colrows for p in r['boundary']))-15))
        right=min(width,max(edges[col],int(max(p[0] for r in colrows for p in r['boundary']))+20))
        candidates=[]
        for row,line in zip(colrows,lines):
            lid=line['id']
            originals[lid]=line
            ys=[p[1] for p in row['boundary']]
            top,bottom=max(0,int(min(ys))-15),min(height,int(max(ys))+15)
            candidates.append({'id':lid,'centre':[0,row['y']], 'baseline':row['baseline'],
                'text':''.join(r['text'] for r in line['runs']),
                'crop':[left,top,right-left,bottom-top],
                'ocr_crop':[left,top,right-left,bottom-top],
                'ui_crop':[left,top,right-left,bottom-top],
                'ui_context_crop':[left,max(0,top-80),right-left,min(height,bottom+80)-max(0,top-80)]})
        draft['columns'][name]={'lines':candidates}
        last_y=max(c['centre'][1] for c in candidates)
        tail=[c for c in candidates if c['centre'][1]>=last_y-20]
        if last_y>height*0.81 and all(len(c['text'])<25 and min(p[0] for p in c['baseline'])-left>(right-left)*0.3 for c in tail):
            draft['columns'][name]['body_cutoff_y']=min(c['centre'][1] for c in tail)-25
    zones=[]
    retained=set()
    for col in (1,2):
        name=f'column-{col}'
        result=infer_column(draft,name,Styles(),None)
        def keep(row):
            lid=row['chosen_candidate']['id']
            retained.add(lid)
            return originals[lid]
        zones.append({'id':f'header-column-{col}','kind':'running_header',
                      'label':f'Column {col} running header','lines':[keep(result['header'])]})
        geometry_lines={}
        remap={}
        for rec in result['row_records'].values():
            oldid=rec['evidence']['source_candidate_ids'][0]
            if rec['line'].get('indent'):
                originals[oldid]['indent']=rec['line']['indent']
            remap[rec['line']['id']]=oldid
            retained.add(oldid)
            geometry_lines[oldid]={k:rec['evidence'][k] for k in ('centre_y','crop','context_crop')}
        headings=iter(result['heading_rows'])
        for zone in result['zones']:
            if zone['kind']=='section_heading':
                zone['lines']=[keep(next(headings))]
            else:
                zone['lines']=[originals[remap[line['id']]] for line in zone['lines']]
            zones.append(zone)
        leftovers=[{'text':c['text'],'centre_y':c['centre'][1],'chosen_candidate':c}
                   for c in draft['columns'][name]['lines'] if c['id'] not in retained]
        for position,subset in [('top',[r for r in leftovers if r['centre_y']<=result['header']['centre_y']+25]),
                                ('bottom',[r for r in leftovers if r['centre_y']>result['header']['centre_y']+25])]:
            zone=furniture_zone(col,position,subset)
            if zone:
                zone['lines']=[keep(row) for row in subset]
                zones.append(zone)
        geometry['columns'][name]={'box':result['geometry']['box'],
             'visual_review':'ocr_bootstrap_unreviewed','lines':geometry_lines}
    assert retained==set(originals),'Structural preparation lost an OCR detection'
    page['zones']=zones
    return page,geometry
