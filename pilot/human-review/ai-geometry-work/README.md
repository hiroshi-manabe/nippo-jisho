# External-AI line-geometry and text review

Files in this directory are task records and returned reviews, not automatically approved geometry or transcription. Initial rectangles are proposals reconstructed by the existing project process and may be horizontally or vertically wrong. In particular, a line can be vertically correct and readily identifiable while its first or last glyph is outside the proposed rectangle. The f31 return demonstrated this failure in column 2: many right-hand line endings were clipped even though the vertical positions were useful.

## Default assignment: geometry and independent text

The default response mode is `geometry_and_text`. The assigned AI has two related but distinct jobs for every physical body line:

1. inspect the isolated crop and full page at a practical enlarged size;
2. read the printed line independently into `observed_text`, before consulting the canonical transcription;
3. adjust `centre_y`, `crop`, and `context_crop` so the complete printed line is visible;
4. only then compare the independent reading with the canonical line and replace the pending judgments.

The independent reading must preserve what is visibly printed. Do not modernize historical spelling, regularize diacritics or long `ſ`, silently repair the language, copy the canonical line, or fill an uncertain character merely to make the response look complete. Use an empty string with `match: unreadable` when nothing can be read; use `assessment: uncertain` and a short `note` when a reading is genuinely doubtful.

Allowed judgments are:

- `match`: `strong`, `partial`, `mismatch`, or `unreadable`;
- `assessment`: `readable` or `uncertain`;
- `geometry_action`: `accepted_initial` or `adjusted`.

An optional `note` should explain only genuine uncertainty, an exceptional crop decision, or a possible lineation problem. A completed default response uses `response_status: completed_independent_ai_line_review`, `geometry_review_status: completed`, and `text_review_status: completed`. Every body-line record must have non-null `observed_text` and no `pending` value.

`geometry_only` is an explicit fallback, not the normal assignment. Use it only when the geometry has been inspected credibly but a complete independent reading cannot be supplied. Such a response must state `geometry_review_status: completed` and `text_review_status: not_completed`; it must not disguise approximate OCR or copied canonical text as an independent review. Neither response mode authorizes changes to the canonical Level 1 transcription. Geometry may be imported after validation, while every textual disagreement remains advisory until it is separately adjudicated against the scan.

## Mandatory crop acceptance check

For **every line**, inspect the actual isolated `crop`, not merely the full page or the proposed `column_box_xyxy`, and confirm all four edges:

1. the first printed glyph is wholly visible at the left edge;
2. the last printed glyph and every line-end mark are wholly visible at the right edge;
3. accents, ascenders, and any ink extending above the nominal line are visible;
4. descenders and any ink extending below the nominal line are visible.

Do not infer horizontal completeness from successful line identification or good vertical centering. For an ordinary page, first determine conservative column-wide left and right boundaries, normally extending slightly beyond both printed column rules. Those boundaries may be reused when every line passes the first/last-glyph check; an insufficient fixed width must never be reused merely because it works for neighboring lines or the other column. The page may be skewed, and column 2 is especially liable to lose its outer/right endings. Inspect the first and last glyph against the full-resolution page before setting `geometry_action` to `accepted_initial`.

A conservative crop extending slightly beyond both printed column rules is preferred when a tight per-line boundary adds no practical value. Neighboring-line overlap is allowed when needed to preserve complete glyphs. `context_crop` must both contain `crop` and retain enough surrounding material to verify that the assigned line—not an adjacent line—is the focus.

After all individual lines are complete, perform one final top-to-bottom sweep of each column using the returned isolated crops. This is a separate completion step: explicitly look for a repeated clipped edge, paying particular attention to the outer/right edge of column 2. A response is not complete until this column-level sweep finds no missing first or last glyphs.

Any `validation_flags` present in the initial task must be resolved before completion. In particular, `context_crop_does_not_contain_crop` means that the enlarged normal crop cannot be reached by expanding to the current context view; the context rectangle must be corrected to contain it.

## Lineation discrepancies

The expected line IDs are stable references, but the canonical lineation can be wrong. If the scan contains a different number or order of physical lines from the task, do **not** invent a blank continuation, attach the wrong image to an ID, silently shift all following IDs, or renumber the response. Mark the response incomplete, record the first point of divergence and the printed evidence in a note, and stop forcing the affected column into the expected sequence. The project will correct the canonical lineation and regenerate or rebase the task before import. The false separate `lar.` line formerly present in f94 is the control example for this rule.

