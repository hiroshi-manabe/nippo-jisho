#!/usr/bin/env python3
"""Infer page-line geometry from scans without consulting saved rectangles.

The input to inference is deliberately limited to a native scan, independent
Kraken segmentation, and the ordered Level 1 line texts.  Production geometry
is loaded only after alignment, to report comparison statistics.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics
import unicodedata

from PIL import Image

from build_clean_ocr_pairs import GEOMETRY_PATH, LEVEL1, ROOT, SCANS, normalized_line
from build_ocr_dataset import load_json, write_json


DEFAULT_PAGES = (147, 151, 154, 157)
DEFAULT_ROOT = ROOT / ".cache" / "ocr-first-geometry-v1"
DEFAULT_SEGMENTATION = DEFAULT_ROOT / "segmentation"
DEFAULT_EXTRACTED = DEFAULT_ROOT / "extracted"
DEFAULT_OUTPUT = DEFAULT_ROOT / "aligned"
DEFAULT_CHECKPOINT = (
    ROOT / ".cache" / "ocr-model" / "runs" / "trocr-isolated-core-v1" / "best"
)


def edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for row, left_character in enumerate(left, start=1):
        current = [row]
        for column, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def line_text(line: dict) -> str:
    return unicodedata.normalize(
        "NFC", "".join(run["text"] for run in line["runs"]).strip()
    )


def ordered_targets(page: dict) -> dict[str, list[dict]]:
    """Return body lines in document order, without reading geometry."""
    result: dict[str, list[dict]] = {}
    for zone in page["zones"]:
        if zone.get("kind") != "column":
            continue
        column = zone["id"]
        result[column] = [
            {
                "id": line["id"],
                "text": line_text(line),
                "index": index,
            }
            for index, line in enumerate(zone.get("lines", []))
        ]
    return result


def baseline_mean(line: dict, coordinate: int) -> float:
    return statistics.mean(point[coordinate] for point in line["baseline"])


def split_candidates(segmentation: dict, image_width: int) -> dict[str, list[dict]]:
    """Assign blind segmenter output to the two page halves and vertical order."""
    result: dict[str, list[dict]] = {"column-1": [], "column-2": []}
    for line in segmentation["lines"]:
        column = "column-1" if baseline_mean(line, 0) < image_width / 2 else "column-2"
        result[column].append(
            {
                **line,
                "centre_x": baseline_mean(line, 0),
                "centre_y": baseline_mean(line, 1),
            }
        )
    for candidates in result.values():
        candidates.sort(key=lambda line: (line["centre_y"], line["centre_x"]))
        for index, candidate in enumerate(candidates):
            candidate["index"] = index
    return result


def comparison_text(text: str) -> str:
    """Relax glyph distinctions that are irrelevant to line identity."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    plain = plain.replace("ſ", "s")
    plain = plain.translate(str.maketrans({"v": "u", "j": "i"}))
    return re.sub(r"[^a-z0-9]+", "", plain)


def normalized_distance(reference: str, hypothesis: str) -> float:
    left = comparison_text(reference)
    right = comparison_text(hypothesis)
    return edit_distance(left, right) / max(1, len(left))


def sequence_alignment(
    references: list[dict],
    candidates: list[dict],
    *,
    gap_cost: float,
    position_cost: float,
    maximum_displacement: int,
) -> list[tuple[int | None, int | None]]:
    """Globally align ordered texts and blind OCR candidates."""
    rows, columns = len(references), len(candidates)
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
            displacement = abs((row - 1) - (column - 1))
            match_cost = float("inf")
            if displacement <= maximum_displacement:
                match_cost = (
                    costs[row - 1][column - 1]
                    + normalized_distance(
                        references[row - 1]["text"],
                        candidates[column - 1]["recognition"],
                    )
                    + position_cost * displacement
                )
            choices = (
                (match_cost, "match"),
                (costs[row - 1][column] + gap_cost, "reference_gap"),
                (costs[row][column - 1] + gap_cost, "candidate_gap"),
            )
            costs[row][column], steps[row][column] = min(
                choices, key=lambda choice: choice[0]
            )
    alignment = []
    row, column = rows, columns
    while row or column:
        step = steps[row][column]
        if step == "match":
            alignment.append((row - 1, column - 1))
            row -= 1
            column -= 1
        elif step == "reference_gap":
            alignment.append((row - 1, None))
            row -= 1
        else:
            alignment.append((None, column - 1))
            column -= 1
    return list(reversed(alignment))


