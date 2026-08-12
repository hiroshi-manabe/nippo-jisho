#!/usr/bin/env python3
"""Render isolated line crops with their complete assigned transcriptions."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def line_text(line: dict) -> str:
    return "".join(run["text"] for run in line["runs"])


def render_group(
    source: Image.Image,
    page_id: str,
    column_id: str,
    lines: list[tuple[str, str, list[int]]],
    output: Path,
) -> None:
    width = 1220
    margin = 24
    gap = 18
    image_width = width - margin * 2
    label_font = font(19)
    text_font = font(21)
    prepared: list[tuple[str, list[str], Image.Image]] = []
    heights: list[int] = []
    for line_id, text, crop in lines:
        x, y, crop_width, crop_height = crop
        strip = source.crop((x, y, x + crop_width, y + crop_height)).convert("RGB")
        if strip.width > image_width:
            strip.thumbnail((image_width, strip.height), Image.Resampling.LANCZOS)
        wrapped = textwrap.wrap(text, width=94, break_long_words=False) or [""]
        card_height = 31 + strip.height + 12 + len(wrapped) * 28 + 18
        prepared.append((line_id, wrapped, strip))
        heights.append(card_height)

    sheet = Image.new("RGB", (width, sum(heights) + gap * (len(lines) + 1)), "#d8cebd")
    draw = ImageDraw.Draw(sheet)
    top = gap
    for (line_id, wrapped, strip), card_height in zip(prepared, heights):
        draw.rounded_rectangle((8, top, width - 8, top + card_height), radius=8, fill="#fbf8f1")
        draw.text((margin, top + 8), f"{page_id}/{column_id}/{line_id}", fill="#5b5145", font=label_font)
        image_top = top + 37
        sheet.paste(strip, (margin, image_top))
        text_top = image_top + strip.height + 10
        for index, text_line in enumerate(wrapped):
            draw.text((margin, text_top + index * 28), text_line, fill="#17130f", font=text_font)
        top += card_height + gap
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, "JPEG", quality=92, optimize=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--last", type=int, required=True)
    parser.add_argument("--group-size", type=int, default=8)
    parser.add_argument("--master-dir", type=Path, default=root / ".cache/sources/bnf-gallica/master")
    parser.add_argument("--output", type=Path, default=root / ".cache/line-geometry-semantic-audit")
    args = parser.parse_args()

    geometry = {page["id"]: page for page in load_json(root / "pilot/human-review/line-geometry.json")["pages"]}
    tiles = {page["id"]: page for page in load_json(root / "pilot/tile-config-v1-trial.json")["pages"]}
    calibrations = {page["id"]: page for page in load_json(root / "pilot/human-review/line-calibration.json")["pages"]}
    for leaf in range(args.first, args.last + 1):
        page_id = f"bnf-f{leaf:04d}"
        page = load_json(root / f"pilot/format-v1-trial/level1/{page_id}.json")
        zones = {zone["id"]: zone for zone in page["zones"]}
        with Image.open(args.master_dir / tiles[page_id]["master"]) as source:
            source.load()
            for column_id, column in geometry[page_id]["columns"].items():
                zone_ids = calibrations[page_id]["columns"][column_id]["zones"]
                source_lines = [line for zone_id in zone_ids for line in zones[zone_id]["lines"]]
                records = [(line["id"], line_text(line), column["lines"][line["id"]]["crop"]) for line in source_lines]
                for start in range(0, len(records), args.group_size):
                    group = records[start : start + args.group_size]
                    output = args.output / page_id / f"{column_id}-{start + 1:03d}-{start + len(group):03d}.jpg"
                    render_group(source, page_id, column_id, group, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
