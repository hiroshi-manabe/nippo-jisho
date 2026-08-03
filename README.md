# Nippo Jisho Project

This project aims to create a reusable, openly available edition of the *Vocabulario da Lingoa de Iapam* (1603–1604), commonly known in Japanese as the *Nippo Jisho* (日葡辞書).

The current page-by-page transcription and correction interface is published at [Nippo Jisho · Human Review](https://hiroshi-manabe.github.io/nippo-jisho/).

Stable copies of all 651 Gallica scan leaves are served from the separate [Cloudflare Scan-Image Mirror](https://nippo-jisho-images.pages.dev/). The mirror and its reproducible local deployment procedure are documented in [Cloudflare scan-image mirror](docs/image-mirror.md). Source gallica.bnf.fr / Bibliothèque nationale de France.

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

The adopted [Level 1 page-transcription format](docs/page-transcription-format-v1-candidate.md) and its [29-page corpus](pilot/format-v1-trial/README.md) now cover 2,763 physical lines. The [compact Level 1 Markdown format](docs/level1-markdown-candidate.md) is the human-readable authoring form and regenerates the validated machine representation. Adoption evidence and timing are recorded in the [f249–f250 production simulation](pilot/production-simulation/f0249-f0250.md); sequential production reports now run from [`f15`](pilot/production-review/bnf-f0015.md) through [`f37`](pilot/production-review/bnf-f0037.md).

The [dictionary-wide human review interface](pilot/human-review/README.md) navigates all 651 acquired Gallica leaves, marks scan-only pages as unprocessed, and presents existing Level 1 pages as scan-and-transcription pairs. The public implementation follows the [Human Review and Correction Workflow](docs/human-review-workflow.md): a thumbnail overview, compact line editing, adaptive complete-glyph crops from one Gallica IIIF page image, an in-context two-level transcription reference, clipboard-to-Issue submission, and correction-history measures that do not claim final verification.

Daily linguistic review now begins with the compact [Transcription Cheat Sheet](docs/transcription-cheat-sheet.md). Its claims, qualifications, and source provenance are developed in the [Historical Language Notes](docs/historical-language-notes.md); scan-adjudicated mistakes from the pilot remain in the [Provisional Transcription Reading Guide](docs/transcription-reading-guide.md).

The project has also acquired NINJAL's CC BY 4.0 [Nippo Jisho Headword Data](docs/headword-data.md), a 32,878-record external reference for post-checkpoint coverage validation and provisional entry scaffolding.

## Working principles

- **Evidence remains visible.** Every reading should point back to its page and location in the source.
- **Source and interpretation remain distinct.** Transcription, Japanese restoration, and translation are stored separately.
- **Uncertainty is recorded.** Difficult readings are marked with confidence or editorial notes rather than silently resolved.
- **Every stage is publishable.** A release does not have to wait for the final annotated edition.
- **Corrections are traceable.** Later improvements should not erase earlier evidence or obscure editorial decisions.

## Initial approach

The completed [Transcription-Format Pilot](docs/transcription-format-pilot.md) surveyed varied pages and established version 1 of the page-transcription format. The project is now preparing bounded Stage 1 production with a human column-review checkpoint. A smaller end-to-end pilot will separately take representative material through all four stages to test the wider data model.

## Current status

The project is currently in **Level 1 production validation**. The format has been adopted, `f14` has completed human review, and sequential scan-confirmed transcription now runs through `f37`; pages `f15`–`f37` await human column review or recheck. See [Project Status](STATUS.md) for the current focus.
