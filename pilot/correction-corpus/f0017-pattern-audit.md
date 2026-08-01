# f17 post-hoc correction-pattern audit

## Purpose

This is the first test of the f13–f16 raw correction corpus as a review instrument. The ordinary f17 visual, independent-comparison, Japanese, Portuguese, glyph, mark, and right-edge passes were completed first. Only then were the earlier correction categories used as a checklist. This prevents the corpus from becoming an automatic emendation table or anchoring the initial reading.

## Method

1. Group the raw events by mechanism rather than by corrected word.
2. Search the current f17 text for places where each mechanism could recur.
3. Inspect the corresponding native-resolution column image, using tighter enlargement where the standard column view is uncomfortable.
4. Change the canonical text only if the scan supports the candidate.
5. Record inspected non-changes as well as corrections, so added passes can be evaluated for both recall and churn.

## Results

No additional correction was accepted in this first corpus-guided pass. That is a meaningful zero, not a claim that human review will find none.

| Earlier error family | f17 specimens rechecked | Result |
| --- | --- | --- |
| `ſ` / short `s` / `f` mixtures | `c1-l005`, `c1-l007`, `c1-l008`, `c1-l019`, `c1-l021`–`c1-l023`, `c1-l033`, `c1-l035`, `c1-l039`–`c1-l040`; `c2-l001`, `c2-l004`, `c2-l010`–`c2-l012`, `c2-l018`, `c2-l031`, `c2-l038`, `c2-l046`–`c2-l047` | Current allographs remain supported. In particular `vocaſu`, `fuqeru`, `Maos coſtumes`, and the divided `Infa-` survive reinspection. |
| Japanese morphology and `g/q`, `n/m`, `i/u`, missing letters | `c1-l019`, `c1-l023`–`c1-l031`; `c2-l009`–`c2-l011`, `c2-l018`–`c2-l029`, `c2-l042`, `c2-l046`–`c2-l047` | The pre-handoff corrections `vocaſu`, `fuqeru`, `quamaru`, `toingiacu`, `Acugaiuo`, `guiacu`, and `Acuno` remain scan-supported; no new candidate survived enlargement. |
| Historical Portuguese and modern-language bias | `c1-l005`–`c1-l008`, `c1-l010`–`c1-l017`, `c1-l035`–`c1-l040`; `c2-l001`–`c2-l008`, `c2-l015`–`c2-l018`, `c2-l029`–`c2-l047` | Existing `conſideraçaõ`, `ſaluaçaõ`, and `nacimento` remain supported. Joined forms such as `Maoreligioſo` and `nacimento,como` are preserved rather than regularized. |
| Diacritics, abbreviation marks, and false marks | Every marked vowel in both columns, with special attention to `lũa`, `dalgũa`, `Emẽ-`, `Idẽ`, `cõtagioſa`, long-vowel marks in headwords, and `grã-` | No omitted, displaced, or falsely inferred mark was confirmed. `quamaru` and `toingiacu` remain unmarked as established before handoff. |
| Source spacing and joined words | `c1-l002`–`c1-l004`, `c1-l018`–`c1-l032`, `c1-l037`; `c2-l001`, `c2-l019`–`c2-l22`, `c2-l029`–`c2-l31`, `c2-l43`–`c2-l44` | Current spaces and printed joins remain supported. No morphology- or syntax-driven spacing change was made. |
| Right-edge signs and punctuation | All 94 dictionary-text line endings, especially `c1-l018`, `c1-l024`, `c1-l029`, `c1-l035`, `c2-l021`, `c2-l029`, `c2-l031`, `c2-l040`, and `c2-l047` | The four blank f17 column-1 edges already corrected before handoff remain blank. Printed divisions such as `grã-`, `dani-`, and `Infa-` remain `-`; punctuation was not inferred from continuation. |
| Repeated forms and repeated error propagation | `conſideraçaõ` twice; the Acu/Acuguiacu family; repeated `Axij`; repeated Portuguese `Ruim`/`Maldade` formulas | Repetitions agree at the diplomatic level where the print agrees; no parallel correction was missed. |

## Interpretation

The pass added no textual churn, so its observed proposal precision is not distorted by speculative changes. Its recall cannot be measured until the human column review is complete. Any later human correction to f17 should be added to the raw corpus and compared with this checklist: if its family was listed here, the failure was inspection or adjudication; if not, the taxonomy itself needs expansion.

## Later repeated-audit result

An open-ended autonomous audit subsequently continued until five atomic source mismatches survived tight comparison with the Gallica master. They are preserved in [`f0017.tsv`](f0017.tsv):

| Line | Before | Scan-supported reading | Evidence mechanism |
| --- | --- | --- | --- |
| `c1-l001` | `gosto` | `goſto` | Full-resolution glyph comparison; `flores` on the same line contrasts final short `s`. |
| `c1-l024` | `Idẽ ¶` | `Idẽ. ¶` | Tight enlargement shows the stop between the abbreviation and paragraph mark. |
| `c2-l029` | `pensamen-` | `penſamen-` | Full-resolution glyph comparison shows a tall medial `ſ`. |
| `c2-l034` | `prejudicial` | `preiudicial` | The printed historical spelling has `i`, not modern `j`. |
| `c2-l034` | terminal letter with no punctuation | terminal `.` | A separate right-edge enlargement shows the full stop. |

This follow-up disproves the practical sufficiency of the first zero-result pass. Two failures belonged to the already-listed long-`ſ` family, one to historical-language bias, and two to punctuation/right-edge inspection. Merely naming an error family is therefore not evidence that all of its occurrences were checked effectively. An inventory of exceptional forms—here, the only ordinary medial ASCII `s` strings in the draft—proved more productive than another broad rereading.

Several plausible proposals were rejected rather than used to reach the target. The scan joins `Maoreligioſo`; the italic `h` in `conhecimento` resembles `b` but agrees with other same-page `h` forms; and `Peſſoa`, `burǒnaru`, `Acudocu`, and the principal headword diacritics remain supported by enlargement.
