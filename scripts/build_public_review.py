#!/usr/bin/env python3
"""Build the static, IIIF-backed Nippo Jisho public review site."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata

import markdown


ARK = "ark:/12148/bpt6k852354j"
IMAGE_BASE_URL = "https://nippo-jisho-images.pages.dev"
REVIEW_UNITS = ("column-1", "column-2", "furniture")
HYPHEN_AUDIT_LEAVES = range(44, 101)
HYPHEN_AUDIT_SCOPE = "f44-f100"
TILDE_AUDIT_LEAVES = range(39, 101)
TILDE_AUDIT_SCOPE = "f39-f100"
TILDE_AUDIT_STATUS = "batch_review_unverified"


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
            "ai_bulk_geometry_sanity_checked",
            "external_ai_width_rechecked",
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


def hyphen_audit_payload(pages: list[dict], commit: str, repository: str) -> dict:
    audit_pages = []
    for page in pages:
        if page["leaf"] not in HYPHEN_AUDIT_LEAVES or not page["processed"]:
            continue
        candidates = []
        for zone in page["zones"]:
            if zone["kind"] != "column":
                continue
            for line in zone["lines"]:
                if not line["text"].rstrip().endswith("-"):
                    continue
                left, top, width, height = line["crop"]
                crop_width = min(width, 720)
                padding = max(12, round(height * 0.28))
                crop_top = max(0, top - padding)
                crop_bottom = min(page["height"], top + height + padding)
                candidates.append(
                    {
                        "line": line["id"],
                        "before": line["text"],
                        "base_line_version": line["transcription_version"],
                        "crop": [
                            left + width - crop_width,
                            crop_top,
                            crop_width,
                            crop_bottom - crop_top,
                        ],
                    }
                )
        audit_pages.append(
            {
                "leaf": page["leaf"],
                "view": page["view"],
                "page_id": page["page_id"],
                "width": page["width"],
                "height": page["height"],
                "image": page["iiif"],
                "gallica": page["gallica"],
                "candidates": candidates,
            }
        )
    return {
        "schema": 1,
        "task": "line-end-hyphen-audit",
        "scope": HYPHEN_AUDIT_SCOPE,
        "base_commit": commit,
        "repository": repository,
        "pages": audit_pages,
    }


def vowel_unit(character: str) -> tuple[str, str]:
    decomposed = unicodedata.normalize("NFD", character)
    return decomposed[0].lower(), decomposed[1:]


def alternate_tilde_carrier(token: str, marked_index: int) -> str | None:
    """Move one tilde across a maximal adjacent-vowel pair."""
    units = [unicodedata.normalize("NFD", character) for character in token]
    if not (0 <= marked_index < len(units)) or "\N{COMBINING TILDE}" not in units[marked_index]:
        return None
    left = marked_index
    while left and vowel_unit(token[left - 1])[0] in "aeiou":
        left -= 1
    right = marked_index + 1
    while right < len(token) and vowel_unit(token[right])[0] in "aeiou":
        right += 1
    if right - left != 2:
        return None
    if sum("\N{COMBINING TILDE}" in units[index] for index in range(left, right)) != 1:
        return None
    destination = left if marked_index == left + 1 else left + 1
    units[marked_index] = units[marked_index].replace("\N{COMBINING TILDE}", "", 1)
    units[destination] += "\N{COMBINING TILDE}"
    return unicodedata.normalize("NFC", "".join(units))


def text_width_units(value: str) -> float:
    narrow = set(" ilIſft.,:;'|")
    wide = set("MWmw&")
    return sum(0.52 if character in narrow else 1.42 if character in wide else 1.0 for character in value)


def tilde_candidate_crop(page: dict, line: dict, start: int, end: int) -> list[int]:
    if "crop" in line:
        left, top, width, height = line["crop"]
    else:
        # Catchwords are outside the column geometry but consistently occupy
        # the lower-right portion of these leaves.
        left = round(page["width"] * 0.43)
        top = round(page["height"] * 0.84)
        width = page["width"] - left - 40
        height = page["height"] - top - 30
    text = line["text"]
    # Printed continuation lines often occupy only a small part of the
    # column. Normalizing every line to the full column width therefore sends
    # short indented text (for example `ta lũa.`) to the wrong edge. Estimate
    # position using a stable full-line measure and the recorded indentation
    # instead; the generous crop remains intentionally approximate.
    unit_width = width / 48
    indent_units = float(line.get("indent", 0)) * 2.0
    centre = (
        indent_units
        + text_width_units(text[:start])
        + text_width_units(text[start:end]) / 2
    )
    centre_x = left + round(unit_width * centre)
    crop_width = min(width, 720)
    trailing_text = text[end:]
    at_printed_line_end = re.fullmatch(r"[\s.,;:!?]*", trailing_text) is not None
    if at_printed_line_end and text_width_units(text) >= 28:
        # A long line ending at the outer rule is safer to anchor to that rule;
        # the fixed-width estimate otherwise risks losing its final character.
        # Terminal punctuation belongs to the same printed ending even though
        # it is outside the candidate token.
        crop_left = left + width - crop_width
    else:
        crop_left = min(
            max(left, centre_x - crop_width // 2), left + width - crop_width
        )
    # Existing line rectangles were reviewed for readable letter bodies, but
    # this task depends on small marks above them. Preserve extra space above
    # the line and modest overlap below it so a slightly displaced rectangle
    # cannot clip the tilde under review.
    crop_top = max(0, top - max(45, round(height * 0.45)))
    crop_bottom = min(
        page["height"], top + height + max(30, round(height * 0.30))
    )
    return [crop_left, crop_top, crop_width, crop_bottom - crop_top]


def tilde_audit_payload(
    pages: list[dict], commit: str, repository: str, ledger: Path
) -> dict:
    page_lookup = {page["page_id"]: page for page in pages if page["processed"]}
    candidates_by_leaf: dict[int, list[dict]] = {}
    with ledger.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        for row in rows:
            leaf = int(re.search(r"f(\d+)$", row["page"]).group(1))
            if leaf not in TILDE_AUDIT_LEAVES or row["status"] != TILDE_AUDIT_STATUS:
                continue
            page = page_lookup.get(row["page"])
            if page is None:
                continue
            lines = {
                line["id"]: line
                for zone in page["zones"]
                for line in zone.get("lines", [])
            }
            line = lines.get(row["line"])
            if line is None:
                raise RuntimeError(f"missing tilde-audit line {row['page']}/{row['line']}")
            start, end = int(row["token_start"]), int(row["token_end"])
            token = line["text"][start:end]
            if token != row["reviewed_token"]:
                raise RuntimeError(
                    f"stale tilde-audit token {row['page']}/{row['line']} "
                    f"#{row['occurrence']}: {token!r} != {row['reviewed_token']!r}"
                )
            alternate = alternate_tilde_carrier(token, int(row["marked_index"]))
            if alternate is None:
                continue
            candidates_by_leaf.setdefault(leaf, []).append(
                {
                    "line": row["line"],
                    "occurrence": int(row["occurrence"]),
                    "before": token,
                    "after": alternate,
                    "line_text": line["text"],
                    "token_start": start,
                    "token_end": end,
                    "base_line_version": line["transcription_version"],
                    "crop": tilde_candidate_crop(page, line, start, end),
                }
            )
    audit_pages = []
    for leaf in TILDE_AUDIT_LEAVES:
        page = next((page for page in pages if page["leaf"] == leaf), None)
        candidates = candidates_by_leaf.get(leaf, [])
        if page is None or not candidates:
            continue
        audit_pages.append(
            {
                "leaf": leaf,
                "view": page["view"],
                "page_id": page["page_id"],
                "width": page["width"],
                "height": page["height"],
                "image": page["iiif"],
                "gallica": page["gallica"],
                "candidates": candidates,
            }
        )
    return {
        "schema": 1,
        "task": "tilde-carrier-audit",
        "scope": TILDE_AUDIT_SCOPE,
        "base_commit": commit,
        "repository": repository,
        "review_basis": TILDE_AUDIT_STATUS,
        "pages": audit_pages,
    }


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
    (output / "hyphen-audit.json").write_text(
        json.dumps(
            hyphen_audit_payload(pages, commit, args.repository),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "tilde-audit.json").write_text(
        json.dumps(
            tilde_audit_payload(
                pages,
                commit,
                args.repository,
                root / "pilot" / "adjacent-vowel-tilde-audit.tsv",
            ),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    for name in (
        "index.html",
        "app.js",
        "styles.css",
        "reference.css",
        "hyphen-audit.html",
        "hyphen-audit.js",
        "hyphen-audit.css",
        "tilde-audit.html",
        "tilde-audit.js",
        "tilde-audit.css",
        ".nojekyll",
    ):
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
