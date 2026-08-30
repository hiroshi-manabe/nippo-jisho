#!/usr/bin/env python3
"""Build conservative isolated-line image/text pairs for Nippo Jisho OCR."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from build_ocr_dataset import ROOT, line_texts, load_json, trim_horizontal


DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "clean-lines-v1"
GEOMETRY_PATH = ROOT / "pilot" / "human-review" / "line-geometry.json"
LEVEL1 = ROOT / "pilot" / "format-v1-trial" / "level1"
SCANS = ROOT / "build" / "nippo-jisho-images" / "scans" / "native"
SPLIT_PATH = ROOT / "experiments" / "ocr" / "f13-f150-split.json"
LINE_ID = re.compile(r"^(?P<block>.+)-l\d+(?:#\d+)?$")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def block_name(line_id: str) -> str:
    match = LINE_ID.match(line_id)
    return match.group("block") if match else line_id


def split_map(first_page: int, last_page: int) -> dict[str, str]:
    specification = load_json(SPLIT_PATH)
    dev = set(specification["dev"])
    test = set(specification["test"])
    result = {}
    for number in range(first_page, last_page + 1):
        split = "dev" if number in dev else "test" if number in test else "train"
        result[f"bnf-f{number:04d}"] = split
    return result


def median_gap(entries: list[tuple[str, dict]]) -> float:
    centres = sorted({line["centre_y"] for _, line in entries})
    gaps = [right - left for left, right in zip(centres, centres[1:])]
    ordinary = [gap for gap in gaps if 40 <= gap <= 90]
    return statistics.median(ordinary or gaps or [62])


def isolated_crop(
    line: dict,
    previous: dict | None,
    following: dict | None,
    *,
    fallback_gap: float,
    source_height: int,
    padding: int,
) -> list[int]:
    """Bound the target near neighbour midpoints inside the review crop."""
    x, original_y, width, original_height = line["crop"]
    centre = line["centre_y"]
    if previous is None:
        top = round(centre - fallback_gap / 2 - padding)
    else:
        top = round((previous["centre_y"] + centre) / 2 - padding)
    if following is None:
        bottom = round(centre + fallback_gap / 2 + padding)
    else:
        bottom = round((centre + following["centre_y"]) / 2 + padding)
    top = max(0, original_y, top)
    bottom = min(source_height, original_y + original_height, bottom)
    return [x, top, width, max(1, bottom - top)]


def otsu_threshold(array: np.ndarray) -> int:
    histogram = np.bincount(array.ravel(), minlength=256).astype(np.float64)
    total = array.size
    cumulative_weight = np.cumsum(histogram)
    cumulative_mean = np.cumsum(histogram * np.arange(256))
    global_mean = cumulative_mean[-1]
    denominator = cumulative_weight * (total - cumulative_weight)
    numerator = (global_mean * cumulative_weight - cumulative_mean * total) ** 2
    variance = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=denominator > 0,
    )
    return int(np.argmax(variance))


def estimate_skew(mask: np.ndarray) -> tuple[float | None, float | None, int]:
    """Estimate text-line angle from median ink height in occupied x bins."""
    height, width = mask.shape
    column_counts = mask.sum(axis=0)
    occupied = np.flatnonzero(column_counts >= 2)
    if occupied.size < 40:
        return None, None, 0
    left, right = int(occupied.min()), int(occupied.max()) + 1
    bin_width = max(24, (right - left) // 16)
    points: list[tuple[float, float]] = []
    for start in range(left, right, bin_width):
        stop = min(right, start + bin_width)
        ys, _ = np.nonzero(mask[:, start:stop])
        if ys.size >= max(15, bin_width // 2):
            points.append(((start + stop - 1) / 2, float(np.median(ys))))
    if len(points) < 5:
        return None, None, len(points)
    xs = np.asarray([point[0] for point in points])
    ys = np.asarray([point[1] for point in points])
    slope, intercept = np.polyfit(xs, ys, 1)
    residual = float(np.median(np.abs(ys - (slope * xs + intercept))))
    return math.degrees(math.atan(float(slope))), residual, len(points)


def row_segments(active: np.ndarray, *, maximum_gap: int = 2) -> list[tuple[int, int]]:
    rows = np.flatnonzero(active)
    if not rows.size:
        return []
    segments = []
    start = previous = int(rows[0])
    for row in rows[1:]:
        row = int(row)
        if row - previous > maximum_gap + 1:
            segments.append((start, previous + 1))
            start = row
        previous = row
    segments.append((start, previous + 1))
    return segments


def visual_metrics(
    image: Image.Image, text: str, *, target_center_y: float
) -> tuple[dict, list[str], tuple[int, int] | None]:
    gray = ImageOps.autocontrast(image.convert("L"), cutoff=0.2)
    array = np.asarray(gray)
    threshold = min(205, max(80, otsu_threshold(array)))
    mask = array < threshold
    dense_columns = mask.mean(axis=0) > 0.62
    mask[:, dense_columns] = False
    row_counts = mask.sum(axis=1)
    smoothed_rows = np.convolve(row_counts, np.ones(5), mode="same")
    peak = float(smoothed_rows.max(initial=0))
    segments = row_segments(smoothed_rows >= max(45, peak * 0.30))
    substantial = [
        segment
        for segment in segments
        if segment[1] - segment[0] >= 4
        and row_counts[segment[0] : segment[1]].sum() >= 80
    ]
    target_segment = (
        min(
            substantial,
            key=lambda segment: abs((segment[0] + segment[1] - 1) / 2 - target_center_y),
        )
        if substantial
        else None
    )
    if target_segment:
        top, bottom = target_segment
        low_threshold = max(5, int(row_counts.max(initial=0) * 0.12))
        while top > 0 and row_counts[top - 1] >= low_threshold:
            top -= 1
        while bottom < image.height and row_counts[bottom] >= low_threshold:
            bottom += 1
        target_segment = (top, bottom)
        target_mask = mask[top:bottom]
    else:
        target_mask = mask
    column_counts = target_mask.sum(axis=0)
    occupied_columns = np.flatnonzero(
        column_counts >= max(2, round(target_mask.shape[0] * 0.08))
    )
    dark_pixels = int(mask.sum())
    target_dark_pixels = int(target_mask.sum())
    skew, skew_residual, skew_bins = estimate_skew(target_mask)
    nonspace_characters = max(1, sum(not character.isspace() for character in text))

    band_centre = (
        (target_segment[0] + target_segment[1] - 1) / 2 if target_segment else None
    )
    band_height = target_segment[1] - target_segment[0] if target_segment else 0
    competing_segments = []
    if target_segment:
        target_area = int(row_counts[target_segment[0] : target_segment[1]].sum())
        for segment in substantial:
            if segment[0] < target_segment[1] and segment[1] > target_segment[0]:
                continue
            area = int(row_counts[segment[0] : segment[1]].sum())
            if area >= target_area * 0.35:
                competing_segments.append([segment[0], segment[1], area])

    metrics = {
        "threshold": threshold,
        "dark_pixels": dark_pixels,
        "target_dark_pixels": target_dark_pixels,
        "peak_smoothed_row_ink": peak,
        "target_center_y": target_center_y,
        "target_band": list(target_segment) if target_segment else None,
        "target_band_center": band_centre,
        "target_band_height": band_height,
        "competing_bands": competing_segments,
        "ink_width": (
            int(occupied_columns.max() - occupied_columns.min() + 1)
            if occupied_columns.size
            else 0
        ),
        "character_pitch": (
            float(
                (occupied_columns.max() - occupied_columns.min() + 1)
                / nonspace_characters
            )
            if occupied_columns.size
            else 0.0
        ),
        "skew_degrees": skew,
        "skew_residual": skew_residual,
        "skew_bins": skew_bins,
    }
    reasons = []
    if target_segment is None or target_dark_pixels < 80 or peak < 30:
        reasons.append("insufficient_ink")
    if target_segment and (target_segment[0] == 0 or target_segment[1] == image.height):
        reasons.append("target_band_at_crop_edge")
    if target_segment and abs(band_centre - target_center_y) > image.height * 0.22:
        reasons.append("target_band_mismatch")
    if not 10 <= band_height <= 70:
        reasons.append("implausible_target_band_height")
    if not 3 <= metrics["character_pitch"] <= 90:
        reasons.append("implausible_text_ink_ratio")
    if skew is None:
        reasons.append("skew_unmeasurable")
    elif abs(skew) > 1.2:
        reasons.append("excessive_skew")
    if skew_residual is not None and skew_residual > 10:
        reasons.append("irregular_baseline")
    return metrics, reasons, target_segment


def normalized_line(image: Image.Image, *, height: int, max_width: int) -> Image.Image:
    line = ImageOps.autocontrast(image.convert("L"), cutoff=0.2)
    line = trim_horizontal(line)
    width = min(max_width, max(1, round(line.width * height / line.height)))
    return line.resize((width, height), Image.Resampling.LANCZOS)


def save_line(image: Image.Image, path: Path, *, height: int, max_width: int) -> dict:
    line = normalized_line(image, height=height, max_width=max_width)
    path.parent.mkdir(parents=True, exist_ok=True)
    line.save(path, format="PNG", optimize=True)
    return {
        "width": line.width,
        "height": line.height,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def font(size: int) -> ImageFont.ImageFont:
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    )
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def audit_sheet(
    records: list[dict], output: Path, *, dataset_root: Path, title: str
) -> None:
    if not records:
        return
    display_width = 1150
    line_height = 48
    label_height = 34
    header_height = 42
    sheet_height = header_height + len(records) * (line_height + label_height)
    sheet = Image.new("RGB", (display_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 8), title, fill="black", font=font(22))
    label_font = font(16)
    y = header_height
    for record in records:
        image_path = dataset_root / record["image"]
        if image_path.exists():
            with Image.open(image_path) as source:
                line = source.convert("RGB")
            if line.width > display_width:
                line.thumbnail((display_width, line_height), Image.Resampling.LANCZOS)
            sheet.paste(line, (0, y))
        reasons = ",".join(record.get("reasons", [])) or "accepted"
        label = f"{record['id']} [{reasons}]  {record['text']}"
        draw.text((8, y + line_height + 4), label, fill="black", font=label_font)
        y += line_height + label_height
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG", optimize=True)


def build(args: argparse.Namespace) -> dict:
    geometry_pages = {page["id"]: page for page in load_json(GEOMETRY_PATH)["pages"]}
    page_splits = split_map(args.first_page, args.last_page)
    accepted: list[dict] = []
    rejected: list[dict] = []

    for number in range(args.first_page, args.last_page + 1):
        page_id = f"bnf-f{number:04d}"
        page_path = LEVEL1 / f"{page_id}.json"
        scan_path = SCANS / f"f{number:04d}.jpg"
        if page_id not in geometry_pages or not page_path.exists() or not scan_path.exists():
            raise FileNotFoundError(f"incomplete source package for {page_id}")
        texts = line_texts(load_json(page_path))
        geometry = geometry_pages[page_id]
        with Image.open(scan_path) as scan:
            if list(scan.size) != geometry["source_size"]:
                raise ValueError(f"{page_id}: scan and geometry dimensions differ")
            for column_name, column in geometry["columns"].items():
                groups: dict[str, list[tuple[str, dict]]] = defaultdict(list)
                duplicates = Counter(
                    (line["centre_y"], tuple(line["crop"]))
                    for line in column["lines"].values()
                )
                for line_id, line in column["lines"].items():
                    groups[block_name(line_id)].append((line_id, line))
                for block, entries in groups.items():
                    entries.sort(key=lambda item: (item[1]["centre_y"], item[0]))
                    fallback_gap = median_gap(entries)
                    for index, (line_id, line) in enumerate(entries):
                        text = texts.get(line_id)
                        reasons: list[str] = []
                        if text is None:
                            reasons.append("missing_text")
                            text = ""
                        if duplicates[(line["centre_y"], tuple(line["crop"]))] > 1:
                            reasons.append("duplicate_geometry")
                        previous = entries[index - 1][1] if index else None
                        following = entries[index + 1][1] if index + 1 < len(entries) else None
                        previous_gap = (
                            line["centre_y"] - previous["centre_y"] if previous else None
                        )
                        following_gap = (
                            following["centre_y"] - line["centre_y"] if following else None
                        )
                        for gap in (previous_gap, following_gap):
                            if gap is not None and not 35 <= gap <= 100:
                                reasons.append("irregular_local_spacing")
                                break
                        crop = isolated_crop(
                            line,
                            previous,
                            following,
                            fallback_gap=fallback_gap,
                            source_height=scan.height,
                            padding=args.vertical_padding,
                        )
                        if not 42 <= crop[3] <= 105:
                            reasons.append("implausible_crop_height")
                        isolation_window_crop = list(crop)
                        x, y, width, height = crop
                        isolation_window = scan.crop((x, y, x + width, y + height))
                        metrics, visual_reasons, target_band = visual_metrics(
                            isolation_window,
                            text,
                            target_center_y=line["centre_y"] - y,
                        )
                        reasons.extend(visual_reasons)
                        reasons = list(dict.fromkeys(reasons))
                        if target_band:
                            band_top, band_bottom = target_band
                            refined_top = max(0, band_top - args.band_padding)
                            refined_bottom = min(height, band_bottom + args.band_padding)
                            crop = [
                                x,
                                y + refined_top,
                                width,
                                refined_bottom - refined_top,
                            ]
                        x, y, width, height = crop
                        source_crop = scan.crop((x, y, x + width, y + height))
                        relative = Path("images") / page_id / f"{line_id}.png"
                        image_info = save_line(
                            source_crop,
                            args.output / relative,
                            height=args.height,
                            max_width=args.max_width,
                        )
                        record = {
                            "id": f"{page_id}/{line_id}",
                            "page_id": page_id,
                            "line_id": line_id,
                            "column": column_name,
                            "block": block,
                            "block_index": index,
                            "split": page_splits[page_id],
                            "text": text,
                            "image": relative.as_posix(),
                            "source_crop": crop,
                            "isolation_window": isolation_window_crop,
                            "review_crop": line["crop"],
                            "metrics": metrics,
                            **image_info,
                        }
                        if reasons:
                            record["reasons"] = reasons
                            rejected.append(record)
                        else:
                            accepted.append(record)

    for name, records in (("pairs", accepted), ("rejected", rejected)):
        with (args.output / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    for split in ("train", "dev", "test"):
        with (args.output / f"{split}.jsonl").open("w", encoding="utf-8") as stream:
            for record in accepted:
                if record["split"] == split:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    reason_counts = Counter(
        reason for record in rejected for reason in record["reasons"]
    )
    summary = {
        "format": "nippo-clean-ocr-pairs",
        "format_version": 1,
        "source_page_range": [args.first_page, args.last_page],
        "candidate_lines": len(accepted) + len(rejected),
        "accepted_lines": len(accepted),
        "rejected_lines": len(rejected),
        "acceptance_rate": len(accepted) / max(1, len(accepted) + len(rejected)),
        "accepted_by_split": dict(Counter(record["split"] for record in accepted)),
        "rejection_reasons": dict(reason_counts.most_common()),
        "criteria": {
            "vertical_boundaries": "neighbour-centre midpoints within canonical review crop",
            "vertical_padding": args.vertical_padding,
            "target_band_padding": args.band_padding,
            "crop_height_range": [42, 105],
            "maximum_absolute_skew_degrees": 1.2,
            "maximum_skew_residual_pixels": 10,
            "minimum_blank_edge_pixels": 1,
            "character_pitch_range": [3, 90],
        },
    }
    write_json(args.output / "summary.json", summary)

    rng = random.Random(args.seed)
    accepted_sample = rng.sample(accepted, min(args.audit_lines, len(accepted)))
    rejected_sample = []
    by_reason: dict[str, list[dict]] = defaultdict(list)
    for record in rejected:
        for reason in record["reasons"]:
            by_reason[reason].append(record)
    reason_names = sorted(by_reason)
    while len(rejected_sample) < min(args.audit_lines, len(rejected)) and reason_names:
        for reason in list(reason_names):
            choices = [record for record in by_reason[reason] if record not in rejected_sample]
            if choices:
                rejected_sample.append(rng.choice(choices))
                if len(rejected_sample) >= args.audit_lines:
                    break
            else:
                reason_names.remove(reason)
    for name, sample in (("accepted", accepted_sample), ("rejected", rejected_sample)):
        for index in range(0, len(sample), 20):
            audit_sheet(
                sample[index : index + 20],
                args.output / "audit" / f"{name}-{index // 20 + 1}.png",
                dataset_root=args.output,
                title=f"{name.title()} clean-pair audit {index // 20 + 1}",
            )
    return summary


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--first-page", type=int, default=13)
    result.add_argument("--last-page", type=int, default=150)
    result.add_argument("--vertical-padding", type=int, default=10)
    result.add_argument("--band-padding", type=int, default=6)
    result.add_argument("--height", type=int, default=48)
    result.add_argument("--max-width", type=int, default=1024)
    result.add_argument("--audit-lines", type=int, default=60)
    result.add_argument("--seed", type=int, default=1603)
    return result


def main() -> int:
    args = parser().parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    summary = build(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
