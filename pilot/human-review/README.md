# Human Column Review Prototype

This prototype adds a human checkpoint after `scan_confirmed`. It initially covers `bnf-f0249` and `bnf-f0250`, divided into three resumable units per page: column 1, column 2, and page furniture.

Generate the local review interface from the repository root:

```sh
python3 scripts/generate_human_review.py
```

Then open `build/human-review/index.html`. Each unit places a high-resolution scan crop beside the rendered Level 1 transcription. The **Show Markdown** control exposes the literal authoring lines, the zoom control enlarges the scan without losing the surrounding column, and previous/next controls move through all six units.

The interface stores provisional status and notes in that browser only and can download a session summary. These conveniences do not alter project files. The committed [`review-status.json`](review-status.json) remains the canonical progress record and must be updated only after corrections have been applied to the Level 1 Markdown and the affected unit has been regenerated and rechecked.

Review states are:

- `pending`: human comparison has not been completed;
- `needs_correction`: the reviewer found a discrepancy that has not yet completed the correction-and-recheck loop;
- `checked`: the current generated view has been compared with the scan, with reviewer and timestamp recorded.

A page may receive the Level 1 status `human_checked` only after both columns and page furniture are `checked`. A later correction does not erase review history; it reopens the affected unit until that unit has been checked again.
