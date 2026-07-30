# Level 1 Format Version 1 Corpus

## Result

The corpus represents seven complete pages in the adopted compact human-readable Level 1 authoring format. The six-page, 526-line adoption baseline has been extended by the first sequential production page, bringing the compiler-validated total to 623 physical lines. Seven structural assertions and eight selected reading sequences remain as a secondary compatibility check, not the current design focus.

Format version 1 was adopted after the [timed f249–f250 production simulation](../production-simulation/f0249-f0250.md) required no new syntax. Compact Markdown is the authoring form; JSON is generated for validation and interchange. A genuinely unresolved reading has not yet exercised uncertainty notation, which will be added only in a compatible evidence-driven revision.

## Scope

| Page | Trial coverage | Principal tests |
| --- | --- | --- |
| `bnf-f0013` | Complete dictionary text and textual furniture | Opening title and initial, mixed typeface, physical lines, fold-crossed `vobitataxiya`, signature, catchword |
| `bnf-f0014` | Complete dictionary text and textual furniture | Cross-page and cross-column continuation, `aburamono`, physical word division, source spacing and capitalization, catchword |
| `bnf-f0015` | Complete dictionary text and textual furniture | First sequential production page, repeated verification passes, historical Portuguese forms, caron and `ſ` checks |
| `bnf-f0248` | Complete dictionary text and textual furniture | Caron/circumflex contrast, displaced `(grande.`, identical running and internal headings, `Gǔcon`, catchword |
| `bnf-f0249` | Complete dictionary text and textual furniture | Fresh-page production timing, `f248` catchword continuation, printed page number and signature, displaced `(o homem.` |
| `bnf-f0250` | Complete dictionary text and textual furniture | Consecutive-page production timing, catchword continuation and confirmation against `f251`, contextual review yield |
| `bnf-f0643` | Complete dictionary text and textual furniture | Circumflex, caron, and grave accent examples; ownership stamp, printed page number, terminus, closing ornament |

The seven complete page records contain 623 physical lines. Exact source-image SHA-256 values are stored in each Level 1 page record.

## Files

- `level1-source/*.md` contains the human-authored source-faithful page evidence in physical order.
- `level1/*.json` is generated validation and interchange data; it is not edited independently.
- `level2/selected-structure.json` is a secondary compatibility fixture, not the current format-design target.
- `generated/*-page.md` contains regenerated page-oriented verification views.
- `generated/selected-reading-views.md` contains regenerated logical excerpts.
- [`../../docs/page-transcription-format-v1-candidate.md`](../../docs/page-transcription-format-v1-candidate.md) documents the adopted format.
- [`../../docs/level1-markdown-candidate.md`](../../docs/level1-markdown-candidate.md) documents the compact version 1 authoring syntax.
- [`../../scripts/compile_level1_markdown.py`](../../scripts/compile_level1_markdown.py) validates and compiles the human-readable sources.
- [`../../scripts/render_format_trial.py`](../../scripts/render_format_trial.py) validates the records and regenerates the views.
- [`../human-review/README.md`](../human-review/README.md) documents the dictionary-wide generated review shell and the side-by-side checkpoint for all seven Level 1 pages.

Run from the repository root:

```sh
python3 scripts/compile_level1_markdown.py compile \
  pilot/format-v1-trial/level1-source \
  pilot/format-v1-trial/level1 --check
python3 scripts/render_format_trial.py pilot/format-v1-trial
python3 -m unittest discover -s tests -v
```

## Review method

1. The native Gallica masters were checked at full resolution.
2. Quarter-column views supplied layout and context.
3. Overlapping sixth-column views supplied the primary line-by-line reading surface.
4. Every physical line was compared at useful enlargement; still larger targeted crops were used for locally difficult spans.
5. Separate Japanese/romanization, Portuguese, and bilingual-context passes actively parsed the text and flagged suspicious readings without overriding the source.
6. A dedicated glyph pass checked confusable letters and marks occurrence by occurrence.
7. A final complete scan pass adjudicated every flag and checked line coverage, typeface changes, punctuation, diacritics, and expectation-driven normalization. Production `scan_confirmed` now requires a fresh full-page sweep that produces no new correction candidate.
8. NINJAL headword data was consulted only after the visual record existed, as a coverage and suspicious-form check.
9. Generated views and all source references were validated automatically.

This strengthened production procedure was first applied end to end in the [f14 production re-review](../production-review/bnf-f0014.md), but independent human comparison then found thirteen further corrections. The result did not meet the working quality target. The method now adds explicit token-by-token alignment, a reverse-order glyph sweep, and separate inspection of base letters and marks. The earlier broad `trial_reviewed` labels—and self-assigned `scan_confirmed` alone—describe process history, not a production-quality guarantee.

The first sequential application is recorded in the [f15 repeated-pass report](../production-review/bnf-f0015.md). Multiple separate passes caught historical `menhã`, source `ruiuos`, `briguigõis`, the caron in `jǔda`, source spacing, and an invented line-end hyphen before the human checkpoint. Whether this reaches the two-or-three correction target remains for independent human review to decide.

