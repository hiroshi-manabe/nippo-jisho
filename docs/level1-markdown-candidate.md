# Level 1 Markdown Format, Version 1

## Status and priority

This is the adopted human-authoring format for Level 1 diplomatic transcription. Adoption follows a six-page, 526-line corpus test and a timed two-page production simulation on previously untranscribed consecutive pages.

The design priority is faithful, readable, and efficient Level 1 work. Later structural layers are a secondary compatibility concern: Level 1 retains stable references and does not discard visible evidence, but ordinary transcription is not made more complex merely to anticipate a complete Level 2 schema.

Level 1 may be read with the full help of historical Japanese, Jesuit romanization, and Portuguese context. Those perspectives belong in later review passes and can identify a likely visual error, but every resulting correction must be confirmed against the scan. What remains outside Level 1 is the added analysis—morpheme boundaries, normalized Japanese, grammatical interpretation, and translation—not the knowledge used to read the type.

## Source of truth and generated data

Human editors work in `pilot/format-v1-trial/level1-source/*.md`. The compiler validates these files and generates `level1/*.json` for machine interchange and the existing page renderer. The JSON is not edited independently.

Run from the repository root:

```sh
python3 scripts/compile_level1_markdown.py compile \
  pilot/format-v1-trial/level1-source \
  pilot/format-v1-trial/level1
```

Use `--check` to verify that committed JSON is current without rewriting it.

## Example

```markdown
---
format: nippo-level1-markdown
version: 1
id: bnf-f0248
source: BnF Gallica
view: f248
url: https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f248.item
sha256: 013dfec07420703620440be7d1d7e5ac07ba8327e4d21ea78217904949793aa8
scope: full_dictionary_text_and_furniture
origin: direct_from_scan
wikisource: false
lineation: checked
status: scan_confirmed
---

## column-1 [column] Column 1

[c1-l021] Gǒyen. Tçuyoi yen. *Grande, & poderoſa*
[c1-l022 >] *amizade. Vt,* Gǒyẽuo motte tanomu.
...
[c1-l037 >] *gũ ſenhor principal.* || {mark} *(* || {word}*grande.*
[c1-l038] Gozadocoro. *Lugar onde eſtá algum ſenhor*
```

The file is ordinary Markdown except for a small line-prefix and placement vocabulary.

## Minimal syntax

| Form | Meaning |
| --- | --- |
| `## zone-id [kind] Label` | Begin a physical page zone. |
| `> Note` | Attach a non-transcribed note to the current zone. |
| `[c1-l001] text` | Record one physical line with a stable ID. |
| `[c1-l002 >] text` | Record relative indentation level 1. |
| `[catch-l001 >>] text` | Place the whole line at the far right. |
| `*text*` | Printed italic type. Roman is the default. |
| `**text**` | Printed display type. |
| `main || far right` | Put the following segment at the far right of the same physical line. |
| `{word}text` | Give an exceptional far-right segment a local stable name. |

Zone kinds and metadata values are explicit strings rather than hidden filename conventions. Blank lines are for readability and have no documentary meaning.

## What remains explicit

The compact form retains:

- canonical source URL and master-image checksum;
- review provenance and page scope;
- physical page zones and their order;
- stable physical-line identifiers;
- visible text in physical order;
- roman, italic, and display type;
- relative indentation;
- exceptional far-right placement;
- optional named spans only where a smaller stable target is actually needed;
- non-textual notes for ornaments, later stamps, and similar copy features.

It does not encode entry boundaries, normalize abbreviations, join divided words, reassign displaced text, or translate the source.

The `status` field records review maturity:

- `visual_draft`: the initial scan-derived transcription and physical lineation exist;
- `context_reviewed`: Japanese/romanization and Portuguese-context passes are complete;
- `scan_confirmed`: all flags have been adjudicated and a final complete scan sweep is complete.

The legacy `trial_reviewed` value is accepted only for existing pilot pages whose earlier history does not map cleanly onto these production states. New work must use the production vocabulary. The procedure is maintained in the [Provisional Transcription Reading Guide](transcription-reading-guide.md#review-passes).

## Exceptional spans and later compatibility

Named spans are optional and should remain rare. The six-page adoption corpus needs them only for the physical `(grande.` and `(o homem.` cases:

```markdown
[c1-l037 >] *gũ ſenhor principal.* || {mark} *(* || {word}*grande.*
```

This preserves the mark and displaced word independently without asserting their meaning. The existing compatibility check can refer to `c1-l037@mark` or `c1-l037@word`, but such later use is not the reason ordinary lines carry IDs.

The production simulation reused the same syntax without modification:

```markdown
[c2-l028 >] *guerra.* || {mark} *(* || {word}*o homem.*
```

The working rule is: preserve what a later layer may need, but postpone deciding what that layer will mean.

## Deliberate limits

- Exact compositor spacing remains available in the scan; the transcription records word separation, indentation level, and exceptional placement rather than pixel geometry.
- Literal asterisks and the literal delimiter ` || ` have not yet occurred in the sample. An escaping convention must be defined if the wider corpus contains them.
- The current files contain no reading that remains materially unresolved after enlargement and contextual review. A lightweight uncertainty notation will be added in a compatible revision only when a real case requires it.
- The compiler supports the indentation and placement patterns observed in the six-page adoption corpus. New syntax should be added from evidence, not pre-emptively.

## Evaluation criterion

The format was adopted because editors can read and correct the Markdown directly, regenerate identical validated page data, and preserve all evidence needed for later re-evaluation. Full entry extraction and continuous-text modelling remain outside Level 1 requirements; only a small compatibility check is retained to guard against obvious information loss.

Across the six-page adoption corpus, the human-authored files occupy 724 lines and 29,594 bytes. Their generated pretty-printed JSON occupies 6,926 lines and 155,958 bytes. Size alone is not an adoption criterion, but the reduction reflects how much repetitive machine syntax editors no longer have to navigate. The decisive production evidence is recorded in the [f249–f250 simulation](../pilot/production-simulation/f0249-f0250.md).
