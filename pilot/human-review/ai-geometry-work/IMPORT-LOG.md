# External-AI import and provenance log

This is project-maintainer documentation. It is not part of the external reviewer’s normal assignment.

## Import policy

A returned file is not automatically approved geometry or transcription. Validate structure, bounds, source hashes, line IDs, response status, and the visual result before import.

A completed response may be imported with `scripts/import_ai_geometry_review.py`. Geometry that credibly demonstrates individual line-level inspection normally receives provenance `ai_line_by_line_checked`. A response whose rectangles pass an independent full contact-sheet audit but whose edit pattern does not demonstrate line-by-line judgment must instead use `--visual-review ai_bulk_geometry_sanity_checked`.

A response explicitly completed as geometry-only may be imported with `--allow-geometry-only` after the same crop audit. This does not promote blank `observed_text` fields into textual evidence and does not imply that the transcription has been reviewed.

Independent textual disagreements remain advisory. Apply a Level 1 correction only after separate scan adjudication. A default `geometry_and_text` response supplies candidates, not canonical amendments.

If the canonical transcription changed after a completed response was prepared, geometry may be imported with `--allow-transcription-drift` only after those later text changes and the response's advisory readings have been separately adjudicated. The importer still requires exact reviewed line-ID coverage, valid rectangles, and the unchanged master-image hash. The flag does not assert that the old independent reading matches the newer canonical text.

## Task-record coverage

Base task records are retained for `f31`–`f237`, `f248`–`f250`, and `f643`, including returned and imported pages. The complete set contains 211 pages and 19,825 body lines. At preparation time, each task had exact page coverage, unique line IDs, current source-image and transcription hashes, in-bounds rectangles, null independent readings, and pending judgments.

The later prepared range `f101`–`f237`, `f248`–`f250`, and `f643` contains 141 pages and 13,253 body lines. A file’s presence does not establish its current workflow state; consult its response status, reviewed variants, and import history.

## Imported batches

### f51–f55 line-by-line rereviews

Fresh geometry-and-text returns were imported on 2026-08-19 after the original f52–f55 batch had only bulk-sanity provenance. All 466 body-line rectangles passed exact line-ID and bounds validation plus a complete strip-to-transcription association sweep; the new line-specific rectangles are recorded as `ai_line_by_line_checked`. The returns were based on commit `a945106`, immediately before Issue #47 changed unchecked `ſt` candidates to provisional short `st`. Geometry was therefore imported with explicit transcription-drift acknowledgement after the newer text and all advisory readings were separately adjudicated.

Thirty-eight physical lines contained scan-supported corrections: 1 on f51, 8 on f52, none on f53, 9 on f54, and 20 on f55. Clear additions, historical spellings, diacritics, Japanese romanization, punctuation, and missed letters were applied. Uncertain line-end hyphens, modernized spellings, and readings that merely reversed Issue #47's explicitly provisional `st` classification were not applied. The returned files remain the evidence for both accepted and rejected proposals; canonical amendments remain independently attributable through this import record and Git.

### f44–f46 geometry rereviews

The stricter geometry-only rereviews were imported on 2026-08-16 after the first returns proved insufficiently centered. All 278 body-line rectangles use the revised vertical positions while retaining previously audited conservative horizontal coverage. Human adjudication established that lower-right `poſito` on f46 is a separate physical line continuing `depoſito` from `c2-l046`, not furniture or a catchword; it is therefore `c2-l047`. No independent text readings were supplied or applied.

### f52–f66

The returns were imported on 2026-08-13. Because every line was reported as a strong match while the rectangles followed a largely mechanical pattern, their geometry is recorded as `ai_bulk_geometry_sanity_checked` after validation and complete contact-sheet generation. Their 17 textual disagreements were adjudicated separately: 15 supported corrections were applied, while the uncertain `f59/c1-l044` plant name and incomplete `f66/c1-l035` observation were not treated as independent evidence.

### f72–f85

Revised submissions were imported on 2026-08-14 after an earlier low-quality return was rejected. All 1,327 rectangles passed structural validation and a 28-column contact-sheet audit. Because the files omitted per-line `geometry_action` evidence and retained partially standardized dimensions, the geometry is recorded as `ai_bulk_geometry_sanity_checked`. Four advisory readings on f72 and f75 were independently confirmed and applied. The highly corrupted `observed_text` in the f77–f85 rereviews was not treated as transcription evidence.

### f86–f100

The submissions were processed on 2026-08-16. Their 1,414 rectangles passed a 30-column contact-sheet and line-to-text sanity sweep, but fixed horizontal bounds repeated the earlier clipped-edge risk. All were expanded to audited rule-to-rule coverage and recorded as `external_ai_width_rechecked`. The readings were too OCR-like to constitute completed independent text review, so those files record `text_review_status: not_completed`. Thirteen compact candidate differences were independently confirmed and applied. Geometry review also exposed the false f94 `lar.` row described in the geometry guide.

### f101–f105

The returns were adjudicated on 2026-08-18. The f101–f104 files retained almost every provisional rectangle unchanged and marked every reading as a strong match despite 160 differences from the canonical text, including many visibly or linguistically impossible forms. Their 375 rectangles nevertheless passed a complete contact-sheet line-association sweep. They were therefore imported as bulk-sanity geometry, expanded to conservative rule-to-rule horizontal coverage, and recorded as `external_ai_width_rechecked`; none of their textual differences was applied as independent evidence.

The f105 return was not imported. It correctly stopped after finding that both columns' provisional geometry begins one printed row below the canonical first line: the crop assigned to `c1-l001` shows `gotogia`, while the crop assigned to `c2-l001` shows `Chicco`. Its pending response is retained as evidence that the page must be re-registered or regenerated before review can continue.

All five pages were subsequently returned as fresh line-by-line rereviews on 2026-08-18. The second returns re-registered f105 correctly and supplied visibly line-specific vertical rectangles throughout f101–f105. A project-side native-scan sweep accepted the 469 line associations, retained the already audited conservative horizontal bounds, and found one remaining exception: the submitted f105 `c2-l047` crop ended after `Titulo do pr`, although the same physical line's lowered `cipio-` continued beneath it. That rectangle was extended downward manually before import was finalized. The rereviews replace the first returns as canonical geometry provenance. Their textual disagreements remained advisory; only separately scan-confirmed readings were applied, with the NINJAL headword list used as a diagnostic rather than as transcription authority.
