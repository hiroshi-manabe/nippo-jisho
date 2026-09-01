#!/usr/bin/env python3
"""Evaluate line OCR predictions with diplomatic feature diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import unicodedata


PAIR_GROUPS = {
    "short_s_or_long_s": set("sſ"),
    "q_or_g": set("qg"),
    "u_or_v": set("uv"),
    "i_or_j": set("ij"),
    "c_or_cedilla": set("cç"),
    "n_or_m": set("nm"),
    "period_or_comma": set(".,"),
}
TILDE_CHARS = set("ãẽĩõũ")
MARKED_VOWELS = set("àáãèêëẽìíĩòóôõǒùúûũǐǔ")


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def edit_alignment(reference: str, hypothesis: str) -> list[tuple[str, str]]:
    """Return a deterministic minimum-edit alignment with empty gaps."""
    rows = len(reference) + 1
    columns = len(hypothesis) + 1
    costs = [[0] * columns for _ in range(rows)]
    steps = [[""] * columns for _ in range(rows)]
    for row in range(1, rows):
        costs[row][0] = row
        steps[row][0] = "delete"
    for column in range(1, columns):
        costs[0][column] = column
        steps[0][column] = "insert"
    for row in range(1, rows):
        for column in range(1, columns):
            equal = reference[row - 1] == hypothesis[column - 1]
            choices = [
                (costs[row - 1][column - 1] + (not equal), "equal" if equal else "substitute"),
                (costs[row - 1][column] + 1, "delete"),
                (costs[row][column - 1] + 1, "insert"),
            ]
            costs[row][column], steps[row][column] = min(
                choices, key=lambda item: (item[0], {"equal": 0, "substitute": 1, "delete": 2, "insert": 3}[item[1]])
            )
    aligned: list[tuple[str, str]] = []
    row, column = len(reference), len(hypothesis)
    while row or column:
        step = steps[row][column]
        if step in {"equal", "substitute"}:
            aligned.append((reference[row - 1], hypothesis[column - 1]))
            row -= 1
            column -= 1
        elif step == "delete":
            aligned.append((reference[row - 1], ""))
            row -= 1
        else:
            aligned.append(("", hypothesis[column - 1]))
            column -= 1
    return list(reversed(aligned))


def base_character(character: str) -> str:
    if not character:
        return ""
    return "".join(
        item for item in unicodedata.normalize("NFD", character)
        if not unicodedata.combining(item)
    )


def evaluate(references: list[dict], predictions: list[dict]) -> dict:
    reference_by_id = {record["id"]: record for record in references}
    prediction_by_id = {record["id"]: record for record in predictions}
    missing = sorted(set(reference_by_id) - set(prediction_by_id))
    extra = sorted(set(prediction_by_id) - set(reference_by_id))
    if missing or extra:
        raise ValueError(
            f"prediction ID mismatch: {len(missing)} missing, {len(extra)} extra"
        )

    errors = 0
    characters = 0
    exact_lines = 0
    catastrophic = 0
    line_cers: list[float] = []
    substitutions: Counter[tuple[str, str]] = Counter()
    feature_counts = {
        name: Counter(reference=0, exact=0, other_member=0, missing_or_other=0)
        for name in PAIR_GROUPS
    }
    feature_counts["marked_vowel"] = Counter(
        reference=0, exact=0, same_base_wrong_mark=0, missing_or_other=0
    )
    feature_counts["tilde_vowel"] = Counter(
        reference=0, exact=0, same_base_wrong_mark=0, missing_or_other=0
    )
    terminal_hyphen = Counter(
        reference_positive=0, true_positive=0, false_negative=0,
        reference_negative=0, true_negative=0, false_positive=0,
    )

    for identifier, reference_record in reference_by_id.items():
        reference = unicodedata.normalize("NFC", reference_record["text"])
        prediction_record = prediction_by_id[identifier]
        hypothesis = unicodedata.normalize(
            "NFC", prediction_record.get("text", prediction_record.get("hypothesis", ""))
        )
        alignment = edit_alignment(reference, hypothesis)
        distance = sum(left != right for left, right in alignment)
        errors += distance
        characters += len(reference)
        exact_lines += reference == hypothesis
        line_cer = distance / max(1, len(reference))
        line_cers.append(line_cer)
        catastrophic += line_cer > 0.5

        reference_hyphen = reference.endswith("-")
        hypothesis_hyphen = hypothesis.endswith("-")
        if reference_hyphen:
            terminal_hyphen["reference_positive"] += 1
            terminal_hyphen["true_positive" if hypothesis_hyphen else "false_negative"] += 1
        else:
            terminal_hyphen["reference_negative"] += 1
            terminal_hyphen["false_positive" if hypothesis_hyphen else "true_negative"] += 1

        for left, right in alignment:
            if left and right and left != right:
                substitutions[(left, right)] += 1
            if not left:
                continue
            for name, members in PAIR_GROUPS.items():
                if left in members:
                    counts = feature_counts[name]
                    counts["reference"] += 1
                    if right == left:
                        counts["exact"] += 1
                    elif right in members:
                        counts["other_member"] += 1
                    else:
                        counts["missing_or_other"] += 1
            for name, members in (
                ("marked_vowel", MARKED_VOWELS),
                ("tilde_vowel", TILDE_CHARS),
            ):
                if left in members:
                    counts = feature_counts[name]
                    counts["reference"] += 1
                    if right == left:
                        counts["exact"] += 1
                    elif right and base_character(right) == base_character(left):
                        counts["same_base_wrong_mark"] += 1
                    else:
                        counts["missing_or_other"] += 1

    return {
        "lines": len(references),
        "characters": characters,
        "character_errors": errors,
        "character_error_rate": errors / max(1, characters),
        "exact_lines": exact_lines,
        "exact_line_rate": exact_lines / max(1, len(references)),
        "median_line_character_error_rate": statistics.median(line_cers),
        "catastrophic_lines_over_50_percent_cer": catastrophic,
        "terminal_hyphen": dict(terminal_hyphen),
        "features": {name: dict(counts) for name, counts in feature_counts.items()},
        "common_substitutions": [
            {"reference": left, "hypothesis": right, "count": count}
            for (left, right), count in substitutions.most_common(40)
        ],
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--references", type=Path, required=True)
    result.add_argument("--predictions", type=Path, required=True)
    result.add_argument("--split", choices=("train", "dev", "test"), required=True)
    result.add_argument("--output", type=Path)
    return result


if __name__ == "__main__":
    args = parser().parse_args()
    references = [
        record for record in load_jsonl(args.references)
        if record["split"] == args.split
    ]
    result = evaluate(references, load_jsonl(args.predictions))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
