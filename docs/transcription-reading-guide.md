# Provisional Transcription Reading Guide

## Status and purpose

This is a working quality-control guide for direct visual transcription of the *Nippo Jisho*. It records source-specific reading cautions discovered during the transcription-format pilot. It is not yet the version 1 transcription specification, a complete account of Jesuit romanization, or authority to normalize the printed text.

For production use, begin with the compact [Transcription Cheat Sheet](transcription-cheat-sheet.md). The fuller linguistic explanations, confidence distinctions, and bibliography are maintained in the [Historical Language Notes](historical-language-notes.md). This guide remains the project evidence trail for scan-adjudicated errors and workflow safeguards.

The scan remains decisive. Historical Japanese, Portuguese spelling, morphology, and expected dictionary structure may indicate where to look again, but they must not silently replace visible evidence.

## Order of operations

For every passage:

1. Read and record the visible characters, capitalization, spacing, punctuation, diacritics, and relevant line divisions.
2. Apply the diagnostic cautions in this guide only after an initial reading exists.
3. Enlarge any locally difficult or suspicious span, regardless of the default size used for routine transcription, and compare nearby specimens of the same type when useful.
4. Return to the surrounding lines to test the enlarged reading in context.
5. Mark materially unresolved uncertainty instead of repairing an implausible form from memory or linguistic expectation.
6. Accept a correction only when the scan supports it. Record linguistic analysis separately as corroboration.

No spelling rule in this guide licenses automatic substitution. The original printing and the Jesuit transcription system both contain variation, anomalous spellings, and errors.

## Review passes

Level 1 is a reasoned diplomatic transcription, not a linguistically blind description of shapes. The scan is already the uninterpreted visual record. Knowledge of historical Japanese, Jesuit romanization, and Portuguese may therefore be used to find and resolve transcription errors, while the Level 1 record itself remains limited to the judged printed reading.

Production review should separate the following perspectives so that expectation does not silently become evidence:

1. **Initial visual pass:** record the apparent print in physical order without consulting an external transcription.
2. **Every-line enlarged alignment:** align every physical line with an enlarged scan tile, not only lines already thought difficult. Point through the source and transcription token by token, including short grammatical words and spaces; then make a second character-level sweep in reverse line order so semantic expectation cannot carry the reading. Check line coverage, word division, typeface, capitalization, spacing, punctuation, and abbreviations while the scan and transcription are adjacent. Isolate both column edges as their own visual surface: lexical continuation on the next line is not evidence that a division mark was printed.
3. **Japanese and romanization pass:** actively parse the Japanese forms and examples, including particles and inflectional endings, and test them against historical Japanese morphology, syntax, and source-specific spelling patterns. Use implausibility to flag passages for reinspection.
4. **Portuguese pass:** read each gloss as Portuguese rather than as a sequence of letter shapes. Check syntax, historical spelling, abbreviations, and whether every sentence is coherent enough to expose a likely misreading.
5. **Bilingual-context pass:** test whether the relationship between the Japanese example or headword and the Portuguese gloss exposes a reading that can look plausible in only one language.
6. **Dedicated glyph pass:** make a fresh occurrence-level check of confusable types and marks, especially `ſ`/`f`/short `s`, `u`/`v`, `g`/`q`, `n`/`u`, `m`/`u`, `i`/`l`, `c`/`ç`, `s`/`z`, single/double consonants, abbreviation tildes, and accent shapes. Verify the base letter and its mark independently; do not expand a printed abbreviation such as `ẽ` to an inferred `en`.
7. **Final scan confirmation:** inspect every proposed contextual correction again and accept it only if the enlarged print supports it. Then sweep the complete page once more from the beginning. A page reaches `scan_confirmed` only when one complete fresh sweep produces no new correction candidate; any new finding is corrected and the relevant contextual and glyph checks are repeated before another complete sweep.

