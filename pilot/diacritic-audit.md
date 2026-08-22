# Pilot Diacritic Audit

## Scope and revision history

This audit checks vowel marks in the three frozen pilot transcriptions directly against the native-resolution Gallica images. It does not claim to inventory the complete dictionary. Wikisource and OCR were not consulted.

An initial audit incorrectly treated every `ô` or `û` in the frozen drafts as a caron. That conclusion, committed as `e7acf6f`, is superseded here. It resulted from recognizing the caron in `Gǔcon` correctly but then generalizing its glyph shape without comparing every occurrence. The revised audit checks each of the 37 flagged occurrences individually and uses historical vowel class only as corroboration. A later full-page transcription pass also corrected adjacent letters that the mark-only audit had inherited from the frozen drafts.

## Historical basis

The Jesuit notation distinguishes two long *o* vowels:

| Printed mark | Traditional category | Approximate value | Diplomatic character |
| --- | --- | --- | --- |
| Caron/háček | 開音, open long *o* | /ɔː/ | `ǒ` |
| Circumflex | 合音, closed long *o* | /oː/ | `ô` |

João Rodrigues describes the former with a more open mouth and lips and the latter with the mouth somewhat closed and the lips rounded. Later scholarship summarizes the notation as `ǒ` for the relatively open long vowel and `ô` for the relatively closed one. The contrast often reflects different historical vowel sequences, but etymology is supporting evidence rather than permission to replace an unclear printed mark.

Long *u* did not have an analogous open/closed opposition. Research on Jesuit romanized books reports that multiple accent signs could be used over `u`, partly as a visual indication of length. The audit therefore classifies marks over `u` by their printed shape without importing the `ǒ`/`ô` phonological contrast.

References:

