# External-AI import and provenance log

This is project-maintainer documentation. It is not part of the external reviewer’s normal assignment.

## Import policy

A returned file is not automatically approved geometry or transcription. Validate structure, bounds, source hashes, line IDs, response status, and the visual result before import.

A completed response may be imported with `scripts/import_ai_geometry_review.py`. Geometry that credibly demonstrates individual line-level inspection normally receives provenance `ai_line_by_line_checked`. A response whose rectangles pass an independent full contact-sheet audit but whose edit pattern does not demonstrate line-by-line judgment must instead use `--visual-review ai_bulk_geometry_sanity_checked`.

A response explicitly completed as geometry-only may be imported with `--allow-geometry-only` after the same crop audit. This does not promote blank `observed_text` fields into textual evidence and does not imply that the transcription has been reviewed.

Independent textual disagreements remain advisory. Apply a Level 1 correction only after separate scan adjudication. A default `geometry_and_text` response supplies candidates, not canonical amendments.

## Task-record coverage

Base task records are retained for `f31`–`f237`, `f248`–`f250`, and `f643`, including returned and imported pages. The complete set contains 211 pages and 19,825 body lines. At preparation time, each task had exact page coverage, unique line IDs, current source-image and transcription hashes, in-bounds rectangles, null independent readings, and pending judgments.

The later prepared range `f101`–`f237`, `f248`–`f250`, and `f643` contains 141 pages and 13,253 body lines. A file’s presence does not establish its current workflow state; consult its response status, reviewed variants, and import history.

## Imported batches

### f44–f46 geometry rereviews

The stricter geometry-only rereviews were imported on 2026-08-16 after the first returns proved insufficiently centered. All 278 body-line rectangles use the revised vertical positions while retaining previously audited conservative horizontal coverage. Human adjudication established that lower-right `poſito` on f46 is a separate physical line continuing `depoſito` from `c2-l046`, not furniture or a catchword; it is therefore `c2-l047`. No independent text readings were supplied or applied.

### f52–f66

The returns were imported on 2026-08-13. Because every line was reported as a strong match while the rectangles followed a largely mechanical pattern, their geometry is recorded as `ai_bulk_geometry_sanity_checked` after validation and complete contact-sheet generation. Their 17 textual disagreements were adjudicated separately: 15 supported corrections were applied, while the uncertain `f59/c1-l044` plant name and incomplete `f66/c1-l035` observation were not treated as independent evidence.

### f72–f85

Revised submissions were imported on 2026-08-14 after an earlier low-quality return was rejected. All 1,327 rectangles passed structural validation and a 28-column contact-sheet audit. Because the files omitted per-line `geometry_action` evidence and retained partially standardized dimensions, the geometry is recorded as `ai_bulk_geometry_sanity_checked`. Four advisory readings on f72 and f75 were independently confirmed and applied. The highly corrupted `observed_text` in the f77–f85 rereviews was not treated as transcription evidence.

### f86–f100

The submissions were processed on 2026-08-16. Their 1,414 rectangles passed a 30-column contact-sheet and line-to-text sanity sweep, but fixed horizontal bounds repeated the earlier clipped-edge risk. All were expanded to audited rule-to-rule coverage and recorded as `external_ai_width_rechecked`. The readings were too OCR-like to constitute completed independent text review, so those files record `text_review_status: not_completed`. Thirteen compact candidate differences were independently confirmed and applied. Geometry review also exposed the false f94 `lar.` row described in the geometry guide.
