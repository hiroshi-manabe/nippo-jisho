# Level 1 Format Version 1 Corpus

## Result

The corpus represents 149 complete pages in the adopted compact human-readable Level 1 authoring format. The six-page, 526-line adoption baseline has been extended by 143 sequential production pages, bringing the compiler-validated total to 14,539 physical lines. Seven structural assertions and eight selected reading sequences remain as a secondary compatibility check, not the current design focus.

Format version 1 was adopted after the [timed f249–f250 production simulation](../production-simulation/f0249-f0250.md) required no new syntax. Compact Markdown is the authoring form; JSON is generated for validation and interchange. A genuinely unresolved reading has not yet exercised uncertainty notation, which will be added only in a compatible evidence-driven revision.

## Scope

| Page | Trial coverage | Principal tests |
| --- | --- | --- |
| `bnf-f0013` | Complete dictionary text and textual furniture | Opening title and initial, mixed typeface, physical lines, fold-crossed `vobitataxiya`, signature, catchword |
| `bnf-f0014` | Complete dictionary text and textual furniture | Cross-page and cross-column continuation, `aburamono`, physical word division, source spacing and capitalization, catchword |
| `bnf-f0015` | Complete dictionary text and textual furniture | First sequential production page, repeated verification passes, historical Portuguese forms, caron and `ſ` checks |
| `bnf-f0016` | Complete dictionary text and textual furniture | Independent double reading, proposal precision/recall benchmark, anomalous `Sõ-` / `tir`, continuation sign |
| `bnf-f0017` | Complete dictionary text and textual furniture | Strengthened contextual and right-edge audit, historical `-aõ`, continuation from f16 and catchword to f18 |
| `bnf-f0018`–`bnf-f0022` | Complete dictionary text and textual furniture | Five-page bounded batch, frozen normal checkpoints, at least five additional scan-confirmed findings per page, enlarged section initials, calibrated human-review geometry |
| `bnf-f0023`–`bnf-f0027` | Complete dictionary text and textual furniture | Strictly sequential five-page batch, page-independent 30–60 marginal-discovery stopping rule, source-anomaly checks, calibrated human-review geometry |
| `bnf-f0028`–`bnf-f0037` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, bilingual and glyph passes, later NINJAL coverage diagnostics, manually reviewed section transitions and complete-glyph crops |
| `bnf-f0038`–`bnf-f0047` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, scan-authoritative NINJAL diagnostics, transition from A to B, manually reviewed line geometry and enlarged initials |
| `bnf-f0048`–`bnf-f0057` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, B vocabulary, scan-authoritative NINJAL diagnostics, manually reviewed line geometry and enlarged initials |
| `bnf-f0058`–`bnf-f0067` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, B vocabulary through `B ANTES DO V.`, scan-authoritative NINJAL diagnostics, manually reviewed line geometry and enlarged initials |
| `bnf-f0068`–`bnf-f0077` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, transition from B into C, scan-authoritative NINJAL diagnostics, manually reviewed line geometry and decorated C |
| `bnf-f0078`–`bnf-f0087` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, C vocabulary, scan-authoritative NINJAL diagnostics, manually reviewed line geometry |
| `bnf-f0088`–`bnf-f0097` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, C vocabulary, scan-authoritative NINJAL diagnostics, explicit recto/verso furniture audit, manually reviewed line geometry |
| `bnf-f0098`–`bnf-f0107` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, transition into `C ANTES DO H.`, scan-authoritative NINJAL diagnostics, printed-header anomaly audit, manually reviewed line geometry |
| `bnf-f0108`–`bnf-f0117` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, transition from `C ANTES DO H.` into `C ANTES DO O.`, scan-authoritative NINJAL diagnostics, printed-header anomaly audit, manually reviewed line geometry |
| `bnf-f0118`–`bnf-f0127` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, C vocabulary, scan-authoritative NINJAL diagnostics, low-baseline and displaced-line geometry audit, recto/verso furniture review |
| `bnf-f0128`–`bnf-f0137` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, transition into `C ANTES DO V.`, scan-authoritative NINJAL diagnostics, section-transition and continuation-line geometry audit, recto/verso furniture review |
| `bnf-f0138`–`bnf-f0147` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, C vocabulary, scan-authoritative NINJAL diagnostics, displaced bottom fragments and continuation-line geometry audit, recto/verso furniture review |
| `bnf-f0148`–`bnf-f0157` | Complete dictionary text and textual furniture | Ten-page normal bounded batch, transition from C into D, scan-authoritative NINJAL diagnostics, internal-section and complete-initial geometry audit, recto/verso furniture review |
| `bnf-f0248` | Complete dictionary text and textual furniture | Caron/circumflex contrast, displaced `(grande.`, identical running and internal headings, `Gǔcon`, catchword |
| `bnf-f0249` | Complete dictionary text and textual furniture | Fresh-page production timing, `f248` catchword continuation, printed page number and signature, displaced `(o homem.` |
| `bnf-f0250` | Complete dictionary text and textual furniture | Consecutive-page production timing, catchword continuation and confirmation against `f251`, contextual review yield |
| `bnf-f0643` | Complete dictionary text and textual furniture | Circumflex, caron, and grave accent examples; ownership stamp, printed page number, terminus, closing ornament |

