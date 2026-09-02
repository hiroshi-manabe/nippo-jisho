# OCR scan-bootstrap candidates

This directory preserves machine-provisional Level 1 candidates made directly
from native scans by `scripts/bootstrap_ocr_level1.py`.

The `f0238-f0247` batch passed the held-out structural and recognition gates,
but none of these files is canonical. Each embedded page explicitly records
`physical_lineation_checked: false`; page furniture, enlarged initials, every
line crop, and the diplomatic reading still require scan-based review before
promotion into `pilot/format-v1-trial/` or the public review interface.

Method, benchmark figures, limitations, and promotion requirements are in
[`docs/ocr-scan-bootstrap.md`](../../docs/ocr-scan-bootstrap.md).
