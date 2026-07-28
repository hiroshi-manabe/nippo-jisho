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

## Candidate-format trial

The completed [format version 1 trial](format-v1-trial/README.md) is a new implementation experiment, not a rewrite of the frozen version-0 checkpoint. It contains complete physical-order records for `bnf-f0013`, `bnf-f0014`, `bnf-f0248`, and `bnf-f0643`, separate structural assertions, and regenerated page and logical reading views.

The trial validates 330 physical lines in a [compact human-readable Level 1 form](../docs/level1-markdown-candidate.md), then regenerates the machine representation and page views. Seven structural assertions and eight reading sequences remain as a secondary information-loss check rather than the project’s present design focus. The remaining Level 1 questions are recorded in the trial report and candidate specification.

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
