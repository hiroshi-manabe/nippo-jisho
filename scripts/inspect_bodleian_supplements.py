#!/usr/bin/env python3
"""Generate source-identification/layout contact sheets (not transcription)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]

def main():
    records = json.loads((ROOT/'sources/bodleian-supplement-sources.json').read_text())['pages']
    out = ROOT/'.cache/sources/bodleian/supplement-inspection'
    out.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(records), 4):
        sheet = Image.new('RGB', (1600, 1950), 'white')
        draw = ImageDraw.Draw(sheet)
        for index, record in enumerate(records[start:start+4]):
            with Image.open(ROOT/record['cache_path']) as source:
                source = source.convert('RGB')
                source.thumbnail((790, 920))
                x,y = (index%2)*800,(index//2)*975
                sheet.paste(source,(x,y+30))
                draw.text((x+10,y+5), record['id']+' '+record['canvas_label'],fill='black')
        sheet.save(out/f"{records[start]['printed_page']}.jpg")
        anchor=int(records[start]['insert_after'].split('f')[-1])
        comparison=Image.new('RGB',(1600,1200),'white')
        draw=ImageDraw.Draw(comparison)
        paths=[ROOT/f'build/nippo-jisho-images/scans/native/f{anchor-1:04d}.jpg',
               ROOT/f'build/nippo-jisho-images/scans/native/f{anchor+1:04d}.jpg']
        for index,path in enumerate(paths):
            with Image.open(path) as source:
                source=source.convert('RGB')
                source.thumbnail((790,1150))
                comparison.paste(source,(index*800,30))
                draw.text((index*800+10,5),path.name,fill='black')
        comparison.save(out/f"{records[start]['printed_page']}-neighbors.jpg")
    geometry={p['id']:p for p in json.loads((ROOT/'pilot/human-review/line-geometry.json').read_text())['pages']}
    for record in records[::4]:
        if record['id'] not in geometry:
            continue
        sheet=Image.new('RGB',(1200,1000),'white')
        draw=ImageDraw.Draw(sheet)
        y=0
        with Image.open(ROOT/record['cache_path']) as image:
            for column in geometry[record['id']]['columns'].values():
                lines=list(column['lines'].items())
                for lid,line in [lines[0],lines[len(lines)//2],lines[-1]]:
                    x,top,w,h=line['crop']
                    crop=image.crop((x,top,x+w,top+h)).convert('RGB')
                    crop.thumbnail((1190,120))
                    draw.text((5,y+3),record['id']+'/'+lid,fill='black')
                    sheet.paste(crop,(0,y+23))
                    y+=160
        sheet.save(out/f"{record['printed_page']}-crops.jpg")

if __name__ == '__main__':
    main()
