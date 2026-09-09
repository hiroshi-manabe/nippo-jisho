# Italic double-s review through f200

This temporary review distinguishes two appearances previously transcribed as
italic `ſſ`: the β-like ligature (proposed `ß`) and two long-s forms (`ſſ`).
`ß` is a diplomatic glyph convention here, not German spelling. Existing `ſs`,
roman-type occurrences, and pages after f200 are outside this campaign.

The user completed ordinary review through f200 before this candidate set was
frozen. AI visual suggestions are provisional, not training labels. Only the
human-submitted result authorizes transcription changes. After application,
these distinctions may be used in a new OCR training dataset.

## Review UI

Open `ss-review.html` from the main overview. Checked means retain `ſſ`;
unchecked means change to `ß`. AI suggestions preselect the checked minority.
Each item highlights the target in its text, supplies a scan strip, and offers
an enlarged surrounding-lines view and a full-scan link. Arrow keys move
between items; Space toggles. Choices persist on the current device.

Copy results, open an Issue, and paste the JSON into its empty body. The URL
contains only the title, never the potentially long payload. Copy failure leaves
a selectable text fallback. Submission describes the entire frozen set, not
just visited groups: review all groups before submitting.

## Frozen data and processing

`site/assets/ss-review/candidates.json` records ordered occurrences, line text,
positions, text versions and scan assets. The compact export has format
`nippo-italic-ss-review`, version 1, a baseline fingerprint, total count,
`default: "ß"`, and `keep` (zero-based indexes of checked occurrences).

The ordinary Issue processor recognizes this format and expands it into its
normal page corrections. Multiple replacements on a line run right-to-left;
the normal processor preserves typefaces and handles stale text rather than
silently overwriting it. Wrong fingerprints, counts, duplicate indexes and
out-of-range indexes are rejected. Human changes remain authoritative.

`scripts/prepare_ss_review.py` uses the public corpus and local native scans.
`scripts/ss_review_classification.json` freezes the visual suggestions and the
candidate fingerprint. Do not regenerate a different candidate set over a live
review. Geometry-only improvements may keep the fingerprint and saved choices.
The generator is intentionally not part of the routine site build: published
review candidates must not change as ordinary transcription work continues.
