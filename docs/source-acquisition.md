# Gallica Source Acquisition

## Purpose

The project keeps a complete local cache of the canonical Gallica/BnF page images so that transcription, cropping, and review do not depend on repeated network requests. The cache is reproducible but is not committed to Git.

The acquisition program is [download_gallica.py](../scripts/download_gallica.py). It uses Python’s standard library and downloads the native-resolution JPEG for each Gallica view from `f1` through `f651`.

## Default command

From the repository root:

```sh
python3 scripts/download_gallica.py
```

The default paths are:

```text
.cache/sources/bnf-gallica/master/          page images
.cache/sources/bnf-gallica/acquisition.jsonl
.cache/sources/bnf-gallica/status.json
.cache/sources/bnf-gallica/download.log
```

The downloader is sequential and waits 0.75 seconds between successful requests. Failed requests use bounded exponential backoff. A page is first written to a `.part` file, checked as a JPEG, and atomically renamed only after validation.

## Resuming

Run the same command again. Existing images are validated and skipped. If an image exists but its manifest entry was not written before interruption, the downloader validates it, computes its checksum, and reconstructs the record.

The downloader records dimensions, byte size, SHA-256 checksum, source URLs, and acquisition time in JSON Lines format. Repeated records may exist after explicit redownloads; the last record for an identifier is authoritative.

## Monitoring

The most recent compact state is available in `status.json`. For example:

```sh
python3 -m json.tool .cache/sources/bnf-gallica/status.json
```

The persistent log can be followed with:

```sh
tail -f .cache/sources/bnf-gallica/download.log
```

## Verification

After acquisition finishes:

```sh
python3 scripts/download_gallica.py --verify-only
```

This checks that each requested file exists, has a parseable JPEG structure, and matches its recorded SHA-256 checksum. Checksums are created for files recovered without a manifest record.

## Limited ranges and testing

Any inclusive subrange can be requested:

```sh
python3 scripts/download_gallica.py --start 14 --end 16
```

Alternative locations can be supplied with `--output`, `--manifest`, `--status`, and `--log`. A non-mutating path and URL check is available through `--dry-run`.

## Storage policy

Native page dimensions vary. Tested dictionary pages are approximately 2,700 pixels wide, while bindings and edge images may have different dimensions. The complete acquisition is expected to require roughly 1–2 GB, subject to variation across the physical object.

The cache is excluded by `.gitignore`. Generated transcription tiles should be derived from these immutable master images and stored separately under the cache.
