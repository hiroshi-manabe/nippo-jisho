# Project Status

Last updated: 2026-08-01

## Current phase

**Level 1 format adopted — sequential production validation**

The transcription-format pilot is complete. The project adopted Level 1 Markdown format version 1 after a six-page corpus test and a timed two-page simulation on previously untranscribed consecutive pages. Sequential Stage 1 production now includes `f15`–`f17`, following human confirmation of the revised `f14`; the method is still being validated before production scales.

The detailed purpose, method, and completion criteria are defined in the [Transcription-Format Pilot](docs/transcription-format-pilot.md).

The complete native-resolution Gallica image sequence has been acquired and checksum-verified. The result is recorded in [Acquisition Summary](sources/acquisition-summary.yaml). Source acquisition does not change the transcription pilot’s current checkpoint.

The first timed second-pass trial is complete. The [Tiled Visual Review Pilot](docs/tiled-visual-review.md) now records overlapping quarter-column and sixth-column views as a workable review method, and the page-level evidence is preserved in the [bnf-f0248 Second Visual Pass](pilot/second-pass/bnf-f0248.md). A revised [Pilot Diacritic Audit](pilot/diacritic-audit.md) distinguishes 30 carons, five genuine circumflexes, one grave accent, and one unmarked form among 37 flagged occurrences across two frozen pages.

The first controlled [Wikisource comparison](pilot/wikisource-comparison/bnf-f0014.md) is also complete. Wikisource supplied four new scan-confirmed corrections in the selected zones, agreed with two corrections already made independently, and contained several errors and structural omissions of its own. Only five of the 653 PDF pages currently contain contributed Wikisource text, none proofread or validated. Routine use has therefore been rejected; external transcription is reserved for exceptional unresolved cases after independent review. The frozen independent files were not rewritten.

The resulting visual, linguistic, and expectation-driven cautions are consolidated in the [Provisional Transcription Reading Guide](docs/transcription-reading-guide.md). It includes the `g`/`q` problem, `qua`/`cua`/`qu` distinctions, capitalization and spacing traps, diacritic findings, and page-furniture safeguards. These are diagnostic reinspection prompts, not normalization rules.

A two-layer linguistic reference is now available for the contextual passes. The compact [Transcription Cheat Sheet](docs/transcription-cheat-sheet.md) is the daily operational view; the linked [Historical Language Notes](docs/historical-language-notes.md) separate dictionary-specific evidence, broader Jesuit-print patterns, variable features, project observations, and source provenance. The notes incorporate the dictionary's own `f11`–`f12` key, a reproducible NINJAL headword-sequence snapshot, and cited research on long-*o* and long-*u* marks, `q` sequences, `u/v`, yotsugana, spacing, long `ſ`, and Early Modern Portuguese. Neither document authorizes normalization: all proposed contextual corrections still return to the enlarged scan.

NINJAL's CC BY 4.0 [Nippo Jisho Headword Data](docs/headword-data.md), version 202510, has been downloaded, unpacked, checksum-verified, and documented. Its 32,878 source-order records provide dictionary-wide coverage and reading checks unavailable from Wikisource. It remains an attributed external reference because it is based on the Bodleian copy and contains editorial normalization; the Gallica scan remains authoritative.

The provisional layer boundary has now been clarified. Stage 1 will preserve observable page evidence in physical order and will not ordinarily assert entry boundaries or logical reassignment of displaced text. Stage 2 will add those interpretations by linking back to stable Stage 1 spans. The lowercase but structurally independent `aburamono` and the physically displaced `(grande.` are the current test cases for this distinction.

The uncertainty policy is intentionally lightweight. Context may support an ordinary secure transcription, as with the fold-crossed `Aa vobitataxiya.` passage on `f13`; explicit markers are reserved for readings that remain materially disputable or illegible. The format must permit more detailed notes without imposing character-level confidence metadata on routine work.

Targeted enlargement is nevertheless a routine review step for any locally difficult span, regardless of the standard tile size. Reviewers return to the surrounding context after enlargement; only doubt that survives both views is marked in the transcription.

The adopted [page-transcription format](docs/page-transcription-format-v1-candidate.md) has now been exercised in a [nine-page corpus](pilot/format-v1-trial/README.md). The six-page adoption baseline has been extended by sequential pages `bnf-f0015`–`bnf-f0017`; the complete physical-order records now comprise 818 physical lines. The [Level 1 Markdown authoring form](docs/level1-markdown-candidate.md) regenerates the validated JSON and page views deterministically.

The compact files preserve stable physical-line references, typeface, relative indentation, page furniture, and exceptional placement while remaining directly readable. JSON is generated machine interchange rather than a hand-authoring format. A small structural test remains only to confirm that Level 1 has not discarded necessary evidence; designing Level 2 and later layers is a secondary concern. Lightweight uncertainty notation has still not encountered a genuinely unresolved reading and will be added only when evidence requires it.

Level 1 review is explicitly contextual rather than linguistically blind. After the initial visual transcription, separate Japanese/romanization and Portuguese-context passes flag suspicious readings; each proposed correction is then confirmed against the scan. Segmentation, normalization, grammatical analysis, and translation remain outside Level 1. Production metadata uses `visual_draft`, `context_reviewed`, and `scan_confirmed` for these checkpoints.

