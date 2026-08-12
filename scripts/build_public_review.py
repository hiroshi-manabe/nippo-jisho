#!/usr/bin/env python3
"""Build the static, IIIF-backed Nippo Jisho public review site."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import subprocess

import markdown


ARK = "ark:/12148/bpt6k852354j"
IMAGE_BASE_URL = "https://nippo-jisho-images.pages.dev"
REVIEW_UNITS = ("column-1", "column-2", "furniture")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_commit(root: Path) -> str:
    override = os.environ.get("GITHUB_SHA")
    if override:
        return override
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


def tile_configuration(path: Path) -> dict[str, dict]:
    config = load_json(path)
    result: dict[str, dict] = {}
    for page in config["pages"]:
        result[page["id"]] = {zone["id"]: zone for zone in page["zones"]}
    return result


def line_crop(
    box: list[int],
    span: list[float],
    index: int,
    count: int,
    override: dict | None,
) -> tuple[list[int], list[int]]:
    left, top, right, bottom = box
    height = bottom - top
    first, last = span
    if count == 1:
        center = top + height / 2
        step = height / 20
    else:
        center = top + height * (first + index / (count - 1) * (last - first)) / 100
        step = height * (last - first) / 100 / (count - 1)
    override = override or {}
    above = float(override.get("top_steps", 0.78))
    below = float(override.get("bottom_steps", 0.70))
    crop_top = max(top, round(center - step * above))
    crop_bottom = min(bottom, round(center + step * below))
    context_top = max(top, round(center - step * 2.6))
    context_bottom = min(bottom, round(center + step * 2.6))
    return (
        [left, crop_top, right - left, crop_bottom - crop_top],
        [left, context_top, right - left, context_bottom - context_top],
    )


def transcription_line_data(line: dict) -> dict:
    return {
        "id": line["id"],
        "text": line["text"],
        "runs": [
            {
                key: run[key]
                for key in ("typeface", "text", "layout", "line_span")
                if key in run
            }
            for run in line["runs"]
        ],
    }


def content_hash(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def transcription_version(zones: list[dict]) -> str:
    """Hash only the ordered text and style information a correction targets."""
    return content_hash(
        [transcription_line_data(line) for zone in zones for line in zone["lines"]]
    )


def processed_page(page: dict, config: dict, review: dict, geometry: dict) -> dict:
    columns = geometry.get("columns", {})
    if not columns:
        raise RuntimeError(f"missing reviewed geometry for {page['id']}")
    unreviewed = [
        column_id
        for column_id, column in columns.items()
        if column.get("visual_review")
        not in {
            "contact_sheet_reviewed",
            "captured_during_transcription",
            "ai_line_by_line_checked",
            "line_by_line_reverified",
            "text_image_sanity_checked",
        }
    ]
    if unreviewed:
        raise RuntimeError(
            f"unreviewed geometry for {page['id']}: {', '.join(unreviewed)}"
        )
    explicit_lines = {
        line_id: line_geometry
        for column in columns.values()
        for line_id, line_geometry in column.get("lines", {}).items()
    }
    zones = []
    for zone in page["zones"]:
        output_zone = {
            "id": zone["id"],
            "kind": zone["kind"],
            "label": zone.get("label", zone["id"]),
            "lines": [],
        }
        zone_config = config.get(zone["id"], {})
        box = zone_config.get("box")
        span = zone_config.get("line_span_percent", [5.8, 95.8])
        overrides = zone_config.get("line_crop_overrides", {})
        for index, line in enumerate(zone.get("lines", [])):
            output_line = {
                "id": line["id"],
                "indent": line.get("indent", 0),
                "runs": line["runs"],
                "text": "".join(run["text"] for run in line["runs"]),
            }
            output_line["transcription_version"] = content_hash(
                transcription_line_data(output_line)
            )
            if zone["kind"] == "column":
                if line["id"] not in explicit_lines:
                    raise RuntimeError(f"missing explicit geometry for {page['id']}/{line['id']}")
                output_line["crop"] = explicit_lines[line["id"]]["crop"]
                output_line["context_crop"] = explicit_lines[line["id"]]["context_crop"]
            output_zone["lines"].append(output_line)
        zones.append(output_zone)
    return {
        "processed": True,
        "status": page["review"]["status"],
        "transcription_version": transcription_version(zones),
        "printed_page": next(
            (
                run["text"].strip()
                for zone in page["zones"]
                if zone["kind"] == "running_header"
                for line in zone.get("lines", [])
                for run in line["runs"]
                if run["text"].strip().isdigit()
            ),
            None,
        ),
        "zones": zones,
        "review": review,
    }


def render_reference(source: Path, title: str) -> str:
    body = markdown.markdown(
        source.read_text(encoding="utf-8"), extensions=["tables", "sane_lists"]
    )
    body = body.replace('href="historical-language-notes.md"', 'href="historical-notes.html"')
    body = body.replace('href="transcription-cheat-sheet.md"', 'href="cheat-sheet.html"')
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>{html.escape(title)}</title><link rel='stylesheet' href='reference.css'></head><body>{body}</body></html>"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "build" / "human-review")
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", "hiroshi-manabe/nippo-jisho"),
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    commit = git_commit(root)
    image_records = load_json(root / "pilot/human-review/page-images.json")["pages"]
    config = tile_configuration(root / "pilot/tile-config-v1-trial.json")
    review_record = load_json(root / "pilot/human-review/review-status.json")
    reviews = {page["id"]: page["units"] for page in review_record["pages"]}
    correction_record = load_json(root / "pilot/human-review/correction-history.json")
    corrections = {page["id"]: page for page in correction_record["pages"]}
    geometry_record = load_json(root / "pilot/human-review/line-geometry.json")
    geometries = {page["id"]: page for page in geometry_record["pages"]}
    level1_dir = root / "pilot/format-v1-trial/level1"
    pages = []
    for image_record in image_records:
        leaf = image_record["leaf"]
        view = f"f{leaf}"
        page_id = f"bnf-f{leaf:04d}"
        page = {
            **image_record,
            "view": view,
            "page_id": page_id,
            "thumbnail": f"assets/thumbnails/f{leaf:04d}.webp",
            "iiif_preview": f"{IMAGE_BASE_URL}/scans/1000/f{leaf:04d}.jpg",
            "iiif": f"{IMAGE_BASE_URL}/scans/2200/f{leaf:04d}.jpg",
            "iiif_highres": f"{IMAGE_BASE_URL}/scans/native/f{leaf:04d}.jpg",
            "gallica": f"https://gallica.bnf.fr/{ARK}/{view}.item",
            "corrections": corrections.get(
                page_id,
                {"id": page_id, "issues_applied": 0, "distinct_lines": 0},
            ),
        }
        source = level1_dir / f"{page_id}.json"
        if source.exists():
            page.update(
                processed_page(
                    load_json(source),
                    config.get(page_id, {}),
                    reviews.get(page_id, {}),
                    geometries.get(page_id, {}),
                )
            )
            page["source"] = f"https://github.com/{args.repository}/blob/{commit}/pilot/format-v1-trial/level1-source/{page_id}.md"
        else:
            page.update(
                {
                    "processed": False,
                    "status": "unprocessed",
                    "printed_page": None,
                    "zones": [],
                    "review": {},
                    "source": None,
                    "transcription_version": None,
                }
            )
        pages.append(page)
    payload = {
        "format": "nippo-public-review-corpus",
        "format_version": 1,
        "repository": args.repository,
        "commit": commit,
        "reference_version": commit[:7],
        "pages": pages,
    }
    (output / "corpus.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    for name in ("index.html", "app.js", "styles.css", "reference.css", ".nojekyll"):
        shutil.copy2(root / "site" / name, output / name)
    shutil.copytree(root / "site/assets", output / "assets")
    reference_dir = output / "reference"
    reference_dir.mkdir()
    (reference_dir / "cheat-sheet.html").write_text(
        render_reference(root / "docs/transcription-cheat-sheet.md", "Transcription Cheat Sheet"),
        encoding="utf-8",
    )
    (reference_dir / "historical-notes.html").write_text(
        render_reference(root / "docs/historical-language-notes.md", "Historical Language Notes"),
        encoding="utf-8",
    )
    print(f"Built {len(pages)} leaves at {output}; commit {commit[:7]}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
