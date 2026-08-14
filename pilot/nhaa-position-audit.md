# `nhãa` / `nhaã` Tilde-Position Audit

## Result

The current Level 1 corpus contained **64 case-insensitive `nhãa` occurrences on 63 lines across 15 pages**. Every occurrence was inspected in an enlarged crop from the local Gallica master. In all 64 cases, the printed tilde is carried by the second `a`: `nhaã`, not `nhãa`.

The corrections cover `manhaã`, `menhaã`, `amenhaã`, `amanhaã`, compounds such as `polamanhaã`, a suffixed `polamanhaãm`, and line-initial continuations `nhaã`. One line, `bnf-f0038:c2a-l011`, contains two separately confirmed occurrences. No current occurrence was retained as `nhãa`.

The affected pages are `f32`, `f37`, `f38`, `f45`, `f56`, `f109`–`f113`, `f125`, `f126`, `f173`, `f210`, and `f236`. This is a source-level correction, not a normalization to modern Portuguese: the two printed `a` types and the mark's carrier are both preserved.

## Method

1. Inventory every case-insensitive `nhãa` sequence in the canonical Level 1 Markdown.
2. Recover each complete physical line from the native-resolution Gallica master using the reviewed line geometry.
3. Enlarge the strip to twice its native dimensions and inspect the two `a` types and tilde as separate features.
4. Make an occurrence-level decision, including repeated words and line-break continuations, before applying any replacement.
5. Rebuild the machine-readable and rendered derivatives from the corrected canonical Markdown.

The recurring word *manhã* made `nhãa` linguistically tempting and encouraged the mark to be assigned to the first `a`. The scan evidence instead shows the historical printed sequence `nhaã` throughout this audited family. This result must not be generalized silently to a different vowel sequence or future page: new occurrences remain subject to scan inspection.

