# Dictionary-Wide Human Review Interface

Public site: <https://hiroshi-manabe.github.io/nippo-jisho/>

This generated interface supports asynchronous Level 1 production and human checking across the complete acquired Gallica sequence. All 651 leaves (`f1`–`f651`) are navigable from the outset. The 229 existing Level 1 pages show their transcription and review state; the remaining 422 pages show the verified scan with a clear `unprocessed` state.

This is the current prototype. The agreed next iteration adds a thumbnail overview, compact in-page editing, complete-glyph line crops, an in-context two-level transcription reference, clipboard-based GitHub Issue submission, and factual correction-history badges. Its behavior and rationale are specified in [Human Review and Correction Workflow](../../docs/human-review-workflow.md).

Generate the local review interface from the repository root:

```sh
python3 scripts/generate_human_review.py
```

Then open `build/human-review/index.html`. The generator also writes `build/human-review/corpus.json`, an auditable 651-record snapshot of the data embedded in the HTML.

The public IIIF-backed successor is built with `python3 scripts/build_public_review.py`. It uses committed thumbnails and page geometry, loads one Gallica IIIF image only when a leaf is opened, and applies line crops in the browser. The older command above remains available for reproducing the local master-image prototype.

Every processed text column now requires explicit line geometry in [`line-geometry.json`](line-geometry.json). The current rectangles for existing pages were reconstructed after transcription: initial rectangles and disposable contact sheets are generated from the local masters with `python3 scripts/calibrate_line_geometry.py`, but each UI crop must still be reopened and checked individually at browser-review scale. Contact-sheet inspection alone is provisional. Broad anchors, intermediate ranges, explicit per-line centre overrides, and individual crop overrides are all available; manual adjustment of every line is acceptable when a page requires it. The current geometry covers all 21,480 text-column lines on the 229 processed pages. Furniture remains reviewed in whole-page context rather than receiving artificial line crops.

For new pages, do not discard the image rectangle used to read a line. Line isolation, transcription, crop adjustment, and UI-geometry capture form one operation: save the exact complete-glyph rectangle under the stable line ID before moving to the next line. This produces `captured_during_transcription` geometry without a later reconstruction pass. Existing pages receive `text_image_sanity_checked` only after every reconstructed crop has been viewed as an isolated card beside its assigned transcription and enough of that transcription can actually be read from the crop. A target line merely being present near an edge is not sufficient when another line dominates the image.

Generate those isolated cards with `python3 scripts/audit_line_geometry.py --first 24 --last 30`. The output groups eight lines at a time, retains the committed crop at source resolution, and prints the complete assigned transcription below it. After changing any browser-visible geometry or interface data, build and test locally, commit, push `main`, wait for the Pages deployment, and inspect the affected row on the public site; a local commit alone does not update the review interface.

When an enlarged initial visibly spans two physical lines, the owning line uses a reviewed `crop_overrides` rectangle tall enough to contain the complete glyph. Its overlap with the following line is deliberate. Ordinary lines continue to use the tighter generated rectangles, so this exception does not add needless vertical context throughout the interface.

The parent interface provides:

- previous and next arrows across the full Gallica sequence;
- direct `f`-number entry and stable fragment links such as `#f249:column-2`;
- full-page, column 1, column 2, and page-furniture views on transcribed pages;
- line-by-line column views in which each scan strip sits directly above its transcription at exactly the same width;
- the Level 1 and human-review status of the selected page;
- a **Reload latest** action for picking up pages generated while human review proceeds elsewhere;
- scan zoom, rendered transcription, literal Markdown, Gallica links, and local full-resolution images.

In a column view, the physical line is the default comparison unit. The compact scan strip and its transcription share one horizontal extent, preserving left-to-right correspondence without forcing the eye between separate panes. **Show context** (or a click on the strip) expands that unit to include neighboring lines. Full-page and page-furniture views retain the broader side-by-side layout. Page-specific column boxes and optional first/last-line calibration live in `pilot/tile-config-v1-trial.json`; f17 provides the first calibrated trial.

Scan-only pages load their original master on demand and display **Not yet processed** instead of an empty or misleading transcription. The generator creates column crops only for pages with Level 1 data.

## Current conversational correction loop

In the current prototype, the normal correction interface is the project chat rather than an editor embedded in the HTML. The reviewer reports a stable line ID and proposed reading; both sides can discuss Japanese and Portuguese context and inspect enlargement before the canonical Markdown is changed. The affected HTML unit is then regenerated and rechecked. The planned public interface will retain this conversational route for ambiguous cases while adding page-level proposals through GitHub Issues.

When adjudicating an Issue, give its proposed reading a modest corrective prior and treat the current transcription as potentially anchored error. Start by trying to verify the proposal against a fresh scan view and relevant linguistic or lexical evidence. Reject it only on positive contrary evidence, not because the old reading can still be seen; if the proposal identifies the right word but misreads punctuation, spacing, or one glyph, apply the scan-supported qualified form and explain the refinement in the Issue. The full rule and the f20 `Aguebune. i. ſacabune.` case are documented in [Human Review and Correction Workflow](../../docs/human-review-workflow.md#github-issue-submission).

Every transcribed physical line has a **Copy** button. It copies only the stable reference and current plain text:

```text
f249/c2-l040
Current: Gunpacu. Icuſano macu. Certas cortinas q̃
```

The reviewer can add a proposed reading, explanation, or question freely in chat.

## Current prototype progress registry

The committed [`review-status.json`](review-status.json) is the canonical human-review progress record. It contains three review units for every existing Level 1 page:

- `pending`: human comparison has not been completed;
- `needs_correction`: the reviewer found a discrepancy that has not yet completed the correction-and-recheck loop;
- `checked`: the current generated view has been compared with the scan, with reviewer and timestamp recorded.

The file must be updated only after corrections have been applied to the Level 1 Markdown and the affected unit has been regenerated and rechecked. A page may receive the Level 1 status `human_checked` only after both columns and page furniture are `checked`. A later correction does not erase review history; it reopens the affected unit until that unit has been checked again.

This registry remains useful for the bounded production experiment, but the public interface will not present `checked` as proof of final correctness. It will instead expose applied-Issue counts, distinct corrected-line counts, and the latest correction, as defined in the workflow document. Git remains the authoritative technical history.
