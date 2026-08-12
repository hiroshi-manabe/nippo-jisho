# Geometry audit pilot: f13–f30

Date: 2026-08-12

This pilot applies the stronger line-image acceptance procedure to ordinary two-column pages through f30. It was prompted by f24, whose old broad linear calibration placed `c1-l011` about one line too high and whose column rectangles cut useful text from their right edges.

## Audited pages

The 13 ordinary-layout pages were audited and recalibrated: f13–f17, f20, f22–f24, f26–f28, and f30. For all 26 columns:

- the horizontal rectangle was checked against the full-resolution master;
- line centres were snapped to visible ink rather than accepted from uniform interpolation alone;
- every generated strip was inspected on a complete contact sheet;
- the top, middle, bottom, and locally irregular crops were checked in the browser-facing interface;
- overlap was retained wherever it protected ascenders, descenders, or displaced type.

These columns carry the review state `line_and_browser_reviewed`. The pilot did not require a final per-line centre override, but the calibration format and generator now support `centre_overrides`; manual adjustment of any or every line remains an explicit option.

## Deferred exceptional layouts

f18, f19, f21, f25, and f29 contain internal alphabet transitions, enlarged initials, or separately calibrated regions. They were deliberately excluded from this ordinary-page pilot and retain their previous review state. They should be audited as the next exceptional-layout batch rather than silently treated as ordinary columns.

## Pilot result

The stronger procedure exposed errors beyond f24, particularly overly broad or displaced column envelopes on several leaves and top anchors that had captured a running header or begun approximately one physical line too high. The scan-snapped centres and explicit manual-override path are suitable for extending the audit to the remaining processed pages, with exceptional layouts handled separately.
