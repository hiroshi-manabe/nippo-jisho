#!/usr/bin/env python3
"""Fine-tune a pretrained printed-text TrOCR model on Nippo Jisho lines."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import random
import time

from PIL import Image
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / ".cache" / "ocr-model" / "dataset-v2"
DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "runs" / "trocr-small-v1"
LONG_S_PLACEHOLDER = "§"


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def encode_text(text: str) -> str:
    if LONG_S_PLACEHOLDER in text:
        raise ValueError(f"reserved placeholder occurs in source text: {text!r}")
    return text.replace("ſ", LONG_S_PLACEHOLDER)


def decode_text(text: str) -> str:
    return text.replace(LONG_S_PLACEHOLDER, "ſ")


class TrocrLines(Dataset):
    def __init__(
        self,
        root: Path,
        split: str,
        processor: TrOCRProcessor,
        *,
        limit: int = 0,
        seed: int = 1603,
    ) -> None:
        self.root = root
        self.processor = processor
        self.records = load_jsonl(root / f"{split}.jsonl")
        if limit and limit < len(self.records):
            indices = sorted(random.Random(seed).sample(range(len(self.records)), limit))
            self.records = [self.records[index] for index in indices]

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict:
        record = self.records[index]
        with Image.open(self.root / record["image"]) as source:
            image = source.convert("RGB")
        pixels = self.processor(images=image, return_tensors="pt").pixel_values[0]
        return {
            "pixel_values": pixels,
            "text": record["text"],
            "encoded_text": encode_text(record["text"]),
            "id": record["id"],
        }


class Collator:
    def __init__(self, processor: TrOCRProcessor, max_length: int) -> None:
        self.processor = processor
        self.max_length = max_length

    def __call__(self, batch: list[dict]) -> dict:
        tokens = self.processor.tokenizer(
            [item["encoded_text"] for item in batch],
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        labels = tokens.input_ids
        labels[labels == self.processor.tokenizer.pad_token_id] = -100
        return {
            "pixel_values": torch.stack(
                [item["pixel_values"] for item in batch]
            ).contiguous(),
            "labels": labels,
            "texts": [item["text"] for item in batch],
            "ids": [item["id"] for item in batch],
        }


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


@torch.inference_mode()
def evaluate_loss(
    model: VisionEncoderDecoderModel,
    loader: DataLoader,
    processor: TrOCRProcessor,
    device: torch.device,
) -> float:
    model.eval()
    total_loss = 0.0
    batches = 0
    for batch in loader:
        labels = batch["labels"].to(device)
        decoder_input_ids = model.prepare_decoder_input_ids_from_labels(labels)
        result = model(
            pixel_values=batch["pixel_values"].to(device),
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_input_ids.ne(
                processor.tokenizer.pad_token_id
            ).long(),
        )
        loss = torch.nn.functional.cross_entropy(
            result.logits.reshape(-1, result.logits.shape[-1]),
            labels.reshape(-1),
            ignore_index=-100,
        )
        total_loss += float(loss.cpu())
        batches += 1
    return total_loss / max(1, batches)


@torch.inference_mode()
def evaluate(
    model: VisionEncoderDecoderModel,
    loader: DataLoader,
    processor: TrOCRProcessor,
    device: torch.device,
    max_length: int,
) -> dict:
    model.eval()
    errors = 0
    characters = 0
    exact = 0
    examples: list[dict] = []
    for batch in loader:
        generated = model.generate(
            batch["pixel_values"].to(device),
            max_length=max_length,
            num_beams=1,
        )
        decoded = processor.batch_decode(
            generated, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        for identifier, reference, raw_hypothesis in zip(
            batch["ids"], batch["texts"], decoded
        ):
            hypothesis = decode_text(raw_hypothesis)
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


def configure_model(
    name: str, processor: TrOCRProcessor
) -> VisionEncoderDecoderModel:
    model = VisionEncoderDecoderModel.from_pretrained(name)
    # Preserve TrOCR/BART's pretrained convention: generation begins with EOS,
    # then predicts the target BOS token. Starting directly from BOS creates a
    # duplicated-BOS training context and caused adapted models to emit empty
    # strings at inference time.
    model.config.decoder_start_token_id = model.config.decoder.decoder_start_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.eos_token_id = processor.tokenizer.sep_token_id
    model.config.vocab_size = model.config.decoder.vocab_size
    # The SDPA backward path used by this PyTorch/Transformers combination
    # creates non-contiguous views that fail on MPS. Eager attention is stable.
    model.encoder.config._attn_implementation = "eager"
    model.decoder.config._attn_implementation = "eager"
    return model


def train(args: argparse.Namespace) -> dict:
    if args.detect_anomaly:
        torch.autograd.set_detect_anomaly(True)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    processor = TrOCRProcessor.from_pretrained(args.base_model, use_fast=False)
    # Verify the placeholder contract before expensive training begins.
    probe = "Cu§uriuo"
    probe_ids = processor.tokenizer(probe, add_special_tokens=False).input_ids
    if processor.tokenizer.decode(probe_ids, clean_up_tokenization_spaces=False) != probe:
        raise RuntimeError("the long-s placeholder no longer round-trips through the tokenizer")
    model = configure_model(args.base_model, processor)
    device = device_for(args.device)
    model.to(device)
    collator = Collator(processor, args.max_length)
    train_data = TrocrLines(
        args.dataset,
        "train",
        processor,
        limit=args.max_train_lines,
        seed=args.seed,
    )
    dev_data = TrocrLines(
        args.dataset, "dev", processor, limit=args.max_eval_lines, seed=args.seed
    )
    test_data = TrocrLines(
        args.dataset, "test", processor, limit=args.max_eval_lines, seed=args.seed
    )
    train_loader = DataLoader(
        train_data,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        collate_fn=collator,
    )
    dev_loader = DataLoader(
        dev_data, batch_size=args.eval_batch_size, num_workers=0, collate_fn=collator
    )
    test_loader = DataLoader(
        test_data, batch_size=args.eval_batch_size, num_workers=0, collate_fn=collator
    )
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
    )
    args.output.mkdir(parents=True, exist_ok=True)
    history: list[dict] = []
    best_dev_loss = float("inf")
    stale_epochs = 0
    started = time.time()

    for epoch in range(1, args.epochs + 1):
        model.train()
        encoder_frozen = epoch <= args.freeze_encoder_epochs
        for parameter in model.encoder.parameters():
            parameter.requires_grad = not encoder_frozen
        if encoder_frozen:
            model.encoder.eval()
        running_loss = 0.0
        epoch_started = time.time()
        for batch_number, batch in enumerate(train_loader, start=1):
            optimizer.zero_grad(set_to_none=True)
            labels = batch["labels"].to(device)
            decoder_input_ids = model.prepare_decoder_input_ids_from_labels(labels)
            result = model(
                pixel_values=batch["pixel_values"].to(device),
                decoder_input_ids=decoder_input_ids,
                decoder_attention_mask=decoder_input_ids.ne(
                    processor.tokenizer.pad_token_id
                ).long(),
            )
            loss = torch.nn.functional.cross_entropy(
                result.logits.reshape(-1, result.logits.shape[-1]),
                labels.reshape(-1),
                ignore_index=-100,
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            running_loss += float(loss.detach().cpu())
            if args.log_every and batch_number % args.log_every == 0:
                print(
                    json.dumps(
                        {
                            "epoch": epoch,
                            "batch": batch_number,
                            "batches": len(train_loader),
                            "mean_loss": running_loss / batch_number,
                        }
                    ),
                    flush=True,
                )
        dev_loss = evaluate_loss(model, dev_loader, processor, device)
        row = {
            "epoch": epoch,
            "encoder_frozen": encoder_frozen,
            "train_loss": running_loss / max(1, len(train_loader)),
            "seconds": time.time() - epoch_started,
            "dev_loss": dev_loss,
        }
        history.append(row)
        print(json.dumps(row), flush=True)
        if dev_loss < best_dev_loss - args.min_delta:
            best_dev_loss = dev_loss
            stale_epochs = 0
            best = args.output / "best"
            model.save_pretrained(best)
            processor.save_pretrained(best)
            (best / "checkpoint_metrics.json").write_text(
                json.dumps({"epoch": epoch, "dev_loss": dev_loss}, indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            stale_epochs += 1
            if stale_epochs >= args.patience:
                break

    best_model = VisionEncoderDecoderModel.from_pretrained(args.output / "best").to(device)
    dev_metrics = evaluate(best_model, dev_loader, processor, device, args.max_length)
    test_metrics = evaluate(best_model, test_loader, processor, device, args.max_length)
    results = {
        "format": "nippo-trocr-training-result",
        "format_version": 1,
        "base_model": args.base_model,
        "dataset": str(args.dataset),
        "device": str(device),
        "seed": args.seed,
        "freeze_encoder_epochs": args.freeze_encoder_epochs,
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
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
    result.add_argument("--base-model", default="microsoft/trocr-small-printed")
    result.add_argument("--device", default="auto")
    result.add_argument("--seed", type=int, default=1603)
    result.add_argument("--batch-size", type=int, default=8)
    result.add_argument("--eval-batch-size", type=int, default=8)
    result.add_argument("--epochs", type=int, default=8)
    result.add_argument("--patience", type=int, default=3)
    result.add_argument("--min-delta", type=float, default=0.0005)
    result.add_argument("--learning-rate", type=float, default=5e-5)
    result.add_argument("--weight-decay", type=float, default=0.01)
    result.add_argument("--freeze-encoder-epochs", type=int, default=1)
    result.add_argument("--max-length", type=int, default=64)
    result.add_argument("--max-train-lines", type=int, default=0)
    result.add_argument("--max-eval-lines", type=int, default=0)
    result.add_argument("--log-every", type=int, default=25)
    result.add_argument("--detect-anomaly", action="store_true")
    return result


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    raise SystemExit(0 if train(parser().parse_args()) else 1)
