# Dictionary-Wide Human Review Interface

Public site: <https://hiroshi-manabe.github.io/nippo-jisho/>

The former line-end-hyphen, adjacent-vowel-tilde, and `ſt`/`st` specialist interfaces have been retired. Their accepted corrections remain in the canonical Level 1 text, Git history, and the Issues that applied them, but their candidate inventories, mutable ledgers, public routes, and dedicated Issue templates are no longer maintained. If another systematic audit is needed, generate a fresh inventory from the then-current transcription and geometry rather than reviving stale task state.

This generated interface supports asynchronous Level 1 production and human checking across the complete acquired Gallica sequence. All 651 leaves (`f1`–`f651`) are navigable from the outset. The overview distinguishes 229 canonical Level 1 pages, 402 editable machine-provisional OCR candidates, and 20 scan-only leaves. An amber provisional state, an explicit warning on every candidate page, and a separate structural-quarantine filter prevent availability for review from being mistaken for promotion to the canonical corpus.

The current public interface provides a thumbnail overview, compact in-page editing, complete-glyph line crops, an in-context two-level transcription reference, clipboard-based GitHub Issue submission, and factual correction-history badges. Its behavior and rationale are specified in [Human Review and Correction Workflow](../../docs/human-review-workflow.md).

Generate the local review interface from the repository root:

```sh
python3 scripts/generate_human_review.py
```

Then open `build/human-review/index.html`. The generator also writes `build/human-review/corpus.json`, an auditable 651-record snapshot of the data embedded in the HTML.

The public IIIF-backed successor is built with `python3 scripts/build_public_review.py`. It uses committed thumbnails and page geometry, loads one Gallica IIIF image only when a leaf is opened, and applies line crops in the browser. The older command above remains available for reproducing the local master-image prototype.

Every canonical text column requires explicit reviewed line geometry in [`line-geometry.json`](line-geometry.json). The current rectangles for existing pages were reconstructed after transcription: initial rectangles and disposable contact sheets are generated from the local masters with `python3 scripts/calibrate_line_geometry.py`, but each UI crop must still be reopened and checked individually at browser-review scale. Contact-sheet inspection alone is provisional. The complete assigned line must be readable as the primary line in its card; a clipped remnant visible through overlap does not pass. If one card exposes drift in a uniformly interpolated range, the whole range returns to unverified status and must be checked line by line, with measured centres replacing interpolation where necessary. Broad anchors, intermediate ranges, explicit per-line centre overrides, and individual crop overrides are all available; manual adjustment of every line is acceptable when a page requires it. On skewed pages, horizontal bounds may also vary line by line by following the printed rules rather than using one oversized fixed column rectangle. A crop passes the horizontal check only when the relevant printed rule and a small margin beyond it are visible; showing all text already recognized in the transcription does not establish that a faint terminal mark was not clipped. The visually verified `f13`–`f30` retrofit is reproducible with `python3 scripts/align_early_column_rules.py`; it preserves all existing vertical geometry and must be followed by the same individual-card inspection. The reviewed geometry covers all 21,479 text-column lines on the 229 canonical pages. The 402 OCR candidates carry their own provisional crop geometry so they can enter this same visual-check loop, but every one of those rectangles remains explicitly `ocr_bootstrap_unreviewed`. Furniture remains reviewed in whole-page context rather than receiving artificial line crops.

For new pages, do not discard the image rectangle used to read a line. Line isolation, transcription, crop adjustment, and UI-geometry capture form one operation: save the exact complete-glyph rectangle under the stable line ID before moving to the next line. This produces `captured_during_transcription` geometry without a later reconstruction pass. Existing pages receive `text_image_sanity_checked` only after every reconstructed crop has been viewed as an isolated card beside its assigned transcription and enough of that transcription can actually be read from the crop. A target line merely being present near an edge is not sufficient when another line dominates the image.

The [external-geometry horizontal-completeness audit](external-geometry-width-audit.md) records the subsequent rule-to-rule width check for all delegated results from `f31` through `f71`.

