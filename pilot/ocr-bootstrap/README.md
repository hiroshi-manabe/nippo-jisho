# OCR scan-bootstrap candidates

This directory preserves machine-provisional Level 1 candidates made directly
from native scans by `scripts/bootstrap_ocr_level1.py`.

The `f0238-f0247` batch passed the held-out structural and recognition gates,
but none of these files is canonical. Each embedded page explicitly records
`physical_lineation_checked: false`; page furniture, enlarged initials, every
line crop, and the diplomatic reading still require scan-based review before
promotion into `pilot/format-v1-trial/`. The public interface exposes them as
clearly labeled provisional review material without changing that status.

Method, benchmark figures, limitations, and promotion requirements are in
[`docs/ocr-scan-bootstrap.md`](../../docs/ocr-scan-bootstrap.md).

The `reference-f0248-f0250` directory freezes the existing near-range pages
before dictionary-wide generation. Bulk candidates are preserved in their own
range directory with a manifest that distinguishes ordinary pages from
structural quarantines; neither set is canonical merely because it exists.

The completed `f0251-f0642` batch contains all 392 requested leaves: 366
ordinary two-column candidates and 26 quarantines, with no inference failures.
Together with `f0238-f0247`, scan-first candidate data now exists for all 402
previously unstructured dictionary leaves in `f238`–`f642` other than the
already structured controls `f248`–`f250`.
