# Roman Japanese inside Portuguese: f54–f237 pre-human audit

## Purpose and scope

This pass extends the [f44–f53 benchmark](roman-japanese-typeface-audit-f44-f53.md) across every prepared Level 1 page that had not yet received human line-by-line review when the audit began: `bnf-f0054` through `bnf-f0237`, 184 pages in all. Its single purpose is to restore printed upright roman type where Japanese expressions had been absorbed into the Markdown italics used for the surrounding Portuguese explanation.

The scan remains authoritative. Candidate discovery used the validated benchmark vocabulary, mixed-language boundaries, cross-references, dialect labels, names, short forms, and words divided across physical lines. Candidates were inspected in scan contact sheets, followed by dedicated passes for continuation fragments, names and titles, and formulae such as `No Cami ſe diz` and `Vide`. Text, spelling, punctuation, capitalization, spacing, line division, and geometry were not intentionally changed.

## Result

The audit restores roman type on 765 physical lines in 171 pages. Those line changes contain 819 distinct italic-to-roman runs and 6,003 affected characters. Thirteen pages required no change: f64, f86, f110, f118, f131, f139, f152, f172, f186, f188, f200, f201, and f222.

The largest clusters occur where the explanations repeatedly cite Buddhist terms and names. The pass also recovered cases that a token-only method misses, including divided forms such as `Fo-` / `toqe`, `Bô-` / `zos`, `Ca-` / `tana`, and `Fu-` / `ne`; short forms such as `Va`, `Vni`, and `Xit`; multiword expressions such as `tanxǒno caua`; and names or titles such as `Amida`, `Miyaco`, `Xingojǔ`, `Yamibuxi`, and `Gioſag`.

## Negative controls and limits

Language supplied candidates but did not determine typeface by itself. The audit retained 118 candidate occurrences that the scan and linguistic context support as italic Portuguese words or fragments despite lexical overlap with Japanese forms. These include complete words such as Portuguese `go`, `caua`, `fita`, `Cano`, `Vaca`, and `Sono`, as well as misleading divided-word fragments such as `cami-` in *caminho*, `cha-` in *chamada*, `coto-` in *cotovelo*, and `Nomi-` in *Nominatiuo*. Labels such as italic `Bup`, and Portuguese geographical or ethnonymic forms such as `Iapão`, remain italic where printed that way. The earlier benchmark's locally italic `zaxiqi` likewise remains unchanged.

This is a high-coverage machine pre-review, not a declaration that these pages are human-checked. Typeface distinctions can be unusually subtle, line crops can omit a divided continuation, and a lexically Japanese word can exceptionally be printed in italic. Later human review should therefore treat these corrections as scan-supported working data and may override them occurrence by occurrence.

## Verification

After the edits, every changed physical line was compared mechanically with its pre-audit form after removing Markdown typeface delimiters. All 765 pairs contain identical documentary text; only run boundaries differ. The complete Level 1 source compiles successfully to all 229 prepared compact records.
