# Nippo Jisho Project

This project aims to create a reusable, openly available edition of the *Vocabulario da Lingoa de Iapam* (1603–1604), commonly known in Japanese as the *Nippo Jisho* (日葡辞書).

The work will proceed from scans of the original dictionary and other public-domain source material. Existing transcriptions may be used where their terms permit, but every imported reading should remain verifiable against a specific page of the original. The project will not reproduce a modern copyrighted Japanese translation; it will produce a new transcription, restoration, and translation.

## Why the project is layered

Completing every entry from transcription through polished translation before moving to the next would make an unfinished project difficult to reuse. Instead, the dictionary will be developed in successive, publishable stages. Each stage should cover as much of the dictionary as possible and remain useful even if later work is delayed or never completed.

The four stages are:

1. **Source package and diplomatic transcription** — page images, stable references, and a faithful transcription of the printed text.
2. **Structured dictionary data** — entries and their components represented as searchable, machine-readable data.
3. **Japanese-readable edition** — Japanese-script restoration of the romanized Japanese and a new Japanese translation of the Portuguese.
4. **Annotated public edition** — editorial notes, cross-references, search, and a reader-friendly presentation.

The complete plan, including deliverables and completion criteria, is described in the [Four-Stage Project Roadmap](docs/four-stage-roadmap.md). Current activity is recorded in [Project Status](STATUS.md).

The [Source and Image Policy](docs/source-policy.md) defines the Gallica/BnF copy as the canonical image source, Wikimedia Commons as a mirror, and Wikisource as an evaluated but rejected production transcription base.

The complete high-resolution source cache can be obtained with the resumable procedure in [Gallica Source Acquisition](docs/source-acquisition.md).

The current high-resolution reading experiment is described in [Tiled Visual Review](docs/tiled-visual-review.md).

Source-specific orthographic patterns, confusable type, and safeguards against expectation-driven correction are collected in the [Provisional Transcription Reading Guide](docs/transcription-reading-guide.md).

The project has also acquired NINJAL's CC BY 4.0 [Nippo Jisho Headword Data](docs/headword-data.md), a 32,878-record external reference for post-checkpoint coverage validation and provisional entry scaffolding.

## Working principles

- **Evidence remains visible.** Every reading should point back to its page and location in the source.
- **Source and interpretation remain distinct.** Transcription, Japanese restoration, and translation are stored separately.
- **Uncertainty is recorded.** Difficult readings are marked with confidence or editorial notes rather than silently resolved.
- **Every stage is publishable.** A release does not have to wait for the final annotated edition.
- **Corrections are traceable.** Later improvements should not erase earlier evidence or obscure editorial decisions.

## Initial approach

Before processing the whole dictionary, the project will conduct a [Transcription-Format Pilot](docs/transcription-format-pilot.md). It will survey varied pages, test provisional representations, and define version 1 of the page-transcription format. A smaller end-to-end pilot will then take representative material through all four stages to test the wider data model. Once these formats have survived both tests, the main effort will return to completing Stage 1 across the dictionary.

## Current status

The project is currently in the **transcription-format pilot** phase. No production transcription format has yet been adopted. See [Project Status](STATUS.md) for the current focus and exit criteria.