def rescue_sandwiched_gaps(
    alignment: list[tuple[int | None, int | None]],
    reference_count: int,
    candidate_count: int,
) -> tuple[list[tuple[int | None, int | None]], list[tuple[int, int]]]:
    """Match a single OCR-garbled row uniquely enclosed by two good matches."""
    matches = {
        reference: candidate
        for reference, candidate in alignment
        if reference is not None and candidate is not None
    }
    unmatched_references = {
        reference
        for reference, candidate in alignment
        if reference is not None and candidate is None
    }
    unmatched_candidates = {
        candidate
        for reference, candidate in alignment
        if reference is None and candidate is not None
    }
    rescued = []
    for reference in sorted(unmatched_references):
        if reference - 1 not in matches or reference + 1 not in matches:
            continue
        left = matches[reference - 1]
        right = matches[reference + 1]
        candidate = left + 1
        if right == candidate + 1 and candidate in unmatched_candidates:
            matches[reference] = candidate
            unmatched_references.remove(reference)
            unmatched_candidates.remove(candidate)
            rescued.append((reference, candidate))

    rebuilt = []
    next_reference = 0
    next_candidate = 0
    for reference, candidate in sorted(matches.items()):
        while next_reference < reference:
            rebuilt.append((next_reference, None))
            next_reference += 1
        while next_candidate < candidate:
            rebuilt.append((None, next_candidate))
            next_candidate += 1
        rebuilt.append((reference, candidate))
        next_reference = reference + 1
        next_candidate = candidate + 1
    while next_reference < reference_count:
        rebuilt.append((next_reference, None))
        next_reference += 1
    while next_candidate < candidate_count:
        rebuilt.append((None, next_candidate))
        next_candidate += 1
    return rebuilt, rescued


def polygon_bbox(line: dict, image_size: tuple[int, int]) -> list[int]:
    points = line.get("boundary") or line["baseline"]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    width, height = image_size
    left = max(0, round(min(xs)) - 10)
    top = max(0, round(min(ys)) - 10)
    right = min(width, round(max(xs)) + 11)
    bottom = min(height, round(max(ys)) + 11)
    return [left, top, max(1, right - left), max(1, bottom - top)]


