# Legacy external-AI geometry guide

This document records the acceptance rules used by the external-AI workflow retired on 2026-08-30. It is preserved to explain historical return files and imported provenance, not as an active assignment.

The goal was not a regular grid. The goal was an isolated image from which the complete assigned physical line could actually be read.

Initial rectangles are proposals reconstructed by the existing project process and may be horizontally or vertically wrong. A line can be correctly identified while its first or last glyph remains outside the rectangle. The f31 return demonstrated this failure in column 2: many right-hand endings were clipped even though its vertical positions were useful.

## Four-edge acceptance

Inspect the actual isolated `crop` for every line, not merely the full page or `column_box_xyxy`. Confirm that:

1. the first printed glyph is wholly visible at the left edge;
2. the last printed glyph and every line-end mark are wholly visible at the right edge;
3. accents, ascenders, displaced marks, and other upper ink are visible;
4. descenders and other lower ink are visible.

Do not infer horizontal completeness from successful OCR, line identity, or vertical centering. Inspect the first and last glyph against the full-resolution page before accepting the initial rectangle.

For an ordinary page, first determine conservative column-wide left and right boundaries, normally slightly beyond both printed rules. Reuse them only when every isolated line passes the edge check. An insufficient width must not be repeated because it happens to work for a neighboring line or the other column. Page skew matters, and column 2 is particularly liable to lose its outer/right endings.

A conservative rule-to-rule crop is preferable when tighter per-line width adds no practical value. Neighboring-line overlap is allowed when required to preserve complete glyphs. Avoid unnecessary empty space when a natural boundary is clear.

`context_crop` must contain `crop` and retain enough surrounding material to prove that the assigned line—not an adjacent row—is the focus. Resolve every supplied `validation_flag`; in particular, `context_crop_does_not_contain_crop` means the context rectangle itself must be enlarged or moved.

After all individual lines pass, perform a separate top-to-bottom sweep of each returned column. Look for repeated clipped edges, wrong line association, missing large-initial ink, and especially lost outer/right endings in column 2.

## Lineation discrepancies

The canonical lineation can be wrong. If the scan contains a different number or order of physical lines:

- do not invent a blank continuation;
- do not attach the wrong image to an expected ID;
- do not silently shift all following IDs;
- do not renumber the response.

Mark the response incomplete, identify the first divergence, and describe the printed evidence in a note. Stop forcing the affected column into the supplied sequence. The project will correct the canonical lineation and regenerate or rebase the task.

The former separate `lar.` row on f94 is the control example: the scan prints `acumu` as the complete line, so inserting a nonexistent continuation shifted the remainder of the column.

## Known exceptional flags

The prepared task set contains ten explicit `context_crop_does_not_contain_crop` flags:

- `f103/c1b-l001`
- `f149/c1b-l001`
- `f153/c1b-l001`
- `f155/c1b-l001`
- `f160/c1f-l001`
- `f181/c1b-l001`
- `f186/c1b-l001`
- `f204/c1b-l001`
- `f216/c2b-l001`
- `f230/c1b-l001`

Several pages combine multiple transcription zones into one physical-column task. Preserve the order specified by `zone_ids` while still checking the physical scan independently.
