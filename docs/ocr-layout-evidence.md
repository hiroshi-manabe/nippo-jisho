# Dictionary-wide OCR layout evidence

## Purpose

The project preserves an OCR layout layer for every dictionary leaf with
ordinary columns before using OCR to improve the browser-facing rectangles.
This layer is evidence, not transcription: generating it must not replace
Level 1 text, stable line IDs, reviewed geometry, or human decisions.

Earlier workflows mixed several cases.  `f161`–`f170` received OCR-first
geometry, `f171`–`f237` received OCR text aligned to older rectangles, and the
later scan-bootstrap candidates were constructed from OCR baselines.  A
dictionary-wide evidence set removes that historical difference.  It also
lets us tell whether a failure began in line segmentation, canonical-line
alignment, rectangle normalization, or browser presentation.

## Preserved source layer

The reproducible range is `f13`–`f642`.  Structurally unusual leaves are not
discarded: their detections remain available even when they cannot safely be
mapped to ordinary two-column line IDs.  `f643` remains a separately handled
final leaf.

For every page, `pilot/ocr-layout-evidence/v1/pages/` stores a deterministic
gzip-compressed JSON record containing:

- the native scan path, dimensions, and SHA-256 digest;
- the exact OCR-draft digest and recognition method;
- every detected row's provisional ID and source detector ID;
- raw baseline and boundary coordinates;
- the detector bounding rectangle and OCR input rectangle;
- unnormalized OCR text and the prepared-image digest.

The manifest records page coverage, line totals, OCR-model and segmentation
provenance, and each compressed record's digest.  Per-page evidence is
immutable by default: a differing record requires an explicit `--replace`.
Temporary prepared images and predictions remain under `.cache`; the compact
evidence needed to reproduce geometry comparisons is committed.

Generate or resume the evidence set with:

```sh
python3 scripts/build_ocr_layout_evidence.py --first 13 --last 642
```

The command reuses a raw draft only when it was made by the same Kraken and
book-specific Calamari workflow.  Missing pages are segmented and recognized
from the native scan.  It never reads or writes canonical transcription text.

## Geometry-improvement campaign

OCR evidence and human-review geometry remain separate.  The campaign uses
the preserved detections to propose associations and rectangles, then compares
those proposals with the current canonical geometry.

Priority order:

1. `f171`–`f237`, whose OCR readings were historically placed on older,
   commonly interpolated rectangles;
2. `f13`–`f160`, whose processed rectangles may include broad, forced, or
   manually reconstructed crops;
3. `f161`–`f170`, as verification of the earlier OCR-first import;
4. machine-provisional later leaves, whose geometry is already OCR-derived
   but still lacks complete visual confirmation.

For a canonical physical line, an automatic proposal may use OCR for ordered
correspondence and baseline position.  It must retain enough vertical overlap
for ascenders, descenders, and diacritics, and enough horizontal context to
show the applicable printed column rules.  The proposal is classified as one
of:

- agreement with current geometry;
- likely horizontal clipping;
- likely vertical clipping or displacement;
- suspicious neighboring-line association;
- unmatched canonical line or unused OCR detection;
- structural exception requiring direct visual judgment.

Raw detections are never altered during this process.  Canonical text is never
changed by a geometry campaign.  Existing reviewed geometry is not silently
replaced: automatic results first become an audit/proposal, and any promoted
rectangle must pass the ordinary full-size crop-to-transcription inspection in
the human-review workflow.  When automation cannot establish the association,
the scan is inspected directly and an explicit per-line rectangle is used.

## Completion and provenance

A page is not `line_by_line_reverified` merely because OCR found a close
baseline.  Promotion requires readable target text in every resulting card,
complete edge evidence, and correct physical-line association.  The geometry
record notes the OCR-evidence version used for the proposal and preserves any
manual override.  This makes later reprocessing possible without erasing why
the current rectangle was accepted.

## First completed run

The 2026-09-05 run archived all 630 leaves in `f13`–`f642`, comprising 62,750
raw detections.  The compressed committed archive is approximately 20 MB.
The initial canonical comparison covered all 21,126 body lines on `f13`–`f237`.

The `f161`–`f170` control confirmed the method's diagnostic value: the ten
pages that had already received OCR-first geometry produced only 41 flagged
rows, compared with 5,921 initially flagged rows on `f171`–`f237`.  A
conflict-free first campaign therefore replaced geometry—not text—for 5,371
lines on 57 pages in `f171`–`f237`.  Every proposed column was rendered into a
contact sheet; numerical containment checks and representative high-drift,
split-zone, early, middle, and late sheets were inspected.  These columns keep
the conservative `contact_sheet_reviewed` state and do not claim
`line_by_line_reverified` status.

Ten pages remain deliberately unchanged because OCR alignment exposed missing
rows, merged rows, displaced fragments, or neighbor conflicts: `f189`, `f190`,
`f195`, `f200`, `f207`, `f213`, `f215`, `f217`, `f220`, and `f231`.  Their raw
evidence and exact conflict inventories are preserved in the campaign report.

For `f13`–`f160`, the first campaign generated 106 conflict-free proposals and
quarantined 42 structurally ambiguous pages.  These proposals have not been
applied: this range contains extensive manual geometry history, so its OCR
results are an audit queue rather than permission to replace reviewed
rectangles wholesale.

## Targeted repair of systematic offsets

The 2026-09-05 follow-up began with a visible failure on `f109`.  Both columns
had been represented by a single linear vertical calibration.  A correction
to the lower part of column 2 had previously been expressed by changing the
endpoint of that calibration, which displaced earlier rows as well.  Because
the review rectangles were taller than the line pitch, the intended text
could remain somewhere in a crop even when the neighboring row occupied its
visual focus.  A check for mere presence or partial readability was therefore
not strong enough.

The follow-up audited `f13`–`f237` against the archived OCR baselines and
selected columns only when at least twenty close text matches showed a
consistent signed displacement.  Moderate cases were included after direct
contact-sheet inspection.  It then applied explicit per-line rectangles to
1,079 lines in 23 columns on 20 pages: `f18`, `f21`, `f29`, `f31`, `f58`,
`f59`, `f106`, `f109`, `f123`, `f131`, `f136`–`f139`, `f141`–`f143`, `f145`,
`f156`, and `f158`.  Four lines without a safe direct OCR match were placed by
interpolation between their nearest matched physical neighbors (`f31`
`c1-l037`, `c1-l039`, and `c1-l046`; `f109` `c1-l039`).  The immutable
proposal and exact application report are preserved in
`pilot/ocr-layout-evidence/v1/campaign-systematic-offset-repair/`.

All 23 repaired columns subsequently cleared the same systematic-offset
audit.  The remaining high-displacement results belong only to the previously
quarantined structural pages in the `f171`–`f237` campaign; they were not
silently altered.

For future geometry review, the target physical line must be the primary,
focused, fully readable content of its crop.  Seeing the target somewhere in
an overlapping band is not sufficient.  Neighboring text may remain as useful
context, but it must not obscure which physical row the card represents.
