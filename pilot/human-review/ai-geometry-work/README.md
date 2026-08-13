# Pending AI line-geometry work

Files in this directory are task records, not approved geometry. Their rectangles are initial proposals reconstructed by the existing project process and may be horizontally or vertically wrong.

For each line, the assigned AI must inspect the proposed crop at full practical width, adjust `centre_y`, `crop`, and `context_crop` when necessary, and independently fill `observed_text` before consulting the canonical transcription. It must then replace the pending judgments as follows:

- `match`: `strong`, `partial`, `mismatch`, or `unreadable`;
- `assessment`: `readable` or `uncertain`;
- `geometry_action`: `accepted_initial` or `adjusted`.

An optional `note` should explain only genuine uncertainty or exceptional geometry. Completion requires every body-line record to have non-null `observed_text` and no `pending` value. It does not authorize changes to the canonical Level 1 transcription.

Any `validation_flags` present in the initial task must be resolved before completion. In particular, `context_crop_does_not_contain_crop` means that the enlarged normal crop cannot be reached by expanding to the current context view; the context rectangle must be corrected to contain it.

The reviewed f30 output in [`../ai-geometry-examples/bnf-f0030.json`](../ai-geometry-examples/bnf-f0030.json) demonstrates the completed shape. Its accompanying README defines the rectangle conventions and visual acceptance rule.

After validation, a completed response may be imported with `scripts/import_ai_geometry_review.py`. Imported columns normally use the provenance state `ai_line_by_line_checked`, which accepts the delegated line-level geometry without claiming human verification. A response whose rectangles pass an independent full contact-sheet audit but whose mechanical edit pattern does not credibly demonstrate individual line-level decisions must instead be imported with `--visual-review ai_bulk_geometry_sanity_checked`. This preserves both the usable geometry and the limitation of the review evidence. Independent textual disagreements remain advisory and must be adjudicated separately against the scan before any Level 1 correction. An `observed_text` field that merely reproduces every canonical line verbatim is useful for line identification but is not independent textual evidence.

If a returned file explicitly marks `geometry_review_status` as `completed` and `text_review_status` as `not_completed`, it may be imported with `--allow-geometry-only` after the same crop audit. This does not promote blank `observed_text` fields into textual evidence, and it does not imply that the transcription has been reviewed.

## Prepared task range

Pending task records are prepared for `f31` through `f100`. The `f32`–`f100` batch contains 69 pages and 6,482 body lines. Every task has been checked for exact page coverage, unique line IDs, current source-image and transcription hashes, source-image bounds, null independent readings, and pending judgments.

The initial geometry has four known containment flags that the reviewing AI must repair: `f33/c1b-l001`, `f36/c2b-l001`, `f62/c2b-l001`, and `f68/c2b-l001`. Twelve pages in this range aggregate multiple transcription zones into one physical-column task; their `zone_ids` preserve the required order.

## Imported batches

The returned `f52`–`f66` records were imported on 2026-08-13. Because every line was reported as a strong match while the rectangles followed a largely mechanical pattern, their geometry is recorded conservatively as `ai_bulk_geometry_sanity_checked`, after validation and complete contact-sheet generation, rather than as independently demonstrated line-by-line checking. Their 17 textual disagreements were adjudicated separately against enlarged scan crops: 15 supported corrections were applied, while the uncertain `f59/c1-l044` plant-name reading and the incomplete `f66/c1-l035` observation were not treated as independent evidence.
