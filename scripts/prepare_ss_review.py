"""Freeze italic double-long-s candidates through f200; render review evidence."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]

def main():
    classification = json.loads((ROOT/'scripts/ss_review_classification.json').read_text())
    corpus = json.loads((ROOT/'build/human-review/corpus.json').read_text())
    pages = corpus['pages']
    out = ROOT/'site/assets/ss-review'
    out.mkdir(exist_ok=True)
    sheets = ROOT/'.cache/ss-review-sheets'
    sheets.mkdir(parents=True, exist_ok=True)
    items = []
    evidence = []
    for p in pages:
        if p['leaf'] > 200 or not p.get('processed'):
            continue
        im = None
        for z in p.get('zones', []):
            for line in z.get('lines', []):
                offset = 0
                matches = []
                for run in line['runs']:
                    start = 0
                    while run['typeface'] == 'italic':
                        pos = run['text'].find('ſſ', start)
                        if pos < 0: break
                        matches.append(offset + pos)
                        start = pos + 2
                    offset += len(run['text'])
                if not matches: continue
                if 'crop' not in line: raise ValueError((p['leaf'], line['id']))
                if im is None:
                    im = Image.open(ROOT/f'build/nippo-jisho-images/scans/native/f{p["leaf"]:04}.jpg')
                x,y,w,h = line['crop']
                if p['leaf'] == 71 and line['id'] == 'c2-l031':
                    y += h * 0.25
                    h *= 1.5
                sx,sy = im.width/p['width'], im.height/p['height']
                crop = im.crop((round(x*sx),round(y*sy),round((x+w)*sx),round((y+h)*sy)))
                name = f'f{p["leaf"]}-{line["id"]}.webp'
                crop.save(out/name, quality=95)
                context = im.crop((max(0,round((x-15)*sx)),max(0,round((y-h)*sy)),
                                   min(im.width,round((x+w+15)*sx)),min(im.height,round((y+2*h)*sy))))
                context.save(out/name.replace('.webp','-context.webp'), quality=95)
                for occurrence,pos in enumerate(matches, 1):
                    ident = f'f{p["leaf"]}/{line["id"]}#{occurrence}'
                    items.append(dict(id=ident, leaf=p['leaf'], line=line['id'], position=pos,
                                      text=line['text'], image=f'assets/ss-review/{name}',
                                      version=line['transcription_version'], two_long=False))
                    evidence.append((len(items)-1, ident, crop.copy()))
    digest = hashlib.sha256(json.dumps(items,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    if digest != classification['baseline']:
        raise ValueError('Frozen candidate identities or text changed; rebase classification explicitly.')
    if len(items) != classification['reviewed_count']:
        raise ValueError('Candidate set changed: rebase the visual classification before publishing.')
    for i in classification['two_long_indices']:
        items[i]['two_long'] = True
    (out/'candidates.json').write_text(json.dumps(dict(format='nippo-italic-ss-review',version=1,
        baseline=digest,commit=corpus['commit'],
        page_versions={str(p['leaf']):p.get('transcription_version') for p in pages if p['leaf']<=200},
        items=items),ensure_ascii=False,indent=2)+'\n')
    for n in range(0,len(evidence),32):
        canvas = Image.new('RGB',(1200,32*140),'white'); draw=ImageDraw.Draw(canvas)
        for row,(idx,ident,crop) in enumerate(evidence[n:n+32]):
            draw.text((5,row*140+2),f'{idx}: {ident}',fill='black')
            crop.thumbnail((1190,115))
            canvas.paste(crop,(5,row*140+22))
        canvas.save(sheets/f'{n//32:02}.jpg')
    print(f'{len(items)} occurrences; {len(list(sheets.glob("*.jpg")))} contact sheets')

if __name__ == '__main__': main()
