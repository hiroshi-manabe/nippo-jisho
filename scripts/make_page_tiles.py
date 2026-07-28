#!/usr/bin/env python3
"""Generate reproducible overlapping image tiles from cached Gallica masters."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Sequence, Tuple

from PIL import Image


Box = Tuple[int, int, int, int]


class TileConfigError(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_box(box: Sequence[int], image_size: Tuple[int, int]) -> Box:
    if len(box) != 4 or not all(isinstance(value, int) for value in box):
        raise TileConfigError("box must contain four integer coordinates")
    left, top, right, bottom = box
    width, height = image_size
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise TileConfigError(
            f"box {list(box)} lies outside image bounds {width}x{height}"
        )
    return left, top, right, bottom


def vertical_tiles(box: Box, count: int, overlap: int) -> List[Box]:
    """Split a box vertically while giving adjacent tiles exact overlap."""

    if count < 1:
        raise TileConfigError("tile count must be at least 1")
    if overlap < 0:
        raise TileConfigError("overlap must not be negative")

    left, top, right, bottom = box
    height = bottom - top
    if count > height:
        raise TileConfigError("tile count exceeds the number of vertical pixels")
    if count > 1 and overlap >= math.ceil(height / count):
        raise TileConfigError("overlap must be smaller than a nominal tile height")

    upper_margin = overlap // 2
    lower_margin = overlap - upper_margin
    result: List[Box] = []
    for index in range(count):
        core_top = top + (height * index) // count
        core_bottom = top + (height * (index + 1)) // count
        tile_top = core_top if index == 0 else core_top - upper_margin
        tile_bottom = core_bottom if index == count - 1 else core_bottom + lower_margin
        result.append((left, tile_top, right, tile_bottom))
    return result


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if config.get("format") != "nippo-tile-config":
        raise TileConfigError("unsupported or missing config format")
    if config.get("format_version") != 0:
        raise TileConfigError("only experimental tile config version 0 is supported")
    return config


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def render_page(
    page: dict,
    master_dir: Path,
    output_dir: Path,
    quality: int,
) -> List[dict]:
    page_id = page.get("id")
    master_name = page.get("master")
    if not page_id or not master_name:
        raise TileConfigError("every page requires id and master")

    master_path = master_dir / master_name
    if not master_path.exists():
        raise TileConfigError(f"master image not found: {master_path}")

    records: List[dict] = []
    with Image.open(master_path) as image:
        image.load()
        image_size = image.size
        for zone in page.get("zones", []):
            zone_id = zone.get("id")
            if not zone_id:
                raise TileConfigError(f"zone without id on {page_id}")
            zone_box = validate_box(zone.get("box", []), image_size)
            for profile in zone.get("profiles", []):
                profile_id = profile.get("id")
                count = profile.get("tiles")
                overlap = profile.get("overlap_pixels")
                if not profile_id or not isinstance(count, int) or not isinstance(overlap, int):
                    raise TileConfigError(
                        f"profile on {page_id}/{zone_id} requires id, tiles, and overlap_pixels"
                    )

                boxes = vertical_tiles(zone_box, count, overlap)
                profile_dir = output_dir / page_id / profile_id / zone_id
                profile_dir.mkdir(parents=True, exist_ok=True)
                for index, tile_box in enumerate(boxes, start=1):
                    tile_id = f"{page_id}-{zone_id}-{profile_id}-t{index:02d}"
                    tile_path = profile_dir / f"t{index:02d}.jpg"
                    tile = image.crop(tile_box)
                    tile.save(
                        tile_path,
                        format="JPEG",
                        quality=quality,
                        subsampling=0,
                        optimize=True,
                    )
                    records.append(
                        {
                            "id": tile_id,
                            "page": page_id,
                            "zone": zone_id,
                            "profile": profile_id,
                            "index": index,
                            "count": count,
                            "box": list(tile_box),
                            "width": tile.width,
                            "height": tile.height,
                            "overlap_pixels": overlap,
                            "local_path": str(tile_path.relative_to(output_dir)),
                            "sha256": sha256_file(tile_path),
                        }
                    )

    return records


def build_parser(repo_root: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument(
        "--master-dir",
        type=Path,
        default=repo_root / ".cache" / "sources" / "bnf-gallica" / "master",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / ".cache" / "tiles",
    )
    parser.add_argument("--quality", type=int, default=95)
    return parser


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = build_parser(repo_root)
    args = parser.parse_args()
    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")

    try:
        config = load_config(args.config.resolve())
        master_dir = args.master_dir.resolve()
        output_dir = args.output_dir.resolve()
        records: List[dict] = []
        for page in config.get("pages", []):
            records.extend(render_page(page, master_dir, output_dir, args.quality))

        manifest = {
            "format": "nippo-tile-manifest",
            "format_version": 0,
            "config": str(args.config.resolve()),
            "master_dir": str(master_dir),
            "output_dir": str(output_dir),
            "jpeg_quality": args.quality,
            "tiles": records,
        }
        manifest_path = output_dir / "tiles.json"
        atomic_write_json(manifest_path, manifest)
        print(f"Generated {len(records)} tiles in {output_dir}")
        print(f"Manifest: {manifest_path}")
        return 0
    except (OSError, json.JSONDecodeError, TileConfigError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
