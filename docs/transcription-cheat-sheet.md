# Transcription Cheat Sheet

This is the short, daily-use layer of the project's linguistic reference. It supports **Level 1 diplomatic transcription**; it does not normalize Japanese or Portuguese. For explanations, qualifications, and sources, follow the links to the [Historical Language Notes](historical-language-notes.md). The [Transcription Reading Guide](transcription-reading-guide.md) remains the evidence trail for mistakes found during the pilot.

## The rule above all others

**Let linguistic knowledge tell you where to look again; let the enlarged scan decide what to write.** The printing contains variation, anomalies, and errors. A plausible Japanese or Portuguese form is not permission to repair the source.

For a human correction Issue, use a stricter anti-anchoring order: hide or mentally discard the current reading; first parse the proposed Japanese and Portuguese in context; list the plausible forms; only then inspect the scan. The proposal leads when it is linguistically coherent and the image is compatible. Keep the old reading only with positive contrary visual evidence, not because it remains possible on a second look. Clear printed anomalies still remain literal. If machine review produces a third, qualified form rather than the exact submitted correction, stop for human confirmation instead of silently applying it.

In a correction proposal only, an adjacent `*` immediately before or after a word with one tilde and one unambiguous adjacent-vowel alternative means “move the tilde to the other vowel; change nothing else”: `*mãos` or `mãos*` → `maõs`; `*dalguã` or `dalguã*` → `dalgũa`. Remove the marker when applying the correction. Write the intended form explicitly if more than two carriers are plausible or the word contains multiple tildes.

## One-minute routine

1. Transcribe the visible letters, case, spaces, punctuation, typeface, diacritics, and line division without an external transcription.
2. Reread the Japanese as Japanese and the Portuguese as Portuguese. Flag anything morphologically, lexically, or bilingually suspicious.
3. Enlarge every flagged or locally difficult span. Compare nearby examples of the same type.
4. Return to the surrounding lines. Accept a contextual correction only when the printed shapes support it.
5. If real doubt remains, record the preferred reading as uncertain rather than silently regularizing it.

## High-risk shapes

| Printed possibilities | What to do |
| --- | --- |
| `ſ` / `f` | Compare the complete word and nearby types. Preserve long `ſ`; do not modernize it to `s` at Level 1. |
| `g` / `q` | Test the Japanese form, then compare enlarged glyphs. `gue`/`gui` and `qe`/`qi` are normal patterns. |
| `n` / `u`, `m` / `u`, `i` / `l` | Use the word and gloss to locate the problem, but decide from enlarged strokes in the same typeface; upright and italic forms may differ sharply. |
| one consonant / two | Count the types. Do not supply an expected historical or modern spelling. |
| `ǒ` / `ô` | Read the mark's direction: caron `ˇ` versus circumflex `ˆ`. They are not interchangeable. |
| `ǔ` / `û` / `ù` | Preserve the visible shape. Long `u` has no open/closed opposition corresponding to long `o`. |
| tilde / grave | A tilde is wavy; a grave is a single diagonal stroke. On `f13`, read `cà peralà`, not `cã perali`. Compare the letter beneath the mark separately. |
| tilde over a vowel sequence | Identify the marked vowel from the scan rather than from the expected word. The corpus prints both `algũa` and `alguã`; preserve each occurrence. |

## Japanese and Jesuit-romanization prompts

These are **reinspection prompts, not replacement rules**.

| Pattern | Working reading cue | Caution |
| --- | --- | --- |
| `ca, co, cu`; `qe, qi` | ordinary /k/-series spellings | The headword data overwhelmingly supports `qe` and `qi`; do not invent modern `ke` or `ki`. |
| `ga, go, gu`; `gue, gui` | ordinary /g/-series spellings | An apparent `q` in an expected /g/ form is a classic enlargement case. |
| `qua`, `gua` | historical labial glides | Contrast `cua`, which can represent /kua/ as two vowels. |
| `qu` | may represent ordinary /ku/, including before an inflectional ending | `qua` is not the only valid `qu-` sequence. The scan-confirmed `Fucaqu aigiacu ſuru` also shows that a visibly anomalous `qu` must not be normalized to expected `cu`. Rare `que`/`qui` strings do not by themselves prove Japanese /kwe, kwi/. |
| `x`, `tç`, `f` | often correspond broadly to modern *sh*, *ts*, and h-row sounds | Preserve the Jesuit spelling; use the modern form only to test plausibility. Thus scan-confirmed `Yafan` corresponds to 夜半 *yahan*, rather than representing an anomalous `r`/`f` substitution. |
| `ji` / `gi`; `zu` / `zzu` | intended yotsugana distinctions | Contemporary sources also confuse them. Never regularize from etymology alone. |
| initial or morpheme-initial `v`; internal `u` | often positional variants for Japanese /u, w/ | Thus `vgoqu` is plausible while particles appear in forms such as `uo`; preserve the actual letter and spacing. |
| doubled letters or mixed clusters such as `cq` | may signal gemination | Jesuit spelling also preserves kana-influenced or exceptional forms. Inspect, do not automatically simplify. |
| `eô` / `iô` and related spellings | competing, partly kana-influenced notation can occur | The dictionary's own key tells readers to search under both `E` and `I`. |

