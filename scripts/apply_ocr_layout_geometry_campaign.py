#!/usr/bin/env python3
"""Apply conflict-free OCR-layout proposals while retaining pending-review status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_ocr_dataset import load_json, write_json
from import_ocr_first_geometry import write_compact_pages


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "pilot/ocr-layout-evidence/v1/campaign-f0171-f0237/line-geometry.json"
REPORT = ROOT / "pilot/ocr-layout-evidence/v1/campaign-f0171-f0237/report.json"
GEOMETRY = ROOT / "pilot/human-review/line-geometry.json"
CALIBRATION = ROOT / "pilot/human-review/line-calibration.json"
TILES = ROOT / "pilot/tile-config-v1-trial.json"


def valid_xywh(value: object, size: list[int]) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(isinstance(item, (int, float)) for item in value)
        and value[0] >= 0
        and value[1] >= 0
        and value[2] > 0
        and value[3] > 0
        and value[0] + value[2] <= size[0]
        and value[1] + value[3] <= size[1]
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--proposal", type=Path, default=PROPOSAL)
    result.add_argument("--report", type=Path, default=REPORT)
    result.add_argument("--apply", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    proposal = load_json(args.proposal)
    report = load_json(args.report)
    if report["excluded_pages"] and any(
        item["id"] in report["proposed_pages"] for item in report["excluded_pages"]
    ):
        raise SystemExit("a structurally excluded page entered the proposal")
    geometry = load_json(GEOMETRY)
    calibration = load_json(CALIBRATION)
    tiles = load_json(TILES)
    geometry_by_id = {page["id"]: page for page in geometry["pages"]}
    calibration_by_id = {page["id"]: page for page in calibration["pages"]}
    tiles_by_id = {page["id"]: page for page in tiles["pages"]}
    changed_lines = 0
    for proposed in proposal["pages"]:
        identifier = proposed["id"]
        current = geometry_by_id.get(identifier)
        if current is None or proposed["source_size"] != current["source_size"]:
            raise SystemExit(f"missing or incompatible canonical page: {identifier}")
        tile_zones = {zone["id"]: zone for zone in tiles_by_id[identifier]["zones"]}
        for column, value in proposed["columns"].items():
            old = current["columns"].get(column)
            if old is None or set(value["lines"]) != set(old["lines"]):
                raise SystemExit(f"line-ID mismatch: {identifier}/{column}")
            for line_id, line in value["lines"].items():
                if not valid_xywh(line["crop"], current["source_size"]):
                    raise SystemExit(f"invalid crop: {identifier}/{line_id}")
                if not valid_xywh(line["context_crop"], current["source_size"]):
                    raise SystemExit(f"invalid context crop: {identifier}/{line_id}")
            current["columns"][column] = value
            tile_zones[column]["box"] = list(value["box"])
            line_ids = list(value["lines"])
            calibration_column = calibration_by_id[identifier]["columns"][column]
            calibration_column["projection_snap"] = False
            calibration_column["ranges"] = [
                [
                    line_ids[0],
                    line_ids[-1],
                    value["lines"][line_ids[0]]["centre_y"],
                    value["lines"][line_ids[-1]]["centre_y"],
                ]
            ]
            calibration_column["centre_overrides"] = {
                line_id: line["centre_y"] for line_id, line in value["lines"].items()
            }
            calibration_column.pop("crop_overrides", None)
            calibration_column["review_state"] = value["visual_review"]
            calibration_column["geometry_method"] = value["geometry_method"]
            changed_lines += len(value["lines"])
    print(f"Validated {changed_lines} lines on {len(proposal['pages'])} pages")
    if args.apply:
        write_json(GEOMETRY, geometry)
        write_compact_pages(CALIBRATION, calibration)
        write_json(TILES, tiles)
        print("Applied OCR-layout proposals with conservative contact-sheet review status")
    else:
        print("Dry run only; pass --apply to update canonical geometry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
