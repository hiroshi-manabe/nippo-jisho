# Human Review and Correction Workflow

## Purpose

The public review interface should make scan comparison easy without claiming that a page has become definitively correct. Most lines will receive no correction, so the ordinary view must stay compact. When a reader does find a problem, the interface should capture a precise, inspectable proposal that can be discussed and applied through GitHub.

This document specifies the behavior and rationale of the current [dictionary-wide review interface](../pilot/human-review/README.md). Experimental or future-facing sections are marked where they do not yet describe a deployed control.

## Two complementary views

### Page overview

The front page presents all acquired leaves as a responsive thumbnail grid in Gallica order. Each page card shows:

- the `f` identifier and scan thumbnail;
- the data state: canonical Level 1, machine-provisional OCR, or scan only;
- the number of applied correction Issues;
- the number of distinct lines corrected;
- optionally, the most recent correction date.

The badges report provenance and activity, not quality. A page with no corrections is not thereby verified, and a page with many corrections is not necessarily worse. Clicking a card opens the page review view. Page order is the default; filters separate all reviewable pages, canonical pages, provisional candidates, structural quarantines, scan-only pages, and pages with corrections.

Machine-provisional candidates remain editable because review is their purpose, but they must never be visually conflated with canonical Level 1. Their cards and page badges use a distinct amber state, every candidate page states that its lineation and geometry remain unchecked, and structurally quarantined candidates also show their recorded reason. Display and correction do not change `physical_lineation_checked: false` or move the package into the canonical tree.

### Page review

The page view retains full-page and column context, but the physical line is the primary checking unit. For each line, the scan strip is placed above its transcription, and both use the same practical horizontal extent. This makes the characters in the image and transcription directly comparable from left to right.

The sticky page-navigation bar includes an explicit **← All pages** button. The project title also returns to the overview, but it is not the sole or implicit way out of an individual page.

Every displayed physical-line ID has a compact copy control beside it.  The
control copies the page-qualified stable reference, such as
`f126/c2-l039`, so a reviewer can cite the location in chat or research notes
without reconstructing the leaf number manually.  It is available in both the
column cards and the continuous page view and does not open the line editor.

Column views also form one continuous review sequence over all reviewable material: a page's column 1 is followed by its column 2, then by column 1 of the next canonical or provisional page. **Previous column** and **Next column** controls appear above the line list and repeat after its final line, where the reviewer naturally decides whether to continue. Moving between columns opens the target at its beginning rather than retaining the previous column's scroll position. Full-page, furniture, and scan-only views do not show these controls; the ordinary page arrows remain independent.

Unchanged rows remain compact. Clicking the transcription opens an editor containing:

- the editable transcription;
- an optional durable line note;
- an optional **Message to AI**;
- **OK** and **Cancel** actions.

**OK** confirms the local proposal and collapses the editor. Pressing **Enter** in the transcription field does the same thing: each record represents one physical printed line, so a newline is not valid transcription content. Enter remains available normally in the note and message fields. IME composition is exempt so that confirming composed input does not close the editor. Opening another line has the same save-and-collapse effect on the active editor before the new one opens, so moving through the page cannot silently discard typed text, notes, or messages. **Cancel** remains the explicit way to discard changes made during that editing session. A changed row can be reopened, and a **Revert** action restores the repository text and durable note.

The durable note belongs to the Level 1 line annotation and may record linguistic reasoning, uncertainty, damage, or another lasting observation. The Message to AI belongs only to the review workspace and correction Issue. Any nonempty message requires AI inspection; there is no separate second-opinion checkbox. The processor mechanically applies settled rows, pauses on messaged rows, and never promotes a temporary message into the durable note without an explicit note change.

In compact form, the durable note occupies its own full-width row below the transcription and wraps normally. This keeps both the diplomatic line and a substantial linguistic note readable without opening the editor. The note remains a button that opens the complete editor. A temporary message is also shown while the editor is collapsed, in its own separately labelled row rather than being reduced to an attention marker or merged with the durable note. Both rows remain visually secondary to the source text, and either reopens the complete editor.

## Transcription reference panel

