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

Column views also form one continuous review sequence over the transcribed corpus: a page's column 1 is followed by its column 2, then by column 1 of the next transcribed page. **Previous column** and **Next column** controls appear above the line list and repeat after its final line, where the reviewer naturally decides whether to continue. Moving between columns opens the target at its beginning rather than retaining the previous column's scroll position. Full-page, furniture, and unprocessed views do not show these controls; the ordinary page arrows remain independent.

Unchanged rows remain compact. Clicking the transcription opens an editor containing:

- the editable transcription;
- an optional comment;
- a **Request second opinion** checkbox;
- **OK** and **Cancel** actions.

**OK** confirms the local proposal and collapses the editor. Pressing **Enter** in the transcription field does the same thing: each record represents one physical printed line, so a newline is not valid transcription content. Enter remains available normally in the separate comment field. IME composition is exempt so that confirming composed input does not close the editor. Opening another line has the same save-and-collapse effect on the active editor before the new one opens, so moving through the page cannot silently discard typed text or comments. **Cancel** remains the explicit way to discard changes made during that editing session. A changed row can be reopened, and a **Revert** action restores the repository text.

Typing a comment selects **Request second opinion** automatically, because a comment usually identifies a distinction that deserves discussion. The reader may clear the checkbox afterward when the comment is only provenance or an already-settled human observation. That explicit choice persists when the row is reopened. A checked row receives a compact marker after **OK** so the page-level review state remains visible.

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

There are two distinct cases.

### Existing transcriptions

The coordinates for existing pages are reconstructed after the fact. Although the text was originally read line by line, the temporary image regions used during that work were not preserved as UI geometry. Contact sheets and automatic calibration can provide starting rectangles, but every stable line ID must therefore be reopened and checked individually at the normal browser-review scale. This is geometry verification, not a requirement to transcribe the text again.

### New transcriptions

For new pages, transcription and UI-geometry capture are one operation:

1. Isolate one physical line and assign its stable line ID.
2. Adjust the displayed rectangle until the intended line and every relevant glyph are completely visible.
3. Read and transcribe from that rectangle, enlarging it further whenever the reading requires more evidence.
4. Save that exact source-pixel rectangle as the line's UI crop, together with its context rectangle.
5. Continue to the next physical line.

The crop used as transcription evidence is therefore preserved instead of being reconstructed later. Subsequent checking may still improve it, but a separate bulk geometry pass should not normally be necessary.

### Acceptance routine

For either case, the final requirements are:

1. Verify the column's horizontal rectangle against the full-resolution page. Both ends of every ordinary line must be present; a large blank margin on one side is a warning that the opposite end may be clipped. On a skewed page, do not force the whole column into one fixed `x`/`width`: identify the four printed vertical rules (the two outer rules and both sides of the central gutter), interpolate each rule down the page, and derive each line's horizontal bounds from the rule positions across that line's own vertical span. Retain a small margin outside the rules and inspect the result; the fitted trajectory is only a starting model, not visual evidence by itself.
2. Choose several vertical anchors across the column and generate scan-snapped initial line centres. A single top-to-bottom interpolation is insufficient evidence that intermediate lines are aligned.
3. Generate a complete column contact sheet pairing every stable line ID with its proposed crop as an overview and line-order diagnostic.
4. Open **every crop individually at the normal browser-review scale**. Confirm that the strip contains the line named by its ID and that every target glyph is complete.
5. Reject a crop when target ink touches or nearly touches a vertical or horizontal edge unless enlarged context proves that the complete glyph is present. Small descenders and diacritics require full-size inspection; a reduced contact sheet cannot establish this.
6. Add intermediate ranges or explicit per-line centre overrides wherever the generated centres drift. Manual adjustment of every line is permitted when that is what the page requires.
7. Expand individual rectangles upward or downward when any target glyph is incomplete or ambiguous.
8. Permit overlap with an adjacent line whenever necessary for a complete reading.
9. Avoid unnecessary padding where a natural boundary is clear.
10. Commit an explicit source-pixel rectangle for every column line, including crops accepted without individual adjustment.

