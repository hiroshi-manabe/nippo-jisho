#!/usr/bin/env python3
"""Validate and preserve a generated scan-bootstrap batch in the repository."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / ".cache" / "ocr-model" / "scan-bootstrap-bulk-v1"
DEFAULT_OUTPUT = ROOT / "pilot" / "ocr-bootstrap" / "f0251-f0642"
SCANS = ROOT / "build" / "nippo-jisho-images" / "scans" / "native"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_id(number: int) -> str:
    return f"bnf-f{number:04d}"


def validate_candidate(path: Path, number: int) -> dict:
    package = load_json(path)
    identifier = page_id(number)
    if package.get("format") != "nippo-ocr-level1-bootstrap-candidate":
        raise ValueError(f"{path}: unsupported candidate format")
    if package.get("id") != identifier or package.get("page", {}).get("id") != identifier:
        raise ValueError(f"{path}: page identifier mismatch")
    review = package["page"].get("review", {})
    if review.get("physical_lineation_checked") is not False:
        raise ValueError(f"{path}: candidate falsely claims checked lineation")
    if review.get("status") != "visual_draft":
        raise ValueError(f"{path}: candidate must remain a visual draft")
    assessment = package.get("audit", {}).get("bulk_assessment")
    if not isinstance(assessment, dict):
        raise ValueError(f"{path}: missing bulk assessment")
    scan = SCANS / f"f{number:04d}.jpg"
    if package["page"]["source"].get("master_sha256") != digest(scan):
        raise ValueError(f"{path}: source scan digest mismatch")
    body_ids = {
        line["id"]
        for zone in package["page"]["zones"]
        if zone.get("kind") == "column"
        for line in zone.get("lines", [])
    }
    geometry_ids = {
        line_id
        for column in package["geometry"]["columns"].values()
        for line_id in column.get("lines", {})
    }
    if body_ids != geometry_ids:
        raise ValueError(f"{path}: body text and geometry identifiers differ")
    return package


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--first", type=int, default=251)
    parser.add_argument("--last", type=int, default=642)
    parser.add_argument("--control-pages", nargs="*", type=int, default=(248, 249, 250))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    source = args.input.resolve()
    output = args.output.resolve()
    report = load_json(source / "report.json")
    if not report.get("gate", {}).get("passed"):
        raise SystemExit("refusing to preserve a batch whose benchmark gate failed")
    reported = {item["page"]: item for item in report.get("targets", [])}
    failures = {item["page"]: item for item in report.get("target_failures", [])}
    expected = set(range(args.first, args.last + 1))
    if set(reported) | set(failures) != expected:
        missing = sorted(expected - set(reported) - set(failures))
        unexpected = sorted((set(reported) | set(failures)) - expected)
        raise SystemExit(
            f"report target mismatch; missing={missing[:10]}, unexpected={unexpected[:10]}"
        )
    if output.exists():
        if not args.replace:
            raise SystemExit(f"output already exists: {output}; pass --replace deliberately")
        shutil.rmtree(output)
    pages_dir = output / "pages"
    pages_dir.mkdir(parents=True)
    eligible = []
    quarantined = []
    totals = {
        "body_lines": 0,
        "heading_lines": 0,
        "uncertain_bottom_rows": 0,
        "initial_repairs": 0,
    }
    for number in sorted(reported):
        path = source / "candidates" / f"{page_id(number)}.json"
        package = validate_candidate(path, number)
        shutil.copy2(path, pages_dir / path.name)
        summary = reported[number]
        for key in totals:
            totals[key] += summary[key]
        assessment = package["audit"]["bulk_assessment"]
        if assessment["eligible_for_provisional_review_queue"]:
            eligible.append(number)
        else:
            quarantined.append(
                {"page": number, "reasons": assessment.get("reasons", [])}
            )
    controls_dir = output / "controls"
    controls_dir.mkdir()
    controls = []
    for number in args.control_pages:
        path = source / "candidates" / f"{page_id(number)}.json"
        if not path.exists():
            raise SystemExit(f"missing control candidate: {path}")
        shutil.copy2(path, controls_dir / path.name)
        controls.append(number)
    manifest = {
        "format": "nippo-ocr-level1-bootstrap-batch",
        "format_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "range": {"first": args.first, "last": args.last},
        "status": "machine_provisional_not_canonical",
        "benchmark": report["benchmark"]["aggregate"],
        "gate": report["gate"],
        "counts": {
            "requested_pages": len(expected),
            "generated_pages": len(reported),
            "eligible_ordinary_two_column_pages": len(eligible),
            "quarantined_pages": len(quarantined),
            "inference_failures": len(failures),
            **totals,
        },
        "eligible_pages": eligible,
        "quarantined_pages": quarantined,
        "inference_failures": [failures[number] for number in sorted(failures)],
        "control_pages": controls,
        "canonical_application": "blocked_pending_visual_lineation_and_geometry_review",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    benchmark = manifest["benchmark"]
    (output / "README.md").write_text(
        "\n".join(
            [
                f"# OCR bootstrap candidates f{args.first:04d}–f{args.last:04d}",
                "",
                f"This directory preserves {len(reported)} machine-provisional page packages",
                "generated directly from the native scans. They are evidence-bearing review",
                "candidates, not canonical Level 1 pages and not human-checked transcriptions.",
                "",
                f"- Ordinary two-column candidates: {len(eligible)}",
                f"- Structurally quarantined candidates: {len(quarantined)}",
                f"- Inference failures: {len(failures)}",
                f"- Provisional body rows: {totals['body_lines']:,}",
                f"- Held-out body-row recall: {benchmark['body_line_recall']:.2%}",
                f"- Held-out body-row precision: {benchmark['body_line_precision']:.2%}",
                f"- Held-out diplomatic character accuracy: {benchmark['character_accuracy']:.2%}",
                "",
                "`pages/` contains every target candidate. `controls/` contains fresh OCR-derived",
                "candidates for the frozen near-range control pages; the pre-bootstrap originals",
                "live in `../reference-f0248-f0250/`. `manifest.json` lists the eligible pages,",
                "quarantines with reasons, failures, totals, and the benchmark gate.",
                "",
                "Every candidate retains `physical_lineation_checked: false`. Promotion still",
                "requires complete visual confirmation of physical rows, page furniture, enlarged",
                "initials, crop readability, and the diplomatic transcription.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(
        f"Preserved {len(reported)} pages: {len(eligible)} eligible ordinary pages, "
        f"{len(quarantined)} quarantined, {len(failures)} inference failures."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
