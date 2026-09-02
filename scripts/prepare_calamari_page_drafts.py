#!/usr/bin/env python3
"""Create independent page drafts with Kraken segmentation and Calamari OCR.

The inference path never reads the existing transcription or review geometry.
Those data are opened only after the draft files have been written, when the
optional benchmark/comparison report is assembled.

The output is intentionally an OCR draft rather than canonical Level 1 data:
it retains every detected row, raw recognition, and scan geometry, but it does
not invent typeface spans, indentation, furniture roles, or stable line IDs.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import unicodedata

from PIL import Image

from align_page_geometry_ocr_first import (
    rescue_sandwiched_gaps,
    sequence_alignment as text_sequence_alignment,
)
from build_clean_ocr_pairs import normalized_line
from build_ocr_dataset import line_texts, load_json, write_json
from evaluate_line_ocr_predictions import evaluate


ROOT = Path(__file__).resolve().parents[1]
SCANS = ROOT / "build" / "nippo-jisho-images" / "scans" / "native"
LEVEL1 = ROOT / "pilot" / "format-v1-trial" / "level1"
GEOMETRY = ROOT / "pilot" / "human-review" / "line-geometry.json"
DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "calamari-page-drafts-v1"
DEFAULT_CHECKPOINT = (
    ROOT / ".cache" / "ocr-model" / "runs"
    / "calamari-antiqua-book-codec-v1" / "best.ckpt"
)
DEFAULT_CALAMARI = (
    ROOT / ".cache" / "ocr-model" / "venv-calamari-arm64"
    / "bin" / "calamari-predict"
)
DEFAULT_KRAKEN = (
    ROOT / ".cache" / "ocr-model" / "venv-kraken-arm64" / "bin" / "kraken"
)
DEFAULT_KRAKEN_PYTHON = (
    ROOT / ".cache" / "ocr-model" / "venv-kraken-arm64" / "bin" / "python"
)
DEFAULT_PAGES = tuple(range(161, 171))
DEFAULT_BENCHMARK_PAGES = (
    31,
    34,
    37,
    39,
    77,
    82,
    90,
    105,
    113,
    134,
    135,
    139,
    142,
    147,
)


def executable_command(path: Path, *arguments: str) -> list[str]:
    """Force native execution for the workspace's arm64 macOS OCR venvs."""
    command = [str(path), *arguments]
    if platform.system() == "Darwin" and "arm64" in path.as_posix():
        return ["arch", "-arm64", *command]
    return command


def page_id(number: int) -> str:
    return f"bnf-f{number:04d}"


def mean_coordinate(line: dict, coordinate: int) -> float:
    return statistics.mean(point[coordinate] for point in line["baseline"])


def polygon_bbox(line: dict, image_size: tuple[int, int], padding: int = 12) -> list[int]:
    points = line.get("boundary") or line["baseline"]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    width, height = image_size
    left = max(0, round(min(xs)) - padding)
    top = max(0, round(min(ys)) - padding)
    right = min(width, round(max(xs)) + padding + 1)
    bottom = min(height, round(max(ys)) + padding + 1)
    return [left, top, max(1, right - left), max(1, bottom - top)]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot take a percentile of an empty list")
    position = fraction * (len(ordered) - 1)
    left = int(position)
    right = min(len(ordered) - 1, left + 1)
    weight = position - left
    return ordered[left] * (1 - weight) + ordered[right] * weight


def inferred_column_band(
    candidates: list[dict], image_size: tuple[int, int], *, padding: int = 48
) -> tuple[int, int]:
    """Infer a generous text-column x range without production geometry."""
    page_width = image_size[0]
    substantial = []
    for candidate in candidates:
        xs = [point[0] for point in candidate["baseline"]]
        if max(xs) - min(xs) >= page_width * 0.16:
            substantial.append((min(xs), max(xs)))
    source = substantial or [
        (
            min(point[0] for point in candidate["baseline"]),
            max(point[0] for point in candidate["baseline"]),
        )
        for candidate in candidates
    ]
    left = max(0, round(percentile([item[0] for item in source], 0.05)) - padding)
    right = min(
        page_width,
        round(percentile([item[1] for item in source], 0.95)) + padding + 1,
    )
    return left, right


