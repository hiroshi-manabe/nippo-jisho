# Adjacent-Vowel Tilde-Carrier Audit

## Result

The not-yet-human-reviewed Level 1 pages contain **3,853 tilde-bearing vowel occurrences adjacent to another vowel**, on **3,443 physical lines across 203 pages**. The already completed `nhaã` / `nhãa` family was deliberately excluded from this pass. This inventory remains useful, but the original contact-sheet adjudication did **not** establish an individual scan confirmation for every occurrence.

The machine review found two cases in which the transcription had regularized a locally printed final `aõ` to the much commoner `ão`:

- `bnf-f0043:c1-l033`: `abanão` → `abanaõ`
- `bnf-f0124:c1-l001`: `Pião` → `Piaõ`

Subsequent tight human inspection disproved the bulk confirmation at `bnf-f0039:c2-l019`, correcting `mãos` to printed `maõs` through Issue #27. A second spot check at `bnf-f0040:c2-l009` likewise found printed `dalgũa` rather than the inventoried `dalguã`; Issue #28 then confirmed that correction along with printed `muniçoẽs`, `algũa`, `naõ`, and newly recovered `quẽte` on the same page. Issue #29 individually confirmed ten further carrier corrections on f41, including nine tilde-over-`o` forms and `algũa` at `c2-l036`. Issues #30 and #31 confirmed f42 `algũas`, `maõs`, `feiçoẽs`, and a distinct printed `alguã` at `c2-l033`. Issue #32 then confirmed five f43 carriers: `graõs`, `botaõ`, `abanão`, `dalgũa`, and `algũa`; notably, `abanão` reverses the earlier machine-only reading `abanaõ`. The failure was not crop localization: the correct word image was present, but grouping by the existing carrier, labels that displayed the existing reading, dense 32-item sheets, and escalation based on OCR-location confidence all encouraged confirmation rather than an explicit carrier decision.

Accordingly, unchanged rows are now marked `batch_review_unverified`, not `scan_confirmed`. The remaining machine-found correction has status `machine_scan_corrected`, while individually adjudicated f39–f43 corrections and the scan-confirmed f100 reading `trauão` have status `human_scan_confirmed`. The current ledger has 2,587 marks on `a`, 1,013 on `u`, 166 on `o`, 83 on `e`, and 4 on `i`; these are inventory totals, not verified distributions or spelling rules.

The occurrence ledger is [adjacent-vowel-tilde-audit.tsv](adjacent-vowel-tilde-audit.tsv). It records the page, physical line, occurrence number, token, marked-vowel context, carrier, and review status. A row may be treated as individually adjudicated only when its status explicitly says so.

## Scope

The audited pages are the canonical Level 1 files from `bnf-f0039` onward that had not yet received line-by-line human transcription review: `f39`–`f237`, the three trial pages `f248`–`f250`, and `f643`. Earlier human-reviewed pages were not re-audited here. Tokens containing either `nhaã` or `nhãa` were excluded because that family already has a separate [64-occurrence audit](nhaa-position-audit.md).

This pass includes all other adjacent-vowel contexts, not only Portuguese word endings: for example `ão`, `õe`, `ũa`, `uã`, `uẽ`, `aã`, `ĩa`, and their capitalized, plural, contracted, or Japanese-romanization contexts.

## Method

1. Inventory every NFC tilde-bearing vowel (`ã`, `õ`, `ũ`, `ẽ`, or `ĩ`) that directly neighbors another vowel in the canonical Markdown.
2. Recover its physical line from the native-resolution local Gallica master using the reviewed line geometry.
3. Use OCR only to locate likely ink. It is never evidence for which vowel carries the mark.
4. The first pass inspected enlarged word crops grouped by the existing vowel context. If localization was weak, repeated, or absent, it inspected a complete enlarged line.
5. This presentation proved insufficient for carrier adjudication: future review must hide the existing carrier classification, enlarge one word at a time, and require an explicit `a`, `e`, `i`, `o`, `u`, or `uncertain` decision before recording confirmation.
6. Rebuild the derived transcription and review-site data from the corrected Level 1 source.

The retained corrections demonstrate why a lexical rule is unsafe: even a familiar-looking final nasal sequence may be set `aõ` in one occurrence and `ão` elsewhere. The invalidated bulk result also demonstrates that a correctly localized crop is not itself a reading. Historical expectation is useful for finding a suspicious form, but only an explicit inspection of the local printed sort establishes the carrier.

## Reproduction

Run `scripts/build_adjacent_tilde_audit.py` to rebuild the occurrence inventory and optional compact or full-line review sheets. Its OCR-assisted locator is useful for finding the word but must not be interpreted as carrier evidence. The checked-in statuses preserve the distinction between the superseded batch review and later individual adjudication.
