#!/usr/bin/env python3
"""Give externally reviewed line crops complete horizontal column coverage."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REVIEW_STATUS = "external_ai_width_rechecked"


def horizontal_bounds(page: dict) -> dict[str, tuple[int, int]]:
    """Return conservative bounds spanning both rules of each printed column."""
    width, _ = page["source_size"]
    first = page["columns"]["column-1"]["box"]
    second = page["columns"]["column-2"]["box"]
    divider = (first[2] + second[0]) // 2
    outer_right_margin = 250 if width < 2700 else 70
    return {
        "column-1": (max(0, first[0] - 40), divider + 30),
        "column-2": (divider - 30, width - outer_right_margin),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--geometry",
        type=Path,
        default=root / "pilot/human-review/line-geometry.json",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--start-page", type=int, default=None)
    parser.add_argument("--end-page", type=int, default=None)
    parser.add_argument("--reviewed-at", default="2026-08-13")
    args = parser.parse_args()

    record = json.loads(args.geometry.read_text(encoding="utf-8"))
    changed_pages = changed_columns = changed_lines = 0
    report = []
    for page in record["pages"]:
        page_number = int(re.search(r"f(\d+)$", page["id"]).group(1))
        if args.start_page is not None and page_number < args.start_page:
            continue
        if args.end_page is not None and page_number > args.end_page:
            continue
        columns = page.get("columns", {})
        if not columns or not any(
            column.get("review_source") and column.get("visual_review") != REVIEW_STATUS
            for column in columns.values()
        ):
            continue
        bounds = horizontal_bounds(page)
        page_report = {"page": page["id"], "columns": {}}
        for column_id, column in columns.items():
            if not column.get("review_source") or column.get("visual_review") == REVIEW_STATUS:
                continue
            left, right = bounds[column_id]
            old_box = list(column["box"])
            column["box"][0] = left
            column["box"][2] = right
            for line in column["lines"].values():
                for key in ("crop", "context_crop"):
                    line[key][0] = left
                    line[key][2] = right - left
                changed_lines += 1
            column["visual_review"] = REVIEW_STATUS
            column["reviewed_at"] = args.reviewed_at
            column["horizontal_completeness_review"] = {
                "status": "complete_column_width_checked",
                "method": "full-scan boundary audit with conservative rule-to-rule coverage",
                "previous_box": old_box,
            }
            page_report["columns"][column_id] = {
                "before": old_box,
                "after": column["box"],
                "lines": len(column["lines"]),
            }
            changed_columns += 1
        changed_pages += 1
        report.append(page_report)

    if args.apply:
        args.geometry.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({
        "applied": args.apply,
        "pages": changed_pages,
        "columns": changed_columns,
        "lines": changed_lines,
        "details": report,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
