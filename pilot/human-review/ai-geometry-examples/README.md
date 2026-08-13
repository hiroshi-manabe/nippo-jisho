# AI line-geometry response example

[`bnf-f0030.json`](bnf-f0030.json) is the complete expected response shape for an AI asked to establish line geometry from `f31` onward. It contains all 94 body lines on the already reviewed `f30`, not merely a shortened schema illustration.

The example combines the current canonical f30 transcription with geometry that has passed the project's text–image sanity check. Its `observed_text` values are therefore **reference values copied from the canonical transcription**, not the result of a new blind reading. This is disclosed in the JSON itself. For a new page, the responding AI must write `observed_text` independently from the proposed crop before comparing it with the supplied canonical line.

## Required response behaviour

For every physical line, the responding AI must:

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

Regenerate the f30 exemplar after intentional changes to its canonical transcription or reviewed geometry:

```sh
python3 scripts/export_ai_geometry_example.py
```
