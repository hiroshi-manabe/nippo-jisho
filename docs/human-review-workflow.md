# Human Review and Correction Workflow

## Purpose

The public review interface should make scan comparison easy without claiming that a page has become definitively correct. Most lines will receive no correction, so the ordinary view must stay compact. When a reader does find a problem, the interface should capture a precise, inspectable proposal that can be discussed and applied through GitHub.

This document specifies the intended next iteration of the existing [dictionary-wide review interface](../pilot/human-review/README.md). It is a design decision, not yet a description of every implemented control.

## Two complementary views

### Page overview

The front page presents all acquired leaves as a responsive thumbnail grid in Gallica order. Each page card shows:

- the `f` identifier and scan thumbnail;
- the processing state, such as `unprocessed` or `transcription available`;
- the number of applied correction Issues;
- the number of distinct lines corrected;
- optionally, the most recent correction date.

The badges report activity, not quality. A page with no corrections is not thereby verified, and a page with many corrections is not necessarily worse. Clicking a card opens the page review view. Page order is the default; filters for unprocessed, transcribed, and corrected pages and an optional recently-corrected order may be added without changing the underlying record.

### Page review

The page view retains full-page and column context, but the physical line is the primary checking unit. For each line, the scan strip is placed above its transcription, and both use the same practical horizontal extent. This makes the characters in the image and transcription directly comparable from left to right.

The sticky page-navigation bar includes an explicit **← All pages** button. The project title also returns to the overview, but it is not the sole or implicit way out of an individual page.

Unchanged rows remain compact. Clicking the transcription opens an editor containing:

- the editable transcription;
- an optional comment;
- **OK** and **Cancel** actions.

**OK** confirms the local proposal and collapses the editor. **Cancel** discards changes made during that editing session. A changed row can be reopened, and a **Revert** action restores the repository text.

In compact form, a comment uses the horizontal space remaining to the right of the usually short transcription. A comment that does not fit is truncated with an ellipsis, with its complete text available on click or focus. On narrow screens it moves below the transcription. The comment should remain visually secondary to the source text.

## Transcription reference panel

The page-review toolbar provides a persistent **Reference** control. It opens a lightweight panel containing the compact [Transcription Cheat Sheet](transcription-cheat-sheet.md), which is the routine operational reference for Japanese romanization, Early Modern Portuguese type, marks, spacing, and recurring visual confusions. Individual topics link to the fuller [Historical Language Notes](historical-language-notes.md) for qualifications, evidence, bibliography, and source provenance.

The panel is closed by default and must not permanently narrow the scan or transcription area. Its state may remain open while the reviewer moves among lines or pages. On the all-page overview, ordinary links to both documents are sufficient; the embedded panel is primarily a line-review aid.

The interface displays the reference source commit or version so that later users can identify which guidance was available during a review. The panel is advisory: it helps generate candidates, but no linguistic expectation overrides the printed scan.

## Visual diff

The collapsed changed row highlights the difference between the repository text and proposed text. This diff is a client-side reading aid only:

- it may use a simple character- or word-level algorithm;
- an awkward comparison may fall back to highlighting a whole word or line;
- the generated diff is not stored or submitted;
- only the original text, proposed text, and optional comment are evidence.

A pale background and darker accent should preserve the legibility of small letters and diacritics better than solid red text alone.

## Line-image cropping

Crop boundaries are governed by legibility, not by a requirement that neighboring line images never overlap. Every glyph belonging to the target line must be completely visible. In particular, ascenders, descenders, diacritics, damaged impressions, and type crossing a nominal line boundary must not be clipped.

The routine is:

1. Produce a reasonably tight initial line crop.
2. Generate a complete column contact sheet pairing every stable line ID with its proposed crop.
3. Inspect every crop visually against the contact sheet and full column context.
4. Expand upward or downward when any target glyph is incomplete or ambiguous.
5. Permit overlap with an adjacent line whenever necessary for a complete reading.
6. Avoid unnecessary padding where a natural boundary is clear.
7. Commit an explicit source-pixel rectangle for every column line, including crops accepted without individual adjustment.

This geometry pass is a required part of processing a page, not optional interface polish. A page must not be handed off for line-by-line human review until both column contact sheets have been visually reviewed. The geometry record stores the source dimensions, crop and context rectangle for every stable line ID, review state, and review date. Later regeneration must fail if a processed column line lacks explicit geometry.

