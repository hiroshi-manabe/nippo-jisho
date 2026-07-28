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

**A printed caron above vowels is distinct from the tilde and circumflex**

| Field | Value |
| --- | --- |
| Status | `confirmed` within the audited pilot pages |
| First recorded | 2026-07-28 |
| Evidence | `bnf-f0248` and `bnf-f0643`; 37 vowel-mark instances previously misclassified as circumflexes |
| Detailed audit | [Pilot Diacritic Audit](diacritic-audit.md) |
| Confidence in glyph identification | High |
| Whole-volume coverage | Not yet established |

### Visible evidence

The mark is a pointed, downward-facing wedge. It occurs repeatedly above `o` and `u`, including in `Goxǒ`, `Gǔcan`, `Zzubǒxi`, and `Zzufǔ`. On the same pages, the tilde in forms such as `acõpanha` is visibly wavy rather than angular.

### Working interpretation

The wedge is a caron or háček and must be encoded as such. Earlier pilot readings using `ô`, `û`, or `ũ` for this shape are glyph misclassifications.

### Confirmed transcription treatment

- Transcribe the confirmed forms with Unicode `ǒ` (U+01D2) and `ǔ` (U+01D4).
- Preserve genuine vowel tildes separately, for example `õ` and `ũ`.
- Use NFC-normalized text when a precomposed caron character exists.
- Do not infer a caron solely from linguistic expectations; inspect the printed mark.
- Continue searching the broader sample for carons on other vowels and for genuine circumflexes or breves before adopting a complete glyph inventory.
