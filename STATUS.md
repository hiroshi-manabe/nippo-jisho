# Project Status

Last updated: 2026-07-29

## Current phase

**Transcription-format pilot — candidate evaluation**

The project has surveyed representative pages and frozen the first format-version-0 transcriptions made directly from the scans. Wikisource has not been consulted for these drafts. This is a pre-production activity supporting Stage 1 of the [Four-Stage Project Roadmap](docs/four-stage-roadmap.md), not yet sequential transcription of the dictionary.

The detailed purpose, method, and completion criteria are defined in the [Transcription-Format Pilot](docs/transcription-format-pilot.md).

The complete native-resolution Gallica image sequence has been acquired and checksum-verified. The result is recorded in [Acquisition Summary](sources/acquisition-summary.yaml). Source acquisition does not change the transcription pilot’s current checkpoint.

The first timed second-pass trial is complete. The [Tiled Visual Review Pilot](docs/tiled-visual-review.md) now records overlapping quarter-column and sixth-column views as a workable review method, and the page-level evidence is preserved in the [bnf-f0248 Second Visual Pass](pilot/second-pass/bnf-f0248.md). A revised [Pilot Diacritic Audit](pilot/diacritic-audit.md) distinguishes 30 carons, five genuine circumflexes, one grave accent, and one unmarked form among 37 flagged occurrences across two frozen pages.

The first controlled [Wikisource comparison](pilot/wikisource-comparison/bnf-f0014.md) is also complete. Wikisource supplied four new scan-confirmed corrections in the selected zones, agreed with two corrections already made independently, and contained several errors and structural omissions of its own. Only five of the 653 PDF pages currently contain contributed Wikisource text, none proofread or validated. Routine use has therefore been rejected; external transcription is reserved for exceptional unresolved cases after independent review. The frozen independent files were not rewritten.

The resulting visual, linguistic, and expectation-driven cautions are consolidated in the [Provisional Transcription Reading Guide](docs/transcription-reading-guide.md). It includes the `g`/`q` problem, `qua`/`cua`/`qu` distinctions, capitalization and spacing traps, diacritic findings, and page-furniture safeguards. These are diagnostic reinspection prompts, not normalization rules.

NINJAL's CC BY 4.0 [Nippo Jisho Headword Data](docs/headword-data.md), version 202510, has been downloaded, unpacked, checksum-verified, and documented. Its 32,878 source-order records provide dictionary-wide coverage and reading checks unavailable from Wikisource. It remains an attributed external reference because it is based on the Bodleian copy and contains editorial normalization; the Gallica scan remains authoritative.

The provisional layer boundary has now been clarified. Stage 1 will preserve observable page evidence in physical order and will not ordinarily assert entry boundaries or logical reassignment of displaced text. Stage 2 will add those interpretations by linking back to stable Stage 1 spans. The lowercase but structurally independent `aburamono` and the physically displaced `(grande.` are the current test cases for this distinction.

The uncertainty policy is intentionally lightweight. Context may support an ordinary secure transcription, as with the fold-crossed `Aa vobitataxiya.` passage on `f13`; explicit markers are reserved for readings that remain materially disputable or illegible. The format must permit more detailed notes without imposing character-level confidence metadata on routine work.

Targeted enlargement is nevertheless a routine review step for any locally difficult span, regardless of the standard tile size. Reviewers return to the surrounding context after enlargement; only doubt that survives both views is marked in the transcription.

The first implemented [candidate page-transcription format](docs/page-transcription-format-v1-candidate.md) has now been exercised in a [four-page trial](pilot/format-v1-trial/README.md). Complete physical-order records for `bnf-f0013` and `bnf-f0014`, plus selected difficult regions of `bnf-f0248` and `bnf-f0643`, comprise 229 physical lines. A separate structural record supplies seven assertions and eight selected reading sequences. The validated renderer regenerates page-oriented and continuous reading views without copying or silently correcting Level 1 text.

The trial supports the Level 1/Level 2 separation, stable physical-line references, typeface runs, relative indentation, and exceptional placement. It also exposes two decisions still needed before adoption: JSON is dependable but verbose as a hand-authoring format, and the lightweight uncertainty representation has not yet been tested on a genuinely unresolved reading.

## Current objective

Evaluate the implemented version 1 candidate, decide whether to retain JSON as the authoring format or generate it from a more compact syntax, and exercise the uncertainty mechanism on a genuinely unresolved source reading. The adopted specification must continue to provide stable evidence for three linked uses:

1. A page-oriented reading and verification view
2. A continuous-text view generated through separate structural assertions
3. Preliminary extraction of structured dictionary entries linked to, but not embedded in, Stage 1

## Milestones

- [x] Establish the provisional canonical source and page identifiers needed for the pilot.
- [x] Select approximately 10–15 representative pages.
- [x] Catalogue the principal page and typography features observed in the sample.
- [x] Produce and freeze independent provisional transcriptions of selected test cases.
- [x] Acquire and checksum-verify all 651 native-resolution Gallica images.
- [x] Generate reproducible quarter-column and sixth-column tile profiles for the first test page.
- [x] Perform a timed second independent visual pass using overlapping tiles.
- [x] Compare independent transcription with correction of available Wikisource text.
- [x] Test generation of page-oriented, continuous-text, and entry-oriented views.
- [x] Document unresolved cases and format limitations.
- [ ] Publish version 1 of the page-transcription specification.
- [ ] Decide the initial transcription provenance and licensing policy.

## Production progress

Production counts are intentionally not reported yet. Pilot transcriptions are experiments and must not be mistaken for reviewed Stage 1 coverage. Page and entry totals will be added after the source inventory and status model have been established.

## Next phase

After the transcription format is stable, a smaller end-to-end pilot will test the entry schema, Japanese restoration, translation, and public-edition requirements. Broad Stage 1 production begins only after those foundational decisions are documented.
