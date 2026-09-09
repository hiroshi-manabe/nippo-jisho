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

The styled run uses `scripts/train_styled_calamari.py` to initialize each
Roman/italic variant from the corresponding pretrained letter's output weights.
If both variants exist, subtracting log(2) from both biases preserves their
combined initial letter probability; the CTC blank remains unchanged. This
avoids making the style-aware model relearn the alphabet merely because its
labels are new. Unknown characters retain Calamari's normal initialization.
The probability identity has a numeric regression test, and a 32-line training
smoke successfully copied 161 outputs and saved a checkpoint. `--style-init
random` retains stock Calamari initialization for a future controlled ablation.

Weights and generated datasets remain local under `.cache/ocr-model/`;
reproducible code and final aggregate results belong in Git.

## Current status

The audited dataset (`retraining-v2d`) contains 13,977 training, 1,784 validation,
and 1,780 test lines. All 17,631 source body lines are accounted for: 17,541
(99.49%) retained and 90 excluded with recorded reasons. There are 150 training,
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

Inspection of remaining worst validation errors exposed a second pixel-level
problem. The old horizontal trim treats dense dark columns as rules; on dark
paper surrounded by a white polygon mask, this can discard most of the actual
text. For example, f20/c1-l020 retained only the ending `Itẽ, Aldea,` despite
having a full-width source polygon. `scripts/ocr_line_images.py` now preserves
the complete rectified extent and only adjusts contrast and scale. Dataset
generation and inference share that function. Synthetic dark-paper regression
tests and enlarged before/after crops verify the fix.

The full comparable runs are `calamari-plain-v2d` and `calamari-styled-v2d`,
both using the corrected full-extent paper-white dataset. Earlier diagnostic
runs are retained locally but are not claimed as completed final models.
On this dataset, the old model's full validation CER is 5.7974%, with 555/1,784
exact lines and five lines over 50% CER. New-model and final-test results are
still pending.

One saved **epoch-seven diagnostic snapshot**, not the final selection, was
independently decoded on all 1,784 validation lines while training continued.
Its corpus CER is 1.7643% (1,042/59,061 characters), versus 5.7974% for the old
model. Exact lines rose from 555 to 1,163; lines over 50% CER fell from five to
one. It recognized 44/48 `ß` instances, 43/46 literal `ſſ` sequences, and all
three `ſs` sequences. Terminal-hyphen false negatives/positives fell from 54/40
to 28/14. Marked-vowel exact matches rose from 614/911 to 818/911. However,
direct short-/long-s substitutions stayed almost unchanged (27 versus 28),
despite fewer missing or otherwise misread s characters. This is evidence of
substantial but uneven improvement, not a claim that all glyph distinctions
are solved. The snapshot and results are retained in
`.cache/ocr-model/runs/calamari-plain-v2d-epoch7-diagnostic/`.
The s-swap total is strongly clustered: 19/28 occur on f66, including 14
Roman headwords in the `Busa-`/`Bus-` sequence. Across the whole validation set,
only seven swaps are immediately before `t`; five are other italic contexts
and 16 other Roman contexts. Do not extrapolate a broad `st` failure from this
aggregate or silently relabel the human-reviewed references to match the model.

On this eight-core/16 GB host the two trainers contended for CPU and ran slower
together. The production runs therefore execute sequentially. The already
started styled trainer was suspended in memory (not restarted) while the plain
run finishes; `scripts/sequence_ocr_training.py` verifies process identities and
resumes it automatically. Its waiting time must not be interpreted as training
compute time when comparing run durations. Reproduction can simply run the
plain command followed by the styled command.

### Residual dataset limitations

Inspecting the five worst old-model validation lines found one remaining bad
pair: `f66/c1-l019` (`couſas.`) has a small right-margin detection instead of the
word visible toward the left of the source column. Width plausibility and
full-band text agreement do not prove that a short line's polygon is correct.
The other four inspected crops (`f57/c1-l047`, `f63/c1-l048`, `f66/c2-l001`, and
`f101/c1-l017`) visibly contain their text, although some are faint or have
displaced material. Thus the automatic dataset audit is not a guarantee of
perfect segmentation. Keep this known mismatch in the frozen comparison;
do not silently remove difficult validation examples after inspecting errors.
It is a candidate for a later dataset revision, not a canonical-text correction.

## Reproduction and delivery

The native Calamari environment is described in [OCR model](ocr-model.md).
Dataset extraction additionally requires the existing native Kraken environment.
Use fresh output directories: the dataset and training runners deliberately
refuse to overwrite an experiment. From the repository root:

```sh
arch -arm64 .cache/ocr-model/venv-kraken-arm64/bin/python \
  scripts/build_ocr_retraining_dataset.py
python3 scripts/validate_ocr_retraining_dataset.py
python3 scripts/run_ocr_retraining.py --mode plain \
  --output .cache/ocr-model/runs/calamari-plain-v2d
python3 scripts/run_ocr_retraining.py --mode styled \
  --output .cache/ocr-model/runs/calamari-styled-v2d
```

Run the last two commands sequentially on this host. They train, save the best
validation checkpoint, and produce independent `dev-evaluation.json` files;
they do not evaluate test pages. Freeze the chosen runs and selection rationale
before generating test predictions. Evaluate those with
`scripts/evaluate_ocr_retraining.py --split test`, adding `--styled` only for
the encoded model.

`scripts/compare_ocr_retraining.py` compares the decoded text predictions and
adds a paired page-bootstrap interval for styled-minus-plain CER. It resamples
whole pages because lines on one page share typography and scan conditions;
the exact same sampled pages contribute to both models. Report the newer
holdout subset separately, while recognizing that five pages give limited
evidence about the rest of the dictionary. Use development predictions for
selection; test comparisons are reporting only, not another tuning round.

`scripts/package_ocr_model.py` requires a completed matching run, final test
evaluation, and selection record. It copies the SavedModel and codec, dataset
summary/audit, validation/test results, and upstream license notice into a fresh
local package. The manifest records file hashes, training-record fingerprint,
and original checkpoint provenance. It does not publish weights or scan images.
`scripts/recognize_nippo_calamari.py` consumes the package and isolated line
images, returning ordinary text plus Roman/italic runs for the styled model.
Its `--prepared` option is for benchmark images that already have exactly the
training preprocessing; ordinary rectified inputs receive the shared full-extent
preprocessing. Neither tool edits canonical transcription files.
