#!/usr/bin/env python3
"""Render isolated proposed crops with their canonical text for visual review."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from build_ocr_dataset import line_texts

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal-dir', type=Path, required=True)
    parser.add_argument('--first', type=int, required=True)
    parser.add_argument('--last', type=int, required=True)
    parser.add_argument('--rows', type=int, default=12)
    args = parser.parse_args()
    pages = json.loads((args.proposal_dir/'proposal.json').read_text())['pages']
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 19)
    for page in pages:
        leaf = int(page['id'].split('f')[-1])
        if not args.first <= leaf <= args.last:
            continue
        scan = Image.open(ROOT/f'.cache/sources/bnf-gallica/master/f{leaf:04d}.jpg').convert('RGB')
        text = line_texts(json.loads((ROOT/f"pilot/format-v1-trial/level1/{page['id']}.json").read_text()))
        directory = args.proposal_dir/'sheets'/page['id']
        directory.mkdir(parents=True, exist_ok=True)
        for column, data in page['columns'].items():
            lines = list(data['lines'].items())
            for start in range(0, len(lines), args.rows):
                rows = []
                for key, value in lines[start:start+args.rows]:
                    x,y,w,h = value['crop']
                    crop = scan.crop((x,y,x+w,y+h))
                    width = 1050
                    crop = crop.resize((width, round(h*width/w)))
                    row = Image.new('RGB', (width, crop.height+34), 'white')
                    row.paste(crop, (0,34))
                    ImageDraw.Draw(row).text((3,3), f'{leaf}/{key}  {text.get(key, "")}', font=font, fill='black')
                    rows.append(row)
                sheet = Image.new('RGB', (1050, sum(r.height+5 for r in rows)), '#3182bd')
                offset = 0
                for row in rows:
                    sheet.paste(row, (0,offset)); offset += row.height+5
                sheet.save(directory/f'{column}-{start+1:03d}.jpg', quality=92)
        print(page['id'], flush=True)


if __name__ == '__main__':
    main()
