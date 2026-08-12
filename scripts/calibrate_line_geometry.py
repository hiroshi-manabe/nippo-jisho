#!/usr/bin/env python3
"""Backfill explicit, reviewable line rectangles for processed pages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter1d


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def local_centres(
    image: Image.Image,
    box: list[int],
    count: int,
    first: int,
    last: int,
    projection_snap: bool = True,
) -> list[int]:
    left, top, right, bottom = box
    inset = max(45, (right - left) // 14)
    gray = np.asarray(image.convert("L"))[top:bottom, left + inset:right - inset]
    projection = gaussian_filter1d((gray < 105).sum(axis=1).astype(float), 4)
    expected = np.linspace(first, last, count)
    if not projection_snap:
        return [round(value) for value in expected]
    centres: list[int] = []
    radius = 24
    for value in expected:
        relative = value - top
        start = max(0, round(relative - radius))
        stop = min(len(projection), round(relative + radius + 1))
        centre = top + start + int(np.argmax(projection[start:stop]))
        if centres and centre <= centres[-1] + 28:
            centre = round(value)
        centres.append(centre)
    return centres


def rectangles(
    box: list[int], centres: list[int], overlap: int = 18
) -> list[tuple[list[int], list[int]]]:
    left, top, right, bottom = box
    if len(centres) > 1:
        nominal = float(np.median(np.diff(centres)))
    else:
        nominal = 62.0
    result = []
    for index, centre in enumerate(centres):
        previous = centres[index - 1] if index else centre - nominal
        following = centres[index + 1] if index + 1 < len(centres) else centre + nominal
        # Retain modest overlap so ascenders, descenders, and locally drifting
        # baselines remain readable in the default line view.
        crop_top = max(top, round((previous + centre) / 2 - overlap))
        crop_bottom = min(bottom, round((centre + following) / 2 + overlap))
        context_top = max(top, round(centre - nominal * 2.7))
        context_bottom = min(bottom, round(centre + nominal * 2.7))
        result.append(
            (
                [left, crop_top, right - left, crop_bottom - crop_top],
                [left, context_top, right - left, context_bottom - context_top],
            )
        )
    return result


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def contact_sheet(
    image: Image.Image,
    page_id: str,
    column_id: str,
    lines: list[tuple[str, str, list[int]]],
    output: Path,
) -> None:
    label_width = 125
    image_width = 1100
    row_height = 78
    header = 42
    sheet = Image.new("RGB", (label_width + image_width, header + row_height * len(lines)), "#f4efe4")
    draw = ImageDraw.Draw(sheet)
    label_font = font(17)
    small_font = font(12)
    draw.text((10, 10), f"{page_id} · {column_id} · {len(lines)} lines", fill="#26221d", font=label_font)
    for index, (line_id, text, crop) in enumerate(lines):
        x, y, width, height = crop
        strip = image.crop((x, y, x + width, y + height)).convert("RGB")
        target_height = row_height - 6
        strip.thumbnail((image_width, target_height), Image.Resampling.LANCZOS)
        top = header + index * row_height
        sheet.paste(strip, (label_width, top + (row_height - strip.height) // 2))
        draw.text((8, top + 8), line_id, fill="#5e5549", font=small_font)
        draw.text((8, top + 31), text[:15], fill="#7c7265", font=small_font)
        draw.line((0, top + row_height - 1, sheet.width, top + row_height - 1), fill="#d5ccbd")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, "JPEG", quality=88, optimize=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration", type=Path, default=root / "pilot/human-review/line-calibration.json")
    parser.add_argument("--tile-config", type=Path, default=root / "pilot/tile-config-v1-trial.json")
    parser.add_argument("--master-dir", type=Path, default=root / ".cache/sources/bnf-gallica/master")
    parser.add_argument("--output", type=Path, default=root / "pilot/human-review/line-geometry.json")
    parser.add_argument("--review-dir", type=Path, default=root / ".cache/line-geometry-review")
    parser.add_argument("--mark-reviewed", action="store_true", help="record that every generated contact sheet has been visually reviewed")
    args = parser.parse_args()
    calibration = load_json(args.calibration)
    tile_pages = {page["id"]: page for page in load_json(args.tile_config)["pages"]}
    output_pages = []
    for calibrated_page in calibration["pages"]:
        page_id = calibrated_page["id"]
        page_data = load_json(root / f"pilot/format-v1-trial/level1/{page_id}.json")
        zones = {zone["id"]: zone for zone in page_data["zones"]}
        config_zones = {zone["id"]: zone for zone in tile_pages[page_id]["zones"]}
        master_name = tile_pages[page_id]["master"]
        with Image.open(args.master_dir / master_name) as source:
            source.load()
            page_output = {"id": page_id, "source_size": list(source.size), "columns": {}}
            for column_id, column in calibrated_page["columns"].items():
                box = config_zones[column_id]["box"]
                line_map: dict[str, dict] = {}
                sheet_lines: list[tuple[str, str, list[int]]] = []
                for first_id, last_id, first_y, last_y in column["ranges"]:
                    zone_lines = [line for zone_id in column["zones"] for line in zones[zone_id]["lines"]]
                    start = next(i for i, line in enumerate(zone_lines) if line["id"] == first_id)
                    stop = next(i for i, line in enumerate(zone_lines) if line["id"] == last_id)
                    selected = zone_lines[start:stop + 1]
                    centres = local_centres(
                        source,
                        box,
                        len(selected),
                        first_y,
                        last_y,
                        column.get("projection_snap", True),
                    )
                    centre_overrides = column.get("centre_overrides", {})
                    for index, line in enumerate(selected):
                        if line["id"] in centre_overrides:
                            centre = centre_overrides[line["id"]]
                            if not isinstance(centre, int):
                                raise SystemExit(
                                    f"invalid centre override for {page_id}/{column_id}/{line['id']}"
                                )
                            centres[index] = centre
                    for line, centre, (crop, context) in zip(
                        selected,
                        centres,
                        rectangles(box, centres, column.get("crop_overlap", 18)),
                    ):
                        line_map[line["id"]] = {"centre_y": centre, "crop": crop, "context_crop": context}
                        text = "".join(run["text"] for run in line["runs"])
                        sheet_lines.append((line["id"], text, crop))
                expected = [line for zone_id in column["zones"] for line in zones[zone_id]["lines"]]
                if set(line_map) != {line["id"] for line in expected}:
                    raise SystemExit(f"incomplete geometry for {page_id}/{column_id}")
                for line_id, crop in column.get("crop_overrides", {}).items():
                    if line_id not in line_map:
                        raise SystemExit(
                            f"unknown crop override for {page_id}/{column_id}/{line_id}"
                        )
                    if (
                        not isinstance(crop, list)
                        or len(crop) != 4
                        or any(not isinstance(value, int) for value in crop)
                    ):
                        raise SystemExit(
                            f"invalid crop override for {page_id}/{column_id}/{line_id}"
                        )
                    line_map[line_id]["crop"] = crop
                page_output["columns"][column_id] = {
                    "box": box,
                    "visual_review": (
                        column.get("review_state", "contact_sheet_reviewed")
                        if args.mark_reviewed
                        else "contact_sheet_pending"
                    ),
                    **(
                        {"reviewed_at": column.get("reviewed_at", "2026-08-01")}
                        if args.mark_reviewed
                        else {}
                    ),
                    "lines": line_map,
                }
                contact_sheet(source, page_id, column_id, sheet_lines, args.review_dir / f"{page_id}-{column_id}.jpg")
            output_pages.append(page_output)
    payload = {
        "format": "nippo-line-geometry",
        "format_version": 1,
        "coordinate_space": "native Gallica master pixels",
        "pages": output_pages,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote explicit geometry for {sum(len(c['lines']) for p in output_pages for c in p['columns'].values())} lines on {len(output_pages)} pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