- Otto Zwartjes and Paolo De Troia, [“André Palmeiro’s *Epistola*: A linguistic analysis”](https://benjamins.com/catalog/sihols.130.01zwa), especially the discussion of Japanese romanization.
- Tomoaki Takayama, [“The changes of Vu hiatuses into long vowels in the history of Japanese language”](https://www.jstage.jst.go.jp/article/gengo1939/1992/101/1992_101_14/_article).
- Takashi Chiba, [“Changes in the Notation of Long U Vowels in Jesuit Mission Japanese Printing Press Characters”](https://cir.nii.ac.jp/crid/1390013010129899648).

## Revised result

The 37 occurrences previously encoded as `ô` or `û` resolved as follows. The retired row-level data remains available through Git history; this table is its historical summary.

| Result | `bnf-f0248` | `bnf-f0643` | Total |
| --- | ---: | ---: | ---: |
| Caron | 23 | 7 | 30 |
| Circumflex | 4 | 1 | 5 |
| Grave accent | 0 | 1 | 1 |
| No printed mark | 1 | 0 | 1 |
| **Total audited** | **28** | **9** | **37** |

Genuine tildes form a separate class. Their wavy shape is visible in forms such as `acõpanha` and `algũa`. Their carrier must also be read locally: the wider corpus genuinely varies between `algũa` and `alguã`, as documented in the [complete position audit](tilde-position-audit.md). Abbreviation tildes must likewise be preserved rather than silently expanded: `q̃` uses a combining tilde, while `Gǒyẽuo` prints `ẽ` in place of `en` before `uo`.

No caron or circumflex occurs in the drafted excerpts of `bnf-f0014`.

## `bnf-f0248` occurrence audit

Repeated forms with the same visible type are grouped, but every occurrence was checked in the overlapping sixth-column tiles.

| Frozen form | Reviewed form | Count | Printed classification | Corroborating context |
| --- | --- | ---: | --- | --- |
| `Goxôuo` | `Goxǒuo` | 1 | Caron | Same type as the adjacent `Goxǒ` forms. |
| `Goxô` / `goxô` | `Goxǒ` / `goxǒ` | 3 | Caron | Open long-*o* type is visually consistent across the entries. |
| `Conjô` | `Conjǒ` | 1 | Caron | Pointed downward wedge. |
| `Goxô` in “Paços do Cubô” entry | `Goxo` | 1 | No mark | The headword’s final `o` is visibly unmarked. |
| `Cubô` | `Cubǒ` | 2 | Caron | Pointed downward wedge; historically an open-series vowel. |
| `Goxô` in `Goxô jenxo` | `Goxǒ` | 1 | Caron | Pointed downward wedge. |
| `Goxxô` | `Goxxǒ` | 1 | Caron | Contrasts on the same line with the circumflex in `Acugôno`. |
| `Acugôno` | `Acugôno` | 1 | Circumflex | Upward-pointing roof shape; historically a closed-series vowel. |
| `Gôyei` / `Gôyeiuo` | `Gǒyen` / `Gǒyẽuo` | 2 | Caron | Pointed downward wedge. The headword prints final `n`; the example instead prints a tilde over `e` as an abbreviation for `n` before `uo`. |
| `Goyô` / `Goyôno` | unchanged | 3 | Circumflex | Upward-pointing roof; `yô` represents the closed long vowel in 御用 and 五葉. |
| `Gozô`, `cannozô`, `xinnozô`, `finozô`, `fainozô`, `jinnozô`, `Gozôroppu` | corresponding forms with `ǒ` | 7 | Caron | Repeated pointed downward wedge in the organ-name sequence. |
| `afô` | `afǒ` | 1 | Caron | Pointed downward wedge. |
| `Dôgu` / `dôgu` | `Dǒgu` / `dǒgu` | 2 | Caron | Pointed downward wedge. |
| `tarôta` | `tarǒta` | 1 | Caron | Pointed downward wedge. |
| `Gûcan` | `Gǔcon` | 1 | Caron over `u` | Shape classification only; full-page review also resolves the following vowel as `o`. |

The `Goyô` entries are decisive counterexamples to the superseded blanket conversion: their second `o` bears a circumflex and must remain `ô`.

## `bnf-f0643` occurrence audit

| Frozen form | Reviewed form | Count | Printed classification | Note |
| --- | --- | ---: | --- | --- |
| `Zzubôxi` | unchanged | 1 | Circumflex | Clear upward-pointing roof. |
| `Zzuchô` / `zzuchô` | `Zzuchǒ` / `zzuchǒ` | 2 | Caron | Pointed downward wedge. |
| `Ienxûs` | `Ienxùs` | 1 | Grave accent | A single descending stroke, not a two-stroke circumflex or caron. |
| `Zzufû` / `Zzufûga` | `Zzufǔ` / `Zzufǔga` | 2 | Caron over `u` | Shape classification only. |
| `Zzujô` | `Zzujǒ` | 1 | Caron | Pointed downward wedge. |
| `Zzuqijô` | `Zzuqiǒ` | 1 | Caron | Pointed downward wedge; no `j` is printed before the marked `o`. |
| `Zzurçû` | `Zzutçǔ` | 1 | Caron over `u` | Shape classification only; full-page review resolves the consonant sequence as `tç`. |

## Character inventory and encoding

| Mark | Character | Unicode treatment |
| --- | --- | --- |
| Caron over `o` | `ǒ` | U+01D2, LATIN SMALL LETTER O WITH CARON |
| Caron over `u` | `ǔ` | U+01D4, LATIN SMALL LETTER U WITH CARON |
| Circumflex over `o` | `ô` | U+00F4, LATIN SMALL LETTER O WITH CIRCUMFLEX |
| Grave over `u` | `ù` | U+00F9, LATIN SMALL LETTER U WITH GRAVE |
| Tilde over a vowel | for example `õ`, `ũ` | Precomposed character where available |
| Abbreviation tilde | for example `q̃` | Base character plus U+0303 when no precomposed form exists |

Reviewed text should be NFC-normalized where a precomposed character exists.

## Representative image evidence

These crops are derived without enhancement from the cached Gallica masters. Coordinates use `[left, top, right, bottom]` pixels in the corresponding source image.

| Evidence | Master and crop box | SHA-256 |
| --- | --- | --- |
| [`Goxǒ`](glyph-samples/bnf-f0248-caron-goxo.jpg) | `f0248.jpg`, `[300, 756, 950, 1076]` | `a7914efb8e3278aa7b0e20c31ea0654db5e72e66010334ee575d3928d74e111b` |
| [`Goxxǒ` and `Acugôno` on the same line](glyph-samples/bnf-f0248-caron-circumflex-same-line.jpg) | `f0248.jpg`, `[300, 1310, 1020, 1570]` | `80ea87e3842cbf6efca29bf7805efec21247a6bd4c9c7709505a252ba49a4f71` |
| [`Goyô`](glyph-samples/bnf-f0248-circumflex-goyo.jpg) | `f0248.jpg`, `[300, 1930, 1000, 2360]` | `57341dd942f652936c9627fb056af97af9b2b034835f7ccb037d520ccdd1097a` |
| [`Gǔcon`](glyph-samples/bnf-f0248-caron-gucan.jpg) | `f0248.jpg`, `[1360, 2546, 2010, 2846]` | `3df14d3dd88b1f70042eb889dc7d8c1c55276634908fe4acda1ba59f9066ec10` |
| [`acõpanha`](glyph-samples/bnf-f0248-tilde-acompanha.jpg) | `f0248.jpg`, `[1360, 1920, 2260, 2220]` | `aab46d08fdf64e584ff27eb6f4a47a5a0894ae60789fbcb248a07cfdd7c784be` |
| [`Zzubôxi`](glyph-samples/bnf-f0643-circumflex-zzuboxi.jpg) | `f0643.jpg`, `[150, 430, 1050, 730]` | `72647bae253b5f3806174c693c09d13303f85e6cc9d06f28558b96947b259a37` |
| [`Ienxùs`](glyph-samples/bnf-f0643-grave-ienxus.jpg) | `f0643.jpg`, `[350, 1500, 1100, 1730]` | `b283310d2e62047840862c8ffcadbb5c31572024476397b0f94141f81cf6d38b` |
| [`Zzufǔ`, `Zzujǒ`](glyph-samples/bnf-f0643-caron-zzufu-zzujo.jpg) | `f0643.jpg`, `[150, 1870, 1050, 2270]` | `167786dd72c6874ad59daca83aba8d74a05c756b4f423c4f0369f7f35f87b7a4` |

## Editorial consequence

The frozen drafts remain unchanged as historical checkpoints. A reviewed or migrated transcription must apply the occurrence-level results above, not a global `ô`/`û` replacement. The wider representative sample must still be checked for carons and circumflexes over other vowels, additional long-*u* marks, and degraded examples before the inventory becomes a version 1 rule.