For bounded process experiments, preserve the normally completed page as a frozen checkpoint before beginning any requested extra audit. Record only atomic differences that survive direct enlarged-scan comparison; an external headword inventory may raise a question but cannot adjudicate spelling, spacing, marks, or type. Check an elapsed-time ceiling only at the end of a complete pass, so clock watching does not fragment the reading. If a pass crosses the ceiling, retain every verified correction from that pass and stop further extra passes; never stop mid-pass or discard a sixth finding merely because the numeric target was reached earlier in the pass. The f18–f22 batch used a five-finding target and a one-hour per-page ceiling; every page reached the target in its first extra pass below the ceiling.

The ordinary production unit ends after the fresh zero-new-candidate sweep, headword-coverage diagnostic, and visually reviewed line geometry. The five-finding and 30–60 procedures are optional marginal audits, not prerequisites for preparing the next pages. Pages f28–f37 deliberately use only the normal bounded procedure so that routine transcription can advance; a high-cost marginal audit may be applied later without changing or obscuring that checkpoint.
8. **Human column review:** after generation, a named human reviewer compares the scan and current Level 1 text one column at a time, followed by a separate page-furniture check.

The contextual passes diagnose possible errors; they do not normalize the text. For example, Japanese context exposes the initial `bodaino tçutomemo naſu` as suspicious, and the scan confirms `bodaino tçutomeuo naſu`. Level 1 records that confirmed printed sequence. Dividing it as `tçutome + uo`, restoring Japanese script, explaining the particle, and translating it belong to later stages.

Page status uses `visual_draft` after the initial visual pass, `context_reviewed` after the Japanese, Portuguese, and bilingual passes, and `scan_confirmed` only after the every-line and glyph audits, adjudication of all flags, and a fresh zero-new-candidate sweep. Human review then proceeds through column 1, column 2, and page furniture in the generated [side-by-side review interface](../pilot/human-review/README.md). The normal interactive correction loop is deliberately simple: the reviewer reports a line ID and proposed reading in the project chat; reviewer and transcriber discuss contextual evidence and the enlarged scan; the transcriber changes only the canonical Level 1 Markdown, regenerates the interface, and reopens the affected unit. When all three units record reviewer and timestamp, the page may become `human_checked`. The pilot's broad `trial_reviewed` label predates this workflow and must not be assigned to new work or interpreted as a permanent claim that no further correction is possible.

Human-review correction yield is a production metric. The working quality target is no more than two or three corrections per page at the human checkpoint. This is an evaluation threshold, not a promise or a reason to conceal doubt: if a page exceeds it, treat the pre-review method as having failed its quality target and improve it before scaling. The first application on [f14](../pilot/production-review/bnf-f0014.md) received thirteen human corrections, so the page became the negative control that motivated explicit token alignment, a reverse-order glyph sweep, and independent checks of base letters and marks. The [f15 production transcription](../pilot/production-review/bnf-f0015.md) applied those perspectives as separate repeated passes but still received ten occurrence-level human corrections. More passes helped, but repetition alone did not meet the target.

Beginning with [f16](../pilot/production-review/bnf-f0016.md), production uses an independent-comparison checkpoint instead of repeatedly editing one anchored reading. Make the first transcription from the scan, then reread the page without consulting that text, using overlapping enlarged tiles in reverse physical order where practical. Compare the two readings mechanically or line by line. A disagreement is a review prompt, not an automatic amendment: change Level 1 only after enlarged source evidence, a secure same-page specimen, or contextual evidence followed by renewed visual confirmation supports the change. Otherwise retain the first reading and flag the location for human review.

Measure this method against the final human-confirmed page, not against the number of changes proposed by later passes. Record true corrections found before handoff, human corrections still missed, and correct readings unnecessarily changed. Report both recall—the share of final errors caught before handoff—and precision—the share of proposed changes that survive human confirmation. Until enough pages exist for stable rates, preserve the raw counts and error categories. The method succeeds only if it reduces missed errors without encouraging normalization or speculative churn.

