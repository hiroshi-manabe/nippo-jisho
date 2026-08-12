# AI line-geometry response example

[`bnf-f0030.json`](bnf-f0030.json) is the complete expected response shape for an AI asked to establish line geometry from `f31` onward. It contains all 94 body lines on the already reviewed `f30`, not merely a shortened schema illustration.

The example combines the current canonical f30 transcription with geometry that has passed the project's text–image sanity check. Its `observed_text` values are therefore **reference values copied from the canonical transcription**, not the result of a new blind reading. This is disclosed in the JSON itself. For a new page, the responding AI must write `observed_text` independently from the proposed crop before comparing it with the supplied canonical line.

## Required response behaviour

For every physical line, the responding AI must:

1. return `centre_y`, `crop`, and `context_crop` in native Gallica-master pixels;
2. read `observed_text` afresh from the image rather than copy the expected transcription;
3. classify the comparison as `strong`, `partial`, `mismatch`, or `unreadable`;
4. classify crop readability as `readable` or `uncertain`;
5. include `note` only when an exception or uncertainty needs explanation;
6. preserve the supplied `expected_line_version` without changing the canonical transcription.

Both `crop` and `context_crop` use `[x, y, width, height]`. `column_box_xyxy` alone uses `[left, top, right, bottom]`, matching the existing tile configuration. A normal crop must contain the complete assigned line—including accents, ascenders, descenders, enlarged initials, and line-end marks—and must be contained by its context crop. Overlap with neighboring lines is allowed when it protects target ink.

`match` concerns line identification, not diplomatic correctness. A recognizably aligned line may receive `strong` even when one difficult character differs. A disagreement in `observed_text` is a later transcription-review candidate; the geometry task must not modify Level 1 text.

Regenerate the f30 exemplar after intentional changes to its canonical transcription or reviewed geometry:

```sh
python3 scripts/export_ai_geometry_example.py
```
