# External-AI response format

This reference defines how to record the result. The assignment and its acceptance standard are in [README.md](README.md); visual crop decisions are covered by [GEOMETRY-GUIDE.md](GEOMETRY-GUIDE.md).

## Default mode

The normal `default_response_mode` is `geometry_and_text`. A completed response uses:

- `response_status: completed_independent_ai_line_review`;
- `geometry_review_status: completed`;
- `text_review_status: completed`.

Every body-line record must have a non-null `observed_text` and no `pending` value.

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

The prepared base-task collection covers `f31`–`f237`, `f248`–`f250`, and `f643`. A base JSON file remains after review and therefore does not indicate that a page is still pending.

## Example

The reviewed f30 response at [`../ai-geometry-examples/bnf-f0030.json`](../ai-geometry-examples/bnf-f0030.json) is the golden structural example. Its accompanying README explains the coordinate conventions. Copy its data shape, not its page-specific values or transcription.
