"""Learn cedilla typefaces from reviewed scans; write proposals, never page edits.

Run collect, train, then predict with a local experiment directory::

    python3 scripts/train_cedilla_typeface.py collect build/cedilla-typeface-v2
    python3 scripts/train_cedilla_typeface.py train build/cedilla-typeface-v2
    python3 scripts/train_cedilla_typeface.py predict build/cedilla-typeface-v2

All reviewed ç examples, including Portuguese, supply training data. Only
Japanese Tç/tç beyond --reference-through are prediction targets. Current target
typefaces are comparison baselines, NOT training labels. Scores are decision
margins, not calibrated probabilities. Human labels remain authoritative.
Training additionally requires the optional scikit-learn and joblib packages.
"""

from __future__ import annotations

import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_VERSION = "native-2x-corrected-component-hog-lr-v2"
SEED = 72491


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def native_patch(scan: Image.Image, row: dict, index: int) -> Image.Image | None:
    """Extract the old 72×48 field at twice its resolution from the native scan.

    Enlarging an already downsampled OCR crop cannot recover fine typeface detail.
    Coordinates are projected directly through the saved native scan mapping.
    """
    alignment = row["alignment"][index]
    mapping = row["scan_mappings"][index] if row.get("scan_mappings") else row.get("scan_mapping")
    if not alignment or not mapping:
        return None
    px = (alignment["left"] + alignment["width"] / 2) * row["image_width"] / 100
    dx = np.asarray(mapping["dx"], dtype=float)
    u = dx / 2
    v = np.array([-u[1], u[0]])
    centre = np.asarray(mapping["origin"]) + px * dx + 24 * np.asarray(mapping["dy"])
    origin = centre - 56 * u - 48 * v
    grayscale = scan if scan.mode == "L" else scan.convert("L")
    return grayscale.transform(
        (144, 96), Image.Transform.AFFINE,
        (u[0], v[0], origin[0], u[1], v[1], origin[1]),
        Image.Resampling.BICUBIC, fillcolor=255,
    )


def normalize(image: Image.Image | np.ndarray) -> np.ndarray:
    """Convert grayscale scan pixels into locally contrast-normalized ink."""
    a = np.asarray(image.convert("L") if isinstance(image, Image.Image) else image, dtype=float)
    if a.ndim != 2:
        raise ValueError("expected a grayscale image")
    dark, light = np.percentile(a, [12, 85])
    return np.clip((light - a) / max(25, light - dark), 0, 1)


def extract_glyph(a: np.ndarray, *, diagnostics: bool = False):
    """Locate ç, avoiding the old nearest-component rule that often selected u.

    Prefer the taller component (body plus cedilla) slightly left of the OCR
    character centre. Preserve aspect ratio when resizing. A fixed field is the
    fallback for broken or joined ink; diagnostics make that fallback auditable.
    """
    if a.shape != (96, 144):
        raise ValueError(f"expected native-detail 144×96 crop, got {a.shape[::-1]}")
    labels, _ = ndi.label(a > .45, np.ones((3, 3)))
    choices = []
    for k, box in enumerate(ndi.find_objects(labels), 1):
        if box is None:
            continue
        y, x = box
        h, w = y.stop - y.start, x.stop - x.start
        cx = (x.start + x.stop) / 2
        if 26 <= h <= 68 and 10 <= w <= 52 and 12 < cx < 76 and 16 <= y.start < 60:
            choices.append((abs(cx - 48) + abs(y.start - 38) * .5 - h * .8, k, box))
    if not choices:
        result = ndi.zoom(a[16:94, 12:72], (48 / 78, 48 / 60))
        info = {"method": "fixed_field_fallback", "box": [12, 16, 72, 94]}
    else:
        _, _, (y, x) = min(choices)
        ya, yb = max(0, y.start - 3), min(96, y.stop + 4)
        xa, xb = max(0, x.start - 3), min(144, x.stop + 3)
        patch = a[ya:yb, xa:xb]
        scale = min(42 / patch.shape[0], 40 / patch.shape[1])
        patch = ndi.zoom(patch, scale, order=1)
        result = np.zeros((48, 48))
        yy, xx = (48 - patch.shape[0]) // 2, (48 - patch.shape[1]) // 2
        result[yy:yy + patch.shape[0], xx:xx + patch.shape[1]] = patch
        info = {"method": "component", "box": [xa, ya, xb, yb]}
    return (result, info) if diagnostics else result


