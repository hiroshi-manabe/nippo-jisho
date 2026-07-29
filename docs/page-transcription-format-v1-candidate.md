# Candidate Page-Transcription Format, Version 1

## Status

This is the implementation candidate exercised by the [format version 1 trial](../pilot/format-v1-trial/README.md). Its current human-authoring form is the [Compact Level 1 Markdown Candidate](level1-markdown-candidate.md). It is not yet the adopted production specification.

## Design boundary

The Level 1 page record contains observable documentary evidence in physical order. It records pages, zones, physical lines, visible text, typeface runs, relative indentation, exceptional placement, and materially unresolved readings. It does not ordinarily identify entries, move displaced text, join divided words, or normalize source forms.

Level 1 is the current design and production priority. The format should first be judged by whether a human can read, transcribe, review, and correct pages efficiently while retaining visible evidence.

This boundary concerns what Level 1 records, not what an editor is allowed to know. Historical Japanese, Jesuit romanization, and Portuguese context are legitimate review tools for locating suspicious readings. A correction enters Level 1 only after renewed inspection confirms that the scan supports it; segmentation, normalization, grammatical analysis, and translation remain later-stage interpretation. The staged procedure is specified in the [Provisional Transcription Reading Guide](transcription-reading-guide.md#review-passes).

Level 2 is presently only a compatibility constraint. A small separate fixture confirms that stable Level 1 lines and rare named spans could support later entry boundaries, reading order, and displaced-text analysis. The project is not currently designing a complete Level 2 schema, and ordinary Level 1 records should not carry extra markup merely to make hypothetical later operations convenient.

## Storage model

The trial now uses one compact UTF-8 Markdown source file per page. A validator/compiler generates the earlier JSON representation for deterministic machine interchange and rendering. Editors read and change the Markdown; generated JSON is not a competing hand-maintained transcription.

A compiled page record has:

- source and scope metadata;
- ordered page zones;
- ordered physical lines within textual zones;
- one or more typeface runs within each line;
- optional relative indentation and exceptional placement;
- optional lightweight uncertainty attached only to materially doubtful text.

The compiled shape is:

```json
{
  "format": "nippo-level1-page",
  "format_version": 1,
  "id": "bnf-f0014",
  "scope": "full_page",
  "zones": [
    {
      "id": "column-1",
      "kind": "column",
      "lines": [
        {
          "id": "c1-l001",
          "indent": 0,
          "runs": [
            {"typeface": "roman", "text": "Aburairi."},
            {"typeface": "italic", "text": " Couſa frita."}
          ]
        }
      ]
    }
  ]
}
```

Line identifiers are stable within a page. Optional named spans are added only when an exceptional line needs a smaller stable target, as with `{mark}` and `{word}` in the physically displaced `(grande.` example. Character offsets and routine run numbering are avoided because they are fragile during correction.

## Physical evidence

`indent` is a small relative level, not a pixel coordinate or a claim about lexical function. A run may use `placement: "far-right"` when ordinary line order cannot express an exceptional physical position, as with `(grande.` on `f248`. The scan remains authoritative for exact geometry.

The allowed trial typefaces are `roman`, `italic`, and `display`. Typeface is recorded because the pilot has shown that it can supply evidence for later structural analysis; it is not inferred from a Level 2 role.

Text is NFC-normalized Unicode. Long `ſ`, printed diacritics, capitalization, word separation, materially anomalous spacing, punctuation, and visible line-end division marks are preserved. Exact variable compositor spacing is not measured; the scan remains the geometric record. Page furniture is retained in its own physical zone. A catchword's relationship to another page is not asserted at Level 1.

## Uncertainty

A secure reading is transcribed normally even when context or enlargement helped establish it. Optional uncertainty is reserved for a reading that remains reasonably disputable after targeted enlargement and contextual review. The detailed representation will be finalized only after the trial encounters a genuinely unresolved example; the format does not require routine character-level confidence or damage metadata.

Review state applies to a page, not to a separate textual layer. At minimum, production metadata must distinguish an initial visual draft from work that has received contextual review and final scan confirmation. The pilot value `trial_reviewed` is provisional and does not claim immunity from later correction.

## Derived views

The trial renderer primarily produces:

1. a page-oriented Markdown view from each Level 1 record.

Selected logical sequences are retained only as a secondary information-loss check. They show that later interpretation remains possible; they are not an adoption requirement for a full structural format.

Join operations in Level 2 may preserve a boundary, insert a space, or remove a visible line-end hyphen while joining a divided word. These transformations affect only the derived view. They never rewrite the Level 1 source string.

## Adoption test

The candidate is suitable for adoption only if the trial confirms that:

- complete pages can be entered and corrected without unreasonable friction;
- physical order and exceptional placement remain auditable;
- later structure can be expressed without duplicating source text;
- page-oriented and logical views can be regenerated deterministically;
- validation detects broken references, duplicate identifiers, invalid typefaces, and non-NFC text.