The 149 complete page records contain 14,539 physical lines. Exact source-image SHA-256 values are stored in each Level 1 page record.

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
- [`../human-review/README.md`](../human-review/README.md) documents the dictionary-wide generated review shell and the line-by-line checkpoint for all 149 Level 1 pages.

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

The first sequential application is recorded in the [f15 repeated-pass report](../production-review/bnf-f0015.md). Multiple separate passes caught several errors before the human checkpoint, but independent comparison still found ten corrections, including faint `menhaã`, tilde placement in `briguigoĩs`, source spacing, `comballas`, `faru`, and the `ſs` sequence in `aſsi`. The method therefore remained above the two-or-three correction target.

Pages `f28`–`f37` use the normal bounded procedure without the optional 30–60 marginal-discovery audit. This separates routine forward progress from the much more expensive diminishing-returns experiment. The scan-based pass includes complete line coverage, Japanese and Portuguese context, base-letter and mark checks, reverse order, and a fresh sweep; it then uses NINJAL only for coverage and suspicion generation. All ten pages have visually reviewed line geometry and remain pending independent human review.

Pages `f38`–`f47` continue the same bounded procedure. They preserve 975 physical lines, including section changes from `S` through `Z` and the decorated transition into the vocabulary under `B`. NINJAL supplied 335 expected source-page records as a coverage diagnostic, while capitalization, spacing, long `ſ`, diacritics, typeface, and subordinate forms were adjudicated from the scan. All ten pages have visually reviewed line geometry and remain pending independent human review.

Pages `f48`–`f57` use the same bounded procedure and add 978 physical lines in the B vocabulary. NINJAL supplied 441 source-page rows only as a post-draft coverage diagnostic. The batch includes internal transitions to `B ANTES DO E.` and `B ANTES DO I.`, with complete-glyph crop overrides for their enlarged initials. All line geometry was inspected, and an initially short f55 pre-heading range was corrected before review status was recorded.

Pages `f58`–`f67` add 983 physical lines and represent all 420 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch preserves the internal transitions to `B ANTES DO O.` and `B ANTES DO V.`, the anomalous printed `A ANTES DO V.` left running header on f64, and several 48-line columns. Visual crop review exposed and corrected a displaced f62 `BV` range before geometry was approved.

Pages `f68`–`f77` add 979 physical lines and represent all 358 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch preserves the two-line transition into the C vocabulary on f68, its five-line decorated initial, and both ordinary and irregular page furniture. All twenty column contact sheets were inspected before the geometry was marked reviewed.

Pages `f78`–`f87` add 988 physical lines and represent all 439 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch continues the C vocabulary under the normal bounded procedure. All twenty column contact sheets were inspected before the geometry was marked reviewed; the pages remain review-ready drafts pending independent human correction.

Pages `f88`–`f97` add 983 physical lines and represent all 401 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch continues the C vocabulary under the normal bounded procedure. In addition to inspecting all twenty column contact sheets, its furniture pass explicitly distinguishes numbered rectos from unnumbered versos instead of inferring a printed number from sequence. The pages remain review-ready drafts pending independent human correction.

Pages `f98`–`f107` add 979 physical lines and represent all 428 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch crosses into `C ANTES DO H.`, preserves the enlarged `CHA` at f103 and anomalous mismatched running headers on f104 and f107, and includes a genuine 48-line column on f106. All twenty contact sheets were inspected before geometry was marked reviewed; the pages remain review-ready drafts pending independent human correction.

