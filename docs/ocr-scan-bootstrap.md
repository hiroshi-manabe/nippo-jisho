# Scan-first Level 1 bootstrap

## Purpose

The existing OCR-to-Level-1 bridge can replace provisional readings on a page
whose physical lines, zones, identifiers, and geometry already exist. It
cannot start a page from the scan alone. `scripts/bootstrap_ocr_level1.py`
tests the missing earlier stage: it constructs a machine-provisional Level 1
candidate without opening the target page's transcription or geometry.

This is an initializer, not an automatic publication path. Its output retains
`physical_lineation_checked: false`, and the script never writes canonical
Level 1 or public-review data.

## Inputs and inference

For every target and benchmark leaf, the script first creates independent raw
page drafts from the native scan:

1. Kraken detects possible text baselines in each column.
2. Calamari reads a complete horizontal scan band around every detection.
3. Detections at nearly the same height are collapsed into one physical row;
   the longest complete-band reading is retained while every source detection
   ID remains in the evidence package.
4. Running headers and internal display headings are separated from body
   flow. Material whose role is not secure, especially short bottom-right
   fragments, is retained as `unclassified_furniture`.
5. Physical left offsets infer entry versus continuation indentation. Extreme
   baseline fragments are excluded before fitting the two ordinary indentation
   clusters.
6. A character 2–5-gram and word model trained on earlier structured pages
   assigns provisional roman and italic runs. It does not alter OCR spelling.
7. The preceding page's main alphabet section is used only as constrained
   sequential context. The recurring decorated `G`→`C` OCR confusion may be
   repaired when the prior section makes `C` impossible; all repairs are
   listed in the candidate audit.

Candidate packages include the provisional page, source-pixel line crops and
context crops, raw OCR evidence, collapsed-detection provenance, uncertain
typeface tokens, initial-letter repairs, ambiguous bottom material, and a flag
for the first row after each internal heading where an enlarged initial may
need direct inspection.

## Independence and benchmark

The script serializes every inferred target and benchmark candidate before it
opens any canonical benchmark transcription or reviewed geometry. Its default
held-out set covers ordinary pages, shortened columns, internal headings,
major alphabet transitions, enlarged initials, and pages adjacent to the
first target: `f14`, `f18`, `f47`, `f68`, `f103`, `f115`, `f135`, `f149`,
`f160`, `f230`, and `f237`.

The 2026-09-02 run compared 997 canonical body rows with 1,001 inferred rows:

| Measure | Result | Gate |
| --- | ---: | ---: |
| Body-row recall | 99.90% | 98.50% |
| Body-row precision | 99.50% | 97.50% |
| Indentation accuracy | 97.49% | 90.00% |
| Roman/italic accuracy on matching characters | 96.37% | 95.00% |
| Diplomatic character accuracy | 96.98% | 94.00% |
| Exact internal-heading count | 21 of 22 columns | diagnostic |

The character score includes OCR spelling, punctuation, diacritics, and long
`ſ`; it is not the recognizer's self-reported confidence. Full per-page
results are preserved in
`experiments/ocr/scan-bootstrap-v1-results.json`.

## First target batch

The passing run created candidate packages for `f238`–`f247`. It recovered
940 provisional body rows and one internal heading. The machine also retained
eight ambiguous bottom fragments outside body flow and recorded its inferred
entry-initial repairs. These files are preserved under
`pilot/ocr-bootstrap/f0238-f0247/` but are deliberately absent from the
canonical corpus and public review UI.

Representative source crops from `f238`, `f242`, and `f247` were visually
checked after generation. The selected rows contain the intended complete
line and both column rules where available. This sample is evidence that the
crop construction is plausible, not a substitute for the required all-line
visual geometry gate.

## Dictionary-wide mechanical generation

The bulk run extends the same independent path to the previously unstructured
dictionary leaves `f251`–`f642`. Existing structured pages are not regenerated
or overwritten merely because their human review is incomplete. `f248`–`f250`
are frozen under `pilot/ocr-bootstrap/reference-f0248-f0250/` and regenerated
only as near-range controls; the exceptional final leaf `f643` retains its
existing hand-structured data.

