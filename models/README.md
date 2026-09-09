# Local OCR models

Finished model packages belong in `local/`, separate from temporary training
runs and datasets under `.cache/ocr-model/`. The binary packages are deliberately
Git-ignored and are not automatically published. Back up `local/` when preserving
trained models independently of this working copy.

Each package contains a SavedModel, its character codec, a `model.json` manifest
with file hashes, upstream attribution, dataset provenance, and the development
and final-test evaluations used for the release. Packaging is done only after
the model-selection decision and final evaluation.

Use `scripts/recognize_nippo_calamari.py` with a package directory to recognize
isolated, rectified line images. Style-aware packages return ordinary text and
Roman/italic runs, never the private-use training labels. Inference does not
modify canonical page data.

See [the retraining report](../docs/ocr-retraining-v2.md) for model selection,
results, limitations, and reproduction instructions.
