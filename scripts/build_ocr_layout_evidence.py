#!/usr/bin/env python3
"""Build an immutable, dictionary-wide archive of raw OCR layout evidence."""

from __future__ import annotations

import argparse
from datetime import date
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SCANS = ROOT / "build" / "nippo-jisho-images" / "scans" / "native"
CACHE = ROOT / ".cache" / "ocr-model" / "whole-book-layout-v1"
OUTPUT = ROOT / "pilot" / "ocr-layout-evidence" / "v1"

# All of these were produced by prepare_calamari_page_drafts.py with the same
# scan-band/Calamari method.  Earlier entries win when duplicate pages exist.
DRAFT_ROOTS = (
    CACHE / "drafts",
    ROOT / ".cache/ocr-model/scan-bootstrap-bulk-v1/raw/drafts",
    ROOT / ".cache/ocr-model/scan-bootstrap-v1/raw/drafts",
    ROOT / ".cache/ocr-model/ocr-page-data-v1/drafts",
    ROOT / ".cache/ocr-model/calamari-page-drafts-v1/drafts",
)
SEGMENTATION_ROOTS = (
    CACHE / "segmentation",
    ROOT / ".cache/ocr-model/scan-bootstrap-bulk-v1/raw/segmentation",
    ROOT / ".cache/ocr-model/scan-bootstrap-v1/raw/segmentation",
    ROOT / ".cache/ocr-model/ocr-page-data-v1/segmentation",
    ROOT / ".cache/ocr-model/calamari-page-drafts-v1/segmentation",
    ROOT / ".cache/ocr-first-geometry-v1/segmentation",
    ROOT / ".cache/ocr-model/f0151-kraken-segmentation",
)
EXPECTED_SEGMENTATION = "Kraken 5.2.9 bundled blla.mlmodel"
EXPECTED_RECOGNITION = "Calamari book-specific antiquatype model"


def page_id(number: int) -> str:
    return f"bnf-f{number:04d}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_page(roots: Iterable[Path], filename: str) -> Path | None:
    return next((root / filename for root in roots if (root / filename).exists()), None)


def seed_segmentations(numbers: list[int]) -> None:
    destination = CACHE / "segmentation"
    destination.mkdir(parents=True, exist_ok=True)
    for number in numbers:
        target = destination / f"f{number:04d}.json"
        if target.exists():
            continue
        source = find_page(SEGMENTATION_ROOTS[1:], target.name)
        if source:
            shutil.copyfile(source, target)


def generate_missing(numbers: list[int]) -> None:
    missing = [
        number
        for number in numbers
        if find_page(DRAFT_ROOTS, f"{page_id(number)}.json") is None
    ]
    if not missing:
        return
    seed_segmentations(missing)
    command = [
        sys.executable,
        str(ROOT / "scripts/prepare_calamari_page_drafts.py"),
        "--pages",
        *map(str, missing),
        "--benchmark-pages",
        "--output",
        str(CACHE),
    ]
    subprocess.run(command, check=True)


def validate_draft(draft: dict, identifier: str) -> None:
    if draft.get("format") != "nippo-ocr-page-draft" or draft.get("id") != identifier:
        raise ValueError(f"invalid OCR draft identity: {identifier}")
    method = draft.get("method", {})
    if method.get("segmentation") != EXPECTED_SEGMENTATION:
        raise ValueError(f"unexpected segmentation method: {identifier}")
    if method.get("recognition") != EXPECTED_RECOGNITION:
        raise ValueError(f"unexpected recognition method: {identifier}")
    for column in ("column-1", "column-2"):
        for line in draft.get("columns", {}).get(column, {}).get("lines", []):
            required = {
                "id", "source_detection_id", "text", "centre", "crop",
                "ocr_crop", "baseline", "boundary", "prepared_sha256",
            }
            absent = required - line.keys()
            if absent:
                raise ValueError(
                    f"{identifier}/{line.get('id', '?')}: missing {sorted(absent)}"
                )


def evidence_record(number: int, draft_path: Path) -> dict:
    identifier = page_id(number)
    draft = load_json(draft_path)
    validate_draft(draft, identifier)
    scan = SCANS / f"f{number:04d}.jpg"
    if not scan.exists():
        raise FileNotFoundError(scan)
    return {
        "format": "nippo-raw-ocr-layout-evidence",
        "format_version": 1,
        "id": identifier,
        "source": {
            **draft["source"],
            "scan_sha256": sha256(scan),
            "ocr_draft_sha256": sha256(draft_path),
        },
        "method": draft["method"],
        "limitations": draft.get("limitations", []),
        "columns": draft["columns"],
    }


def encoded(record: dict) -> bytes:
    raw = (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return gzip.compress(raw, compresslevel=9, mtime=0)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--first", type=int, default=13)
    result.add_argument("--last", type=int, default=642)
    result.add_argument("--replace", action="store_true")
    result.add_argument("--skip-generate", action="store_true")
    result.add_argument("--output", type=Path, default=OUTPUT)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.first < 1 or args.last < args.first:
        raise SystemExit("invalid page range")
    numbers = list(range(args.first, args.last + 1))
    if not args.skip_generate:
        generate_missing(numbers)

    page_dir = args.output / "pages"
    page_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    total_lines = 0
    for number in numbers:
        identifier = page_id(number)
        draft_path = find_page(DRAFT_ROOTS, f"{identifier}.json")
        if draft_path is None:
            raise FileNotFoundError(f"missing OCR draft for {identifier}")
        record = evidence_record(number, draft_path)
        payload = encoded(record)
        target = page_dir / f"{identifier}.json.gz"
        if target.exists() and target.read_bytes() != payload and not args.replace:
            raise SystemExit(f"immutable evidence differs: {target}; use --replace")
        target.write_bytes(payload)
        line_count = sum(
            len(column.get("lines", [])) for column in record["columns"].values()
        )
        total_lines += line_count
        pages.append(
            {
                "id": identifier,
                "lines": line_count,
                "record": target.relative_to(args.output).as_posix(),
                "record_sha256": hashlib.sha256(payload).hexdigest(),
                "scan_sha256": record["source"]["scan_sha256"],
                "ocr_draft_sha256": record["source"]["ocr_draft_sha256"],
            }
        )

    checkpoint = ROOT / ".cache/ocr-model/runs/calamari-antiqua-book-codec-v1/best.ckpt"
    checkpoint_files = sorted(path for path in checkpoint.rglob("*") if path.is_file())
    checkpoint_digest = hashlib.sha256()
    for path in checkpoint_files:
        checkpoint_digest.update(path.relative_to(checkpoint).as_posix().encode())
        checkpoint_digest.update(bytes.fromhex(sha256(path)))
    manifest = {
        "format": "nippo-ocr-layout-evidence-manifest",
        "format_version": 1,
        "created": date.today().isoformat(),
        "range": [args.first, args.last],
        "pages": pages,
        "totals": {"pages": len(pages), "detected_lines": total_lines},
        "method": {
            "segmentation": EXPECTED_SEGMENTATION,
            "recognition": EXPECTED_RECOGNITION,
            "checkpoint_tree_sha256": checkpoint_digest.hexdigest(),
            "source_image": "native Gallica JPEG",
        },
        "policy": {
            "canonical_text_modified": False,
            "canonical_geometry_modified": False,
            "raw_page_records_immutable_by_default": True,
        },
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Archived {len(pages)} pages and {total_lines} detected lines in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
