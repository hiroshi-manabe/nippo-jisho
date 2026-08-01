# Dictionary-Wide Human Review Interface

This generated interface supports asynchronous Level 1 production and human checking across the complete acquired Gallica sequence. All 651 leaves (`f1`–`f651`) are navigable from the outset. The nine existing Level 1 pages show their transcription and review state; the remaining 642 pages show the verified scan with a clear `unprocessed` state.

Generate the local review interface from the repository root:

```sh
python3 scripts/generate_human_review.py
```

Then open `build/human-review/index.html`. The generator also writes `build/human-review/corpus.json`, an auditable 651-record snapshot of the data embedded in the HTML.

The parent interface provides:

- previous and next arrows across the full Gallica sequence;
- direct `f`-number entry and stable fragment links such as `#f249:column-2`;
- full-page, column 1, column 2, and page-furniture views on transcribed pages;
- the Level 1 and human-review status of the selected page;
- a **Reload latest** action for picking up pages generated while human review proceeds elsewhere;
- scan zoom, rendered transcription, literal Markdown, Gallica links, and local full-resolution images.

Scan-only pages load their original master on demand and display **Not yet processed** instead of an empty or misleading transcription. The generator creates column crops only for pages with Level 1 data.

## Conversational correction loop

The normal correction interface is the project chat, not an editor embedded in the HTML. The reviewer reports a stable line ID and proposed reading; both sides can discuss Japanese and Portuguese context and inspect enlargement before the canonical Markdown is changed. The affected HTML unit is then regenerated and rechecked. This simple conversational loop keeps judgments visible without introducing a second editing surface.

Every transcribed physical line has a **Copy** button. It copies only the stable reference and current plain text:

```text
f249/c2-l040
Current: Gunpacu. Icuſano macu. Certas cortinas q̃
```

The reviewer can add a proposed reading, explanation, or question freely in chat.

## Canonical progress

The committed [`review-status.json`](review-status.json) is the canonical human-review progress record. It contains three review units for every existing Level 1 page:

- `pending`: human comparison has not been completed;
- `needs_correction`: the reviewer found a discrepancy that has not yet completed the correction-and-recheck loop;
- `checked`: the current generated view has been compared with the scan, with reviewer and timestamp recorded.

The file must be updated only after corrections have been applied to the Level 1 Markdown and the affected unit has been regenerated and rechecked. A page may receive the Level 1 status `human_checked` only after both columns and page furniture are `checked`. A later correction does not erase review history; it reopens the affected unit until that unit has been checked again.
