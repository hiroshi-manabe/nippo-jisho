# Corpus-based kana converter checks

The reading guide is derived data, not a transcription authority. Test both
failure coverage and expected readings; successful conversion alone does not
prove linguistic correctness. Do not alter Level 1 to make a hint look better.

## Repeatable sweep

After building the public corpus, run:

```sh
python3 scripts/audit_kana_coverage.py --baseline-ref fb5f170
```

The default scope is Roman-type body-column material through f180 (including
irregular columns), excluding furniture and known editorial labels. The
baseline converter is read from Git; neither the source pages nor Git state
is changed. `build/kana-coverage.json` contains every changed occurrence and
remaining failure with source references. Select a different comparison commit
for later work. `--last-leaf 651 --output build/kana-coverage-all.json` checks
all currently available body pages, including machine-provisional ones.

These files are regenerable diagnostics, not permanent audit records.

## Initial sweep after fb5f170

The f13–f180 sample contains 23,342 candidate tokens across 168 pages:

| Measure | Before | After |
| --- | ---: | ---: |
| Tokens producing kana | 22,977 | 23,123 |
| Unconverted tokens | 365 | 219 |
| Mechanical coverage | 98.44% | 99.06% |

All 146 changes recover previously unconverted tokens; existing successful
outputs in this sample are unchanged. Remaining failures include Portuguese
words in Roman type, pluralized Japanese loans such as `Fotoqes`, abbreviations,
physical-line fragments, and uncertain spellings. They are not all missing
Japanese conversion rules. Do not strip endings or silently repair spellings
just to improve this percentage.

The new patterns are:

- `xx` gemination: `Bexxo` → ベッショ, `Buxxin` → ブッシン.
- Vocalic `y` before a consonant or at word end: `ytçucuximi` → イツクシミ,
  `taguy` → タグイ. Consonantal `ya`, `yǔ`, and `yô` stay intact.
- Vocalic internal `j` after a vowel and before a consonant: `ijta` → イイタ,
  `qijta` → キイタ, `Chijſai` → チイサイ. Ordinary `ji` remains ジ.
- Nasal `m` before `b`/`p`: `Ambai` → アンバイ, `Birampǔ` → ビランプゥ.

The accepted source contexts support these readings: e.g. `Bexxo` is glossed
as `Bechino tocoro`, while `Ambai` concerns seasoning. Vocalic `y` is also
documented in the dictionary's preliminary spelling instructions; see the
discussion in [Takemura's study](https://hdl.handle.net/11094/47013).

The broader sweep covers 89,471 tokens across 631 body pages, recovering 778
failures without changing any previously successful output. This is a
compatibility check, not validation of those provisional source texts.

## Expected-reading tests

`tests/fixtures/kana-corpus-cases.json` retains 37 source-referenced examples
as converter fixtures. These test how a specified spelling is rendered, not
whether that spelling must forever remain in the diplomatic transcription.
Additional negative tests protect ordinary y/j/m readings, unresolved fragments,
and existing doubled-consonant behavior. The older tests retain the recent
I/J, `reǒ`, `nuuo`, `cq`, and `cc` examples.

Future work should sample successful outputs too: incorrect but pronounceable
hints, lexical ambiguity, and long-vowel interpretation are invisible to the
failure count. Broaden this fixture set as human review supplies evidence.
