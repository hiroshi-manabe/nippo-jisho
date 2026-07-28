# Working Editorial Observations

This register preserves potentially reusable discoveries made during the transcription-format pilot. It sits between page-specific review evidence and the eventual version 1 specification.

An observation is not a rule merely because it appears here. Each item must cite its source location, distinguish visible evidence from interpretation, and carry one of these states:

- `provisional` — supported by limited evidence and awaiting more examples;
- `confirmed` — supported by repeated or otherwise decisive evidence;
- `adopted` — incorporated into a versioned transcription specification;
- `rejected` — retained for audit history but not accepted as a convention.

When an observation is adopted, the specification should state the resulting rule and link back to the evidence. Page-specific corrections remain in their review records rather than being duplicated here unless they illustrate a reusable phenomenon.

## OBS-001

**Displaced text belonging to the following line**

| Field | Value |
| --- | --- |
| Status | `provisional` |
| First recorded | 2026-07-28 |
| Evidence | `bnf-f0248`, column 1, transition from `Gozadatami` to `Gozadocoro` |
| Page review | [Second visual pass: bnf-f0248](second-pass/bnf-f0248.md) |
| Confidence in this page’s logical reading | High |
| Confidence as a general convention | Medium; further examples required |

### Visible evidence

The word `(grande.` is printed at the far right of the physical line containing the end of the `Gozadatami` definition. The following entry reads `Gozadocoro. Lugar onde eſtá algum ſenhor` and has no visible completion or terminal punctuation on its own physical line.

### Working interpretation

The lexical text reads:

```text
Gozadatami. Tatami mais alto em q̃ eſtá algũ ſenhor principal.
Gozadocoro. Lugar onde eſtá algum ſenhor grande.
```

`grande.` therefore belongs logically to the following `Gozadocoro` definition. Its unusual physical position, together with the parenthesis-like mark, appears to be a space-saving displacement convention rather than a parenthetical addition to `Gozadatami`.

### Provisional transcription treatment

- Put `grande.` in its logical position at the end of the `Gozadocoro` definition in a reading-order transcription.
- Do not treat the parenthesis-like placement mark as lexical punctuation.
- Preserve the exceptional physical placement in a page note or explicit layout annotation so the editorial reordering is auditable against the scan.
- Do not generalize this treatment from position alone; require syntactic continuity and visible layout evidence.

### Confirmation needed

Search other sampled pages for words printed beside a preceding line but completing the following entry or line. Record confirming and contrary examples before promoting this treatment into the version 1 specification.

## OBS-002

**Caron and circumflex distinguish two long `o` vowels; marks over `u` require shape-level transcription**

| Field | Value |
| --- | --- |
| Status | `confirmed` within the audited pilot pages |
| First recorded | 2026-07-28 |
| Evidence | An occurrence-level audit of 37 previously flagged forms on `bnf-f0248` and `bnf-f0643` |
| Detailed audit | [Pilot Diacritic Audit](diacritic-audit.md) |
| Confidence in glyph identification | High |
| Whole-volume coverage | Not yet established |

### Visible evidence

The caron is a pointed, downward-facing wedge, as in `Goxǒ` and `Gǔcan`. The circumflex is an upward-facing roof, clearly visible in `Goyô` and `Zzubôxi`. The grave accent in `Ienxùs` is a single descending stroke. The tilde in forms such as `acõpanha` is wavy rather than angular.

### Working interpretation

For long `o`, `ǒ` and `ô` are not interchangeable type variants: they correspond respectively to the traditional open and closed long-vowel categories. Marks over long `u` can vary even though `u` lacks the analogous phonological opposition, so their printed shapes must still be preserved diplomatically. The earlier conclusion that all 37 flagged marks were carons is rejected and retained only in the audit history.

### Confirmed transcription treatment

- Transcribe a visible caron with `ǒ` (U+01D2) or `ǔ` (U+01D4).
- Preserve a visible circumflex as `ô` rather than converting it to `ǒ`.
- Preserve other visible marks independently, including the grave in `Ienxùs`.
- Preserve genuine vowel tildes separately, for example `õ` and `ũ`.
- Use NFC-normalized text when a precomposed character exists.
- Read the glyph first and use historical vowel class only to corroborate or challenge the reading.
- Do not perform a global `ô`/`û` replacement; corrections must be occurrence-level.
- Continue searching the broader sample for other vowel marks and degraded examples before adopting a complete glyph inventory.