The page-review toolbar provides a persistent **Reference** control. It opens a lightweight panel containing the compact [Transcription Cheat Sheet](transcription-cheat-sheet.md), which is the routine operational reference for Japanese romanization, Early Modern Portuguese type, marks, spacing, and recurring visual confusions. Individual topics link to the fuller [Historical Language Notes](historical-language-notes.md) for qualifications, evidence, bibliography, and source provenance.

The panel is closed by default and must not permanently narrow the scan or transcription area. Its state may remain open while the reviewer moves among lines or pages. On the all-page overview, ordinary links to both documents are sufficient; the embedded panel is primarily a line-review aid.

The interface displays the reference source commit or version so that later users can identify which guidance was available during a review. The panel is advisory: it helps generate candidates, but no linguistic expectation overrides the printed scan.

## Visual diff

The collapsed changed row highlights the difference between the repository text and proposed text. This diff is a client-side reading aid only:

- it may use a simple character- or word-level algorithm;
- an awkward comparison may fall back to highlighting a whole word or line;
- the generated diff is not stored or submitted;
- only the original and proposed text, durable note change, and optional AI message are evidence.

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

### OCR-first candidate geometry

When ordered Level 1 line texts already exist but their rectangles are absent or
untrustworthy, initialize geometry without consulting the saved rectangles.
Run an independent neural line segmenter on the native page, rectify every
detected polygon, recognize each strip with the book-specific OCR model, and
align those noisy strings monotonically to the transcription's document order.
Headers, catchwords, and split fragments remain extra candidates that the
alignment may skip. The transcription supplies line identity and sequence; OCR
supplies correspondence evidence, not diplomatic text.

Production column boxes, line centres, crops, and context crops must remain
unopened until the proposed associations and rectangles have been serialized.
They may then be compared with the proposal as benchmark evidence. This makes
"treat the old geometry as untrusted" an enforceable data boundary rather than
an instruction to discount coordinates after they have already anchored the
result.

The first blind benchmark used `f147`, `f151`, the skewed `f154`, and the
previously troublesome `f157`. It aligned all 377 body lines from 396 blind
segmenter candidates, left 19 furniture or split-fragment candidates unused,
and produced no unmatched body line or OCR-to-neighbour conflict. Median
relaxed line CER was 10.0%; that is adequate for correspondence even though it
is not adequate diplomatic transcription. Reproducible code and aggregate
results are in
[`align_page_geometry_ocr_first.py`](../scripts/align_page_geometry_ocr_first.py)
and
[`ocr-first-geometry-v1-results.json`](../experiments/ocr/ocr-first-geometry-v1-results.json).

The benchmark is reproduced by first writing Kraken native segmentation JSON
for the chosen scans, rectifying it in the isolated Kraken environment, and
then running the aligner in the OCR environment:

```sh
for number in 0147 0151 0154 0157; do
  .cache/ocr-model/venv-kraken/bin/kraken \
    -i build/nippo-jisho-images/scans/native/f${number}.jpg \
    .cache/ocr-first-geometry-v1/segmentation/f${number}.json segment -bl
done
.cache/ocr-model/venv-kraken/bin/python scripts/extract_kraken_lines.py \
  --pages 147 151 154 157 \
  --kraken .cache/ocr-first-geometry-v1/segmentation \
  --output .cache/ocr-first-geometry-v1/extracted
.cache/ocr-model/venv-arm64/bin/python \
  scripts/align_page_geometry_ocr_first.py --pages 147 151 154 157
```

This method is now the preferred **initializer** for an already-transcribed
page. It does not confer geometry-review status. Its output still has to pass
every item in the acceptance routine below, at full browser-review scale, and
must be manually adjusted wherever a polygon split, displaced fragment,
diacritic, rule edge, or slanted baseline makes the rectangular review crop
incomplete.

The first production-scale trial applied the initializer to `f161`–`f170`.
It matched all 943 body lines from 990 blind candidates and left 47 furniture
or fragment candidates unused. One very short, badly recognized row,
`f164/c2-l007` (`ros ſae.`), was initially left unmatched. It was accepted only
because exactly one candidate lay between its already matched immediate
neighbors and the native scan confirmed the complete text in that strip. This
defines the sole positional rescue rule: one missing reference, one unused
candidate, and matched immediate neighbors on both sides. Multiple-row gaps,
edge gaps, or more than one candidate still stop automatic import. The same
scan check accepted f164's final `tas folhas.` association despite its garbled
OCR. Aggregate evidence is recorded in
[`ocr-first-geometry-f161-f170-results.json`](../experiments/ocr/ocr-first-geometry-f161-f170-results.json).

