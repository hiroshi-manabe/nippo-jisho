#!/usr/bin/env python3
"""Prepare reversible terminal-hyphen suggestions from locally aligned OCR."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PAGE_FROM_SOURCE = re.compile(r"(bnf-f\d{4})/([^/]+)\.png$")
TERMINAL_CONFUSIONS = ".,;&"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for row, left_character in enumerate(left, 1):
        current = [row]
        for column, right_character in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def similarity(source_without_hyphen: str, recognized: str) -> float:
    recognized = recognized.strip().rstrip(TERMINAL_CONFUSIONS)
    length = max(len(source_without_hyphen), len(recognized), 1)
    return 1 - edit_distance(source_without_hyphen, recognized) / length


def page_lines(page: dict) -> dict[str, str]:
    return {
        line["id"]: "".join(run["text"] for run in line["runs"]).strip()
        for zone in page["zones"]
        for line in zone.get("lines", [])
    }


def rectangular_outputs(directory: Path, leaf: int) -> dict[str, str]:
    path = directory / f"f{leaf:04d}.json"
    if not path.exists():
        return {}
    return {record["line_id"]: record["text"] for record in load_json(path)}


def isolated_outputs(path: Path) -> dict[tuple[str, str], str]:
    result = {}
    for record in load_json(path):
        match = PAGE_FROM_SOURCE.search(record.get("source", ""))
        if match:
            result[(match.group(1), match.group(2))] = record["text"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--last", type=int, required=True)
    parser.add_argument("--rectangular-dir", type=Path, required=True)
    parser.add_argument("--isolated-recognition", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.65)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "pilot" / "human-review" / "ocr-hyphen-suggestions.json",
    )
    args = parser.parse_args()
    isolated = isolated_outputs(args.isolated_recognition)
    pages = []
    for leaf in range(args.first, args.last + 1):
        page_id = f"bnf-f{leaf:04d}"
        source = load_json(ROOT / "pilot" / "format-v1-trial" / "level1" / f"{page_id}.json")
        lines = page_lines(source)
        rectangular = rectangular_outputs(args.rectangular_dir, leaf)
        suggestions = []
        for line_id, text in lines.items():
            if not text.endswith("-"):
                continue
            evidence = []
            for route, recognized in (
                ("canonical_review_crop", rectangular.get(line_id)),
                ("isolated_conservative_crop", isolated.get((page_id, line_id))),
            ):
                if not recognized:
                    continue
                score = similarity(text[:-1], recognized)
                evidence.append(
                    {
                        "route": route,
                        "recognized": recognized,
                        "similarity": round(score, 4),
                        "terminal_hyphen": recognized.rstrip().endswith("-"),
                    }
                )
            qualifying = [
                item
                for item in evidence
                if not item["terminal_hyphen"] and item["similarity"] >= args.threshold
            ]
            if qualifying:
                suggestions.append(
                    {
                        "line": line_id,
                        "kind": "ocr_terminal_hyphen",
                        "source_text": text,
                        "suggested_after": text[:-1],
                        "evidence": evidence,
                    }
                )
        pages.append({"id": page_id, "suggestions": suggestions})
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    result = {
        "format": "nippo-ocr-hyphen-suggestions",
        "format_version": 1,
        "generated_from_commit": commit,
        "page_range": [args.first, args.last],
        "minimum_local_similarity": args.threshold,
        "policy": (
            "A missing terminal hyphen is proposed only when at least one OCR route "
            "omits it and recognizes the surrounding physical line above the local "
            "similarity threshold. Routes from the same checkpoint are geometry tests, "
            "not independent votes. Every proposal remains reversible human-review data."
        ),
        "pages": pages,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {sum(len(page['suggestions']) for page in pages)} suggestions "
        f"for f{args.first}–f{args.last} to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
