#!/usr/bin/env python3
"""Prepare committed page metadata and overview thumbnails from local masters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--master-dir",
        type=Path,
        default=root / ".cache" / "sources" / "bnf-gallica" / "master",
    )
    parser.add_argument(
        "--thumbnail-dir",
        type=Path,
        default=root / "site" / "assets" / "thumbnails",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=root / "pilot" / "human-review" / "page-images.json",
    )
    args = parser.parse_args()
    masters = sorted(args.master_dir.glob("f[0-9][0-9][0-9][0-9].jpg"))
    if len(masters) != 651:
        raise SystemExit(f"expected 651 masters, found {len(masters)}")
    args.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for master_path in masters:
        leaf = int(master_path.stem[1:])
        with Image.open(master_path) as source:
            width, height = source.size
            thumbnail_path = args.thumbnail_dir / f"f{leaf:04d}.webp"
            if not thumbnail_path.exists():
                preview = ImageOps.exif_transpose(source).convert("RGB")
                preview.thumbnail((220, 320), Image.Resampling.LANCZOS)
                preview.save(thumbnail_path, "WEBP", quality=72, method=4)
        pages.append({"leaf": leaf, "width": width, "height": height})
    payload = {
        "format": "nippo-review-page-images",
        "format_version": 1,
        "source": "BnF Gallica ark:/12148/bpt6k852354j",
        "pages": pages,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared {len(pages)} page records and thumbnails.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