The crop is therefore page- and line-sensitive rather than a uniform band with permanently large margins. The clipped top of `T` in `f17/c2-l042` (`Acuma. i. Tengu. Diabo.`) is the motivating example: part of the preceding line may be repeated, but the whole `T` must appear in the target line image. The same reviewed crops should support both project transcription checks and the public human-review interface.

### IIIF delivery and local cropping

The public site stores crop geometry, not derivative line-image files. When a reader opens a leaf, the browser requests one medium-high-resolution page image from Gallica's IIIF Image API. Full-page, column, context, and line views reuse that same URL from the browser cache and apply the committed crop coordinates locally. A separate IIIF region request is reserved for an exceptional high-resolution detail, rather than being made for every ordinary line.

The application retains the JPEGs for every successfully visited leaf in in-memory `Image` caches for the lifetime of the browser tab. It makes no speculative or neighboring-page requests. On first visit it immediately requests a 1000-pixel-wide preview and displays it as soon as it arrives. After the preview succeeds and the leaf remains current for a short dwell period, a dedicated manager may request the 2200-pixel HD image and replace the preview when it arrives. Revisiting a leaf reuses either or both retained versions. Both sizes, along with the native downloaded master, are served by the project's [Cloudflare scan-image mirror](image-mirror.md); the canonical-source link continues to open the corresponding Gallica page.

The HD manager owns every 2200-pixel request. It permits only one in-flight HD request and replaces queued work when the reader moves to another leaf, avoiding wasted transfer during rapid navigation. An HD request that has already started is allowed to complete and is retained even if the reader navigates away. Preview failures receive bounded backoff retries; failed preview and HD entries are removed rather than cached. Visible scan elements receive their `src` only after a retained image has loaded, so a temporary failure produces an explicit loading or retry state rather than a broken-image icon. The earlier fifteen-second Gallica rate limit and sixty-second failure cooldown were removed when image delivery moved to the project-controlled static mirror; only a short five-second failure cooldown remains.

The caches are intentionally unbounded within one tab for now. If a reader visits hundreds of leaves, memory use may grow, although the browser remains free to discard decoded pixels under memory pressure. Closing or reloading the tab releases both caches.

The repository contains pre-generated overview thumbnails because loading hundreds of Gallica pages on the overview would be slow and discourteous to the service. It does not contain the high-resolution masters. Each page record retains the original source dimensions so crop coordinates can be scaled correctly at the requested IIIF resolution. The interface loads the transcription immediately, shows image-loading state where needed, and retains a direct Gallica link as provenance and fallback.

This design keeps the deployed site small and makes a crop correction a reviewable metadata change. It also respects Gallica's current request limits better than issuing dozens of line-region requests whenever one page is opened.

### Build and deployment

The site source, transcription data, crop geometry, and correction Issues live in this repository. The generated site does not occupy a maintained `gh-pages` branch: a GitHub Actions workflow builds it from `main`, uploads the temporary Pages artifact, and deploys that artifact to GitHub Pages. This keeps generated HTML and corpus data out of source history while ensuring that one commit identifies the transcription, reference notes, geometry, and interface shown together.

The committed overview thumbnails and `page-images.json` are reproducible derivatives of the ignored local Gallica master cache. Run `python3 scripts/prepare_review_images.py` only when those derivatives need to be created or refreshed. An ordinary public-site build requires no local master images and runs with `python3 scripts/build_public_review.py`.

Before deployment, the actual browser rendering must also be inspected on representative first, middle, last, tall-glyph, and overridden lines. Numerical coordinate validation and inspection of a source crop do not establish that CSS scaling and positioning render it correctly. `f17/c1-l001` and `f17/c2-l042` are permanent browser-level regression cases.

## GitHub Issue submission

The interface prepares corrections page by page. A submission contains only rows whose edits have been confirmed with **OK**. Before submission, the reader can inspect the collected changes.

The Issue body must not be placed in a GitHub `issues/new` query parameter. GitHub documents query prefilling but does not promise a usable maximum URL length, and realistic multi-correction payloads can exceed browser, intermediary, or server limits. Compact JSON reduces the risk but does not remove it, especially when comments contain Japanese text.

