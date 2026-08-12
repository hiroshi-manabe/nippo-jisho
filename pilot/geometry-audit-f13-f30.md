# Geometry audit pilot: f13–f30

Date: 2026-08-12

This pilot improved reconstructed line geometry for ordinary two-column pages through f30. It was prompted by f24, whose old broad linear calibration placed `c1-l011` about one line too high and whose column rectangles cut useful text from their right edges. Its original completion claim was withdrawn after the lower part of the `g` in f20/c1-l007 was found clipped: reduced contact sheets and representative browser checks cannot establish line-level completeness.

## Audited pages

The 13 ordinary-layout pages were audited and recalibrated: f13–f17, f20, f22–f24, f26–f28, and f30. For all 26 columns:

- the horizontal rectangle was checked against the full-resolution master;
- line centres were snapped to visible ink rather than accepted from uniform interpolation alone;
- every generated strip was inspected on a complete contact sheet;
- representative crops were checked in the browser-facing interface;
- overlap was retained wherever it protected ascenders, descenders, or displaced type.

These columns remain reconstructed, provisional geometry and carry only the legacy `contact_sheet_reviewed` state. They must not be treated as fully verified until every crop has been opened at normal browser-review scale and adjusted as necessary. The calibration format and generator support `centre_overrides`; manual adjustment of any or every line is an explicit option.

## Deferred exceptional layouts

f18, f19, f21, f25, and f29 contain internal alphabet transitions, enlarged initials, or separately calibrated regions. They were excluded from the initial bulk recalibration, but the required next audit is line-by-line rather than layout-class based. They can therefore be checked in the same f13–f30 sequence: unusual layout affects the starting rectangle, not the final acceptance rule.

## Pilot result

The bulk procedure exposed errors beyond f24, particularly overly broad or displaced column envelopes on several leaves and top anchors that had captured a running header or begun approximately one physical line too high. It produced better starting geometry, not completed geometry. Existing pages must now be reopened line by line. For future pages, the rectangle actually used during transcription must be saved immediately as UI geometry so this reconstruction problem does not recur.