def hog(a: np.ndarray) -> np.ndarray:
    """Small local gradient histograms; exact feature used in the experiment."""
    dx, dy = ndi.sobel(a, axis=1), ndi.sobel(a, axis=0)
    magnitude = np.hypot(dx, dy)
    bins = (np.arctan2(dy, dx) % np.pi) * 8 / np.pi
    result = []
    for y in range(0, 48, 4):
        for x in range(0, 48, 4):
            angle = bins[y:y + 4, x:x + 4].ravel()
            value = magnitude[y:y + 4, x:x + 4].ravel()
            histogram = np.zeros(8)
            lower = angle.astype(int) % 8
            fraction = angle - lower
            np.add.at(histogram, lower, value * (1 - fraction))
            np.add.at(histogram, (lower + 1) % 8, value * fraction)
            result.extend(histogram / (np.linalg.norm(histogram) + .05))
    return np.asarray(result)


def make_model():
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LogisticRegression(
        C=.01, class_weight="balanced", max_iter=2000, random_state=SEED,
    ))


def collect(args) -> None:
    # Lazy import keeps feature helpers usable without importing project parsers.
    import external_ai_review as rev

    out = args.dataset
    out.mkdir(parents=True, exist_ok=True)
    samples, missing, provenance = [], [], []
    for n in range(args.first_page, args.last_page + 1):
        source = ROOT / rev.SOURCE / f"bnf-f{n:04}.md"
        aligned = ROOT / "site/assets/alignment" / f"bnf-f{n:04}.json"
        if not source.exists():
            continue
        rows = {r["id"]: r for r in read_json(aligned)["rows"]} if aligned.exists() else {}
        scan_path = ROOT / "build/nippo-jisho-images/scans/native" / f"f{n:04}.jpg"
        scan = None
        page_provenance = {"page": n, "source_sha256": sha256(source),
                           "alignment_sha256": sha256(aligned) if aligned.exists() else None}
        if scan_path.exists():
            page_provenance["scan"] = {"path": str(scan_path.relative_to(ROOT)),
                                      "size": scan_path.stat().st_size,
                                      "mtime_ns": scan_path.stat().st_mtime_ns}
        provenance.append(page_provenance)
        for lid, line in rev.lines(rev.parse(source.read_bytes())).items():
            text = rev.plain(line)
            faces = [run["typeface"] for run in line["runs"] for _ in run["text"]]
            row = rows.get(lid)
            mapping = {}
            if row and row.get("alignment"):
                for tag, a, b, c, _ in SequenceMatcher(None, text, row["text"], autojunk=False).get_opcodes():
                    if tag == "equal":
                        mapping.update((i, c + i - a) for i in range(a, b))
            for word in re.finditer(r"[^\W\d_]+", text):
                for local, character in enumerate(word[0]):
                    if character != "ç":
                        continue
                    i = word.start() + local
                    post_t = i > 0 and text[i - 1] in "Tt"
                    japanese = any(faces[k] == "roman" and text[k].islower()
                                   for k in range(word.start(), word.end()) if k != i)
                    if n > args.reference_through and not (post_t and japanese):
                        continue
                    item = dict(page=n, line=lid, offset=i, word=word[0], expected_text=text,
                                expected_typeface=faces[i], label=int(faces[i] == "italic"),
                                post_t=post_t, japanese=japanese)
                    j = mapping.get(i)
                    alignment = row["alignment"][j] if j is not None else None
                    if not alignment or alignment.get("kind") != "matched":
                        missing.append({**item, "reason": "no_matched_alignment"})
                        continue
                    if not scan_path.exists():
                        missing.append({**item, "reason": "no_native_scan"})
                        continue
                    if scan is None:
                        with Image.open(scan_path) as im:
                            scan = im.convert("L")
                    patch = native_patch(scan, row, j)
                    if patch is None:
                        missing.append({**item, "reason": "no_native_mapping"})
                        continue
                    item["crop"] = f"{len(samples):05}.png"
                    item["target_width"] = alignment["width"] * row["image_width"] / 50
                    patch.save(out / item["crop"])
                    samples.append(item)
        if n % 25 == 0:
            print(f"f{n}: {len(samples)} samples", flush=True)
    write_json(out / "samples.json", samples)
    write_json(out / "missing.json", missing)
    write_json(out / "collection.json", {
        "pipeline_version": PIPELINE_VERSION, "reference_commit": git_commit(),
        "reference_through": args.reference_through, "first_page": args.first_page,
        "last_page": args.last_page, "sources": provenance,
        "samples_sha256": sha256(out / "samples.json"),
        "note": "Source hashes identify exact inputs, including any uncommitted edits; scan stat metadata is not a content hash.",
    })
    print(f"Collected {len(samples)} crops; {len(missing)} unavailable.")


