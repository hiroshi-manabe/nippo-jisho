# Historical Language Notes for Transcription

## Purpose and scope

This is the detailed layer behind the [Transcription Cheat Sheet](transcription-cheat-sheet.md). It gathers historical Japanese, Jesuit-romanization, Early Modern Portuguese, and printing knowledge that can improve direct reading of the *Vocabulario da Lingoa de Iapam*. It is a transcription aid, not a grammar, a normalization standard, or a substitute for the scan.

The notes deliberately distinguish what the dictionary itself says from what is known about other Jesuit works. This matters because the system was broadly regular but never completely standardized, and because individual books, compositors, and even sections of one book can differ.

## How to use the evidence

The project uses this order of authority:

1. **The exact Gallica scan location** decides the Level 1 reading.
2. **The dictionary's own prologue and key** state how its compilers intended the work to be used.
3. **Repeated forms within the dictionary** provide local comparison types and distributional evidence.
4. **NINJAL headword data** supplies a broad, attributed checkpoint, not a diplomatic authority.
5. **Rodrigues and other contemporary Jesuit sources** explain the wider system but cannot prove what this impression prints.
6. **Modern scholarship** reconstructs patterns and exceptions; it is diagnostic evidence, not a source of replacement text.

The labels used below are:

- **Dictionary-specific:** explicitly stated in the *Vocabulario* or verified repeatedly in its scan.
- **Jesuit-print pattern:** demonstrated across related romanized works and likely useful here, but requiring dictionary confirmation.
- **Variable:** known exceptions, competing spellings, or unresolved phonetic interpretation make automatic correction unsafe.
- **Project observation:** learned from the present pilot; it remains revisable as coverage grows.

## 1. The dictionary's own key

The primary guide is the two-page section “Algũas advertencias necessarias pera o vſo, & intelligencia deste Vocabulario” at [Gallica `f11`](https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f11.item) and [`f12`](https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f12.item).

### 1.1 Ordering and lookup

**Dictionary-specific.** The key says that entries follow the Latin alphabet rather than grouping words by derivational families. It gives a special internal order for `G` words—beginning with `G`, `Ga`, `Gan`, `Gue`, `Guen`, `Gui`, `Go`, `Gu`, `Guan`, `Gi`, `Gio`, `Giu`—and places consonantal `I` (`Ia, Ie, Ii, Io, Iu`) after vocalic `I`, reserving Greek `Y` for a position near the end of the alphabet.

This is valuable for coverage review and ambiguous headwords, but it is not a licence to change a visible letter merely to restore expected order. Misprints and exceptional ordering are possible.

The key also uses `Gu-i` to show that vocalic `i` is a separate syllable rather than part of `gui`. A printed hyphen can therefore be linguistic rather than a line-break repair; preserve it before interpreting it.

### 1.2 Register and domain labels

**Dictionary-specific.** The key explains `X.`, `alicubi`, `P.`, `S.`, `Bup.`, and final `B.` as regional, restricted, poetic, written, Buddhist, and low-register labels respectively. It also explains that comparisons with *Cami* usage may be stated in prose. These labels are strong clues to the function of surrounding text, especially where roman and italic types are difficult to distinguish.

The lowercase `l` occurring between forms is Latin *vel* “or.” NINJAL's source documentation confirms that its dataset normalizes this printed `l` to a vertical bar, which is one reason the dataset cannot be copied directly into Level 1.

### 1.3 `E`/`I` variation

**Dictionary-specific and variable.** The key tells the reader that words involving certain long-vowel spellings may be entered with either `E` or `I`, partly because contemporary kana spelling and pronunciation point in different directions. It explicitly advises searching under the other letter if a word is not found and gives paired examples such as `Meǒji` / `Miǒji` and `Riǒchi` / `Reǒchi`.

Morita's study expands this point: forms in `eô` and `iô` can compete, and some spellings preserve contemporary kana or morphological connections rather than representing pronunciation in a mechanically phonographic way (Morita 2024: 118–121). Consequently, an unfamiliar `e` is a reason to inspect carefully, not to substitute `i`.

## 2. Japanese in Jesuit romanization

### 2.1 The system is regular but not exceptionless

