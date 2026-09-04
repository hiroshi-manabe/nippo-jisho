#!/usr/bin/env python3
"""Build the static, IIIF-backed Nippo Jisho public review site."""

from __future__ import annotations

import argparse
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

try:
    from scripts.kana_reading import reading_hint
except ModuleNotFoundError:  # Direct execution places scripts/ on sys.path.
    from kana_reading import reading_hint


ARK = "ark:/12148/bpt6k852354j"
IMAGE_BASE_URL = "https://nippo-jisho-images.pages.dev"
REVIEW_UNITS = ("column-1", "column-2", "furniture")
REVIEWED_GEOMETRY_STATES = {
    "contact_sheet_reviewed",
    "captured_during_transcription",
    "ai_line_by_line_checked",
    "ai_bulk_geometry_sanity_checked",
    "external_ai_width_rechecked",
    "line_by_line_reverified",
    "text_image_sanity_checked",
}
OCR_PROVISIONAL_GEOMETRY_STATE = "ocr_bootstrap_unreviewed"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_commit(root: Path) -> str:
    override = os.environ.get("GITHUB_SHA")
    if override:
        return override
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


def git_file_revisions(root: Path, paths: list[Path]) -> dict[str, tuple[str, str]]:
    relatives = [path.relative_to(root).as_posix() for path in paths]
    output = subprocess.check_output(
        ["git", "log", "--format=@@%H%x09%cI", "--name-only", "--", *relatives],
        cwd=root,
        text=True,
    )
    revisions: dict[str, tuple[str, str]] = {}
    revision: tuple[str, str] | None = None
    for line in output.splitlines():
        if line.startswith("@@"):
            revision = tuple(line[2:].split("\t", 1))
        elif line and revision and line in relatives and line not in revisions:
            revisions[line] = revision
    missing = sorted(set(relatives) - revisions.keys())
    if missing:
        raise RuntimeError(f"no Git revision found for {', '.join(missing)}")
    return revisions


def embedded_roman_terms(pages: list[dict]) -> list[str]:
    """Words proven upright after italic text in canonical dictionary lines."""
    terms: set[str] = set()
    for page in pages:
        if page.get("data_state") != "canonical_level1":
            continue
        for zone in page.get("zones", []):
            for line in zone.get("lines", []):
                saw_italic = False
                for run in line.get("runs", []):
                    if run["typeface"] == "italic":
                        saw_italic = True
                    elif run["typeface"] == "roman" and saw_italic:
                        terms.update(re.findall(r"[^\W\d_]+", run["text"], re.UNICODE))
    return sorted(term for term in terms if len(term) > 1)


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
        "note": line.get("note", ""),
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
    """Hash the ordered canonical line text, style, and durable notes."""
    return content_hash(
        [transcription_line_data(line) for zone in zones for line in zone["lines"]]
    )


def processed_page(
    page: dict,
    config: dict,
    review: dict,
    geometry: dict,
    machine_suggestions: dict[str, dict],
    *,
    allowed_geometry_states: set[str] | None = None,
) -> dict:
    allowed_geometry_states = allowed_geometry_states or REVIEWED_GEOMETRY_STATES
    columns = geometry.get("columns", {})
    if not columns:
        raise RuntimeError(f"missing reviewed geometry for {page['id']}")
    unreviewed = [
        column_id
        for column_id, column in columns.items()
        if column.get("visual_review") not in allowed_geometry_states
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
            previous_line = zone["lines"][index - 1] if index else None
            previous_runs = previous_line.get("runs", []) if previous_line else []
            current_runs = line.get("runs", [])
            leading_roman_continuation = bool(
                previous_runs
                and current_runs
                and previous_runs[-1].get("typeface") == "roman"
                and current_runs[0].get("typeface") == "roman"
                and previous_runs[-1].get("text", "").rstrip().endswith("-")
            )
            generated_reading = reading_hint(
                current_runs,
                leading_roman_continuation=leading_roman_continuation,
            )
            has_roman_words = any(
                run.get("typeface") == "roman"
                and re.search(r"[A-Za-zÀ-žǍ-ǔſç]", run.get("text", ""))
                for run in line["runs"]
            )
            output_line = {
                "id": line["id"],
                "indent": line.get("indent", 0),
                "runs": line["runs"],
                "text": "".join(run["text"] for run in line["runs"]),
                "reading_hint": generated_reading,
                "reading_hint_status": "available" if generated_reading else ("unavailable" if has_roman_words else "not_applicable"),
                **({"note": line["note"]} if line.get("note") else {}),
            }
            output_line["transcription_version"] = content_hash(
                transcription_line_data(output_line)
            )
            suggestion = machine_suggestions.get(line["id"])
            if (
                suggestion
                and suggestion.get("source_text") == output_line["text"]
                and output_line["text"].endswith("-")
            ):
                output_line["machine_suggestions"] = [suggestion["kind"]]
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


def ocr_candidate_sources(root: Path) -> dict[str, Path]:
    """Return only materialized review candidates, never controls or references."""
    sources: dict[str, Path] = {}
    for directory in (
        root / "pilot" / "ocr-bootstrap" / "f0238-f0247",
        root / "pilot" / "ocr-bootstrap" / "f0251-f0642" / "pages",
    ):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("bnf-f[0-9][0-9][0-9][0-9].json")):
            if path.stem in sources:
                raise RuntimeError(f"duplicate OCR candidate for {path.stem}")
            sources[path.stem] = path
    return sources


