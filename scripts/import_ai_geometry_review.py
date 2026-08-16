#!/usr/bin/env python3
"""Validate and import one completed AI line-geometry review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def contains(outer: list[int], inner: list[int]) -> bool:
    ox, oy, ow, oh = outer
    ix, iy, iw, ih = inner
    return ox <= ix and oy <= iy and ox + ow >= ix + iw and oy + oh >= iy + ih


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path)
    parser.add_argument(
        "--geometry",
        type=Path,
        default=root / "pilot/human-review/line-geometry.json",
    )
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument(
        "--allow-geometry-only",
        action="store_true",
        help=(
            "accept a response whose geometry review is explicitly completed "
            "while its independent text review remains incomplete"
        ),
    )
    parser.add_argument(
        "--visual-review",
        choices=("ai_line_by_line_checked", "ai_bulk_geometry_sanity_checked"),
        default="ai_line_by_line_checked",
        help=(
            "provenance assigned to imported columns; use the bulk-sanity state "
            "when the rectangles were verified independently but the response "
            "does not credibly demonstrate individual line-level decisions"
        ),
    )
    args = parser.parse_args()

    review_path = args.review.resolve()
    review = load_json(review_path)
    if review.get("format") != "nippo-ai-line-geometry-response":
        raise SystemExit("unexpected review format")
    complete_review = review.get("response_status") == "completed_independent_ai_line_review"
    geometry_only_review = (
        args.allow_geometry_only
        and review.get("geometry_review_status") == "completed"
        and review.get("text_review_status") == "not_completed"
    )
    if not (complete_review or geometry_only_review):
        raise SystemExit("AI review is not complete")

    page_id = review["page"]
    page_path = root / review["transcription_source"]["page_file"]
    expected_page_hash = review["transcription_source"]["page_file_sha256"]
    if hashlib.sha256(page_path.read_bytes()).hexdigest() != expected_page_hash:
        raise SystemExit("canonical transcription differs from the version reviewed by the AI")
    source_path = root / ".cache/sources/bnf-gallica/master" / review["source"]["filename"]
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != review["source"]["sha256"]:
        raise SystemExit("master image differs from the version reviewed by the AI")

    geometry = load_json(args.geometry)
    page = next((item for item in geometry["pages"] if item["id"] == page_id), None)
    if page is None:
        raise SystemExit(f"page is absent from geometry record: {page_id}")
    width, height = page["source_size"]
    if [width, height] != [review["source"]["width"], review["source"]["height"]]:
        raise SystemExit("source dimensions differ")

    transcription = load_json(page_path)
    transcription_zones = {zone["id"]: zone for zone in transcription["zones"]}
    expected_ids = {
        line["id"]
        for reviewed_column in review["columns"].values()
        for zone_id in reviewed_column["zone_ids"]
        for line in transcription_zones[zone_id].get("lines", [])
    }
    reviewed_ids: set[str] = set()
    for column_id, reviewed_column in review["columns"].items():
        if column_id not in page["columns"]:
            raise SystemExit(f"unknown column: {column_id}")
        imported_lines = {}
        for line in reviewed_column["lines"]:
            line_id = line["id"]
            if line_id in reviewed_ids:
                raise SystemExit(f"duplicate line: {line_id}")
            reviewed_ids.add(line_id)
            if line.get("observed_text") is None and not geometry_only_review:
                raise SystemExit(f"missing independent reading: {line_id}")
            if line.get("match") not in {"strong", "partial", "mismatch", "unreadable"}:
                raise SystemExit(f"invalid match value: {line_id}")
            if line.get("assessment") not in {"readable", "uncertain"}:
                raise SystemExit(f"invalid assessment value: {line_id}")
            crop = line["crop"]
            context = line["context_crop"]
            for name, rectangle in (("crop", crop), ("context_crop", context)):
                if len(rectangle) != 4 or not all(isinstance(value, int) for value in rectangle):
                    raise SystemExit(f"invalid {name}: {line_id}")
                x, y, rectangle_width, rectangle_height = rectangle
                if (
                    min(x, y, rectangle_width, rectangle_height) < 0
                    or x + rectangle_width > width
                    or y + rectangle_height > height
                ):
                    raise SystemExit(f"out-of-bounds {name}: {line_id}")
            if not contains(context, crop):
                raise SystemExit(f"context does not contain crop: {line_id}")
            imported_lines[line_id] = {
                "centre_y": line["centre_y"],
                "crop": crop,
                "context_crop": context,
            }
        page["columns"][column_id]["lines"] = imported_lines
        page["columns"][column_id]["visual_review"] = args.visual_review
        page["columns"][column_id]["reviewed_at"] = args.reviewed_at
        page["columns"][column_id]["review_source"] = str(review_path.relative_to(root))

    if reviewed_ids != expected_ids:
        missing = sorted(expected_ids - reviewed_ids)
        extra = sorted(reviewed_ids - expected_ids)
        raise SystemExit(f"line-ID mismatch; missing={missing}, extra={extra}")

    args.geometry.write_text(
        json.dumps(geometry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Imported {len(reviewed_ids)} reviewed rectangles for {page_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
