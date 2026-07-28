# Transcription-Format Pilot

## Status

This is the project’s **current phase**. It precedes production transcription and supports Stage 1 of the [Four-Stage Project Roadmap](four-stage-roadmap.md).

## Purpose

The pilot will determine how the printed pages of the *Nippo Jisho* should be represented as editable, auditable text. The format must preserve meaningful documentary evidence without attempting to recreate the scan typographically.

The pilot exists because a format designed from a single page is likely to fail when it encounters different headers, entry continuations, catchwords, damaged type, unusual abbreviations, or later sections of the dictionary. Changes are inexpensive while the sample is small and increasingly costly after sequential transcription has begun.

## Relationship to the four stages

This pilot is not a fifth publication stage. It is pre-production design for Stage 1.

It is followed by a smaller end-to-end pilot that will take selected material through entry structuring, Japanese restoration, translation, and presentation. The two pilots answer different questions:

| Pilot | Principal question |
| --- | --- |
| Transcription-format pilot | Can the source page be represented faithfully and consistently? |
| End-to-end pilot | Can that representation support all later editorial stages? |

Some pages may be shared between the pilots, but their evaluation criteria remain distinct.

## Questions to resolve

The pilot must provide evidence for decisions about:

- the authoritative unit of page transcription;
- representation of columns and physical lineation;
- running headers, section headings, catchwords, signatures, ornaments, and other page furniture;
- continuations between columns and pages;
- printed hyphenation and divided words;
- original glyphs, diacritics, ligatures, abbreviations, and spacing;
- source-specific romanization patterns and expectation-driven reading errors;
- damaged, illegible, doubtful, corrected, or anomalous print;
- stable references from later entry records back to the page;
- the boundary between hand-edited source data and generated views;
- whether a lightweight text format remains robust enough for production;
- whether existing Wikisource transcription saves sufficient work to justify reuse and its licensing consequences.

## Representative sample

Approximately 10–15 pages should be selected by feature rather than simply taking the first consecutive pages. The sample should include, where available:

- the first dictionary page with its title and ornamental initial;
- an ordinary two-column page;
- an entry continuing between columns;
- an entry continuing across a page boundary;
- complete and divided catchwords;
- repeated and changing running headers;
- dense sequences of short entries;
- a long entry containing examples and grammatical information;
- unusual characters, abbreviations, or difficult typography;
- damage, staining, weak contrast, or an uncertain reading;
- a section transition or other change in page organization;
- supplementary matter if it is intended to enter the transcription corpus;
- a page from another copy if it is needed to address a lacuna or damaged passage.

The sample list must record why each page was selected. A page may satisfy several requirements.

## Provisional representation model

The pilot begins with cumulative, linked representations:

```text
source scan
    ↓
page-oriented diplomatic transcription
    ↓
structural analysis
    ↓
generated continuous text and entry-oriented views
```

The scan remains authoritative for exact visual layout. The page transcription records observable evidence in physical order: visible characters and marks, capitalization, spacing, punctuation, typeface where significant, pages, columns, lines, indentation, and exceptional placement. It does not ordinarily decide entry boundaries, assign text to headwords or definitions, or move displaced text into a proposed logical position. Those interpretations belong to the structural layer.

The layers are cumulative rather than replacement texts. Structural records point back to transcription units and add interpretations; they do not copy and silently modify the diplomatic text. Generated views may omit repeated furniture, join continuations, or present a proposed reading order, but every transformation must remain traceable to the page transcription and ultimately to the scan.

The design criterion for Stage 1 is therefore not whether it resolves each structural question, but whether it preserves the visible evidence later editors need to resolve it. For example, the lowercase form and typeface of `aburamono` belong to the page transcription, while its identification as an independent entry belongs to Stage 2. Similarly, the parenthesis-like mark, physical line, and exceptional placement of `(grande.` belong to Stage 1, while assignment of `grande.` to the following definition belongs to Stage 2.

The initial candidate is one UTF-8 Markdown file per scan page, with machine-readable metadata and explicitly labelled page zones. This is a hypothesis to test, not yet the adopted production format.

An illustrative experiment might look like:

