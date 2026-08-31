#!/usr/bin/env python3
"""Page-level cross-validation for the Nippo Jisho ô/ǒ N-gram model."""

from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = ROOT / "scripts" / "evaluate_o_mark_ngram.py"


def load_evaluator():
    spec = importlib.util.spec_from_file_location("evaluate_o_mark_ngram", EVALUATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--page-start", type=int, default=13)
    result.add_argument("--page-end", type=int, default=151)
    result.add_argument("--folds", type=int, default=10)
    result.add_argument("--seed", type=int, default=1603)
    result.add_argument("--orders", type=int, nargs="+", default=[2, 3, 4, 5])
    result.add_argument("--lmplz", type=Path, required=True)
    result.add_argument(
        "--include-errors",
        action="store_true",
        help="Include every erroneous occurrence in the tracked JSON.",
    )
    result.add_argument(
        "--work-dir", type=Path, default=ROOT / ".cache" / "o-mark-ngram-cv"
    )
    result.add_argument("--output", type=Path)
    return result


def make_folds(pages: list[int], count: int, seed: int) -> list[list[int]]:
    shuffled = list(pages)
    random.Random(seed).shuffle(shuffled)
    return [sorted(shuffled[index::count]) for index in range(count)]


def aggregate_summaries(summaries: list[dict]) -> dict:
    occurrences = sum(item["occurrences"] for item in summaries)
    correct = sum(item["correct"] for item in summaries)
    confusion = Counter()
    for item in summaries:
        confusion.update(item["confusion"])
    by_seen = {}
    for key in ("seen", "unseen"):
        subset_occurrences = sum(
            item["by_word_signature"][key]["occurrences"] for item in summaries
        )
        subset_correct = sum(
            item["by_word_signature"][key]["correct"] for item in summaries
        )
        by_seen[key] = {
            "occurrences": subset_occurrences,
            "correct": subset_correct,
            "accuracy": (
                subset_correct / subset_occurrences if subset_occurrences else None
            ),
        }
    return {
        "occurrences": occurrences,
        "correct": correct,
        "accuracy": correct / occurrences if occurrences else None,
        "confusion": dict(sorted(confusion.items())),
        "by_word_signature": by_seen,
    }


def main() -> int:
    args = parser().parse_args()
    evaluator = load_evaluator()
    kenlm = evaluator.load_kenlm()
    pages = list(range(args.page_start, args.page_end + 1))
    folds = make_folds(pages, args.folds, args.seed)
    page_runs = {page: evaluator.roman_runs(page) for page in pages}
    fold_results = []
    model_summaries = {order: [] for order in args.orders}
    model_records = {order: [] for order in args.orders}
    majority_correct = 0
    majority_occurrences = 0
    signature_summaries = []

    for fold_number, test_pages in enumerate(folds, start=1):
        test_set = set(test_pages)
        train_runs = [
            run for page in pages if page not in test_set for run in page_runs[page]
        ]
        test_runs = [run for page in test_pages for run in page_runs[page]]
        signatures = evaluator.marked_signatures(train_runs)
        signature_counts = evaluator.signature_counts(train_runs)
        train_marks = Counter(
            token
            for run in train_runs
            for token in run["tokens"]
            if token in evaluator.MARKS
        )
        test_marks = Counter(
            token
            for run in test_runs
            for token in run["tokens"]
            if token in evaluator.MARKS
        )
        majority = max(evaluator.MARKS, key=lambda mark: train_marks[mark])
        majority_correct += test_marks[majority]
        majority_occurrences += sum(test_marks.values())
        signature_summary = evaluator.signature_baseline(
            test_runs, signature_counts, majority
        )
        signature_summaries.append(signature_summary)
        fold_result = {
            "fold": fold_number,
            "test_pages": test_pages,
            "test_occurrences": sum(test_marks.values()),
            "test_marked_o_counts": dict(test_marks),
            "orders": [],
        }
        fold_dir = args.work_dir / f"fold-{fold_number:02d}"
        corpus = fold_dir / "roman-character-corpus.txt"
        evaluator.write_corpus(corpus, train_runs)
        for order in args.orders:
            arpa = fold_dir / f"roman-char-{order}gram.arpa"
            evaluator.train_arpa(args.lmplz, corpus, arpa, order)
            model = kenlm.Model(str(arpa))
            evaluation = evaluator.evaluate_order(model, kenlm, test_runs, signatures)
            summary = evaluation["forced_site"]
            model_summaries[order].append(summary)
            model_records[order].extend(evaluation["occurrences"])
            fold_result["orders"].append(
                {
                    "order": order,
                    "forced_site": summary,
                    "confidence_curve": evaluation["confidence_curve"],
                }
            )
        fold_results.append(fold_result)

    orders = []
    for order in args.orders:
        summary = aggregate_summaries(model_summaries[order])
        records = model_records[order]
        order_result = {
            "order": order,
            "forced_site": summary,
            "confidence_curve": evaluator.confidence_curve(records),
            "error_count": sum(
                record["prediction"] != record["truth"] for record in records
            ),
        }
        if args.include_errors:
            order_result["errors"] = [
                record
                for record in records
                if record["prediction"] != record["truth"]
            ]
        orders.append(order_result)
    result = {
        "format": "nippo-o-mark-page-cross-validation",
        "format_version": 1,
        "assumption": "The visual system has located a marked o; choose only circumflex ô versus caron ǒ.",
        "page_start": args.page_start,
        "page_end": args.page_end,
        "page_count": len(pages),
        "fold_count": args.folds,
        "seed": args.seed,
        "split_unit": "physical page",
        "training_majority_baseline": {
            "occurrences": majority_occurrences,
            "correct": majority_correct,
            "accuracy": majority_correct / majority_occurrences,
        },
        "word_signature_baseline": aggregate_summaries(signature_summaries),
        "orders": orders,
        "selected_order": max(
            orders, key=lambda item: item["forced_site"]["accuracy"]
        )["order"],
        "folds": fold_results,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