Pages `f108`–`f117` add 980 physical lines and represent all 421 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch moves from `C ANTES DO H.` into `C ANTES DO O.`, preserves several visibly mismatched running headers, and retains f115's internal alphabetical divider independently from its text lines. All twenty contact sheets were inspected before geometry was marked reviewed; the pages remain review-ready drafts pending independent human correction.

Pages `f118`–`f127` add 989 physical lines and represent all 472 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch continues the C vocabulary, preserves mismatched running headers on f121 and f127, and records f127's displaced `ji-` as physical text rather than a catchword. Enlarged scan comparison prompted corrections to `Coi fuſube`, `Cǒjifuſube`, and `Cômô`. Geometry review replaced inherited lower bounds with page-specific endpoints on leaves whose final lines sit unusually low; all twenty contact sheets were inspected before geometry was marked reviewed. The pages remain review-ready drafts pending independent human correction.

Pages `f128`–`f137` add 983 physical lines and represent all 447 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch continues from f127's displaced `ji-`, preserves the internal f135 `C ANTES DO V.` transition and anomalous running-header changes, and leaves f137's final `ſobre` as an ordinary continuation into the next leaf. All twenty contact sheets were inspected before geometry was marked reviewed. The pages remain review-ready drafts pending independent human correction.

Pages `f138`–`f147` add 981 physical lines and represent all 440 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch preserves mismatched running headers, displaced bottom fragments on f139, f142, f143, f145, and f147, and the physical placement of f141's far-right `i. fabrica.` without duplicating it as another line. All twenty contact sheets were inspected before geometry was marked reviewed. The pages remain review-ready drafts pending independent human correction.

Pages `f148`–`f157` add 978 physical lines and represent all 435 NINJAL rows assigned to those leaves as a post-draft coverage diagnostic. The batch crosses into the D vocabulary on f149, preserves anomalous and mismatched printed running headers, and records internal transitions on f149, f153, and f155 with complete-glyph crops for their enlarged initials. Geometry review corrected the physical `madeira-` / `mento` split on f156, and a full-page furniture check established f157's abbreviated catchword `Dô`. All twenty contact sheets were inspected before geometry was marked reviewed. The pages remain review-ready drafts pending independent human correction.

The [f16 production report](../production-review/bnf-f0016.md) replaces further anchored rereading with an independent second reading and explicit proposal adjudication. Its two pre-handoff proposals each caught a real local feature but neither complete proposed string survived human review: the space in `Sagui yuqu` and the marked `Sõ-` were valid, while `yiqu` and following `fir` were not. The first human checkpoint and renewed audit found seven missed corrections; completed column review and a repetition sweep found twenty-two more. These include right-edge evidence, mixed `ſs`, historical Portuguese spelling and spacing, and Japanese-context errors. Two audit proposals, `A=` and `cla=`, were also unnecessary under the provisional uniform `-` convention. The result shows that proposals must be recorded atomically and that independent comparison alone did not meet the quality target.

The older version-0 files remain frozen and were not rewritten. They were useful as error-history and coverage prompts, not as text to convert mechanically.

## Headword coverage check

NINJAL version 202510 expects 16 source-order records on `f13` (`001a01`–`001b07`), 31 on `f14` (`001c01`–`001d18`), 36 on `f248` (`122c01`–`122d18`), and 29 on `f643` (`330a01`–`330b15`). Every expected record has a corresponding visible form in the complete Level 1 page records; the post-checkpoint comparison found no omitted entry candidate.

The sequential pages add all 37 expected records on `f15` (`002a01`–`002b20`), all 36 on `f16` (`002c01`–`002d19`), and all 40 on `f17` (`003a01`–`003b23`). The production simulation adds all 43 expected records on `f249` (`123a01`–`123b20`) and all 43 on `f250` (`123c01`–`123d20`). NINJAL was opened only after the independent visual checkpoint. It exposed suspicious forms such as draft `Gunauaqi`, but the scan independently decided every correction and disagreement, including preservation of printed `Guxer` where the headword row gives `Guxet`.