```markdown
---
format: nippo-page-transcription
format_version: 0
id: bnf-f0013
source: bnf-gallica
gallica_view: f13
commons_pdf_page: 15
status: draft
---

[title]
DOS VOCABVLOS

[column-1]
[001] A NOME de hũa das 47.
...

[catchword]
Abu-

[signature]
A
```

Version `0` identifies experimental files. They do not become production transcription merely because they contain transcribed text.

## Method

1. **Inventory observed features.** Inspect the selected pages and record every feature the format may need to express.
2. **Create independent prototypes.** Transcribe representative portions directly from the scans without consulting Wikisource and without prematurely designing a comprehensive markup language.
3. **Exercise difficult cases.** Test continuations, repeated furniture, catchwords, uncertainty, abbreviations, and line division.
4. **Record working observations.** Preserve potentially reusable discoveries with page evidence and a provisional status rather than turning a single example directly into a rule.
5. **Freeze the independent drafts.** Record provenance and prevent later comparison from silently changing the initial readings.
6. **Generate alternative views.** Confirm that a page-oriented view, continuous text, and preliminary entry references can be derived without maintaining conflicting copies.
7. **Complete the Wikisource experiment.** After freezing the drafts, compare the eligible overlap with Wikisource, classify every meaningful difference, and decide whether routine reuse is justified.
8. **Revise and repeat.** Apply the revised format to several difficult pages again rather than judging it only on earlier examples.
9. **Specify and migrate.** Document version 1 and either convert or discard version 0 experiments explicitly.

## Wikisource evaluation and decision

The project evaluated Wikisource's usefulness and licensing consequences only after freezing an independent scan-derived draft.

The comparison should record:

- page coverage and review status;
- omitted or duplicated text;
- character and word errors;
- handling of long *s*, diacritics, abbreviations, and spacing;
- treatment of headers, catchwords, columns, and continuations;
- time required to correct the text to project standards;
- provenance information available for each imported page.

The controlled evaluation is recorded in [Wikisource comparison: bnf-f0014](../pilot/wikisource-comparison/bnf-f0014.md). Wikisource identified useful individual corrections, but its extremely limited and unreviewed coverage cannot materially support whole-volume production. Routine use has therefore been rejected. Transcription will remain scan-first and independent, with external transcription reserved for exceptional unresolved cases and recorded with exact provenance.

The comparison also exposed recurring cognitive and visual errors. These have been converted into the [Provisional Transcription Reading Guide](transcription-reading-guide.md), which must be consulted during later pilot review.

## Required outputs

The pilot should produce:

- a representative page list with selection reasons;
- a catalogue of observed textual and physical features;
- experimental page transcriptions marked as format version 0;
- a provisional register of reusable working observations;
- a provisional source-specific transcription reading guide;
- examples of the three derived views;
- a comparison of direct and Wikisource-assisted transcription;
- a list of unresolved or deliberately unsupported cases;
- version 1 of the page-transcription specification;
- a migration note from experimental files to version 1;
- an initial provenance and licensing policy.

## Exit criteria

The project may leave this phase when:

1. The sample covers the known common features and a reasonable range of exceptional ones.
2. Difficult pages have been transcribed successfully after at least one format revision.
3. Every transcribed element can be traced to a source page and meaningful location.
4. Page furniture can be preserved without contaminating continuous dictionary text.
5. Continuations and typographical line division can be represented without silent editorial changes.
6. The page transcription supplies stable addressable units from which a separate structural layer can support continuous text and entry references without modifying or duplicating the source record.
7. Uncertainty and exceptional cases have explicit representations or documented escape mechanisms.
8. Version 1 of the format and its conventions are documented.
9. The initial Wikisource-use and licensing policy has been decided.

Passing the pilot does not mean that the format can never change. It means later changes must be versioned, documented, and accompanied by a migration path.

## Non-goals

This phase does not aim to:

- transcribe the dictionary sequentially or claim production coverage;
- reproduce the exact page appearance in manually maintained files;
- create a newly typeset PDF;
- settle all entry boundaries or complete the Stage 2 schema;
- restore all Japanese forms or translate the Portuguese;
- anticipate every exceptional feature in the entire book.

Exact appearance remains available in the scan. Printable facsimile or side-by-side editions may later be generated from the source data, but they are publication formats rather than the editorial source of truth.
