# External-AI line review

This directory contains proposed tasks and returned reviews. Neither is automatically approved geometry or transcription.

## Assignment

The default assignment is `geometry_and_text`. For every physical body line:

1. inspect the full page and the isolated line at a practical enlarged size;
2. read the print independently into `observed_text` before consulting the canonical transcription;
3. adjust the line geometry until the complete printed line is comfortably readable;
4. compare the independent reading with the canonical line and finish the required judgments.

Use visual judgment. Uniform spacing, identical crop sizes, and mechanically reused rectangles are not goals. A good result may use conservative rule-to-rule width, local vertical overlap, or an exceptional line rectangle when the print requires it.

Preserve what is visibly printed: historical spelling, spacing, diacritics, short and long `s`, punctuation, and line division. Do not modernize, silently repair the language, copy the canonical line as an independent reading, or invent a character merely to complete the task. Uncertainty is valid evidence and should be reported explicitly.

## Completion standard

A completed default response must satisfy all of the following:

- every expected physical body line has a non-null independent reading and no pending judgment;
- each isolated crop contains the complete first and last glyph, every line-end mark, and all upper and lower ink;
- each context crop contains its line crop and enough surrounding print to establish line identity;
- a final top-to-bottom column sweep finds no repeated clipping or shifted line association;
- any supplied validation flag has been resolved;
- any genuine line-count or line-order discrepancy has been reported rather than forced into the expected IDs.

The scan decides the reading. Linguistic knowledge may identify a suspicious character, but it does not authorize normalization. Returned textual differences are advisory until this project adjudicates them separately against the scan. The reviewer must not edit the canonical Level 1 files.

`geometry_only` is an explicit fallback when geometry can be reviewed credibly but a complete independent transcription cannot be supplied. It must be labelled honestly; blank or copied text must not be presented as independent evidence.

## References

- [Response format](FORMAT.md): fields, allowed values, completion states, hashes, and the golden example.
- [Geometry guide](GEOMETRY-GUIDE.md): crop acceptance, page skew, overlap, validation flags, and lineation discrepancies.
- [Project import log](IMPORT-LOG.md): project-side validation, provenance, coverage, and earlier batch outcomes. This is background for maintainers, not part of the reviewer’s normal assignment.

The reviewed f30 example at [`../ai-geometry-examples/bnf-f0030.json`](../ai-geometry-examples/bnf-f0030.json) demonstrates the completed response shape.
