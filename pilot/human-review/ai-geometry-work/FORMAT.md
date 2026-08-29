# Legacy external-AI response format

This frozen reference defines the response format used by the external-AI workflow retired on 2026-08-30. It remains solely to interpret archived task and return files. The former assignment and its archival boundary are in [README.md](README.md); visual crop decisions are covered by [GEOMETRY-GUIDE.md](GEOMETRY-GUIDE.md).

## Default mode

The normal `default_response_mode` is `geometry_and_text`. A completed response uses:

- `response_status: completed_independent_ai_line_review`;
- `geometry_review_status: completed`;
- `text_review_status: completed`.

Every body-line record must have a non-null `observed_text` and no `pending` value.

A task regenerated after a lineation repair may include a `review_scope` object, completed lines in columns marked `completed_preserved`, and pending lines in columns marked `pending_regenerated_after_lineation_rebase`. Do not reread or alter the preserved columns. Complete the pending columns and return the whole page with the normal completed response statuses.

For each line, allowed values are:

- `match`: `strong`, `partial`, `mismatch`, or `unreadable`;
- `assessment`: `readable` or `uncertain`;
- `geometry_action`: `accepted_initial` or `adjusted`.

Use an empty `observed_text` with `match: unreadable` when nothing can be read. Use `assessment: uncertain` and a short `note` when a reading is materially doubtful. An optional `note` should otherwise be limited to an exceptional crop decision or a possible lineation problem.

Read `observed_text` independently before comparing it with the canonical line. It must preserve visible spelling, spacing, punctuation, diacritics, short and long `s`, and division marks. A verbatim copy of every canonical line can help identify lines, but it is not an independent text review.

## Geometry-only fallback

`geometry_only` is not the normal assignment. Use it only when every crop has been inspected credibly but a complete independent reading cannot be supplied. Record:

- `geometry_review_status: completed`;
- `text_review_status: not_completed`;
- null `observed_text` where no independent reading exists.

Do not disguise approximate OCR or copied canonical text as completed independent review.

## Stable IDs and pinned sources

Expected line IDs are stable references. Do not renumber them, silently shift them after a discrepancy, or attach an adjacent line merely to fill the record.

The response pins both the source image and canonical transcription with hashes. Do not edit those hashes. If the canonical text changes while a review is in progress, the project must rebase or regenerate the task before import.

The preserved base-task collection covers `f31`–`f125`, exactly the pages for which a returned review artifact exists. A base JSON file is archived as the input to that historical return and does not indicate pending work. Unused prepared tasks outside this range were deleted at retirement.

## Examples

Use the [example guide](../ai-geometry-examples/README.md) to keep two distinct purposes straight:

- [`bnf-f0053-reviewed.json`](bnf-f0053-reviewed.json) is the recommended model for real independent reading, visible disagreement, explicit uncertainty, and exceptional crop judgment;
- [`../ai-geometry-examples/bnf-f0030.json`](../ai-geometry-examples/bnf-f0030.json) is only the current structural and coordinate specimen. Its readings were copied from the canonical transcription and are not review evidence.

The f53 return predates the explicit `geometry_review_status`, `text_review_status`, and `geometry_action` fields. That omission is part of the archived record; this document no longer defines a live submission path.