The imported columns retain the conservative `contact_sheet_reviewed` state;
the OCR initializer and overview audit do not upgrade them to
`line_by_line_reverified`.

### Acceptance routine

For either case, the final requirements are:

1. Verify the column's horizontal rectangle against the full-resolution page. Both ends of every ordinary line must be present; a large blank margin on one side is a warning that the opposite end may be clipped. The relevant printed vertical rule must itself remain visible, with a small margin beyond it: seeing all currently recognized text is not enough, because a crop ending before the rule cannot prove that no terminal mark or faint letter was lost. On a skewed page, do not force the whole column into one fixed `x`/`width`: identify the four printed vertical rules (the two outer rules and both sides of the central gutter), interpolate each rule down the page, and derive each line's horizontal bounds from the rule positions across that line's own vertical span. Retain a small margin outside the rules and inspect the result; the fitted trajectory is only a starting model, not visual evidence by itself.
2. Choose several vertical anchors across the column and generate scan-snapped initial line centres. A single top-to-bottom interpolation is insufficient evidence that intermediate lines are aligned.
3. Generate a complete column contact sheet pairing every stable line ID with its proposed crop as an overview and line-order diagnostic. This overview is not acceptance evidence by itself.
4. After writing the proposed coordinates to the canonical geometry file, run `python3 scripts/audit_line_geometry.py --first N --last N`. Open **every generated crop card individually at the normal browser-review scale**, with its assigned transcription visible immediately below it. Read the target from the image itself before using the transcription as confirmation. The complete assigned physical line must be independently readable and must be the primary line in the strip; visibility of a few target letters through overlap does not pass. Confirm the first and last printed tokens and terminal punctuation as well as the middle of the line. In particular, the first body card must not show the running header in place of the first body line, and the assigned text must not appear primarily in the preceding or following card.
5. Reject a crop when target ink touches or nearly touches a vertical or horizontal edge unless enlarged context proves that the complete glyph is present. Small descenders and diacritics require full-size inspection; a reduced contact sheet cannot establish this.
6. Add intermediate ranges or explicit per-line centre overrides wherever the generated centres drift. If even one card from a uniformly interpolated range fails the primary-line test, treat the entire range as unverified: inspect every card in it and, unless a new set of anchors demonstrably fixes every row, replace the range with measured per-line centres. A local patch must not leave the same failed interpolation authoritative for neighboring lines. Manual adjustment of every line is required when that is what the page needs.
7. Expand individual rectangles upward or downward when any target glyph is incomplete or ambiguous.
8. Permit overlap with an adjacent line whenever necessary for a complete reading.
9. Avoid unnecessary padding where a natural boundary is clear.
10. Commit an explicit source-pixel rectangle for every column line, including crops accepted without individual adjustment.

The first skew-aware retrofit covers `f13`–`f30`. Its four rule trajectories are recorded reproducibly in `scripts/align_early_column_rules.py`; the command changes only horizontal bounds and deliberately preserves the previously reviewed `y`/height of every line and context crop. Any future rerun still requires a fresh isolated-card audit of every affected line before the resulting geometry is accepted.

This geometry pass is a required part of processing a page, not optional interface polish. A page-level geometry status is earned only after every browser-facing line crop regenerated from the committed coordinates has passed the crop-to-transcription inspection above. Reviewing proposed rectangles before they are written, or merely checking that their sequence looks regular, is insufficient. The geometry record stores the source dimensions, crop and context rectangle for every stable line ID, review state, and review date. Later regeneration must fail if a processed column line lacks explicit geometry.

