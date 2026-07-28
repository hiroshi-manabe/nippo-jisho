# Pilot Diacritic Audit

## Scope

This audit checks vowel marks in the three frozen pilot transcriptions directly against the native-resolution Gallica images. It does not claim to inventory the complete dictionary. Wikisource, OCR, and modern editions were not consulted.

The audit was prompted by the recognition that the mark above `u` in `Gǔcan` is a caron (háček), not the tilde or circumflex recorded in earlier passes.

## Result

The downward-pointing wedge is consistently distinct from the book’s wavy tilde. In the audited passages:

| Printed mark | Diplomatic character | Unicode | Confirmed examples | Treatment |
| --- | --- | --- | --- | --- |
| Caron above `o` | `ǒ` | U+01D2, LATIN SMALL LETTER O WITH CARON | `Goxǒ`, `Zzubǒxi`, `Zzujǒ` | Preserve as precomposed `ǒ` in NFC text. |
| Caron above `u` | `ǔ` | U+01D4, LATIN SMALL LETTER U WITH CARON | `Gǔcan`, `Zzufǔ`, `Zzurçǔ` | Preserve as precomposed `ǔ` in NFC text. |
| Tilde above a vowel | for example `õ`, `ũ` | Precomposed where available | `acõpanha`, `algũa` | Preserve as a tilde; do not confuse its wavy form with the pointed caron. |
| Tilde used as an abbreviation mark | for example `q̃` | Base letter plus U+0303 | `q̃ eſtá` | Preserve with a combining tilde when no precomposed character exists. |

Unicode’s character database names `ǒ` and `ǔ` as “LATIN SMALL LETTER O WITH CARON” and “LATIN SMALL LETTER U WITH CARON.” The audit therefore uses those characters rather than a visually approximate circumflex or tilde: [UnicodeData.txt](https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt).

No genuine circumflex was confirmed among the vowel marks examined in these pilot passages. This is a scoped finding, not evidence that the complete volume contains no circumflexes.

## Previously misclassified forms

### `bnf-f0248`

The frozen lexical text contains 28 instances encoded as `ô` or `û`. Direct comparison shows the caron in each case. The unique affected forms are:

```text
Acugôno     → Acugǒno
Conjô       → Conjǒ
Cubô        → Cubǒ
Dôgu        → Dǒgu
Goxxô       → Goxxǒ
Goxô        → Goxǒ
Goxôuo      → Goxǒuo
Goyô        → Goyǒ
Goyôno      → Goyǒno
Gozô        → Gozǒ
Gozôroppu   → Gozǒroppu
Gôyei       → Gǒyei
Gôyeiuo     → Gǒyeiuo
Gûcan       → Gǔcan
afô         → afǒ
cannozô     → cannozǒ
dôgu        → dǒgu
fainozô     → fainozǒ
finozô      → finozǒ
goxô        → goxǒ
jinnozô     → jinnozǒ
tarôta      → tarǒta
xinnozô     → xinnozǒ
```

The separate correction `Goxô.` → `Goxo.` remains valid for the third `Goxo` entry: that particular printed headword has no mark at all.

### `bnf-f0643`

The frozen lexical text contains nine instances encoded as `ô` or `û`. Direct comparison shows the caron in each case:

```text
Ienxûs     → Ienxǔs
Zzubôxi    → Zzubǒxi
Zzuchô     → Zzuchǒ
Zzufû      → Zzufǔ
Zzufûga    → Zzufǔga
Zzujô      → Zzujǒ
Zzuqijô    → Zzuqijǒ
Zzurçû     → Zzurçǔ
zzuchô     → zzuchǒ
```

### `bnf-f0014`

The drafted excerpts contain no character previously encoded as `ô` or `û`. Their visible vowel tildes remain classified as tildes.

## Representative image evidence

These small crops are derived without enhancement from the cached Gallica masters. Coordinates use `[left, top, right, bottom]` pixels in the corresponding source image.

| Evidence | Master and crop box | SHA-256 |
| --- | --- | --- |
| [`Goxǒ`](glyph-samples/bnf-f0248-caron-goxo.jpg) | `f0248.jpg`, `[300, 756, 950, 1076]` | `a7914efb8e3278aa7b0e20c31ea0654db5e72e66010334ee575d3928d74e111b` |
| [`Gǔcan`](glyph-samples/bnf-f0248-caron-gucan.jpg) | `f0248.jpg`, `[1360, 2546, 2010, 2846]` | `3df14d3dd88b1f70042eb889dc7d8c1c55276634908fe4acda1ba59f9066ec10` |
| [`acõpanha`](glyph-samples/bnf-f0248-tilde-acompanha.jpg) | `f0248.jpg`, `[1360, 1920, 2260, 2220]` | `aab46d08fdf64e584ff27eb6f4a47a5a0894ae60789fbcb248a07cfdd7c784be` |
| [`Zzufǔ`, `Zzujǒ`](glyph-samples/bnf-f0643-caron-zzufu-zzujo.jpg) | `f0643.jpg`, `[150, 1870, 1050, 2270]` | `167786dd72c6874ad59daca83aba8d74a05c756b4f423c4f0369f7f35f87b7a4` |

## Editorial consequence

The frozen drafts remain unchanged as historical checkpoints. Any reviewed or migrated transcription must replace the misclassified circumflex characters listed above with carons. Before version 1 is adopted, the broader representative sample should be checked for carons over `a`, `e`, or `i`, and for any genuine circumflex or breve that requires a separate category.
