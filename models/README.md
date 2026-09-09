# Local OCR models

Completed packages (2026-09-10):

- `local/nippo-calamari-v2-plain`: text-only, 1.255% final test character error.
- `local/nippo-calamari-v2-styled`: text and Roman/italic runs, 1.312% text error;
  99.644% style accuracy conditional on correct non-space text.

Matching `.zip` archives sit alongside these directories. Archive CRCs and
every archived file were verified against the unpacked packages.

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