The first skew-aware retrofit covers `f13`–`f30`. Its four rule trajectories are recorded reproducibly in `scripts/align_early_column_rules.py`; the command changes only horizontal bounds and deliberately preserves the previously reviewed `y`/height of every line and context crop. Any future rerun still requires a fresh isolated-card audit of every affected line before the resulting geometry is accepted.

This geometry pass is a required part of processing a page, not optional interface polish. A page-level geometry status is earned only after every browser-facing line crop has passed individual inspection. The geometry record stores the source dimensions, crop and context rectangle for every stable line ID, review state, and review date. Later regeneration must fail if a processed column line lacks explicit geometry.

The existing `contact_sheet_reviewed` records were reconstructed after transcription and are provisional: they say that a contact sheet was inspected, not that every full-size UI crop is complete. New pages whose rectangles are preserved during line-by-line transcription may use `captured_during_transcription`; reconstructed pages may use `line_by_line_reverified` only after the same individual browser-scale check has subsequently been completed. Delegated geometry accepted from a completed independent AI line review uses `ai_line_by_line_checked`; this records the provenance of the coordinate decision without claiming human verification or transcription correctness. If a response supplies usable rectangles but its edit pattern does not credibly demonstrate individual line-level decisions—for example, it applies one uniform shift or crop height while marking every line strongly readable—an independent full contact-sheet audit may instead accept the geometry as `ai_bulk_geometry_sanity_checked`. That state records the useful result without endorsing an unsupported line-by-line-review claim. Geometry and text review may also complete independently: a response explicitly recording completed geometry and incomplete text may be imported through the geometry-only path after every crop has been checked, without treating blank readings as textual evidence. These statuses describe how the geometry was established; none removes the possibility of later correction.

A line may be vertically centered and still unusable if its first or last glyph is outside the crop. Every imported geometry review must therefore check **horizontal completeness** independently of line identification: compare the isolated crop with the full scan and ensure that all printed text assigned to the line remains visible. For ordinary two-column pages, a conservative crop spanning slightly beyond both column rules is preferable to a tight fixed-width crop. The status `external_ai_width_rechecked` means that externally supplied vertical coordinates were retained but every affected line was subsequently expanded to audited rule-to-rule horizontal coverage. This status does not imply a new textual review.

The width-recheck command accepts `--start-page`, `--end-page`, and `--reviewed-at` so a new delegated batch can be corrected without rewriting the provenance of earlier accepted batches. If the delegated review exposes a genuine canonical lineation error, correct the canonical physical-line sequence first; the importer validates returned IDs against that current sequence rather than preserving stale geometry IDs.

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

The former line-end-hyphen, adjacent-vowel-tilde, and `ſt`/`st` specialist tasks are retired. Their accepted results live in the canonical transcription and correction Issues; Git retains the implementation and raw inventories as historical evidence. The public site, ordinary build, and correction processor do not carry forward their routes, candidate payloads, ledgers, selection state, or validation counts. A future systematic question begins with a newly generated inventory based on the current transcription and geometry, so ordinary corrections never have to synchronize obsolete task records.

#### Current build

The committed overview thumbnails and `page-images.json` are reproducible derivatives of the ignored local Gallica master cache. Run `python3 scripts/prepare_review_images.py` only when those derivatives need to be created or refreshed. An ordinary public-site build requires no local master images and runs with `python3 scripts/build_public_review.py`.

Before deployment, the actual browser rendering must also be inspected on representative first, middle, last, tall-glyph, and overridden lines. Numerical coordinate validation and inspection of a source crop do not establish that CSS scaling and positioning render it correctly. `f17/c1-l001` and `f17/c2-l042` are permanent browser-level regression cases.

A geometry-only external review remains importable after transcription-only changes when the canonical page still has exactly the reviewed line IDs. Its rectangles did not depend on the reviewed wording, so the importer verifies structural compatibility instead of requiring the old page-file hash. A completed geometry-and-text review remains pinned to its exact transcription hash because its textual observations may otherwise be stale.

