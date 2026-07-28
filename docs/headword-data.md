# NINJAL Headword Data

## Source

The project uses the National Institute for Japanese Language and Linguistics (NINJAL) release [*Entry Words Data of Nippojisho*, version 202510](https://www2.ninjal.ac.jp/textdb_dataset/en/nipp/index.html) as an external reference dataset.

| Field | Value |
| --- | --- |
| Publisher | National Institute for Japanese Language and Linguistics (NINJAL) |
| Developer | Hideyuki Ohshima |
| Assisting developer | Taichi Aida |
| Version | 202510 |
| Publication date | 2025-10-30 |
| License | CC BY 4.0 |
| Official archive | `ew-nippo-202510.zip` |
| Archive SHA-256 | `6bb4f084b9e10778ecfc32e2e2f54c6c4c120f4b6cc91813cccba2b074250175` |

The official archive contains equivalent UTF-8 tab-separated and XLSX datasets plus a Japanese readme. The raw archive and unpacked files remain in the ignored local cache; they are not silently incorporated into the project's canonical transcription.

## Acquisition

Run from the repository root:

```sh
python3 scripts/download_ninjal_headwords.py
```

The verified files are placed under:

```text
.cache/external/ninjal-headwords/202510/
```

Running the same command again validates and reuses the existing archive. A non-downloading verification is available with:

```sh
python3 scripts/download_ninjal_headwords.py --verify-only
```

The downloader pins the release URL and observed SHA-256 checksum, tests the ZIP members and CRCs, and validates the TSV schema, sequential record numbers, unique headword IDs, BnF URL form, and record count.

## Verified contents

The local acquisition on 2026-07-28 contains:

- 32,878 records and 32,878 unique source-location IDs;
- 25,991 main-dictionary records and 6,887 supplement records;
- 24,940 records with direct Gallica/BnF page links;
- 7,938 records without BnF links, principally because the Paris copy lacks the supplement and several main-text leaves;
- 631 distinct linked Gallica pages;
- twelve documented columns, including original romanized headword, automatic katakana conversion, modern verb form, source locations, Gallica URL, editorial note, and *Nihon Kokugo Daijiten* identifiers.

The dataset is based on the Bodleian Library copy, using the 2013 colour facsimile. Its readme states that difficult readings generally follow the 1980 Iwanami Japanese translation. Katakana forms are mechanically generated with manual corrections; modern verb forms and dictionary identifiers are later editorial data.

## Intended project roles

The dataset may be used in two deliberately separate ways:

1. **Coverage and error detection after an independent checkpoint.** Compare visually transcribed pages against the expected source-order IDs and headwords to find omissions, duplications, boundary differences, and suspicious spellings.
2. **Provisional entry scaffolding.** Import selected identifiers, source locations, or headword strings into a separate attributed layer, then verify every imported reading against the project's canonical Gallica scan.

The scan remains primary evidence. NINJAL identifiers and Bodleian locations do not replace the project's Gallica page identifiers, and the dataset must not silently rewrite capitalization, spacing, diacritics, or entry structure in the diplomatic transcription.

## Initial quality observations

The data already adds useful evidence:

- It confirms `Aburamigaqi.` and `Aburicauarague,uru,eta.` on Gallica `f14`.
- It correctly identifies lowercase `aburamono` on Gallica `f14` as an independent headword. Its capitalization as `Aburamono.` is normalization, but its entry selection and boundary analysis are supported by the alphabetical sequence, the headword typeface, and the self-contained Portuguese gloss.
- It provides 31 expected entries on `f14`, 36 on `f248`, and 29 on `f643`, making page-completeness checks practical.
- It links the main dictionary directly to the Gallica images while also supplying Bodleian leaf-and-column locations.

It is not a diplomatic transcription:

- It records `Aburamono.` with a capital even though the Paris scan prints lowercase `aburamono`. The form is physically placed within the `Aburamigaqi` text block, as the dataset note observes, but it is structurally a separate entry.
- It distinguishes the unmarked `Gucan.` entry from the later `Gǔcon.` entry; the Paris scan confirms both the separate entries and the caron in the latter, while close review remains necessary for adjacent confusable letters.
- It replaces the printed lowercase `l` used in *vel* notes with a vertical bar.
- It contains katakana, modern verb forms, source mappings, and lexical identifiers derived through later editorial analysis.

These are not reasons to reject the dataset. They define its proper role: a broad and valuable reference index whose suggestions must be classified and checked against the scan.

The `aburamono` case also establishes an important distinction for later comparison: **headword identification and diplomatic form are separate claims**. An external dataset can correctly identify an entry while normalizing its capitalization or spelling. Comparison reports must therefore assess at least (a) whether an entry exists and where its boundary falls, and (b) whether the supplied headword string reproduces the source exactly. Agreement on the first does not authorize importing the second into the diplomatic transcription.

## Attribution and redistribution

Any redistributed copy or derived dataset containing NINJAL material must retain attribution to NINJAL, Hideyuki Ohshima, and Taichi Aida, identify version 202510, link to the official release, and state that the source is licensed under CC BY 4.0. Project-authored changes must be distinguished from the supplied data.
