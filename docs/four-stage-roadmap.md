# Four-Stage Project Roadmap

## Purpose

The aim is to create a new, reusable edition of the *Nippo Jisho* while ensuring that incomplete work still has lasting value. The project therefore advances horizontally through the dictionary in four publishable stages instead of finishing isolated entries one at a time.

The stages describe releases and working priorities. They do not collapse the underlying scholarly distinctions: facsimile location, transcription, structural analysis, Japanese restoration, translation, and annotation must remain separate data fields even when they are produced during the same stage.

## Overview

| Stage | Main result | Independently useful as |
| --- | --- | --- |
| 1. Source and transcription | Auditable text tied to the scans | Searchable primary-source transcription |
| 2. Structured data | Entries divided into meaningful fields | Dataset for research, search, and reuse |
| 3. Japanese-readable edition | Japanese forms and new translations | Readable working dictionary for Japanese users |
| 4. Annotated public edition | Editorial apparatus and public interface | Finished research and reference edition |

## Stage 1: Source Package and Diplomatic Transcription

### Objective

Produce a faithful, citable transcription of the complete original text, with every passage linked to its physical location in a scan.

### Work included

- Identify the scans and copies used, including missing, damaged, or duplicated pages.
- Assign stable identifiers to volumes, pages, columns, and—where practical—lines or text regions.
- Import useful existing transcriptions when licensing and provenance are clear.
- Verify imported or automatically recognized text directly against the scans.
- Preserve original spelling, romanization, abbreviations, punctuation, and typographical distinctions according to documented conventions.
- Review the initial visual transcription in separate Japanese/romanization and Portuguese-context passes, then confirm every proposed correction against the scan. These are Stage 1 reading controls, not later normalization or translation.
- Preserve observable physical evidence needed for later interpretation, including line and column order, visible placement marks, indentation, and exceptional text placement where relevant.
- Record illegible passages and materially uncertain readings explicitly; do not burden secure readings with routine character-level confidence metadata merely because context assisted their recognition.
- Retain page furniture such as headings, catchwords, and continuation markers when it assists reconstruction of the text.
- Defer entry boundaries, logical reassignment of displaced text, and other lexical interpretations to Stage 2 rather than embedding them in the diplomatic text.

### Principal outputs

- Source inventory and page map
- Page images or durable links to them
- Diplomatic transcription
- Transcription conventions
- List of unresolved readings

### Completion criterion

Every surviving dictionary page has been transcribed or explicitly accounted for, and every transcription unit can be checked against a known source location.

### Valid stopping point

Even without later stages, this release is a searchable and correctable primary-source text suitable for linguistic and historical research.

## Stage 2: Structured Dictionary Data

### Objective

Transform the page-oriented transcription into entry-oriented, machine-readable dictionary data without altering the source transcription.

### Work included

- Identify entry boundaries and continuations across columns or pages.
- Infer logical reading order for displaced material from the preserved marks, position, syntax, and context in Stage 1.
- Separate headwords, inflectional forms, grammatical labels, Portuguese definitions, Japanese examples, usage labels, dialect information, and cross-references.
- Preserve the order and wording of the diplomatic transcription alongside the structured representation.
- Link every structural assertion back to stable Stage 1 transcription units instead of maintaining a separately corrected copy of their text.
- Give each entry a stable identifier.
- Record editorial decisions where boundaries or field assignments are uncertain.
- Validate the resulting data for consistency and completeness.

### Principal outputs

- Structured entry dataset
- Data schema and field documentation
- Stable entry identifiers
- Validation reports and unresolved structural questions

### Completion criterion

Every transcribed dictionary entry is represented in the agreed schema, linked bidirectionally to its source transcription and scan location, and passes the project’s structural validation checks.

### Valid stopping point

This release supports full-text and fielded search, computational analysis, concordances, and reuse by other editions or research projects.

## Stage 3: Japanese-Readable Edition

### Objective

Make the dictionary usable by present-day Japanese readers while preserving a clear boundary between historical evidence and editorial interpretation.

