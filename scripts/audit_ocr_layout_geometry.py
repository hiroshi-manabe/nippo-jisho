#!/usr/bin/env python3
"""Compare preserved OCR detections with canonical line geometry, without editing it."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import statistics

from align_page_geometry_ocr_first import (
    normalized_distance,
    rescue_sandwiched_gaps,
    sequence_alignment,
)
from build_ocr_dataset import load_json


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "pilot/ocr-layout-evidence/v1"
LEVEL1 = ROOT / "pilot/format-v1-trial/level1"
GEOMETRY = ROOT / "pilot/human-review/line-geometry.json"
OUTPUT = ROOT / "pilot/ocr-layout-evidence/v1/geometry-audit.json.gz"


def read_evidence(identifier: str, root: Path) -> dict:
    path = root / "pages" / f"{identifier}.json.gz"
    return json.loads(gzip.decompress(path.read_bytes()))


def bbox(line: dict) -> list[int]:
    value = line.get("crop")
    if value and len(value) == 4:
        return [round(item) for item in value]
    points = line.get("boundary") or line["baseline"]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
    return [round(left), round(top), max(1, round(right - left)), max(1, round(bottom - top))]


def outside_distance(inner: list[int], outer: list[int]) -> dict[str, int]:
    ix, iy, iw, ih = inner
    ox, oy, ow, oh = outer
    return {
        "left": max(0, ox - ix),
        "top": max(0, oy - iy),
        "right": max(0, ix + iw - (ox + ow)),
        "bottom": max(0, iy + ih - (oy + oh)),
    }


def column_candidates(evidence: dict, column: str) -> list[dict]:
    result = []
    for line in evidence["columns"].get(column, {}).get("lines", []):
        result.append(
            {
                **line,
                "recognition": line.get("text", ""),
                "centre_y": line["centre"][1],
            }
        )
    return sorted(result, key=lambda value: (value["centre_y"], value["centre"][0]))


def targets_for_geometry(page: dict, geometry_page: dict) -> dict[str, list[dict]]:
    """Group stable body IDs by physical column, including split zones."""
    text_by_id = {
        line["id"]: "".join(run["text"] for run in line["runs"]).strip()
        for zone in page["zones"]
        if zone.get("kind") == "column"
        for line in zone.get("lines", [])
    }
    result = {}
    for column, value in geometry_page["columns"].items():
        result[column] = [
            {"id": line_id, "text": text_by_id[line_id], "index": index}
            for index, line_id in enumerate(value["lines"])
            if line_id in text_by_id
        ]
    return result


def align_audit_rows(references, candidates):
    """Allow marginal detections to be skipped without exhausting an index band."""
    return sequence_alignment(
        references, candidates, gap_cost=0.55, position_cost=0.005,
        maximum_displacement=max(len(references), len(candidates)),
    )


def audit_page(number: int, evidence_root: Path, geometry_page: dict) -> dict:
    identifier = f"bnf-f{number:04d}"
    page = load_json(LEVEL1 / f"{identifier}.json")
    evidence = read_evidence(identifier, evidence_root)
    targets = targets_for_geometry(page, geometry_page)
    result = {
        "id": identifier,
        "status": "complete",
        "targets": 0,
        "candidates": 0,
        "matched": 0,
        "unmatched_targets": [],
        "unused_candidates": [],
        "neighbor_conflicts": [],
        "lines": [],
    }
    for column, references in targets.items():
        candidates = column_candidates(evidence, column)
        result["targets"] += len(references)
        result["candidates"] += len(candidates)
        alignment = align_audit_rows(references, candidates)
        alignment, rescues = rescue_sandwiched_gaps(
            alignment, len(references), len(candidates)
        )
        rescue_set = set(rescues)
        current_column = geometry_page["columns"].get(column)
        if current_column is None:
            result["status"] = "structural_review_required"
            result["unmatched_targets"].extend(ref["id"] for ref in references)
            continue
        for reference_index, candidate_index in alignment:
            if reference_index is None:
                result["unused_candidates"].append(candidates[candidate_index]["id"])
                continue
            reference = references[reference_index]
            if candidate_index is None:
                result["unmatched_targets"].append(reference["id"])
                continue
            candidate = candidates[candidate_index]
            current = current_column["lines"].get(reference["id"])
            if current is None:
                result["unmatched_targets"].append(reference["id"])
                continue
            distance = normalized_distance(reference["text"], candidate["recognition"])
            neighbor_distances = [
                normalized_distance(targets[column][index]["text"], candidate["recognition"])
                for index in (reference_index - 1, reference_index + 1)
                if 0 <= index < len(references)
            ]
            neighbor_margin = min(neighbor_distances) - distance if neighbor_distances else None
            conflict = neighbor_margin is not None and neighbor_margin < -0.05
            if conflict:
                result["neighbor_conflicts"].append(reference["id"])
            detected = bbox(candidate)
            overflow = outside_distance(detected, current["crop"])
            centre_delta = round(candidate["centre_y"] - current["centre_y"], 2)
            flags = []
            # Detector polygons and the historical OCR-first importer differ
            # by a harmless two-pixel rounding/padding convention.  Surface
            # only an amount large enough to represent plausible lost ink.
            if overflow["left"] >= 6 or overflow["right"] >= 6:
                flags.append("horizontal_clip")
            if overflow["top"] >= 6 or overflow["bottom"] >= 6:
                flags.append("vertical_clip")
            if abs(centre_delta) >= 20:
                flags.append("centre_disagreement")
            if conflict:
                flags.append("neighbor_conflict")
            if distance > 0.55:
                flags.append("weak_text_alignment")
            result["lines"].append(
                {
                    "column": column,
                    "line_id": reference["id"],
                    "candidate_id": candidate["id"],
                    "recognition": candidate["recognition"],
                    "relaxed_cer": round(distance, 4),
                    "neighbor_margin": round(neighbor_margin, 4) if neighbor_margin is not None else None,
                    "positional_rescue": (reference_index, candidate_index) in rescue_set,
                    "current_crop": current["crop"],
                    "detected_bbox": detected,
                    "ocr_crop": candidate.get("ocr_crop"),
                    "overflow": overflow,
                    "current_centre_y": current["centre_y"],
                    "ocr_centre_y": round(candidate["centre_y"], 2),
                    "centre_delta": centre_delta,
                    "flags": flags,
                }
            )
            result["matched"] += 1
    if result["unmatched_targets"] or result["neighbor_conflicts"]:
        result["status"] = "structural_review_required"
    deltas = [abs(line["centre_delta"]) for line in result["lines"]]
    result["summary"] = {
        "flagged_lines": sum(bool(line["flags"]) for line in result["lines"]),
        "horizontal_clips": sum("horizontal_clip" in line["flags"] for line in result["lines"]),
        "vertical_clips": sum("vertical_clip" in line["flags"] for line in result["lines"]),
        "centre_disagreements": sum("centre_disagreement" in line["flags"] for line in result["lines"]),
        "median_absolute_centre_delta": round(statistics.median(deltas), 2) if deltas else None,
        "maximum_absolute_centre_delta": round(max(deltas), 2) if deltas else None,
    }
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--first", type=int, default=13)
    result.add_argument("--last", type=int, default=237)
    result.add_argument("--evidence", type=Path, default=EVIDENCE)
    result.add_argument("--output", type=Path, default=OUTPUT)
    return result


def main() -> int:
    args = parser().parse_args()
    geometry = {page["id"]: page for page in load_json(GEOMETRY)["pages"]}
    pages = []
    for number in range(args.first, args.last + 1):
        identifier = f"bnf-f{number:04d}"
        if identifier not in geometry or not (LEVEL1 / f"{identifier}.json").exists():
            continue
        pages.append(audit_page(number, args.evidence, geometry[identifier]))
        print(identifier, pages[-1]["status"], pages[-1]["summary"]["flagged_lines"])
    totals = {
        "pages": len(pages),
        "targets": sum(page["targets"] for page in pages),
        "matched": sum(page["matched"] for page in pages),
        "structural_review_pages": sum(page["status"] != "complete" for page in pages),
        "flagged_lines": sum(page["summary"]["flagged_lines"] for page in pages),
        "horizontal_clips": sum(page["summary"]["horizontal_clips"] for page in pages),
        "vertical_clips": sum(page["summary"]["vertical_clips"] for page in pages),
        "centre_disagreements": sum(page["summary"]["centre_disagreements"] for page in pages),
    }
    output = {
        "format": "nippo-ocr-layout-geometry-audit",
        "format_version": 1,
        "range": [args.first, args.last],
        "policy": {
            "canonical_geometry_modified": False,
            "canonical_text_modified": False,
            "ocr_is_correspondence_evidence_not_authority": True,
        },
        "totals": totals,
        "pages": pages,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if args.output.suffix == ".gz":
        args.output.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    else:
        args.output.write_bytes(raw)
    summary_path = args.output.with_name("geometry-audit-summary.json")
    summary_path.write_text(
        json.dumps(
            {
                "format": output["format"] + "-summary",
                "format_version": 1,
                "range": output["range"],
                "totals": totals,
                "pages": [
                    {
                        "id": page["id"],
                        "status": page["status"],
                        **page["summary"],
                        "unmatched_targets": len(page["unmatched_targets"]),
                        "unused_candidates": len(page["unused_candidates"]),
                        "neighbor_conflicts": len(page["neighbor_conflicts"]),
                    }
                    for page in pages
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(totals, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
