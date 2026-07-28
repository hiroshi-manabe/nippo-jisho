# Independent Draft Log

## 2026-07-28 — Format version 0

### Method

- Inspected page images rendered from the Wikimedia Commons mirror of the Gallica scan.
- Read the selected text directly from the images without OCR.
- Did not consult Wikisource for the three frozen draft files.
- Preserved uncertain readings in notes instead of resolving them from another transcription.
- Used high-resolution page renders for the drafted pages and lower-resolution renders for the wider feature survey.
- After adopting Gallica identifiers, visually verified the three drafted page mappings against Gallica `f14`, `f248`, and `f643`. Future pilot image acquisition will use Gallica’s IIIF service directly.

### Output

| Page | Scope | Visual passes | State |
| --- | --- | ---: | --- |
| `bnf-f0014` | Selected zones | 1 | Independent draft frozen |
| `bnf-f0248` | Full lexical text | 1 | Independent draft frozen |
| `bnf-f0643` | Full lexical text and furniture | 1 | Independent draft frozen |

The frozen files remain unchanged. A timed second visual pass of `bnf-f0248`, performed with native Gallica tiles and without Wikisource, is recorded separately in [bnf-f0248 Second Visual Pass](second-pass/bnf-f0248.md).

### Timing limitation

Elapsed transcription time was not measured reliably during this first format experiment, so these files could not provide a timing baseline for the later Wikisource comparison. The completed comparison was therefore treated as qualitative evidence only and made no claim about time saved. Any future timing experiment must measure image preparation, first-pass transcription, and visual self-check separately.

This limitation does not affect comparison of readings or format coverage, but it prevents a defensible claim about time saved.

### Known limitations

- Physical lineation is approximated and has not been certified line by line.
- Each file has received only one visual pass.
- The markup vocabulary is experimental and has no version 1 specification yet.
- No continuous-text or entry-reference output has been generated.
- The opening page is not eligible for blinded comparison because its Wikisource text had been seen previously.
