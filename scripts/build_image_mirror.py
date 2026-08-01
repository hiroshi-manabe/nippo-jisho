#!/usr/bin/env python3
"""Build the static Cloudflare Pages image mirror from downloaded Gallica masters."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil

from PIL import Image, ImageOps


EXPECTED_PAGES = 651
SIZES = (1000, 2200)
SOURCE_LABEL = "Source gallica.bnf.fr / Bibliothèque nationale de France"
ARK = "ark:/12148/bpt6k852354j"


def variant_dimensions(width: int, height: int, target_width: int) -> tuple[int, int]:
    if width <= target_width:
        return width, height
    return target_width, round(height * target_width / width)


def link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def prepare_variant(source: Path, destination: Path, target_width: int, force: bool) -> None:
    if destination.exists() and not force:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp.jpg")
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        target = variant_dimensions(*image.size, target_width)
        if target != image.size:
            image = image.resize(target, Image.Resampling.LANCZOS)
        image.save(temporary, "JPEG", quality=90, optimize=True, progressive=True)
    temporary.replace(destination)


def page_record(source: Path) -> dict[str, object]:
    leaf = int(source.stem[1:])
    with Image.open(source) as image:
        width, height = image.size
    return {
        "leaf": leaf,
        "width": width,
        "height": height,
        "native": f"scans/native/f{leaf:04d}.jpg",
        "preview": f"scans/1000/f{leaf:04d}.jpg",
        "reading": f"scans/2200/f{leaf:04d}.jpg",
        "gallica": f"https://gallica.bnf.fr/{ARK}/f{leaf}.item",
    }


def write_support_files(output: Path, pages: list[dict[str, object]]) -> None:
    manifest = {
        "format": "nippo-jisho-image-mirror",
        "format_version": 1,
        "source": SOURCE_LABEL,
        "source_object": f"https://gallica.bnf.fr/{ARK}",
        "pages": pages,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "_headers").write_text(
        "/*\n"
        "  Access-Control-Allow-Origin: *\n"
        "  X-Content-Type-Options: nosniff\n"
        "/scans/*\n"
        "  Cache-Control: public, max-age=31536000, immutable\n",
        encoding="utf-8",
    )
    (output / "index.html").write_text(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width\">"
        "<title>Nippo Jisho scan images</title>"
        "<style>body{max-width:48rem;margin:4rem auto;padding:0 1.25rem;"
        "font:18px/1.6 system-ui,sans-serif;color:#26231f}a{color:#7a351f}</style>"
        "</head><body><h1>Nippo Jisho scan images</h1>"
        "<p>This static site supplies stable scan images to the "
        "<a href=\"https://hiroshi-manabe.github.io/nippo-jisho/\">Nippo Jisho "
        "transcription project</a>.</p>"
        f"<p>{SOURCE_LABEL}. View the "
        f"<a href=\"https://gallica.bnf.fr/{ARK}\">original Gallica object</a>.</p>"
        "<p><a href=\"manifest.json\">Image manifest</a></p></body></html>\n",
        encoding="utf-8",
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--master-dir",
        type=Path,
        default=root / ".cache" / "sources" / "bnf-gallica" / "master",
    )
    parser.add_argument(
        "--variant-cache",
        type=Path,
        default=root / ".cache" / "image-mirror",
    )
    parser.add_argument(
        "--output", type=Path, default=root / "build" / "nippo-jisho-images"
    )
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    masters = sorted(args.master_dir.glob("f[0-9][0-9][0-9][0-9].jpg"))
    if len(masters) != EXPECTED_PAGES:
        raise SystemExit(f"expected {EXPECTED_PAGES} masters, found {len(masters)}")

    jobs = [
        (source, args.variant_cache / str(size) / source.name, size, args.force)
        for source in masters
        for size in SIZES
    ]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda job: prepare_variant(*job), jobs))

    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    pages = [page_record(source) for source in masters]
    for source in masters:
        link_or_copy(source, args.output / "scans" / "native" / source.name)
        for size in SIZES:
            link_or_copy(
                args.variant_cache / str(size) / source.name,
                args.output / "scans" / str(size) / source.name,
            )
    write_support_files(args.output, pages)
    print(f"Prepared {len(pages)} pages in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
