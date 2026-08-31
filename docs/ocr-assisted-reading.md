# Provisional OCR-Assisted Reading Policy

## Status and scope

This policy describes how the book-specific OCR engine may improve the
transcriber's **pre-human default reading** without replacing scan-led Level 1
work. Its first calibration source is the human-corrected `f151` transcription
at commit `64fcba7`, compared with the stored outputs of one TrOCR checkpoint
applied to ordinary rectangular lines and independently segmented,
Kraken-rectified lines. The two outputs test sensitivity to geometry; they are
not independent model votes.

The f151 sample is too small to establish permanent volume-wide error rates.
Every later human-reviewed page should extend the same occurrence-level
comparison. A feature rule remains provisional until it survives varied pages,
typefaces, letters, and scan conditions.

## Governing principle

OCR should not replace a physical line wholesale. Align each OCR output with a
scan-led visual draft and extract only local evidence for a particular printed
choice. Let that evidence improve the transcriber's initial decision when the
surrounding word or line is sufficiently well recognized; discard an isolated
character claim taken from otherwise garbled output.

The source image remains authoritative. OCR changes the order in which the
transcriber investigates plausible readings, not what Level 1 is allowed to
record. Later explicit human scan confirmation supersedes every machine
preference.

## Shared geometry, separate renderings

Each stable physical-line ID should ultimately have one verified source-image
geometry. Derive two purpose-specific renderings from it:

- the human view includes generous vertical context and the right column rule,
  or an equivalent outer boundary, so terminal ink and the absence of a
  division mark are independently visible;
- the OCR view retains all terminal ink and a small blank margin but excludes
  the rule and rectifies the baseline where useful.

Record a geometry version or hash with OCR output. A changed physical-line
region invalidates only the affected recognition. Do not maintain unrelated UI
and OCR notions of which source row belongs to a line.

## Initial f151 calibration

The figures below compare 94 body lines with the transcription after human
Issue 158. “Conditional choice” means that OCR emitted one of the members of
the named alternative set at the aligned source position; it excludes a
missing or otherwise garbled character.

| Feature | f151 evidence | Provisional use |
| --- | --- | --- |
| line-final division mark | rectangular 92/94 binary decisions correct; rectified 93/94; both found 15 of 16 printed marks | Prefer OCR when verified geometry contains the complete right edge. Flag route disagreement or clipped geometry. |
| spaces | 389/392 preserved by rectangular crops; 385/392 by rectified crops | Prefer OCR for a local join or division when the neighbouring letters align. Do not import spaces from a garbled word. |
| period / comma | 205/214 exact for each route; 5 further instances chose the other member | Strong diagnostic evidence under clean local alignment, but inspect disputed punctuation. |
| short `s` / long `ſ` | 79/92 exact in rectangular crops; 83/92 in rectified crops; no direct `s`/`ſ` reversal among aligned `s`-type outputs | Prefer the OCR allograph when the containing word aligns. Ignore added `ſ` inside garbled output. In headwords, this evidence outranks normalized NINJAL spelling. |
| `q` / `g` | 81/86 and 78/86 exact overall; conditional choice 98.8% and 100% | Prefer a clean local OCR choice; use disagreement to force enlargement. |
| `u` / `v` | 125/142 and 127/142 exact; no conditional reversal | Prefer a clean local OCR choice. |
| `i` / `j` | 192/217 and 203/217 exact; conditional choice 100% and 98.1% | Prefer a clean local OCR choice. |
| capitalization | 171/180 and 175/180 exact on printed capitals | Useful secondary evidence when the rest of the word aligns. |
| ampersand | 8/8 in both routes | Retain as promising evidence, but do not generalize from this small count alone. |
| `c` / `ç` | 58/71 and 60/71 exact; conditional choice 96.7% and 95.2% | Generate a reinspection candidate; do not make it a default replacement yet. |
| `n` / `m` | 176/216 exact in both routes; conditional choice 93.1% and 94.1% | Generate a reinspection candidate only. |
| marked `o` (`ô`, `ǒ`, and related forms) | only 28/48 and 26/48 exact overall; a separate held-out character N-gram experiment chose `ô` versus `ǒ` correctly in 43/46 cases | Do not let OCR infer the presence of a mark. Once a mark is visually established, use the N-gram score as linguistic evidence and enlarge low-margin cases. |
| tilde presence or carrier | `quẽtura`, `dizẽ`, and `feijoẽs` were lost or materially misread | Do not let line OCR decide tilde placement. Use it only to raise a possible-mark flag. |
| pilcrow | 6/7 and 5/7 exact, with additional false detections | Retain the scan-led reading. |
| roman / italic type | not represented by the recognizer | OCR supplies no evidence. |

These rates measure one out-of-range page after human correction. They do not
license blind substitution. In particular, the strong repeated `Vôqina`
result does not contradict the poor page-wide marked-`o` rate: recurrence is
part of the evidence.

The [marked-`o` character N-gram experiment](o-mark-ngram.md) separates two
questions that line OCR had conflated. Vision must first establish that a mark
exists; conditional on that fact, the selected 2-gram language model chose
`ô` versus `ǒ` in 43/46 held-out f151 occurrences and got all 20 members of the
`Vôqina`/`Vôyubi` family correct. Its confidence cutoff is not yet independently
validated, so the score currently changes review priority rather than silently
changing Level 1.

## Evidence-fusion procedure

For each prepared page:

1. Verify the common physical-line geometry and render both line variants.
2. Produce the transcriber's visual draft and both OCR strings without using
   an external running-text transcription as diplomatic authority.
3. Align each OCR string to the draft. Treat the two crop results as a geometry
   stability check, not two independent recognizers.
4. Extract atomic alternatives only where the surrounding token or line is
   recognizable. Record the line ID, geometry version, feature, OCR proposal,
   and which rendering supported it.
5. Apply the feature-specific priorities above to the **default reading**.
   Disagreement, low local alignment, or a weak feature becomes an explicit
   enlargement prompt rather than an automatic change.
6. Cluster repeated equivalent disagreements across the page. A stable
   recurring pattern may outweigh a mistaken existing transcription even when
   isolated instances of that feature are unreliable.
7. Complete the ordinary Japanese, Portuguese, bilingual, glyph, edge, and
   scan-confirmation passes. OCR does not replace any of them.

NINJAL headword data remains useful for entry coverage and location. Its
normalized spelling must not override a clean OCR allograph or the scan. The
f151 sequence `Daisô`, `Daisocu`, `Daisôjǒ`, `Daison`, and `Daisu` demonstrates
how normalized short `s` can reinforce an anchored machine reading even though
the print and locally aligned OCR support `Daiſ-`.

## Learning from later human review

Preserve OCR output and its geometry version until the page's human correction
Issue has been applied. Then compare the pre-human machine evidence with the
new canonical text and append occurrence counts by feature and context. At a
minimum, distinguish upright Japanese/headword text from italic Portuguese,
line-final position from internal punctuation, and `st` from other `s`/`ſ`
contexts.

Update a default only from accumulated human-confirmed outcomes. Preserve both
successes and false positives: a feature that finds genuine corrections but
also creates speculative churn should remain a review prompt rather than an
automatic preference.
