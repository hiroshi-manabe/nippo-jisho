# Source and Image Policy

## Canonical copy

The Bibliothèque nationale de France copy published through Gallica is the initial canonical image source for the project:

```text
https://gallica.bnf.fr/ark:/12148/bpt6k852354j
```

Each page is identified by its Gallica view identifier, such as `f14`. Stable internal page identifiers therefore take the form:

```text
bnf-f0014
bnf-f0248
bnf-f0643
```

The identifier names the physical image in the canonical copy. Printed page numbers, signatures, and logical dictionary sequence are recorded separately.

## Image acquisition and public delivery

Acquisition should ordinarily request page images directly from Gallica’s IIIF image service. For example:

```text
Item page:
https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f14.item

IIIF image:
https://gallica.bnf.fr/iiif/ark:/12148/bpt6k852354j/f14/full/2000,/0/native.jpg
```

The requested width may be changed according to the task. Full-page survey images may be smaller than images used for difficult transcription, and IIIF crops may later be used for targeted review.

Downloaded images belong in an ignored local cache. The maintained project data should record source URLs, identifiers, dimensions, and—once the acquisition process is stable—checksums. Large image collections should not be committed to the main repository.

The reproducible procedure, cache layout, resumption behavior, and verification commands are documented in [Gallica Source Acquisition](source-acquisition.md).

The public interface does not depend on live Gallica image requests. All 651
downloaded leaves, plus 1000px preview and 2200px reading derivatives, are
published through the project-controlled [Cloudflare scan-image
mirror](image-mirror.md). This delivery mirror preserves the canonical Gallica
leaf identifiers and original-page links. It is a transport layer, not a new
textual witness or numbering authority.

## Wikimedia Commons mirror

The Wikimedia Commons PDF is a useful convenience mirror and fallback, but it is not the canonical numbering authority:

```text
https://commons.wikimedia.org/wiki/File:Gallica%E2%80%99s_Nippo_Jisho.pdf
```

Its PDF sequence includes two images before the corresponding Gallica `f` sequence. The following mappings have been visually verified:

| Gallica view | Commons PDF page |
| --- | ---: |
| `f14` | 16 |
| `f248` | 250 |
| `f643` | 645 |

The observed relationship is:

```text
Commons PDF page = Gallica f-number + 2
```

This relationship is useful for migration and cross-reference, but individual mappings should remain explicit in page metadata. It must not replace the canonical Gallica identifier.

## Wikisource

Wikisource is not an independent image source for this project. Its page views are associated with the Wikimedia Commons PDF. A controlled evaluation found only five PDF pages with contributed text, none proofread or validated, together with useful individual readings but significant textual and structural errors. The full evidence is in the [bnf-f0014 comparison](../pilot/wikisource-comparison/bnf-f0014.md).

Wikisource will therefore not be consulted during routine transcription or review. The project will work directly from the Gallica scan and preserve an independent checkpoint. An external transcription may be consulted exceptionally after independent review when a reading remains unresolved; its exact source and revision must be recorded, and every proposed reading must be adjudicated against the scan.

The roles are therefore:

1. **Gallica/BnF:** canonical copy, image service, and page identifiers
2. **Project Cloudflare mirror:** routine public delivery of the acquired Gallica scans
3. **Wikimedia Commons:** independent image mirror, complete-PDF convenience, and fallback
4. **Wikisource:** completed pilot comparison and exceptional fallback only, not a production transcription base

## Other physical copies

Other surviving copies may be consulted when the canonical copy is incomplete, damaged, or ambiguous. Text or images from another copy must never be inserted silently. The relevant page record must identify the witness and explain why it was used.

## External headword data

NINJAL's CC BY 4.0 [*Entry Words Data of Nippojisho*, version 202510](headword-data.md) is an approved external reference. It may be used after an independent visual checkpoint for coverage checking, error detection, and provisional entry scaffolding. Because it is based on the Bodleian copy and includes later editorial fields and normalization, it is not a substitute for the Gallica scan or the project's diplomatic transcription.
