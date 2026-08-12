#!/usr/bin/env python3
"""Export reviewed line geometry as an example AI-geometry response."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def content_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def line_version(line: dict) -> str:
    value = {
        "id": line["id"],
        "text": "".join(run["text"] for run in line["runs"]),
        "runs": [
            {
                key: run[key]
                for key in ("typeface", "text", "layout", "line_span")
                if key in run
            }
            for run in line["runs"]
        ],
    }
    return content_hash(value)


def contains(outer: list[int], inner: list[int]) -> bool:
    ox, oy, ow, oh = outer
    ix, iy, iw, ih = inner
    return (
        ox <= ix
        and oy <= iy
        and ox + ow >= ix + iw
        and oy + oh >= iy + ih
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", default="bnf-f0030")
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "pilot/human-review/ai-geometry-examples/bnf-f0030.json",
    )
    args = parser.parse_args()

    page_path = root / f"pilot/format-v1-trial/level1/{args.page}.json"
    page = load_json(page_path)
    geometries = {
        item["id"]: item
        for item in load_json(root / "pilot/human-review/line-geometry.json")["pages"]
    }
    tiles = {
        item["id"]: item
        for item in load_json(root / "pilot/tile-config-v1-trial.json")["pages"]
    }
    geometry = geometries[args.page]
    tile = tiles[args.page]
    zones = {zone["id"]: zone for zone in page["zones"]}
    source_width, source_height = geometry["source_size"]
    source_path = root / ".cache/sources/bnf-gallica/master" / tile["master"]
    actual_source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if actual_source_hash != page["source"]["master_sha256"]:
        raise SystemExit(f"source checksum mismatch: {source_path}")

    result = {
        "format": "nippo-ai-line-geometry-response",
        "format_version": 1,
        "page": args.page,
        "example_status": "reviewed_f30_golden_example",
        "observed_text_provenance": (
            "Copied from the current canonical Level 1 transcription to demonstrate "
            "the expected response shape; unlike future AI responses, these values "
            "are not an independent blind reading."
        ),
        "coordinate_space": "native Gallica master pixels",
        "rectangle_format": "[x, y, width, height]",
        "source": {
            "filename": tile["master"],
            "width": source_width,
            "height": source_height,
            "sha256": actual_source_hash,
            "gallica_url": page["source"]["url"],
        },
        "transcription_source": {
            "page_file": str(page_path.relative_to(root)),
            "page_file_sha256": hashlib.sha256(page_path.read_bytes()).hexdigest(),
        },
        "columns": {},
    }

    for column_id, column_geometry in geometry["columns"].items():
        source_lines = zones[column_id]["lines"]
        output_lines = []
        for line in source_lines:
            line_id = line["id"]
            item = column_geometry["lines"][line_id]
            crop = item["crop"]
            context = item["context_crop"]
            for rectangle in (crop, context):
                x, y, width, height = rectangle
                if min(x, y, width, height) < 0:
                    raise SystemExit(f"negative rectangle value: {args.page}/{line_id}")
                if x + width > source_width or y + height > source_height:
                    raise SystemExit(f"out-of-bounds rectangle: {args.page}/{line_id}")
            if not contains(context, crop):
                raise SystemExit(f"context does not contain crop: {args.page}/{line_id}")
            output_lines.append(
                {
                    "id": line_id,
                    "centre_y": item["centre_y"],
                    "crop": crop,
                    "context_crop": context,
                    "observed_text": "".join(run["text"] for run in line["runs"]),
                    "match": "strong",
                    "assessment": "readable",
                    "expected_line_version": line_version(line),
                }
            )
        if set(column_geometry["lines"]) != {line["id"] for line in source_lines}:
            raise SystemExit(f"geometry and transcription line IDs differ: {column_id}")
        result["columns"][column_id] = {
            "column_box_xyxy": column_geometry["box"],
            "example_geometry_review": column_geometry["visual_review"],
            "example_reviewed_at": column_geometry.get("reviewed_at"),
            "lines": output_lines,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {sum(len(c['lines']) for c in result['columns'].values())} lines "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
