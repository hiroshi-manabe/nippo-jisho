# Raw correction corpus

This directory preserves the correction evidence from the opening production pages in a form that can be reused during later transcription. It is intentionally occurrence-level and chronological: an attractive but rejected reading is evidence about the review process too, and a multi-step history is not collapsed into its final answer.

## Files

- [`f0013-f0016.tsv`](f0013-f0016.tsv) is the raw event table. One row is one textual transition at one source location.
- [`f0017.tsv`](f0017.tsv) records the five atomic mismatches found by the repeated autonomous audit and four subsequent human-review corrections.
- [`f0017-pattern-audit.md`](f0017-pattern-audit.md) records the first use of the corpus as a post-hoc checklist on a new page.

## TSV fields

| Field | Meaning |
| --- | --- |
| `event_id` | Stable local identifier, ordered by page and observed sequence. |
| `page` | Gallica view number in the project's `f0013` form. |
| `line` | Stable Level 1 physical-line reference. A range is used only when one divided string spans physical lines. |
| `phase` | When the event occurred: draft review, pre-handoff review, human review, repetition sweep, or convention audit. |
| `step` | Order within a multi-step history at the same location. |
| `before` / `after` | The smallest exact string preserved by the evidence. These are literal strings, not normalized forms. |
| `outcome` | `accepted`, `intermediate`, `reverted`, or `rejected`. An `intermediate` reading contributed evidence but was later superseded. |
| `finder` | The review perspective that exposed the candidate. |
| `categories` | Semicolon-separated reusable error mechanisms. |
| `provenance` | Commit, report, or preserved discussion record supporting the row. |
| `note` | Short evidence note; not a replacement for the source scan. |

## Scope and limits

The table includes every exact before/after correction recoverable from the f13 commit sequence and the f14–f16 production reports, including same-page repetition findings and the rejected f16 `-`/`=` proposal. It also includes the two exact f14 changes preserved in the pre-comparison log. Fleeting visual hypotheses that were corrected before any exact earlier string was recorded cannot be reconstructed and are therefore not invented; report-only examples are included when both sides survive in the report.

The corpus is a diagnostic checklist, not an automatic substitution list. A category may direct attention to a location, but a change is made only when enlargement supports it. The f17 audits demonstrate both the intended order and the limits of a checklist: complete the page-specific passes first, use past error families to search for omissions, record both changes and inspected non-changes, and return every candidate to the scan. The first pattern pass found zero changes; a later open-ended repeated audit found five atomic mismatches, including two long-`ſ` errors inside a category that the checklist had nominally covered.
