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

## Image acquisition

Page images should ordinarily be requested directly from Gallica’s IIIF image service. For example:

```text
Item page:
https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f14.item

IIIF image:
https://gallica.bnf.fr/iiif/ark:/12148/bpt6k852354j/f14/full/2000,/0/native.jpg
```

The requested width may be changed according to the task. Full-page survey images may be smaller than images used for difficult transcription, and IIIF crops may later be used for targeted review.

Downloaded images belong in an ignored local cache. The maintained project data should record source URLs, identifiers, dimensions, and—once the acquisition process is stable—checksums. Large image collections should not be committed to the main repository.

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

Wikisource is not an independent image source for this project. Its page views are associated with the Wikimedia Commons PDF. It may later be evaluated as a secondary transcription source under the procedure defined in the [Transcription-Format Pilot](transcription-format-pilot.md).

The roles are therefore:

1. **Gallica/BnF:** canonical copy, image service, and page identifiers
2. **Wikimedia Commons:** image mirror, complete-PDF convenience, and fallback
3. **Wikisource:** possible transcription source to be evaluated after independent drafts are frozen

## Other physical copies

Other surviving copies may be consulted when the canonical copy is incomplete, damaged, or ambiguous. Text or images from another copy must never be inserted silently. The relevant page record must identify the witness and explain why it was used.
