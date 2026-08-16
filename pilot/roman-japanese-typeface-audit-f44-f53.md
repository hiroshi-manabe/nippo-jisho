# Roman Japanese inside Portuguese: f44–f53 benchmark

## Purpose and scope

This is a deliberately narrow pre-human benchmark of whether machine review can recover Japanese expressions whose upright roman type was mistakenly enclosed in Markdown italics with the surrounding Portuguese explanation. It covers `bnf-f0044` through `bnf-f0053`, the next ten transcribed pages without a human correction-Issue review when the pass began.

The pass inspected the scans rather than changing typeface from vocabulary alone. Candidate discovery combined known Japanese forms, mixed-language transitions, cross-references, dialect labels, short forms, and words split across physical lines. Every applied change was then checked against the corresponding Gallica master. Text, spacing, punctuation, and physical line division were not changed.

## Applied corrections

| Page | Physical line(s) | Japanese restored to roman type |
| --- | --- | --- |
| f44 | `c1-l023` | `Xintô` |
| f44 | `c2-l008` | `Faxira` |
| f44 | `c2-l009` | `Tega-` |
| f45 | `c2-l045` | `Ximo` |
| f46 | `c1a-l008` | `Miſo` |
| f46 | `c1a-l010` | `Namaſu` |
| f46 | `c1a-l012` | `Namaſu`, `Ximo` |
| f46 | `c2-l007` | `Cauago` |
| f46 | `c2-l008` | `Ayemono` |
| f47 | `c2-l046` | `Macuno xita` |
| f48 | `c2-l026` | `Baxen` |
| f49 | `c2-l005` | `Go` |
| f49 | `c2-l013` | `Banaraxi` |
| f49 | `c2-l030` | `Cha` |
| f50 | `c1-l028` | `Ximo` |
| f50 | `c2-l009` | `Cami` |
| f51 | `c1-l006`–`c1-l007` | `Cha-` / `noyu` |
| f52 | `c1-l020` | `Barabara` |
| f52 | `c1-l035` | `Chanoyu` |
| f52 | `c2-l009` | `Xitauo nuqu` |
| f53 | `c1b-l026` | `Cha` |
| f53 | `c1b-l028` | `Vono fito` |

The result is 23 corrected physical lines containing 23 lexical spans (with two spans on `f46/c1a-l012`, balanced by one `Chanoyu` span divided across two lines on f51).

## Negative controls and limits

Referential meaning alone does not make a word Japanese typography. Portuguese forms such as italic `Iapão`, `China`, and `Rei` were left italic after scan inspection. Likewise, `f52/c2-l022` retains italic `zaxiqi`: it is Japanese lexically, but the enlarged types appear italic, so the diplomatic transcription must preserve that local exception.

This pass found cases that a simple dictionary lookup would miss: the two-word phrases `Macuno xita`, `Xitauo nuqu`, and `Vono fito`; the very short `Go`; and `Chanoyu` divided across a line break. It is therefore a coverage benchmark awaiting human review, not evidence that an automatic lexical replacement is complete or safe.

