# Provisional Transcription Reading Guide

## Status and purpose

This is a working quality-control guide for direct visual transcription of the *Nippo Jisho*. It records source-specific reading cautions discovered during the transcription-format pilot. It is not yet the version 1 transcription specification, a complete account of Jesuit romanization, or authority to normalize the printed text.

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

Production review should separate four perspectives so that expectation does not silently become evidence:

1. **Initial visual pass:** record the apparent print in physical order without consulting an external transcription.
2. **Japanese and romanization pass:** test forms against historical Japanese morphology, syntax, and source-specific spelling patterns. Use implausibility to flag passages for reinspection.
3. **Portuguese and bilingual-context pass:** test whether the Portuguese gloss and the relationship between both languages expose a likely misreading.
4. **Final scan confirmation:** inspect every proposed contextual correction again, enlarged when useful, and accept it only if the printed shapes support it.
5. **Human column review:** after generation, a named human reviewer compares the scan and current Level 1 text one column at a time, followed by a separate page-furniture check.

The second and third passes diagnose possible errors; they do not normalize the text. For example, Japanese context exposes the initial `bodaino tçutomemo naſu` as suspicious, and the scan confirms `bodaino tçutomeuo naſu`. Level 1 records that confirmed printed sequence. Dividing it as `tçutome + uo`, restoring Japanese script, explaining the particle, and translating it belong to later stages.

Page status uses `visual_draft` after the initial visual pass, `context_reviewed` after both contextual passes, and `scan_confirmed` after every flag and the complete page have been checked again against the scan. Human review then proceeds through column 1, column 2, and page furniture in the generated [side-by-side review interface](../pilot/human-review/README.md). The normal interactive correction loop is deliberately simple: the reviewer reports a line ID and proposed reading in the project chat; reviewer and transcriber discuss contextual evidence and the enlarged scan; the transcriber changes only the canonical Level 1 Markdown, regenerates the interface, and reopens the affected unit. When all three units record reviewer and timestamp, the page may become `human_checked`. The pilot's broad `trial_reviewed` label predates this workflow and must not be assigned to new work or interpreted as a permanent claim that no further correction is possible.

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

The first four findings and their scan adjudication are recorded in the [bnf-f0014 Wikisource comparison](../pilot/wikisource-comparison/bnf-f0014.md). `tçutomeuo`, `bocetinha`, and `deſiguaes` arose from the [contextual-review experiment](../pilot/contextual-review/f0248-f0643.md); `vgoqu` and `macu` were caught by human reader review after the [f249–f250 production simulation](../pilot/production-simulation/f0249-f0250.md). The useful result is the error taxonomy and review method, not continued dependence on an external transcription.

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
