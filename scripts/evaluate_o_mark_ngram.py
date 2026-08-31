#!/usr/bin/env python3
"""Train and evaluate character N-grams for Nippo Jisho ô/ǒ choices.

The experiment deliberately assumes that another visual stage has already
located a marked ``o``.  It asks only whether a character language model can
choose circumflex ``ô`` or caron ``ǒ`` from the surrounding Roman text.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics
import subprocess
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
LEVEL1 = ROOT / "pilot" / "format-v1-trial" / "level1"
MARKS = ("ô", "ǒ")
SPACE_TOKEN = "▁"


def load_page(page_number: int) -> dict:
    path = LEVEL1 / f"bnf-f{page_number:04d}.json"
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def normalized_run(text: str) -> str:
    return unicodedata.normalize("NFC", " ".join(text.split()))


def roman_runs(page_number: int) -> list[dict]:
    page = load_page(page_number)
    result = []
    for zone in page["zones"]:
        if zone.get("kind") != "column":
            continue
        for line in zone["lines"]:
            for run_index, run in enumerate(line["runs"]):
                if run["typeface"] != "roman":
                    continue
                text = normalized_run(run["text"])
                if not text:
                    continue
                result.append(
                    {
                        "page_id": page["id"],
                        "line_id": line["id"],
                        "run_index": run_index,
                        "text": text,
                        "tokens": encode_text(text),
                    }
                )
    return result


def encode_text(text: str) -> list[str]:
    tokens = []
    in_space = False
    for character in unicodedata.normalize("NFC", text):
        if character.isspace():
            if not in_space:
                tokens.append(SPACE_TOKEN)
            in_space = True
        else:
            tokens.append(character)
            in_space = False
    return tokens


def word_at(tokens: list[str], index: int) -> tuple[str, str]:
    left = index
    while left and tokens[left - 1].isalpha():
        left -= 1
    right = index + 1
    while right < len(tokens) and tokens[right].isalpha():
        right += 1
    word = "".join(tokens[left:right])
    signature = word.replace("ô", "O").replace("ǒ", "O")
    return word, signature


def write_corpus(path: Path, runs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for run in runs:
            stream.write(" ".join(run["tokens"]) + "\n")


def train_arpa(lmplz: Path, corpus: Path, arpa: Path, order: int) -> None:
    arpa.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(lmplz),
        "--order",
        str(order),
        "--text",
        str(corpus),
        "--arpa",
        str(arpa),
        "--discount_fallback",
    ]
    subprocess.run(command, check=True)


def load_kenlm():
    try:
        import kenlm
    except ImportError as exc:
        raise SystemExit(
            "The kenlm Python binding is required. Run this script with the "
            "project's isolated KenLM environment or another compatible Python."
        ) from exc
    return kenlm


def decode_lattice(model, kenlm, lattice: list[list[str]]) -> tuple[float, list[str]]:
    initial = kenlm.State()
    model.BeginSentenceWrite(initial)
    chart = {initial: (0.0, [])}
    for alternatives in lattice:
        next_chart = {}
        for state, (score, path) in chart.items():
            for token in alternatives:
                new_state = kenlm.State()
                new_score = score + model.BaseScore(state, token, new_state)
                current = next_chart.get(new_state)
                if current is None or new_score > current[0]:
                    next_chart[new_state] = (new_score, path + [token])
        chart = next_chart
    best_score = -math.inf
    best_path = []
    for state, (score, path) in chart.items():
        final_state = kenlm.State()
        final_score = score + model.BaseScore(state, "</s>", final_state)
        if final_score > best_score:
            best_score = final_score
            best_path = path
    return best_score, best_path


def lattice_for(tokens: list[str], forced: dict[int, str] | None = None) -> list[list[str]]:
    forced = forced or {}
    return [
        [forced[index]]
        if index in forced
        else list(MARKS)
        if token in MARKS
        else [token]
        for index, token in enumerate(tokens)
    ]


def marked_signatures(runs: list[dict]) -> set[str]:
    result = set()
    for run in runs:
        for index, token in enumerate(run["tokens"]):
            if token in MARKS:
                result.add(word_at(run["tokens"], index)[1])
    return result


def signature_counts(runs: list[dict]) -> dict[str, Counter]:
    result = {}
    for run in runs:
        for index, token in enumerate(run["tokens"]):
            if token not in MARKS:
                continue
            signature = word_at(run["tokens"], index)[1]
            result.setdefault(signature, Counter())[token] += 1
    return result


def signature_baseline(
    runs: list[dict], counts: dict[str, Counter], fallback: str
) -> dict:
    records = []
    for run in runs:
        for index, truth in enumerate(run["tokens"]):
            if truth not in MARKS:
                continue
            word, signature = word_at(run["tokens"], index)
            prediction = (
                counts[signature].most_common(1)[0][0]
                if signature in counts
                else fallback
            )
            records.append(
                {
                    "word": word,
                    "word_signature": signature,
                    "seen_word": signature in counts,
                    "truth": truth,
                    "prediction": prediction,
                }
            )
    return summarize_accuracy(records, "prediction")


def confidence_curve(
    records: list[dict], thresholds=(0.0, 0.2, 0.3, 0.6, 1.0)
) -> list[dict]:
    result = []
    for threshold in thresholds:
        retained = [
            record
            for record in records
            if abs(record["score_circumflex"] - record["score_caron"])
            >= threshold
        ]
        correct = sum(record["prediction"] == record["truth"] for record in retained)
        result.append(
            {
                "minimum_absolute_margin_log10": threshold,
                "retained": len(retained),
                "coverage": len(retained) / len(records) if records else None,
                "correct": correct,
                "accuracy": correct / len(retained) if retained else None,
            }
        )
    return result


def summarize_accuracy(records: list[dict], prediction_key: str) -> dict:
    correct = sum(record[prediction_key] == record["truth"] for record in records)
    confusion = Counter(
        f"{record['truth']}->{record[prediction_key]}" for record in records
    )
    by_seen = {}
    for seen in (True, False):
        subset = [record for record in records if record["seen_word"] is seen]
        subset_correct = sum(
            record[prediction_key] == record["truth"] for record in subset
        )
        by_seen["seen" if seen else "unseen"] = {
            "occurrences": len(subset),
            "correct": subset_correct,
            "accuracy": subset_correct / len(subset) if subset else None,
        }
    return {
        "occurrences": len(records),
        "correct": correct,
        "accuracy": correct / len(records) if records else None,
        "confusion": dict(sorted(confusion.items())),
        "by_word_signature": by_seen,
    }


def evaluate_order(model, kenlm, runs: list[dict], signatures: set[str]) -> dict:
    records = []
    joint_predictions = {}
    for run_number, run in enumerate(runs):
        target_indices = [
            index for index, token in enumerate(run["tokens"]) if token in MARKS
        ]
        if not target_indices:
            continue
        _, joint_path = decode_lattice(model, kenlm, lattice_for(run["tokens"]))
        for index in target_indices:
            joint_predictions[(run_number, index)] = joint_path[index]
            scores = {}
            for candidate in MARKS:
                scores[candidate], _ = decode_lattice(
                    model,
                    kenlm,
                    lattice_for(run["tokens"], {index: candidate}),
                )
            predicted = max(MARKS, key=lambda candidate: scores[candidate])
            truth = run["tokens"][index]
            word, signature = word_at(run["tokens"], index)
            records.append(
                {
                    "page_id": run["page_id"],
                    "line_id": run["line_id"],
                    "run_index": run["run_index"],
                    "token_index": index,
                    "word": word,
                    "word_signature": signature,
                    "seen_word": signature in signatures,
                    "truth": truth,
                    "prediction": predicted,
                    "joint_prediction": joint_path[index],
                    "score_circumflex": scores["ô"],
                    "score_caron": scores["ǒ"],
                    "correct_margin": scores[truth] - scores[
                        "ǒ" if truth == "ô" else "ô"
                    ],
                    "text": run["text"],
                }
            )
    margins = [record["correct_margin"] for record in records]
    return {
        "forced_site": summarize_accuracy(records, "prediction"),
        "joint_decode": summarize_accuracy(records, "joint_prediction"),
        "confidence_curve": confidence_curve(records),
        "margin_log10": {
            "minimum": min(margins) if margins else None,
            "median": statistics.median(margins) if margins else None,
            "maximum": max(margins) if margins else None,
        },
        "occurrences": records,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--train-start", type=int, default=13)
    result.add_argument("--train-end", type=int, default=150)
    result.add_argument("--test-page", type=int, default=151)
    result.add_argument("--orders", type=int, nargs="+", default=[2, 3, 4, 5])
    result.add_argument("--lmplz", type=Path, required=True)
    result.add_argument(
        "--work-dir", type=Path, default=ROOT / ".cache" / "o-mark-ngram"
    )
    result.add_argument("--output", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.test_page in range(args.train_start, args.train_end + 1):
        raise SystemExit("test page must be held out from the training range")
    kenlm = load_kenlm()
    train_runs = [
        run
        for page_number in range(args.train_start, args.train_end + 1)
        for run in roman_runs(page_number)
    ]
    test_runs = roman_runs(args.test_page)
    signatures = marked_signatures(train_runs)
    signatures_by_mark = signature_counts(train_runs)
    corpus = args.work_dir / "roman-character-corpus.txt"
    write_corpus(corpus, train_runs)
    train_marks = Counter(
        token
        for run in train_runs
        for token in run["tokens"]
        if token in MARKS
    )
    test_marks = Counter(
        token
        for run in test_runs
        for token in run["tokens"]
        if token in MARKS
    )
    majority = max(MARKS, key=lambda mark: train_marks[mark])
    result = {
        "format": "nippo-o-mark-character-ngram-evaluation",
        "format_version": 1,
        "assumption": "The visual system has located a marked o; choose only circumflex ô versus caron ǒ.",
        "training": {
            "page_start": args.train_start,
            "page_end": args.train_end,
            "test_page_excluded": args.test_page,
            "typeface": "roman",
            "runs": len(train_runs),
            "character_tokens": sum(len(run["tokens"]) for run in train_runs),
            "marked_o_counts": dict(train_marks),
            "marked_word_signatures": len(signatures),
        },
        "test": {
            "page": args.test_page,
            "runs": len(test_runs),
            "marked_o_counts": dict(test_marks),
            "occurrences": sum(test_marks.values()),
        },
        "training_majority_baseline": {
            "prediction": majority,
            "correct": test_marks[majority],
            "accuracy": test_marks[majority] / sum(test_marks.values()),
        },
        "word_signature_baseline": signature_baseline(
            test_runs, signatures_by_mark, majority
        ),
        "orders": [],
    }
    for order in args.orders:
        arpa = args.work_dir / f"roman-char-{order}gram.arpa"
        train_arpa(args.lmplz, corpus, arpa, order)
        model = kenlm.Model(str(arpa))
        evaluation = evaluate_order(model, kenlm, test_runs, signatures)
        result["orders"].append({"order": order, **evaluation})
    result["selected_order"] = max(
        result["orders"], key=lambda item: item["forced_site"]["accuracy"]
    )["order"]
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
