# Experimental Nippo Jisho recognition engine

This project has a private, book-specific line recognizer trained from the
reviewed transcriptions and native Gallica scans. It produces a useful first
draft for human correction; it is not an authority and never replaces review
against the scan.

## Dataset and benchmark

`scripts/build_ocr_dataset.py` matches the compact Level 1 text for `f13`–`f150`
to canonical line geometry and native scans. It writes 12,930 line pairs:

| Split | Pages | Lines |
| --- | ---: | ---: |
| Training | 110 | 10,296 |
| Development | 14 | 1,320 |
| Test | 14 | 1,314 |

The split is made at page level, so no physical page contributes to more than
one set. Seed `1603` and the exact development and test pages are frozen in
[`experiments/ocr/f13-f150-split.json`](../experiments/ocr/f13-f150-split.json).
The test set is used only for final reporting, never checkpoint selection.

The target is NFC diplomatic Unicode text without Markdown typeface markers or
outer whitespace. Crops are autocontrasted, trimmed horizontally while ignoring
dense column rules, and scaled to 48 pixels high without changing their aspect
ratio. The generated manifests, line images, and metadata live under the
ignored `.cache/ocr-model/dataset-v2` directory.

```sh
python3 scripts/build_ocr_dataset.py
```

## Model choice

A compact convolutional CTC model was implemented first to establish a fully
local baseline. Even with approximate monotonic-alignment warm-up, its best
small experiment remained around 88% test character error rate. It is retained
as experimental code, but it is not the working engine.

The useful model fine-tunes `microsoft/trocr-small-printed`. The pretrained
vision encoder is frozen for the initial three-epoch run while the decoder
adapts to the book's typography, historical Portuguese, and romanized Japanese.
Two implementation details are important:

- The XLM-R tokenizer normalizes long `ſ` to short `s`. The wrapper substitutes
  the otherwise unused `§` internally and restores `ſ` after decoding.
- TrOCR/BART must retain its pretrained decoder-start convention. Replacing the
  decoder start token with the tokenizer's BOS token lowers teacher-forced loss
  while causing empty or collapsed free generation.

## Reproducing training

The recorded run used native Apple Silicon with the versions pinned in
[`requirements-ocr-model.txt`](../requirements-ocr-model.txt). The native
environment also avoids a batch-backward problem observed in an older PyTorch
MPS build.

```sh
arch -arm64 /usr/bin/python3 -m venv .cache/ocr-model/venv-arm64
arch -arm64 .cache/ocr-model/venv-arm64/bin/python -m pip install \
  -r requirements-ocr-model.txt

arch -arm64 .cache/ocr-model/venv-arm64/bin/python \
  scripts/train_nippo_trocr.py \
  --output .cache/ocr-model/runs/trocr-small-v1 \
  --epochs 3 --patience 3 --max-eval-lines 128 \
  --batch-size 8 --eval-batch-size 8 \
  --learning-rate 0.00001 --freeze-encoder-epochs 3 \
  --max-length 48 --log-every 50
```

The checkpoint with the lowest development loss is saved to
`.cache/ocr-model/runs/trocr-small-v1/best`. The 128-line generation sample at
the end of training is only a quick diagnostic; the complete page-disjoint
benchmark must be run separately:

```sh
arch -arm64 .cache/ocr-model/venv-arm64/bin/python \
  scripts/evaluate_nippo_trocr.py
```

The full metrics and up to 40 error examples per split are written to
`.cache/ocr-model/runs/trocr-small-v1/full-evaluation.json`.

## Version 1 results

The complete evaluation—not the smaller training diagnostic—produced:

| Split | Lines | Character error rate | Exact lines |
| --- | ---: | ---: | ---: |
| Development | 1,320 | 19.88% | 64 (4.85%) |
| Test | 1,314 | **16.70%** | 61 (4.64%) |

The tracked aggregate record is
[`experiments/ocr/trocr-small-v1-results.json`](../experiments/ocr/trocr-small-v1-results.json).
The test score corresponds to 83.30% diplomatic character accuracy, including
spacing, punctuation, diacritics, and long `ſ`; it is useful for draft creation
but plainly still requires human correction.

An exploratory run on the next page, `f151`, reached 31.63% CER. Inspection
showed that the generous human-review crops expose fragments of neighbouring
lines, which particularly confuses recognition of short lines. Tightening those
crops only at inference time worsened the page to 37.01% because it changed the
distribution learned during training, so that change was rejected. A future
version should generate OCR-specific isolated crops and retrain on them rather
than changing inference alone.

That follow-up [clean isolated-line dataset](clean-ocr-pairs.md) now has two
reproducible profiles. The conservative version retains 8,049 image–text
pairs; the evidence-gated high-recall version retains 12,519 pairs (96.82% of
the source lines) while continuing to route the remaining visually difficult
material back to the established general-purpose visual-AI workflow.

## Using the engine

Recognize one or more already-cropped physical line images:

```sh
arch -arm64 .cache/ocr-model/venv-arm64/bin/python \
  scripts/recognize_nippo_trocr.py path/to/line.png
```

Or recognize every line for a page whose native scan and geometry are present:

```sh
arch -arm64 .cache/ocr-model/venv-arm64/bin/python \
  scripts/recognize_nippo_trocr.py --page 151 \
  --output .cache/ocr-model/drafts/f0151.json
```

The output is JSON containing stable page/line identifiers, source crop
coordinates, and recognized text. Model weights remain private, ignored local
artifacts; only the reproducible code, split, parameters, and aggregate results
belong in Git.

## Deliberate limitations

The first engine recognizes physical lines independently. It does not emit
roman/italic Markdown, model neighbouring-line or dictionary-entry context, or
resolve typographic ambiguities such as short-`s` versus long-`ſ` reliably
enough to remove human review. Those are better treated as later rescoring or
specialized passes after the line recognizer has supplied a strong draft.
