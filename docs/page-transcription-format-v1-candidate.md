# Candidate Page-Transcription Format, Version 1

## Status

This is the implementation candidate exercised by the [format version 1 trial](../pilot/format-v1-trial/README.md). It is not yet the adopted production specification.

## Design boundary

The Level 1 page record contains observable documentary evidence in physical order. It records pages, zones, physical lines, visible text, typeface runs, relative indentation, exceptional placement, and materially unresolved readings. It does not ordinarily identify entries, move displaced text, join divided words, or normalize source forms.

Level 2 is a separate linked record. It points to stable Level 1 line or run identifiers and adds entry boundaries, logical reading order, catchword relationships, and other structural assertions. It does not maintain a corrected duplicate of Level 1 text.

## Storage model

The trial uses one UTF-8 JSON file per page. JSON is deliberately conservative: it is widely supported, has unambiguous nesting, and can be validated without an additional dependency. The trial will determine whether its verbosity is acceptable for sustained manual work.

A page record has:

- source and scope metadata;
- ordered page zones;
- ordered physical lines within textual zones;
- one or more typeface runs within each line;
- optional relative indentation and exceptional placement;
- optional lightweight uncertainty attached only to materially doubtful text.

The basic shape is:

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

Line identifiers are stable within a page. A Level 2 reference combines the page and line identifiers, for example `bnf-f0014:c1-l001`. A structural selector may identify the whole line or selected zero-based run numbers. Character offsets are deliberately omitted from the first candidate because they are fragile during correction; the trial uses a separate run when a smaller stable target is needed.

## Physical evidence

`indent` is a small relative level, not a pixel coordinate or a claim about lexical function. A run may use `placement: "far-right"` when ordinary line order cannot express an exceptional physical position, as with `(grande.` on `f248`. The scan remains authoritative for exact geometry.

The allowed trial typefaces are `roman`, `italic`, and `display`. Typeface is recorded because the pilot has shown that it can supply evidence for later structural analysis; it is not inferred from a Level 2 role.

Text is NFC-normalized Unicode. Long `ſ`, printed diacritics, capitalization, word separation, materially anomalous spacing, punctuation, and visible line-end division marks are preserved. Exact variable compositor spacing is not measured; the scan remains the geometric record. Page furniture is retained in its own physical zone. A catchword's relationship to another page is not asserted at Level 1.

## Uncertainty

A secure reading is transcribed normally even when context or enlargement helped establish it. Optional uncertainty is reserved for a reading that remains reasonably disputable after targeted enlargement and contextual review. The detailed representation will be finalized only after the trial encounters a genuinely unresolved example; the format does not require routine character-level confidence or damage metadata.

## Derived views

The trial renderer produces:

1. a page-oriented Markdown view from each Level 1 record; and
2. selected logical sequences from Level 2 references.

Join operations in Level 2 may preserve a boundary, insert a space, or remove a visible line-end hyphen while joining a divided word. These transformations affect only the derived view. They never rewrite the Level 1 source string.

## Adoption test

The candidate is suitable for adoption only if the trial confirms that:

- complete pages can be entered and corrected without unreasonable friction;
- physical order and exceptional placement remain auditable;
- later structure can be expressed without duplicating source text;
- page-oriented and logical views can be regenerated deterministically;
- validation detects broken references, duplicate identifiers, invalid typefaces, and non-NFC text.