A follow-up [contextual-review experiment](pilot/contextual-review/f0248-f0643.md) completed both passes on `f248` and the less familiar `f643`. It found no additional correction on `f248` and two on `f643` (`bocetinha`, `deſiguaes`). Several linguistically attractive changes were rejected after scan confirmation, supporting the separation of diagnostic contextual review from source adjudication.

The decisive [f249–f250 production simulation](pilot/production-simulation/f0249-f0250.md) added 196 physical lines without requiring new syntax. Measured pass time was 10 minutes for two pages, but a completion audit and later reader review found additional errors, so this is not yet a final-quality rate. Sixteen initial readings were corrected while contextually odd but visibly printed forms were preserved. The post-simulation corrections from `vgogu` to printed `vgoqu` and from `inacu` to `macu` demonstrate that the Japanese morphology and bilingual-context passes must actively test even visually plausible forms. Cross-page catchwords and a second displaced-text example also remained auditable.

The first strengthened production re-review was evaluated through human review on [`f14`](pilot/production-review/bnf-f0014.md). Although the pre-review found three corrections and ended with a nominal zero-new-candidate sweep, the human comparison found thirteen more. These include modern-language regularizations (`baxo`, `touçinho`, `mu`), exact-spacing errors, long-`ſ` and `z` confusions, and a silently expanded `ẽ` abbreviation. This greatly exceeded the two-or-three correction target. The corrections have now been applied and the project owner has confirmed both columns and the furniture, making `f14` the first `human_checked` page.

The next page, [`f15`](pilot/production-review/bnf-f0015.md), was transcribed directly from the scan with additional independent passes: forward token alignment, Japanese, Portuguese, bilingual context, reverse-order glyph inspection, separate mark inspection, headword coverage, and a fresh final sweep. Those passes caught several errors before handoff, but the project owner's comparison still found ten corrections, including `Acano`, `menhaã`, `Aca muſubu`, `briguigoĩs`, `comballas`, `dedia`, `faru`, and `aſsi`. Repetition alone therefore did not reach the working target. Both corrected column units now await recheck; page furniture remains pending.

Sequential [`f16`](pilot/production-review/bnf-f0016.md) trials an independent second reading instead of further anchored repetition. Its two proposals contained useful partial observations, but neither final string survived full human review: `Sagui yiqu` became `Sagui yuqu`, and `Sõ-` / `fir` became `Sõ-` / `tir`. The project owner's first checkpoint prompted a renewed full-page audit that found seven missed occurrences; completed column review and a same-page repetition sweep then found twenty-two more, including mixed `ſs`, historical Portuguese spelling and spacing, and Japanese-context errors such as `Qinomiga`, `Acariſaqi`, `yuqu`, `ſuru`, and `Tçuqi`. The audit also made two unnecessary changes from `-` to `=`; these remain reverted under the provisional uniform `-` convention. Both corrected columns await recheck, so final recall remains open; the independent-comparison method did not meet the working quality target.

The next sequential page, [`f17`](pilot/production-review/bnf-f0017.md), applies the independent comparison together with mandatory Japanese, Portuguese, glyph, mark, and right-edge passes. Before handoff these checks caught modernized Portuguese (`conſideração`, `ſaluação`, `nascimento`), four unprinted division signs, and context-sensitive Japanese readings including `fuqeru`, `Acugaiuo`, and `Acuno`. All 40 expected NINJAL headwords are represented. The page is `scan_confirmed`, and its two columns and furniture await human review; its true correction yield remains open until that comparison.

A generated [dictionary-wide human review interface](pilot/human-review/README.md) now covers all 651 acquired leaves. The nine Level 1 pages present a high-resolution scan beside rendered or literal transcription; the other 642 leaves retain immediate scan access and an explicit `unprocessed` state. Previous/next controls, direct leaf entry, stable page-and-column links, and reloadable generated data allow transcription and human checking to proceed asynchronously. The review registry now contains 27 resumable units: all three `f14` units are checked, both corrected `f15` and `f16` columns need recheck, and the new `f17` units await their first human check. Each physical line can copy its stable reference and current text into the project chat, which remains the intentionally simple correction interface.

## Current objective

Complete the human check of newly transcribed `f17`, recheck the corrected `f16` and `f15` columns, and continue the first bounded sequential Level 1 production batch. The immediate objective is repeatable quality control supporting:

1. A page-oriented reading and verification view
2. Efficient source-faithful editing in physical order
3. Stable references and retained evidence sufficient for later work without designing later layers now

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
- [x] Publish version 1 of the page-transcription specification.
- [x] Generate a dictionary-wide asynchronous human-review interface.
- [ ] Decide the initial transcription provenance and licensing policy.

## Production progress

The Level 1 corpus contains nine complete pages and 818 physical lines. `f14` is human-checked; sequential `f15` and `f16` have both been corrected after human comparison and their columns await recheck; `f17` is scan-confirmed and awaits its first human comparison. `f249` and `f250` retain the earlier production `scan_confirmed` status but should be re-evaluated against the revised procedure. The other 642 acquired leaves appear as `unprocessed` in the review UI.

## Next phase

Complete and evaluate human review on `f16`, using the human-confirmed page to score proposal precision and missed-error recall; recheck f15 and continue sequentially. Newly generated pages can appear in the same corpus UI while earlier pages are still being checked. A smaller end-to-end pilot will separately test the entry schema, Japanese restoration, translation, and public-edition requirements without delaying publishable Level 1 progress.
