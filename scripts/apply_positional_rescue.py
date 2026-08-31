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
    candidates_path = args.candidates / "validated-candidates.jsonl"
    candidates = load_jsonl(candidates_path)
    if evidence["candidate_count"] != len(candidates):
        raise ValueError("candidate count differs from the audited build")
    candidate_sha256 = hashlib.sha256(candidates_path.read_bytes()).hexdigest()
    if evidence.get("validated_candidates_sha256") != candidate_sha256:
        raise ValueError("candidate manifest differs from the audited build")
    sampled_ids = evidence.get("sample_ids", [])
    if len(sampled_ids) != evidence["sample_size"]:
        raise ValueError("audit sample IDs do not match the recorded sample size")

    existing = load_jsonl(args.dataset / "aligned-pairs.jsonl")
    existing_by_id = {record["id"]: record for record in existing}
    rejected = load_jsonl(args.dataset / "alignment-rejected.jsonl")
    rejected_ids = {record["id"] for record in rejected if record.get("text")}
    all_candidates = load_jsonl(args.candidates / "candidates.jsonl")
    validation_rejected = load_jsonl(
        args.candidates / "validation-rejected.jsonl"
    )
    candidate_by_id = {record["id"]: record for record in all_candidates}
    candidate_by_id.update({record["id"]: record for record in candidates})
    candidate_by_id.update(
        {record["id"]: record for record in validation_rejected}
    )
    validated_ids = {record["id"] for record in candidates}
    invalid_ids = set(candidate_by_id) - validated_ids
    additions = []
    for candidate in candidates:
        existing_record = existing_by_id.get(candidate["id"])
        if (
            existing_record is None
            and candidate["id"] not in rejected_ids
        ):
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
        [
            record
            for record in existing
            if record.get("quality_tier") != "positionally-anchored"
        ]
        + additions,
        key=lambda record: (
            record["page_id"],
            record["column"],
            record["block"],
            record["block_index"],
        ),
    )
    remaining = [
        record
        for record in rejected
        if not (record["id"] in candidate_by_id and record.get("text"))
    ]
    raw = load_jsonl(args.dataset / "pairs.jsonl") + load_jsonl(
        args.dataset / "rejected.jsonl"
    )
    raw_by_id = {record["id"]: record for record in raw if record.get("text")}
    for identifier in sorted(invalid_ids):
        candidate = candidate_by_id[identifier]
        base = raw_by_id.get(identifier, candidate)
        remaining.append(
            {
                **base,
                "text": candidate["text"],
                "reasons": ["positional_crop_recognition_mismatch"],
                "positional_probe_recognition": candidate.get(
                    "positional_probe_recognition"
                ),
                "positional_probe_cer": candidate.get("positional_probe_cer"),
            }
        )
    remaining.sort(
        key=lambda record: (
            record["page_id"],
            record["column"],
            record["block"],
            record["block_index"],
            not bool(record.get("text")),
        )
    )
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
                "added": sum(
                    record["id"] not in existing_by_id for record in additions
                ),
                "refreshed": sum(
                    record["id"] in existing_by_id for record in additions
                ),
                "returned_to_rejected": len(invalid_ids),
                "accepted": len(combined),
                "rejected": summary["candidate_lines"] - len(combined),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
