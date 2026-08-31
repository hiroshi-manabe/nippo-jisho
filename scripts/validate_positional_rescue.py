#!/usr/bin/env python3
"""Gate positional rescue crops with the independently trained core OCR model."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from build_clean_ocr_pairs import audit_sheet, ROOT, write_json
from build_positional_rescue import DEFAULT_OUTPUT, load_jsonl
from train_nippo_trocr import decode_text, device_for, edit_distance


DEFAULT_CHECKPOINT = (
    ROOT / ".cache" / "ocr-model" / "runs" / "trocr-isolated-core-v1" / "best"
)


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--candidates", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    result.add_argument("--maximum-cer", type=float, default=0.6)
    result.add_argument("--batch-size", type=int, default=16)
    result.add_argument("--max-length", type=int, default=48)
    result.add_argument("--device", default="auto")
    result.add_argument("--audit-lines", type=int, default=100)
    result.add_argument("--seed", type=int, default=20260831)
    return result


@torch.inference_mode()
def main() -> int:
    args = parser().parse_args()
    records = load_jsonl(args.candidates / "candidates.jsonl")
    processor = TrOCRProcessor.from_pretrained(args.checkpoint, use_fast=False)
    model = VisionEncoderDecoderModel.from_pretrained(args.checkpoint)
    model.encoder.config._attn_implementation = "eager"
    model.decoder.config._attn_implementation = "eager"
    device = device_for(args.device)
    model.to(device).eval()

    validated = []
    rejected = []
    for start in range(0, len(records), args.batch_size):
        batch = records[start : start + args.batch_size]
        images = []
        for record in batch:
            with Image.open(args.candidates / record["image"]) as source:
                images.append(source.convert("RGB"))
        pixels = processor(images=images, return_tensors="pt").pixel_values.to(device)
        generated = model.generate(pixels, max_length=args.max_length, num_beams=1)
        readings = processor.batch_decode(
            generated,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        for record, reading in zip(batch, readings):
            reading = decode_text(reading)
            distance = edit_distance(record["text"], reading)
            cer = distance / max(1, len(record["text"]))
            result = {
                **record,
                "positional_probe_recognition": reading,
                "positional_probe_cer": cer,
                "positional_probe_checkpoint": str(args.checkpoint.relative_to(ROOT)),
            }
            if cer <= args.maximum_cer:
                validated.append(result)
            else:
                result["reasons"] = ["positional_crop_recognition_mismatch"]
                rejected.append(result)

    validated_path = args.candidates / "validated-candidates.jsonl"
    rejected_path = args.candidates / "validation-rejected.jsonl"
    write_jsonl(validated_path, validated)
    write_jsonl(rejected_path, rejected)

    rng = random.Random(args.seed)
    audit = rng.sample(validated, min(args.audit_lines, len(validated)))
    for index in range(0, len(audit), 20):
        audit_sheet(
            [
                {
                    **record,
                    "reasons": [
                        f"core OCR CER {record['positional_probe_cer']:.1%}"
                    ],
                }
                for record in audit[index : index + 20]
            ],
            args.candidates / "validated-audit" / f"sample-{index // 20 + 1}.png",
            dataset_root=args.candidates,
            title=f"Validated positional rescue {index + 1}-{index + 20}",
        )
    summary = {
        "format": "nippo-positional-rescue-validation",
        "format_version": 1,
        "checkpoint": str(args.checkpoint.relative_to(ROOT)),
        "maximum_cer": args.maximum_cer,
        "candidate_count": len(records),
        "accepted_count": len(validated),
        "rejected_count": len(rejected),
        "acceptance_rate": len(validated) / max(1, len(records)),
        "accepted_by_split": dict(Counter(record["split"] for record in validated)),
        "validated_candidates_sha256": hashlib.sha256(
            validated_path.read_bytes()
        ).hexdigest(),
        "audit": {
            "seed": args.seed,
            "sample_size": len(audit),
            "sample_ids": [record["id"] for record in audit],
        },
    }
    write_json(args.candidates / "validation-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