**Variable.** Morita describes a shared Jesuit transcription practice used consistently at a broad level, while documenting multiple graphemes for the same sound, unusual spellings, kana-influenced forms, and errors in the *Vocabulario* and Rodrigues's *Arte* (2024: 117–118, 129). This dual fact governs the project:

- learned expectations are powerful error detectors;
- no expectation is a global substitution rule.

### 2.2 Core consonant cues

The following are reading cues rather than modern transliterations:

| Jesuit form | Broad cue | Status and danger |
| --- | --- | --- |
| `ca, co, cu`; `qe, qi` | /k/ series | Strong dictionary distribution; `q/g` remains visually confusable. |
| `ga, go, gu`; `gue, gui` | /g/ series | Strong dictionary distribution; do not turn an unfamiliar hard-`g` spelling into `q`. |
| `qua`, `gua` | historical /kwa, gwa/ | Distinguished from non-labial sequences; individual exceptions exist. |
| `x` | broadly the historical sound corresponding to modern *sh* in many words | Useful for recognition only; preserve `x`. |
| `tç` | broadly the historical sound corresponding to modern *ts* | The letters may be ligatured in related prints; preserve the visible sequence. |
| `f` | often corresponds to a modern h-row sound | Do not modernize to `h`; distinguish it from long `ſ`. |
| `ji` / `gi`, `zu` / `zzu` | intended yotsugana distinctions | Morita documents substantial confusion in both the *Vocabulario* and *Arte* (2024: 123). |

### 2.3 What the headword data says about `q`

**External checkpoint, not scan authority.** A case-insensitive count over the 32,878 romanized headword strings in NINJAL version 202510 gives:

| Sequence beginning at `q` | Occurrences |
| --- | ---: |
| `qi` | 4,527 |
| `qe` | 1,838 |
| `qu` | 870 |
| other marked or uppercase continuations | 5 |

Among the 870 `qu` occurrences, the next character is `a` in 554 and caroned `ǒ` in 97; 148 end the captured sequence with punctuation after `qu`. The dataset has only two `que` and seven `qui` strings, and no `quo`. It also has 166 `gua` but only five `cua` occurrences.

These counts support four working cautions:

1. `qe` and `qi`, not modern-looking `ke` and `ki`, are normal in headwords.
2. `qu` is not confined to `qua`; it can represent /ku/ and occur at a stem or form boundary.
3. `qua`/`gua` are strong prompts for historical labial glides, while `cua` can represent /kua/ as a vowel sequence.
4. A written `que` or `qui` must be read as a complete sequence in context. Its mere presence does not establish a Japanese /kwe/ or /kwi/ syllable.

The calculation is reproducible from the official headword field documented in [NINJAL Headword Data](headword-data.md). Because those strings come from a Bodleian-based edited dataset and difficult readings may follow the copyrighted 1980 edition, they are distributional evidence only.

Kishimoto's study of `-ia` similarly shows why an identical letter sequence cannot always be assigned one phonetic interpretation: within one word it can represent a contracted syllable, while at a boundary it can represent a vowel sequence (1999: 1–11). The same discipline—read the whole lexical and morphological environment—applies to `qua`, `cua`, and other glide-like sequences.

### 2.4 `u` and `v` are positional as well as phonetic

**Jesuit-print pattern, strongly useful.** In their quantitative study of the 1596 *Contemptus mundi*, Takahashi and Osterkamp show that lowercase `u` and `v` can represent the same Japanese /u, w/ material. Initial or potentially morpheme-initial position tends to take `v`, while internal position takes `u`; particles such as `uo` and `ua` retain `u` because they are treated as dependent on what precedes them (2025: 49–50). Compounds can retain a morpheme's initial `v`, though exceptions occur.

This explains why Japanese knowledge correctly flags `vgogu` as suspicious and makes printed `vgoqu` intelligible. It also explains why modern phonetic intuition alone cannot choose between `u` and `v`. The exact scan and the word's internal structure must both be checked.

The dictionary-wide extent of this pattern still needs a dedicated inventory; it should not be promoted to an automatic rule from a different Jesuit book.

### 2.5 Long `o`: two marks, one difficult distinction

**Dictionary-specific glyph distinction; variable historical interpretation.** The project records:

