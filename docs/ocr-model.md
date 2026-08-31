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
pairs; the evidence-gated high-recall version retains 12,368 pairs (95.65% of
the source lines) while continuing to route the remaining visually difficult
material back to the established general-purpose visual-AI workflow.

## Isolated-line version 2 ablation

Two fresh models were trained from `microsoft/trocr-small-printed` with the
same seed and three-epoch frozen-encoder configuration. The core run used 9,406
training pairs and excluded the positional-rescue tier. The full run added the
437 validated positional training pairs. Both selected checkpoints on the same
1,177-line core development set and were evaluated on the same page-disjoint
test material.

| Model | Ordinary test CER | Positional test CER | Combined CER |
| --- | ---: | ---: | ---: |
| Core | **10.93%** | 18.67% | **11.03%** |
| Full | 11.85% | **9.43%** | 11.82% |

The full model nearly halves error on the 67 positional test lines and raises
their exact-line rate from 29.85% to 53.73%, but it degrades the much larger
ordinary subset. The core checkpoint is therefore the best single default.
When provenance is available, routing only `positionally-anchored` crops to the
full checkpoint yields 10.91% combined CER and a 10.68% exact-line rate, both
better than using either checkpoint indiscriminately.

The model weights remain local. Reproducible manifests are generated by
`scripts/build_ocr_training_ablation.py`; aggregate results and the adopted
routing policy are recorded in
[`experiments/ocr/trocr-isolated-ablation-v1-results.json`](../experiments/ocr/trocr-isolated-ablation-v1-results.json).
`scripts/recognize_nippo_trocr.py` now uses the core checkpoint by default; pass
`--run .cache/ocr-model/runs/trocr-isolated-full-v1` only for a crop already
marked `positionally-anchored`.

## First post-training page pilot

`f151`, the out-of-range page on which version 1 had reached 31.63% CER, was
used as the first real application of the isolated-line engine. The comparison
first exposed a canonical geometry defect rather than a recognition defect:
both columns' first body-line centres were recorded at y=420, while an
independent Kraken pass placed the first 47 ordered body baselines at y=464 and
y=470. The old overlapping rectangles made the intended lines visible to a
human but associated several short lines more strongly with a neighbour.

After the 94 stable line IDs were remapped to the detected baselines and every
new review rectangle was checked on complete contact sheets, the core model
reached 13.36% aggregate CER on the corrected canonical review rectangles.
Kraken's independently rectified line polygons aligned all 94 lines and reduced
aggregate CER to **10.09%** (14 exact lines); 93 of 94 lines were at or below
the existing 60% usable-draft threshold. The remaining failure was a correctly
cropped short line that the recognizer simply misread, so it did not justify a
geometry change.

The OCR differences then served as a review queue, not replacements for the
transcription. Enlarged scan inspection recovered the printed division
`actu-` / `almente.` where Level 1 had `actua-` / `lmente.`, and found a
roman/italic boundary error after `Bup.`. The tracked measurements and
correction evidence are in
[`experiments/ocr/f0151-post-training-pilot-results.json`](../experiments/ocr/f0151-post-training-pilot-results.json).

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
