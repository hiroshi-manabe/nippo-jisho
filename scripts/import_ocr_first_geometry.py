#!/usr/bin/env python3
"""Import a complete, audited OCR-first geometry proposal into project data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROPOSAL = ROOT / ".cache" / "ocr-first-geometry-v1" / "aligned" / "line-geometry.json"
DEFAULT_REPORT = ROOT / ".cache" / "ocr-first-geometry-v1" / "aligned" / "report.json"
GEOMETRY = ROOT / "pilot" / "human-review" / "line-geometry.json"
CALIBRATION = ROOT / "pilot" / "human-review" / "line-calibration.json"
TILES = ROOT / "pilot" / "tile-config-v1-trial.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_pretty(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_compact_pages(path: Path, value: dict) -> None:
    """Preserve line-calibration.json's one-page-per-line review format."""
    keys = [key for key in value if key != "pages"]
    lines = ["{"]
    for key in keys:
        lines.append(
            f"  {json.dumps(key)}: "
            f"{json.dumps(value[key], ensure_ascii=False, separators=(',', ':'))},"
        )
    lines.append('  "pages": [')
    for index, page in enumerate(value["pages"]):
        suffix = "," if index + 1 < len(value["pages"]) else ""
        lines.append(
            "    "
            + json.dumps(page, ensure_ascii=False, separators=(",", ":"))
            + suffix
        )
    lines.extend(["  ]", "}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rectangle_is_valid(rectangle: object, source_size: list[int]) -> bool:
    if (
        not isinstance(rectangle, list)
        or len(rectangle) != 4
        or any(not isinstance(value, int) for value in rectangle)
    ):
        return False
    x, y, width, height = rectangle
    return (
        x >= 0
        and y >= 0
        and width > 0
        and height > 0
        and x + width <= source_size[0]
        and y + height <= source_size[1]
    )


def box_is_valid(box: object, source_size: list[int]) -> bool:
    if (
        not isinstance(box, list)
        or len(box) != 4
        or any(not isinstance(value, int) for value in box)
    ):
        return False
    left, top, right, bottom = box
    return (
        0 <= left < right <= source_size[0]
        and 0 <= top < bottom <= source_size[1]
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--pages", nargs="+", type=int, required=True)
    result.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    result.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    result.add_argument("--reviewed-at", required=True)
    result.add_argument(
        "--accept-conflict",
        action="append",
        default=[],
        metavar="PAGE_ID/LINE_ID",
        help="scan-confirmed neighbor warning allowed during this import",
    )
    result.add_argument("--apply", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    page_ids = [f"bnf-f{number:04d}" for number in args.pages]
    accepted_conflicts = set(args.accept_conflict)
    proposal = load(args.proposal)
    report = load(args.report)
    geometry = load(GEOMETRY)
    calibration = load(CALIBRATION)
    tiles = load(TILES)
    proposals = {page["id"]: page for page in proposal["pages"]}
    geometry_pages = {page["id"]: page for page in geometry["pages"]}
    calibration_pages = {page["id"]: page for page in calibration["pages"]}
    tile_pages = {page["id"]: page for page in tiles["pages"]}

    report_conflicts = set()
    for page_id in page_ids:
        result = report["results"].get(page_id)
        if result is None:
            raise SystemExit(f"missing report page: {page_id}")
        if result["matched"] != result["targets"] or result["unmatched_targets"]:
            raise SystemExit(f"incomplete OCR-first alignment: {page_id}")
        report_conflicts.update(
            f"{page_id}/{conflict['line_id']}"
            for conflict in result.get("neighbor_conflicts", [])
        )
    unaccepted = report_conflicts - accepted_conflicts
    unknown_accepts = accepted_conflicts - report_conflicts
    if unaccepted:
        raise SystemExit(
            "unaccepted OCR-to-neighbor conflicts: " + ", ".join(sorted(unaccepted))
        )
    if unknown_accepts:
        raise SystemExit(
            "accepted conflicts are not present in the report: "
            + ", ".join(sorted(unknown_accepts))
        )

    changed_lines = 0
    for page_id in page_ids:
        proposed = proposals.get(page_id)
        current = geometry_pages.get(page_id)
        if proposed is None or current is None:
            raise SystemExit(f"missing geometry page: {page_id}")
        if proposed["source_size"] != current["source_size"]:
            raise SystemExit(f"source-size mismatch: {page_id}")
        calibration_page = calibration_pages[page_id]
        tile_page = tile_pages[page_id]
        tile_zones = {zone["id"]: zone for zone in tile_page["zones"]}
        for column_id, proposed_column in proposed["columns"].items():
            current_column = current["columns"][column_id]
            if set(proposed_column["lines"]) != set(current_column["lines"]):
                raise SystemExit(f"line-id mismatch: {page_id}/{column_id}")
            if not box_is_valid(proposed_column["box"], current["source_size"]):
                raise SystemExit(f"invalid column box: {page_id}/{column_id}")
            for line_id, line in proposed_column["lines"].items():
                if not rectangle_is_valid(line["crop"], current["source_size"]):
                    raise SystemExit(f"invalid crop: {page_id}/{line_id}")
                if not rectangle_is_valid(line["context_crop"], current["source_size"]):
                    raise SystemExit(f"invalid context crop: {page_id}/{line_id}")

            proposed_column["visual_review"] = "contact_sheet_reviewed"
            proposed_column["reviewed_at"] = args.reviewed_at
            proposed_column["geometry_method"] = "blind_segmentation_ocr_alignment"
            current["columns"][column_id] = proposed_column
            tile_zones[column_id]["box"] = list(proposed_column["box"])

            calibration_column = calibration_page["columns"][column_id]
            lines = proposed_column["lines"]
            line_ids = list(lines)
            calibration_column["projection_snap"] = False
            calibration_column["ranges"] = [
                [
                    line_ids[0],
                    line_ids[-1],
                    lines[line_ids[0]]["centre_y"],
                    lines[line_ids[-1]]["centre_y"],
                ]
            ]
            calibration_column["centre_overrides"] = {
                line_id: line["centre_y"] for line_id, line in lines.items()
            }
            calibration_column.pop("crop_overrides", None)
            calibration_column["review_state"] = "contact_sheet_reviewed"
            calibration_column["reviewed_at"] = args.reviewed_at
            changed_lines += len(lines)

    print(
        f"Validated {changed_lines} lines on {len(page_ids)} pages; "
        f"accepted {len(report_conflicts)} scan-confirmed OCR warnings."
    )
    if args.apply:
        write_pretty(GEOMETRY, geometry)
        write_compact_pages(CALIBRATION, calibration)
        write_pretty(TILES, tiles)
        print("Updated canonical geometry, calibration, and tile configuration.")
    else:
        print("Dry run only; pass --apply to write project data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