| Mark | Traditional label | Level 1 character |
| --- | --- | --- |
| downward caron `ˇ` | 開音, “open” long *o* | `ǒ` |
| upward circumflex `ˆ` | 合音, “closed” long *o* | `ô` |

The two types occur clearly on the same dictionary page—for example `Goxxǒ` and `Acugôno` on `f248`—so their shape-level distinction is secure. The [Diacritic Audit](../pilot/diacritic-audit.md) supplies occurrence-level images and Unicode choices.

The phonology is less simple than a two-symbol chart suggests. Morita documents confusion between the categories even in sources that explain them, including 19 *Vocabulario* verb forms in which the expected class is reversed (2024: 123–126). Kishimoto's analysis of Christian texts concludes that the common phonetic interpretation is not by itself proved by the kana evidence and that behavior differs by book and word (1999: 13–14). Therefore:

- use vowel history to identify a place needing reinspection;
- identify `ǒ` versus `ô` from the printed direction of the mark;
- do not “correct” a clearly printed mark from etymology.

### 2.6 Long `u` and other marks

**Jesuit-print pattern, visually confirmed in the dictionary.** Long `u` lacks the open/closed opposition of long `o`. Chiba found that Jesuit romanized books use more than one accent shape over `u` because any such mark could visually distinguish a long vowel from plain `u`; the choice could be left to the page compositor (2009; 2022). The dictionary sample contains caron and circumflex shapes over long `u`; it also contains a grave over `u`, which Level 1 keeps as a separate mark rather than assimilating to either of them.

Tildes must be classified separately. Portuguese uses them for nasal material, while the dictionary also uses abbreviation tildes: `q̃` visibly carries an abbreviation sign, and `Gǒyẽuo` prints `ẽ` where the uncontracted headword has `en`. Level 1 preserves the mark without expansion.

The carrier of a tilde is itself source evidence. The audited corpus prints both `algũa` and `alguã`, including their capitalized, plural, and contracted forms. The occurrence-level scan ledger currently records 237 marks over `u` and 151 over final `a`; `bnf-f0019:c2b-l011` is one of the latter. Early Portuguese sources and scholarship allow positional variation, and a separately set mark can also be displaced in movable type. Consequently neither historical expectation nor the spelling of a neighboring occurrence licenses moving the mark. See the [`algũa` / `alguã` Tilde-Position Audit](../pilot/tilde-position-audit.md) and its complete ledger.

