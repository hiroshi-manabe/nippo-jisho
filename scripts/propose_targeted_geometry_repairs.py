#!/usr/bin/env python3
"""Build targeted per-line geometry repairs from archived OCR evidence."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from build_ocr_dataset import load_json, write_json
from propose_geometry_from_ocr_layout import proposal_page, render_page


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT = ROOT / ".cache/f013-f237-current-geometry-audit.json.gz"
DEFAULT_OUTPUT = ROOT / "pilot/ocr-layout-evidence/v1/campaign-systematic-offset-repair"
GEOMETRY = ROOT / "pilot/human-review/line-geometry.json"
LEVEL1 = ROOT / "pilot/format-v1-trial/level1"


def large_initial_lines(page_id: str) -> set[str]:
    page = load_json(LEVEL1 / f"{page_id}.json")
    return {
        line["id"]
        for zone in page.get("zones", [])
        for line in zone.get("lines", [])
        if any(run.get("layout") == "large-initial" for run in line.get("runs", []))
    }


def load_gzip(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))


def parse_target(value: str) -> tuple[str, str]:
    try:
        page, column = value.split(":", 1)
        number = int(page.removeprefix("bnf-f").removeprefix("f"))
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("target must look like f109:column-1") from error
    if column not in {"column-1", "column-2"}:
        raise argparse.ArgumentTypeError("column must be column-1 or column-2")
    return f"bnf-f{number:04d}", column


def interpolated_line(
    line_id: str,
    index: int,
    ordered_ids: list[str],
    matched: dict[str, dict],
    current_line: dict,
) -> dict:
    before = next(
        (matched[ordered_ids[position]] for position in range(index - 1, -1, -1)
         if ordered_ids[position] in matched),
        None,
    )
    after = next(
        (matched[ordered_ids[position]] for position in range(index + 1, len(ordered_ids))
         if ordered_ids[position] in matched),
        None,
    )
    if before and after:
        before_index = ordered_ids.index(before["line_id"])
        after_index = ordered_ids.index(after["line_id"])
        ratio = (index - before_index) / (after_index - before_index)
        centre = round(before["ocr_centre_y"] + ratio * (after["ocr_centre_y"] - before["ocr_centre_y"]))
    elif before:
        centre = round(before["ocr_centre_y"] + 62 * (index - ordered_ids.index(before["line_id"])))
    elif after:
        centre = round(after["ocr_centre_y"] - 62 * (ordered_ids.index(after["line_id"]) - index))
    else:
        raise ValueError(f"cannot interpolate {line_id}: no matched neighbors")
    left, _, width, _ = current_line["crop"]
    return {
        "candidate_id": "interpolated-between-ocr-matches",
        "centre_delta": centre - current_line["centre_y"],
        "column": "",
        "current_centre_y": current_line["centre_y"],
        "current_crop": current_line["crop"],
        "detected_bbox": [left, centre - 48, width, 96],
        "flags": ["interpolated_unmatched_target"],
        "line_id": line_id,
        "neighbor_margin": None,
        "ocr_centre_y": centre,
        "ocr_crop": [left, centre - 36, width, 72],
        "overflow": {"bottom": 0, "left": 0, "right": 0, "top": 0},
        "positional_rescue": True,
        "recognition": None,
        "relaxed_cer": None,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--target", action="append", type=parse_target, required=True)
    result.add_argument("--render", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    audit = {page["id"]: page for page in load_gzip(args.audit)["pages"]}
    current = {page["id"]: page for page in load_json(GEOMETRY)["pages"]}
    proposals: dict[str, dict] = {}
    interpolations: list[dict] = []
    for page_id, column in args.target:
        current_column = current[page_id]["columns"][column]
        ordered_ids = list(current_column["lines"])
        matched = {
            line["line_id"]: dict(line)
            for line in audit[page_id]["lines"]
            if line["column"] == column
        }
        complete_lines = []
        for index, line_id in enumerate(ordered_ids):
            line = matched.get(line_id)
            if line is None:
                line = interpolated_line(
                    line_id, index, ordered_ids, matched, current_column["lines"][line_id]
                )
                line["column"] = column
                interpolations.append({"id": page_id, "column": column, "line": line_id})
            complete_lines.append(line)
        partial = proposal_page({"id": page_id, "lines": complete_lines}, current[page_id])
        proposed_column = partial["columns"][column]

        # Preserve provenance for earlier horizontal and line-by-line reviews,
        # while making it explicit that the replacement vertical geometry has
        # received the newer targeted contact-sheet review.
        for key in ("review_source", "horizontal_completeness_review"):
            if key in current_column:
                proposed_column[key] = current_column[key]
        proposed_column["prior_visual_review"] = current_column.get("visual_review")
        proposed_column["visual_review"] = "targeted_ocr_contact_sheet_reviewed"

        # Enlarged initials span physical rows.  A single OCR baseline must not
        # collapse a manually verified multi-row glyph crop.
        for line_id in large_initial_lines(page_id):
            if line_id not in proposed_column["lines"]:
                continue
            old_line = current_column["lines"][line_id]
            new_line = proposed_column["lines"][line_id]
            left, _, right, _ = proposed_column["box"]
            for field in ("crop", "context_crop"):
                _, top, _, height = old_line[field]
                new_line[field] = [left, top, right - left, height]
        if page_id not in proposals:
            proposals[page_id] = {
                "id": page_id,
                "source_size": current[page_id]["source_size"],
                "columns": {},
            }
        proposals[page_id]["columns"][column] = proposed_column

    pages = list(proposals.values())
    if args.render:
        for page in pages:
            render_page(page, args.output / "contact-sheets")
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output / "line-geometry.json",
        {
            "format": "nippo-line-geometry-proposal",
            "format_version": 1,
            "method": "targeted-preserved-ocr-layout-v1-alignment",
            "pages": pages,
        },
    )
    write_json(
        args.output / "report.json",
        {
            "format": "nippo-targeted-geometry-repair-campaign",
            "format_version": 1,
            "targets": [f"{page}:{column}" for page, column in args.target],
            "proposed_pages": [page["id"] for page in pages],
            "excluded_pages": [],
            "interpolated_lines": interpolations,
            "policy": {
                "canonical_text_modified": False,
                "unmatched_lines_interpolated_only_from_adjacent_matches": True,
                "visual_review_required_before_application": True,
            },
        },
    )
    print(
        f"Proposed {len(args.target)} columns on {len(pages)} pages; "
        f"interpolated {len(interpolations)} unmatched line(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