def render_reference(source: Path, title: str) -> str:
    body = markdown.markdown(
        source.read_text(encoding="utf-8"), extensions=["tables", "sane_lists"]
    )
    body = body.replace('href="historical-language-notes.md"', 'href="historical-notes.html"')
    body = body.replace('href="transcription-cheat-sheet.md"', 'href="cheat-sheet.html"')
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>{html.escape(title)}</title><link rel='stylesheet' href='../reference.css'></head><body>{body}</body></html>"


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
    suggestion_record = load_json(
        root / "pilot/human-review/ocr-hyphen-suggestions.json"
    )
    machine_suggestions = {
        page["id"]: {
            suggestion["line"]: suggestion for suggestion in page["suggestions"]
        }
        for page in suggestion_record["pages"]
    }
    level1_dir = root / "pilot/format-v1-trial/level1"
    candidate_sources = ocr_candidate_sources(root)
    revision_paths = [
        root / "pilot" / "format-v1-trial" / "level1-source" / source.name.replace(".json", ".md")
        for source in level1_dir.glob("bnf-f*.json")
    ] + list(candidate_sources.values())
    revisions = git_file_revisions(root, revision_paths)
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
            revision_path = root / "pilot" / "format-v1-trial" / "level1-source" / f"{page_id}.md"
            baseline_commit, baseline_updated_at = revisions[revision_path.relative_to(root).as_posix()]
            page.update(
                processed_page(
                    load_json(source),
                    config.get(page_id, {}),
                    reviews.get(page_id, {}),
                    geometries.get(page_id, {}),
                    machine_suggestions.get(page_id, {}),
                )
            )
            page["source"] = f"https://github.com/{args.repository}/blob/{commit}/pilot/format-v1-trial/level1-source/{page_id}.md"
            page.update(
                {
                    "data_state": "canonical_level1",
                    "machine_provisional": False,
                    "source_label": "Source Markdown",
                    "structural_review_required": False,
                    "ai_checked": (root / "pilot" / "production-review" / f"{page_id}.md").exists(),
                    "baseline_commit": baseline_commit,
                    "baseline_updated_at": baseline_updated_at,
                }
            )
        elif page_id in candidate_sources:
            candidate_path = candidate_sources[page_id]
            baseline_commit, baseline_updated_at = revisions[candidate_path.relative_to(root).as_posix()]
            candidate = load_json(candidate_path)
            if candidate.get("id") != page_id or candidate["page"].get("id") != page_id:
                raise RuntimeError(f"candidate identity mismatch in {candidate_path}")
            if candidate["page"].get("review", {}).get("physical_lineation_checked") is not False:
                raise RuntimeError(f"OCR candidate {page_id} must remain visually unchecked")
            assessment = candidate.get("audit", {}).get("bulk_assessment") or {}
            page.update(
                processed_page(
                    candidate["page"],
                    config.get(page_id, {}),
                    reviews.get(page_id, {}),
                    candidate["geometry"],
                    machine_suggestions.get(page_id, {}),
                    allowed_geometry_states={OCR_PROVISIONAL_GEOMETRY_STATE},
                )
            )
            relative_candidate = candidate_path.relative_to(root).as_posix()
            page.update(
                {
                    "data_state": "machine_provisional",
                    "machine_provisional": True,
                    "source": f"https://github.com/{args.repository}/blob/{commit}/{relative_candidate}",
                    "source_label": "Candidate JSON",
                    "provisional_classification": assessment.get(
                        "classification", "initial_batch"
                    ),
                    "provisional_queue_eligible": assessment.get(
                        "eligible_for_provisional_review_queue"
                    ),
                    "provisional_reasons": assessment.get("reasons", []),
                    "structural_review_required": assessment.get("classification")
                    == "quarantine",
                    "ai_checked": False,
                    "baseline_commit": baseline_commit,
                    "baseline_updated_at": baseline_updated_at,
                }
            )
        else:
            page.update(
                {
                    "processed": False,
                    "status": "unprocessed",
                    "printed_page": None,
                    "zones": [],
                    "review": {},
                    "source": None,
                    "source_label": None,
                    "transcription_version": None,
                    "data_state": "scan_only",
                    "machine_provisional": False,
                    "structural_review_required": False,
                    "ai_checked": False,
                    "baseline_commit": None,
                    "baseline_updated_at": None,
                }
            )
        pages.append(page)
    payload = {
        "format": "nippo-public-review-corpus",
        "format_version": 1,
        "repository": args.repository,
        "commit": commit,
        "reference_version": commit[:7],
        "known_roman_terms": embedded_roman_terms(pages),
        "pages": pages,
    }
    (output / "corpus.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    for name in (
        "index.html",
        "quick-edit.js",
        "app.js",
        "styles.css",
        "reference.css",
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