Portuguese grave accents also require shape-level comparison. On `bnf-f0013:c1-l033`, the wavy tilde in `ordẽ` contrasts on the same line with single diagonal strokes in `cà peralà`. The latter marks match the confirmed grave in `arà` on `c1-l016`; the final letter has the bowl of italic `a`, not the simple stem of `i`. The phrase is historically well supported: [Gil Vicente](https://ceteatro.pt/wp-content/uploads/2018/01/festa-d66.pdf) has `de cá pera lá`, and the related [*Vocabulário na Língua Brasílica*](https://upload.wikimedia.org/wikipedia/commons/8/84/Vocabul%C3%A1rio_na_l%C3%ADngua_bras%C3%ADlica_%28A3%29.pdf) has `de ca pera la`. Duarte Nunes de Leão describes the grave with the form `à` and recommends accents where they differentiate otherwise similar words ([1576, fols. 65v–66r](https://pml.cel.utad.pt/ViewEntry.aspx?id_entry=9)). These parallels identify the place for comparison, but the local type remains decisive.

### 2.7 Sound change, kana spelling, and variation

Several patterns are especially useful during the Japanese pass:

- **Sandhi:** Morita finds that pronunciation-changing sandhi existed but Jesuit transcription generally retained the unsandhied, kana-related form (2024: 121–122). Do not force the expected spoken assimilation.
- **Gemination:** doubled letters and mixed homophonous sequences can represent geminates, but `t` may also preserve a kana- or morpheme-final analysis (Morita 2024: 122–123). Count what is printed.
- **Sino-Japanese checked final `t`:** the dictionary can preserve a bare syllable-final or word-final `t` rather than open it as `tçu`. Irie's corpus analysis counts checked syllables as 6.3% of the dictionary's Sino-Japanese word-final phonological units, and modern work on inherited Noh pronunciation likewise cites dictionary forms such as `Iixet`, `Tenbat`, `Ichiguat`, and `Xǒmet` as closed-syllable spellings. The generated kana guide renders this coda with small ッ (`Nhôjet` → ニョゥゼッ), following the practical convention also used by the NINJAL headword data. This ッ is editorial notation for historical final /t/, not a claim that its phonetic realization was simply the same as an ordinary modern sokuon; Level 1 continues to preserve the printed `t`.
- **Yotsugana:** `ji/gi` and `zu/zzu` distinctions were intended but frequently confused (Morita 2024: 123). Etymology is corroboration, not adjudication.
- **`m/b` doublets:** the *Vocabulario* contains genuine competing forms, and Morita argues that at least some reflect different pronunciations rather than mere spelling variants (2024: 126–127).
- **Nasal and long-vowel interaction:** Morita records `n`, `ǒ`, and `ô` variation, especially in certain verb forms, alongside foreign-speaker and dialect effects (2024: 124–126). A seemingly extra `n` is not automatically an OCR-like error.

### 2.8 Morphology is part of Level 1 review, not Level 1 data

The dictionary frequently gives multiple principal forms after a Japanese word, separated by commas: examples include `Ague,ru,eta` and `Abaqi,u,aita`. Such patterns allow a reviewer to notice that an apparent letter sequence would produce an implausible verb or particle construction. That is how `tçutomemo` led back to printed `tçutomeuo`, `vgogu` to `vgoqu`, and `inacu` to `macu`.

The resulting Level 1 text still records only the printed sequence. Identifying a stem, expanding an abbreviation, segmenting `uo` as a particle, supplying kanji or kana, and describing an inflection belong to later analysis.

## 3. Spacing, segmentation, and typography

### 3.1 Spaces are meaningful but inconsistent

**Jesuit-print pattern and project observation.** Takahashi and Osterkamp show that Jesuit practice changed during the printing of *Feiqe no monogatari* in 1592: later works generally attach particles and other enclitics rather than placing spaces before them. Neither the earlier nor the later practice is fully consistent. Spacing can reflect grammatical analysis, readability, oral performance, justification, and production constraints rather than a single word-boundary theory (2025: 34–35, 57–58).

This directly supports the project's treatment of printed `Aburaqega ſuru`: inserting `Aburaqe ga` because `ga` is a particle destroys source evidence. Copy the physical spacing first; add morphological segmentation later.

### 3.2 Other segmentation cues

The same 2025 study demonstrates that capitalization, word-final letter shapes, `u/v`, hyphens, and ligatures can all participate in segmentation. These cues can conflict. The dictionary adds its own roman/italic contrast, alphabetical ordering, punctuation, and layout.

The lowercase but independent `aburamono` entry is therefore not paradoxical. Capitalization is one clue among several; entry typeface, punctuation, alphabetical position, and a complete Portuguese gloss establish the structural boundary. Level 1 preserves lowercase print, while a later layer records the entry.

### 3.3 Long `ſ`

Long `ſ` is not simply `f`, and in Japanese romanized prints its distribution may itself mark continuation inside a word. Chiba's survey argues that round `s` and long `ſ` have functional distributions rather than being random allographs, though type collision with following diacritics also affects the choice (2008: 27–36). In Portuguese glosses, long `ſ` is also an ordinary early-print allograph.

Operationally, compare the type and the complete word, preserve whichever form is printed, and do not infer a universal morpheme boundary from `s/ſ` alone.

## 4. Early Modern Portuguese in the glosses

### 4.1 Why modern spelling is unsafe

The dictionary predates official modern Portuguese orthography by centuries and was printed far from Lisbon by a multilingual mission press. Contemporary writers themselves debated spelling. Duarte Nunes de Leão's 1576 *Orthographia da lingoa portuguesa* devotes separate chapters to letters, diphthongs, division of words, doubled letters, accents, apostrophes, abbreviations, and punctuation; its [BnP scan](https://purl.pt/15) and [searchable PML edition](https://pml.cel.utad.pt/ViewEntry.aspx?id_entry=9) are the best primary comparators.

Even one Jesuit work can change practice internally. Takahashi and Osterkamp report that Rodrigues's Portuguese in the *Arte* strongly favors `ão` and `ey` through folio 94, then strongly favors `am` and `ei` from folio 95 (2025: 34 n. 9). Morita also points to *Vocabulario* gloss pairs such as `Ceremonia`/`Cerimonia`, `menino`/`minino`, and `infirmidade`/`enfermidede` (2024: 120). Variation is evidence, not noise to remove.

The opening dictionary page gives a compact warning against lexical modernization: it prints `Interieção` three times (`bnf-f0013:c1-l007`, `c1-l009`, and `c1-l016`), without the second `i` of modern Portuguese *interjeição*. Consonantal `i` represents modern `j`, while the remaining vowel sequence reflects historical orthographic variation. João de Barros's 1540 *Grammatica* similarly uses related forms such as `Interieçam`. Read and count the printed vowels before allowing the modern lemma to guide recognition.

### 4.2 Practical Portuguese reading categories

| Feature | Why it matters at Level 1 |
| --- | --- |
| `ſ` versus `f` | They are different letters but visually close; the complete Portuguese word often exposes a misreading. |
| `u` / `v`, `i` / `j` | Historical editions preserve these characters independently of modern vowel/consonant values. Copy the glyph rather than modernizing the word. |
| `c` / `ç` | Cedilla use is not governed by modern Portuguese spelling in this source. A printed `ç` may occur where modern spelling has plain `c`, even before `e` or `i`; scan-confirmed examples include `touçinho`, `Eſclarçeo`, and `açẽdem`. Preserve or omit the cedilla occurrence by occurrence from visible ink. |
| tildes | They can denote nasalization or omitted material. Preserve their occurrence-level placement and do not expand them; this dictionary genuinely varies between forms such as `algũa` and `alguã`. |
| accents | They may represent stress, vowel quality, length in Japanese material, or a different mark entirely. Classify the local sign. |
| doubled letters | Contemporary spelling and typesetting can differ from modern expectation. Count the printed types. |
| vowel and ending variants | Forms such as printed `deſiguaes` can look wrong to a modern reader but be historically coherent. |
| spacing and punctuation | `de mais`, contractions, commas, colons, and clause boundaries need not follow modern practice. Preserve them. |
| abbreviations and `&` | Expansion is editorial interpretation and belongs after Level 1. |

The modern [Portugaliae Monumenta Linguistica](https://pml.cel.utad.pt/?lang=2) project is useful precisely because it exposes historical Portuguese grammars and orthographies. Its published semidiplomatic criteria preserve `u/v`, `i/j`, italics, lineation, and unexpanded tilde notation while normalizing long `ſ` to round `s`. Our stricter Level 1 makes a different, explicit choice on the last point: it preserves `ſ` because glyph-level evidence and `ſ/f` confusion matter to this project.

### 4.3 The bilingual review pass

For every gloss, ask:

1. Does the Portuguese form exist historically or fit a productive historical spelling or inflection?
2. Does its meaning fit the Japanese form and example?
3. Is an odd sequence better explained by `ſ/f`, `g/q`, `m/in`, a missing or doubled type, or a damaged impression?
4. After enlargement, does the scan support the contextually preferred reading?

The pilot demonstrates both sides of the method. Portuguese context found printed `bocetinha` where `bocezinha` had been read, and printed `deſiguaes` where a modernized `deſiguais` had been supplied. Conversely, the scan required preservation of unfamiliar `anotomia` and spaced `de mais`. Context finds the question; the scan answers it.

## 5. Source cards

### Primary sources

- **The *Vocabulario* scan.** Bibliothèque nationale de France, [complete Gallica object](https://gallica.bnf.fr/ark:/12148/bpt6k852354j); prologue/key at [`f11`](https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f11.item) and [`f12`](https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f12.item). First authority for the project.
- **João Rodrigues, *Arte da Lingoa de Iapam* (1604–1608).** A contemporary systematic account of Japanese used to explain broader Jesuit practice. A public-domain [scan is available through Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arte_da_Lingoa_de_Iapam.pdf). It is a comparator, not part of the *Vocabulario*.
- **Duarte Nunes de Leão, *Orthographia da lingoa portuguesa* (1576).** Contemporary Portuguese orthographic treatise: [Biblioteca Nacional de Portugal scan](https://purl.pt/15) and [PML transcription/catalogue](https://pml.cel.utad.pt/ViewEntry.aspx?id_entry=9).
- **João de Barros, *Grammatica da lingua portuguesa* (1540).** Near-contemporary evidence for Portuguese grammatical terminology and variable spelling, including forms related to the dictionary's `Interieção`: [Biblioteca Nacional de Portugal scan](https://purl.pt/12148).

### Modern scholarship

- Takeshi Morita, translated by Mark Irwin, [“The Roman Transcription of the Christian Materials with a Focus on *Vocabulario da Lingoa de Iapam* and Rodrigues’ *Arte da Lingoa de Iapam*”](https://doi.org/10.20666/lij.1.0_117), *Language in Japan* 1 (2024), 117–130; original Japanese article published 1955. Best compact survey of dictionary-specific variation. The translation is CC BY-NC-ND 4.0; these notes paraphrase and cite it rather than reproducing it.
- Emi Kishimoto, [“キリシタン資料の拗音および連母音を表す -ia について”](https://doi.org/10.14989/137270), *京都大学國文學論叢* 2 (1999), 1–11. Contracted syllables, vowel sequences, and the danger of assigning one reading to a letter string.
- Emi Kishimoto, [“キリシタン版国字本における本語の開合表記”](https://doi.org/10.14989/137276), *京都大学國文學論叢* 3 (1999), 1–17. Long-*o* categories, variation by book, and limits of simple phonetic reconstruction.
- Takashi Chiba, [“キリシタン・ローマ字文献のウ段長音の表記について”](https://doi.org/10.18999/nagujj.102.104), *名古屋大学国語国文学* 102 (2009), 104–92, and [“キリシタン文献・ローマ字本のウ段長音表記変遷について”](https://doi.org/10.18999/nagujj.115.96), no. 115 (2022), 96–82. Multiple marks over long `u` and the role of printing decisions.
- Takashi Chiba, [“キリシタン・ローマ字文献における s とその異体字について”](https://doi.org/10.18999/nagl.2.27), *Nagoya Linguistics* 2 (2008), 27–36. Distribution and possible segmentation function of round `s` and long `ſ`.
- Sophie Takahashi and Sven Osterkamp, [“Reading Between the Words in Romanized Japanese”](https://doi.org/10.20666/lij.2.0_30), *Language in Japan* 2 (2025), 30–61. Quantitative account of spacing, hyphenation, `u/v`, capitalization, and ligatures in a related Jesuit print. CC BY-NC-ND 4.0.
- Sayaka Irie, [*日本語の音素の分布・配列に関する歴史的研究*](https://doi.org/10.14988/pa.2017.0000013649), *同志社日本語研究* special issue 1 (2012), 1–210. Quantitative analysis of phoneme distributions, including checked codas in the dictionary's Sino-Japanese vocabulary.
- Rolf Kemmler et al., [“Dos Ortógrafos Portugueses aos Portugaliae Monumenta Linguistica”](https://doi.org/10.21814/diacritica.5584), *Diacrítica* 38.1 (2024), 146–164. Source portal and explicit semidiplomatic editorial criteria for historical Portuguese orthographies.

### External data

- NINJAL, *Entry Words Data of Nippojisho*, version 202510, documented locally in [NINJAL Headword Data](headword-data.md). Its 32,878 source-order records are licensed CC BY 4.0. Use for coverage and suspicious-form detection only after an independent visual checkpoint.

## 6. What still needs research

This reference should grow from production findings, but only where a note changes reading behavior. High-value next steps are:

1. replace the NINJAL-based sequence counts with a full scan-derived dictionary transcription inventory;
2. measure dictionary-specific `u/v`, spacing, `s/ſ`, and ligature distributions rather than importing patterns from *Contemptus mundi*;
3. transcribe and annotate the complete `f11`–`f12` key as an independent public-domain primary-source artifact;
4. add compact Portuguese lemma notes only for recurrent forms that actually cause transcription errors;
5. attach newly discovered rules to at least one exact dictionary page example and one counterexample where possible.

Raw page-specific discoveries continue to belong in [Working Editorial Observations](../pilot/working-observations.md). Only findings that generalize into a repeatable reading caution should graduate into this document and then, if short enough, into the cheat sheet.
