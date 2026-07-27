# Transcription-Format Pilot Workspace

This directory contains experimental material for the [Transcription-Format Pilot](../docs/transcription-format-pilot.md). It is not production Stage 1 transcription.

## Frozen independent-draft checkpoint

The files under `transcription-v0/` were produced by direct visual inspection of the Gallica/Wikimedia scan. Wikisource was not consulted while preparing these drafts.

The drafts are now frozen for the later comparison step. Any comparison with Wikisource must be recorded separately and must not silently alter these files.

The circumstances and limitations of the first pass are recorded in the [Independent Draft Log](draft-log.md).

One qualification applies: the opening dictionary page, `bnf-f0013`, had already been viewed together with its Wikisource transcription earlier in the project discussion. It is therefore useful for the page-feature survey but is excluded from the blinded transcription comparison.

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