The reviewed f30 output in [`../ai-geometry-examples/bnf-f0030.json`](../ai-geometry-examples/bnf-f0030.json) demonstrates the completed shape. Its accompanying README defines the rectangle conventions and visual acceptance rule.

After validation, a completed response may be imported with `scripts/import_ai_geometry_review.py`. Imported columns normally use the provenance state `ai_line_by_line_checked`, which accepts the delegated line-level geometry without claiming human verification. A response whose rectangles pass an independent full contact-sheet audit but whose mechanical edit pattern does not credibly demonstrate individual line-level decisions must instead be imported with `--visual-review ai_bulk_geometry_sanity_checked`. This preserves both the usable geometry and the limitation of the review evidence. Independent textual disagreements remain advisory and must be adjudicated separately against the scan before any Level 1 correction. An `observed_text` field that merely reproduces every canonical line verbatim is useful for line identification but is not independent textual evidence.

If a returned file explicitly marks `geometry_review_status` as `completed` and `text_review_status` as `not_completed`, it may be imported with `--allow-geometry-only` after the same crop audit. This does not promote blank `observed_text` fields into textual evidence, and it does not imply that the transcription has been reviewed. A default `geometry_and_text` response likewise supplies candidates rather than canonical corrections: its independent readings must still be checked against the scan before application.

## Task-record coverage

Task records are retained for `f31`–`f237`, `f248`–`f250`, and `f643`, including already returned and imported work; the presence of a base JSON file therefore does not by itself mean that its page is still pending. The complete set contains 211 pages and 19,825 body lines. At preparation time, every task was checked for exact page coverage, unique line IDs, current source-image and transcription hashes, source-image bounds, null independent readings, and pending judgments. Those hashes deliberately make a task stale when its canonical transcription changes.

The newly prepared outstanding batch comprises `f101`–`f237`, `f248`–`f250`, and `f643`: 141 pages and 13,253 body lines. It contains ten explicit `context_crop_does_not_contain_crop` flags that the reviewer must resolve: `f103/c1b-l001`, `f149/c1b-l001`, `f153/c1b-l001`, `f155/c1b-l001`, `f160/c1f-l001`, `f181/c1b-l001`, `f186/c1b-l001`, `f204/c1b-l001`, `f216/c2b-l001`, and `f230/c1b-l001`. Several pages aggregate multiple transcription zones into one physical-column task; their `zone_ids` preserve the required order.

## Imported batches

The returned `f52`–`f66` records were imported on 2026-08-13. Because every line was reported as a strong match while the rectangles followed a largely mechanical pattern, their geometry is recorded conservatively as `ai_bulk_geometry_sanity_checked`, after validation and complete contact-sheet generation, rather than as independently demonstrated line-by-line checking. Their 17 textual disagreements were adjudicated separately against enlarged scan crops: 15 supported corrections were applied, while the uncertain `f59/c1-l044` plant-name reading and the incomplete `f66/c1-l035` observation were not treated as independent evidence.

The revised `f72`–`f85` submissions were imported on 2026-08-14 after an earlier low-quality return was rejected. All 1,327 rectangles passed structural validation and an independent 28-column contact-sheet audit, including explicit four-edge and column-2 outer-edge checks. Because the returned files omit per-line `geometry_action` evidence and retain partially standardized crop dimensions, the usable geometry is recorded conservatively as `ai_bulk_geometry_sanity_checked`. Four advisory readings on `f72` and `f75` were independently confirmed and applied. The highly corrupted `observed_text` in the `f77`–`f85` rereviews was not treated as transcription evidence; those files contribute geometry only.

The `f86`–`f100` submissions were processed on 2026-08-16. Their 1,414 rectangles passed a complete 30-column contact-sheet and line-to-text sanity sweep, but their fixed horizontal bounds repeated the earlier clipped-edge risk; all were therefore expanded to audited rule-to-rule coverage and recorded as `external_ai_width_rechecked`. The supplied readings were too pervasively OCR-like to constitute a completed independent text review, so the response files explicitly record `text_review_status: not_completed`. Thirteen compact candidate differences were independently confirmed from enlarged scans and applied. The geometry check also exposed a false f94 column-1 line: printed `acumu` has no separate continuation `lar.`, so the canonical column and its reviewed geometry now contain the actual 47 physical rows.