The existing `contact_sheet_reviewed` records were reconstructed after transcription and are provisional: they say that a contact sheet was inspected, not that every full-size UI crop is complete. New pages whose rectangles are preserved during line-by-line transcription may use `captured_during_transcription`; reconstructed pages may use `line_by_line_reverified` only after the same individual browser-scale check has subsequently been completed. Historical delegated geometry retains provenance values such as `ai_line_by_line_checked`, `ai_bulk_geometry_sanity_checked`, and `external_ai_width_rechecked`; these describe how an existing coordinate decision entered the record and do not claim human verification or transcription correctness. The external-AI workflow that created them was retired on 2026-08-30. New geometry must use the ordinary capture-and-verification process rather than extending those provenance classes.

A line may be vertically centered and still unusable if its first or last glyph is outside the crop. Historical imported geometry therefore required horizontal-completeness checks independent of line identification. For ordinary two-column pages, a conservative crop spanning slightly beyond both column rules remains preferable to a tight fixed-width crop. The retained status `external_ai_width_rechecked` means that externally supplied vertical coordinates were kept but every affected line was subsequently expanded to audited rule-to-rule horizontal coverage; it is legacy provenance, not a current review stage.

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

## General-AI commented page review

During this review, identify Japanese terms embedded in Portuguese explanations whose typeface the human may want to change. Add the page ID, line ID, exact current plain `source_text`, and a `terms` list to `pilot/human-review/typeface-toggle-terms.json` (see f164 for examples). Do this regardless of whether the term is currently roman or italic. Do not mark ordinary Japanese headwords, Japanese synonyms introduced by `i,`, or Japanese examples merely because italic text precedes them. The public builder enables whole-word clicking only on matching marked lines. If the canonical line text changes, refresh the annotation after checking its context; until then the old annotation is inactive. These controls do not change transcription versions or Issue payloads.

Before a page is handed to the human reviewer, the general-AI review uses two
separate complete passes.

1. **Commented contextual reading:** read every physical line against its scan
   crop, considering the Japanese, Jesuit romanization, Portuguese, and the
   bilingual relationship while proceeding through the page. Write a
   substantive English durable note for **every body line**, including short,
   apparently obvious, and continuation lines. Explain the Japanese meaning
   or morphology, the Portuguese sense, or how the fragment connects with
   neighboring lines, as appropriate. Use the generated kana guide as a
   reference, but do not merely copy it as the note. Write these comments
   during the reading pass, not as filler added after declaring review complete.
   Suspicious words receive particular attention: the note should say
   what is suspicious, give the plausible reading or interpretation, and name
   the evidence that would decide it. Boilerplate such as “checked” does not
   satisfy this requirement. A plausible explanation must never silently normalize the
   diplomatic transcription.
2. **Fresh whole-page pass:** after reaching the end, return to the beginning
   and inspect every line once more.  Treat the first-pass transcription and
   notes as provisional rather than as authority.  Look specifically for
   omissions and wrong-line associations, Japanese forms that fail to parse,
   incoherent Portuguese, misleading word boundaries or typeface, diacritics,
   `s`/`ſ`/`f`, punctuation, spacing, and terminal line-division signs.  A new
   finding is corrected only when compatible with the scan; its note is then
   updated if the reasoning remains useful.

Before declaring this commented review complete, check that every body-line ID
has a nonempty, substantive English note and that the fresh whole-page pass
has been completed. Include displaced body fragments; running headers, page
numbers, signatures, and catchwords do not require routine commentary. Report
any missing body-line notes as unfinished work, with their IDs, rather than
silently exempting them. Note coverage is a necessary completion check, not
proof of accurate reading: empty filler and mechanically duplicated notes do
not establish review. An older “AI checked” label alone does not establish
completion of this stricter procedure.

The durable note produced here is part of the canonical line annotation and is
shown to the human reviewer.  It is distinct from the temporary **Message to
AI** field used by the human reviewer when submitting a correction.  Comments
should preserve useful reasoning and genuine doubt, not become a transcript of
routine internal deliberation.

During both passes, OCR is strongest evidence for locally aligned but
linguistically arbitrary graphic features, such as the position or identity of
a diacritic, line-end punctuation, and short versus long `s`.  Linguistic and
lexical evidence carries more weight when the alternatives change the Japanese
or Portuguese analysis, especially for headword identity and morphology.  The
balance selects reinspection hypotheses; the scan remains the Level 1
authority.