The bulk command has two deliberately separate decisions:

1. generate a self-contained candidate for every requested scan, retaining
   OCR evidence even when the page is structurally unusual; and
2. classify the candidate as an ordinary two-column leaf or quarantine it for
   structural review.

The ordinary-page check considers per-column row counts and spacing, column
width, text/geometry line-ID equality, internal-heading count, running-header
evidence, and constrained alphabet-section continuity. Failure does not delete
or normalize a candidate. It records the exact reasons in
`audit.bulk_assessment` and keeps that leaf outside the ordinary review queue.

`scripts/materialize_ocr_bootstrap_batch.py` is the repository boundary. It
refuses a failed held-out benchmark, verifies each native-scan checksum and
page identifier, requires exact body-text/geometry ID agreement, and rejects
any candidate that falsely claims visually checked physical lineation. Its
manifest distinguishes ordinary candidates, quarantined candidates, and
inference failures. Materialization still does not modify the canonical Level
1 corpus or public review data.

The 2026-09-02 bulk run generated all 392 requested leaves with no inference
failures. It preserved 36,745 provisional body rows, 112 internal-heading
rows, and 341 uncertain bottom fragments. The conservative classifier placed
366 leaves in the ordinary two-column queue and quarantined 26: 25 because
their running header was not securely recognized, and `f376` because its
genuine N/adverb/P/Q transition produced ten internal display-heading rows.
The complete result is under `pilot/ocr-bootstrap/f0251-f0642/`.

The 14-page held-out set contained 1,278 canonical body rows. The bulk run
matched 1,277, missed one, and proposed five extras: 99.92% recall and 99.61%
precision. Indentation accuracy was 97.89%, roman/italic accuracy on matching
characters was 96.44%, and diplomatic character accuracy was 97.14%. The
three frozen near-range controls `f248`–`f250` each had exact body-row counts
with no missing or extra rows; their character accuracies were 98.86%, 97.61%,
and 96.64%. The full report is preserved in
`experiments/ocr/scan-bootstrap-bulk-v1-results.json`.

## Known limitations and promotion gate

The body-line result is strong enough to make dictionary-wide candidate
generation realistic, but two structures remain deliberately unresolved:

- Page numbers can share a physical baseline with a running header. The
  column-band recognizer may join them or read only the part inside the column.
  The scan must be used to split and identify such furniture.
- Enlarged initials after alphabet headings can span several rows and may be
  omitted or misread by ordinary line OCR. The candidate audit identifies the
  affected first row, but a reviewer must determine the glyph and its span.

Before any candidate becomes canonical, a reviewer must therefore:

1. confirm every physical row and every heading/furniture transition against
   the whole page;
2. inspect every generated line crop and context crop for complete readable
   glyphs and visible right-edge evidence;
3. resolve enlarged initials and ambiguous bottom fragments;
4. perform the ordinary Japanese, Portuguese, punctuation, diacritic, and
   typeface review passes; and
5. only then compile, validate, and publish the page through the normal Level
   1 workflow.

## Reproduction

Run the default benchmark and bounded candidate batch with:

```sh
python3 scripts/bootstrap_ocr_level1.py
```

Use `--skip-ocr` only when the matching raw drafts already exist in the output
directory. A failed gate exits non-zero and still leaves the diagnostic
candidate packages and report for inspection; canonical files remain
unchanged in either case.

For an inclusive bulk range, use:

```sh
python3 scripts/bootstrap_ocr_level1.py \
  --page-range 251 642 \
  --benchmark-pages 14 18 47 68 103 115 135 149 160 230 237 248 249 250 \
  --continue-on-page-error \
  --output .cache/ocr-model/scan-bootstrap-bulk-v1
```

After inspecting the report, preserve a passing batch with:

```sh
python3 scripts/materialize_ocr_bootstrap_batch.py
```
