#!/usr/bin/env python3
"""Align isolated Nippo line candidates to reviewed text with the v1 recognizer."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import json
from pathlib import Path
import shutil

from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from build_clean_ocr_pairs import (
    DEFAULT_OUTPUT,
    HIGH_RECALL_SOFT_FLAGS,
    ROOT,
    audit_sheet,
    write_json,
)
from build_ocr_dataset import DEFAULT_OUTPUT as DEFAULT_RECOGNITION_DATASET
from train_nippo_trocr import DEFAULT_OUTPUT as DEFAULT_RUN
from train_nippo_trocr import decode_text, device_for, edit_distance


def load_records(root: Path) -> list[dict]:
    records = []
    for name in ("pairs.jsonl", "rejected.jsonl"):
        with (root / name).open(encoding="utf-8") as stream:
            records.extend(json.loads(line) for line in stream if line.strip())
    return sorted(
        records,
        key=lambda record: (
            record["page_id"],
            record["column"],
            record["block"],
            record["block_index"],
        ),
    )


def load_recognizer(args: argparse.Namespace) -> tuple:
    checkpoint = args.checkpoint or args.run / "best"
    processor = TrOCRProcessor.from_pretrained(checkpoint, use_fast=False)
    model = VisionEncoderDecoderModel.from_pretrained(checkpoint)
    model.encoder.config._attn_implementation = "eager"
    model.decoder.config._attn_implementation = "eager"
    device = device_for(args.device)
    model.to(device).eval()
    return processor, model, device


@torch.inference_mode()
def recognize(
    records: list[dict], args: argparse.Namespace, runtime: tuple | None = None
) -> tuple:
    cache = {}
    if args.prediction_cache and args.prediction_cache.exists():
        with args.prediction_cache.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    cached = json.loads(line)
                    cache[cached["id"]] = cached["recognition"]
    processor, model, device = runtime or load_recognizer(args)
    for record in records:
        record["recognition"] = cache.get(record["id"], "")
    eligible = [
        record
        for record in records
        if not record.get("reasons") and record["id"] not in cache
    ]
    if cache:
        reused = sum(
            not record.get("reasons") and record["id"] in cache
            for record in records
        )
        print(f"reused {reused} cached recognitions", flush=True)
    cache_stream = None
    if args.prediction_cache:
        args.prediction_cache.parent.mkdir(parents=True, exist_ok=True)
        cache_stream = args.prediction_cache.open("a", encoding="utf-8")
    for start in range(0, len(eligible), args.batch_size):
        batch = eligible[start : start + args.batch_size]
        images = []
        for record in batch:
            with Image.open(args.recognition_dataset / record["image"]) as source:
                images.append(source.convert("RGB"))
        pixels = processor(images=images, return_tensors="pt").pixel_values.to(device)
        generated = model.generate(pixels, max_length=args.max_length, num_beams=1)
        decoded = processor.batch_decode(
            generated,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        for record, prediction in zip(batch, decoded):
            record["recognition"] = decode_text(prediction)
            if cache_stream:
                cache_stream.write(
                    json.dumps(
                        {"id": record["id"], "recognition": record["recognition"]},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        if cache_stream:
            cache_stream.flush()
        completed = min(len(eligible), start + len(batch))
        if args.log_every and completed % args.log_every < args.batch_size:
            print(f"recognized {completed}/{len(eligible)}", flush=True)
    if cache_stream:
        cache_stream.close()
    return processor, model, device


@torch.inference_mode()
def recognize_flagged_crops(
    records: list[dict], args: argparse.Namespace, runtime: tuple
) -> None:
    for record in records:
        record["crop_recognition"] = None
    if args.alignment_policy != "high-recall":
        return
    cache = {}
    if args.crop_prediction_cache and args.crop_prediction_cache.exists():
        with args.crop_prediction_cache.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    cached = json.loads(line)
                    cache[cached["sha256"]] = cached["recognition"]
    eligible = [
        record
        for record in records
        if not record.get("reasons")
        and (
            HIGH_RECALL_SOFT_FLAGS.intersection(record.get("quality_flags", []))
            or normalized_distance(record["text"], record["recognition"])
            > args.crop_validation_probe_cer
        )
    ]
    for record in eligible:
        if record["sha256"] in cache:
            record["crop_recognition"] = cache[record["sha256"]]
    pending = [
        record for record in eligible if record["crop_recognition"] is None
    ]
    print(
        f"reused {len(eligible) - len(pending)} cached crop recognitions",
        flush=True,
    )
    cache_stream = None
    if args.crop_prediction_cache:
        args.crop_prediction_cache.parent.mkdir(parents=True, exist_ok=True)
        cache_stream = args.crop_prediction_cache.open("a", encoding="utf-8")
    processor, model, device = runtime
    for start in range(0, len(pending), args.batch_size):
        batch = pending[start : start + args.batch_size]
        images = []
        for record in batch:
            with Image.open(args.dataset / record["image"]) as source:
                images.append(source.convert("RGB"))
        pixels = processor(images=images, return_tensors="pt").pixel_values.to(device)
        generated = model.generate(pixels, max_length=args.max_length, num_beams=1)
        decoded = processor.batch_decode(
            generated,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        for record, prediction in zip(batch, decoded):
            record["crop_recognition"] = decode_text(prediction)
            if cache_stream:
                cache_stream.write(
                    json.dumps(
                        {
                            "sha256": record["sha256"],
                            "recognition": record["crop_recognition"],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        if cache_stream:
            cache_stream.flush()
        completed = min(len(pending), start + len(batch))
        if args.log_every and completed % args.log_every < args.batch_size:
            print(f"crop-recognized {completed}/{len(pending)}", flush=True)
    if cache_stream:
        cache_stream.close()


def baseline_pairs(root: Path | None) -> dict[str, dict]:
    if root is None or not (root / "aligned-pairs.jsonl").exists():
        return {}
    with (root / "aligned-pairs.jsonl").open(encoding="utf-8") as stream:
        records = (json.loads(line) for line in stream if line.strip())
        return {record["id"]: record for record in records}


def baseline_fallback_pair(
    pair: dict, baseline: dict, *, baseline_root: Path, dataset_root: Path
) -> dict:
    """Reuse a previously audited image when a new expanded crop is less certain."""
    source = baseline_root / baseline["image"]
    relative_image = Path("baseline-images") / Path(baseline["image"]).relative_to(
        "images"
    )
    destination = dataset_root / relative_image
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    result = {
        **pair,
        "image": str(relative_image),
        "source_crop": baseline["source_crop"],
        "isolation_window": baseline["isolation_window"],
        "review_crop": baseline["review_crop"],
        "metrics": baseline["metrics"],
        "quality_flags": [],
        "width": baseline["width"],
        "height": baseline["height"],
        "sha256": baseline["sha256"],
        "recognition": baseline["recognition"],
        "recognition_cer": baseline["recognition_cer"],
        "crop_recognition": None,
        "crop_recognition_cer": None,
        "alignment_margin": baseline["alignment_margin"],
        "alignment_displacement": baseline["alignment_displacement"],
        "source_candidate_id": baseline["source_candidate_id"],
        "baseline_fallback": True,
        "quality_tier": "strict",
    }
    result.pop("reasons", None)
    return result


def visual_accepts(path: Path | None) -> set[str]:
    if path is None:
        return set()
    return set(json.loads(path.read_text(encoding="utf-8"))["pairs"])


@lru_cache(maxsize=None)
def normalized_distance(reference: str, hypothesis: str) -> float:
    return edit_distance(reference, hypothesis) / max(1, len(reference))


def sequence_alignment(
    references: list[dict],
    candidates: list[dict],
    *,
    gap_cost: float,
    position_cost: float,
    maximum_displacement: int,
) -> list[tuple[int | None, int | None]]:
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
            match = float("inf")
            if displacement <= maximum_displacement:
                match = costs[row - 1][column - 1] + normalized_distance(
                    references[row - 1]["text"],
                    candidates[column - 1]["recognition"],
                ) + position_cost * displacement
            options = (
                (match, "match"),
                (costs[row - 1][column] + gap_cost, "reference_gap"),
                (costs[row][column - 1] + gap_cost, "candidate_gap"),
            )
            costs[row][column], steps[row][column] = min(options, key=lambda item: item[0])
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


def match_margin(reference: dict, candidates: list[dict], selected: int) -> float | None:
    distances = sorted(
        (
            normalized_distance(reference["text"], candidate["recognition"]),
            index,
        )
        for index, candidate in enumerate(candidates)
        if abs(reference["block_index"] - candidate["block_index"]) <= 3
    )
    selected_distance = next(
        (distance for distance, index in distances if index == selected), None
    )
    competitors = [distance for distance, index in distances if index != selected]
    if selected_distance is None or not competitors:
        return None
    return min(competitors) - selected_distance


def align(records: list[dict], args: argparse.Namespace) -> tuple[list[dict], list[dict]]:
    baseline = baseline_pairs(args.baseline_dataset)
    confirmed = visual_accepts(args.visual_accepts)
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for record in records:
        groups[(record["page_id"], record["column"], record["block"])].append(record)
    accepted = []
    rejected = []
    for group_records in groups.values():
        references = sorted(group_records, key=lambda record: record["block_index"])
        candidates = references
        alignment = sequence_alignment(
            references,
            candidates,
            gap_cost=args.gap_cost,
            position_cost=args.position_cost,
            maximum_displacement=args.maximum_displacement,
        )
        matched_references: set[int] = set()
        matched_candidates: set[int] = set()
        for reference_index, candidate_index in alignment:
            if reference_index is None or candidate_index is None:
                continue
            matched_references.add(reference_index)
            matched_candidates.add(candidate_index)
            reference = references[reference_index]
            candidate = candidates[candidate_index]
            distance = normalized_distance(reference["text"], candidate["recognition"])
            margin = match_margin(reference, candidates, candidate_index)
            crop_recognition = candidate.get("crop_recognition")
            crop_distance = (
                normalized_distance(reference["text"], crop_recognition)
                if crop_recognition is not None
                else None
            )
            reasons = list(candidate.get("reasons", []))
            displacement = candidate_index - reference_index
            if not reasons:
                if args.alignment_policy == "high-recall":
                    needs_crop_check = crop_recognition is not None
                    if needs_crop_check and (
                        crop_distance is None
                        or crop_distance > args.maximum_crop_cer
                    ):
                        reasons.append("isolated_crop_recognition_mismatch")
                if args.alignment_policy == "strict" or displacement != 0:
                    if distance > args.maximum_cer:
                        reasons.append("recognition_mismatch")
                    if abs(displacement) > args.maximum_displacement:
                        reasons.append("excessive_alignment_displacement")
                    if distance > args.automatic_cer and (
                        margin is None or margin < args.minimum_margin
                    ):
                        reasons.append("ambiguous_text_alignment")
            pair = {
                **reference,
                "image": candidate["image"],
                "source_crop": candidate["source_crop"],
                "isolation_window": candidate["isolation_window"],
                "review_crop": candidate["review_crop"],
                "metrics": candidate["metrics"],
                "quality_flags": candidate.get("quality_flags", []),
                "width": candidate["width"],
                "height": candidate["height"],
                "sha256": candidate["sha256"],
                "recognition": candidate["recognition"],
                "recognition_cer": distance,
                "crop_recognition": crop_recognition,
                "crop_recognition_cer": crop_distance,
                "alignment_margin": margin,
                "alignment_displacement": displacement,
                "source_candidate_id": candidate["id"],
            }
            pair.pop("reasons", None)
            reasons = list(dict.fromkeys(reasons))
            baseline_record = baseline.get(reference["id"])
            strict_baseline_match = (
                baseline_record is not None
                and baseline_record["source_candidate_id"] == candidate["id"]
            )
            if (
                reasons
                and args.alignment_policy == "high-recall"
                and strict_baseline_match
            ):
                pair = baseline_fallback_pair(
                    pair,
                    baseline_record,
                    baseline_root=args.baseline_dataset,
                    dataset_root=args.dataset,
                )
                reasons = []
            visually_confirmed = (
                reference["id"] in confirmed
                and reasons == ["isolated_crop_recognition_mismatch"]
            )
            if visually_confirmed:
                reasons = []
                pair["visual_accept"] = True
            if reasons:
                pair["reasons"] = reasons
                rejected.append(pair)
            else:
                if args.alignment_policy == "high-recall":
                    pair["quality_tier"] = (
                        "visually-confirmed"
                        if visually_confirmed
                        else (
                            "strict"
                            if strict_baseline_match
                            else "recovered"
                        )
                    )
                accepted.append(pair)
        for index, reference in enumerate(references):
            if index not in matched_references:
                rejected.append({**reference, "reasons": ["unmatched_reference"]})
        for index, candidate in enumerate(candidates):
            if index not in matched_candidates:
                rejected.append(
                    {
                        **candidate,
                        "text": "",
                        "reasons": ["unmatched_candidate_image"],
                    }
                )
    return accepted, rejected


def write_results(
    accepted: list[dict], rejected: list[dict], args: argparse.Namespace
) -> dict:
    for name, records in (("aligned-pairs", accepted), ("alignment-rejected", rejected)):
        with (args.dataset / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    for split in ("train", "dev", "test"):
        with (args.dataset / f"aligned-{split}.jsonl").open(
            "w", encoding="utf-8"
        ) as stream:
            for record in accepted:
                if record["split"] == split:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    reason_counts = Counter(
        reason for record in rejected for reason in record.get("reasons", [])
    )
    summary = load_summary(args.dataset)
    model_path = (args.checkpoint or args.run / "best").resolve()
    recognition_path = args.recognition_dataset.resolve()
    summary["alignment"] = {
        "model": relative_display_path(model_path),
        "recognition_probe_dataset": relative_display_path(recognition_path),
        "accepted_pairs": len(accepted),
        "rejected_target_lines": summary["candidate_lines"] - len(accepted),
        "diagnostic_rejection_records": len(rejected),
        "unmatched_candidate_images": sum(
            record.get("text") == "" for record in rejected
        ),
        "acceptance_rate_from_all_candidates": len(accepted)
        / max(1, summary["candidate_lines"]),
        "accepted_by_split": dict(Counter(record["split"] for record in accepted)),
        "accepted_by_quality_tier": dict(
            Counter(record.get("quality_tier", "unclassified") for record in accepted)
        ),
        "baseline_fallback_pairs": sum(
            bool(record.get("baseline_fallback")) for record in accepted
        ),
        "visually_confirmed_pairs": sum(
            bool(record.get("visual_accept")) for record in accepted
        ),
        "rejection_reasons": dict(reason_counts.most_common()),
        "maximum_recognition_cer": args.maximum_cer,
        "automatic_acceptance_cer": args.automatic_cer,
        "minimum_ambiguous_match_margin": args.minimum_margin,
        "maximum_sequence_displacement": args.maximum_displacement,
        "alignment_policy": args.alignment_policy,
        "maximum_isolated_crop_cer": args.maximum_crop_cer,
        "crop_validation_probe_cer": args.crop_validation_probe_cer,
        "visual_accepts": relative_display_path(args.visual_accepts.resolve())
        if args.visual_accepts
        else None,
    }
    write_json(args.dataset / "summary.json", summary)
    rng = __import__("random").Random(args.seed)
    accepted_sample = rng.sample(accepted, min(args.audit_lines, len(accepted)))
    rejected_sample = rng.sample(rejected, min(args.audit_lines, len(rejected)))
    recovered = [
        record for record in accepted if record.get("quality_tier") == "recovered"
    ]
    recovered_sample = rng.sample(recovered, min(args.audit_lines, len(recovered)))
    samples = (
        ("aligned", accepted_sample),
        ("recovered", recovered_sample),
        ("alignment-rejected", rejected_sample),
    )
    for name, sample in samples:
        for index in range(0, len(sample), 20):
            audit_sheet(
                sample[index : index + 20],
                args.dataset / "audit" / f"{name}-{index // 20 + 1}.png",
                dataset_root=args.dataset,
                title=f"{name.title()} audit {index // 20 + 1}",
            )
    return summary


def load_summary(root: Path) -> dict:
    return json.loads((root / "summary.json").read_text(encoding="utf-8"))


def relative_display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument(
        "--recognition-dataset", type=Path, default=DEFAULT_RECOGNITION_DATASET
    )
    result.add_argument("--run", type=Path, default=DEFAULT_RUN)
    result.add_argument("--checkpoint", type=Path)
    result.add_argument("--prediction-cache", type=Path)
    result.add_argument("--crop-prediction-cache", type=Path)
    result.add_argument("--baseline-dataset", type=Path)
    result.add_argument("--visual-accepts", type=Path)
    result.add_argument(
        "--alignment-policy", choices=("strict", "high-recall"), default="strict"
    )
    result.add_argument("--device", default="auto")
    result.add_argument("--batch-size", type=int, default=16)
    result.add_argument("--max-length", type=int, default=48)
    result.add_argument("--gap-cost", type=float, default=0.55)
    result.add_argument("--position-cost", type=float, default=0.015)
    result.add_argument("--maximum-cer", type=float, default=0.32)
    result.add_argument("--maximum-crop-cer", type=float, default=0.60)
    result.add_argument("--crop-validation-probe-cer", type=float, default=0.50)
    result.add_argument("--automatic-cer", type=float, default=0.12)
    result.add_argument("--minimum-margin", type=float, default=0.08)
    result.add_argument("--maximum-displacement", type=int, default=3)
    result.add_argument("--audit-lines", type=int, default=60)
    result.add_argument("--log-every", type=int, default=512)
    result.add_argument("--seed", type=int, default=1603)
    return result


def main() -> int:
    args = parser().parse_args()
    records = load_records(args.dataset)
    runtime = recognize(records, args)
    recognize_flagged_crops(records, args, runtime)
    accepted, rejected = align(records, args)
    summary = write_results(accepted, rejected, args)
    print(json.dumps(summary["alignment"], ensure_ascii=False, indent=2))
    print(args.dataset / "aligned-pairs.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
