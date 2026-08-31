# OCR and N-gram fusion for marked `o`

## Purpose

This experiment asks whether the existing line OCR can complement the
character N-gram when a marked `o` has already been located and the remaining
choice is `ô` versus `ǒ`. It does not test mark detection, and it does not allow
either model to override the scan.

## Leakage control

The OCR checkpoint was trained on most pages in `f13`–`f150`, so applying it to
all of those pages would produce a misleading result. Fusion is instead fitted
on the OCR run's original 14 development pages and evaluated once on its
original untouched 14 test pages. The N-gram is separately retrained with the
entire physical-page group being scored excluded from its corpus.

The development material contains 249 canonical marked-`o` occurrences, of
which 245 have accepted isolated-line images. The test material contains 188,
of which 183 have accepted images. Missing lines remain outside the experiment
rather than receiving fabricated OCR evidence.

## OCR evidence tested

At each target position, the TrOCR decoder receives the canonical preceding
text but not the target token. The experiment compares its logits for the
single-token alternatives `ô` and `ǒ`. This is favorable, oracle-quality
context and therefore may overestimate production performance when the
pre-human draft itself is wrong.

Four visual scores were tested:

- the model's trained 48-pixel isolated-line rendering;
- a new 96-pixel rendering generated from the native scan;
- each of the above after subtracting the same-prefix score obtained from a
  blank image, intended to remove part of the decoder's linguistic prior.

The core checkpoint is used ordinarily; the full checkpoint is used for lines
already classified as `positionally-anchored`. Free OCR decoding is also
aligned to the reference as a separate, lower-information baseline.

## Untouched test result

| Method | Correct | Accuracy | Coverage |
| --- | ---: | ---: | ---: |
| 2-gram alone | **130/183** | **71.04%** | 100% |
| ordinary 48-pixel OCR contrast | 105/183 | 57.38% | 100% |
| native-scan 96-pixel OCR contrast | 111/183 | 60.66% | 100% |
| free OCR decoded a usable `ô`/`ǒ` | 54/103 | 52.43% | 56.28% |
| N-gram and 96-pixel OCR agree | 86/114 | 75.44% | 62.30% |
| page-calibrated logistic fusion | 127/183 | 69.40% | 100% |

The apparently better agreement row is not a useful two-class classifier: all
114 retained predictions are `ǒ`. It correctly retains 86 printed `ǒ` forms
and misclassifies 28 `ô` forms. The blank-image residual variants perform still
worse, showing that simple prior subtraction does not isolate accent shape.

A deliberately asymmetric rule was also selected on development data: retain
the N-gram decision except when strong 96-pixel OCR evidence favors `ǒ` against
a weak N-gram `ô`. It improved development accuracy from 172/245 to 184/245,
but on the untouched test set it changed 22 decisions with only 50% override
precision and left total accuracy unchanged at 130/183. The apparent
development gain did not generalize.

The logistic model could produce a development subset at 90% precision, but
the same threshold reached only 35/43 (81.40%) on the untouched test pages and
again predicted only `ǒ`. No development threshold reached 95% precision with
even ten retained examples.

## Decision

The present line recognizer should **not** vote on circumflex versus caron. Its
accent evidence is correlated with the corpus majority, unstable between page
groups, and adds no reproducible improvement over the N-gram.

The useful division of labor is therefore:

1. OCR may flag a possible marked-`o` location or an unstable crop.
2. The N-gram may order `ô` and `ǒ` as weak linguistic candidates.
3. Enlarged scan inspection decides the printed mark.

A future visual contribution should be a dedicated high-resolution glyph or
accent-shape classifier trained on localized, human-confirmed examples. It
must use page-disjoint evaluation and report both classes separately; another
weighted combination of the present line-decoder scores is not justified.

## Reproduction

The tracked evaluator generates the OCR contrasts, trains split-specific
KenLM models, fits the page-balanced logistic model, selects thresholds only on
development pages, and evaluates them on the untouched test pages.

```sh
arch -arm64 .cache/ocr-model/venv-arm64/bin/python \
  scripts/evaluate_o_mark_fusion.py \
  --lmplz /path/to/lmplz \
  --output experiments/ocr/o-mark-ocr-ngram-fusion-v1-results.json
```

The complete aggregate result is tracked in
[`experiments/ocr/o-mark-ocr-ngram-fusion-v1-results.json`](../experiments/ocr/o-mark-ocr-ngram-fusion-v1-results.json).
Occurrence-level OCR scores and generated language models remain reproducible
ignored cache artifacts.
