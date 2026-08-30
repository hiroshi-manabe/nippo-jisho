#!/usr/bin/env python3
"""Build page-disjoint line-image data for the experimental Nippo OCR model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import unicodedata

import numpy as np
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "dataset-v2"


def page_number(page_id: str) -> int:
    return int(page_id.removeprefix("bnf-f"))


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def line_texts(page: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for zone in page["zones"]:
        for line in zone.get("lines", []):
            text = "".join(run["text"] for run in line["runs"]).strip()
            if text:
                result[line["id"]] = unicodedata.normalize("NFC", text)
    return result


def split_pages(
    page_ids: list[str], *, seed: int, dev_fraction: float, test_fraction: float
) -> dict[str, list[str]]:
    shuffled = list(page_ids)
    random.Random(seed).shuffle(shuffled)
    dev_count = round(len(shuffled) * dev_fraction)
    test_count = round(len(shuffled) * test_fraction)
    test = sorted(shuffled[:test_count], key=page_number)
    dev = sorted(shuffled[test_count : test_count + dev_count], key=page_number)
    train = sorted(shuffled[test_count + dev_count :], key=page_number)
    return {"train": train, "dev": dev, "test": test}


def trim_horizontal(line: Image.Image, padding: int = 12) -> Image.Image:
    """Trim blank margins while ignoring dense vertical column rules."""
    pixels = np.asarray(line)
    maximum_rule_density = int(line.height * 0.6)
    dark = np.count_nonzero(pixels < 180, axis=0)
    active = np.flatnonzero((dark >= 2) & (dark <= maximum_rule_density))
    if not active.size:
        return line
    left = max(0, int(active.min()) - padding)
    right = min(line.width, int(active.max()) + padding + 1)
    if right - left < 32:
        return line
    return line.crop((left, 0, right, line.height))


def prepare_crop(
    scan: Image.Image,
    crop: list[int],
    *,
    height: int = 48,
    max_width: int = 1024,
) -> Image.Image:
    """Apply the dataset's deterministic line-image preprocessing in memory."""
    x, y, width, crop_height = crop
    line = scan.crop((x, y, x + width, y + crop_height)).convert("L")
    line = ImageOps.autocontrast(line, cutoff=0.2)
    line = trim_horizontal(line)
    resized_width = min(max_width, max(1, round(line.width * height / line.height)))
    return line.resize((resized_width, height), Image.Resampling.LANCZOS)


def save_crop(
    scan: Image.Image, crop: list[int], output: Path, *, height: int, max_width: int
) -> tuple[int, int, str]:
    line = prepare_crop(scan, crop, height=height, max_width=max_width)
    output.parent.mkdir(parents=True, exist_ok=True)
    line.save(output, format="PNG", optimize=True)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return line.width, line.height, digest


def build(args: argparse.Namespace) -> dict:
    compiled = ROOT / "pilot" / "format-v1-trial" / "level1"
    geometry_path = ROOT / "pilot" / "human-review" / "line-geometry.json"
    scans = ROOT / "build" / "nippo-jisho-images" / "scans" / "native"
    geometry_pages = {page["id"]: page for page in load_json(geometry_path)["pages"]}

    eligible: list[str] = []
    for number in range(args.first_page, args.last_page + 1):
        page_id = f"bnf-f{number:04d}"
        if (compiled / f"{page_id}.json").exists() and page_id in geometry_pages:
            eligible.append(page_id)
    splits = split_pages(
        eligible,
        seed=args.seed,
        dev_fraction=args.dev_fraction,
        test_fraction=args.test_fraction,
    )
    split_for_page = {
        page_id: split for split, pages in splits.items() for page_id in pages
    }
    records: dict[str, list[dict]] = {name: [] for name in splits}
    skipped: list[dict] = []
    characters: set[str] = set()

    for page_id in eligible:
        number = page_number(page_id)
        scan_path = scans / f"f{number:04d}.jpg"
        if not scan_path.exists():
            raise FileNotFoundError(scan_path)
        text_by_id = line_texts(load_json(compiled / f"{page_id}.json"))
        page_geometry = geometry_pages[page_id]
        with Image.open(scan_path) as scan:
            source_size = tuple(page_geometry["source_size"])
            if scan.size != source_size:
                raise ValueError(
                    f"{page_id}: scan is {scan.size}, geometry expects {source_size}"
                )
            for column_name, column in page_geometry["columns"].items():
                for line_id, line_geometry in column["lines"].items():
                    text = text_by_id.get(line_id)
                    if text is None:
                        skipped.append(
                            {"page_id": page_id, "line_id": line_id, "reason": "no_text"}
                        )
                        continue
                    relative = Path("images") / page_id / f"{line_id}.png"
                    width, height, digest = save_crop(
                        scan,
                        line_geometry["crop"],
                        args.output / relative,
                        height=args.height,
                        max_width=args.max_width,
                    )
                    characters.update(text)
                    records[split_for_page[page_id]].append(
                        {
                            "id": f"{page_id}/{line_id}",
                            "page_id": page_id,
                            "line_id": line_id,
                            "column": column_name,
                            "image": relative.as_posix(),
                            "width": width,
                            "height": height,
                            "sha256": digest,
                            "text": text,
                        }
                    )

    for split, items in records.items():
        manifest = args.output / f"{split}.jsonl"
        with manifest.open("w", encoding="utf-8") as stream:
            for item in items:
                stream.write(json.dumps(item, ensure_ascii=False) + "\n")

    metadata = {
        "format": "nippo-ocr-line-dataset",
        "format_version": 1,
        "source_page_range": [args.first_page, args.last_page],
        "seed": args.seed,
        "split_method": "seeded page-level shuffle",
        "target": "NFC diplomatic text without typeface markup or outer whitespace",
        "image": {
            "mode": "grayscale",
            "height": args.height,
            "max_width": args.max_width,
            "autocontrast_cutoff": 0.2,
            "horizontal_trim": "ink projection excluding dense vertical rules, 12px padding",
        },
        "pages": splits,
        "counts": {name: len(items) for name, items in records.items()},
        "characters": sorted(characters),
        "skipped": skipped,
    }
    write_json(args.output / "dataset.json", metadata)
    return metadata


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--first-page", type=int, default=13)
    result.add_argument("--last-page", type=int, default=150)
    result.add_argument("--seed", type=int, default=1603)
    result.add_argument("--dev-fraction", type=float, default=0.1)
    result.add_argument("--test-fraction", type=float, default=0.1)
    result.add_argument("--height", type=int, default=48)
    result.add_argument("--max-width", type=int, default=1024)
    return result


def main() -> int:
    args = parser().parse_args()
    metadata = build(args)
    print(
        "Built Nippo OCR dataset: "
        + ", ".join(f"{name}={count}" for name, count in metadata["counts"].items())
    )
    print(args.output / "dataset.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
