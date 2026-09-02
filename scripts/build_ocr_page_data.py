#!/usr/bin/env python3
"""Build provisional Level 1 pages from independent Calamari page drafts.

This is the production bridge between ``prepare_calamari_page_drafts.py`` and
the existing human-review corpus.  Recognition remains independent: the raw
draft is written before this script opens the current Level 1 page or its saved
geometry.  Existing data are used only after recognition to supply stable
physical-line IDs, structural zones, indentation, approximate typeface spans,
and already reviewed UI rectangles. Body text comes from the OCR draft;
independent detections validate row association without silently replacing the
human-readable crop geometry.

The default target is the currently prepared but human-unreviewed run
f161–f237. A dry run writes an audit report. ``--apply`` also rewrites the compact
Markdown and compiled JSON for pages whose complete body-line sequence can be
aligned. Incomplete or structurally suspicious pages are reported and left
unchanged.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import unicodedata

from PIL import Image

from build_clean_ocr_pairs import normalized_line
from build_ocr_dataset import load_json, write_json
from compile_level1_markdown import export_markdown, parse_markdown
from prepare_calamari_page_drafts import (
    DEFAULT_CALAMARI,
    DEFAULT_CHECKPOINT,
    executable_command,
    position_alignment,
)
from align_page_geometry_ocr_first import (
    rescue_sandwiched_gaps,
    sequence_alignment as text_sequence_alignment,
)


ROOT = Path(__file__).resolve().parents[1]
LEVEL1 = ROOT / "pilot" / "format-v1-trial" / "level1"
LEVEL1_SOURCE = ROOT / "pilot" / "format-v1-trial" / "level1-source"
GEOMETRY = ROOT / "pilot" / "human-review" / "line-geometry.json"
REVIEW_STATUS = ROOT / "pilot" / "human-review" / "review-status.json"
SCANS = ROOT / "build" / "nippo-jisho-images" / "scans" / "native"
DEFAULT_WORK = ROOT / ".cache" / "ocr-model" / "ocr-page-data-v1"
DEFAULT_MANIFEST = ROOT / "pilot" / "human-review" / "ocr-page-baseline.json"
DEFAULT_BENCHMARK_PAGES = (14, 18, 47, 68, 103, 115, 135, 149, 160)
DEFAULT_HUMAN_REVIEWED_THROUGH = 160
BODY_COLUMNS = ("column-1", "column-2")


@dataclass(frozen=True)
class CharacterStyle:
    typeface: str
    placement: str | None = None
    span_id: str | None = None


def page_id(number: int) -> str:
    return f"bnf-f{number:04d}"


def page_number(identifier: str) -> int:
    return int(identifier.removeprefix("bnf-f"))


def line_text(line: dict) -> str:
    return unicodedata.normalize(
        "NFC", "".join(run["text"] for run in line["runs"]).strip()
    )


def body_lines(page: dict) -> dict[str, dict]:
    return {
        line["id"]: line
        for zone in page["zones"]
        if zone.get("kind") == "column"
        for line in zone.get("lines", [])
    }


def checked_pages(path: Path) -> set[str]:
    """Return pages with any explicitly checked human-review unit."""
    if not path.exists():
        return set()
    result = set()
    for page in load_json(path).get("pages", []):
        if any(unit.get("status") == "checked" for unit in page["units"].values()):
            result.add(page["id"])
    return result


def target_pages(
    first: int,
    last: int,
    *,
    allow_checked: bool,
    human_reviewed_through: int,
) -> list[int]:
    reviewed = checked_pages(REVIEW_STATUS)
    result = []
    for number in range(first, last + 1):
        if number <= human_reviewed_through and not allow_checked:
            continue
        identifier = page_id(number)
        path = LEVEL1 / f"{identifier}.json"
        if not path.exists():
            continue
        page = load_json(path)
        if page.get("review", {}).get("status") == "human_checked":
            continue
        if identifier in reviewed and not allow_checked:
            continue
        result.append(number)
    return result


def prepare_drafts(pages: list[int], benchmarks: list[int], args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "prepare_calamari_page_drafts.py"),
        "--output",
        str(args.work),
        "--pages",
        *map(str, pages),
        "--benchmark-pages",
        *map(str, benchmarks),
        "--line-image",
        "scan-band",
        "--segmentation-workers",
        str(args.segmentation_workers),
    ]
    if args.fresh_segmentation:
        command.append("--fresh-segmentation")
    if args.fresh_recognition:
        command.append("--fresh-recognition")
    subprocess.run(command, cwd=ROOT, check=True)


def prepare_rectified_drafts(pages: list[int], args: argparse.Namespace) -> None:
    """Run a neighbor-resistant second crop only on suspicious pages."""
    if not pages:
        return
    source_segmentations = args.work / "segmentation"
    target_segmentations = args.rectified_work / "segmentation"
    target_segmentations.mkdir(parents=True, exist_ok=True)
    for number in pages:
        source = source_segmentations / f"f{number:04d}.json"
        target = target_segmentations / source.name
        if not source.exists():
            raise FileNotFoundError(source)
        if not target.exists() or args.fresh_segmentation:
            shutil.copy2(source, target)
    command = [
        sys.executable,
        str(ROOT / "scripts" / "prepare_calamari_page_drafts.py"),
        "--output",
        str(args.rectified_work),
        "--pages",
        *map(str, pages),
        "--benchmark-pages",
        "--line-image",
        "rectified",
        "--segmentation-workers",
        str(args.segmentation_workers),
    ]
    if args.fresh_recognition:
        command.append("--fresh-recognition")
    subprocess.run(command, cwd=ROOT, check=True)


def median_spacing(references: list[dict]) -> float:
    differences = [
        right["centre_y"] - left["centre_y"]
        for left, right in zip(references, references[1:])
        if right["centre_y"] > left["centre_y"]
    ]
    return statistics.median(differences) if differences else 60.0


def align_column(
    reference_lines: dict[str, dict],
    candidates: list[dict],
    reference_texts: dict[str, str] | None = None,
) -> dict:
    references = [
        {"line_id": line_id, **geometry}
        for line_id, geometry in sorted(
            reference_lines.items(), key=lambda item: item[1]["centre_y"]
        )
    ]
    candidates = sorted(candidates, key=lambda candidate: candidate["centre"][1])
    spacing = median_spacing(references)
    maximum_distance = max(30.0, min(56.0, spacing * 0.78))

    # Kraken records a baseline, while historical geometry sometimes records
    # the optical ink centre.  Estimate the coordinate offset from many local
    # nearest-neighbour differences rather than trusting one top row.
    local_offsets = []
    for reference in references:
        nearest = min(
            candidates,
            key=lambda candidate: abs(candidate["centre"][1] - reference["centre_y"]),
        )
        difference = nearest["centre"][1] - reference["centre_y"]
        if abs(difference) <= spacing * 0.55:
            local_offsets.append(difference)
    offset = statistics.median(local_offsets) if local_offsets else 0.0
    positioned = [
        {**candidate, "centre_y": candidate["centre"][1] - offset}
        for candidate in candidates
    ]
    if reference_texts is None:
        alignment = position_alignment(
            references, positioned, maximum_distance=maximum_distance
        )
        alignment_method = "position"
    else:
        textual_references = [
            {**reference, "text": reference_texts[reference["line_id"]]}
            for reference in references
        ]
        textual_candidates = [
            {**candidate, "recognition": candidate["text"]}
            for candidate in candidates
        ]
        alignment = text_sequence_alignment(
            textual_references,
            textual_candidates,
            gap_cost=0.55,
            position_cost=0.005,
            maximum_displacement=12,
        )
        alignment, _ = rescue_sandwiched_gaps(
            alignment, len(references), len(candidates)
        )
        alignment_method = "post_ocr_text_and_order"
    matches = {}
    missing = []
    extras = []
    for reference_index, candidate_index in alignment:
        if reference_index is None:
            candidate = candidates[candidate_index]
            if (
                references[0]["centre_y"] - maximum_distance
                <= candidate["centre"][1] - offset
                <= references[-1]["centre_y"] + maximum_distance
            ):
                extras.append(candidate["id"])
            continue
        reference = references[reference_index]
        if candidate_index is None:
            missing.append(reference["line_id"])
            continue
        matches[reference["line_id"]] = candidates[candidate_index]
    return {
        "matches": matches,
        "missing": missing,
        "extras": extras,
        "offset": round(offset, 2),
        "maximum_distance": round(maximum_distance, 2),
        "method": alignment_method,
    }


def character_alignment(left: str, right: str) -> list[tuple[int | None, int | None]]:
    """Return a deterministic minimum-edit character alignment."""
    rows, columns = len(left), len(right)
    costs = [[0] * (columns + 1) for _ in range(rows + 1)]
    steps: list[list[str | None]] = [[None] * (columns + 1) for _ in range(rows + 1)]
    for row in range(1, rows + 1):
        costs[row][0] = row
        steps[row][0] = "delete"
    for column in range(1, columns + 1):
        costs[0][column] = column
        steps[0][column] = "insert"
    for row in range(1, rows + 1):
        for column in range(1, columns + 1):
            choices = (
                (costs[row - 1][column - 1] + (left[row - 1] != right[column - 1]), "pair"),
                (costs[row - 1][column] + 1, "delete"),
                (costs[row][column - 1] + 1, "insert"),
            )
            costs[row][column], steps[row][column] = min(
                choices, key=lambda item: (item[0], {"pair": 0, "delete": 1, "insert": 2}[item[1]])
            )
    result = []
    row, column = rows, columns
    while row or column:
        step = steps[row][column]
        if step == "pair":
            result.append((row - 1, column - 1))
            row -= 1
            column -= 1
        elif step == "delete":
            result.append((row - 1, None))
            row -= 1
        else:
            result.append((None, column - 1))
            column -= 1
    return list(reversed(result))


def old_character_styles(line: dict) -> tuple[str, list[CharacterStyle]]:
    text = ""
    styles = []
    for run in line["runs"]:
        style = CharacterStyle(
            typeface=run["typeface"],
            placement=run.get("placement"),
            span_id=run.get("span_id"),
        )
        text += run["text"]
        styles.extend([style] * len(run["text"]))
    leading = len(text) - len(text.lstrip())
    trailing = len(text.rstrip())
    return text.strip(), styles[leading:trailing]


def projected_styles(line: dict, replacement: str) -> list[CharacterStyle]:
    old_text, old_styles = old_character_styles(line)
    if not replacement:
        return []
    if not old_styles:
        return [CharacterStyle("roman")] * len(replacement)
    result: list[CharacterStyle | None] = [None] * len(replacement)
    alignment = character_alignment(old_text, replacement)
    for old_index, new_index in alignment:
        if old_index is not None and new_index is not None:
            result[new_index] = old_styles[old_index]
    for index, style in enumerate(result):
        if style is not None:
            continue
        previous = next((result[i] for i in range(index - 1, -1, -1) if result[i]), None)
        following = next((result[i] for i in range(index + 1, len(result)) if result[i]), None)
        result[index] = previous or following or CharacterStyle("roman")
    return [style for style in result if style is not None]


def replace_line_text(line: dict, replacement: str) -> dict:
    replacement = unicodedata.normalize("NFC", replacement.strip())
    if not replacement:
        raise ValueError("OCR replacement is empty")
    normal_runs = [
        run for run in line["runs"] if run.get("placement", "normal") == "normal"
    ]
    far_right_runs = [
        run for run in line["runs"] if run.get("placement") == "far-right"
    ]
    if far_right_runs:
        # A far-right fragment is a structural assertion that the full-width
        # OCR band frequently omits or merges with furniture. Preserve that
        # cell verbatim and let OCR replace only the ordinary line portion.
        far_text = "".join(run["text"] for run in far_right_runs)
        if not normal_runs:
            return deepcopy(line)
        visible_far = far_text.strip()
        main_replacement = replacement
        if visible_far and replacement.endswith(visible_far):
            main_replacement = replacement[: -len(visible_far)].rstrip()
        normal_line = {**line, "runs": normal_runs}
        output = replace_line_text(normal_line, main_replacement)
        output["runs"].extend(deepcopy(far_right_runs))
        return output
    styles = projected_styles(line, replacement)
    runs = []
    for character, style in zip(replacement, styles):
        attributes = {"typeface": style.typeface}
        if style.placement:
            attributes["placement"] = style.placement
        if style.span_id:
            attributes["span_id"] = style.span_id
        last_attributes = (
            {key: value for key, value in runs[-1].items() if key != "text"}
            if runs
            else None
        )
        if runs and attributes == last_attributes:
            runs[-1]["text"] += character
        else:
            runs.append({**attributes, "text": character})

    # Preserve a large initial as layout, not recognition.  The OCR supplies
    # its character, while the scan-derived structural record supplies span.
    old_initial = next(
        (run for run in line["runs"] if run.get("layout") == "large-initial"), None
    )
    if old_initial and runs:
        first = runs[0]
        initial = {
            "typeface": first["typeface"],
            "text": first["text"][0],
            "layout": "large-initial",
            "line_span": old_initial["line_span"],
        }
        if first.get("placement"):
            initial["placement"] = first["placement"]
        remainder = first["text"][1:]
        runs[:1] = [initial] + ([{**first, "text": remainder}] if remainder else [])

    output = deepcopy(line)
    output["runs"] = runs
    return output


def normalized_edit_rate(left: str, right: str) -> float:
    alignment = character_alignment(left, right)
    edits = sum(
        1
        for left_index, right_index in alignment
        if left_index is None
        or right_index is None
        or left[left_index] != right[right_index]
    )
    return edits / max(1, len(left))


def build_page(
    number: int,
    draft: dict,
    geometry_page: dict,
    fallbacks: dict[str, dict] | None = None,
    rectified_draft: dict | None = None,
) -> tuple[dict, dict, dict]:
    identifier = page_id(number)
    page = load_json(LEVEL1 / f"{identifier}.json")
    output = deepcopy(page)
    output["review"] = {
        **output["review"],
        "origin": "independent_calamari_ocr_from_scan",
        "status": "visual_draft",
    }
    line_by_id = body_lines(page)
    output_lines = body_lines(output)
    updated_geometry = deepcopy(geometry_page)
    report = {
        "page_id": identifier,
        "status": "ready",
        "body_lines": len(line_by_id),
        "matched": 0,
        "changed": 0,
        "exact": 0,
        "missing": [],
        "extra_body_detections": [],
        "columns": {},
        "high_change_lines": [],
        "empty_ocr_lines": [],
        "fallback_rows": [],
        "rectified_rows": [],
        "quarantined_rows": [],
        "preserved_structural_rows": [],
    }
    fallbacks = fallbacks or {}
    draft_columns = draft["columns"]
    rectified_columns = rectified_draft["columns"] if rectified_draft else None
    for column in BODY_COLUMNS:
        geometry_column = geometry_page["columns"].get(column)
        if not geometry_column:
            report["status"] = "structural_review_required"
            report["missing"].append(f"missing geometry column {column}")
            continue
        alignment = align_column(
            geometry_column["lines"],
            draft_columns[column]["lines"],
            {line_id: line_text(line_by_id[line_id]) for line_id in geometry_column["lines"]},
        )
        rectified_matches = {}
        rectified_by_candidate_id = {}
        if rectified_columns:
            rectified_candidates = rectified_columns[column]["lines"]
            rectified_by_candidate_id = {
                candidate["id"]: candidate for candidate in rectified_candidates
            }
            rectified_alignment = align_column(
                geometry_column["lines"],
                rectified_candidates,
                {
                    line_id: line_text(line_by_id[line_id])
                    for line_id in geometry_column["lines"]
                },
            )
            rectified_matches = rectified_alignment["matches"]
        missing = []
        for line_id in alignment["missing"]:
            fallback = rectified_matches.get(line_id) or fallbacks.get(
                f"{identifier}/{line_id}"
            )
            if fallback is None:
                missing.append(line_id)
                continue
            alignment["matches"][line_id] = fallback
            if line_id in rectified_matches:
                report["rectified_rows"].append(line_id)
            else:
                report["fallback_rows"].append(line_id)
        alignment["missing"] = missing
        report["columns"][column] = {
            "offset": alignment["offset"],
            "maximum_distance": alignment["maximum_distance"],
            "matched": len(alignment["matches"]),
            "missing": alignment["missing"],
            "extra_body_detections": alignment["extras"],
            "method": alignment["method"],
        }
        report["missing"].extend(f"{column}/{line_id}" for line_id in alignment["missing"])
        report["extra_body_detections"].extend(
            f"{column}/{candidate_id}" for candidate_id in alignment["extras"]
        )
        for line_id, candidate in alignment["matches"].items():
            text = unicodedata.normalize("NFC", candidate["text"].strip())
            if not text:
                report["empty_ocr_lines"].append(line_id)
                continue
            current = line_text(line_by_id[line_id])
            alternate = rectified_by_candidate_id.get(candidate["id"])
            if alternate is not None:
                alternate_text = unicodedata.normalize(
                    "NFC", alternate["text"].strip()
                )
                primary_rate = normalized_edit_rate(current, text)
                alternate_rate = normalized_edit_rate(current, alternate_text)
                primary_has_neighbor_bleed = (
                    current in text
                    and len(text) >= len(current) + 3
                ) or len(text) > max(len(current) + 8, round(len(current) * 1.35))
                if alternate_text and (
                    primary_has_neighbor_bleed
                    or (
                        primary_rate > 0.35
                        and alternate_rate + 0.15 < primary_rate
                    )
                ):
                    candidate = alternate
                    text = alternate_text
                    report["rectified_rows"].append(line_id)
            proposed_line = replace_line_text(line_by_id[line_id], text)
            proposed_text = line_text(proposed_line)
            if (
                proposed_text == current
                and text != current
                and all(
                    run.get("placement") == "far-right"
                    for run in line_by_id[line_id]["runs"]
                )
            ):
                report["preserved_structural_rows"].append(line_id)
                continue
            rate = normalized_edit_rate(current, proposed_text)
            if rate > 0.35:
                report["high_change_lines"].append(
                    {
                        "line_id": line_id,
                        "current": current,
                        "ocr": text,
                        "projected": proposed_text,
                        "edit_rate": round(rate, 4),
                    }
                )
                report["quarantined_rows"].append(line_id)
                continue
            output_lines[line_id].update(proposed_line)
            report["matched"] += 1
            if current == proposed_text:
                report["exact"] += 1
            else:
                report["changed"] += 1

    accounted = (
        report["matched"]
        + len(report["quarantined_rows"])
        + len(report["preserved_structural_rows"])
    )
    if report["missing"] or report["empty_ocr_lines"] or accounted != report["body_lines"]:
        report["status"] = "structural_review_required"
    elif report["quarantined_rows"] or report["preserved_structural_rows"]:
        report["status"] = "ready_with_quarantine"
    report["rectified_rows"] = sorted(set(report["rectified_rows"]))
    report["exact_rate"] = report["exact"] / max(1, report["body_lines"])
    report["draft_sha256"] = hashlib.sha256(
        json.dumps(draft, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return output, updated_geometry, report


def fallback_candidate(
    identifier: str,
    line_id: str,
    text: str,
    geometry_line: dict,
    column_box: list[int],
) -> dict:
    x, y, width, height = geometry_line["crop"]
    left, _, right, _ = column_box
    centre = geometry_line["centre_y"]
    return {
        "id": f"fallback-{line_id}",
        "text": text,
        "centre": [(left + right) / 2, centre],
        "boundary": [
            [x, y],
            [x + width, y],
            [x + width, y + height],
            [x, y + height],
        ],
        "baseline": [[x, centre], [x + width, centre]],
        "source": "saved-geometry fallback after independent segmentation miss",
    }


def recognize_fallbacks(
    requests: list[tuple[str, str, str, dict, list[int]]],
    args: argparse.Namespace,
) -> dict[str, dict]:
    if not requests:
        return {}
    prepared_dir = args.work / "fallback-prepared"
    prediction_dir = args.work / "fallback-predictions"
    prepared_dir.mkdir(parents=True, exist_ok=True)
    prediction_dir.mkdir(parents=True, exist_ok=True)
    expected = {}
    candidates = {}
    for identifier, column, line_id, geometry_line, column_box in requests:
        number = page_number(identifier)
        scan_path = SCANS / f"f{number:04d}.jpg"
        with Image.open(scan_path) as scan:
            centre = geometry_line["centre_y"]
            top = max(0, round(centre - 36))
            bottom = min(scan.height, round(centre + 36))
            left, _, right, _ = column_box
            source = scan.crop((left, top, right, bottom))
        prepared = normalized_line(source, height=48, max_width=1024)
        stem = f"{identifier}__{line_id}"
        path = prepared_dir / f"{stem}.png"
        prepared.save(path, format="PNG", optimize=True)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        expected[stem] = digest
        candidates[stem] = (identifier, line_id, geometry_line, column_box)

    expected_prepared = {f"{stem}.png" for stem in candidates}
    expected_predictions = {f"{stem}.pred.txt" for stem in candidates}
    for path in prepared_dir.glob("*.png"):
        if path.name not in expected_prepared:
            path.unlink()
    for path in prediction_dir.glob("*.pred.txt"):
        if path.name not in expected_predictions:
            path.unlink()

    manifest_path = prediction_dir / "manifest.json"
    stored = load_json(manifest_path) if manifest_path.exists() else None
    outputs_exist = all(
        (prediction_dir / f"{stem}.pred.txt").exists() for stem in candidates
    )
    if stored != expected or not outputs_exist or args.fresh_recognition:
        subprocess.run(
            executable_command(
                DEFAULT_CALAMARI,
                "--checkpoint",
                str(DEFAULT_CHECKPOINT),
                "--data.images",
                str(prepared_dir / "*.png"),
                "--output_dir",
                str(prediction_dir),
                "--verbose",
                "false",
                "--pipeline.batch_size",
                "32",
                "--pipeline.num_processes",
                "2",
            ),
            check=True,
        )
        write_json(manifest_path, expected)

    result = {}
    for stem, (identifier, line_id, geometry_line, column_box) in candidates.items():
        text = unicodedata.normalize(
            "NFC",
            (prediction_dir / f"{stem}.pred.txt")
            .read_text(encoding="utf-8")
            .rstrip("\r\n"),
        )
        result[f"{identifier}/{line_id}"] = fallback_candidate(
            identifier, line_id, text, geometry_line, column_box
        )
    return result


def validate_page(page: dict, geometry: dict) -> None:
    body = body_lines(page)
    geometry_lines = {
        line_id
        for column in geometry["columns"].values()
        for line_id in column["lines"]
    }
    if set(body) != geometry_lines:
        missing = sorted(set(body) - geometry_lines)
        extra = sorted(geometry_lines - set(body))
        raise ValueError(f"{page['id']}: geometry mismatch missing={missing} extra={extra}")
    source_size = geometry["source_size"]
    scan = SCANS / f"f{page_number(page['id']):04d}.jpg"
    with Image.open(scan) as image:
        if list(image.size) != source_size:
            raise ValueError(f"{page['id']}: source-size mismatch")
    for column in geometry["columns"].values():
        for line_id, line in column["lines"].items():
            for key in ("crop", "context_crop"):
                x, y, width, height = line[key]
                if not (
                    0 <= x < source_size[0]
                    and 0 <= y < source_size[1]
                    and width > 0
                    and height > 0
                    and x + width <= source_size[0]
                    and y + height <= source_size[1]
                ):
                    raise ValueError(f"{page['id']}/{line_id}: invalid {key}")
    rendered = export_markdown(page)
    temporary = ROOT / ".cache" / "ocr-page-validation.md"
    temporary.write_text(rendered, encoding="utf-8")
    try:
        if parse_markdown(temporary) != page:
            raise ValueError(f"{page['id']}: Markdown round trip changed the page")
    finally:
        temporary.unlink(missing_ok=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--first-page", type=int, default=161)
    result.add_argument("--last-page", type=int, default=237)
    result.add_argument("--pages", nargs="+", type=int)
    result.add_argument("--benchmark-pages", nargs="*", type=int, default=list(DEFAULT_BENCHMARK_PAGES))
    result.add_argument("--work", type=Path, default=DEFAULT_WORK)
    result.add_argument("--rectified-work", type=Path)
    result.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    result.add_argument("--skip-ocr", action="store_true")
    result.add_argument("--fresh-segmentation", action="store_true")
    result.add_argument("--fresh-recognition", action="store_true")
    result.add_argument("--segmentation-workers", type=int, default=3)
    result.add_argument(
        "--human-reviewed-through",
        type=int,
        default=DEFAULT_HUMAN_REVIEWED_THROUGH,
        help="protect this known human-reviewed prefix (default: 160)",
    )
    result.add_argument("--allow-checked", action="store_true")
    result.add_argument("--allow-incomplete", action="store_true")
    result.add_argument("--apply", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    pages = sorted(
        set(
            args.pages
            or target_pages(
                args.first_page,
                args.last_page,
                allow_checked=args.allow_checked,
                human_reviewed_through=args.human_reviewed_through,
            )
        )
    )
    if not pages:
        raise SystemExit("no eligible human-unreviewed structured pages")
    reviewed = checked_pages(REVIEW_STATUS)
    prohibited = [
        number
        for number in pages
        if not args.allow_checked
        and (
            number <= args.human_reviewed_through
            or page_id(number) in reviewed
        )
    ]
    if prohibited:
        raise SystemExit(f"refusing explicitly checked pages: {prohibited}")
    missing_sources = [
        number
        for number in pages
        if not (LEVEL1 / f"{page_id(number)}.json").exists()
    ]
    if missing_sources:
        raise SystemExit(f"pages do not yet have structural Level 1 data: {missing_sources}")

    args.work = args.work.resolve()
    args.rectified_work = (
        args.rectified_work.resolve()
        if args.rectified_work
        else args.work.with_name(args.work.name + "-rectified")
    )
    if not args.skip_ocr:
        prepare_drafts(pages, args.benchmark_pages, args)

    geometry = load_json(GEOMETRY)
    geometry_by_id = {page["id"]: page for page in geometry["pages"]}

    # First align only independent detections.  If Kraken genuinely omitted a
    # canonical body row, recognize a narrow scan band around that row as an
    # explicit fallback, then rebuild the page.  Existing text never enters
    # recognition; it is used only by the post-inference sequence alignment.
    preliminary = []
    for number in pages:
        identifier = page_id(number)
        draft_path = args.work / "drafts" / f"{identifier}.json"
        if not draft_path.exists():
            raise SystemExit(f"missing OCR draft: {draft_path}")
        if identifier not in geometry_by_id:
            raise SystemExit(f"missing structural geometry: {identifier}")
        _, _, report = build_page(
            number, load_json(draft_path), geometry_by_id[identifier]
        )
        preliminary.append(report)

    suspicious_pages = sorted(
        page_number(report["page_id"])
        for report in preliminary
        if report["missing"] or report["high_change_lines"]
    )
    if suspicious_pages and not args.skip_ocr:
        prepare_rectified_drafts(suspicious_pages, args)

    rectified_drafts = {}
    for number in suspicious_pages:
        path = args.rectified_work / "drafts" / f"{page_id(number)}.json"
        if path.exists():
            rectified_drafts[page_id(number)] = load_json(path)

    # Re-evaluate after the tighter rectified-line route.  Only rows still
    # absent from both independent associations need saved-geometry fallback.
    fallback_requests = []
    for number in pages:
        identifier = page_id(number)
        draft_path = args.work / "drafts" / f"{identifier}.json"
        _, _, report = build_page(
            number,
            load_json(draft_path),
            geometry_by_id[identifier],
            rectified_draft=rectified_drafts.get(identifier),
        )
        for value in report["missing"]:
            column, line_id = value.split("/", 1)
            geometry_column = geometry_by_id[identifier]["columns"][column]
            fallback_requests.append(
                (
                    identifier,
                    column,
                    line_id,
                    geometry_column["lines"][line_id],
                    geometry_column["box"],
                )
            )
    fallbacks = recognize_fallbacks(fallback_requests, args)

    replacements = {}
    reports = []
    for number in pages:
        identifier = page_id(number)
        draft_path = args.work / "drafts" / f"{identifier}.json"
        if not draft_path.exists():
            raise SystemExit(f"missing OCR draft: {draft_path}")
        if identifier not in geometry_by_id:
            raise SystemExit(f"missing structural geometry: {identifier}")
        page, page_geometry, report = build_page(
            number,
            load_json(draft_path),
            geometry_by_id[identifier],
            fallbacks,
            rectified_draft=rectified_drafts.get(identifier),
        )
        reports.append(report)
        if report["status"] in {"ready", "ready_with_quarantine"} or args.allow_incomplete:
            validate_page(page, page_geometry)
            replacements[identifier] = page

    unresolved = [
        report["page_id"]
        for report in reports
        if report["status"] == "structural_review_required"
    ]
    audit = {
        "format": "nippo-ocr-page-baseline-audit",
        "format_version": 1,
        "method": {
            "segmentation": "Kraken 5.2.9 bundled blla.mlmodel",
            "recognition": "Calamari book-specific antiquatype model",
            "checkpoint": ".cache/ocr-model/runs/calamari-antiqua-book-codec-v1/best.ckpt",
            "association": "post-inference text/order alignment to stable physical-line IDs, checked against scan position",
            "association_detail": "current text is opened only after independent OCR and may aid stable-ID sequence alignment",
            "fallback": "saved-geometry 72-pixel scan band only when independent segmentation omitted a canonical row",
            "style": "character alignment projection from the existing structural draft",
            "geometry": "existing review rectangles retained; blind OCR detections validate physical-row association",
        },
        "scope": {
            "requested_pages": pages,
            "ready_pages": [page_number(identifier) for identifier in replacements],
            "structural_review_required": unresolved,
        },
        "totals": {
            "pages": len(reports),
            "body_lines": sum(report["body_lines"] for report in reports),
            "matched": sum(report["matched"] for report in reports),
            "changed": sum(report["changed"] for report in reports),
            "exact": sum(report["exact"] for report in reports),
            "missing": sum(len(report["missing"]) for report in reports),
            "extra_body_detections": sum(len(report["extra_body_detections"]) for report in reports),
            "high_change_lines": sum(len(report["high_change_lines"]) for report in reports),
            "fallback_rows": sum(len(report["fallback_rows"]) for report in reports),
            "rectified_rows": sum(len(report["rectified_rows"]) for report in reports),
            "quarantined_rows": sum(len(report["quarantined_rows"]) for report in reports),
            "preserved_structural_rows": sum(
                len(report["preserved_structural_rows"]) for report in reports
            ),
        },
        "pages": reports,
    }
    args.work.mkdir(parents=True, exist_ok=True)
    write_json(args.work / "page-data-audit.json", audit)

    print(
        f"Audited {audit['totals']['body_lines']} body lines on {len(reports)} pages; "
        f"{len(replacements)} ready, {len(unresolved)} require structural review."
    )
    print(
        f"OCR changes {audit['totals']['changed']} lines; "
        f"{audit['totals']['exact']} lines already agree exactly."
    )
    if unresolved and not args.allow_incomplete:
        print("Not applying incomplete pages: " + ", ".join(unresolved))

    if args.apply:
        if unresolved and not args.allow_incomplete:
            raise SystemExit(
                "structural exceptions remain; inspect the audit or pass --allow-incomplete to retain unmatched current lines"
            )
        for identifier, page in replacements.items():
            (LEVEL1_SOURCE / f"{identifier}.md").write_text(
                export_markdown(page), encoding="utf-8"
            )
            write_json(LEVEL1 / f"{identifier}.json", page)
        baseline = {
            "format": "nippo-ocr-page-baseline",
            "format_version": 1,
            "pages": [
                {
                    "id": report["page_id"],
                    "draft_sha256": report["draft_sha256"],
                    "body_lines": report["body_lines"],
                    "changed_lines": report["changed"],
                    "exact_lines": report["exact"],
                    "fallback_lines": report["fallback_rows"],
                    "rectified_lines": report["rectified_rows"],
                    "quarantined_lines": report["quarantined_rows"],
                    "quarantined_candidates": report["high_change_lines"],
                    "preserved_structural_lines": report["preserved_structural_rows"],
                    "source": "independent Calamari page draft",
                    "human_review": "pending",
                }
                for report in reports
                if report["page_id"] in replacements
            ],
        }
        write_json(args.manifest, baseline)
        print(f"Applied OCR baselines to {len(replacements)} pages.")
    else:
        print("Dry run only; pass --apply after inspecting the audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