Any change that affects the public review interface—including crop geometry, generated corpus data, reference material shown by the interface, or UI code—is not complete when it is merely committed locally. It must be pushed to `main`, the GitHub Pages workflow must finish successfully, and the affected public view must be reopened at the deployed reference commit. This deployment check is part of the UI-change workflow, not a separate optional publication step.

## GitHub Issue submission

The interface prepares corrections page by page. A submission contains only rows whose edits have been confirmed with **OK**. Before submission, the reader can inspect the collected changes.

The Issue body must not be placed in a GitHub `issues/new` query parameter. GitHub documents query prefilling but does not promise a usable maximum URL length, and realistic multi-correction payloads can exceed browser, intermediary, or server limits. Compact JSON reduces the risk but does not remove it, especially when comments contain Japanese text.

The submission flow is therefore:

1. Serialize the confirmed page corrections as readable schema-2 JSON, marking only requested second-opinion rows with `"second_opinion": true`.
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
  "schema": 2,
  "page": "f17",
  "base_commit": "abc1234",
  "base_transcription_version": "sha256:0123456789abcdef…",
  "changes": [
    {
      "line": "c1-l026",
      "before": "Acuni toingiacu ſuru.",
      "after": "Acuni tongiacu ſuru.",
      "comment": "Japanese 頓着 supports tongiacu.",
      "second_opinion": true
    }
  ]
}
```

`before` protects against silently applying a correction to a line that has subsequently changed. In schema 2, an absent or false `second_opinion` means that the human reviewer has settled the exact correction and asks for mechanical application. A true value asks the machine reviewer to investigate that item independently. The automated processor accepts schema 2 only and returns an error for schema 1; no new schema-1 submission is expected.

Issue processing is deliberately two-stage. First validate the page, base version, line IDs, `before` values, and correction notation, then mechanically apply all unflagged schema-2 changes to the working tree. Do not reopen their glyph judgments merely because machine vision would have read them differently. Next, perform the detailed linguistic-first and visual review below only for `second_opinion: true` items. Do not commit, push, or close the Issue until the flagged set is settled. If no items are flagged, the validated mechanical application may proceed directly through tests, commit, deployment, and Issue closure.

### Automated Issue processor

The normal first action for a correction Issue is:

```sh
python3 scripts/process_correction_issue.py process ISSUE_NUMBER
```

The command takes an explicit Issue number; it never selects an Issue implicitly. It fetches the single schema-2 payload, verifies that the Issue is open and its base commit exists, validates every stable line ID and `before` value, resolves lightweight `*word`, `[roman]`, and `{italic}` notation, and applies all unflagged changes to the compact Level 1 source. A page-version mismatch caused by unrelated lines is reported but does not defeat exact line-level validation. Unknown lines, changed `before` text, ambiguous notation, multiple payload blocks, and schema 1 are hard errors. Existing large-initial, far-right, and other run metadata is retained through textual edits.

After application, the processor writes its report before validation, recompiles the interchange JSON, regenerates verification views, rebuilds the public review artifact, and runs the complete test suite. A validation failure leaves the Issue open, records `validation_failed` and the error in the report, and permits a repeat invocation to recognize the already-applied unflagged targets rather than applying them twice. If no second opinion was requested, it updates correction history, stages only the expected page-derived files, commits, pushes `main`, waits for the Pages workflow, verifies the deployed commit and correction record, comments on the Issue, and closes it. A failure before deployed verification leaves the Issue open.

If one or more changes contain `second_opinion: true`, the processor applies and validates only the unflagged subset, writes `build/correction-issues/issue-N.json`, prints its path, and exits with status 3. No history update, commit, push, deployment, or Issue closure occurs. Each flagged item begins with `"decision": "pending"`. After the linguistic-first and visual review, the machine reviewer records one of:

- `"accept"`: apply the submitted form exactly;
- `"reject"`: retain the existing line;
- `"qualify"`: apply the separately recorded `qualified_after` form after any required human confirmation.

The reviewer then resumes with:

```sh
python3 scripts/process_correction_issue.py finalize ISSUE_NUMBER
```

Finalization refuses unresolved decisions, validates rejected and accepted lines against the prepared base, and then follows the same generation, testing, publication, deployed-verification, and closure sequence. `--local-only` exercises either path through local generation and tests without Git or GitHub writes; it is intended for development and regression testing, not ordinary Issue processing.

Tests must not freeze a particular reading from the evolving diplomatic transcription as though it were a permanent software invariant. Text changes are preserved by Git history, correction provenance, and Issue records. Tests instead protect parsing, round trips, stable addressing, structural metadata, geometry validity, correction-history consistency, and publication behavior. Features that transform correction text or typography use synthetic fixtures. A newly accepted reading should therefore not require a corpus-content assertion to be rewritten.

Second-opinion adjudication is deliberately asymmetric. A human correction receives a strong corrective prior because it normally reports a discrepancy found while comparing the scan with the published text, whereas the existing transcription is usually the machine reader's own earlier visual judgment. Showing that old judgment during a second visual pass creates anchoring: the machine can reproduce its first interpretation without adding independent evidence.

Review therefore proceeds in this order:

1. Temporarily disregard the current transcription and do not begin by rereading its disputed form.
2. Analyse the proposal from Japanese morphology and lexicon, Portuguese grammar and historical spelling, the bilingual definition, and relevant headword or scholarly evidence. Write down the plausible linguistic forms and the distinctions the image must decide.
3. Treat a linguistically coherent human proposal as the leading hypothesis, especially when the old form fails to parse or breaks an expected inflectional series.
4. Inspect the scan afresh and actively look for the proposed reading, then compare only genuinely discriminating same-page glyphs and marks.
5. Accept the proposal when the image is compatible with it and linguistic evidence materially favors it. The old reading's continued visual possibility is not a reason to retain it.
6. Retain the old reading only when the scan supplies positive contrary evidence strong enough to outweigh the linguistic case. If neither reading can be settled, request human re-check.

This is evidence-weighting, not silent normalization. An unmistakably printed anomaly remains literal Level 1 text even when its intended word is certain. Linguistic priority governs hypothesis formation and ambiguous evidence; it does not authorize replacing clear type with an expected form.

An explicit human pre-confirmation attached to a second-opinion item is already an adjudication, not merely supporting commentary. When the comment states that the reviewer has inspected the relevant feature and records the resulting decision—for example, confirming that a visibly slanted Japanese word is nevertheless roman type—the machine skips that stated visual check and applies the exact submitted correction. It must not reopen the same distinction merely because it is difficult for machine vision. A comment that only supplies context, a hypothesis, or a reason to inspect the scan follows the ordinary second-opinion procedure. In the UI, a reader who intends the former may also clear the automatically selected checkbox and submit the item as human-settled.

The machine reviewer accepts and applies every proposal supported by this combined linguistic-first and visual test. A proposal it cannot substantiate is provisionally rejected and marked **Human re-check required**. Here, *rejected* means only *not independently verified by the machine reviewer*; it does not mean that the proposal has been proved incorrect. The machine must state the positive contrary evidence or the exact unresolved distinction rather than merely report that the old reading still looks possible.

A machine-derived **qualified form** is also a new proposal, not an automatic acceptance. If the submitted `after` text appears substantially right but the machine would change any textual content, spacing, punctuation, diacritic, or styling within it, the machine must not silently substitute and apply that third form. It records the exact submitted form, exact qualified form, and reason for the difference, then marks the item **Human re-check required**. Only an exact submitted correction may be applied without this extra confirmation. Purely explanatory paraphrase does not trigger the rule. Issue #16 provides the control example: submitted `Tçuquiami` was qualified to scan- and language-supported `Tçuqiami`, but the qualified form required and received explicit human confirmation.

The human reviewer then re-examines each provisionally rejected item. The reviewer may withdraw the proposal or explicitly override the machine judgment when confident that the proposed reading is correct. An explicit human override is the final adjudication for that Issue item: apply it without reopening the same visual dispute, and retain the Issue discussion as the record of the machine's initial uncertainty and the human decision. An override may inform later error analysis, but it does not become a volume-wide transcription rule without broader evidence.

An Issue remains open while any item is marked **Human re-check required**. Close it only after every submitted item has reached one of these states:

- accepted and applied after machine verification;
- explicitly withdrawn by the human reviewer; or
- accepted and applied by explicit human override.

This makes the Issue the durable adjudication checklist and prevents a provisional rejection from being mistaken for a settled decision.

This prior does not authorize automatic acceptance or normalization. The scan remains the Level 1 authority, and a partly correct proposal should be refined rather than accepted or rejected wholesale. The f20 correction `Aguetçire. i. l. catune.` → submitted `Aguebune. i. ſ. cabune.` illustrates both points: repeated inspection anchored on the old transcription reproduced the same mistaken shapes, while independent evidence for 上げ槽 *aguebune* and 酒槽 *sacabune* supplied the useful hypothesis. Renewed inspection then supported the qualified continuous reading `Aguebune. i. ſacabune.` rather than either complete string. Issue 14 supplies the broader control case: linguistic analysis strongly favored `Amabiyori`, `qeru`, `ru`, `Amagayeru`, and `Amajiuono uo`, but a visually anchored second pass provisionally retained the machine's earlier anomalous readings. Enlarged human reinspection confirmed the proposals. Future Issue review must perform that linguistic analysis before viewing the old disputed reading.

## Transcription-character input

In the collapsed line view, common corrections can be made directly on the displayed transcription. Clicking `s`, `ſ`, or `f` cycles the plausible printed forms according to the line's original character; `g` and `q` toggle in both directions; lowercase `u` and `v` likewise toggle in both directions; clicking a vowel cycles its plain, tilde, grave, acute, and relevant circumflex/caron forms. Clicking an italic Portuguese word's initial capital toggles a Roman-type annotation. Spaces, hyphens, commas, and periods can be clicked to remove them. A compact visible marker remains at every such deletion and can be clicked to restore the exact character. Clicking unused space beside the transcription still opens the complete line editor. These controls only construct the ordinary `after` string (including the existing `[]` typeface notation), so copied schema-2 correction JSON and Issue application require no special quick-edit format.

The line editor provides a compact transcription-character palette. Number keys `1`–`9` insert the character shown on the corresponding button while the transcription field is focused: `ſ`, `ç`, tilde, grave, acute, `ǒ`, `ǔ`, `ô`, and `û`. The three accent buttons apply their mark to a selected single letter or to the letter immediately before the caret; output is normalized to NFC except for combinations such as `q̃` that have no precomposed Unicode character. A **Literal digits** control temporarily restores ordinary numeric input for the uncommon correction that must introduce or change a printed number.

The correction field has paired lightweight typeface annotations. Select text and press **Roman** to wrap it as `[Fotoqe]`, or press **Italic** to wrap it as `{P.}`. Square brackets force roman type and curly braces force italic type; neither pair is a literal transcription character in a correction proposal. The row preview removes the delimiters, renders the selected text in the requested typeface, and highlights the styling correction. Submitted JSON retains the notation so the Issue remains readable, while Issue application converts each span into the corresponding canonical Markdown run boundary. Typeface spans may be separate, but cannot be empty, nested, or overlapping. If a genuine square or curly bracket is encountered in the source, the notation will be revised interactively rather than adding an unused escaping system now.

An asterisk immediately before or after a word supplies a second lightweight proposal annotation without adding a dedicated UI control. When the word has one tilde in an adjacent-vowel sequence and exactly one unambiguous alternative carrier, `*word` or `word*` means **move that tilde to the other vowel and change nothing else**: submitted `*mãos` or `mãos*` requests `maõs`, and `*dalguã` or `dalguã*` requests `dalgũa`. The asterisk is an instruction only; Issue application removes it, moves the combining mark, normalizes the result to NFC where possible, and never writes `*` into canonical Level 1 text. It does not mean general uncertainty. If the local sequence has three or more plausible carriers, the word has multiple tildes, or any other reading is in question, the reviewer must instead supply the complete intended spelling or explain it in a comment. No special editor behavior is required: the current plain-text editor displays the marker as an ordinary proposed difference and preserves it in the submitted JSON for Issue adjudication; it does not preview the requested carrier move.

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
