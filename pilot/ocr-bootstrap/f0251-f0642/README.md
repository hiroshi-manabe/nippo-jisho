# OCR bootstrap candidates f0251–f0642

This directory preserves 392 machine-provisional page packages
generated directly from the native scans. They are evidence-bearing review
candidates, not canonical Level 1 pages and not human-checked transcriptions.

- Ordinary two-column candidates: 366
- Structurally quarantined candidates: 26
- Inference failures: 0
- Provisional body rows: 36,745
- Held-out body-row recall: 99.92%
- Held-out body-row precision: 99.61%
- Held-out diplomatic character accuracy: 97.14%

`pages/` contains every target candidate. `controls/` contains fresh OCR-derived
candidates for the frozen near-range control pages; the pre-bootstrap originals
live in `../reference-f0248-f0250/`. `manifest.json` lists the eligible pages,
quarantines with reasons, failures, totals, and the benchmark gate.

Every candidate retains `physical_lineation_checked: false`. Promotion still
requires complete visual confirmation of physical rows, page furniture, enlarged
initials, crop readability, and the diplomatic transcription. The candidates are
visible and editable in the public review UI, but that exposure is not promotion;
structural quarantines remain separately marked with their recorded reasons.
