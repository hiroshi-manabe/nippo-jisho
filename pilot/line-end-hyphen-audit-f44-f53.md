# Line-end division-mark audit: f44–f53

Date: 2026-08-16

## Purpose

This ten-page trial tests whether a dedicated scan pass can reliably distinguish visibly printed line-end division marks from hyphens inferred merely because a word continues on the following physical line. It is independent of the roman-Japanese typeface audit on the same pages.

## Method

- Scope: every dictionary-text line on f44–f53, 936 physical lines in all.
- Primary evidence: the locally cached full-resolution Gallica scans.
- First pass: inspect each complete line crop, paying particular attention to both column edges.
- Adjudication: enlarge the right edge whenever the presence or absence of a mark is not immediately clear. Lexical continuation was used to locate candidates, never to supply a mark.
- Control: retain `-` only where the scan shows a printed division sign, including the equals-like italic form already encoded as `-` by the Level 1 convention.
- Geometry fallback: several f49 column-2 contact crops were vertically mislabelled, so those endings were checked directly in a larger full-page crop rather than accepted from the line UI.

## Results

The existing transcription contained 191 candidate terminal division marks. The scan audit removed 15 unsupported marks, retained 176 visibly printed marks, and found no omitted printed mark.

| Page | Line | Before | After | Scan finding |
| --- | --- | --- | --- | --- |
| f44 | c2-l021 | `Dar par-` | `Dar par` | blank after `r` |
| f47 | c1a-l002 | `Gojǒni azzu-` | `Gojǒni azzu` | blank after `u` |
| f47 | c1b-l002 | `Matoba. Lu-` | `Matoba. Lu` | blank after `u` |
| f47 | c1b-l003 | `Ichi-` | `Ichi` | blank after `i` |
| f48 | c2-l037 | `poſtu-` | `poſtu` | blank after `u` |
| f48 | c2-l042 | `mer-` | `mer` | blank after `r` |
| f49 | c2-l001 | `Tabolei-` | `Tabolei` | blank after `i` |
| f49 | c2-l002 | `Tabolei-` | `Tabolei` | blank after `i` |
| f49 | c2-l004 | `Tabolei-` | `Tabolei` | blank after `i` |
| f49 | c2-l006 | `Ba-` | `Ba` | blank after `a` |
| f50 | c1-l041 | `Ro-` | `Ro` | blank after `o` |
| f52 | c1-l043 | `paſſa-` | `paſſa` | blank after `a` |
| f53 | c2-l011 | `ben-` | `ben` | blank after `n` |
| f53 | c2-l016 | `Ben-` | `Ben` | blank after `n` |
| f53 | c2-l019 | `co-` | `co` | blank after `o` |

All corrections are removals of inferred marks. Repeated or linguistically obvious continuations were a particular source of false positives: the three `Tabolei` lines on f49 demonstrate that even identical continuation structure does not license a printed mark. Conversely, many nearby roman and italic endings do contain clearly visible division signs and were retained.

## Assessment

The dedicated pass added material value: it corrected 15 of 191 previously recorded candidate marks (7.9%) without proposing a speculative addition. The result is promising enough to use the same scan-first audit on further unchecked pages. It does not prove complete recall, especially for faint marks, so the first larger batch should still receive a human spot-check before this becomes a fully delegated specialist pass.
