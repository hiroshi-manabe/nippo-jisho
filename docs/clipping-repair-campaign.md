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

The intended extension to f13–f237 remains pending; this pilot is not evidence
that columns outside f121–f145 have passed the new campaign.
