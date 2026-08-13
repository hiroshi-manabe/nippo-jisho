# Preliminary italic `st`-ligature audit

## Question

Can Level 1 expand italic `st` ligatures to their constituent letters without losing information because lowercase `st` and `ſt` are always ligatured in this printing?

## Corpus inventory

The compact Level 1 corpus was searched only inside italic spans, keeping roman type out of the comparison. Across the 229 processed pages, the current transcription contains:

- 8 italic `st` occurrences on 8 physical lines;
- 2,713 italic `ſt` occurrences on 2,562 physical lines.

These figures describe the current transcription, not the printed allographs. The audit began precisely because many printed short-`s`–`t` ligatures may already have been expanded incorrectly as `ſt`.

## Scan comparison

The scan check exhaustively inspected all eight current `st` cases and an evenly distributed 48-case sample from the current `ſt` inventory. The latter runs from `f13` through the shortened final page `f643` and samples the ordered inventory at equal intervals. It therefore covers the beginning, middle, and end of the processed sequence rather than one convenient page or word.

All 56 inspected cases are joined or at least compatible with a joined sort; none is a secure lowercase italic non-ligature counterexample. More importantly, several cases currently assigned to different textual categories use the same apparent low-`s` plus tall-`t` construction:

- `f16/c2-l029`, currently `Roſto`;
- `f17/c1-l001`, currently `goſto`;
- `f29/c2-l002` and `c2-l004`, where `Oeſnoroeste` contrasts a clear long `ſ` before `n` with the final `st` construction;
- `f54/c1-l010`, `Abastança`;
- `f148/c1-l001`, `Castigar`;
- `f162/c1-l022`, `distan-`;
- `f209/c1-l016`, currently `ſubſtancia`;
- `f228/c2-l028`, `Rosto`.

This confirms that the current `st`/`ſt` text cannot itself be used to infer which ligature sort was printed. It also confirms that overall glyph height is an unsafe classifier: the only conspicuous tall stroke may belong to the `t`, while the joined `s` remains low.

## Comparison with documented Jesuit practice

Takahashi and Osterkamp's quantitative analysis of the 1596 Jesuit *Contemptus mundi* explicitly distinguishes ligatured `s*t` and `ſ*t` from unligatured `s't` and `ſ't`. Both ligature types dominate word-internally, but non-ligature forms occur in conditioning environments and at least one word-internal exception is reported. Ligature choice also participates in marking word-internal structure versus a word-plus-enclitic boundary. See Sophie Takahashi and Sven Osterkamp, [“Reading Between the Words in Romanized Japanese”](https://doi.org/10.20666/lij.2.0_30), especially pp. 51–54.

That study concerns a related mission-press book, not the *Vocabulario*. It does not prove the dictionary's distribution. It does prove that categorical ligaturing cannot safely be imported as a general Jesuit-printing rule.

## Provisional decision

The proposed lossless inference rule is **not yet established**. The 56-case dictionary sample found no secure unligatured lowercase occurrence, but the source-specific distinction is visually difficult, the present transcription has already conflated the `s` allographs, and closely related printing has documented exceptions.

Therefore:

1. do not globally replace `ﬆ`/`ﬅ` evidence with unannotated `st`/`ſt` on the assumption that ligaturing is automatic;
2. do not globally change current `ſt` to `st`; each printed sort still needs adjudication;
3. treat `f16/c2-l029` and the comparison cases above as an audit set for a human-assisted classifier;
4. decide the final Level 1 notation only after an occurrence audit can reliably separate short-`s`–`t`, long-`ſ`–`t`, and any unligatured exceptions.

The eventual notation can remain minimalist—for example, ordinary letters as the searchable reading plus a sparse ligature annotation—but the source distinction should not be discarded before its predictability has been demonstrated within this dictionary.

## Repeated-long-s control specimen

`f33/c1b-l005`, in italic `engroſſo`, is a clear positive specimen of a genuine two-long-s sequence. The scan shows two separately legible tall `ſ` forms. This differs visibly from the recurring single β-like sort that the provisional transcription has also expanded as `ſſ` in many words.

This observation does **not** yet establish what the β-like sort represents or how Level 1 should encode it. It establishes that the printing contains at least two visually distinct ways of setting material currently represented as `ſſ`, so the current character string alone has collapsed potentially meaningful typographic evidence. The final dedicated pass must therefore compare at least these classes separately:

- two visibly discrete long-s sorts, using `f33/c1b-l005` as a control;
- the β-like joined sort currently expanded as `ſſ`;
- mixed `ſs` and any two-short-s setting;
- the already deferred short-`s`–`t` and long-`ſ`–`t` ligatures.

Until that comparison is complete, preserve the provisional transcription and the stable line reference rather than globally rewriting either visual class.

## Workflow disposition

The project will defer final `st`/`ſt` allograph and ligature classification to a dedicated human-guided pass near the end of Level 1 production. This visually difficult distinction will not interrupt ordinary page transcription or require the human reviewer to report occurrences piecemeal in chat.

Until that pass:

- retain the provisional reading produced during normal transcription;
- do not apply global `st`/`ſt` substitutions;
- do not treat unresolved ligature classification as blocking a page's `scan_confirmed` status;
- preserve stable page-and-line references and scan geometry so every occurrence can be revisited in one purpose-built review sequence;
- keep later corrections attributable through Git and the correction workflow.

The final pass should present tightly enlarged occurrences with same-type comparators—including the genuine `ſſ` control at `f33/c1b-l005`—and should classify both the `s` allograph and ligature status. Its results can then determine whether ligature information is predictable enough to omit, requires sparse exception annotations, or must be represented occurrence by occurrence.
