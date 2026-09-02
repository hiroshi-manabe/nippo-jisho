# OCR-initialized Level 1 page data

## Purpose

`scripts/build_ocr_page_data.py` turns independent Calamari page drafts into
provisional Level 1 pages. It is intended for structured pages that have not
yet received human review. It does not overwrite a page with any completed
human-review unit unless `--allow-checked` is explicitly supplied. Because the
older registry does not completely represent the conversational review record,
the known human-reviewed prefix through f160 is also protected by default;
`--human-reviewed-through` makes that boundary explicit on later runs.

The recognizer is the source of the new body-line reading. Existing page data
are retained only as structural scaffolding: stable physical-line IDs, zones,
indentation, approximate roman/italic spans, displaced-text metadata, and the
already checked rectangles used by the browser. The old reading is opened only
after the raw OCR draft has been written, and may then help associate the
independently detected rows with those stable IDs.

## Pipeline

1. Kraken detects rows from each native page scan without using saved line
   rectangles or transcription.
2. The book-specific Calamari model recognizes a native-scan band around every
   detected row.
3. Post-inference sequence alignment maps the resulting rows to physical-line
   IDs by text, order, and scan position.
4. Pages with suspicious omissions or large disagreements receive a second,
   neighbor-resistant rectified-line pass. A saved-geometry scan band is used
   only for a row genuinely missed by both independent passes.
5. Existing roman/italic and placement spans are projected onto the OCR text by
   character alignment. Page furniture and structurally displaced far-right
   fragments are preserved.
6. Readings whose projected edit rate exceeds 35% are quarantined: the prior
   provisional text is retained and the line is recorded for scan review.
7. Every output must round-trip through compact Markdown and pass the complete
   corpus validator before publication.

The independent detections validate row association, but do not silently
replace browser geometry. Human-review crops have stricter needs than OCR
crops—especially complete glyphs and visible outer rules—so their existing
rectangles remain authoritative until explicitly rechecked.

## Running it

The default range is the existing human-unreviewed structured run f161–f237.
The first command performs OCR and writes a dry-run audit; the second applies
the inspected cached result:

```sh
python3 scripts/build_ocr_page_data.py
python3 scripts/build_ocr_page_data.py --skip-ocr --apply
```

Use `--first-page`, `--last-page`, or `--pages` for another prepared range.
Intermediate drafts and the detailed audit remain under
`.cache/ocr-model/ocr-page-data-v1/`. The tracked
`pilot/human-review/ocr-page-baseline.json` records the exact raw-draft digest,
changed-line count, and quarantined or structurally preserved lines for each
applied page.

## f161–f237 application

The first complete application on 2026-09-02 covered 77 pages and 7,261 body
lines. It changed 4,212 line readings; 3,009 already agreed exactly with the
previous provisional text. All physical lines were accounted for. Seven rows
needed the saved-geometry fallback, 20 used the rectified second route, 17
high-change readings were quarantined, and 23 displaced structural rows were
preserved instead of being erased by OCR.

The raw page-level benchmark used nine previously reviewed or structurally
irregular pages. Blind detection found 814 of 816 body lines (99.75%). Strict
diplomatic CER was 7.82%, but this aggregate is distorted by f160: its internal
section transition defeated the benchmark's position-only row comparison. The
other eight pages had 98.91–100% line recall and 1.26–4.54% CER. This is why the
application stage uses post-inference sequence alignment while preserving a
hard independence boundary around recognition.

These pages remain `visual_draft`, not human-checked transcriptions. OCR is a
better provisional reading source here, but it is still weak on terminal
hyphens, long/short *s*, diacritic identity and placement, unusual capitals,
typeface boundaries, and damaged or displaced text. General visual inspection
and then human comparison remain required.

## Generic-AI fusion trial on f162–f170

After the human correction of f161, pages f162–f170 received a fresh
generic-AI pass that treated the independent OCR draft and the earlier visual
draft as competing evidence rather than choosing either source wholesale. On
f161, the earlier visual draft matched 59 of 99 physical lines exactly and had
a 1.86% character error rate against the human-corrected page; the independent
OCR draft matched 53 lines and had a 2.98% character error rate. A simple
feature-aware hybrid improved that comparison to 62 exact lines and a 1.76%
character error rate. This small benchmark motivated the evidence-weighting
rule in [the OCR-assisted reading policy](ocr-assisted-reading.md), but is not
a general accuracy estimate.

For f162–f170, NINJAL and linguistic context were used to recover headword
identity, Japanese morphology, and coherent Portuguese where OCR produced a
different reading. Locally aligned OCR was preferentially retained for
reading-neutral diplomatic details such as `s`/`ſ`, a physical terminal
hyphen, spacing, punctuation, and accent placement, unless enlarged scan
inspection contradicted it. Every physical line was then compared with its
scan crop, and these pages are now `scan_confirmed` while human review remains
pending. The trial confirms that OCR is most useful as local typographic
evidence; it is not yet a dependable source for complete lexical readings.

The concise reproducibility record is
[`experiments/ocr/ocr-page-data-f161-f237-results.json`](../experiments/ocr/ocr-page-data-f161-f237-results.json).