The [raw f13–f16 correction corpus](../pilot/correction-corpus/README.md) is the occurrence-level memory for this evaluation. Preserve successive readings rather than replacing them with a polished summary: a partly useful intermediate proposal and a later-reverted overcorrection identify different failure modes. Use its categories only after the ordinary page-specific passes. For each category, reinspect plausible occurrences on the new page and record both accepted changes and checked non-changes. Never apply a past before/after pair mechanically. The first such [post-hoc audit on f17](../pilot/correction-corpus/f0017-pattern-audit.md) accepted no additional change; its recall remains unknown until human review.

The first f16 human check exposed a further requirement: audit the complete right edge as its own visual surface. Do not infer a division mark merely because a word continues on the next line. Compare each ending against the scan and distinguish a blank edge, a printed line-division sign, and punctuation such as a comma. As a provisional Level 1 convention, encode the line-division sign uniformly as `-` in both roman and italic type. In the pages examined so far, a two-stroke or equals-like impression appears to be a typeface-conditioned form with the same function, while typeface is already recorded independently. This is a working hypothesis rather than a volume-wide typographical conclusion. During production, flag any equals-like occurrence outside italic type or with a function other than line division; such a counterexample would require reconsidering `=` as a distinct diplomatic character. The f16 contrasts are `dẽpres` / `tado`, `tol` / `dado`, and `ſel` / `la` with no mark; `A-` / `carta` and `cla-` / `ridade` with a division sign; and `Tçuqi,` / `fanani` with a comma. The f24 marginal audit independently found bare `af` / `fabilmente`, `fron` / `te`, `cre` / `cerão`, and `xe` / `muru` beside unmistakable equals-like division types after `pe`, `Fal`, `al`, `flo`, `da`, `pro`, `inimi`, `com`, and `for`. A global edge inventory is therefore required even after every lexical join has already been reconstructed correctly. This audit is independent of reconstructing the continuous word.

Japanese morphology must likewise be tested at the character level, not merely used to judge whether the overall entry is plausible. On f16, *acamiga ſaſu* and *Fiuo acaſu* expose `ſ`/`f` and `u`/`t` errors that survived the first contextual pass. When context predicts a correction, return to same-page glyph specimens before amending the diplomatic text.

## Marginal-discovery audit: the 30–60 rule

After the ordinary page workflow and checkpoint, a page may receive a deliberately open-ended marginal-discovery audit. Apply the rule independently to each page:

1. Continue focused passes until one certain error has been found and confirmed against the scan.
2. If that finding took no more than 30 minutes since the preceding confirmed finding (or the start of this audit for the first finding), retain it, reset that page's clock, and repeat.
3. If a confirmed finding took more than 30 minutes, retain it and stop that page.
4. If 60 minutes pass without a confirmed finding, stop that page without manufacturing a change.

Only a source-supported correction resets the clock. A rejected candidate, unresolved reading, external-data disagreement, formatting experiment, or finding on another page does not. When several pages are interleaved, record and judge their intervals separately. Check elapsed time at pass boundaries rather than repeatedly interrupting close reading.

The audit should vary its attention rather than repeat one undifferentiated sweep: complete visual reading, Japanese morphology and syntax, Portuguese lexical and historical spelling, typeface boundaries, spacing and line edges, diacritics and abbreviation marks, same-page confusable-glyph comparison, and NINJAL headword disagreement are useful distinct passes. NINJAL remains an alarm only; the scan decides every accepted correction. The stopping rule measures diminishing returns from the machine review, not completeness of the page or the value of later human checking.

## Practical threshold for uncertainty

Contextual reasoning is part of ordinary visual transcription. A reading need not be marked uncertain merely because a fold, weak impression, or unfamiliar letter made context useful in confirming it. If the surviving shapes and context together yield a reading that a careful reviewer is unlikely to dispute, transcribe it normally.

Reserve explicit uncertainty notation for materially doubtful results:

- give the preferred reading with a lightweight uncertainty marker when it is probable but reasonably disputable;
- record alternatives in a short note only when more than one reading remains plausible;
- use an illegible marker when no defensible reading can be supplied, optionally with a clearly labelled tentative suggestion.

Do not require character-by-character confidence values, damage categories, or explanations for every difficult passage. More detailed notes remain available for exceptional cases where they help later review. The version 1 format must support this escalation without making it routine.

