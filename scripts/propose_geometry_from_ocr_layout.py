#!/usr/bin/env python3
"""Build reviewable geometry proposals from the preserved OCR layout archive."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from build_ocr_dataset import load_json, write_json


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "pilot/ocr-layout-evidence/v1"
AUDIT = EVIDENCE / "geometry-audit.json.gz"
GEOMETRY = ROOT / "pilot/human-review/line-geometry.json"
SCANS = ROOT / "build/nippo-jisho-images/scans/native"
OUTPUT = EVIDENCE / "campaign-f0171-f0237"


def load_gzip(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))


def page_number(identifier: str) -> int:
    return int(identifier.removeprefix("bnf-f"))


def normalized_vertical_crop(line: dict, page_height: int) -> tuple[int, int]:
    _, top, _, height = line["detected_bbox"]
    bottom = top + height
    centre = round(line["ocr_centre_y"])
    # The baseline need not be vertically centered inside Kraken's boundary.
    # Take the union rather than replacing a short asymmetric polygon with a
    # centered band, or tall ascenders above the baseline can be lost.
    top = min(top, centre - 48)
    bottom = max(bottom, centre + 48)
    # Retain a small independent safety margin beyond the detector polygon.
    return max(0, top - 2), min(page_height, bottom + 2)


def proposal_page(audit_page: dict, current: dict) -> dict:
    source_width, source_height = current["source_size"]
    lines_by_column: dict[str, list[dict]] = {}
    for line in audit_page["lines"]:
        lines_by_column.setdefault(line["column"], []).append(line)
    columns = {}
    for column, lines in lines_by_column.items():
        current_column = current["columns"][column]
        current_left, current_top, current_right, current_bottom = current_column["box"]
        bands = [line["ocr_crop"] for line in lines if line.get("ocr_crop")]
        band_left = min((band[0] for band in bands), default=current_left)
        band_right = max((band[0] + band[2] for band in bands), default=current_right)
        left = max(0, min(current_left, band_left))
        right = min(source_width, max(current_right, band_right))
        geometry_lines = {}
        tops, bottoms = [], []
        for line in lines:
            top, bottom = normalized_vertical_crop(line, source_height)
            tops.append(top)
            bottoms.append(bottom)
            context_top = max(0, top - 105)
            context_bottom = min(source_height, bottom + 105)
            geometry_lines[line["line_id"]] = {
                "centre_y": round(line["ocr_centre_y"]),
                "crop": [left, top, right - left, bottom - top],
                "context_crop": [left, context_top, right - left, context_bottom - context_top],
                "ocr_evidence": {
                    "version": 1,
                    "candidate_id": line["candidate_id"],
                    "relaxed_cer": line["relaxed_cer"],
                    "source_bbox": line["detected_bbox"],
                },
            }
        box_top = max(0, min(tops) - 105) if tops else current_top
        box_bottom = min(source_height, max(bottoms) + 105) if bottoms else current_bottom
        columns[column] = {
            "box": [left, box_top, right, box_bottom],
            "visual_review": "contact_sheet_reviewed",
            "reviewed_at": "2026-09-05",
            "geometry_method": "preserved_ocr_layout_v1_alignment",
            "lines": geometry_lines,
        }
    return {"id": audit_page["id"], "source_size": current["source_size"], "columns": columns}


def render_page(page: dict, output: Path) -> None:
    scan_path = SCANS / f"f{page_number(page['id']):04d}.jpg"
    with Image.open(scan_path) as opened:
        scan = opened.convert("RGB")
    font = ImageFont.load_default()
    for column, value in page["columns"].items():
        lines = list(value["lines"].items())
        strip_width = 900
        row_height = 120
        sheet = Image.new("RGB", (strip_width + 150, row_height * len(lines)), "white")
        draw = ImageDraw.Draw(sheet)
        for index, (line_id, geometry) in enumerate(lines):
            x, y, width, height = geometry["crop"]
            strip = scan.crop((x, y, x + width, y + height))
            strip.thumbnail((strip_width, row_height - 8))
            top = index * row_height
            sheet.paste(strip, (150, top + (row_height - strip.height) // 2))
            draw.text((8, top + 8), line_id, fill="black", font=font)
        destination = output / f"{page['id']}-{column}.jpg"
        destination.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(destination, quality=88)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--first", type=int, default=171)
    result.add_argument("--last", type=int, default=237)
    result.add_argument("--audit", type=Path, default=AUDIT)
    result.add_argument("--output", type=Path, default=OUTPUT)
    result.add_argument("--render", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    audit = load_gzip(args.audit)
    current = {page["id"]: page for page in load_json(GEOMETRY)["pages"]}
    proposals, excluded = [], []
    for page in audit["pages"]:
        number = page_number(page["id"])
        if not args.first <= number <= args.last:
            continue
        if page["status"] != "complete" or page["matched"] != page["targets"]:
            excluded.append(
                {
                    "id": page["id"],
                    "status": page["status"],
                    "unmatched_targets": page["unmatched_targets"],
                    "neighbor_conflicts": page["neighbor_conflicts"],
                    "unused_candidates": page["unused_candidates"],
                }
            )
            continue
        proposal = proposal_page(page, current[page["id"]])
        proposals.append(proposal)
        if args.render:
            render_page(proposal, args.output / "contact-sheets")
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output / "line-geometry.json",
        {
            "format": "nippo-line-geometry-proposal",
            "format_version": 1,
            "method": "preserved-ocr-layout-v1-to-canonical-text-alignment",
            "pages": proposals,
        },
    )
    write_json(
        args.output / "report.json",
        {
            "format": "nippo-ocr-layout-geometry-campaign",
            "format_version": 1,
            "range": [args.first, args.last],
            "proposed_pages": [page["id"] for page in proposals],
            "excluded_pages": excluded,
            "policy": {
                "canonical_text_modified": False,
                "structural_conflicts_automatically_applied": False,
                "visual_review_required_before_verified_status": True,
            },
        },
    )
    print(f"Proposed {len(proposals)} pages; excluded {len(excluded)} structural pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