The older version-0 files remain frozen and were not rewritten. They were useful as error-history and coverage prompts, not as text to convert mechanically.

## Headword coverage check

NINJAL version 202510 expects 16 source-order records on `f13` (`001a01`–`001b07`), 31 on `f14` (`001c01`–`001d18`), 36 on `f248` (`122c01`–`122d18`), and 29 on `f643` (`330a01`–`330b15`). Every expected record has a corresponding visible form in the complete Level 1 page records; the post-checkpoint comparison found no omitted entry candidate.

The first sequential page adds all 37 expected records on `f15` (`002a01`–`002b20`). The production simulation adds all 43 expected records on `f249` (`123a01`–`123b20`) and all 43 on `f250` (`123c01`–`123d20`). NINJAL was opened only after the independent visual checkpoint. It exposed suspicious forms such as draft `Gunauaqi`, but the scan independently decided every correction and disagreement, including preservation of printed `Guxer` where the headword row gives `Guxet`.

This agreement concerns coverage, not diplomatic identity. The Level 1 record retains differences such as source `Abarabone` without an immediately following period and lowercase `aburamono`, while the external headword data supplies normalized strings. `Abunaſa` and `Abunǒ` are also preserved as visible subordinate forms even though they are not separate NINJAL records.

## Exceptional external check

The first direct pass read one badly inked word in the `Aburatçuqi` gloss only provisionally. After enlargement did not fully settle its middle letters, the project consulted Portuguese Wikisource page `Página:Gallica’s Nippo Jisho.pdf/16`, [revision `532710`](https://pt.wikisource.org/w/index.php?title=P%C3%A1gina%3AGallica%E2%80%99s_Nippo_Jisho.pdf%2F16&oldid=532710) of `2025-03-18T22:55:03Z`, on `2026-07-29`. Its reading `teſto` prompted renewed inspection; the enlarged source shapes support `teſto de`, which is therefore recorded as a scan-adjudicated reading rather than imported text.

The external page displayed neighboring text as unavoidable context. No neighboring Wikisource transcription was copied into the Level 1 record. `f13` had been viewed with Wikisource earlier in the project and is consequently not epistemically blind, although this trial transcription was made directly from the scan.

## Findings

### Successful parts

- All seven complete pages can be read directly as Markdown while compiling back to the complete 623-line machine representation.
- The seven authoring files occupy 853 lines and 34,735 bytes, compared with 8,198 lines and 184,350 bytes for the generated pretty-printed JSON.
- Ordinary physical lines require only a stable ID and their visible text; Markdown emphasis records typeface without explicit run objects.
- Only `(grande.` and `(o homem.` need named sub-line spans in the current sample, so exceptional machinery remains exceptional.
- Stable physical-line identifiers provide adequate targets for later structure.
- Typeface runs preserve evidence without labelling a span as a headword or definition at Level 1.
- Relative indentation and `far-right` placement preserve the tested layout distinctions without pixel coordinates.
- The physical `(grande.` remains untouched at Level 1; Level 2 can omit the placement mark and append `grande.` to `Gozadocoro` in a generated view.
- The lowercase source form `aburamono` remains unchanged while Level 2 identifies an entry boundary.
- Catchwords remain visible source strings while their page relationships and exclusion from lexical views are structural assertions.
- Line-end joining handles both ordinary hyphens and the printed double division mark represented by `=`.
- Occurrence-level Unicode preserves `ǒ`, `ô`, `ǔ`, and `ù` without global replacement.

### Costs and limitations

- The compact syntax is project-specific, although its compiler is small and dependency-free; production evidence must continue to drive compatible revisions.
- Literal asterisks and the literal delimiter ` || ` have not occurred in the sample; escaping must be specified if the wider corpus contains them.
- Relative indentation is sufficient for the tested pages but is not a substitute for the scan's exact geometry.
- The corpus contains locally damaged text resolved through enlargement and context, but no reading that remains materially uncertain. Lightweight uncertainty notation therefore still needs one real stress case.
- Level 2 contains only the assertions and reading sequences needed to check that Level 1 retained necessary evidence. It is deliberately not a complete structural encoding of the four pages.
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
- full-page corrections on `f248`, including the contrast between `Gǒyen` and abbreviated `Gǒyẽuo`, plus `Guchina`, `Gǔcon`, and `nibuxi`;
- the contextually detected and visually confirmed `tçutomeuo`, correcting an `m`/`u` sequence error in `tçutomemo`;
- contextual-review corrections on `f643`: printed `bocetinha` and `deſiguaes`, replacing `bocezinha` and `deſiguais`;
- full-page corrections on `f643`, including `Zzuqiǒ`, `Zzuſocu`, `Zzuſu`, `Zzutçǔ`, `couſada`, and `Veo me`.

This error yield supports an initial visual pass followed by explicit Japanese/romanization and Portuguese-context passes, with every proposed correction finally confirmed against the scan. These are all Level 1 review activities: later segmentation, normalization, interpretation, and translation remain separate.

The structured follow-up and its rejected context-driven suspicions are reported in [Contextual Review of f0248 and f0643](../contextual-review/f0248-f0643.md).