Targeted enlargement, by contrast, is routine. It is a review action used whenever the default view does not make a local reading comfortably clear. A span may require enlargement and contextual checking yet still receive an ordinary unmarked transcription once resolved.

## Known expectation-driven errors

The first controlled comparison exposed errors caused not only by difficult type but by unconsciously regularizing the source.

| Printed reading | Initial reading | Likely cause | Required caution |
| --- | --- | --- | --- |
| `aburamono` | `Aburamono` | Assuming that an apparent headword must begin with a capital | Copy visible case before deciding entry structure. |
| `Aburaqega ſuru` | `Aburaqe ga ſuru` | Inserting a space at an expected Japanese particle boundary | Copy visible spacing before morphological analysis. |
| `ſecar` | `ſeccar` | Visual error or expectation of a doubled historical spelling | Count repeated letters individually; do not complete an expected spelling. |
| `Aburicauarague` | `Aburicauaraque` | Misreading `g` as `q` despite an otherwise expected /ge/ form | Treat linguistic implausibility as a prompt for enlarged reinspection. |
| `tçutomeuo` | `tçutomemo` | Reading `u` as `m` without testing the Japanese phrase | Use morphology to flag a sequence, then confirm the individual types in the scan. |
| `vgoqu` | `vgogu` | Failing to test the apparent spelling against Japanese *ugoku* | Use Japanese verb morphology to flag the final consonant, then distinguish `q` from `g` in enlargement. |
| `macu` | `inacu` | Treating adjacent strokes as `in` without testing Japanese *ikusano maku* or the Portuguese gloss “curtains” | Use both languages to flag the form, then distinguish the single `m` type in enlargement. |
| `bocetinha` | `bocezinha` | Making an unfamiliar Portuguese diminutive into a visually plausible non-word | Test the complete gloss during Portuguese review and reinspect the suspect letters. |
| `deſiguaes` | `deſiguais` | Unconsciously modernizing an older Portuguese plural | Preserve the printed vowel even when a modern form is more familiar. |
| `Interieção` | `Interieição` | Supplying the extra vowel expected from modern Portuguese *interjeição* | Count the printed vowels; compare repeated occurrences of the same word on the page. |
| `cà peralà` | `cã perali` | Treating the first diagonal grave as a tilde, then misreading final grave `à` as dotted `i` | Compare both the diacritic and the base letter; test the historical phrase *de cá pera lá*. |
| `baxo`, `touçinho` | `baixo`, `toucinho` | Modernizing an older Portuguese spelling while reading fluently | Align every source token to the transcription before accepting lexical familiarity. |
| `afiuela`, `Aburauo tçugu` | `a fiuela`, `Aburauotçugu` | Supplying or removing a space from grammatical expectation | Treat each visible word boundary as an independent source feature. |
| `vzão`, `Aquẽtarſe` | `vſão`, `Aquentarſe` | Reading the expected word instead of the printed `z`, or silently expanding an abbreviation | Inspect the base letter and mark separately; preserve printed abbreviation rather than its expansion. |
| `mu`, `Aburauo ſumuru` | `miru`, `Aburauo funuuru` | Failing to parse the historical Japanese verb, compounded by `ſ`/`f` and `m`/`n`/`u` confusion | Parse the complete Japanese phrase, then confirm every type in enlargement. |
| `menhaã`, `antemenhaã`, `briguigoĩs` | `menhã`, `antemanhã`, `briguigõis` | Losing a weak vowel or assigning a tilde to the expected vowel rather than the printed base | Inspect every base and each mark independently, including faint letters and marks over a vowel sequence; then sweep repeated forms on the same page. |
| `Aca muſubu`, `dedia` | `Acamuſubu`, `de dia` | Regularizing source spacing in opposite directions | Compare the actual gap at enlargement even when morphology or Portuguese syntax strongly predicts a boundary. |
| `Huns`, `aſsi`, `peſsoa`, `Paſsar` | `Hũs`, `aſſi`, `peſſoa`, `Paſſar` | Inferring a tilde or treating two visibly different sibilant types as an expected pair | Require visible ink for a mark and classify each member of a repeated-letter sequence separately. `ſs` and `ſſ` have no lexical contrast here, but Level 1 retains the printed allographs. |
| `peſoa`, `neceſsidade` | `peſſoa`, `neceſſidade` | Supplying the expected number of s-types, then making a surviving pair all long | Count both the number and the form of the printed types. A familiar spelling does not establish doubling, and a true pair may still be mixed `ſs`. |
| `cazados`, `Eſclarçeo`, `melõẽs` | `caſados`, `Eſclareceo`, `melões` | Regularizing historical Portuguese letters, spelling, or a marked vowel sequence | Treat familiar Portuguese as a diagnostic prompt only; align every printed character and mark before accepting the word. |
| `Qinomiga`, `Sagui yuqu`, `Accô ſuru`, `Tçuqi` | `Qinoniga`, `Sagui yiqu`, `Accô iuru`, `Tçuyi` | Accepting a visually plausible form without parsing the Japanese phrase | Parse particles and inflections, then use the predicted form to direct tight glyph comparison rather than to emend automatically. |
| `Couſaleue` | `Couſa leue` | Inserting a space between recognizable Portuguese words | Inspect the physical gap independently of lexical segmentation; Level 1 preserves the printed joining. |
| `A. xirouo` | `A xirouo` | Dismissing a small source-anomalous period as a paper speck because punctuation is linguistically unexpected | Isolate the mark at high enlargement and compare ink density, baseline placement, and nearby punctuation before either retaining or rejecting it. |
| `Fucaqu`, `Ajuocaqe`, `Amanegaua` | `Fucacu`, repeated `Ajirocaqe`, `Amanogaua` | Repairing visibly anomalous Japanese forms from morphology, repetition, or lexical expectation | Let Japanese identify the suspect span, then compare each base letter; Level 1 retains a confirmed source anomaly even when the expected form is certain. |
| `Aixizzumari, u, arta` | expected conjugational `atta` | Silently regularizing a visibly anomalous inflection | Compare the suspect sorts with a genuine same-page `atta`; on f25 the short `r` contrasts with two tall crossed `t` sorts. |
| `Amatiyori`, `Amagayeiu`, `Amano tebeco` | indexed or lexically expected `Amabiyori`, `Amagayeru`, `Amano toboco` | Letting a known word overwrite anomalous printed base letters | Use expectation only to locate the span, then compare the disputed sort with intact same-page `b/t`, `r/i`, and `e/o` forms; Level 1 retains the type actually present. |
| `Poëtas`, `printuras`, `baxo`, `cercido` | `Poetas`, `pinturas`, `baixo`, `cercado` | Reading through a small mark or completing a familiar Portuguese spelling | Isolate marks and unexpected internal letters; compare the disputed type with same-page `e/o`, `a/i`, and mark specimens before accepting the familiar word. |
| `Amano fara` | `Amano tara` | Reading a weak `f` without testing the Japanese phrase 天の原 and its exact Portuguese gloss “sky” | Use bilingual semantics to force tight reinspection, then accept only the letter shape supported by the scan. |
| `chouer`, `ſonzear`, `delgaça`, `eſtà`, `pès` | `chover`, `ſonjear`, `delgada`, `eſtá`, `pés` | Letting modern Portuguese silently replace visible historical or anomalous sorts and marks | Sweep repeated forms page-wide, then inventory every diagonal accent before classifying it; on f26 all four disputed marks match the secure grave in `à terra`, and no acute comparator occurs. |
| `galamiuo`, `bichintos` | expected Japanese `garamiuo`, Portuguese `bichinhos` | Letting a certain lexical restoration overrule unlike printed sorts | Compare inside the same word and typeface: on f26 the disputed `l` matches the printed variant marker while nearby `r` has a shoulder, and the second ascender of `bichintos` is a crossed `t` unlike the earlier `h`. |
| `Ameno farema`, `Decer do ceo` | provisional `Ameuo farema`, `Decer doceo` | Mistaking an upright-font `n` for `u`, or treating a narrow word space as an internal gap | Compare within the same typeface, and measure the suspect gap against both local interletter and word spaces; rejected candidates do not become corrections merely because OCR agrees. |
| `Bilho de ſaude`, `Amatçumi iora`, `Amatçu iora` | expected or normalized `Bicho`/`Milho`, `sora` | Letting lexical certainty replace anomalous printed sorts | Compare the disputed `l` with local `l`/`c`/`h`, and the dotted `i` with the unmistakable long `ſ` on the next line; Level 1 records the printed anomalies. |
| `Paſsante`, `Peſsoa`; `Paſsante,ou`, `annos,ou`, `comprido,ou` | doubled-long-s or regularly spaced forms | Normalizing repeated s-types or punctuation spacing while reading fluent Portuguese | Classify each sort separately, then inspect punctuation joins at nearest-neighbor enlargement and compare them with a local true word space. |
| f26 bottom-right `do` | final content line completing `mun-` | Classifying an isolated bottom-right word without consulting the next page | Check whether the following page begins with the same word. Here f27 begins `do às eſcuras`, proving that f26's `do` is a catchword. |