def load_features(dataset: Path, samples: list[dict]) -> tuple[np.ndarray, str]:
    """Cache only when the manifest, actual crop bytes, and pipeline all match."""
    digest = hashlib.sha256(PIPELINE_VERSION.encode())
    digest.update((dataset / "samples.json").read_bytes())
    for sample in samples:
        digest.update(bytes.fromhex(sha256(dataset / sample["crop"])))
    fingerprint = digest.hexdigest()
    cache, metadata = dataset / "features.npy", dataset / "features.json"
    if cache.exists() and metadata.exists() and read_json(metadata).get("fingerprint") == fingerprint:
        return np.load(cache), fingerprint
    features, diagnostics = [], []
    for i, sample in enumerate(samples):
        with Image.open(dataset / sample["crop"]) as image:
            glyph, info = extract_glyph(normalize(image), diagnostics=True)
        features.append(hog(glyph))
        diagnostics.append({"id": i, **info})
    values = np.asarray(features)
    np.save(cache, values)
    write_json(metadata, {"fingerprint": fingerprint, "pipeline_version": PIPELINE_VERSION})
    write_json(dataset / "segmentation.json", diagnostics)
    return values, fingerprint


def measures(labels: np.ndarray, scores: np.ndarray) -> dict:
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix

    if len(labels) == 0:
        return {"n": 0}
    predicted = scores > 0
    return {"n": len(labels), "correct": int((labels == predicted).sum()),
            "accuracy": float(accuracy_score(labels, predicted)),
            "balanced_accuracy": float(balanced_accuracy_score(labels, predicted)),
            "confusion": confusion_matrix(labels, predicted, labels=[0, 1]).tolist()}


