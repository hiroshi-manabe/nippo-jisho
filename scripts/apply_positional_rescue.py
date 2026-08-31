#!/usr/bin/env python3
"""Merge audited positional midpoint crops into the high-recall corpus."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

from build_clean_ocr_pairs import HIGH_RECALL_OUTPUT, ROOT, write_json
from build_positional_rescue import DEFAULT_OUTPUT, load_jsonl


DEFAULT_EVIDENCE = ROOT / "experiments" / "ocr" / "positional-rescue-v1-audit.json"


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", type=Path, default=HIGH_RECALL_OUTPUT)
    result.add_argument("--candidates", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    return result


def main() -> int:
    args = parser().parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    if evidence.get("result") != "passed" or not evidence.get("sample_size"):
        raise ValueError("positional rescue requires a passed visual sample audit")
    candidates_path = args.candidates / "candidates.jsonl"
    candidates = load_jsonl(candidates_path)
    if evidence["candidate_count"] != len(candidates):
        raise ValueError("candidate count differs from the audited build")
    candidate_sha256 = hashlib.sha256(candidates_path.read_bytes()).hexdigest()
    if evidence.get("candidates_sha256") != candidate_sha256:
        raise ValueError("candidate manifest differs from the audited build")
    sampled_ids = evidence.get("sample_ids", [])
    if len(sampled_ids) != evidence["sample_size"]:
        raise ValueError("audit sample IDs do not match the recorded sample size")

    existing = load_jsonl(args.dataset / "aligned-pairs.jsonl")
    existing_ids = {record["id"] for record in existing}
    rejected = load_jsonl(args.dataset / "alignment-rejected.jsonl")
    rejected_ids = {record["id"] for record in rejected if record.get("text")}
    additions = []
    for candidate in candidates:
        if candidate["id"] in existing_ids:
            continue
        if candidate["id"] not in rejected_ids:
            raise ValueError(f"candidate is not a rejected target: {candidate['id']}")
        source = args.candidates / candidate["image"]
        relative = (
            Path("positional-images")
            / candidate["page_id"]
            / f"{candidate['line_id']}.png"
        )
        destination = args.dataset / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != candidate["sha256"]:
            raise ValueError(f"checksum mismatch after copying {candidate['id']}")
        pair = {
            **candidate,
            "image": relative.as_posix(),
            "recognition": None,
            "recognition_cer": None,
            "crop_recognition": None,
            "crop_recognition_cer": None,
            "alignment_margin": None,
            "alignment_displacement": 0,
            "quality_tier": "positionally-anchored",
            "positional_audit": str(args.evidence.relative_to(ROOT)),
        }
        pair.pop("reasons", None)
        pair.pop("candidate_reason", None)
        additions.append(pair)

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
            "positionally_anchored_pairs": sum(
                r.get("quality_tier") == "positionally-anchored" for r in combined
            ),
            "positional_audit": str(args.evidence.relative_to(ROOT)),
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
