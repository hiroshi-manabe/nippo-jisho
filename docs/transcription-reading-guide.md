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

These findings and their scan adjudication are recorded in the [bnf-f0014 Wikisource comparison](../pilot/wikisource-comparison/bnf-f0014.md). The useful result is the error taxonomy, not continued dependence on Wikisource.

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
- The current occurrence-level evidence and Unicode choices are in the [Pilot Diacritic Audit](../pilot/diacritic-audit.md).

### Confusable characters and sequences

At minimum, check these pairs or patterns explicitly during enlarged review:

- `g` / `q`
- long `ſ` / `f`
- `n` / `u`
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