def split_candidates(segmentation: dict, image_size: tuple[int, int]) -> dict[str, list[dict]]:
    """Assign blind detections to page halves and stable vertical order."""
    midpoint = image_size[0] / 2
    columns: dict[str, list[dict]] = {"column-1": [], "column-2": []}
    for source in segmentation["lines"]:
        centre_x = mean_coordinate(source, 0)
        centre_y = mean_coordinate(source, 1)
        column = "column-1" if centre_x < midpoint else "column-2"
        columns[column].append(
            {
                "source_id": source["id"],
                "centre_x": centre_x,
                "centre_y": centre_y,
                "baseline": source["baseline"],
                "boundary": source.get("boundary"),
                "crop": polygon_bbox(source, image_size),
            }
        )
    for column, candidates in columns.items():
        candidates.sort(key=lambda item: (item["centre_y"], item["centre_x"]))
        for index, candidate in enumerate(candidates, start=1):
            candidate["id"] = f"{column}-k{index:03d}"
    return columns


def ensure_segmentations(page_numbers: list[int], args: argparse.Namespace) -> None:
    args.segmentation.mkdir(parents=True, exist_ok=True)
    pending = []
    for number in page_numbers:
        output = args.segmentation / f"f{number:04d}.json"
        if output.exists() and not args.fresh_segmentation:
            continue
        pending.append(number)

    def segment(number: int) -> None:
        output = args.segmentation / f"f{number:04d}.json"
        scan = args.scans / f"f{number:04d}.jpg"
        if not scan.exists():
            raise FileNotFoundError(scan)
        subprocess.run(
            executable_command(
                args.kraken, "-i", str(scan), str(output), "segment", "-bl"
            ),
            check=True,
        )

    # Each Kraken invocation owns one independent page and output file.  A
    # small process pool avoids making dictionary-wide initialization needlessly
    # serial while keeping memory use bounded on ordinary laptops.
    with ThreadPoolExecutor(max_workers=args.segmentation_workers) as executor:
        list(executor.map(segment, pending))


def ensure_extracted(page_numbers: list[int], args: argparse.Namespace) -> None:
    missing = []
    for number in page_numbers:
        destination = args.extracted / page_id(number)
        segmentation = load_json(args.segmentation / f"f{number:04d}.json")
        if args.fresh_segmentation or not destination.exists() or len(list(destination.glob("*.png"))) != len(segmentation["lines"]):
            missing.append(number)
    if not missing:
        return
    subprocess.run(
        executable_command(
            args.kraken_python,
            str(ROOT / "scripts" / "extract_kraken_lines.py"),
            "--pages",
            *[str(number) for number in missing],
            "--kraken",
            str(args.segmentation),
            "--output",
            str(args.extracted),
        ),
        check=True,
    )


