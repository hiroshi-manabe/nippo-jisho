# Calamari page-draft pipeline

## Purpose

`scripts/prepare_calamari_page_drafts.py` tests whether the selected
book-specific Calamari recognizer can initialize a page without first reading
the project's saved transcription or line rectangles. The inference path uses
only the native scan:

1. Kraken 5.2.9's bundled baseline model detects physical rows.
2. A 72-pixel horizontal band is cut from the native scan around each detected
   baseline and normalized to the Calamari model's 48-pixel line height.
3. Calamari recognizes every detected row in one batch.
4. A provisional `nippo-ocr-page-draft` JSON file preserves the raw reading,
   baseline, polygon, bounding rectangle, OCR crop, and prepared-image digest.

The draft deliberately does not guess typeface spans, indentation, furniture
roles, or canonical Level 1 line IDs. Those decisions remain part of the normal
visual-AI and human-review process.

## Independence boundary

Draft JSON is written before any existing transcription or review geometry is
opened. Comparison happens afterward:

- reviewed benchmark pages use monotonic scan-position alignment, with OCR text
  excluded from row association;
- f161–f170 use monotonic text/order alignment only after the independent draft
  exists, because their current text and geometry are both still unreviewed.

The latter is a disagreement measurement, not an accuracy score. The complete
local comparison retains every aligned reading and every unmatched detection.

## Reproduction

The default command processes the fourteen page-disjoint OCR test pages and
f161–f170:

```sh
python3 scripts/prepare_calamari_page_drafts.py
```

The output is under `.cache/ocr-model/calamari-page-drafts-v1/`:

- `drafts/bnf-fNNNN.json`: independent provisional page drafts;
- `comparison.json`: complete line-by-line benchmark and disagreement data;
- `comparison.md`: compact aggregate and per-page tables;
- `segmentation/`, `prepared/`, and `predictions/`: reproducible intermediate
  evidence.

Segmentation and recognition are cached. Recognition reuse is allowed only when
the manifest of prepared-image SHA-256 values is unchanged. Use
`--fresh-segmentation` or `--fresh-recognition` to force either stage.

## First result

On fourteen reviewed, page-disjoint benchmark pages, blind segmentation found
1,312 of 1,314 canonical body lines (99.85%). Calamari reached 2.25% strict
diplomatic character error on those position-matched rows; 769 of 1,312 lines
(58.61%) were exact. There were two catastrophic rows over 50% CER. The two
missed canonical lines were `f113/c1-l037` and `f135/c2-l047`.

Against the current human-unchecked f161–f170 data, all 943 body lines were
matched. The independent OCR draft differed by 4.77% of characters and agreed
exactly on 327 lines (34.68%). This larger distance includes errors on both
sides. A conspicuous OCR-domain gap is the roman capital `F` at the beginning
of F-section headwords: it is absent as a headword initial from the f13–f150
training pages and is the most common substitution in the trial.

The comparison also found a concrete geometry conflict at `f161/c1-l033`: the
saved centre points to a short spurious `auet` detection, while the next blind
candidate contains the expected `Facanaſa.`-like headword row. No current page
text or geometry was automatically replaced.

The tracked aggregate record is
[`experiments/ocr/calamari-page-draft-v1-results.json`](../experiments/ocr/calamari-page-draft-v1-results.json).

## Interpretation

This is good enough to initialize provisional rows and to expose likely
geometry defects. It is not good enough to publish unattended Level 1 data:
typeface remains absent, extra detections remain, two benchmark rows were
missed, terminal hyphens and marked vowels still need targeted checking, and
the new F-section glyph distribution is partly out of the training domain.

The intended route is therefore:

1. generate the independent page draft;
2. let general-purpose visual AI inspect the scan and reconcile structure,
   typeface, and difficult readings;
3. publish the resulting page to the existing human review interface;
4. treat human corrections as the final authority and future training data.
