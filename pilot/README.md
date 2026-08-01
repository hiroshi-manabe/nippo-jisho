# Transcription-Format Pilot Workspace

This directory contains experimental material for the [Transcription-Format Pilot](../docs/transcription-format-pilot.md). It is not production Stage 1 transcription.

## Frozen independent-draft checkpoint

The files under `transcription-v0/` were produced by direct visual inspection of the Gallica/Wikimedia scan. Wikisource was not consulted while preparing these drafts.

The drafts were frozen before the completed comparison step and remain unchanged. Any exceptional future comparison with an external transcription must be recorded separately and must not silently alter these files.

The circumstances and limitations of the first pass are recorded in the [Independent Draft Log](draft-log.md).

Pre-comparison corrections found by later direct inspection are kept outside the frozen files. The first complete record is the [bnf-f0248 Second Visual Pass](second-pass/bnf-f0248.md), which includes its timing, tile coverage, proposed corrections, and layout findings.

Potentially reusable discoveries are collected in [Working Editorial Observations](working-observations.md). These remain provisional until further page evidence confirms them; adopted conventions will later move into the versioned transcription specification.

The [Pilot Diacritic Audit](diacritic-audit.md) maintains the initial glyph inventory, occurrence-level results, Unicode choices, representative source-image crops, and the history of a superseded blanket correction. It distinguishes caron, circumflex, grave, and tilde without rewriting the frozen drafts.

The first controlled [Wikisource comparison](wikisource-comparison/bnf-f0014.md) uses the blinded selected zones of `bnf-f0014`. It records exact revision provenance, a coverage snapshot, scan adjudication of every meaningful disagreement, and the limited licensing conclusion. The frozen draft remains unchanged.

The comparison's reusable error patterns, together with later research on Jesuit romanization, are maintained in the [Provisional Transcription Reading Guide](../docs/transcription-reading-guide.md). Wikisource is no longer part of the routine workflow.

One qualification applies: the opening dictionary page, `bnf-f0013`, had already been viewed together with its Wikisource transcription earlier in the project discussion. It is therefore useful for the page-feature survey but is excluded from the blinded transcription comparison.

## Level 1 format corpus

The [format version 1 corpus](format-v1-trial/README.md) is not a rewrite of the frozen version-0 checkpoint. Its six-page adoption baseline has been extended by sequential production pages `bnf-f0015`–`bnf-f0017`; it now contains nine complete physical-order records, separate structural assertions over the adoption examples, and regenerated page and logical reading views.

The corpus validates 818 physical lines in the adopted [compact human-readable Level 1 form](../docs/level1-markdown-candidate.md), then regenerates the machine representation and page views. Seven structural assertions and eight reading sequences remain as a secondary information-loss check rather than the project’s present design focus.

A subsequent [contextual review of `f0248` and `f0643`](contextual-review/f0248-f0643.md) tests separate Japanese/romanization and Portuguese passes followed by scan confirmation. It finds two residual corrections and rejects five plausible but unprinted emendations.

The [timed `f0249`–`f0250` production simulation](production-simulation/f0249-f0250.md) applies the full workflow to unfamiliar consecutive pages, adds 196 lines, and supplies the evidence for adopting version 1.

The [dictionary-wide human review interface](human-review/README.md) navigates all 651 acquired leaves. Column review now trials vertically stacked, equal-width scan-line and transcription pairs with expandable context; full-page and furniture views retain the broader layout. The other 642 leaves are marked `unprocessed`, and 27 resumable human-review units track two columns and page furniture for every transcribed page. The revised `f14` units are human-checked; the corrected `f15` and `f16` columns await recheck, while `f17` review is in progress.

The [raw f13–f16 correction corpus](correction-corpus/README.md) preserves 97 exact textual transitions, including superseded and reverted proposals, in a searchable occurrence-level table. Its first post-hoc use on `f17` is recorded beside it: all major earlier error families were reinspected after the normal review passes, no new change was accepted, and the non-changes remain available for later recall and precision analysis.

## Draft coverage

- `bnf-f0014`: selected zones testing a cross-column continuation, repeated running header, and divided catchword.
- `bnf-f0248`: full lexical text in a provisional logical-line transcription, testing a section transition within a column.
- `bnf-f0643`: full lexical text and page furniture in a provisional logical-line transcription, testing the final page.

The phrase “full lexical text” does not mean reviewed or production-complete. Uncertain readings are deliberately retained, and physical lineation has not yet been certified.

## Freeze rule

Files at this checkpoint carry:

```yaml
status: independent_draft_frozen
wikisource_consulted: false
```

Corrections discovered before the comparison may be placed in a separately dated review file. Corrections discovered through Wikisource comparison belong in a comparison record with explicit provenance.
