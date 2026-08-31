#!/usr/bin/env python3
"""Merge visually confirmed Kraken line crops into a clean-pair corpus."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

from build_clean_ocr_pairs import HIGH_RECALL_OUTPUT, ROOT, write_json


DEFAULT_BENCHMARK = ROOT / ".cache" / "ocr-model" / "kraken-line-benchmark-v1"
DEFAULT_ACCEPTS = (
    ROOT / "experiments" / "ocr" / "kraken-line-segmentation-v1-visual-accepts.json"
)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def supplemental_pair(base: dict, match: dict, image: str) -> dict:
    result = {
        **base,
        "image": image,
        "source_crop": match["kraken_crop"],
        "isolation_window": match["kraken_crop"],
        "metrics": {
            "segmentation_engine": "Kraken 5.2.9 blla.mlmodel",
            "baseline": match["kraken_baseline"],
            "boundary": match["kraken_boundary"],
        },
        "quality_flags": [],
        "width": match["kraken_width"],
        "height": match["kraken_height"],
        "sha256": match["kraken_sha256"],
        "recognition": match["recognition"],
        "recognition_cer": match["recognition_cer"],
        "crop_recognition": match["recognition"],
        "crop_recognition_cer": match["recognition_cer"],
        "alignment_margin": None,
        "alignment_displacement": match["alignment_displacement"],
        "source_candidate_id": match["kraken_candidate_id"],
        "quality_tier": "kraken-rectified",
        "visual_accept": True,
    }
    result.pop("reasons", None)
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", type=Path, default=HIGH_RECALL_OUTPUT)
    result.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    result.add_argument("--visual-accepts", type=Path, default=DEFAULT_ACCEPTS)
    return result


def main() -> int:
    args = parser().parse_args()
    accepted_ids = set(
        json.loads(args.visual_accepts.read_text(encoding="utf-8"))["pairs"]
    )
    existing = load_jsonl(args.dataset / "aligned-pairs.jsonl")
    existing_ids = {record["id"] for record in existing}
    rejected = load_jsonl(args.dataset / "alignment-rejected.jsonl")
    rejected_by_id = {
        record["id"]: record
        for record in rejected
        if record.get("text") and record["id"] in accepted_ids
    }
    matches = {
        record["id"]: record
        for record in load_jsonl(args.benchmark / "matched.jsonl")
        if record["id"] in accepted_ids
    }
    missing = accepted_ids - existing_ids - rejected_by_id.keys()
    if missing:
        raise ValueError(f"accepted IDs missing from corpus: {sorted(missing)}")
    if accepted_ids - existing_ids - matches.keys():
        raise ValueError("accepted IDs missing from Kraken benchmark")

    additions = []
    for line_id in sorted(accepted_ids - existing_ids):
        match = matches[line_id]
        source = args.benchmark / match["image"]
        relative = Path("kraken-images") / match["page_id"] / f"{match['line_id']}.png"
        destination = args.dataset / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if (
            hashlib.sha256(destination.read_bytes()).hexdigest()
            != match["kraken_sha256"]
        ):
            raise ValueError(f"checksum mismatch after copying {line_id}")
        additions.append(
            supplemental_pair(rejected_by_id[line_id], match, relative.as_posix())
        )

    combined = sorted(
        existing + additions,
        key=lambda record: (
            record["page_id"],
            record["column"],
            record["block"],
            record["block_index"],
        ),
    )
    added_ids = {record["id"] for record in additions}
    # Remove only the target-side rejection that the supplemental image
    # resolves.  Candidate-side diagnostic records may legitimately share a
    # canonical ID after a shifted sequence alignment and remain useful.
    remaining = [
        record
        for record in rejected
        if not (record["id"] in added_ids and record.get("text"))
    ]
    write_jsonl(args.dataset / "aligned-pairs.jsonl", combined)
    write_jsonl(args.dataset / "alignment-rejected.jsonl", remaining)
    for split in ("train", "dev", "test"):
        write_jsonl(
            args.dataset / f"aligned-{split}.jsonl",
            [record for record in combined if record["split"] == split],
        )

    summary_path = args.dataset / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    reason_counts = Counter(
        reason for record in remaining for reason in record.get("reasons", [])
    )
    alignment = summary["alignment"]
    alignment.update(
        {
            "accepted_pairs": len(combined),
            "rejected_target_lines": summary["candidate_lines"] - len(combined),
            "diagnostic_rejection_records": len(remaining),
            "unmatched_candidate_images": sum(
                record.get("text") == "" for record in remaining
            ),
            "acceptance_rate_from_all_candidates": len(combined)
            / summary["candidate_lines"],
            "accepted_by_split": dict(Counter(r["split"] for r in combined)),
            "accepted_by_quality_tier": dict(
                Counter(r.get("quality_tier", "unclassified") for r in combined)
            ),
            "visually_confirmed_pairs": sum(
                bool(record.get("visual_accept")) for record in combined
            ),
            "kraken_supplemental_pairs": len(
                [r for r in combined if r.get("quality_tier") == "kraken-rectified"]
            ),
            "kraken_visual_accepts": str(args.visual_accepts.relative_to(ROOT)),
            "rejection_reasons": dict(reason_counts.most_common()),
        }
    )
    write_json(summary_path, summary)
    print(
        json.dumps(
            {
                "added": len(additions),
                "accepted": len(combined),
                "rejected": summary["candidate_lines"] - len(combined),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