The first four findings and their scan adjudication are recorded in the [bnf-f0014 Wikisource comparison](../pilot/wikisource-comparison/bnf-f0014.md). `tçutomeuo`, `bocetinha`, and `deſiguaes` arose from the [contextual-review experiment](../pilot/contextual-review/f0248-f0643.md); `vgoqu` and `macu` were caught by human reader review after the [f249–f250 production simulation](../pilot/production-simulation/f0249-f0250.md). The later mixed-sibilant, historical-Portuguese, and spacing examples are recorded in the completed [f16 production review](../pilot/production-review/bnf-f0016.md); the source-anomaly, diaeresis, and `Amano fara` examples are recorded in the [f25 production review](../pilot/production-review/bnf-f0025.md). The useful result is the error taxonomy and review method, not continued dependence on an external transcription.

## Provisional Jesuit-romanization cautions

### `q`, `c`, `g`, and `gu`

- The system is Portuguese-based but source-specific. Modern Portuguese spelling intuition is useful only as a warning signal.
- `qe` is the ordinary pattern to expect for Japanese /ke/ in the *Nippo Jisho*; `qi` similarly occurs for /ki/. A complete occurrence inventory is still required.
- `gue` and `gui` can preserve hard /g/ before `e` and `i`. An apparent `q` where the Japanese form calls for /g/ should trigger comparison of the glyph with nearby `g` and `q`, not automatic correction.
- `qua` and `gua` represent the labial glides /kwa/ and /gwa/, historically written クヮ and グヮ. They contrast with `cua`, which can represent the two-vowel sequence /kua/.
- Long or historically compound members of the same labialized family include forms such as `quǒ` and `quau`. The letters following `qu` therefore need to be read as a sequence, not classified from the pair `qu` alone.
- `qu` can also represent ordinary /ku/. Morita cites *Vocabulario* forms such as `catamuqu` and `catamuquru`; `qua` is therefore not the only legitimate `q`-plus-`u` sequence.
- No secure Japanese `que` occurrence has yet been established for the *Nippo Jisho*. Related Jesuit works use forms such as `queô` and `xetxutque`, where `u` need not represent /w/. Do not infer that written `que`, if found, would prove a Japanese /kwe/ syllable.
- Keep dictionary-specific evidence separate from conventions reported for other Jesuit books or manuscripts. A spelling attested elsewhere is a comparison specimen, not proof of what this volume prints.

