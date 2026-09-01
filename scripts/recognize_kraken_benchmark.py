#!/usr/bin/env python3
"""Recognize an exported line benchmark with a trained Kraken VGSL model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image
import torch
import torch.nn.functional as functional

from kraken.lib.dataset import ImageInputTransforms
from kraken.lib.models import load_any


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def batches(records: list[dict], size: int):
    for index in range(0, len(records), size):
        yield records[index : index + size]


@torch.inference_mode()
def recognize(args: argparse.Namespace) -> None:
    records = [
        record for record in load_jsonl(args.benchmark / "records.jsonl")
        if record["split"] == args.split
    ]
    model = load_any(args.model, train=False, device=args.device)
    _, channels, height, width = model.nn.input
    transforms = ImageInputTransforms(
        args.batch_size,
        height,
        width,
        channels,
        (args.pad, 0),
        valid_norm=True,
        force_binarization=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        completed = 0
        for group in batches(records, args.batch_size):
            rendered = []
            for record in group:
                with Image.open(args.benchmark / record["image"]) as source:
                    tensor = transforms(source)
                rendered.append((record, tensor))
            rendered.sort(key=lambda item: item[1].shape[2], reverse=True)
            lengths = torch.tensor([item[1].shape[2] for item in rendered]).long()
            maximum = int(lengths.max())
            images = torch.stack(
                [
                    functional.pad(tensor, (0, maximum - tensor.shape[2]))
                    for _, tensor in rendered
                ]
            )
            predictions = model.predict_string(images, lengths)
            for (record, _), prediction in zip(rendered, predictions):
                stream.write(
                    json.dumps(
                        {"id": record["id"], "text": prediction},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            completed += len(group)
            if args.log_every and completed % args.log_every < len(group):
                print(f"recognized {completed}/{len(records)}", flush=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--benchmark", type=Path, required=True)
    result.add_argument("--model", type=Path, required=True)
    result.add_argument("--split", choices=("train", "dev", "test"), required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--device", default="cpu")
    result.add_argument("--batch-size", type=int, default=8)
    result.add_argument("--pad", type=int, default=16)
    result.add_argument("--log-every", type=int, default=200)
    return result


if __name__ == "__main__":
    recognize(parser().parse_args())
