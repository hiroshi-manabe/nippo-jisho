#!/usr/bin/env python3
"""Collect Calamari ``.pred.txt`` files into benchmark prediction JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import unicodedata


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def main(args: argparse.Namespace) -> int:
    records = [
        record
        for record in load_jsonl(args.records)
        if record["split"] == args.split
    ]
    predictions = []
    missing = []
    for record in records:
        prediction_path = args.prediction_dir / (
            Path(record["image"]).stem + args.extension
        )
        if not prediction_path.is_file():
            missing.append(str(prediction_path))
            continue
        prediction = unicodedata.normalize(
            "NFC", prediction_path.read_text(encoding="utf-8").rstrip("\r\n")
        )
        predictions.append({"id": record["id"], "text": prediction})

    if missing:
        preview = "\n".join(missing[:10])
        raise FileNotFoundError(
            f"missing {len(missing)} prediction files; first paths:\n{preview}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for prediction in predictions:
            stream.write(json.dumps(prediction, ensure_ascii=False) + "\n")
    print(f"wrote {len(predictions)} predictions to {args.output}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--records", type=Path, required=True)
    result.add_argument("--split", choices=("train", "dev", "test"), required=True)
    result.add_argument("--prediction-dir", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--extension", default=".pred.txt")
    return result


if __name__ == "__main__":
    raise SystemExit(main(parser().parse_args()))