## Automatic kana guide

The four *yotsugana* spellings remain distinct in hints: `ji` → ジ, `gi` → ヂ, `zu` → ズ, and `zzu` → ヅ (for example, `mizzu` → ミヅ). Follow the actual printed spelling, including historical inconsistencies, rather than restoring an expected etymological form. This affects generated hints only. The correspondence is documented in [Kishimoto Emi's study of the manuscript Portuguese–Japanese dictionary, opening transcription table](https://repository.kulib.kyoto-u.ac.jp/bitstream/2433/137262/1/kkr00001_001b.pdf).

Every prepared human or general-AI review line carries a read-only `reading_hint`, generated during the public-review build from the exact baseline transcription. It pairs each detected upright Japanese phrase with a mechanical katakana rendering, for example `Facuran/ハクラン, Firoqu miru/ヒロク ミル`. This is a mandatory review aid, not a new transcription field. The generator explicitly handles common dictionary spellings such as `q`, `tç`, `x`, initial `v`, intervocalic `u`, labialized `qua`/`gua` (`Quacuran` → クヮクラン), and the silent orthographic `u` in `gue`/`gui` (`Xiraſagui` → シラサギ); Portuguese italic text and recognized editorial labels are excluded. Failure is displayed explicitly rather than silently hiding the guide.

Standalone editorial abbreviations inside Roman-type Japanese material, including `i` and Latin `l` (*vel*, “or”), are excluded without suppressing the surrounding Japanese reading. A visible fragment of a Roman-type Japanese word divided across physical lines is still rendered mechanically on each line: for example, the second-line `qu` of `fa-` + `qu` is shown as `qu/ク`. The accompanying note or transcription context, rather than the reading hint itself, records that it is not an independent word.

The mechanical guide also recognizes common boundaries and historical spellings that cannot be recovered by converting each apparent syllable independently. Thus `-nuo` is segmented as word-final `-n` plus particle `uo` when a vowel follows the `u` (`Quǒguenuo` → `クオゥゲンヲ`), and Jesuit `gi` before another vowel is rendered with the historical voiced palatal series (`cotogia` → `コトヂャ`, modern コトジャ).

The guide is intended to make Japanese linguistic checking faster. An implausible output can flag likely `q/g` confusions, omitted or substituted letters, bad word boundaries, impossible inflectional forms, and some mistaken long-vowel marks. It is not reliable evidence for typeface, physical spacing, line-division signs, punctuation, or graphic allographs such as long and short `s`. A suspicious kana result starts renewed linguistic and scan review; it never edits Level 1, enters correction JSON, or substitutes for visual confirmation.

Because the guide is fully derived, its output is not stored in canonical Markdown or interchange records, is not editable, and does not affect the transcription version or Issue payload. It is regenerated after accepted textual changes on the next build; live JavaScript regeneration from an unsaved edit is deliberately unnecessary. This keeps Level 1 diplomatic and human-readable while providing in the interface the same provisional kana conversion that an experienced reviewer would otherwise perform mentally. Reviewed Japanese-script restoration, kanji selection, segmentation, and translation remain Stage 3 work.

## GitHub Issue submission

The overview's **Select pages to submit** mode turns page cards into multi-select buttons. Only pages with locally saved corrections can be selected; cards show their saved correction count and submitted status. **Submit selected pages** checks every selected baseline, copies one combined JSON payload, and opens a single empty Issue with an automatically generated title. The overview then asks whether that combined Issue was submitted and updates the included pages together. Existing single-page submission remains available.

Combined submissions use `{"schema": 4, "pages": [...]}`, where each element is a complete schema-3 page payload with its own page identifier, baseline commit, transcription version, and changes. Duplicate pages are invalid. The processor resolves and validates all included pages before writing any of them, applies unflagged changes, and keeps page-specific pending review decisions in the preparation report. It closes the single Issue only after all pages are settled, records that Issue separately in each page's history, and verifies every included page after deployment. Plain JSON and older fenced payloads are both accepted.

The interface prepares corrections page by page. A submission contains only rows whose edits have been confirmed with **OK**. Before submission, the reader can inspect the collected changes.

The Issue body must not be placed in a GitHub `issues/new` query parameter. GitHub documents query prefilling but does not promise a usable maximum URL length, and realistic multi-correction payloads can exceed browser, intermediary, or server limits. Compact JSON reduces the risk but does not remove it, especially when notes or messages contain Japanese text.

The submission flow is therefore:

1. Serialize the confirmed page corrections as readable schema-3 JSON. Durable annotation changes use `note_after`; temporary requests use `message`.
2. Copy the complete payload to the clipboard.
3. Open a short GitHub Issue URL containing only the template selection and a page-specific title.
4. Ask the reader to paste the copied JSON directly into the initially empty Issue body. The template retains the automatic title and correction label but supplies no prose, code-block wrapper, or formatted preview. The application script accepts plain JSON as well as the fenced JSON used by earlier Issues.
5. Retain the local draft until the reader explicitly clears it.

After the Issue composer opens, the review tab changes to ask whether the Issue was actually submitted. Confirming this does not delete the local draft: it changes the bar to a compact **Marked as submitted** state with a **Submit again** escape hatch. Choosing **Not yet**, editing any line, or explicitly submitting again returns the page to draft state. This local state is persisted per page so returning to or reloading the review tab does not make the submission ambiguous.

Each local page workspace records a review-baseline version derived only from the ordered line IDs, transcription text, typeface runs, and durable notes. Generated readings, scan crops, thumbnails, correction-history badges, other metadata, and interface code do not affect this version. When repository text or notes change, saved edits based on the earlier baseline must not be restored as though they were current.

The page version is only a trigger for line-level reconciliation. Every saved edit also records the content version of its stable physical-line ID. Unchanged edited lines retain their proposals silently, even when another line on the page changed. If the current repository text equals a saved proposal, that textual correction is removed as already incorporated. Otherwise a changed edited line is automatically rebased: its current repository text becomes the new `before`, its saved proposal remains the `after`, and the row receives a persistent **Base updated** marker. A page notice reports the number of affected rows. Confirming a highlighted row with **OK** clears its marker; rebasing any submitted row returns the workspace to draft status.

A durable note is canonical annotation whose continued relevance cannot be decided by text equality. When its line changes, a locally edited note is preserved and marked **Note needs review** until the reviewer confirms the row. A temporary message is likewise preserved across rebasing but never becomes canonical data.

Only a missing stable line ID prevents automatic rebasing. In that exceptional case, unaffected edits are retained while a blocking warning lets the reviewer copy and then discard the orphaned records. Pre-versioning browser data is migrated once against the first version-aware corpus rather than being discarded without a known comparison point. This is deliberately simple optimistic concurrency control; the browser never attempts to synthesize a textual merge.

Edited rows must continue to render the original Level 1 typeface runs. Diff highlighting is an additional visual layer; it must not flatten italic Portuguese and roman Japanese into one style.

If clipboard access fails, the interface displays the payload in a selectable text area. Direct GitHub API submission is deliberately deferred because a static GitHub Pages site should not contain a privileged token, and an authentication service is unnecessary for the initial workflow.

A representative payload is:

```json
{
  "schema": 3,
  "page": "f17",
  "base_commit": "abc1234",
  "base_transcription_version": "sha256:0123456789abcdef…",
  "changes": [
    {
      "line": "c1-l026",
      "before": "Acuni toingiacu ſuru.",
      "after": "Acuni tongiacu ſuru.",
      "note_before": "",
      "note_after": "Japanese 頓着 supports tongiacu.",
      "message": "Please verify the damaged g/q shape."
    }
  ]
}
```

`before` and `note_before` protect against silently applying a correction to text or durable annotation that has subsequently changed. In schema 3, an absent or empty `message` means that the human reviewer has settled the exact correction and asks for mechanical application. A nonempty message requires AI inspection. The processor retains schema-2 compatibility for already-created Issues, treating an old `comment` as a temporary message and `second_opinion: true` as requiring inspection, but the interface creates schema 3 only.

Issue processing is deliberately two-stage. First validate the page, base version, line IDs, text, notes, and correction notation, then mechanically apply every schema-3 change without a message. Do not reopen those glyph judgments merely because machine vision would have read them differently. Next, perform the detailed linguistic-first and visual review below only for rows carrying a message. Do not commit, push, or close the Issue until that set is settled. If no messages are present, the validated mechanical application may proceed directly through tests, commit, deployment, and Issue closure.

### Automated Issue processor

The normal first action for a correction Issue is:

```sh
python3 scripts/process_correction_issue.py process ISSUE_NUMBER
```

The command takes an explicit Issue number; it never selects an Issue implicitly. It fetches one schema-2 or schema-3 payload, verifies that the Issue is open and its base commit exists, validates every stable line ID and baseline value, resolves lightweight `*word`, `[roman]`, and `{italic}` notation, and applies all unmessaged changes to the page's editable source. Canonical pages update compact Level 1 Markdown; machine-provisional pages update their candidate package in place and remain provisional. Unknown lines, changed baseline text or notes, ambiguous notation, multiple payload blocks, and schema 1 are hard errors. Existing layout metadata is retained through textual edits.

After application, the processor writes its report before validation, recompiles canonical interchange JSON and views when applicable, rebuilds the public review artifact, and runs the complete test suite. A validation failure leaves the Issue open and permits a repeat invocation to recognize already-applied targets. If no AI message is present, it updates correction history, commits, pushes `main`, verifies deployment, comments on the Issue, and closes it. A failure before deployed verification leaves the Issue open.

If one or more schema-3 changes contain a nonempty `message`, the processor applies and validates only the unmessaged subset, writes `build/correction-issues/issue-N.json`, prints its path, and exits with status 3. No history update, commit, push, deployment, or Issue closure occurs. Each messaged item begins with `"decision": "pending"`. Schema-2 `second_opinion` items follow the same compatibility path. After review, the machine reviewer records one of:

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

An explicit human pre-confirmation in a Message to AI is already an adjudication, not merely supporting commentary. When the message states that the reviewer has inspected the relevant feature and records the resulting decision—for example, confirming that a visibly slanted Japanese word is nevertheless roman type—the machine skips that stated visual check and applies the exact submitted correction. It must not reopen the same distinction merely because it is difficult for machine vision. A message that only supplies context, a hypothesis, or a reason to inspect the scan follows the ordinary review procedure.

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

Plain lowercase `a` is excluded from the independent one-letter typeface toggle because it is common prose and must retain the vowel/accent quick edit. Standalone body-text `S.` is recorded in italic type; section headings such as `A ANTES DO S.` remain display type.

In the collapsed line view, common corrections can be made directly on the displayed transcription. Clicking `s`, `ſ`, or `f` cycles the plausible printed forms according to the line's original character; `g` and `q` toggle in both directions. Lowercase `c/ç` is also a two-way toggle. Lowercase `n/m` normally toggles in the same way, but a consonant immediately preceded by a plain vowel and not followed by a vowel has a base-aware third state: original `n` cycles `n → m →` nasalized preceding vowel `→ n`, while original `m` cycles `m → n →` nasalized preceding vowel `→ m`. Thus original `membro` can become `menbro` and then `mẽbro`; clicking the generated `ẽ` restores the exact original `em`. This restoration record remains in saved browser work across rerenders and reloads but is excluded from copied schema-2 correction JSON. An originally printed `ẽ` does not acquire an inferred expansion because the scan alone may not determine `em` versus `en`. Lowercase `u/v` and `i/j` use similar base-aware cycles: a printed `u` cycles `u → v → ũ → ù → ú → û → ǔ → u`, while a printed `v` only toggles `v → u → v`; correspondingly, a printed `i` cycles `i → j → ĩ → ì → í → î → i`, while a printed `j` only toggles `j → i → j`. Uppercase `N/M`, `C/Ç`, `U/V`, and `I/J` are not quick-edit targets. Other vowels cycle their plain, tilde, grave, acute, and relevant circumflex/caron forms. These cycles retain the printed base character: an original `ǒ` begins `ǒ → ô → …`, while an original `ô` begins `ô → ǒ → …`; original `ǔ` and `û` behave analogously. Whole-word typeface toggles are explicitly enabled for Japanese terms embedded in Portuguese explanations during AI review. They are scoped to the marked physical line; a corpus vocabulary or an earlier italic run alone does not enable them. The former general rule for capital-initial, period-ending words has been removed. Independent one-letter tokens remain special, except for lowercase `a`: clicking the letter in a bare `l` or a token such as `i.`, `l.`, `S.`, or `X.` toggles the whole token's typeface instead of invoking its ordinary letter or accent cycle. Clicking a final period retains the ordinary punctuation control. Spaces, hyphens, commas, and periods can be clicked to remove them. A compact visible marker remains at every such deletion and can be clicked to restore the exact character. Clicking unused space beside the transcription still opens the complete line editor. These controls only construct the ordinary `after` string (including the existing `[]` and `{}` typeface notation), so copied schema-2 correction JSON and Issue application require no special quick-edit format.

For an evidence-qualified OCR disagreement at a physical line end, the same mechanism may begin with the canonical terminal hyphen already removed. Such a row is marked `OCR: no hyphen`, and its yellow deletion marker restores the hyphen with one click. Restoration dismisses that suggestion for the exact transcription-line version and is retained in local workspace data. Leaving the provisional deletion in place includes it as an ordinary correction; restoring it removes that correction. OCR suggestions never add a special field to copied schema-2 JSON and never modify the canonical source merely by appearing in the interface. The qualification and the initial `f154`–`f160` pilot are documented in [Provisional OCR-Assisted Reading Policy](ocr-assisted-reading.md#reversible-terminal-hyphen-proposals).

The line editor provides a compact transcription-character palette. Number keys `1`–`9` insert the character shown on the corresponding button while the transcription field is focused: `ſ`, `ç`, tilde, grave, acute, `ǒ`, `ǔ`, `ô`, and `û`. The three accent buttons apply their mark to a selected single letter or to the letter immediately before the caret; output is normalized to NFC except for combinations such as `q̃` that have no precomposed Unicode character. A **Literal digits** control temporarily restores ordinary numeric input for the uncommon correction that must introduce or change a printed number.

The correction field has paired lightweight typeface annotations. Select text and press **Roman** to wrap it as `[Fotoqe]`, or press **Italic** to wrap it as `{P.}`. Square brackets force roman type and curly braces force italic type; neither pair is a literal transcription character in a correction proposal. The row preview removes the delimiters, renders the selected text in the requested typeface, and highlights the styling correction. Submitted JSON retains the notation so the Issue remains readable, while Issue application converts each span into the corresponding canonical Markdown run boundary. Typeface spans may be separate, but cannot be empty, nested, or overlapping. If a genuine square or curly bracket is encountered in the source, the notation will be revised interactively rather than adding an unused escaping system now.

An asterisk immediately before or after a word supplies a second lightweight proposal annotation without adding a dedicated UI control. When the word has one tilde in an adjacent-vowel sequence and exactly one unambiguous alternative carrier, `*word` or `word*` means **move that tilde to the other vowel and change nothing else**: submitted `*mãos` or `mãos*` requests `maõs`, and `*dalguã` or `dalguã*` requests `dalgũa`. The asterisk is an instruction only; Issue application removes it, moves the combining mark, normalizes the result to NFC where possible, and never writes `*` into canonical Level 1 text. It does not mean general uncertainty. If the local sequence has three or more plausible carriers, the word has multiple tildes, or any other reading is in question, the reviewer must instead supply the complete intended spelling or explain it in a comment. No special editor behavior is required: the current plain-text editor displays the marker as an ordinary proposed difference and preserves it in the submitted JSON for Issue adjudication; it does not preview the requested carrier move.

## Correction history, not certification

Git records the complete technical history, while Issues retain discussion and the submitted proposal. The page view exposes a compact floating factual summary. Its closed form reports the review stage (`Machine draft` or `AI checked`), the local date and time of the page transcription's own most recent Git revision, and the number of applied correction Issues. Expanding it reveals the full timestamp, exact baseline commit, and corrected-line count. It deliberately does not claim that an AI or human is currently working. The interface fetches the corpus without browser caching, checks again when the tab regains focus and immediately before submission, and blocks submission if the current page's transcription version has changed; reloading then invokes the existing line-wise saved-edit reconciliation.

The generated interface also exposes this factual correction summary for each page:

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
