#!/usr/bin/env python3
"""Train and evaluate the experimental Nippo Jisho line recognizer."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import time

# PyTorch currently routes CTC loss to the CPU on Apple Silicon. The encoder and
# recurrent network remain on MPS; this opt-in makes the mixed execution path
# explicit instead of failing after the first batch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

from PIL import Image, ImageEnhance
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from nippo_ocr_model import LineCTC, ModelConfig


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / ".cache" / "ocr-model" / "dataset-v2"
DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "runs" / "line-ctc-v2"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


class LineDataset(Dataset):
    def __init__(self, root: Path, split: str, *, augment: bool, limit: int = 0) -> None:
        self.root = root
        self.records = load_jsonl(root / f"{split}.jsonl")
        if limit:
            self.records = self.records[:limit]
        self.augment = augment

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, str, str]:
        record = self.records[index]
        with Image.open(self.root / record["image"]) as source:
            image = source.convert("L")
        if self.augment:
            image = ImageEnhance.Contrast(image).enhance(random.uniform(0.85, 1.2))
            image = ImageEnhance.Brightness(image).enhance(random.uniform(0.9, 1.1))
        pixels = torch.frombuffer(bytearray(image.tobytes()), dtype=torch.uint8)
        pixels = pixels.reshape(image.height, image.width).float().div_(255.0)
        pixels = (1.0 - pixels).unsqueeze(0)
        return pixels, record["text"], record["id"]


class Codec:
    def __init__(self, characters: list[str]) -> None:
        self.characters = characters
        self.to_index = {character: index + 1 for index, character in enumerate(characters)}

    def encode(self, text: str) -> list[int]:
        return [self.to_index[character] for character in text]

    def decode(self, sequence: list[int]) -> str:
        output: list[str] = []
        previous = -1
        for index in sequence:
            if index != 0 and index != previous:
                output.append(self.characters[index - 1])
            previous = index
        return "".join(output)


def collate(codec: Codec):
    def apply(batch: list[tuple[torch.Tensor, str, str]]) -> dict:
        widths = torch.tensor([item[0].shape[-1] for item in batch], dtype=torch.long)
        padded_width = int((int(widths.max()) + 3) // 4 * 4)
        images = torch.zeros((len(batch), 1, batch[0][0].shape[-2], padded_width))
        targets: list[int] = []
        target_lengths: list[int] = []
        for row, (image, text, _) in enumerate(batch):
            images[row, :, :, : image.shape[-1]] = image
            encoded = codec.encode(text)
            targets.extend(encoded)
            target_lengths.append(len(encoded))
        return {
            "images": images,
            "widths": widths,
            "targets": torch.tensor(targets, dtype=torch.long),
            "target_lengths": torch.tensor(target_lengths, dtype=torch.long),
            "texts": [item[1] for item in batch],
            "ids": [item[2] for item in batch],
        }

    return apply


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


def device_for(name: str) -> torch.device:
    if name != "auto":
        return torch.device(name)
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def aligned_loss(
    logits: torch.Tensor,
    lengths: torch.Tensor,
    texts: list[str],
    codec: Codec,
) -> torch.Tensor:
    """Approximate a monotonic alignment to bootstrap CTC from scratch."""
    labels = torch.full(
        logits.shape[:2], -100, dtype=torch.long, device=logits.device
    )
    for row, (text, length) in enumerate(zip(texts, lengths.tolist())):
        encoded = torch.tensor(codec.encode(text), dtype=torch.long, device=logits.device)
        positions = torch.div(
            torch.arange(length, device=logits.device) * len(encoded),
            length,
            rounding_mode="floor",
        )
        labels[row, :length] = encoded[positions]
    return nn.functional.cross_entropy(
        logits.reshape(-1, logits.shape[-1]), labels.reshape(-1), ignore_index=-100
    )


def penalize_blank(logits: torch.Tensor, penalty: float) -> torch.Tensor:
    adjusted = logits.clone()
    adjusted[:, :, 0] -= penalty
    return adjusted


@torch.inference_mode()
def evaluate(
    model: LineCTC,
    loader: DataLoader,
    codec: Codec,
    device: torch.device,
    blank_penalty: float,
) -> dict:
    model.eval()
    errors = 0
    characters = 0
    exact = 0
    examples: list[dict] = []
    for batch in loader:
        logits, _ = model(batch["images"].to(device), batch["widths"].to(device))
        predictions = penalize_blank(logits, blank_penalty).argmax(dim=-1).cpu().tolist()
        lengths = model.output_lengths(batch["widths"]).tolist()
        for identifier, reference, indices, length in zip(
            batch["ids"], batch["texts"], predictions, lengths
        ):
            indices = indices[:length]
            hypothesis = codec.decode(indices)
            distance = edit_distance(reference, hypothesis)
            errors += distance
            characters += len(reference)
            exact += reference == hypothesis
            if distance and len(examples) < 40:
                examples.append(
                    {
                        "id": identifier,
                        "reference": reference,
                        "hypothesis": hypothesis,
                        "distance": distance,
                    }
                )
    return {
        "lines": len(loader.dataset),
        "characters": characters,
        "character_errors": errors,
        "cer": errors / max(1, characters),
        "exact_lines": exact,
        "exact_line_rate": exact / max(1, len(loader.dataset)),
        "examples": examples,
    }


def save_checkpoint(
    path: Path,
    model: LineCTC,
    codec: Codec,
    epoch: int,
    metrics: dict,
    blank_penalty: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "format": "nippo-line-ctc",
            "format_version": 1,
            "state_dict": model.state_dict(),
            "characters": codec.characters,
            "model_config": asdict(model.config),
            "epoch": epoch,
            "dev_metrics": metrics,
            "blank_penalty": blank_penalty,
        },
        path,
    )


def train(args: argparse.Namespace) -> dict:
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    metadata = load_json(args.dataset / "dataset.json")
    codec = Codec(metadata["characters"])
    train_data = LineDataset(
        args.dataset, "train", augment=True, limit=args.max_train_lines
    )
    dev_data = LineDataset(args.dataset, "dev", augment=False, limit=args.max_eval_lines)
    test_data = LineDataset(args.dataset, "test", augment=False, limit=args.max_eval_lines)
    collator = collate(codec)
    train_loader = DataLoader(
        train_data,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.workers,
        persistent_workers=args.workers > 0,
        collate_fn=collator,
    )
    dev_loader = DataLoader(dev_data, batch_size=args.eval_batch_size, collate_fn=collator)
    test_loader = DataLoader(test_data, batch_size=args.eval_batch_size, collate_fn=collator)
    device = device_for(args.device)
    config = ModelConfig(temporal_blocks=args.temporal_blocks, dropout=args.dropout)
    model = LineCTC(len(codec.characters) + 1, config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    loss_function = nn.CTCLoss(blank=0, zero_infinity=True)
    args.output.mkdir(parents=True, exist_ok=True)
    history: list[dict] = []
    best_cer = float("inf")
    stale_epochs = 0
    started = time.time()

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        batches = 0
        epoch_started = time.time()
        for batch in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits, input_lengths = model(
                batch["images"].to(device), batch["widths"].to(device)
            )
            if epoch <= args.warmup_epochs:
                loss = aligned_loss(logits, input_lengths, batch["texts"], codec)
            else:
                adjusted = penalize_blank(logits, args.blank_penalty)
                loss = loss_function(
                    adjusted.log_softmax(dim=-1).transpose(0, 1),
                    batch["targets"].to(device),
                    input_lengths,
                    batch["target_lengths"],
                )
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            running_loss += float(loss.detach().cpu())
            batches += 1
            if args.log_every and batches % args.log_every == 0:
                print(
                    json.dumps(
                        {
                            "epoch": epoch,
                            "batch": batches,
                            "batches": len(train_loader),
                            "mean_loss": running_loss / batches,
                        }
                    ),
                    flush=True,
                )
        metrics = evaluate(model, dev_loader, codec, device, args.blank_penalty)
        row = {
            "epoch": epoch,
            "phase": "alignment_warmup" if epoch <= args.warmup_epochs else "ctc",
            "train_loss": running_loss / max(1, batches),
            "seconds": time.time() - epoch_started,
            "dev_cer": metrics["cer"],
            "dev_exact_line_rate": metrics["exact_line_rate"],
        }
        history.append(row)
        print(json.dumps(row), flush=True)
        if epoch <= args.warmup_epochs:
            save_checkpoint(
                args.output / "warmup.pt",
                model,
                codec,
                epoch,
                metrics,
                args.blank_penalty,
            )
            continue
        if metrics["cer"] < best_cer - args.min_delta:
            best_cer = metrics["cer"]
            stale_epochs = 0
            save_checkpoint(
                args.output / "best.pt",
                model,
                codec,
                epoch,
                metrics,
                args.blank_penalty,
            )
        else:
            stale_epochs += 1
            if stale_epochs >= args.patience:
                break

    checkpoint = torch.load(args.output / "best.pt", map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["state_dict"])
    dev_metrics = evaluate(model, dev_loader, codec, device, args.blank_penalty)
    test_metrics = evaluate(model, test_loader, codec, device, args.blank_penalty)
    results = {
        "format": "nippo-ocr-training-result",
        "format_version": 1,
        "dataset": str(args.dataset),
        "device": str(device),
        "seed": args.seed,
        "warmup_epochs": args.warmup_epochs,
        "blank_penalty": args.blank_penalty,
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "best_epoch": checkpoint["epoch"],
        "elapsed_seconds": time.time() - started,
        "history": history,
        "dev": dev_metrics,
        "test": test_metrics,
    }
    (args.output / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"dev": dev_metrics["cer"], "test": test_metrics["cer"]}))
    return results


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--device", default="auto")
    result.add_argument("--seed", type=int, default=1603)
    result.add_argument("--batch-size", type=int, default=24)
    result.add_argument("--eval-batch-size", type=int, default=32)
    result.add_argument("--workers", type=int, default=0)
    result.add_argument("--log-every", type=int, default=100)
    result.add_argument("--max-train-lines", type=int, default=0)
    result.add_argument("--max-eval-lines", type=int, default=0)
    result.add_argument("--epochs", type=int, default=20)
    result.add_argument("--warmup-epochs", type=int, default=3)
    result.add_argument("--blank-penalty", type=float, default=1.0)
    result.add_argument("--patience", type=int, default=5)
    result.add_argument("--min-delta", type=float, default=0.0005)
    result.add_argument("--learning-rate", type=float, default=3e-4)
    result.add_argument("--temporal-blocks", type=int, default=8)
    result.add_argument("--dropout", type=float, default=0.2)
    return result


if __name__ == "__main__":
    raise SystemExit(0 if train(parser().parse_args()) else 1)