### Vowel marks

- `ǒ` = printed caron, the traditional **open** long-*o* category (開音).
- `ô` = printed circumflex, the traditional **closed** long-*o* category (合音).
- The exact historical phonetic interpretation is a research question; it is not needed to identify the mark.
- Over `u`, caron and circumflex can both mark length in Jesuit printing. Classify the glyph shape, not an imagined open/closed class.
- Keep grave accents and tildes separate. On `f248`, `Gǒyẽuo` contains an abbreviation tilde, not another long-vowel mark.

## Spacing, case, and word structure

- Copy the printed space before analysing a particle or morpheme boundary. Later Jesuit prints often attach particles, but the practice is not perfectly consistent.
- For a narrow disputed gap, compare it with both interletter gaps and secure word spaces on the same line. OCR agreement is only a prompt: on f26, `Decer do ceo` retains a real but tight space.
- When semantics predicts an emendation, require a same-typeface comparator before accepting it autonomously, but do not mistake machine visual confidence for final authority. On f26, the machine initially retained `galamiuo` and `bichintos`; enlarged human reinspection established the lexically expected `garamiuo` and `bichinhos` by explicit override. On f27, the scan prints anomalous `Bilho de ſaude` rather than tempting `Bicho` or likely intended `Milho`, and two expected `sora` forms use a dotted `i` while the next line supplies a secure long-`ſ` control.
- Copy visible case before deciding whether something is a headword. Lowercase `aburamono` is nevertheless an independent entry.
- Initial `v`, capitalization, long `ſ`, ligatures, and spacing can carry segmentation cues, but none is a complete entry-boundary system.
- Keep line-end hyphens, catchwords, displaced text, and physical line division as page evidence. Structural joining belongs later. Inspect every column edge directly: a word continuing on the next line does not prove that a hyphen was printed. On f26, `bo` / `ião` has no visible mark even though nearby `na-`, `on-`, and `mun-` do. The [f44–f53 dedicated edge audit](../pilot/line-end-hyphen-audit-f44-f53.md) removed 48 inferred marks in two stages: an AI scan pass found 15, then a compact human audit found 33 more among the 176 marks that pass had retained. Repeated wording and obvious lexical continuation remain unsafe evidence, and this distinction is currently a human-led specialist task. Verify isolated bottom-right text against the following page before deciding that it is a final content line: f26's `do` repeats the first word of f27 and is a catchword.
- Count repeated s-types twice—first for how many letters are present, then for whether each is long `ſ` or short `s`; do not supply an expected doubling or turn a visible mixed `ſs` pair into `ſſ`. F27 independently confirms mixed `Paſsante` and `Peſsoa` beside true `ſſ` pairs. At `f33/c1b-l005`, italic `engroſſo` supplies a particularly clear genuine `ſſ` comparator: two separate tall long-s forms, visually distinct from the recurring β-like sort that has provisionally also been expanded as `ſſ`. Preserve that distinction for the later dedicated typography pass rather than normalizing either class now.
- Treat italic `st` as a separate high-risk case. A short, low `s` can be joined to a `t` whose head or cross-stroke extends left; the resulting `ﬆ` ligature can look like long `ſ` plus `t` (`ﬅ`). Locate the body of the `s` and decide which letter owns the tall stroke before expanding the ligature. Compare genuine isolated `ſ`, short `s`, and `t` in the same italic type. At `f16/c2-l029`, current `Roſto` is flagged for systematic re-evaluation because the scan appears instead to contain short-`s`–`t` `Rosto`; nearby `vestido` appears to use the same construction. The [preliminary dictionary audit](../pilot/st-ligature-audit.md) found no secure unligatured counterexample in 56 distributed cases, but related Jesuit printing has documented exceptions; ligature status is therefore not yet safely inferable from the letters alone.
- Do not let this difficult class stop normal page production. Retain the provisional `st`/`ſt` reading and stable line reference without making a global substitution; final classification is deferred to the dedicated human-guided pass specified in the audit report.

