# External-AI line review

This directory contains proposed tasks and returned reviews. Neither is automatically approved geometry or transcription.

## Assignment

The default assignment is `geometry_and_text`. For every physical body line:

1. inspect the full page and the isolated line at a practical enlarged size;
2. read the print independently into `observed_text` before consulting the canonical transcription;
3. adjust the line geometry until the complete printed line is comfortably readable;
4. compare the independent reading with the canonical line and finish the required judgments.

Treat each page as an independent completion unit. A normal `geometry_and_text` run should contain only one or two pages; a larger archive is a storage convenience, not an instruction to finish every enclosed page in one response. Write each `*-reviewed.json` as soon as that page meets the completion standard. If a later page cannot be finished, return the already completed page files and identify the unfinished page separately rather than withholding the whole batch.

When a scan exposes a genuine line-count, line-order, or displaced-text problem in the supplied canonical structure, stop adjudicating that page and report the discrepancy precisely. Other pages in the assignment may still be completed independently. The project will repair and regenerate the affected page before asking for a new review.

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

- [Response format](FORMAT.md): fields, allowed values, completion states, hashes, and the examples.
- [Geometry guide](GEOMETRY-GUIDE.md): crop acceptance, page skew, overlap, validation flags, and lineation discrepancies.
- [Project import log](IMPORT-LOG.md): project-side validation, provenance, coverage, and earlier batch outcomes. This is background for maintainers, not part of the reviewer’s normal assignment.

Start with the [example guide](../ai-geometry-examples/README.md). The completed f53 return is the recommended model for actual review behavior; f30 is retained only as a current structural and coordinate specimen.
