# Candidate Format Version 1 Trial

## Result

The trial successfully represents four complete pages as linked but separate Level 1 and Level 2 data. The renderer validates 330 physical lines, seven structural assertions, and eight selected reading sequences, then regenerates auditable page views and logical reading views without copying source text into Level 2.

This is a successful implementation trial, not yet adoption of format version 1. The representation works for the tested evidence, but JSON authoring is verbose and a genuinely unresolved reading has not yet exercised the uncertainty field.

## Scope

| Page | Trial coverage | Principal tests |
| --- | --- | --- |
| `bnf-f0013` | Complete dictionary text and textual furniture | Opening title and initial, mixed typeface, physical lines, fold-crossed `vobitataxiya`, signature, catchword |
| `bnf-f0014` | Complete dictionary text and textual furniture | Cross-page and cross-column continuation, `aburamono`, physical word division, source spacing and capitalization, catchword |
| `bnf-f0248` | Complete dictionary text and textual furniture | Caron/circumflex contrast, displaced `(grande.`, identical running and internal headings, `Gǔcon`, catchword |
| `bnf-f0643` | Complete dictionary text and textual furniture | Circumflex, caron, and grave accent examples; ownership stamp, printed page number, terminus, closing ornament |

The four complete page records contain 330 physical text lines. Exact source-image SHA-256 values are stored in each Level 1 page record.

## Files

- `level1/*.json` contains source-faithful page evidence in physical order.
- `level2/selected-structure.json` contains entry, catchword, displacement, and logical-order assertions that point back to Level 1.
- `generated/*-page.md` contains regenerated page-oriented verification views.
- `generated/selected-reading-views.md` contains regenerated logical excerpts.
- [`../../docs/page-transcription-format-v1-candidate.md`](../../docs/page-transcription-format-v1-candidate.md) documents the candidate format.
- [`../../scripts/render_format_trial.py`](../../scripts/render_format_trial.py) validates the records and regenerates the views.

Run from the repository root:

```sh
python3 scripts/render_format_trial.py pilot/format-v1-trial
python3 -m unittest discover -s tests -v
```

## Review method

1. The native Gallica masters were checked at full resolution.
2. Quarter-column views supplied layout and context.
3. Overlapping sixth-column views supplied the primary line-by-line reading surface.
4. Targeted enlargements were used for locally difficult spans regardless of the default tile size.
5. A separate verification pass checked line coverage, typeface changes, punctuation, diacritics, and expectation-driven normalization.
6. NINJAL headword data was consulted only after the visual record existed, as a coverage and boundary check.
7. Generated views and all source references were validated automatically.

The older version-0 files remain frozen and were not rewritten. They were useful as error-history and coverage prompts, not as text to convert mechanically.

## Headword coverage check

NINJAL version 202510 expects 16 source-order records on `f13` (`001a01`–`001b07`), 31 on `f14` (`001c01`–`001d18`), 36 on `f248` (`122c01`–`122d18`), and 29 on `f643` (`330a01`–`330b15`). Every expected record has a corresponding visible form in the complete Level 1 page records; the post-checkpoint comparison found no omitted entry candidate.

This agreement concerns coverage, not diplomatic identity. The Level 1 record retains differences such as source `Abarabone` without an immediately following period and lowercase `aburamono`, while the external headword data supplies normalized strings. `Abunaſa` and `Abunǒ` are also preserved as visible subordinate forms even though they are not separate NINJAL records.

## Exceptional external check

The first direct pass read one badly inked word in the `Aburatçuqi` gloss only provisionally. After enlargement did not fully settle its middle letters, the project consulted Portuguese Wikisource page `Página:Gallica’s Nippo Jisho.pdf/16`, [revision `532710`](https://pt.wikisource.org/w/index.php?title=P%C3%A1gina%3AGallica%E2%80%99s_Nippo_Jisho.pdf%2F16&oldid=532710) of `2025-03-18T22:55:03Z`, on `2026-07-29`. Its reading `teſto` prompted renewed inspection; the enlarged source shapes support `teſto de`, which is therefore recorded as a scan-adjudicated reading rather than imported text.

The external page displayed neighboring text as unavoidable context. No neighboring Wikisource transcription was copied into the Level 1 record. `f13` had been viewed with Wikisource earlier in the project and is consequently not epistemically blind, although this trial transcription was made directly from the scan.

## Findings

### Successful parts

- Stable physical-line identifiers provide adequate targets for later structure.
- Typeface runs preserve evidence without labelling a span as a headword or definition at Level 1.
- Relative indentation and `far-right` placement preserve the tested layout distinctions without pixel coordinates.
- The physical `(grande.` remains untouched at Level 1; Level 2 can omit the placement mark and append `grande.` to `Gozadocoro` in a generated view.
- The lowercase source form `aburamono` remains unchanged while Level 2 identifies an entry boundary.
- Catchwords remain visible source strings while their page relationships and exclusion from lexical views are structural assertions.
- Line-end joining handles both ordinary hyphens and the printed double division mark represented by `=`.
- Occurrence-level Unicode preserves `ǒ`, `ô`, `ǔ`, and `ù` without global replacement.

### Costs and limitations

- JSON is reliable but verbose for manual entry, especially where typeface changes several times on one line. A compact authoring syntax that generates this validated representation may be preferable for production.
- Relative indentation is sufficient for the tested pages but is not a substitute for the scan's exact geometry.
- The trial contains locally damaged text resolved through enlargement and context, but no reading that remains materially uncertain. The eventual lightweight uncertainty syntax therefore still needs one real stress case.
- Level 2 contains only the assertions and reading sequences needed to test the separation. It is not a complete structural encoding of all entries on the four pages.
- Exact variable compositor spacing is not measured. Ordinary word separation is preserved, while irregular visual width remains recoverable from the scan.

## Verification-pass corrections

The second pass caught several expectation-driven or resolution-dependent errors in the initial trial entry, including:

- source `Iaponi=` rather than a normalized single hyphen;
- source `eu enor-` rather than contextually expected `ou enor-`;
- `vſada` and `ſe vſa` rather than normalized initial `u`;
- no visible period after `Abarabone`;
- `debrum`, `exo`, and joined `Aburauotçugu`;
- abbreviated `vẽde` and source spacing `veſtido,ou`;
- `Aburaguitta` and anomalous `Aburaguitra`;
- the earlier established `Aburamigaqi`, `acepilhada`, `aburamono`, `Aburaqega`, `ſecar`, and `Aburicauarague` readings;
- full-page corrections on `f248`, including `Gǒyen`, `Gǒyenuo`, `Guchina`, `Gǔcon`, and `nibuxi`;
- full-page corrections on `f643`, including `Zzuqiǒ`, `Zzuſocu`, `Zzuſu`, `Zzutçǔ`, `couſada`, and `Veo me`.

This error yield supports retaining a separate verification pass and routine targeted enlargement in production.
