#!/usr/bin/env python3
"""Rectify line polygons from Kraken segmentation JSON files.

Run this script with the separate Kraken environment.  The resulting images
retain Kraken's curved polygon extraction instead of reducing each detection
to an axis-aligned rectangle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image
from kraken.containers import Segmentation
from kraken.lib.segmentation import extract_polygons


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGES = (
    13,
    18,
    24,
    31,
    46,
    58,
    68,
    83,
    96,
    110,
    123,
    125,
    136,
    143,
    150,
)
DEFAULT_KRAKEN = ROOT / ".cache" / "ocr-model" / "kraken-segmentation-v1"
DEFAULT_OUTPUT = DEFAULT_KRAKEN / "extracted"
SCANS = ROOT / "build" / "nippo-jisho-images" / "scans" / "native"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--pages", nargs="+", type=int, default=DEFAULT_PAGES)
    result.add_argument("--kraken", type=Path, default=DEFAULT_KRAKEN)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return result


def main() -> int:
    args = parser().parse_args()
    manifest = []
    for page_number in args.pages:
        page_id = f"bnf-f{page_number:04d}"
        segmentation_path = args.kraken / f"f{page_number:04d}.json"
        segmentation_data = json.loads(segmentation_path.read_text(encoding="utf-8"))
        segmentation = Segmentation(**segmentation_data)
        scan_path = SCANS / f"f{page_number:04d}.jpg"
        page_output = args.output / page_id
        page_output.mkdir(parents=True, exist_ok=True)
        with Image.open(scan_path) as scan:
            extracted = list(extract_polygons(scan.convert("RGB"), segmentation))
        if len(extracted) != len(segmentation_data["lines"]):
            raise ValueError(
                f"{page_id}: extracted {len(extracted)} images for "
                f"{len(segmentation_data['lines'])} lines"
            )
        for index, ((image, line), source) in enumerate(
            zip(extracted, segmentation_data["lines"])
        ):
            if line.id != source["id"]:
                raise ValueError(f"{page_id}: extraction order changed at {index}")
            relative = Path(page_id) / f"{line.id}.png"
            image.save(args.output / relative, format="PNG", optimize=True)
            manifest.append(
                {
                    "page_id": page_id,
                    "index": index,
                    "kraken_id": line.id,
                    "image": relative.as_posix(),
                    "width": image.width,
                    "height": image.height,
                }
            )
        print(f"{page_id}: extracted {len(extracted)} lines", flush=True)
    (args.output / "manifest.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in manifest),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
