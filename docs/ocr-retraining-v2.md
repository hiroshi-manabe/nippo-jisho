# Corrected f13–f200 OCR retraining

## Experiment contract

Compare a newly trained plain-text Calamari model with a style-aware variant,
using the same corrected human-reviewed source, images, page split, starting
checkpoint, seed, learning rate, and maximum training budget. The starting
book checkpoint saw only the old training pages. Preserve the old validation
and test split, and deterministically assign five additional validation and
five additional test pages from f151–f200 (seed 1603).

The earlier test pages have historical published results, so they are not
completely unseen by this project. They remain excluded from optimization in
this experiment; report the newly held-out f151–f200 subset separately too.

1. Build a frozen dataset from current canonical body lines and preserved
   independent OCR polygons. Match in physical sequence; reject uncertain or
   neighbor-conflicting correspondences and record exclusions. Do not rewrite
   canonical text or geometry. Rectify polygons instead of training on broad
   human-display crops. Both models receive identical images.
2. Train baseline and style-aware runs. Use validation only for early stopping
   and error inspection. Plain targets retain diplomatic Unicode, including
   the human-reviewed `ß` versus `ſſ` distinction.
3. Inspect validation errors and attempt at most two or three targeted changes
   with an explicit hypothesis. Do not optimize indefinitely. Evaluate crop
   errors, lost accents, double-s forms, short labels, and typeface transitions.
4. Freeze selection before final test evaluation. Report text CER, exact lines,
   style accuracy conditional on correct characters, combined text/style error,
   and relevant feature subsets. Never count a plain model's absent style
   output as a correct typeface prediction.
5. Deliver actual usable local checkpoints, decoder/inference support, metrics,
   and reproduction instructions. Choose the practical default from evidence;
   do not modify existing canonical transcriptions as part of model training.

## Internal style encoding

The styled model assigns each italic non-space character a private-use code
point equal to the original code point plus U+F0000. Roman characters retain
their ordinary code points. The model thus learns character/style pairs with
CTC; this is not a request to emit literal Markdown delimiters without ink.
Whitespace has no style label because visual attribution at boundaries is
usually undefined. NFC is preserved; combining marks without a precomposed
character retain their own labels. Internal labels never enter Level 1 data.

`scripts/build_ocr_retraining_dataset.py` exports the paired datasets and
ordinary-text references with per-character style. It records source and image
hashes, split membership, and exclusions in ignored local artifacts.
`scripts/run_ocr_retraining.py` runs one controlled experiment and predicts only
the validation split. It refuses to overwrite a run directory.

Weights and generated datasets remain local under `.cache/ocr-model/`;
reproducible code and final aggregate results belong in Git.

## Current status

The frozen dataset contains 13,982 training, 1,784 validation, and 1,780 test
lines. It excludes 83 uncertain correspondences and two display-type lines.
The first controlled comparison is running; no new model has yet been selected
or claimed superior. The full plain and styled runs use output directories
`calamari-plain-v2b` and `calamari-styled-v2b` under `.cache/ocr-model/runs`.
Each has a maximum of 12 epochs and patience of three validation evaluations.
The existing deployed model is also evaluated on the same validation images
and corrected references, rather than comparing incompatible historical scores.

A 32-training-line / 16-validation-line smoke run successfully saved a styled
checkpoint and retained the private-use labels for italic `ẽ` and `ß`.
This is an implementation check, not an accuracy result. An earlier export
used too small a private-use range and was discarded from comparison before
training; the corrected frozen dataset is `.cache/ocr-model/retraining-v2b`.

Visual crop spot checks identified the black exterior mask used by Kraken's
polygon extraction. Both initial runs share it, as did the earlier isolated
pipeline. If validation errors justify a crop experiment, test a paper-colored
exterior mask with the original polygon retained; do not erase border-connected
ink heuristically or silently change only inference preprocessing.
