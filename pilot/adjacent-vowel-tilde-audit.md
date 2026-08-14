# Adjacent-Vowel Tilde-Carrier Audit

## Result

The not-yet-human-reviewed Level 1 pages contained **3,852 tilde-bearing vowel occurrences adjacent to another vowel**, on **3,443 physical lines across 203 pages**. Every occurrence was checked against the Gallica scan as an individual typographic setting. The already completed `nhaã` / `nhãa` family was deliberately excluded from this pass.

The review corrected two cases in which the transcription had regularized a locally printed final `aõ` to the much commoner `ão`:

- `bnf-f0043:c1-l033`: `abanão` → `abanaõ`
- `bnf-f0124:c1-l001`: `Pião` → `Piaõ`

The other 3,850 occurrences retain their existing carrier. The corrected corpus has 2,605 audited marks on `a`, 1,008 on `u`, 155 on `o`, 80 on `e`, and 4 on `i`. These totals describe this audit scope only; they are not spelling rules.

The occurrence ledger is [adjacent-vowel-tilde-audit.tsv](adjacent-vowel-tilde-audit.tsv). It records the page, physical line, occurrence number, token, marked-vowel context, carrier, and review status.

## Scope

The audited pages are the canonical Level 1 files from `bnf-f0039` onward that had not yet received line-by-line human transcription review: `f39`–`f237`, the three trial pages `f248`–`f250`, and `f643`. Earlier human-reviewed pages were not re-audited here. Tokens containing either `nhaã` or `nhãa` were excluded because that family already has a separate [64-occurrence audit](nhaa-position-audit.md).

This pass includes all other adjacent-vowel contexts, not only Portuguese word endings: for example `ão`, `õe`, `ũa`, `uã`, `uẽ`, `aã`, `ĩa`, and their capitalized, plural, contracted, or Japanese-romanization contexts.

## Method

1. Inventory every NFC tilde-bearing vowel (`ã`, `õ`, `ũ`, `ẽ`, or `ĩ`) that directly neighbors another vowel in the canonical Markdown.
2. Recover its physical line from the native-resolution local Gallica master using the reviewed line geometry.
3. Use OCR only to locate likely ink. It is never evidence for which vowel carries the mark.
4. Inspect enlarged word crops grouped by vowel context. If localization is weak, repeated, or absent, inspect a complete enlarged line instead of accepting the crop.
5. Decide the carrier occurrence by occurrence and record the result in the ledger before changing canonical text.
6. Rebuild the derived transcription and review-site data from the corrected Level 1 source.

The two corrections demonstrate why a lexical rule is unsafe: even a familiar-looking final nasal sequence may be set `aõ` in one occurrence and `ão` elsewhere. Historical expectation is useful for finding a suspicious reading, but the local printed sort remains authoritative.

## Reproduction

Run `scripts/build_adjacent_tilde_audit.py` to rebuild the occurrence inventory and optional compact or full-line review sheets. Its OCR-assisted locator is intentionally separated from the visual adjudication represented by the checked-in ledger.
