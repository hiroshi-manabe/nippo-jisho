# Line-clipping repair campaign

The pilot covers every body column of f121–f145, including previously repaired
columns. The intended later scope is f13–f237. Transcription and stable IDs are
not changed by this campaign.

Unlike the earlier systematic-offset campaign, selection does not require a
consistent column-wide displacement. Every column enters the coverage ledger;
unmatched or ambiguous OCR alignments remain explicit manual-review items.

1. Re-audit current crops against the preserved OCR evidence.
2. Generate proposals with `scripts/prepare_clipping_campaign.py`. OCR warnings
   are candidate evidence, not verified defects. Proposals preserve existing
   coverage and add detector boundaries with padding; inspect surplus neighboring
   ink and narrow or reposition manually where warranted.
3. Inspect actual cropped images with their canonical line text, using wider
   context for ambiguous alignment or damaged print. Check accents, ascenders,
   descenders, both horizontal ends, and displaced fragments.
4. Re-render each adjusted crop and verify the whole target row is included.
5. Mark each column checked/unchanged, repaired/verified, or unresolved. Never
   infer visual completion from an OCR score or from proposal generation.
6. Apply only visually verified proposals, synchronize dependent geometry,
   validate the site, commit, push, and verify deployment.

Pilot coverage is recorded in
`pilot/ocr-layout-evidence/v1/campaign-line-clipping/coverage.json`.
Incomplete entries prevent claiming campaign completion. The old audit is
historical evidence only; all proposals must use current canonical geometry.

## Pilot result — 2026-09-05

All 50 body columns (2,362 line crops) are accounted for: 38 columns repaired
and visually verified, 12 checked/unchanged, none unresolved. The campaign
expanded 1,572 crops on 23 pages. This is the number of adjusted rectangles,
not a claim that every OCR warning represented an independently confirmed
clipped character. f139 needed no changes. f123 retained its immediately
preceding complete individual-crop verification and unchanged geometry.

The remaining 24 pages received visual inspection of every isolated crop beside
its assigned text. Weak OCR matches were checked separately and retained when
the existing crop already contained the target row. The initial C on f135 was
also inspected in enlarged context; the proposed crop already contains it.
Text, line IDs, furniture and human-review counts were not changed.

`scripts/apply_clipping_campaign.py` checks the complete pilot range and column
ledger and refuses proposals whose baseline geometry has changed. It defaults
to a dry run. Its `--apply` option synchronizes canonical geometry, calibration
centres and column boxes, and saves the compact coverage record. The review
decisions must be recorded after actual image inspection, never generated from
the OCR score. Local audit/proposal sheets are disposable derived files.

## Extension checkpoint — 2026-09-06

The extension covers f13–f237. A fresh automated audit covers all 225 pages
(21,125 body rows), but this is not a claim of completed visual review.
The audit alignment now permits skipping long runs of marginal handwriting
detections: the previous fixed 12-row displacement limit could force body text
onto unrelated OCR detections. A synthetic regression test covers that failure.

Additional completed individual-crop inspections: f13–f14 and f146–f150
(14 columns). These yielded 447 adjusted rectangles, with text and IDs unchanged.
The oversized initial A on f13 and D on f149 required manual expansion and
re-rendering. f15 column 1 has been inspected, but its oversized initial still
needs attention; the page remains unapplied and unverified as a whole.

`extension-decisions.json` and `extension-coverage.json` in the campaign directory
record this checkpoint. Pending entries are deliberately not applied. The
original pilot ledger remains authoritative for f121–f145; pending entries in
the extension ledger do not revoke that earlier inspection.

The subsequent f181–f185 commentary review inspected all ten columns' individual
crops again, retaining nine columns unchanged and enlarging the owning crop of
the f181 initial. Its two former body rows that are actually catchwords are
recorded separately in the notes; no stable IDs were renumbered. Outside the pilot,
188 pages still await completed visual review. Do not describe the extension
as finished.

`scripts/render_clipping_campaign.py` renders actual individual proposed crops
beside their text. The application command supports `--reviewed-only` and
`--coverage-output` to publish a verified checkpoint without overwriting the
pilot ledger. Before a later application, regenerate proposals against current
geometry and preserve the explicit manual crop decisions. Never mechanically
mark pending pages reviewed.