The f28–f37 batch represents all 378 NINJAL rows assigned to those Gallica leaves, f38–f47 represents all 335 rows assigned to the next ten leaves, f48–f57 represents 441 rows, f58–f67 represents 420 rows, f68–f77 represents 358 rows, f78–f87 represents 439 rows, f88–f97 represents 401 rows, f98–f107 represents 428 rows, f108–f117 represents 421 rows, f118–f127 represents 472 rows, f128–f137 represents 447 rows, f138–f147 represents 440 rows, and f148–f157 represents 435 rows. These are coverage results, not claims that the normalized row strings are diplomatic transcriptions. In particular, NINJAL's `Asa-` strings prompted a coverage check while the Gallica scan adjudicated the printed medial long `ſ` throughout f36–f38.

This agreement concerns coverage, not diplomatic identity. The Level 1 record retains differences such as source `Abarabone` without an immediately following period and lowercase `aburamono`, while the external headword data supplies normalized strings. `Abunaſa` and `Abunǒ` are also preserved as visible subordinate forms even though they are not separate NINJAL records.

## Exceptional external check

The first direct pass read one badly inked word in the `Aburatçuqi` gloss only provisionally. After enlargement did not fully settle its middle letters, the project consulted Portuguese Wikisource page `Página:Gallica’s Nippo Jisho.pdf/16`, [revision `532710`](https://pt.wikisource.org/w/index.php?title=P%C3%A1gina%3AGallica%E2%80%99s_Nippo_Jisho.pdf%2F16&oldid=532710) of `2025-03-18T22:55:03Z`, on `2026-07-29`. Its reading `teſto` prompted renewed inspection; the enlarged source shapes support `teſto de`, which is therefore recorded as a scan-adjudicated reading rather than imported text.

The external page displayed neighboring text as unavoidable context. No neighboring Wikisource transcription was copied into the Level 1 record. `f13` had been viewed with Wikisource earlier in the project and is consequently not epistemically blind, although this trial transcription was made directly from the scan.

## Findings

### Successful parts

- All 149 complete pages can be read directly as Markdown while compiling back to the complete 14,539-line machine representation.
- The 149 authoring files occupy 19,379 lines and 793,659 bytes, compared with 190,092 lines and 4,264,326 bytes for the generated pretty-printed JSON.
- Ordinary physical lines require only a stable ID and their visible text; Markdown emphasis records typeface without explicit run objects.
- Only `(grande.` and `(o homem.` need named sub-line spans in the current sample, so exceptional machinery remains exceptional.
- Stable physical-line identifiers provide adequate targets for later structure.
- Typeface runs preserve evidence without labelling a span as a headword or definition at Level 1.
- Relative indentation and `far-right` placement preserve the tested layout distinctions without pixel coordinates.
- The physical `(grande.` remains untouched at Level 1; Level 2 can omit the placement mark and append `grande.` to `Gozadocoro` in a generated view.
- The lowercase source form `aburamono` remains unchanged while Level 2 identifies an entry boundary.
- Catchwords remain visible source strings while their page relationships and exclusion from lexical views are structural assertions.
- Provisionally, the printed line-division sign is encoded uniformly as `-` in roman and italic type; the equals-like appearance seen in italic text is not promoted to a separate character unless wider sampling supplies a functional or non-italic counterexample.
- Occurrence-level Unicode preserves `ǒ`, `ô`, `ǔ`, and `ù` without global replacement.
- The compatible `initial=N` annotation preserves twenty-one recurring enlarged section initials without joining the following physical line or burdening ordinary lines with extra markup; the decorated `B` on f47 spans four lines while ordinary enlarged initials span two.

### Costs and limitations

- The compact syntax is project-specific, although its compiler is small and dependency-free; production evidence must continue to drive compatible revisions.
- Literal asterisks and the literal delimiter ` || ` have not occurred in the sample; escaping must be specified if the wider corpus contains them.
- Relative indentation is sufficient for the tested pages but is not a substitute for the scan's exact geometry.
- The corpus contains locally damaged text resolved through enlargement and context, but no reading that remains materially uncertain. Lightweight uncertainty notation therefore still needs one real stress case.
- Level 2 contains only the assertions and reading sequences needed to check that Level 1 retained necessary evidence. It is deliberately not a complete structural encoding of the four pages.
- Exact variable compositor spacing is not measured. Ordinary word separation is preserved, while irregular visual width remains recoverable from the scan.

## Verification-pass corrections

The second pass caught several expectation-driven or resolution-dependent errors in the initial trial entry, including:

- source `Iaponi-`, retaining the line division without treating its italic appearance as a separate character;
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