def train(args) -> None:
    import joblib
    from sklearn.model_selection import StratifiedGroupKFold

    samples = read_json(args.dataset / "samples.json")
    X, fingerprint = load_features(args.dataset, samples)
    labels = np.asarray([s["label"] for s in samples])
    pages = np.asarray([s["page"] for s in samples])
    japanese = np.asarray([s["japanese"] and s["post_t"] for s in samples])
    reference = pages <= args.reference_through
    ids = np.flatnonzero(reference)
    if len(np.unique(pages[ids])) < 5 or len(np.unique(labels[ids])) != 2:
        raise ValueError("training requires both typefaces and at least five reference pages")
    scores = np.zeros(len(samples))
    folds = np.full(len(samples), -1)
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=args.seed)
    for fold, (tr, te) in enumerate(splitter.split(X[ids], labels[ids], pages[ids])):
        training, testing = ids[tr], ids[te]
        model = make_model()
        model.fit(X[training], labels[training])
        scores[testing] = model.decision_function(X[testing])
        folds[testing] = fold
        print(f"Fold {fold}: {measures(labels[testing], scores[testing])}", flush=True)
    subsets = {
        "all": reference, "japanese_post_t": reference & japanese,
        "japanese_438_onward": reference & japanese & (pages >= 438),
        "japanese_468_onward": reference & japanese & (pages >= 468),
        "recent_japanese": reference & japanese & (pages >= args.reference_through - 1),
        "other_cedillas": reference & ~japanese,
    }
    metrics = {name: measures(labels[mask], scores[mask]) for name, mask in subsets.items()}
    # These held-out pages were also examined during method development: do not
    # present them as a permanently untouched final test.
    chronological_training = np.flatnonzero(pages <= args.reference_through - 2)
    chronological_test = np.flatnonzero(reference & japanese & (pages >= args.reference_through - 1))
    model = make_model()
    model.fit(X[chronological_training], labels[chronological_training])
    chronological_scores = model.decision_function(X[chronological_test])
    report = {
        "pipeline_version": PIPELINE_VERSION, "seed": args.seed,
        "reference_through": args.reference_through, "feature_fingerprint": fingerprint,
        "collection": read_json(args.dataset / "collection.json") if (args.dataset / "collection.json").exists() else None,
        "training_commit": git_commit(), "page_grouped_metrics": metrics,
        "page_grouped_rows": [dict(id=int(i), label=int(labels[i]), score=float(scores[i]), fold=int(folds[i])) for i in ids],
        "chronological": {
            "training_through": args.reference_through - 2,
            "metrics": measures(labels[chronological_test], chronological_scores),
            "rows": [dict(id=int(i), label=int(labels[i]), score=float(score)) for i, score in zip(chronological_test, chronological_scores)],
        },
        "caveat": "Exploratory model comparisons informed feature/model choices. Margins are not calibrated confidence; abstentions are not counted as correct.",
    }
    write_json(args.dataset / "validation.json", report)
    model = make_model()
    model.fit(X[ids], labels[ids])
    joblib.dump({"model": model, "pipeline_version": PIPELINE_VERSION,
                 "reference_through": args.reference_through, "feature_fingerprint": fingerprint},
                args.dataset / "model.joblib")
    print(json.dumps({"page_grouped": metrics, "chronological": report["chronological"]["metrics"]}, indent=2))


def predict(args) -> None:
    import joblib

    samples = read_json(args.dataset / "samples.json")
    X, fingerprint = load_features(args.dataset, samples)
    bundle = joblib.load(args.dataset / "model.joblib")
    if bundle["pipeline_version"] != PIPELINE_VERSION or bundle["feature_fingerprint"] != fingerprint:
        raise ValueError("dataset or feature pipeline changed since training; train again")
    threshold = bundle["reference_through"]
    ids = [i for i, s in enumerate(samples) if s["page"] > threshold and s["japanese"] and s["post_t"]]
    scores = bundle["model"].decision_function(X[ids]) if ids else []
    predictions, proposals = [], []
    for i, score in zip(ids, scores):
        sample = samples[i]
        typeface = "italic" if score > 0 else "roman"
        item = {"id": i, **sample, "score": float(score), "prediction": typeface}
        predictions.append(item)
        if typeface != sample["expected_typeface"]:
            proposals.append({**item, "page": f"bnf-f{sample['page']:04}", "typeface": typeface})
    write_json(args.dataset / "predictions.json", predictions)
    write_json(args.dataset / "proposals.json", proposals)
    print(f"Scored {len(predictions)} targets; proposed {len(proposals)} changes: {dict(Counter(p['typeface'] for p in proposals))}")
    print("No canonical files changed. Recheck expected_text/expected_typeface before applying proposals.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, handler in [("collect", collect), ("train", train), ("predict", predict)]:
        command = commands.add_parser(name)
        command.add_argument("dataset", type=Path, help="local experiment directory")
        command.set_defaults(handler=handler)
        if name != "predict":
            command.add_argument("--reference-through", type=int, default=484)
        if name == "collect":
            command.add_argument("--first-page", type=int, default=13)
            command.add_argument("--last-page", type=int, default=542)
        if name == "train":
            command.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