def prepare_candidates(page_numbers: list[int], args: argparse.Namespace) -> list[dict]:
    records: list[dict] = []
    args.prepared.mkdir(parents=True, exist_ok=True)
    for number in page_numbers:
        identifier = page_id(number)
        scan_path = args.scans / f"f{number:04d}.jpg"
        with Image.open(scan_path) as scan:
            image_size = scan.size
            segmentation = load_json(args.segmentation / f"f{number:04d}.json")
            columns = split_candidates(segmentation, image_size)
            for column, candidates in columns.items():
                column_left, column_right = inferred_column_band(candidates, image_size)
                for candidate in candidates:
                    if args.line_image == "rectified":
                        extracted = (
                            args.extracted / identifier / f"{candidate['source_id']}.png"
                        )
                        if not extracted.exists():
                            raise FileNotFoundError(extracted)
                        with Image.open(extracted) as image:
                            source = image.copy()
                        ocr_crop = candidate["crop"]
                    else:
                        centre_y = round(candidate["centre_y"])
                        top = max(0, centre_y - args.scan_band_height // 2)
                        bottom = min(
                            image_size[1], top + args.scan_band_height
                        )
                        top = max(0, bottom - args.scan_band_height)
                        ocr_crop = [
                            column_left,
                            top,
                            column_right - column_left,
                            bottom - top,
                        ]
                        source = scan.crop(
                            (column_left, top, column_right, bottom)
                        )
                    prepared = normalized_line(
                        source, height=args.height, max_width=args.max_width
                    )
                    filename = f"{identifier}__{candidate['id']}.png"
                    destination = args.prepared / filename
                    prepared.save(destination, format="PNG", optimize=True)
                    records.append(
                        {
                            "page_id": identifier,
                            "page_number": number,
                            "column": column,
                            **candidate,
                            "ocr_crop": ocr_crop,
                            "prepared_image": destination.relative_to(args.output).as_posix(),
                            "prepared_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                        }
                    )
    return records


def run_calamari(records: list[dict], args: argparse.Namespace) -> None:
    if not records:
        return
    args.predictions.mkdir(parents=True, exist_ok=True)
    prediction_paths = {
        record["prepared_image"]: args.predictions
        / f"{Path(record['prepared_image']).stem}.pred.txt"
        for record in records
    }
    expected_manifest = {
        record["prepared_image"]: record["prepared_sha256"] for record in records
    }
    expected_prepared_names = {
        Path(record["prepared_image"]).name for record in records
    }
    expected_prediction_names = {
        path.name for path in prediction_paths.values()
    }
    # Both Calamari inputs are directory globs. Remove stale intermediates from
    # earlier page selections so a smaller rerun cannot silently recognize and
    # retain rows outside its manifest.
    for path in args.prepared.glob("*.png"):
        if path.name not in expected_prepared_names:
            path.unlink()
    for path in args.predictions.glob("*.pred.txt"):
        if path.name not in expected_prediction_names:
            path.unlink()
    manifest_path = args.predictions / "manifest.json"
    stored_manifest = load_json(manifest_path) if manifest_path.exists() else None
    cache_is_current = (
        not args.fresh_recognition
        and stored_manifest == expected_manifest
        and all(path.exists() for path in prediction_paths.values())
    )
    if cache_is_current:
        for record in records:
            record["text"] = unicodedata.normalize(
                "NFC",
                prediction_paths[record["prepared_image"]]
                .read_text(encoding="utf-8")
                .rstrip("\r\n"),
            )
        return
    subprocess.run(
        executable_command(
            args.calamari,
            "--checkpoint",
            str(args.checkpoint),
            "--data.images",
            str(args.prepared / "*.png"),
            "--output_dir",
            str(args.predictions),
            "--verbose",
            "false",
            "--pipeline.batch_size",
            str(args.batch_size),
            "--pipeline.num_processes",
            str(args.num_processes),
        ),
        check=True,
    )
    for record in records:
        stem = Path(record["prepared_image"]).stem
        prediction = args.predictions / f"{stem}.pred.txt"
        if not prediction.exists():
            raise FileNotFoundError(prediction)
        record["text"] = unicodedata.normalize(
            "NFC", prediction.read_text(encoding="utf-8").rstrip("\r\n")
        )
    write_json(manifest_path, expected_manifest)


def write_drafts(records: list[dict], args: argparse.Namespace) -> None:
    by_page: dict[str, list[dict]] = {}
    for record in records:
        by_page.setdefault(record["page_id"], []).append(record)
    args.drafts.mkdir(parents=True, exist_ok=True)
    for identifier, page_records in sorted(by_page.items()):
        number = page_records[0]["page_number"]
        scan_path = args.scans / f"f{number:04d}.jpg"
        with Image.open(scan_path) as scan:
            source_size = list(scan.size)
        columns = {}
        for column in ("column-1", "column-2"):
            lines = []
            for record in page_records:
                if record["column"] != column:
                    continue
                lines.append(
                    {
                        "id": record["id"],
                        "source_detection_id": record["source_id"],
                        "text": record["text"],
                        "centre": [round(record["centre_x"], 2), round(record["centre_y"], 2)],
                        "crop": record["crop"],
                        "ocr_crop": record["ocr_crop"],
                        "baseline": record["baseline"],
                        "boundary": record["boundary"],
                        "prepared_image": record["prepared_image"],
                        "prepared_sha256": record["prepared_sha256"],
                    }
                )
            columns[column] = {"lines": lines}
        write_json(
            args.drafts / f"{identifier}.json",
            {
                "format": "nippo-ocr-page-draft",
                "format_version": 1,
                "id": identifier,
                "source": {
                    "scan": scan_path.relative_to(ROOT).as_posix(),
                    "source_size": source_size,
                },
                "method": {
                    "segmentation": "Kraken 5.2.9 bundled blla.mlmodel",
                    "line_extraction": (
                        "Kraken polygon rectification"
                        if args.line_image == "rectified"
                        else "native-scan horizontal band centred on Kraken baseline"
                    ),
                    "recognition": "Calamari book-specific antiquatype model",
                    "checkpoint": str(args.checkpoint.relative_to(ROOT)),
                    "line_height": args.height,
                    "max_width": args.max_width,
                },
                "limitations": [
                    "raw OCR text has no inferred typeface spans or indentation",
                    "detections include running headers and page furniture",
                    "candidate IDs are provisional and are not canonical Level 1 line IDs",
                ],
                "columns": columns,
            },
        )


def median_spacing(lines: list[dict]) -> float:
    differences = [
        right["centre_y"] - left["centre_y"]
        for left, right in zip(lines, lines[1:])
        if right["centre_y"] - left["centre_y"] > 20
    ]
    return statistics.median(differences) if differences else 60.0


def position_alignment(
    references: list[dict], candidates: list[dict], *, maximum_distance: float
) -> list[tuple[int | None, int | None]]:
    """Align ordered rows by scan position only; OCR strings are not consulted."""
    rows, columns = len(references), len(candidates)
    gap_cost = 1.0
    costs = [[0.0] * (columns + 1) for _ in range(rows + 1)]
    steps: list[list[str | None]] = [[None] * (columns + 1) for _ in range(rows + 1)]
    for row in range(1, rows + 1):
        costs[row][0] = row * gap_cost
        steps[row][0] = "reference_gap"
    for column in range(1, columns + 1):
        costs[0][column] = column * gap_cost
        steps[0][column] = "candidate_gap"
    for row in range(1, rows + 1):
        for column in range(1, columns + 1):
            distance = abs(
                references[row - 1]["centre_y"] - candidates[column - 1]["centre_y"]
            )
            match = float("inf")
            if distance <= maximum_distance:
                match = costs[row - 1][column - 1] + distance / maximum_distance
            choices = (
                (match, "match"),
                (costs[row - 1][column] + gap_cost, "reference_gap"),
                (costs[row][column - 1] + gap_cost, "candidate_gap"),
            )
            costs[row][column], steps[row][column] = min(
                choices, key=lambda value: value[0]
            )
    result = []
    row, column = rows, columns
    while row or column:
        step = steps[row][column]
        if step == "match":
            result.append((row - 1, column - 1))
            row -= 1
            column -= 1
        elif step == "reference_gap":
            result.append((row - 1, None))
            row -= 1
        else:
            result.append((None, column - 1))
            column -= 1
    return list(reversed(result))


def reference_columns(identifier: str, geometry: dict) -> dict[str, list[dict]]:
    page = load_json(LEVEL1 / f"{identifier}.json")
    texts = line_texts(page)
    result = {}
    for column, value in geometry["columns"].items():
        result[column] = [
            {
                "id": f"{identifier}/{line_id}",
                "line_id": line_id,
                "text": texts[line_id],
                "centre_y": line_geometry["centre_y"],
            }
            for line_id, line_geometry in sorted(
                value["lines"].items(), key=lambda item: item[1]["centre_y"]
            )
        ]
    return result


def compare_page(
    identifier: str,
    page_records: list[dict],
    geometry: dict,
    *,
    alignment_mode: str,
) -> tuple[dict, list[dict], list[dict]]:
    references_by_column = reference_columns(identifier, geometry)
    matched_references: list[dict] = []
    matched_predictions: list[dict] = []
    line_comparisons = []
    missing = []
    extra_in_body_band = []
    alignment_offsets = {}
    for column, references in references_by_column.items():
        candidates = sorted(
            (record for record in page_records if record["column"] == column),
            key=lambda record: record["centre_y"],
        )
        spacing = median_spacing(references)
        maximum_distance = max(28.0, min(52.0, spacing * 0.72))
        if alignment_mode == "text":
            textual_candidates = [
                {**candidate, "recognition": candidate["text"]}
                for candidate in candidates
            ]
            alignment = text_sequence_alignment(
                references,
                textual_candidates,
                gap_cost=0.55,
                position_cost=0.005,
                maximum_displacement=12,
            )
            alignment, _ = rescue_sandwiched_gaps(
                alignment, len(references), len(candidates)
            )
            alignment_offsets[column] = None
        else:
            # Some older canonical rectangles store the visual ink centre while
            # Kraken exposes the lower baseline.  Calibrate that coordinate-system
            # offset from the first plausible body row before aligning the series.
            first_y = references[0]["centre_y"]
            plausible_first = [
                candidate
                for candidate in candidates
                if first_y - 20 <= candidate["centre_y"] <= first_y + spacing * 0.85
            ]
            alignment_offset = (
                min(
                    plausible_first,
                    key=lambda candidate: abs(candidate["centre_y"] - first_y),
                )["centre_y"]
                - first_y
                if plausible_first
                else 0.0
            )
            alignment_offsets[column] = round(alignment_offset, 2)
            aligned_candidates = [
                {**candidate, "centre_y": candidate["centre_y"] - alignment_offset}
                for candidate in candidates
            ]
            alignment = position_alignment(
                references, aligned_candidates, maximum_distance=maximum_distance
            )
        body_top = references[0]["centre_y"] - maximum_distance
        body_bottom = references[-1]["centre_y"] + maximum_distance
        for reference_index, candidate_index in alignment:
            if reference_index is None:
                candidate = candidates[candidate_index]
                if body_top <= candidate["centre_y"] <= body_bottom:
                    extra_in_body_band.append(f"{identifier}/{candidate['id']}")
                continue
            reference = references[reference_index]
            if candidate_index is None:
                missing.append(reference["id"])
                continue
            candidate = candidates[candidate_index]
            matched_references.append({"id": reference["id"], "text": reference["text"]})
            matched_predictions.append({"id": reference["id"], "text": candidate["text"]})
            line_comparisons.append(
                {
                    "line_id": reference["line_id"],
                    "draft_id": candidate["id"],
                    "reference": reference["text"],
                    "draft": candidate["text"],
                    "centre_y_difference": round(
                        candidate["centre_y"] - reference["centre_y"], 2
                    ),
                }
            )
    metrics = evaluate(matched_references, matched_predictions)
    metrics.update(
        {
            "canonical_body_lines": sum(
                len(lines) for lines in references_by_column.values()
            ),
            "matched_body_lines": len(matched_references),
            "line_detection_recall": len(matched_references)
            / max(1, sum(len(lines) for lines in references_by_column.values())),
            "unmatched_canonical_lines": missing,
            "extra_detections_inside_body_band": extra_in_body_band,
            "all_detections": len(page_records),
            "comparison_alignment_offsets": alignment_offsets,
            "comparison_alignment_mode": alignment_mode,
        }
    )
    return metrics, line_comparisons, matched_references


def aggregate_metrics(page_results: list[dict]) -> dict:
    references = []
    predictions = []
    canonical = matched = detections = 0
    missing = extras = 0
    for page in page_results:
        canonical += page["metrics"]["canonical_body_lines"]
        matched += page["metrics"]["matched_body_lines"]
        detections += page["metrics"]["all_detections"]
        missing += len(page["metrics"]["unmatched_canonical_lines"])
        extras += len(page["metrics"]["extra_detections_inside_body_band"])
        for line in page["lines"]:
            identifier = f"{page['page_id']}/{line['line_id']}"
            references.append({"id": identifier, "text": line["reference"]})
            predictions.append({"id": identifier, "text": line["draft"]})
    recognition = evaluate(references, predictions) if references else {}
    return {
        "pages": len(page_results),
        "canonical_body_lines": canonical,
        "matched_body_lines": matched,
        "line_detection_recall": matched / max(1, canonical),
        "unmatched_canonical_lines": missing,
        "extra_detections_inside_body_band": extras,
        "all_detections_including_furniture": detections,
        "recognition_on_position_matched_lines": recognition,
    }


def build_report(
    records: list[dict], args: argparse.Namespace, benchmark_pages: set[int]
) -> dict:
    geometry_by_id = {
        page["id"]: page for page in load_json(args.geometry)["pages"]
    }
    by_page: dict[str, list[dict]] = {}
    for record in records:
        by_page.setdefault(record["page_id"], []).append(record)
    benchmark = []
    comparison = []
    for identifier, page_records in sorted(by_page.items()):
        number = int(identifier.removeprefix("bnf-f"))
        if identifier not in geometry_by_id or not (LEVEL1 / f"{identifier}.json").exists():
            continue
        is_benchmark = number in benchmark_pages
        metrics, lines, _ = compare_page(
            identifier,
            page_records,
            geometry_by_id[identifier],
            alignment_mode="position" if is_benchmark else "text",
        )
        value = {"page_id": identifier, "metrics": metrics, "lines": lines}
        (benchmark if is_benchmark else comparison).append(value)
    return {
        "format": "nippo-calamari-page-draft-comparison",
        "format_version": 1,
        "method": {
            "draft_inputs": ["native page scan"],
            "draft_does_not_read": [
                "existing transcription",
                "canonical line geometry",
                "human review state",
            ],
            "benchmark_alignment": "monotonic scan-y alignment; OCR text excluded",
            "unreviewed_comparison_alignment": (
                "monotonic OCR/current-text alignment performed only after independent draft output"
            ),
            "recognition_scope": "plain physical-line text; typeface excluded",
            "line_image": {
                "mode": args.line_image,
                "scan_band_height": args.scan_band_height
                if args.line_image == "scan-band"
                else None,
                "normalized_height": args.height,
                "maximum_normalized_width": args.max_width,
            },
        },
        "benchmark": {
            "note": "Human-reviewed pages from the page-disjoint OCR test split.",
            "aggregate": aggregate_metrics(benchmark),
            "pages": benchmark,
        },
        "unreviewed_comparison": {
            "note": (
                "Disagreement with the current f161-f170 draft is not an error label: "
                "neither side has received human review."
            ),
            "aggregate": aggregate_metrics(comparison),
            "pages": comparison,
        },
    }


def report_markdown(report: dict) -> str:
    lines = [
        "# Calamari page-draft trial",
        "",
        "The page drafts were generated from native scans without reading the existing",
        "transcription or canonical geometry. The reviewed benchmark uses position-only",
        "alignment. The unreviewed comparison uses text/order alignment only after draft",
        "generation, so it can expose suspect saved geometry. Typeface, indentation, and",
        "furniture classification are outside this trial.",
        "",
        "| Set | Pages | Detected lines | Recall | CER | Exact lines |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, label in (("benchmark", "Reviewed benchmark"), ("unreviewed_comparison", "f161-f170 current draft")):
        aggregate = report[key]["aggregate"]
        recognition = aggregate["recognition_on_position_matched_lines"]
        lines.append(
            f"| {label} | {aggregate['pages']} | {aggregate['matched_body_lines']}/"
            f"{aggregate['canonical_body_lines']} | {aggregate['line_detection_recall']:.2%} | "
            f"{recognition.get('character_error_rate', 0):.2%} | "
            f"{recognition.get('exact_line_rate', 0):.2%} |"
        )
    lines.extend(["", "## Per-page results", "", "| Page | Role | Recall | CER | Exact lines | Extra body detections |", "| --- | --- | ---: | ---: | ---: | ---: |"])
    for key, label in (("benchmark", "benchmark"), ("unreviewed_comparison", "unreviewed comparison")):
        for page in report[key]["pages"]:
            metrics = page["metrics"]
            lines.append(
                f"| {page['page_id']} | {label} | {metrics['line_detection_recall']:.2%} | "
                f"{metrics['character_error_rate']:.2%} | {metrics['exact_line_rate']:.2%} | "
                f"{len(metrics['extra_detections_inside_body_band'])} |"
            )
    return "\n".join(lines) + "\n"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--pages", nargs="+", type=int, default=DEFAULT_PAGES)
    result.add_argument(
        "--benchmark-pages", nargs="*", type=int, default=DEFAULT_BENCHMARK_PAGES
    )
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--scans", type=Path, default=SCANS)
    result.add_argument("--geometry", type=Path, default=GEOMETRY)
    result.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    result.add_argument("--calamari", type=Path, default=DEFAULT_CALAMARI)
    result.add_argument("--kraken", type=Path, default=DEFAULT_KRAKEN)
    result.add_argument("--kraken-python", type=Path, default=DEFAULT_KRAKEN_PYTHON)
    result.add_argument("--height", type=int, default=48)
    result.add_argument("--max-width", type=int, default=1024)
    result.add_argument(
        "--line-image", choices=("scan-band", "rectified"), default="scan-band"
    )
    result.add_argument("--scan-band-height", type=int, default=72)
    result.add_argument("--batch-size", type=int, default=32)
    result.add_argument("--num-processes", type=int, default=2)
    result.add_argument("--segmentation-workers", type=int, default=3)
    result.add_argument("--fresh-segmentation", action="store_true")
    result.add_argument("--fresh-recognition", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.segmentation = args.output / "segmentation"
    args.extracted = args.output / "extracted"
    args.prepared = args.output / "prepared"
    args.predictions = args.output / "predictions"
    args.drafts = args.output / "drafts"
    page_numbers = sorted(set(args.pages) | set(args.benchmark_pages))
    ensure_segmentations(page_numbers, args)
    if args.line_image == "rectified":
        ensure_extracted(page_numbers, args)
    records = prepare_candidates(page_numbers, args)
    run_calamari(records, args)
    write_drafts(records, args)
    report = build_report(records, args, set(args.benchmark_pages))
    write_json(args.output / "comparison.json", report)
    (args.output / "comparison.md").write_text(
        report_markdown(report), encoding="utf-8"
    )
    counts = Counter(record["page_id"] for record in records)
    print(
        f"wrote {len(counts)} page drafts and {len(records)} detected lines to "
        f"{args.output}"
    )
    print(args.output / "comparison.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
