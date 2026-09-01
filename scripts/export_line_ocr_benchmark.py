#!/usr/bin/env python3
"""Export the reviewed line corpus for character-level OCR engines.

The source manifests remain authoritative.  This exporter creates a flat,
engine-neutral directory with stable image names, adjacent ``.gt.txt`` files,
Kraken/Calamari-compatible manifests, and a JSONL index for evaluation.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / ".cache" / "ocr-model" / "usable-lines-v2"
DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "engine-benchmark-v1"
SPLITS = ("train", "dev", "test")


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def safe_name(identifier: str) -> str:
    return identifier.replace("/", "__").replace("#", "--")


def link_or_copy(source: Path, destination: Path) -> None:
    try:
        relative = os.path.relpath(source, destination.parent)
        destination.symlink_to(relative)
    except OSError:
        shutil.copy2(source, destination)


def export(source: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    alphabet: set[str] = set()
    page_sets: dict[str, set[str]] = {}

    for split in SPLITS:
        records = load_jsonl(source / f"aligned-{split}.jsonl")
        split_dir = output / split
        if split_dir.exists():
            shutil.rmtree(split_dir)
        split_dir.mkdir(parents=True)
        manifest: list[str] = []
        identifiers: set[str] = set()
        pages: set[str] = set()

        for record in records:
            identifier = record["id"]
            if identifier in identifiers:
                raise ValueError(f"duplicate line identifier in {split}: {identifier}")
            identifiers.add(identifier)
            pages.add(record["page_id"])
            text = unicodedata.normalize("NFC", record["text"])
            if "\n" in text or "\r" in text:
                raise ValueError(f"physical line contains a newline: {identifier}")
            image_source = source / record["image"]
            if not image_source.is_file():
                raise FileNotFoundError(image_source)

            stem = safe_name(identifier)
            image_path = split_dir / f"{stem}.png"
            ground_truth = split_dir / f"{stem}.gt.txt"
            link_or_copy(image_source.resolve(), image_path)
            ground_truth.write_text(text, encoding="utf-8")
            # Keep the exported symlink path rather than resolving it: Kraken
            # locates the adjacent ``.gt.txt`` file from this exact basename.
            manifest.append(str(image_path.absolute()))
            alphabet.update(text)
            all_records.append(
                {
                    "id": identifier,
                    "page_id": record["page_id"],
                    "line_id": record["line_id"],
                    "split": split,
                    "text": text,
                    "image": image_path.relative_to(output).as_posix(),
                    "quality_tier": record.get("quality_tier"),
                }
            )

        (output / f"{split}.txt").write_text(
            "\n".join(manifest) + "\n", encoding="utf-8"
        )
        page_sets[split] = pages

    for left_index, left in enumerate(SPLITS):
        for right in SPLITS[left_index + 1 :]:
            overlap = page_sets[left] & page_sets[right]
            if overlap:
                raise ValueError(
                    f"page-disjoint split violation between {left} and {right}: "
                    + ", ".join(sorted(overlap))
                )

    with (output / "records.jsonl").open("w", encoding="utf-8") as stream:
        for record in all_records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    (output / "alphabet.txt").write_text(
        "".join(sorted(alphabet)) + "\n", encoding="utf-8"
    )
    summary = {
        "format": "nippo-engine-neutral-line-ocr-benchmark",
        "format_version": 1,
        "source": str(source.relative_to(ROOT)),
        "normalization": "NFC",
        "splits": {
            split: {
                "lines": sum(record["split"] == split for record in all_records),
                "pages": len(page_sets[split]),
            }
            for split in SPLITS
        },
        "alphabet_size": len(alphabet),
        "page_disjoint": True,
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return result


if __name__ == "__main__":
    args = parser().parse_args()
    print(json.dumps(export(args.source, args.output), ensure_ascii=False, indent=2))
