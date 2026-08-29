# Legacy AI line-review examples

The external-AI workflow was retired on 2026-08-30. These frozen examples remain for interpreting its archived evidence; they are not templates for current assignments.

## Recommended behavioral example: f53

[`../ai-geometry-work/bnf-f0053-reviewed.json`](../ai-geometry-work/bnf-f0053-reviewed.json) is a real completed external-AI return and was the recommended behavioral example. All 93 body lines have independently read `observed_text`. The return preserves visible disagreements with the then-canonical text, labels a materially abraded passage `uncertain`, and explains the exceptional tall crop needed for an enlarged initial rather than forcing that line into the ordinary geometry.

This is a historical return, frozen by Git at commit `340f4bb`. It predates the explicit `geometry_review_status`, `text_review_status`, and per-line `geometry_action` fields later required by [the response format](../ai-geometry-work/FORMAT.md). Its readings are evidence from that review, not automatically accepted Level 1 corrections.

## Structural specimen: f30

[`bnf-f0030.json`](bnf-f0030.json) preserves the final response shape and all 94 body-line records on an already reviewed page. It documents nesting, coordinate conventions, source/version metadata, and allowed field placement.

The f30 specimen combines canonical transcription with geometry that passed the project's text–image sanity check. Its `observed_text` values are therefore **reference values copied from the canonical transcription**, not the result of a blind reading. This is disclosed in the JSON itself. Do not imitate that provenance in a new response: write `observed_text` independently from the proposed crop before comparing it with the supplied canonical line.

## Historical response behaviour

For every physical line, the retired protocol required the responding AI to:

1. return `centre_y`, `crop`, and `context_crop` in native Gallica-master pixels;
2. inspect the isolated crop at full practical size and confirm that its left, right, top, and bottom edges contain all ink belonging to the assigned line;
3. compare the isolated crop with the full page and verify the complete first and last printed glyphs, including line-end marks;
4. read `observed_text` afresh from the image rather than copy the expected transcription;
5. classify the comparison as `strong`, `partial`, `mismatch`, or `unreadable`;
6. classify crop readability as `readable` or `uncertain`;
7. include `note` only when an exception or uncertainty needs explanation;
8. preserve the supplied `expected_line_version` without changing the canonical transcription;
9. finish with a top-to-bottom sweep of every returned crop in each column to detect a repeated clipped edge, especially the outer/right edge of column 2.

Both `crop` and `context_crop` use `[x, y, width, height]`. `column_box_xyxy` alone uses `[left, top, right, bottom]`, matching the existing tile configuration. A normal crop must contain the complete assigned line—including accents, ascenders, descenders, enlarged initials, and line-end marks—and must be contained by its context crop. Overlap with neighboring lines is allowed when it protects target ink. Correct vertical placement or successful line identification does not establish horizontal completeness. A conservative rule-to-rule width is preferable to a tight repeated width when page skew or long italic lines make the outer edge uncertain.

`match` concerns line identification, not diplomatic correctness. A recognizably aligned line may receive `strong` even when one difficult character differs. A disagreement in `observed_text` is a later transcription-review candidate; the geometry task must not modify Level 1 text.

The f30 specimen is now frozen with the archive and is not regenerated as canonical transcription or geometry changes.