The delegated external-AI geometry-and-text workflow was retired on 2026-08-30. Its returned reviews and their matching `f31`–`f125` task inputs remain in the [legacy archive](ai-geometry-work/README.md), together with the [f30 structural specimen](ai-geometry-examples/README.md). They preserve provenance for imported geometry and adjudicated suggestions, but they are not current assignments and must not be refreshed as canonical text changes. Unused future-task JSON and native-image ZIPs were deleted. Future page work captures and verifies geometry in the ordinary project workflow above.

Human-unreviewed pages `f161`–`f237` were reinitialized from independent page-first OCR on 2026-09-02. [`ocr-page-baseline.json`](ocr-page-baseline.json) records each raw-draft digest, changed-line count, quarantine, and preserved structural row; [the pipeline documentation](../../docs/ocr-page-data.md) defines the independence boundary and safeguards. Their browser rectangles were retained rather than inferred from OCR, and every page remains pending human scan comparison.

Generate those isolated cards with `python3 scripts/audit_line_geometry.py --first 24 --last 30`. The output groups eight lines at a time, retains the committed crop at source resolution, and prints the complete assigned transcription below it. After changing any browser-visible geometry or interface data, build and test locally, commit, push `main`, wait for the Pages deployment, and inspect the affected row on the public site; a local commit alone does not update the review interface.

When an enlarged initial visibly spans two physical lines, the owning line uses a reviewed `crop_overrides` rectangle tall enough to contain the complete glyph. Its overlap with the following line is deliberate. Ordinary lines continue to use the tighter generated rectangles, so this exception does not add needless vertical context throughout the interface.

The parent interface provides:

- previous and next arrows across the full Gallica sequence;
- direct `f`-number entry and stable fragment links such as `#f249:column-2`;
- full-page, column 1, column 2, and page-furniture views on canonical and machine-provisional pages;
- line-by-line column views in which each scan strip sits directly above its transcription at exactly the same width;
- the Level 1 and human-review status of the selected page;
- a **Reload latest** action for picking up pages generated while human review proceeds elsewhere;
- scan zoom, rendered transcription, literal Markdown, Gallica links, and local full-resolution images.

In a column view, the physical line is the default comparison unit. The compact scan strip and its transcription share one horizontal extent, preserving left-to-right correspondence without forcing the eye between separate panes. **Show context** (or a click on the strip) expands that unit to include neighboring lines. Full-page and page-furniture views retain the broader side-by-side layout. Page-specific column boxes and optional first/last-line calibration live in `pilot/tile-config-v1-trial.json`; f17 provides the first calibrated trial.

Scan-only pages load their original master on demand and display **Not yet processed** instead of an empty or misleading transcription. Canonical pages use reviewed geometry; provisional candidates use their embedded unreviewed geometry and display that fact prominently.

## Correction loop

The ordinary correction interface is the embedded line editor and page-level schema-2 GitHub Issue submission. The processor applies settled corrections to canonical Markdown or to a provisional candidate package as appropriate, then rebuilds and deploys the site. Project chat remains the preferred route for ambiguous readings: the reviewer can report a stable line ID and proposed reading, discuss Japanese and Portuguese context, and inspect enlargement before a second-opinion decision is applied.

When adjudicating an Issue, treat the proposed reading as the leading hypothesis and the current transcription as potentially anchored machine error. Before inspecting the disputed glyph, temporarily disregard the old reading and analyse the proposal through Japanese morphology, Portuguese grammar and historical spelling, the bilingual gloss, and relevant lexical evidence. Then inspect the scan specifically to distinguish the resulting hypotheses. Accept a linguistically favored proposal when the image is compatible; retain the old form only on positive contrary visual evidence. If the proposal identifies the right word but appears to misread punctuation, spacing, or one glyph, do not silently apply a machine-qualified replacement: mark that qualified form **Human re-check required**, present its exact difference from the submitted form, and apply it only after human confirmation. The full rule and the f20, f26, and f28 control cases are documented in [Human Review and Correction Workflow](../../docs/human-review-workflow.md#github-issue-submission).

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
