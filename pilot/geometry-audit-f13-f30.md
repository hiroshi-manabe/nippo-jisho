# Geometry audit pilot: f13–f30

Date: 2026-08-12

This audit completed a line-by-line re-verification of reconstructed geometry from f13 through f30. It was prompted by f24, whose old broad linear calibration placed `c1-l011` about one line too high, and by the clipped descender in f20/c1-l007. Those failures established that reduced contact sheets and representative browser checks cannot establish line-level completeness.

## Audited pages and acceptance method

All 18 pages, f13–f30 inclusive, were audited: 1,655 individual line crops across 36 columns. This includes the exceptional internal sections and enlarged initials on f18, f19, f21, f25, and f29. For every line:

- the horizontal rectangle was checked against the full-resolution master;
- line centres were snapped to visible ink rather than accepted from uniform interpolation alone;
- the generated strip was inspected individually at native/full row width;
- the complete target line, including ascenders, descenders, accents, and enlarged initials, had to be readable;
- overlap with adjacent lines was accepted when it protected target glyphs;
- horizontal coverage had to include the complete printed line in its column or exceptional region.

The audit must judge each crop in isolation. Adjacent strips in a stacked sheet can visually supply ink omitted from the target strip and create a false impression of completeness. This failure was confirmed at f24/c2-l023, where the following strip made the clipped lower stroke of the `g` in `folgar` appear present. That line now has an explicit taller crop.

The ordinary generated crops now use 30 source pixels of vertical overlap instead of 18. Existing enlarged-initial overrides remain in force where one ordinary-height crop cannot contain the target. The calibration format and generator continue to support `centre_overrides` and per-line `crop_overrides`; manual adjustment of any line remains available when future review exposes a local exception.

## Exceptional layouts

f18, f19, f21, f25, and f29 were reviewed by the same line-level rule as ordinary pages. Their section-specific rectangles and enlarged-initial overrides were retained because unusual layout changes the appropriate source rectangle, not the final acceptance rule.

## Result

All f13–f30 columns now carry `line_by_line_reverified` with the audit date. The increased overlap restores the full `g` in f20/c1-l007 and protects similar displaced type throughout the range. This status records crop readability, not transcription correctness. For future pages, the rectangle actually used while reading each line must be saved immediately as UI geometry so this reconstruction problem does not recur.