def save_candidate_images(
    *,
    page_id: str,
    candidates: dict[str, list[dict]],
    extracted_root: Path,
    output: Path,
    height: int,
    max_width: int,
) -> None:
    for column, lines in candidates.items():
        for line in lines:
            source = extracted_root / page_id / f"{line['id']}.png"
            if not source.exists():
                raise FileNotFoundError(source)
            with Image.open(source) as image:
                prepared = normalized_line(image, height=height, max_width=max_width)
            relative = Path("images") / page_id / column / f"k{line['index'] + 1:03d}.png"
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            prepared.save(destination, format="PNG", optimize=True)
            line["image"] = relative.as_posix()
            line["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()


def prediction_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            record = json.loads(raw)
            result[record["sha256"]] = record["recognition"]
    return result


def recognize_candidates(candidates: list[dict], args: argparse.Namespace) -> None:
    import torch
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    cache_path = args.output / "predictions.jsonl"
    cache = prediction_cache(cache_path)
    for candidate in candidates:
        candidate["recognition"] = cache.get(candidate["sha256"])
    pending = [candidate for candidate in candidates if candidate["recognition"] is None]
    if not pending:
        return
    processor = TrOCRProcessor.from_pretrained(args.checkpoint, use_fast=False)
    model = VisionEncoderDecoderModel.from_pretrained(args.checkpoint)
    model.encoder.config._attn_implementation = "eager"
    model.decoder.config._attn_implementation = "eager"
    if args.device != "auto":
        device = torch.device(args.device)
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    model.to(device).eval()
    with cache_path.open("a", encoding="utf-8") as stream, torch.inference_mode():
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start : start + args.batch_size]
            images = []
            for candidate in batch:
                with Image.open(args.output / candidate["image"]) as image:
                    images.append(image.convert("RGB"))
            pixels = processor(images=images, return_tensors="pt").pixel_values.to(device)
            generated = model.generate(pixels, max_length=args.max_length, num_beams=1)
            decoded = processor.batch_decode(
                generated,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            for candidate, raw in zip(batch, decoded):
                candidate["recognition"] = raw.replace("§", "ſ")
                stream.write(
                    json.dumps(
                        {
                            "sha256": candidate["sha256"],
                            "recognition": candidate["recognition"],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            stream.flush()
            print(
                f"recognized {min(len(pending), start + len(batch))}/{len(pending)}",
                flush=True,
            )


def inferred_column_box(
    matched_candidates: list[dict], image_size: tuple[int, int]
) -> list[int]:
    """Derive a generous review box solely from matched baseline extents."""
    width, height = image_size
    xs = [point[0] for line in matched_candidates for point in line["baseline"]]
    ys = [point[1] for line in matched_candidates for point in line["baseline"]]
    left = max(0, round(min(xs)) - 45)
    right = min(width, round(max(xs)) + 46)
    top = max(0, round(min(ys)) - 125)
    bottom = min(height, round(max(ys)) + 125)
    return [left, top, right, bottom]


def geometry_for_matches(
    *,
    page_id: str,
    image_size: tuple[int, int],
    targets: dict[str, list[dict]],
    candidates: dict[str, list[dict]],
    alignments: dict[str, list[tuple[int | None, int | None]]],
) -> dict:
    page = {"id": page_id, "source_size": list(image_size), "columns": {}}
    for column, alignment in alignments.items():
        matched_candidates = [
            candidates[column][candidate_index]
            for reference_index, candidate_index in alignment
            if reference_index is not None and candidate_index is not None
        ]
        box = inferred_column_box(matched_candidates, image_size)
        line_geometry = {}
        selected_by_reference = {
            reference_index: candidate_index
            for reference_index, candidate_index in alignment
            if reference_index is not None and candidate_index is not None
        }
        for reference_index, reference in enumerate(targets[column]):
            if reference_index not in selected_by_reference:
                continue
            candidate = candidates[column][selected_by_reference[reference_index]]
            _, top, _, crop_height = polygon_bbox(candidate, image_size)
            bottom = top + crop_height
            # A 96-pixel minimum preserves ascenders/descenders and allows the
            # adjacent-row overlap preferred by the human review interface.
            centre = round(candidate["centre_y"])
            if crop_height < 96:
                top = max(0, centre - 48)
                bottom = min(image_size[1], centre + 48)
            crop = [box[0], top, box[2] - box[0], bottom - top]
            context_top = max(box[1], top - 105)
            context_bottom = min(box[3], bottom + 105)
            line_geometry[reference["id"]] = {
                "centre_y": centre,
                "crop": crop,
                "context_crop": [
                    box[0],
                    context_top,
                    box[2] - box[0],
                    context_bottom - context_top,
                ],
            }
        page["columns"][column] = {"box": box, "lines": line_geometry}
    return page


def benchmark_page(
    inferred: dict,
    production: dict | None,
    targets: dict[str, list[dict]],
    candidates: dict[str, list[dict]],
    alignments: dict[str, list[tuple[int | None, int | None]]],
    positional_rescues: dict[str, list[tuple[int, int]]],
) -> dict:
    matched = []
    unmatched_targets = []
    unmatched_candidates = []
    current_errors = []
    current_row_agreements = 0
    neighbor_conflicts = []
    for column, alignment in alignments.items():
        for reference_index, candidate_index in alignment:
            if reference_index is None:
                unmatched_candidates.append(candidates[column][candidate_index]["id"])
                continue
            reference = targets[column][reference_index]
            if candidate_index is None:
                unmatched_targets.append(reference["id"])
                continue
            candidate = candidates[column][candidate_index]
            distance = normalized_distance(reference["text"], candidate["recognition"])
            neighbor_distances = []
            for neighbor_index in (reference_index - 1, reference_index + 1):
                if 0 <= neighbor_index < len(targets[column]):
                    neighbor = targets[column][neighbor_index]
                    neighbor_distances.append(
                        (
                            neighbor["id"],
                            normalized_distance(
                                neighbor["text"], candidate["recognition"]
                            ),
                        )
                    )
            neighbor_margin = (
                min(value for _, value in neighbor_distances) - distance
                if neighbor_distances
                else None
            )
            record = {
                "line_id": reference["id"],
                "candidate_id": candidate["id"],
                "candidate_index": candidate_index,
                "target_index": reference_index,
                "recognition": candidate["recognition"],
                "recognition_cer_relaxed": distance,
                "neighbor_margin": neighbor_margin,
                "centre_y": round(candidate["centre_y"]),
            }
            if neighbor_margin is not None and neighbor_margin < -0.05:
                neighbor_conflicts.append(
                    {
                        "line_id": reference["id"],
                        "recognition": candidate["recognition"],
                        "target_distance": distance,
                        "closer_neighbor": min(
                            neighbor_distances, key=lambda item: item[1]
                        )[0],
                        "neighbor_margin": neighbor_margin,
                    }
                )
            if production and reference["id"] in production["columns"][column]["lines"]:
                old_y = production["columns"][column]["lines"][reference["id"]][
                    "centre_y"
                ]
                error = abs(old_y - candidate["centre_y"])
                record["production_centre_y"] = old_y
                record["production_centre_error"] = error
                current_errors.append(error)
                ordered = list(production["columns"][column]["lines"])
                old_index = ordered.index(reference["id"])
                neighbours = []
                if old_index:
                    neighbours.append(
                        production["columns"][column]["lines"][ordered[old_index - 1]][
                            "centre_y"
                        ]
                    )
                if old_index + 1 < len(ordered):
                    neighbours.append(
                        production["columns"][column]["lines"][ordered[old_index + 1]][
                            "centre_y"
                        ]
                    )
                tolerance = min([abs(old_y - value) / 2 for value in neighbours] or [35])
                if error <= tolerance:
                    current_row_agreements += 1
            matched.append(record)
    return {
        "targets": sum(len(lines) for lines in targets.values()),
        "candidates": sum(len(lines) for lines in candidates.values()),
        "matched": len(matched),
        "unmatched_targets": unmatched_targets,
        "unmatched_candidates": unmatched_candidates,
        "positional_rescues": [
            {
                "column": column,
                "line_id": targets[column][reference]["id"],
                "candidate_id": candidates[column][candidate]["id"],
            }
            for column, rescues in positional_rescues.items()
            for reference, candidate in rescues
        ],
        "neighbor_conflicts": neighbor_conflicts,
        "mean_relaxed_cer": statistics.mean(
            record["recognition_cer_relaxed"] for record in matched
        ),
        "median_relaxed_cer": statistics.median(
            record["recognition_cer_relaxed"] for record in matched
        ),
        "production_comparison": {
            "compared": len(current_errors),
            "median_centre_error": statistics.median(current_errors)
            if current_errors
            else None,
            "p95_centre_error": sorted(current_errors)[
                min(len(current_errors) - 1, round(0.95 * (len(current_errors) - 1)))
            ]
            if current_errors
            else None,
            "same_production_row_band": current_row_agreements,
        },
        "lines": matched,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--pages", nargs="+", type=int, default=DEFAULT_PAGES)
    result.add_argument("--segmentation", type=Path, default=DEFAULT_SEGMENTATION)
    result.add_argument("--extracted", type=Path, default=DEFAULT_EXTRACTED)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    result.add_argument("--device", default="auto")
    result.add_argument("--batch-size", type=int, default=16)
    result.add_argument("--max-length", type=int, default=96)
    result.add_argument("--height", type=int, default=48)
    result.add_argument("--max-width", type=int, default=1024)
    result.add_argument("--gap-cost", type=float, default=0.55)
    result.add_argument("--position-cost", type=float, default=0.005)
    result.add_argument("--maximum-displacement", type=int, default=12)
    return result


def main() -> int:
    args = parser().parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    page_records = []
    all_candidates = []
    for page_number in args.pages:
        page_id = f"bnf-f{page_number:04d}"
        scan_path = SCANS / f"f{page_number:04d}.jpg"
        with Image.open(scan_path) as scan:
            image_size = scan.size
        targets = ordered_targets(load_json(LEVEL1 / f"{page_id}.json"))
        segmentation = load_json(args.segmentation / f"f{page_number:04d}.json")
        candidates = split_candidates(segmentation, image_size[0])
        save_candidate_images(
            page_id=page_id,
            candidates=candidates,
            extracted_root=args.extracted,
            output=args.output,
            height=args.height,
            max_width=args.max_width,
        )
        all_candidates.extend(
            candidate for lines in candidates.values() for candidate in lines
        )
        page_records.append((page_id, image_size, targets, candidates))
    recognize_candidates(all_candidates, args)

    inferred_records = []
    for page_id, image_size, targets, candidates in page_records:
        alignments = {}
        positional_rescues = {}
        for column in targets:
            alignment = sequence_alignment(
                targets[column],
                candidates[column],
                gap_cost=args.gap_cost,
                position_cost=args.position_cost,
                maximum_displacement=args.maximum_displacement,
            )
            alignment, rescues = rescue_sandwiched_gaps(
                alignment,
                len(targets[column]),
                len(candidates[column]),
            )
            alignments[column] = alignment
            positional_rescues[column] = rescues
        inferred = geometry_for_matches(
            page_id=page_id,
            image_size=image_size,
            targets=targets,
            candidates=candidates,
            alignments=alignments,
        )
        inferred_records.append(
            (
                page_id,
                targets,
                candidates,
                alignments,
                positional_rescues,
                inferred,
            )
        )

    # Production geometry is intentionally not opened until every proposed
    # association and rectangle has been inferred.
    production_by_id = {
        page["id"]: page for page in load_json(GEOMETRY_PATH)["pages"]
    }
    geometry_pages = []
    reports = {}
    for (
        page_id,
        targets,
        candidates,
        alignments,
        positional_rescues,
        inferred,
    ) in inferred_records:
        geometry_pages.append(inferred)
        reports[page_id] = benchmark_page(
            inferred,
            production_by_id.get(page_id),
            targets,
            candidates,
            alignments,
            positional_rescues,
        )
        print(
            f"{page_id}: {reports[page_id]['matched']}/{reports[page_id]['targets']} "
            f"matched; median relaxed CER "
            f"{reports[page_id]['median_relaxed_cer']:.3f}",
            flush=True,
        )
    write_json(
        args.output / "line-geometry.json",
        {
            "format": "nippo-line-geometry",
            "format_version": 1,
            "method": "ocr-first-blind-to-production-geometry",
            "pages": geometry_pages,
        },
    )
    write_json(
        args.output / "report.json",
        {
            "format": "nippo-ocr-first-geometry-benchmark",
            "format_version": 1,
            "pages": list(args.pages),
            "inference_inputs": [
                "native scan",
                "independent Kraken segmentation",
                "ordered Level 1 line text",
            ],
            "excluded_from_inference": [
                "production column boxes",
                "production line centres",
                "production crop rectangles",
            ],
            "results": reports,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
