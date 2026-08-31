#!/usr/bin/env python3
"""Evaluate OCR and N-gram fusion for Nippo Jisho ô/ǒ choices.

The OCR checkpoint's original development pages calibrate the fusion model;
its untouched test pages provide the final evaluation.  The N-gram model is
retrained with the pages being scored excluded.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.util
import json
import math
from pathlib import Path
import random
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
LEVEL1 = ROOT / "pilot" / "format-v1-trial" / "level1"
ABLATION = ROOT / ".cache" / "ocr-model" / "training-ablation-v2"
CORE_CHECKPOINT = ROOT / ".cache" / "ocr-model" / "runs" / "trocr-isolated-core-v1" / "best"
FULL_CHECKPOINT = ROOT / ".cache" / "ocr-model" / "runs" / "trocr-isolated-full-v1" / "best"
MARKS = ("ô", "ǒ")
OCR_FEATURES = (
    "ocr_delta",
    "ocr_visual_residual_delta",
    "ocr_native96_delta",
    "ocr_native96_visual_residual_delta",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def occurrence_id(record: dict) -> str:
    return (
        f"{record['page_id']}/{record['line_id']}/"
        f"r{record['run_index']}/t{record['token_index']}"
    )


def page_targets(page_number: int, evaluator) -> list[dict]:
    page = evaluator.load_page(page_number)
    lines = {
        line["id"]: line
        for zone in page["zones"]
        if zone.get("kind") == "column"
        for line in zone["lines"]
    }
    result = []
    for run in evaluator.roman_runs(page_number):
        line = lines[run["line_id"]]
        preceding_runs = line["runs"][: run["run_index"]]
        preceding_marks = sum(
            character in MARKS
            for item in preceding_runs
            for character in unicodedata.normalize("NFC", item["text"])
        )
        line_text = unicodedata.normalize(
            "NFC", "".join(item["text"] for item in line["runs"]).strip()
        )
        for token_index, truth in enumerate(run["tokens"]):
            if truth not in MARKS:
                continue
            within_run = sum(token in MARKS for token in run["tokens"][:token_index])
            word, signature = evaluator.word_at(run["tokens"], token_index)
            target = {
                "page_id": run["page_id"],
                "line_id": run["line_id"],
                "run_index": run["run_index"],
                "token_index": token_index,
                "global_mark_ordinal": preceding_marks + within_run,
                "truth": truth,
                "word": word,
                "word_signature": signature,
                "line_text": line_text,
            }
            target["id"] = occurrence_id(target)
            result.append(target)
    return result


def alignment_map(reference: str, hypothesis: str) -> list[str | None]:
    """Map each reference character to an aligned hypothesis character."""
    rows = len(reference) + 1
    columns = len(hypothesis) + 1
    costs = [[0] * columns for _ in range(rows)]
    moves = [[""] * columns for _ in range(rows)]
    for row in range(1, rows):
        costs[row][0] = row
        moves[row][0] = "delete"
    for column in range(1, columns):
        costs[0][column] = column
        moves[0][column] = "insert"
    for row in range(1, rows):
        for column in range(1, columns):
            choices = [
                (
                    costs[row - 1][column - 1]
                    + (reference[row - 1] != hypothesis[column - 1]),
                    "align",
                ),
                (costs[row - 1][column] + 1, "delete"),
                (costs[row][column - 1] + 1, "insert"),
            ]
            costs[row][column], moves[row][column] = min(
                choices, key=lambda item: (item[0], item[1] != "align")
            )
    mapping: list[str | None] = [None] * len(reference)
    row = len(reference)
    column = len(hypothesis)
    while row or column:
        move = moves[row][column]
        if move == "align":
            mapping[row - 1] = hypothesis[column - 1]
            row -= 1
            column -= 1
        elif move == "delete":
            row -= 1
        else:
            column -= 1
    return mapping


def line_edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for row, left_character in enumerate(left, start=1):
        current = [row]
        for column, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def score_ocr_split(
    split: str,
    evaluator,
    *,
    batch_size: int,
    device_name: str,
) -> list[dict]:
    from PIL import Image
    import torch
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    training = load_module("train_nippo_trocr", ROOT / "scripts" / "train_nippo_trocr.py")
    dataset_builder = load_module("build_ocr_dataset", ROOT / "scripts" / "build_ocr_dataset.py")
    manifest_root = ABLATION / "core"
    manifest = load_jsonl(manifest_root / f"{split}.jsonl")
    records_by_id = {record["id"]: record for record in manifest}
    pages = sorted({int(record["page_id"].removeprefix("bnf-f")) for record in manifest})
    targets = [target for page in pages for target in page_targets(page, evaluator)]
    targets_by_line: dict[str, list[dict]] = defaultdict(list)
    missing = []
    for target in targets:
        line_id = f"{target['page_id']}/{target['line_id']}"
        if line_id in records_by_id:
            targets_by_line[line_id].append(target)
        else:
            missing.append(target)

    processor = TrOCRProcessor.from_pretrained(CORE_CHECKPOINT, use_fast=False)
    tokenizer = processor.tokenizer
    candidate_ids = {}
    for mark in MARKS:
        ids = tokenizer(training.encode_text(mark), add_special_tokens=False).input_ids
        # A standalone character receives SentencePiece's separate word-boundary
        # token, while the same mark inside a word remains the final token.
        if not ids or tokenizer.decode([ids[-1]]) != mark:
            raise RuntimeError(f"{mark!r} no longer has a distinct OCR token: {ids}")
        candidate_ids[mark] = ids[-1]
    device = training.device_for(device_name)
    output = []

    for route, checkpoint in (("core", CORE_CHECKPOINT), ("full", FULL_CHECKPOINT)):
        line_records = []
        for identifier in sorted(targets_by_line):
            record = records_by_id[identifier]
            expected_route = (
                "full" if record.get("quality_tier") == "positionally-anchored" else "core"
            )
            if expected_route == route:
                line_records.append(record)
        if not line_records:
            continue
        model = VisionEncoderDecoderModel.from_pretrained(checkpoint)
        model.encoder.config._attn_implementation = "eager"
        model.decoder.config._attn_implementation = "eager"
        model.to(device).eval()
        with torch.inference_mode():
            for start in range(0, len(line_records), batch_size):
                batch = line_records[start : start + batch_size]
                images = []
                native_images = []
                texts = []
                for record in batch:
                    with Image.open(manifest_root / record["image"]) as source:
                        images.append(source.convert("RGB"))
                    scan_path = (
                        ROOT
                        / "build"
                        / "nippo-jisho-images"
                        / "scans"
                        / "native"
                        / f"f{int(record['page_id'].removeprefix('bnf-f')):04d}.jpg"
                    )
                    with Image.open(scan_path) as scan:
                        native_images.append(
                            dataset_builder.prepare_crop(
                                scan,
                                record["source_crop"],
                                height=96,
                                max_width=2048,
                            ).convert("RGB")
                        )
                    texts.append(targets_by_line[record["id"]][0]["line_text"])
                pixels = processor(images=images, return_tensors="pt").pixel_values.to(device)
                native_pixels = processor(
                    images=native_images, return_tensors="pt"
                ).pixel_values.to(device)
                blank_pixels = processor(
                    images=[Image.new("RGB", image.size, "white") for image in images],
                    return_tensors="pt",
                ).pixel_values.to(device)
                encoded = tokenizer(
                    [training.encode_text(text) for text in texts],
                    padding=True,
                    return_tensors="pt",
                )
                labels = encoded.input_ids.to(device)
                decoder_inputs = model.prepare_decoder_input_ids_from_labels(labels)
                attention_mask = decoder_inputs.ne(tokenizer.pad_token_id).long()

                def candidate_deltas(batch_pixels):
                    result = model(
                        pixel_values=batch_pixels,
                        decoder_input_ids=decoder_inputs,
                        decoder_attention_mask=attention_mask,
                    )
                    selected = result.logits[
                        :, :, [candidate_ids["ô"], candidate_ids["ǒ"]]
                    ]
                    return (selected[:, :, 0] - selected[:, :, 1]).cpu()

                actual_deltas = candidate_deltas(pixels)
                native_deltas = candidate_deltas(native_pixels)
                blank_deltas = candidate_deltas(blank_pixels)
                generated = model.generate(pixels, max_length=96, num_beams=1)
                decoded = processor.batch_decode(
                    generated,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )
                for batch_index, (record, text, raw_hypothesis) in enumerate(
                    zip(batch, texts, decoded)
                ):
                    hypothesis = training.decode_text(raw_hypothesis)
                    mapping = alignment_map(text, hypothesis)
                    character_mark_positions = [
                        index for index, character in enumerate(text) if character in MARKS
                    ]
                    token_ids = encoded.input_ids[batch_index].tolist()
                    token_mark_positions = [
                        index
                        for index, token_id in enumerate(token_ids)
                        if token_id in candidate_ids.values()
                    ]
                    if len(character_mark_positions) != len(token_mark_positions):
                        raise RuntimeError(
                            f"{record['id']}: {len(character_mark_positions)} marked characters "
                            f"but {len(token_mark_positions)} marked OCR tokens"
                        )
                    for target in targets_by_line[record["id"]]:
                        ordinal = target["global_mark_ordinal"]
                        token_position = token_mark_positions[ordinal]
                        character_position = character_mark_positions[ordinal]
                        ocr_delta = float(actual_deltas[batch_index, token_position])
                        native_delta = float(native_deltas[batch_index, token_position])
                        blank_delta = float(blank_deltas[batch_index, token_position])
                        scored = {
                            key: value for key, value in target.items() if key != "line_text"
                        }
                        scored.update(
                            {
                                "split": split,
                                "quality_tier": record.get("quality_tier"),
                                "ocr_route": route,
                                "ocr_delta": ocr_delta,
                                "ocr_blank_delta": blank_delta,
                                "ocr_visual_residual_delta": ocr_delta - blank_delta,
                                "ocr_native96_delta": native_delta,
                                "ocr_native96_visual_residual_delta": native_delta
                                - blank_delta,
                                "decoded_character": mapping[character_position],
                                "decoded_choice": (
                                    mapping[character_position]
                                    if mapping[character_position] in MARKS
                                    else None
                                ),
                                "line_cer": line_edit_distance(text, hypothesis)
                                / max(1, len(text)),
                            }
                        )
                        output.append(scored)
        del model
        if device.type == "mps":
            torch.mps.empty_cache()
    output.append(
        {
            "_coverage": {
                "split": split,
                "canonical_occurrences": len(targets),
                "scored_occurrences": len(output),
                "missing_occurrences": len(missing),
                "missing_ids": [target["id"] for target in missing],
            }
        }
    )
    return output


def load_or_score_ocr(args, evaluator) -> dict:
    if args.score_cache.exists() and not args.refresh_ocr:
        return json.loads(args.score_cache.read_text(encoding="utf-8"))
    value = {
        "format": "nippo-o-mark-ocr-scores",
        "format_version": 1,
        "development": score_ocr_split(
            "dev", evaluator, batch_size=args.batch_size, device_name=args.device
        ),
        "test": score_ocr_split(
            "test", evaluator, batch_size=args.batch_size, device_name=args.device
        ),
    }
    args.score_cache.parent.mkdir(parents=True, exist_ok=True)
    args.score_cache.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return value


def ngram_scores(pages: list[int], all_pages: list[int], evaluator, kenlm, args, name: str):
    test_set = set(pages)
    train_runs = [
        run
        for page in all_pages
        if page not in test_set
        for run in evaluator.roman_runs(page)
    ]
    test_runs = [run for page in pages for run in evaluator.roman_runs(page)]
    signatures = evaluator.marked_signatures(train_runs)
    directory = args.work_dir / name
    corpus = directory / "roman-character-corpus.txt"
    arpa = directory / "roman-char-2gram.arpa"
    evaluator.write_corpus(corpus, train_runs)
    evaluator.train_arpa(args.lmplz, corpus, arpa, 2)
    model = kenlm.Model(str(arpa))
    evaluated = evaluator.evaluate_order(model, kenlm, test_runs, signatures)
    result = {}
    for record in evaluated["occurrences"]:
        record = dict(record)
        record["id"] = occurrence_id(record)
        record["ngram_delta"] = record["score_circumflex"] - record["score_caron"]
        result[record["id"]] = record
    return result


def sigmoid(value):
    import numpy as np

    value = np.clip(value, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-value))


def page_weights(records: list[dict]):
    import numpy as np

    counts = Counter(record["page_id"] for record in records)
    weights = np.array([1.0 / counts[record["page_id"]] for record in records])
    return weights * (len(records) / weights.sum())


def feature_matrix(records: list[dict], ocr_feature: str, means=None, scales=None):
    import numpy as np

    raw = np.array(
        [[record[ocr_feature], record["ngram_delta"]] for record in records],
        dtype=float,
    )
    if means is None:
        means = raw.mean(axis=0)
    if scales is None:
        scales = raw.std(axis=0)
        scales[scales == 0] = 1.0
    standardized = (raw - means) / scales
    return np.column_stack([np.ones(len(records)), standardized]), means, scales


def fit_logistic(records: list[dict], regularization: float, ocr_feature: str):
    import numpy as np

    matrix, means, scales = feature_matrix(records, ocr_feature)
    labels = np.array([record["truth"] == "ô" for record in records], dtype=float)
    weights = page_weights(records)
    coefficients = np.zeros(matrix.shape[1])
    penalty = np.diag([0.0] + [regularization] * (matrix.shape[1] - 1))
    for _ in range(100):
        probabilities = sigmoid(matrix @ coefficients)
        gradient = matrix.T @ ((probabilities - labels) * weights) + penalty @ coefficients
        curvature = weights * probabilities * (1.0 - probabilities)
        hessian = matrix.T @ (matrix * curvature[:, None]) + penalty
        step = np.linalg.solve(hessian + np.eye(hessian.shape[0]) * 1e-9, gradient)
        coefficients -= step
        if float(np.max(np.abs(step))) < 1e-9:
            break
    return {
        "coefficients": coefficients,
        "means": means,
        "scales": scales,
        "regularization": regularization,
        "ocr_feature": ocr_feature,
    }


def predict_logistic(model: dict, records: list[dict]):
    matrix, _, _ = feature_matrix(
        records, model["ocr_feature"], model["means"], model["scales"]
    )
    return sigmoid(matrix @ model["coefficients"])


def grouped_oof(records: list[dict], regularization: float, ocr_feature: str):
    import numpy as np

    probabilities = np.zeros(len(records))
    pages = sorted({record["page_id"] for record in records})
    for page in pages:
        train = [record for record in records if record["page_id"] != page]
        test_indices = [
            index for index, record in enumerate(records) if record["page_id"] == page
        ]
        model = fit_logistic(train, regularization, ocr_feature)
        probabilities[test_indices] = predict_logistic(
            model, [records[index] for index in test_indices]
        )
    return probabilities


def log_loss(records: list[dict], probabilities) -> float:
    import numpy as np

    labels = np.array([record["truth"] == "ô" for record in records], dtype=float)
    clipped = np.clip(probabilities, 1e-9, 1.0 - 1e-9)
    weights = page_weights(records)
    return float(
        np.sum(weights * -(labels * np.log(clipped) + (1 - labels) * np.log(1 - clipped)))
        / np.sum(weights)
    )


def prediction_summary(records: list[dict], predictions: list[str | None]) -> dict:
    eligible = [
        (record, prediction)
        for record, prediction in zip(records, predictions)
        if prediction in MARKS
    ]
    correct = sum(record["truth"] == prediction for record, prediction in eligible)
    confusion = Counter(
        f"{record['truth']}->{prediction}" for record, prediction in eligible
    )
    page_scores = []
    for page in sorted({record["page_id"] for record, _ in eligible}):
        page_items = [item for item in eligible if item[0]["page_id"] == page]
        page_scores.append(
            sum(record["truth"] == prediction for record, prediction in page_items)
            / len(page_items)
        )
    return {
        "total_occurrences": len(records),
        "retained": len(eligible),
        "coverage": len(eligible) / len(records) if records else None,
        "correct": correct,
        "accuracy": correct / len(eligible) if eligible else None,
        "macro_page_accuracy": sum(page_scores) / len(page_scores) if page_scores else None,
        "confusion": dict(sorted(confusion.items())),
    }


def choose_threshold(records: list[dict], probabilities, target_precision: float):
    confidences = [max(float(value), 1.0 - float(value)) for value in probabilities]
    candidates = sorted(set(confidences))
    best = None
    for threshold in candidates:
        predictions = [
            ("ô" if probability >= 0.5 else "ǒ")
            if confidence >= threshold
            else None
            for probability, confidence in zip(probabilities, confidences)
        ]
        summary = prediction_summary(records, predictions)
        if summary["retained"] < 10 or summary["accuracy"] < target_precision:
            continue
        if best is None or summary["retained"] > best["development"]["retained"]:
            best = {"threshold": threshold, "development": summary}
    return best


def combine_records(ocr_scores: list[dict], ngram: dict) -> tuple[list[dict], dict]:
    coverage = next(item["_coverage"] for item in ocr_scores if "_coverage" in item)
    records = []
    for item in ocr_scores:
        if "_coverage" in item:
            continue
        if item["id"] not in ngram:
            continue
        combined = dict(item)
        combined.update(
            {
                "ngram_delta": ngram[item["id"]]["ngram_delta"],
                "seen_word": ngram[item["id"]]["seen_word"],
            }
        )
        records.append(combined)
    return records, coverage


def evaluate_methods(records: list[dict], probabilities, ocr_feature: str) -> dict:
    ngram_predictions = ["ô" if record["ngram_delta"] >= 0 else "ǒ" for record in records]
    contrast_predictions = [
        "ô" if record[ocr_feature] >= 0 else "ǒ" for record in records
    ]
    decoded_predictions = [record["decoded_choice"] for record in records]
    agreement = [
        ngram if ngram == visual else None
        for ngram, visual in zip(ngram_predictions, contrast_predictions)
    ]
    decoded_agreement = [
        ngram if ngram == decoded else None
        for ngram, decoded in zip(ngram_predictions, decoded_predictions)
    ]
    fused = ["ô" if probability >= 0.5 else "ǒ" for probability in probabilities]
    return {
        "ngram_only": prediction_summary(records, ngram_predictions),
        "selected_ocr_feature": ocr_feature,
        "ocr_feature_only": prediction_summary(records, contrast_predictions),
        "ocr_free_decode": prediction_summary(records, decoded_predictions),
        "ngram_ocr_contrast_agreement": prediction_summary(records, agreement),
        "ngram_free_decode_agreement": prediction_summary(records, decoded_agreement),
        "logistic_fusion": prediction_summary(records, fused),
    }


def evaluate_ocr_features(records: list[dict]) -> dict:
    result = {}
    ngram = ["ô" if record["ngram_delta"] >= 0 else "ǒ" for record in records]
    for feature in OCR_FEATURES:
        visual = ["ô" if record[feature] >= 0 else "ǒ" for record in records]
        agreement = [
            ngram_prediction if ngram_prediction == visual_prediction else None
            for ngram_prediction, visual_prediction in zip(ngram, visual)
        ]
        result[feature] = {
            "feature_only": prediction_summary(records, visual),
            "ngram_agreement": prediction_summary(records, agreement),
        }
    return result


def serializable_model(model: dict) -> dict:
    return {
        "coefficients": model["coefficients"].tolist(),
        "feature_means": model["means"].tolist(),
        "feature_scales": model["scales"].tolist(),
        "regularization": model["regularization"],
        "features": [
            "intercept",
            f"standardized_{model['ocr_feature']}",
            "standardized_ngram_delta",
        ],
    }


def asymmetric_predictions(
    records: list[dict], *, ocr_feature: str, ocr_threshold: float, lm_maximum: float
) -> list[str]:
    predictions = []
    for record in records:
        prediction = "ô" if record["ngram_delta"] >= 0 else "ǒ"
        if (
            prediction == "ô"
            and record["ngram_delta"] <= lm_maximum
            and record[ocr_feature] <= -ocr_threshold
        ):
            prediction = "ǒ"
        predictions.append(prediction)
    return predictions


def asymmetric_rule_summary(records: list[dict], predictions: list[str]) -> dict:
    baseline = ["ô" if record["ngram_delta"] >= 0 else "ǒ" for record in records]
    changed = [
        (record, prediction)
        for record, before, prediction in zip(records, baseline, predictions)
        if before != prediction
    ]
    correct = sum(record["truth"] == prediction for record, prediction in changed)
    summary = prediction_summary(records, predictions)
    summary["overrides"] = len(changed)
    summary["correct_overrides"] = correct
    summary["override_precision"] = correct / len(changed) if changed else None
    summary["net_correct_change_from_ngram"] = summary["correct"] - sum(
        record["truth"] == prediction for record, prediction in zip(records, baseline)
    )
    return summary


def select_asymmetric_rule(records: list[dict]) -> dict:
    candidates = []
    for ocr_feature in OCR_FEATURES:
        for ocr_threshold in (
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            1.75,
            2.0,
            2.25,
            2.5,
            2.75,
            3.0,
        ):
            for lm_maximum in (0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 2.0):
                predictions = asymmetric_predictions(
                    records,
                    ocr_feature=ocr_feature,
                    ocr_threshold=ocr_threshold,
                    lm_maximum=lm_maximum,
                )
                summary = asymmetric_rule_summary(records, predictions)
                candidates.append(
                    {
                        "ocr_feature": ocr_feature,
                        "ocr_threshold": ocr_threshold,
                        "lm_maximum": lm_maximum,
                        "development": summary,
                    }
                )
    return max(
        candidates,
        key=lambda item: (
            item["development"]["correct"],
            item["development"]["macro_page_accuracy"],
            -item["development"]["overrides"],
        ),
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--lmplz", type=Path, required=True)
    result.add_argument(
        "--score-cache",
        type=Path,
        default=ROOT / ".cache" / "o-mark-fusion" / "ocr-scores.json",
    )
    result.add_argument(
        "--work-dir",
        type=Path,
        default=ROOT / ".cache" / "o-mark-fusion" / "ngram",
    )
    result.add_argument("--output", type=Path)
    result.add_argument("--refresh-ocr", action="store_true")
    result.add_argument("--batch-size", type=int, default=8)
    result.add_argument("--device", default="auto")
    return result


def main() -> int:
    args = parser().parse_args()
    evaluator = load_module("evaluate_o_mark_ngram", ROOT / "scripts" / "evaluate_o_mark_ngram.py")
    kenlm = evaluator.load_kenlm()
    ocr = load_or_score_ocr(args, evaluator)
    manifests = {
        split: load_jsonl(ABLATION / "core" / f"{split}.jsonl")
        for split in ("dev", "test")
    }
    pages = {
        split: sorted(
            {int(record["page_id"].removeprefix("bnf-f")) for record in manifest}
        )
        for split, manifest in manifests.items()
    }
    all_pages = list(range(13, 151))
    dev_ngram = ngram_scores(pages["dev"], all_pages, evaluator, kenlm, args, "dev")
    test_ngram = ngram_scores(pages["test"], all_pages, evaluator, kenlm, args, "test")
    development, development_coverage = combine_records(ocr["development"], dev_ngram)
    test, test_coverage = combine_records(ocr["test"], test_ngram)

    regularizations = (0.01, 0.1, 1.0, 10.0)
    selections = []
    for ocr_feature in OCR_FEATURES:
        for regularization in regularizations:
            probabilities = grouped_oof(development, regularization, ocr_feature)
            selections.append(
                {
                    "ocr_feature": ocr_feature,
                    "regularization": regularization,
                    "page_grouped_oof_log_loss": log_loss(
                        development, probabilities
                    ),
                    "probabilities": probabilities,
                }
            )
    selected = min(selections, key=lambda item: item["page_grouped_oof_log_loss"])
    oof_probabilities = selected["probabilities"]
    model = fit_logistic(
        development, selected["regularization"], selected["ocr_feature"]
    )
    test_probabilities = predict_logistic(model, test)
    thresholds = []
    for target_precision in (0.9, 0.95, 0.98):
        chosen = choose_threshold(development, oof_probabilities, target_precision)
        if chosen is None:
            thresholds.append(
                {"target_development_precision": target_precision, "available": False}
            )
            continue
        threshold = chosen["threshold"]
        predictions = [
            ("ô" if probability >= 0.5 else "ǒ")
            if max(float(probability), 1.0 - float(probability)) >= threshold
            else None
            for probability in test_probabilities
        ]
        thresholds.append(
            {
                "target_development_precision": target_precision,
                "available": True,
                **chosen,
                "test": prediction_summary(test, predictions),
            }
        )
    asymmetric = select_asymmetric_rule(development)
    asymmetric_test_predictions = asymmetric_predictions(
        test,
        ocr_feature=asymmetric["ocr_feature"],
        ocr_threshold=asymmetric["ocr_threshold"],
        lm_maximum=asymmetric["lm_maximum"],
    )
    asymmetric["test"] = asymmetric_rule_summary(test, asymmetric_test_predictions)
    result = {
        "format": "nippo-o-mark-ocr-ngram-fusion-evaluation",
        "format_version": 1,
        "task": "Given a visually established marked o, choose circumflex ô versus caron ǒ.",
        "leakage_control": {
            "fusion_calibration": "OCR checkpoint's original 14 development pages",
            "final_evaluation": "OCR checkpoint's original untouched 14 test pages",
            "ngram": "retrained separately with every scored split's physical pages excluded",
            "fusion_regularization": "selected by leave-one-page-out development log loss",
            "thresholds": "selected from leave-one-page-out development predictions",
        },
        "ocr_evidence": {
            "contrast": "teacher-forced logit(ô)-logit(ǒ) at the target token; the target token is not present in decoder input",
            "context_caveat": "the rest of the canonical line supplies the decoder prefix, so this is an oracle-context visual-language score",
            "routing": "core checkpoint except full checkpoint for positionally-anchored lines",
            "variants": [
                "trained 48-pixel line rendering",
                "96-pixel rendering regenerated from the native scan",
                "each rendering minus the same-prefix blank-image decoder preference",
            ],
        },
        "development": {
            "pages": pages["dev"],
            "coverage": development_coverage,
            "combined_occurrences": len(development),
            "ocr_feature_only": evaluate_ocr_features(development),
            "methods_page_grouped_oof": evaluate_methods(
                development, oof_probabilities, selected["ocr_feature"]
            ),
        },
        "test": {
            "pages": pages["test"],
            "coverage": test_coverage,
            "combined_occurrences": len(test),
            "ocr_feature_only": evaluate_ocr_features(test),
            "methods": evaluate_methods(
                test, test_probabilities, selected["ocr_feature"]
            ),
        },
        "fusion_model": serializable_model(model),
        "regularization_selection": [
            {key: value for key, value in item.items() if key != "probabilities"}
            for item in selections
        ],
        "asymmetric_rule": asymmetric,
        "precision_thresholds": thresholds,
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
