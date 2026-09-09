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

The audited dataset (`retraining-v2c`) contains 13,848 training, 1,755 validation,
and 1,764 test lines. All 17,631 source body lines are accounted for: 17,367
(98.50%) retained and 264 excluded with recorded reasons. There are 150 training,
19 validation, and 19 test pages; no page spans multiple splits. File hashes,
current canonical references, style targets, and crop-width constraints passed
`scripts/validate_ocr_retraining_dataset.py`.
The first controlled comparison is in progress; no new model has yet been selected
or claimed superior. The original black-exterior plain run stopped after its
first saved checkpoint (validation CER 6.52%) when the controlled crop probe
below identified a substantially better input representation. It is retained
as a diagnostic, not represented as a completed paired comparison.
Each has a maximum of 12 epochs and patience of three validation evaluations.
The existing deployed model is also evaluated on the same validation images
and corrected references, rather than comparing incompatible historical scores.

A 32-training-line / 16-validation-line smoke run successfully saved a styled
checkpoint and retained the private-use labels for italic `ẽ` and `ß`.
This is an implementation check, not an accuracy result. An earlier export
used too small a private-use range and was discarded from comparison before
training; that encoding correction was recorded in `retraining-v2b`.

Visual crop spot checks identified the black exterior mask used by Kraken's
polygon extraction. A systematic 95-line validation sample spanning all 19 dev
pages compared the old model on identical polygons with black versus paper-white
exteriors. CER fell from 464/3,265 (14.21%) to 300/3,265 (9.19%), and exact lines
rose from 8 to 27. This validates the first targeted improvement without using
test scores. The same corrected references and polygons were first re-extracted
in `.cache/ocr-model/retraining-v2-white`.

`scripts/reextract_ocr_retraining.py` inverts image intensities before Kraken
extraction (which pads with zero) and inverts back afterwards. It thus gives a
paper-white exterior without guessing which border-connected pixels are ink.
It preserves line identities, reference hashes, splits and polygons. Training
and inference must use the same convention.

The subsequent training-input audit caught a separate correspondence defect:
the preserved OCR text came from a **full-column horizontal band**, whereas
its associated detection polygon could be a margin speck or a small fragment
at that height. For example, the original f43/c1-l021 image was only 8 pixels
wide for a 42-character sentence; the corrected image is 471 pixels wide.
The exporter now filters margin detections and implausibly short fragments
before sequence alignment, then checks whether both target encodings have
enough image width for CTC. It does not equate full-band recognition agreement
with proof that the detection polygon contains the whole line.

The full comparable runs are `calamari-plain-v2c` and `calamari-styled-v2c`,
both using the corrected paper-white dataset. Earlier diagnostic runs are
retained locally but are not claimed as completed final models.
