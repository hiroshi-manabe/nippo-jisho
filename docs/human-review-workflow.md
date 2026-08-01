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

Unchanged rows remain compact. Clicking the transcription opens an editor containing:

- the editable transcription;
- an optional comment;
- **OK** and **Cancel** actions.

**OK** confirms the local proposal and collapses the editor. **Cancel** discards changes made during that editing session. A changed row can be reopened, and a **Revert** action restores the repository text.

In compact form, a comment uses the horizontal space remaining to the right of the usually short transcription. A comment that does not fit is truncated with an ellipsis, with its complete text available on click or focus. On narrow screens it moves below the transcription. The comment should remain visually secondary to the source text.

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
2. Inspect the crop visually against its full column context.
3. Expand upward or downward when any target glyph is incomplete or ambiguous.
4. Permit overlap with an adjacent line whenever necessary for a complete reading.
5. Avoid unnecessary padding where a natural boundary is clear.

The crop is therefore page- and line-sensitive rather than a uniform band with permanently large margins. The clipped top of `T` in `f17/c2-l042` (`Acuma. i. Tengu. Diabo.`) is the motivating example: part of the preceding line may be repeated, but the whole `T` must appear in the target line image. The same reviewed crops should support both project transcription checks and the public human-review interface.

## GitHub Issue submission

The interface prepares corrections page by page. A submission contains only rows whose edits have been confirmed with **OK**. Before submission, the reader can inspect the collected changes.

The Issue body must not be placed in a GitHub `issues/new` query parameter. GitHub documents query prefilling but does not promise a usable maximum URL length, and realistic multi-correction payloads can exceed browser, intermediary, or server limits. Compact JSON reduces the risk but does not remove it, especially when comments contain Japanese text.

The submission flow is therefore:

1. Serialize the confirmed page corrections as readable, versioned JSON.
2. Copy the complete payload to the clipboard.
3. Open a short GitHub Issue URL containing only the template selection and a page-specific title.
4. Ask the reader to paste the copied payload at the marked location in the Issue body.
5. Retain the local draft until the reader explicitly clears it.

If clipboard access fails, the interface displays the payload in a selectable text area. Direct GitHub API submission is deliberately deferred because a static GitHub Pages site should not contain a privileged token, and an authentication service is unnecessary for the initial workflow.

A representative payload is:

```json
{
  "schema": 1,
  "page": "f17",
  "base_commit": "abc1234",
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