The submission flow is therefore:

1. Serialize the confirmed page corrections as readable, versioned JSON.
2. Copy the complete payload to the clipboard.
3. Open a short GitHub Issue URL containing only the template selection and a page-specific title.
4. Ask the reader to paste the copied payload at the marked location in the Issue body.
5. Retain the local draft until the reader explicitly clears it.

After the Issue composer opens, the review tab changes to ask whether the Issue was actually submitted. Confirming this does not delete the local draft: it changes the bar to a compact **Marked as submitted** state with a **Submit again** escape hatch. Choosing **Not yet**, editing any line, or explicitly submitting again returns the page to draft state. This local state is persisted per page so returning to or reloading the review tab does not make the submission ambiguous.

Each local page workspace records a transcription version derived only from the ordered line IDs, transcription text, and typeface runs. Scan crops, thumbnails, correction-history badges, metadata, and interface code do not affect this version. When repository text changes, saved edits based on the earlier transcription must not be restored onto the new lines as though they were current.

The page version is only a trigger for line-level reconciliation. Every saved edit also records the content version of its stable physical-line ID. Unchanged edited lines retain their proposals silently, even when another line on the page changed. If the current repository text equals a saved proposal, that textual correction is removed as already incorporated. Otherwise a changed edited line is automatically rebased: its current repository text becomes the new `before`, its saved proposal remains the `after`, and the row receives a persistent **Base updated** marker. A page notice reports the number of affected rows. Confirming a highlighted row with **OK** clears its marker; rebasing any submitted row returns the workspace to draft status.

A comment is an annotation whose continued relevance cannot be decided by text equality. When its line changes, the comment is preserved and marked **Comment needs review** until the reviewer confirms the row. If an incorporated textual correction still has a comment, it becomes a comment-only record on the current text. A pre-existing comment-only record is likewise rebased with both `before` and `after` set to the current text, so it cannot accidentally become a proposal to restore the earlier reading. Submitted comments are treated the same way because repository text alone does not show that their reasoning has been preserved elsewhere.

Only a missing stable line ID prevents automatic rebasing. In that exceptional case, unaffected edits are retained while a blocking warning lets the reviewer copy and then discard the orphaned records. Pre-versioning browser data is migrated once against the first version-aware corpus rather than being discarded without a known comparison point. This is deliberately simple optimistic concurrency control; the browser never attempts to synthesize a textual merge.

Edited rows must continue to render the original Level 1 typeface runs. Diff highlighting is an additional visual layer; it must not flatten italic Portuguese and roman Japanese into one style.

If clipboard access fails, the interface displays the payload in a selectable text area. Direct GitHub API submission is deliberately deferred because a static GitHub Pages site should not contain a privileged token, and an authentication service is unnecessary for the initial workflow.

A representative payload is:

```json
{
  "schema": 1,
  "page": "f17",
  "base_commit": "abc1234",
  "base_transcription_version": "sha256:0123456789abcdef…",
  "changes": [
    {
      "line": "c1-l026",
      "before": "Acuni toingiacu ſuru.",
      "after": "Acuni tongiacu ſuru.",
      "comment": "Japanese 頓着 supports tongiacu."
    }
  ]
}
```

`before` protects against silently applying a proposal to a line that has subsequently changed. The Issue is a proposal: each reading is still checked against the scan and linguistic context before the canonical Markdown is edited.

## Correction history, not certification

Git records the complete technical history, while Issues retain discussion and the submitted proposal. The generated interface exposes a small factual summary for each page:

- number of applied correction Issues;
- number of distinct lines corrected;
- optionally, total accepted edits when a line has changed more than once;
- date and commit of the latest applied correction.

For example:

```text
Corrections applied: 3 Issues · 17 distinct lines
Last correction: 2026-08-01 at abc1234
```

These measures show accumulated human attention without asserting that review is complete. Terms such as `verified` or `final` should not be inferred from the absence of a pending edit. Processing state and correction history remain separate dimensions.

## Relationship to conversational review

Chat remains useful for ambiguous readings and allows the reviewer to quote a stable line reference and current text. The web editor does not replace that discussion; it supplies a lightweight way to assemble unambiguous corrections and hand them to the same adjudication process. GitHub Issues make the public, asynchronous version of that loop durable and traceable.
