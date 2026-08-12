# Pending AI line-geometry work

Files in this directory are task records, not approved geometry. Their rectangles are initial proposals reconstructed by the existing project process and may be horizontally or vertically wrong.

For each line, the assigned AI must inspect the proposed crop at full practical width, adjust `centre_y`, `crop`, and `context_crop` when necessary, and independently fill `observed_text` before consulting the canonical transcription. It must then replace the pending judgments as follows:

- `match`: `strong`, `partial`, `mismatch`, or `unreadable`;
- `assessment`: `readable` or `uncertain`;
- `geometry_action`: `accepted_initial` or `adjusted`.

An optional `note` should explain only genuine uncertainty or exceptional geometry. Completion requires every body-line record to have non-null `observed_text` and no `pending` value. It does not authorize changes to the canonical Level 1 transcription.

Any `validation_flags` present in the initial task must be resolved before completion. In particular, `context_crop_does_not_contain_crop` means that the enlarged normal crop cannot be reached by expanding to the current context view; the context rectangle must be corrected to contain it.

The reviewed f30 output in [`../ai-geometry-examples/bnf-f0030.json`](../ai-geometry-examples/bnf-f0030.json) demonstrates the completed shape. Its accompanying README defines the rectangle conventions and visual acceptance rule.

After validation, a completed response may be imported with `scripts/import_ai_geometry_review.py`. Imported columns use the provenance state `ai_line_by_line_checked`, which accepts the delegated line-level geometry without claiming human verification. Independent textual disagreements remain advisory and must be adjudicated separately against the scan before any Level 1 correction.