### Work included

- Restore the romanized Japanese headwords and examples in Japanese script.
- Distinguish secure kana readings from proposed kanji spellings.
- Translate the Portuguese definitions, labels, and explanatory text into new Japanese.
- Interpret Japanese forms and Portuguese definitions together where necessary, while storing restoration and translation separately.
- Attach confidence levels or notes to uncertain restorations and translations.
- Apply consistent policies for historical forms, obsolete vocabulary, names, Buddhist terminology, regional usages, and other specialized material.

### Principal outputs

- Japanese-script forms for headwords and examples
- New Japanese translations of Portuguese content
- Restoration and translation guidelines
- Review status and confidence information

### Completion criterion

Every structured entry has either a reviewed Japanese restoration and translation or an explicit status explaining why one cannot yet be supplied. Original romanization and Portuguese text remain visible and unchanged.

### Valid stopping point

This release functions as a practical Japanese working edition even before extensive annotation or a dedicated public interface exists.

## Stage 4: Annotated Public Edition

### Objective

Turn the accumulated source, data, restoration, and translation layers into a coherent scholarly and public reference edition.

### Work included

- Add concise editorial notes where readers need historical, linguistic, or cultural context.
- Link variant forms, cross-references, related entries, and occurrences in examples.
- Provide introductions explaining the source, romanization, Portuguese usage, editorial method, and limitations.
- Build browsing and search facilities suited to both Japanese and original romanized forms.
- Display scan, transcription, structured fields, restoration, and translation together without confusing their evidential status.
- Provide downloadable data and clear reuse information.
- Establish a correction and revision process for the published edition.

### Principal outputs

- Annotated edition
- Searchable public interface
- Downloadable datasets and documentation
- Citation guidance and revision history

### Completion criterion

The edition is publicly accessible, its layers can be inspected and cited, its editorial policies are documented, and users can report or propose corrections.

## Distinctions preserved across stages

The following fields may be worked on together, but must never be merged into a single undocumented string:

```text
source_location       page, column, and region in the scan
source_transcription  what the original print is judged to say
entry_structure       the editorial division into dictionary fields
japanese_restoration  Japanese script reconstructed from romanization
portuguese_text       the original definition or explanation
japanese_translation  the project’s new translation
editorial_note        explanation, alternatives, or historical context
confidence            review and uncertainty status for an editorial claim
```

A correction to a proposed Japanese spelling, for example, must not silently change the diplomatic transcription from which it was derived.

## Pilot and execution order

The project begins with a [Transcription-Format Pilot](transcription-format-pilot.md). Approximately 10–15 pages selected for varied physical and textual features will be used to establish version 1 of the page-transcription specification. This is the project’s current phase and precedes production transcription.

After that format has stabilized, an end-to-end pilot of approximately five representative pages will test the wider data model. The selection should include ordinary entries as well as difficult typography, cross-page continuations, grammatical information, examples, and at least one uncertain reading.

The pilot should:

1. Exercise all four stages.
2. Test whether the source identifiers and data schema support later editorial work.
3. Produce initial transcription, restoration, and translation conventions.
4. Identify tasks that can be automated and those requiring human review.
5. End with a documented revision of the data model.

After the pilot, work should return to Stage 1 and proceed broadly through the complete dictionary. Later stages begin as full production phases only after the preceding layer is sufficiently stable. Small experiments may continue, but they should not displace completion of the current foundational release.

## Release strategy

Each stage should have its own versioned release rather than being treated as an internal draft of the final edition. Partial releases may also be useful when they cover a clearly defined range and include review status.

A release should state:

- the source copy and page range covered;
- which fields are present;
- which material has been visually verified or reviewed;
- known omissions and unresolved readings;
- the applicable license and attribution requirements;
- the software or data version used to produce it.

This approach treats interruption as a normal project risk. Progress remains cumulative: finishing an earlier layer across the dictionary is a substantive result, not merely preparation for a result that may never arrive.
