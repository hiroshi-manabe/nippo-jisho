#!/usr/bin/env python3
"""Compare Kraken line segmentation with the canonical Nippo line geometry."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import statistics

from PIL import Image
import torch

from align_clean_ocr_pairs import (
    load_recognizer,
    normalized_distance,
    sequence_alignment,
)
from build_clean_ocr_pairs import (
    GEOMETRY_PATH,
    LEVEL1,
    ROOT,
    SCANS,
    audit_sheet,
    normalized_line,
    write_json,
)
from build_ocr_dataset import line_texts, load_json
from train_nippo_trocr import decode_text


DEFAULT_PAGES = (
    13,
    18,
    24,
    31,
    46,
    58,
    68,
    83,
    96,
    110,
    123,
    125,
    136,
    143,
    150,
)
DEFAULT_KRAKEN = ROOT / ".cache" / "ocr-model" / "kraken-segmentation-v1"
DEFAULT_EXTRACTED = DEFAULT_KRAKEN / "extracted"
DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "kraken-line-benchmark-v1"
DEFAULT_CURRENT = ROOT / ".cache" / "ocr-model" / "usable-lines-v2"
DEFAULT_RUN = ROOT / ".cache" / "ocr-model" / "runs" / "trocr-small-v1"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def horizontal_overlap(line: dict, left: int, right: int) -> float:
    xs = [point[0] for point in line["baseline"]]
    return max(0, min(right, max(xs)) - max(left, min(xs)))


def line_bbox(line: dict, image_size: tuple[int, int]) -> list[int]:
    points = line.get("boundary") or line["baseline"]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    image_width, image_height = image_size
    left = max(0, round(min(xs)) - 12)
    top = max(0, round(min(ys)) - 5)
    right = min(image_width, round(max(xs)) + 13)
    bottom = min(image_height, round(max(ys)) + 6)
    return [left, top, max(1, right - left), max(1, bottom - top)]


def target_records(page: dict) -> dict[str, list[dict]]:
    page_data = load_json(LEVEL1 / f"{page['id']}.json")
    texts = line_texts(page_data)
    result = {}
    for column_name, column in page["columns"].items():
        lines = sorted(
            column["lines"].items(), key=lambda item: item[1]["centre_y"]
        )
        result[column_name] = [
            {
                "id": f"{page['id']}/{line_id}",
                "page_id": page["id"],
                "line_id": line_id,
                "column": column_name,
                "block_index": index,
                "centre_y": geometry["centre_y"],
                "text": texts[line_id],
            }
            for index, (line_id, geometry) in enumerate(lines)
        ]
    return result


def build_candidates(args: argparse.Namespace) -> tuple[list[dict], list[dict]]:
    geometry = {page["id"]: page for page in load_json(GEOMETRY_PATH)["pages"]}
    references = []
    candidates = []
    for page_number in args.pages:
        page_id = f"bnf-f{page_number:04d}"
        page = geometry[page_id]
        targets = target_records(page)
        for lines in targets.values():
            references.extend(lines)
        kraken_path = args.kraken / f"f{page_number:04d}.json"
        kraken = load_json(kraken_path)
        assigned: dict[str, list[dict]] = defaultdict(list)
        for line in kraken["lines"]:
            score, column_name = max(
                (
                    horizontal_overlap(
                        line, column["box"][0], column["box"][2]
                    ),
                    name,
                )
                for name, column in page["columns"].items()
            )
            if score:
                assigned[column_name].append(line)
        scan_path = SCANS / f"f{page_number:04d}.jpg"
        with Image.open(scan_path) as scan:
            for column_name, lines in targets.items():
                minimum_y = min(line["centre_y"] for line in lines) - 70
                maximum_y = max(line["centre_y"] for line in lines) + 70
                detections = sorted(
                    (
                        line
                        for line in assigned[column_name]
                        if minimum_y
                        <= statistics.mean(point[1] for point in line["baseline"])
                        <= maximum_y
                    ),
                    key=lambda line: statistics.mean(
                        point[1] for point in line["baseline"]
                    ),
                )
                for index, detection in enumerate(detections):
                    crop = line_bbox(detection, scan.size)
                    extracted_path = (
                        args.extracted / page_id / f"{detection['id']}.png"
                    )
                    if not extracted_path.exists():
                        raise FileNotFoundError(
                            f"missing rectified Kraken line: {extracted_path}"
                        )
                    with Image.open(extracted_path) as extracted:
                        image = normalized_line(
                            extracted,
                            height=args.height,
                            max_width=args.max_width,
                        )
                    relative = (
                        Path("images")
                        / page_id
                        / f"{column_name}-k{index + 1:03d}.png"
                    )
                    output_path = args.output / relative
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    image.save(output_path, format="PNG", optimize=True)
                    candidates.append(
                        {
                            "id": f"{page_id}/{column_name}-k{index + 1:03d}",
                            "page_id": page_id,
                            "column": column_name,
                            "block_index": index,
                            "baseline": detection["baseline"],
                            "boundary": detection.get("boundary"),
                            "crop": crop,
                            "image": relative.as_posix(),
                            "width": image.width,
                            "height": image.height,
                            "sha256": hashlib.sha256(
                                output_path.read_bytes()
                            ).hexdigest(),
                        }
                    )
    return references, candidates


def prediction_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        record["sha256"]: record["recognition"]
        for record in load_jsonl(path)
    }


@torch.inference_mode()
def recognize_records(
    records: list[dict],
    *,
    root: Path,
    cache_path: Path,
    runtime: tuple,
    batch_size: int,
    max_length: int,
) -> None:
    cache = prediction_cache(cache_path)
    for record in records:
        record["recognition"] = cache.get(record["sha256"])
    pending = [record for record in records if record["recognition"] is None]
    processor, model, device = runtime
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8") as stream:
        for start in range(0, len(pending), batch_size):
            batch = pending[start : start + batch_size]
            images = []
            for record in batch:
                with Image.open(root / record["image"]) as source:
                    images.append(source.convert("RGB"))
            pixels = processor(images=images, return_tensors="pt").pixel_values.to(
                device
            )
            generated = model.generate(
                pixels, max_length=max_length, num_beams=1
            )
            decoded = processor.batch_decode(
                generated,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            for record, prediction in zip(batch, decoded):
                recognition = decode_text(prediction)
                record["recognition"] = recognition
                stream.write(
                    json.dumps(
                        {"sha256": record["sha256"], "recognition": recognition},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            stream.flush()
            print(
                f"recognized {min(len(pending), start + len(batch))}/{len(pending)}",
                flush=True,
            )


def current_records(args: argparse.Namespace, reference_ids: set[str]) -> list[dict]:
    records = load_jsonl(args.current / "pairs.jsonl") + load_jsonl(
        args.current / "rejected.jsonl"
    )
    return [record for record in records if record["id"] in reference_ids]


def align_candidates(
    references: list[dict], candidates: list[dict], args: argparse.Namespace
) -> tuple[list[dict], list[dict], list[dict]]:
    reference_groups = defaultdict(list)
    candidate_groups = defaultdict(list)
    for record in references:
        reference_groups[(record["page_id"], record["column"])].append(record)
    for record in candidates:
        candidate_groups[(record["page_id"], record["column"])].append(record)
    matched = []
    unmatched_references = []
    unmatched_candidates = []
    for key, group_references in reference_groups.items():
        group_candidates = candidate_groups[key]
        alignment = sequence_alignment(
            group_references,
            group_candidates,
            gap_cost=args.gap_cost,
            position_cost=args.position_cost,
            maximum_displacement=args.maximum_displacement,
        )
        for reference_index, candidate_index in alignment:
            if reference_index is None:
                unmatched_candidates.append(group_candidates[candidate_index])
            elif candidate_index is None:
                unmatched_references.append(group_references[reference_index])
            else:
                reference = group_references[reference_index]
                candidate = group_candidates[candidate_index]
                matched.append(
                    {
                        **reference,
                        "image": candidate["image"],
                        "kraken_candidate_id": candidate["id"],
                        "kraken_crop": candidate["crop"],
                        "kraken_baseline": candidate["baseline"],
                        "kraken_boundary": candidate["boundary"],
                        "kraken_width": candidate["width"],
                        "kraken_height": candidate["height"],
                        "kraken_sha256": candidate["sha256"],
                        "recognition": candidate["recognition"],
                        "recognition_cer": normalized_distance(
                            reference["text"], candidate["recognition"]
                        ),
                        "alignment_displacement": (
                            candidate_index - reference_index
                        ),
                    }
                )
    return matched, unmatched_references, unmatched_candidates


def summarize(
    references: list[dict],
    candidates: list[dict],
    matched: list[dict],
    unmatched_references: list[dict],
    unmatched_candidates: list[dict],
    current: list[dict],
    accepted_ids: set[str],
    args: argparse.Namespace,
) -> dict:
    current_by_id = {record["id"]: record for record in current}
    comparisons = []
    for record in matched:
        current_record = current_by_id[record["id"]]
        current_cer = normalized_distance(
            record["text"], current_record["recognition"]
        )
        record["current_recognition"] = current_record["recognition"]
        record["current_recognition_cer"] = current_cer
        record["current_accepted"] = record["id"] in accepted_ids
        comparisons.append((record["recognition_cer"], current_cer))
    potential = [
        record
        for record in matched
        if not record["current_accepted"]
        and record["recognition_cer"] <= args.usable_cer
    ]
    per_page = {}
    for page_number in args.pages:
        page_id = f"bnf-f{page_number:04d}"
        page_references = [r for r in references if r["page_id"] == page_id]
        page_candidates = [r for r in candidates if r["page_id"] == page_id]
        page_matched = [r for r in matched if r["page_id"] == page_id]
        per_page[page_id] = {
            "canonical_lines": len(page_references),
            "kraken_body_candidates": len(page_candidates),
            "aligned_pairs": len(page_matched),
            "mean_kraken_crop_cer": statistics.mean(
                record["recognition_cer"] for record in page_matched
            ),
        }
    return {
        "format": "nippo-kraken-line-segmentation-benchmark",
        "format_version": 1,
        "pages": list(args.pages),
        "kraken_version": "5.2.9",
        "kraken_model": "bundled blla.mlmodel",
        "line_extraction": "kraken.lib.segmentation.extract_polygons",
        "canonical_lines": len(references),
        "kraken_body_candidates": len(candidates),
        "aligned_pairs": len(matched),
        "unmatched_canonical_lines": len(unmatched_references),
        "unmatched_kraken_candidates": len(unmatched_candidates),
        "line_alignment_recall": len(matched) / len(references),
        "crop_recognition": {
            "mean_current_cer": statistics.mean(current for _, current in comparisons),
            "mean_kraken_cer": statistics.mean(kraken for kraken, _ in comparisons),
            "median_current_cer": statistics.median(
                current for _, current in comparisons
            ),
            "median_kraken_cer": statistics.median(
                kraken for kraken, _ in comparisons
            ),
            "kraken_better": sum(kraken < current for kraken, current in comparisons),
            "equal": sum(kraken == current for kraken, current in comparisons),
            "current_better": sum(kraken > current for kraken, current in comparisons),
            "kraken_at_or_below_usable_cer": sum(
                record["recognition_cer"] <= args.usable_cer for record in matched
            ),
        },
        "currently_rejected_lines_on_benchmark_pages": sum(
            reference["id"] not in accepted_ids for reference in references
        ),
        "potentially_recovered_rejections": len(potential),
        "per_page": per_page,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--pages", nargs="+", type=int, default=DEFAULT_PAGES)
    result.add_argument("--kraken", type=Path, default=DEFAULT_KRAKEN)
    result.add_argument("--extracted", type=Path, default=DEFAULT_EXTRACTED)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    result.add_argument("--run", type=Path, default=DEFAULT_RUN)
    result.add_argument("--checkpoint", type=Path)
    result.add_argument("--device", default="auto")
    result.add_argument("--batch-size", type=int, default=16)
    result.add_argument("--max-length", type=int, default=48)
    result.add_argument("--height", type=int, default=48)
    result.add_argument("--max-width", type=int, default=1024)
    result.add_argument("--gap-cost", type=float, default=0.55)
    result.add_argument("--position-cost", type=float, default=0.01)
    result.add_argument("--maximum-displacement", type=int, default=12)
    result.add_argument("--usable-cer", type=float, default=0.60)
    result.add_argument("--seed", type=int, default=1603)
    return result


def main() -> int:
    args = parser().parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    references, candidates = build_candidates(args)
    runtime = load_recognizer(args)
    recognize_records(
        candidates,
        root=args.output,
        cache_path=args.output / "kraken-predictions.jsonl",
        runtime=runtime,
        batch_size=args.batch_size,
        max_length=args.max_length,
    )
    current = current_records(args, {record["id"] for record in references})
    recognize_records(
        current,
        root=args.current,
        cache_path=args.output / "current-predictions.jsonl",
        runtime=runtime,
        batch_size=args.batch_size,
        max_length=args.max_length,
    )
    matched, unmatched_references, unmatched_candidates = align_candidates(
        references, candidates, args
    )
    accepted_ids = {
        record["id"]
        for record in load_jsonl(args.current / "aligned-pairs.jsonl")
    }
    summary = summarize(
        references,
        candidates,
        matched,
        unmatched_references,
        unmatched_candidates,
        current,
        accepted_ids,
        args,
    )
    for name, records in (
        ("matched", matched),
        ("unmatched-references", unmatched_references),
        ("unmatched-candidates", unmatched_candidates),
    ):
        with (args.output / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_json(args.output / "summary.json", summary)
    rng = random.Random(args.seed)
    audit = rng.sample(matched, min(100, len(matched)))
    for index in range(0, len(audit), 20):
        sample = []
        for record in audit[index : index + 20]:
            sample.append(
                {
                    **record,
                    "reasons": [f"CER={record['recognition_cer']:.2f}"],
                }
            )
        audit_sheet(
            sample,
            args.output / "audit" / f"matched-{index // 20 + 1}.png",
            dataset_root=args.output,
            title=f"Kraken matched audit {index // 20 + 1}",
        )
    potential = [
        record
        for record in matched
        if not record["current_accepted"]
        and record["recognition_cer"] <= args.usable_cer
    ]
    for index in range(0, len(potential), 20):
        sample = [
            {
                **record,
                "reasons": [
                    f"K={record['recognition_cer']:.2f}",
                    f"current={record['current_recognition_cer']:.2f}",
                    f"d={record['alignment_displacement']}",
                ],
            }
            for record in potential[index : index + 20]
        ]
        audit_sheet(
            sample,
            args.output / "audit" / f"potential-recovery-{index // 20 + 1}.png",
            dataset_root=args.output,
            title=(
                f"Kraken potential recoveries {index + 1}-"
                f"{index + len(sample)}"
            ),
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