Principal research starting points:

- Takeshi Morita, translated by Mark Irwin, [“The Roman Transcription of the Christian Materials with a Focus on *Vocabulario da Lingoa de Iapam* and Rodrigues’ *Arte da Lingoa de Iapam*”](https://doi.org/10.20666/lij.1.0_117), especially the discussion of labial glides and exceptional spellings.
- Emi Kishimoto, [“On *-ia* Representing Contracted Sounds and Vowel Sequences in Christian Materials”](https://repository.kulib.kyoto-u.ac.jp/dspace/bitstream/2433/137270/1/kkr00002_001b.pdf), including the contrast between `qua`/`gua` and `cua`.

### Vowel marks

- `ǒ` and `ô` must not be treated as interchangeable decoration. In the audited material they distinguish the traditional open and closed long `o` categories.
- The caron is a downward-pointing wedge; the circumflex is an upward-pointing roof. Compare the shape, not only the expected vowel class.
- Marks over `u` require the same shape-level reading even though `u` lacks the corresponding open/closed opposition.
- Preserve grave accents and genuine tildes independently. Do not globally replace one accent family with another.
- Preserve abbreviation tildes as printed rather than expanding them in Level 1. On `f248`, the headword prints `Gǒyen`, but its example prints `Gǒyẽuo`, with `ẽ` abbreviating `en` before `uo`.
- The current occurrence-level evidence and Unicode choices are in the [Pilot Diacritic Audit](../pilot/diacritic-audit.md).

### Confusable characters and sequences

At minimum, check these pairs or patterns explicitly during enlarged review:

- `g` / `q`
- long `ſ` / `f`
- `n` / `u`
- `m` / `u`
- `i` / `l`
- one consonant / doubled consonant
- caron / circumflex / tilde / grave

Nearby letters from the same page and type size are better comparison specimens than a modern font. Linguistic plausibility ranks possible readings but does not decide between visible glyphs.

## Documentary cautions

- Preserve printed capitalization even when entry analysis suggests a headword.
- Defer headword status and entry boundaries to the structural layer. There, determine them independently of capitalization: alphabetical position, typeface, punctuation, semantic completeness, and surrounding syntax may establish an entry boundary even when the printer used a lowercase initial.
- Preserve printed spacing even when it conflicts with Japanese morpheme boundaries. Morphological segmentation belongs in the structured layer.
- Preserve physical line division and printed word division in the page layer until a documented generated view joins them.
- Preserve visible catchword text and position in the page layer; store its later structural interpretation separately. Do not add a hyphen merely to indicate that the anticipated word is divided.
- Distinguish repeated running headers from internal section headings and retain both in the page layer.
- Preserve apparently displaced words, their placement marks, and their physical position in the page layer. Assign them a logical reading order only in the linked structural layer and generated views.
- Inventory roman and italic type before deciding whether the distinction should be explicit or generated from entry roles.

The evidence for catchwords, displaced text, typeface, and diacritics is maintained in [Working Editorial Observations](../pilot/working-observations.md).

## External-transcription policy

Routine transcription and review will proceed directly from the Gallica scan without consulting Wikisource. Its current coverage is too small and insufficiently reviewed to benefit whole-volume production, and routine use would introduce avoidable provenance and licensing complexity.

The completed comparison remains useful because it exposed four corrections and several recurring error mechanisms. Wikisource or another external transcription may be consulted only as an exceptional aid after independent review when a reading remains unresolved. Any such consultation must identify the exact source and revision, remain separate from the independent checkpoint, and be adjudicated against the scan.

NINJAL's [Nippo Jisho Headword Data](headword-data.md) is treated differently from a page transcription because it supplies dictionary-wide source-order coverage. It may be compared routinely after an independent page checkpoint to detect missing entries, entry-boundary differences, and suspicious readings. Its structural claims and its diplomatic forms must be evaluated separately: for example, it correctly identifies `aburamono` as a headword but normalizes it to `Aburamono.` It must not be opened as a substitute for the initial visual pass or used to normalize the diplomatic layer automatically.

## Work still required

Before this guide becomes normative:

1. Build an occurrence inventory for important romanization sequences across a larger scan-derived sample.
2. Separate conventions specific to the *Nippo Jisho* from those in Rodrigues’s *Arte* and other Christian materials.
3. Add verified page examples and counterexamples for each proposed pattern.
4. Classify cautions as strong distributional rules, variable conventions, or merely common tendencies.
5. Incorporate adopted rules into the version 1 transcription specification while retaining this document as their evidence trail.