## Portuguese prompts

- Read the whole gloss, not isolated letter shapes. Modern Portuguese can expose a suspicious sequence, but it cannot settle it.
- Preserve `ſ`, historical `u/v` and `i/j`, accents, tildes, abbreviations, capitalization, spacing, and punctuation as printed.
- Preserve each visible cedilla independently of modern spelling. This dictionary can print `ç` where modern Portuguese would use plain `c`, including before `e` or `i`; confirmed examples include `touçinho`, `Eſclarçeo`, and `açẽdem`. Treat modern spelling only as a prompt to enlarge the glyph, never as grounds for removing the cedilla.
- Expect spelling variation, including missing or unfamiliar-looking vowels, endings, and accent choices. The project has confirmed printed `Interieção`, `deſiguaes`, `anotomia`, `baxo`, `printuras`, `cercido`, `chouer`, `eſtà`, `pès`, and `de mais` against tempting modernizations. Earlier machine readings `ſonzear` and `delgaça` on f26 were later overturned by explicit human reinspection as `ſongear` and `delgada`.
- Inventory uncommon marks rather than reading through them: `Poëtas` on `f25` has a real diaeresis, not two paper specks.
- A tilde can stand for omitted letters as well as nasalization. Do not expand it in Level 1.
- Do not normalize a tilde to the vowel that usually carries it. The [`algũa` / `alguã` audit](../pilot/tilde-position-audit.md) confirms real position variation, and the broader [adjacent-vowel carrier audit](../pilot/adjacent-vowel-tilde-audit.md) found locally printed `abanaõ` and `Piaõ` where lexical expectation had produced `abanão` and `Pião`.
- In the currently transcribed `manhaa` family, assign the mark only after isolating both `a` types. A [64-occurrence scan audit](../pilot/nhaa-position-audit.md) found `nhaã` in every case—including `manhaã`, `menhaã`, `amenhaã`, and `amanhaã`—and no genuine `nhãa`; do not let modern *manhã* pull the tilde leftward.
- Typeface helps: Japanese forms are generally roman and Portuguese explanations generally italic in the sampled dictionary pages. Confirm the local case before relying on that tendency.
- For a dedicated roman-Japanese-in-Portuguese pass, search more broadly than headwords: inspect Japanese examples and gloss phrases, cross-references, regional labels such as `Ximo`, very short forms such as `Go`, names and titles, and forms divided across physical lines. Use language to generate candidates, but change the Markdown only after the local type is visible in the scan. Portuguese forms that merely refer to Japan, such as italic `Iapão`, remain Portuguese typography. The first machine benchmark and its negative controls are recorded in the [f44–f53 audit](../pilot/roman-japanese-typeface-audit-f44-f53.md); the same method's pre-human expansion across every then-prepared unchecked page is recorded in the [f54–f237 audit](../pilot/roman-japanese-typeface-audit-f54-f237.md).

## Dictionary-specific labels and conventions

The dictionary's own [prologue and key](https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f11.item) explain these labels; the continuation is on [Gallica `f12`](https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f12.item).

| Printed form | Meaning in the key |
| --- | --- |
| `X.` | usage limited to *Ximo* (the western regions), subject to the key's qualification |
| `alicubi` | current only in some places, not throughout Japan or *Ximo* |
| `P.` | used only in poetry |
| `S.` | used only in writing, such as books or letters |
| `Bup.` | Buddhist term |
| final `B.` | low or vulgar word |
| lowercase `l` | Latin *vel*, “or”; it introduces an alternative form |

Do not expand these inside Level 1. Their interpretation belongs in later structured data.

## When something looks wrong

Ask, in this order:

1. Is it a known type confusion (`ſ/f`, `g/q`, `m/u`, `n/u`, diacritic shape)?
2. Does Japanese morphology or the Portuguese gloss make one reading substantially more likely?
3. Does the dictionary's romanization allow the apparently odd sequence?
4. Does enlargement support the contextual reading?
5. In an apparent `ſt`, does the tall stroke belong to `ſ`, or is it the left-reaching head of `t` joined to a short `s`?
6. If not, should the print's odd form be preserved or the reading marked uncertain?

Known traps and scan-adjudicated examples are catalogued in the [reading guide](transcription-reading-guide.md#known-expectation-driven-errors). Detailed linguistic explanations and source provenance are in the [historical notes](historical-language-notes.md).
