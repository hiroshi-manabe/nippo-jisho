#!/usr/bin/env python3
"""Build short-line rescue crops directly from canonical neighbour positions."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random

import numpy as np
from PIL import Image

from build_clean_ocr_pairs import (
    GEOMETRY_PATH,
    HIGH_RECALL_OUTPUT,
    ROOT,
    SCANS,
    audit_sheet,
    normalized_line,
    write_json,
)
from build_ocr_dataset import load_json


DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "positional-rescue-v1"
HARD_GEOMETRY_REASONS = {
    "duplicate_geometry",
    "irregular_local_spacing",
    "implausible_crop_height",
}


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def ordinary_geometry(record: dict) -> bool:
    metrics = record.get("metrics", {})
    skew = metrics.get("skew_degrees")
    residual = metrics.get("skew_residual")
    return (
        skew is not None
        and abs(skew) <= 1.2
        and (residual is None or residual <= 10)
        and not HARD_GEOMETRY_REASONS.intersection(record.get("reasons", []))
    )


def trim_target_horizontal(line: Image.Image, padding: int = 12) -> Image.Image:
    """Keep the strongest central-row ink cluster, excluding column rules."""
    pixels = np.asarray(line.convert("L"))
    top = max(0, line.height // 6)
    bottom = min(line.height, line.height - line.height // 6)
    band = pixels[top:bottom]
    counts = np.count_nonzero(band < 100, axis=0)
    active = np.flatnonzero((counts >= 2) & (counts <= band.shape[0] * 0.75))
    if not active.size:
        return line

    runs: list[tuple[int, int]] = []
    start = previous = int(active[0])
    for column in active[1:]:
        column = int(column)
        if column > previous + 1:
            runs.append((start, previous + 1))
            start = column
        previous = column
    runs.append((start, previous + 1))

    clusters: list[tuple[int, int]] = []
    for start, stop in runs:
        if clusters and start - clusters[-1][1] <= 56:
            clusters[-1] = (clusters[-1][0], stop)
        else:
            clusters.append((start, stop))
    start, stop = max(
        clusters,
        key=lambda bounds: int(counts[bounds[0] : bounds[1]].sum()),
    )
    left = max(0, start - padding)
    right = min(line.width, stop + padding)
    if right - left < 32:
        return line
    return line.crop((left, 0, right, line.height))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", type=Path, default=HIGH_RECALL_OUTPUT)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--maximum-text-length", type=int, default=12)
    result.add_argument("--vertical-padding", type=int, default=6)
    result.add_argument("--height", type=int, default=48)
    result.add_argument("--max-width", type=int, default=1024)
    result.add_argument("--audit-lines", type=int, default=100)
    result.add_argument("--seed", type=int, default=20260831)
    return result


def main() -> int:
    args = parser().parse_args()
    accepted_records = load_jsonl(args.dataset / "aligned-pairs.jsonl")
    accepted_ids = {record["id"] for record in accepted_records}
    rejected_records = load_jsonl(args.dataset / "alignment-rejected.jsonl")
    targets = {
        record["id"]: record for record in rejected_records if record.get("text")
    }
    targets.update(
        {
            record["id"]: record
            for record in accepted_records
            if record.get("quality_tier") == "positionally-anchored"
        }
    )
    raw = load_jsonl(args.dataset / "pairs.jsonl") + load_jsonl(
        args.dataset / "rejected.jsonl"
    )
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for record in raw:
        groups[(record["page_id"], record["column"], record["block"])].append(
            record
        )
    for group in groups.values():
        group.sort(key=lambda record: record["block_index"])

    geometry = {page["id"]: page for page in load_json(GEOMETRY_PATH)["pages"]}
    proposals: list[tuple[dict, dict, dict, dict]] = []
    for group in groups.values():
        for index, current in enumerate(group):
            target = targets.get(current["id"])
            if (
                target is None
                or len(target["text"]) > args.maximum_text_length
                or index == 0
                or index + 1 == len(group)
                or not ordinary_geometry(current)
            ):
                continue
            previous = group[index - 1]
            following = group[index + 1]
            if (
                previous["id"] not in accepted_ids
                or following["id"] not in accepted_ids
            ):
                continue
            proposals.append((previous, current, following, target))

    by_page: dict[str, list[tuple[dict, dict, dict, dict]]] = defaultdict(list)
    for proposal in proposals:
        by_page[proposal[1]["page_id"]].append(proposal)
    candidates = []
    for page_id, page_proposals in by_page.items():
        page_number = int(page_id[-4:])
        page_geometry = geometry[page_id]
        with Image.open(SCANS / f"f{page_number:04d}.jpg") as scan:
            for previous, current, following, target in page_proposals:
                column = page_geometry["columns"][current["column"]]
                previous_geometry = column["lines"][previous["line_id"]]
                current_geometry = column["lines"][current["line_id"]]
                following_geometry = column["lines"][following["line_id"]]
                x, _, width, _ = current_geometry["crop"]
                top = max(
                    0,
                    round(
                        (previous_geometry["centre_y"] + current_geometry["centre_y"])
                        / 2
                    )
                    - args.vertical_padding,
                )
                bottom = min(
                    scan.height,
                    round(
                        (current_geometry["centre_y"] + following_geometry["centre_y"])
                        / 2
                    )
                    + args.vertical_padding
                    + 1,
                )
                image = normalized_line(
                    scan.crop((x, top, x + width, bottom)),
                    height=args.height,
                    max_width=args.max_width,
                )
                image = trim_target_horizontal(image)
                relative = (
                    Path("images") / page_id / f"{current['line_id']}.png"
                )
                output_path = args.output / relative
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(output_path, format="PNG", optimize=True)
                target_fields = {
                    key: target[key]
                    for key in (
                        "id",
                        "page_id",
                        "line_id",
                        "column",
                        "block",
                        "block_index",
                        "split",
                        "text",
                        "review_crop",
                    )
                    if key in target
                }
                candidates.append(
                    {
                        **target_fields,
                        "image": relative.as_posix(),
                        "source_crop": [x, top, width, bottom - top],
                        "isolation_window": [x, top, width, bottom - top],
                        "metrics": {
                            "method": "native midpoint crop",
                            "previous_anchor": previous["id"],
                            "following_anchor": following["id"],
                            "recorded_centre_y": current_geometry["centre_y"],
                            "source_geometry_metrics": current.get("metrics", {}),
                        },
                        "quality_flags": [],
                        "width": image.width,
                        "height": image.height,
                        "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
                        "source_candidate_id": f"{current['id']}:native-midpoint",
                        "candidate_reason": "short-clean-between-accepted-neighbours",
                    }
                )
    candidates.sort(
        key=lambda record: (
            record["page_id"],
            record["column"],
            record["block"],
            record["block_index"],
        )
    )
    args.output.mkdir(parents=True, exist_ok=True)
    candidates_path = args.output / "candidates.jsonl"
    with candidates_path.open("w", encoding="utf-8") as stream:
        for record in candidates:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    rng = random.Random(args.seed)
    audit = rng.sample(candidates, min(args.audit_lines, len(candidates)))
    for index in range(0, len(audit), 20):
        audit_sheet(
            [
                {**record, "reasons": ["native midpoint crop"]}
                for record in audit[index : index + 20]
            ],
            args.output / "audit" / f"sample-{index // 20 + 1}.png",
            dataset_root=args.output,
            title=f"Positional rescue audit {index + 1}-{index + 20}",
        )
    summary = {
        "format": "nippo-positional-rescue-candidates",
        "format_version": 1,
        "candidate_count": len(candidates),
        "candidates_sha256": hashlib.sha256(
            candidates_path.read_bytes()
        ).hexdigest(),
        "criteria": {
            "maximum_text_length": args.maximum_text_length,
            "maximum_absolute_skew_degrees": 1.2,
            "maximum_skew_residual_pixels": 10,
            "accepted_immediate_target_neighbours_required": True,
            "crop": "native scan between neighbour-centre midpoints",
            "vertical_padding": args.vertical_padding,
        },
        "audit": {
            "seed": args.seed,
            "sample_size": len(audit),
            "sample_ids": [record["id"] for record in audit],
        },
    }
    write_json(args.output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
