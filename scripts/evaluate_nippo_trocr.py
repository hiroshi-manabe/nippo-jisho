#!/usr/bin/env python3
"""Evaluate a trained Nippo Jisho TrOCR checkpoint on complete held-out splits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from train_nippo_trocr import (
    Collator,
    DEFAULT_DATASET,
    DEFAULT_OUTPUT,
    TrocrLines,
    device_for,
    evaluate,
    evaluate_loss,
)


def main(args: argparse.Namespace) -> int:
    checkpoint = args.checkpoint or args.run / "best"
    processor = TrOCRProcessor.from_pretrained(checkpoint, use_fast=False)
    model = VisionEncoderDecoderModel.from_pretrained(checkpoint)
    model.encoder.config._attn_implementation = "eager"
    model.decoder.config._attn_implementation = "eager"
    device = device_for(args.device)
    model.to(device)

    results: dict[str, object] = {
        "format": "nippo-trocr-evaluation",
        "format_version": 1,
        "checkpoint": str(checkpoint),
        "dataset": str(args.dataset),
        "device": str(device),
        "splits": {},
    }
    for split in args.splits:
        dataset = TrocrLines(args.dataset, split, processor)
        loader = DataLoader(
            dataset,
            batch_size=args.batch_size,
            num_workers=0,
            collate_fn=Collator(processor, args.max_length),
        )
        metrics = evaluate(model, loader, processor, device, args.max_length)
        if args.include_loss:
            metrics["loss"] = evaluate_loss(model, loader, processor, device)
        results["splits"][split] = metrics
        print(
            f"{split}: lines={metrics['lines']} CER={metrics['cer']:.4f} "
            f"exact={metrics['exact_line_rate']:.2%}",
            flush=True,
        )

    output = args.output or args.run / "full-evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(output)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    result.add_argument("--run", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--checkpoint", type=Path)
    result.add_argument("--output", type=Path)
    result.add_argument(
        "--splits",
        nargs="+",
        default=("dev", "test"),
        help="manifest basenames to evaluate (default: dev test)",
    )
    result.add_argument("--device", default="auto")
    result.add_argument("--batch-size", type=int, default=16)
    result.add_argument("--max-length", type=int, default=48)
    result.add_argument("--include-loss", action="store_true")
    return result


if __name__ == "__main__":
    raise SystemExit(main(parser().parse_args()))
