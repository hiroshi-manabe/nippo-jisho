#!/usr/bin/env python3
"""Align isolated Nippo line candidates to reviewed text with the v1 recognizer."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from build_clean_ocr_pairs import DEFAULT_OUTPUT, ROOT, audit_sheet, write_json
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


@torch.inference_mode()
def recognize(records: list[dict], args: argparse.Namespace) -> None:
    checkpoint = args.checkpoint or args.run / "best"
    processor = TrOCRProcessor.from_pretrained(checkpoint, use_fast=False)
    model = VisionEncoderDecoderModel.from_pretrained(checkpoint)
    model.encoder.config._attn_implementation = "eager"
    model.decoder.config._attn_implementation = "eager"
    device = device_for(args.device)
    model.to(device).eval()
    for record in records:
        record["recognition"] = ""
    eligible = [record for record in records if not record.get("reasons")]
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
        completed = min(len(eligible), start + len(batch))
        if args.log_every and completed % args.log_every < args.batch_size:
            print(f"recognized {completed}/{len(eligible)}", flush=True)


def normalized_distance(reference: str, hypothesis: str) -> float:
    return edit_distance(reference, hypothesis) / max(1, len(reference))


def sequence_alignment(
    references: list[dict], candidates: list[dict], *, gap_cost: float, position_cost: float
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
            match = costs[row - 1][column - 1] + normalized_distance(
                references[row - 1]["text"], candidates[column - 1]["recognition"]
            ) + position_cost * abs((row - 1) - (column - 1))
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
            reasons = list(candidate.get("reasons", []))
            displacement = candidate_index - reference_index
            if not reasons:
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
                "width": candidate["width"],
                "height": candidate["height"],
                "sha256": candidate["sha256"],
                "recognition": candidate["recognition"],
                "recognition_cer": distance,
                "alignment_margin": margin,
                "alignment_displacement": displacement,
                "source_candidate_id": candidate["id"],
            }
            pair.pop("reasons", None)
            reasons = list(dict.fromkeys(reasons))
            if reasons:
                pair["reasons"] = reasons
                rejected.append(pair)
            else:
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
        "rejection_reasons": dict(reason_counts.most_common()),
        "maximum_recognition_cer": args.maximum_cer,
        "automatic_acceptance_cer": args.automatic_cer,
        "minimum_ambiguous_match_margin": args.minimum_margin,
        "maximum_sequence_displacement": args.maximum_displacement,
    }
    write_json(args.dataset / "summary.json", summary)
    rng = __import__("random").Random(args.seed)
    accepted_sample = rng.sample(accepted, min(args.audit_lines, len(accepted)))
    rejected_sample = rng.sample(rejected, min(args.audit_lines, len(rejected)))
    for name, sample in (("aligned", accepted_sample), ("alignment-rejected", rejected_sample)):
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
    result.add_argument("--device", default="auto")
    result.add_argument("--batch-size", type=int, default=16)
    result.add_argument("--max-length", type=int, default=48)
    result.add_argument("--gap-cost", type=float, default=0.55)
    result.add_argument("--position-cost", type=float, default=0.015)
    result.add_argument("--maximum-cer", type=float, default=0.32)
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
    recognize(records, args)
    accepted, rejected = align(records, args)
    summary = write_results(accepted, rejected, args)
    print(json.dumps(summary["alignment"], ensure_ascii=False, indent=2))
    print(args.dataset / "aligned-pairs.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
