#!/usr/bin/env python3
"""Recognize Nippo Jisho line images or every geometry-defined line on a page."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from build_ocr_dataset import ROOT, prepare_crop, trim_horizontal
from train_nippo_trocr import decode_text, device_for


DEFAULT_RUN = ROOT / ".cache" / "ocr-model" / "runs" / "trocr-isolated-core-v1"


def preprocess_line(image: Image.Image, *, height: int, max_width: int) -> Image.Image:
    line = ImageOps.autocontrast(image.convert("L"), cutoff=0.2)
    line = trim_horizontal(line)
    width = min(max_width, max(1, round(line.width * height / line.height)))
    return line.resize((width, height), Image.Resampling.LANCZOS)


def page_inputs(page_number: int, *, height: int, max_width: int) -> list[dict]:
    geometry_path = ROOT / "pilot" / "human-review" / "line-geometry.json"
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    page_id = f"bnf-f{page_number:04d}"
    page = next((item for item in geometry["pages"] if item["id"] == page_id), None)
    if page is None:
        raise ValueError(f"no line geometry found for {page_id}")
    scan_path = (
        ROOT
        / "build"
        / "nippo-jisho-images"
        / "scans"
        / "native"
        / f"f{page_number:04d}.jpg"
    )
    with Image.open(scan_path) as scan:
        if list(scan.size) != page["source_size"]:
            raise ValueError(f"{page_id}: scan and geometry dimensions differ")
        records = []
        for column in page["columns"].values():
            for line_id, line in column["lines"].items():
                records.append(
                    {
                        "id": f"{page_id}/{line_id}",
                        "page_id": page_id,
                        "line_id": line_id,
                        "crop": line["crop"],
                        "image": prepare_crop(
                            scan, line["crop"], height=height, max_width=max_width
                        ).convert("RGB"),
                    }
                )
    return records


def image_inputs(paths: list[Path], *, height: int, max_width: int) -> list[dict]:
    records = []
    for path in paths:
        with Image.open(path) as source:
            image = preprocess_line(source, height=height, max_width=max_width).convert("RGB")
        records.append({"id": path.name, "source": str(path), "image": image})
    return records


@torch.inference_mode()
def recognize(args: argparse.Namespace) -> list[dict]:
    checkpoint = args.checkpoint or args.run / "best"
    processor = TrOCRProcessor.from_pretrained(checkpoint, use_fast=False)
    model = VisionEncoderDecoderModel.from_pretrained(checkpoint)
    model.encoder.config._attn_implementation = "eager"
    model.decoder.config._attn_implementation = "eager"
    device = device_for(args.device)
    model.to(device).eval()

    if args.page is not None:
        records = page_inputs(args.page, height=args.height, max_width=args.max_width)
    else:
        records = image_inputs(args.images, height=args.height, max_width=args.max_width)

    output: list[dict] = []
    for start in range(0, len(records), args.batch_size):
        batch = records[start : start + args.batch_size]
        pixels = processor(
            images=[record["image"] for record in batch], return_tensors="pt"
        ).pixel_values.to(device)
        generated = model.generate(pixels, max_length=args.max_length, num_beams=args.beams)
        decoded = processor.batch_decode(
            generated, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        for record, text in zip(batch, decoded):
            result = {key: value for key, value in record.items() if key != "image"}
            result["text"] = decode_text(text)
            output.append(result)
    return output


def main(args: argparse.Namespace) -> int:
    if args.page is None and not args.images:
        raise SystemExit("provide one or more line images, or --page NUMBER")
    if args.page is not None and args.images:
        raise SystemExit("line images and --page are mutually exclusive")
    results = recognize(args)
    serialized = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
        print(args.output)
    else:
        print(serialized, end="")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("images", nargs="*", type=Path)
    result.add_argument("--page", type=int)
    result.add_argument("--run", type=Path, default=DEFAULT_RUN)
    result.add_argument("--checkpoint", type=Path)
    result.add_argument("--output", type=Path)
    result.add_argument("--device", default="auto")
    result.add_argument("--batch-size", type=int, default=16)
    result.add_argument("--beams", type=int, default=1)
    result.add_argument("--max-length", type=int, default=48)
    result.add_argument("--height", type=int, default=48)
    result.add_argument("--max-width", type=int, default=1024)
    return result


if __name__ == "__main__":
    raise SystemExit(main(parser().parse_args()))
