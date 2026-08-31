#!/usr/bin/env python3
"""Build matched core/full manifests for the isolated-line OCR ablation."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from build_clean_ocr_pairs import HIGH_RECALL_OUTPUT, ROOT, write_json


DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "training-ablation-v2"
POSITIONAL_TIER = "positionally-anchored"


def load_jsonl(path: Path) -> list[dict]:
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


def link_image_roots(dataset: Path, output: Path, records: list[dict]) -> None:
    roots = sorted({Path(record["image"]).parts[0] for record in records})
    for name in roots:
        source = (dataset / name).resolve()
        destination = output / name
        if destination.is_symlink() and destination.resolve() == source:
            continue
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"refusing to replace {destination}")
        destination.symlink_to(source, target_is_directory=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", type=Path, default=HIGH_RECALL_OUTPUT)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return result


def main() -> int:
    args = parser().parse_args()
    by_split = {
        split: load_jsonl(args.dataset / f"aligned-{split}.jsonl")
        for split in ("train", "dev", "test")
    }
    core = {
        split: [
            record
            for record in records
            if record.get("quality_tier") != POSITIONAL_TIER
        ]
        for split, records in by_split.items()
    }

    # Only the training manifest differs. Both runs use the same core-only
    # development set for checkpoint selection and the same complete test set.
    variants = {
        "core": core["train"],
        "full": by_split["train"],
    }
    for name, training_records in variants.items():
        output = args.output / name
        output.mkdir(parents=True, exist_ok=True)
        manifests = {
            "train": training_records,
            "dev": core["dev"],
            "test": by_split["test"],
            "test-core": core["test"],
            "test-positional": [
                record
                for record in by_split["test"]
                if record.get("quality_tier") == POSITIONAL_TIER
            ],
        }
        for split, records in manifests.items():
            write_jsonl(output / f"{split}.jsonl", records)
        link_image_roots(
            args.dataset,
            output,
            [record for records in manifests.values() for record in records],
        )

    summary = {
        "format": "nippo-isolated-ocr-training-ablation",
        "format_version": 1,
        "source_dataset": str(args.dataset.relative_to(ROOT)),
        "core_excludes_quality_tier": POSITIONAL_TIER,
        "core_train_lines": len(core["train"]),
        "full_train_lines": len(by_split["train"]),
        "shared_core_dev_lines": len(core["dev"]),
        "shared_complete_test_lines": len(by_split["test"]),
        "test_core_lines": len(core["test"]),
        "test_positional_lines": len(by_split["test"]) - len(core["test"]),
        "positional_lines_by_source_split": dict(
            Counter(
                record["split"]
                for records in by_split.values()
                for record in records
                if record.get("quality_tier") == POSITIONAL_TIER
            )
        ),
    }
    write_json(args.output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
