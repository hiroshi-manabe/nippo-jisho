# Tiled Visual Review Pilot

## Purpose

Whole-page display reduces the type too far for reliable visual transcription. The project therefore tests overlapping vertical tiles made from each full-resolution column. The original master remains authoritative; tiles are disposable, reproducible viewing aids.

This experiment occurs before Wikisource comparison. It is intended to improve the independent visual draft and quantify which crop size provides enough letter detail without removing necessary linguistic context.

## Hierarchy

```text
whole page for layout
    → column for reading order
        → overlapping vertical tile for transcription
            → entry-level enlargement for uncertainty
```

The whole page is inspected before and after tiled transcription. This protects against missed page furniture, incorrect column order, and continuation errors.

## Experimental profiles

The initial configuration tests two profiles on Gallica `f14` and `f248`:

| Profile | Tiles per column | Overlap |
| --- | ---: | ---: |
| Quarter-column | 4 | 160 pixels |
| Sixth-column | 6 | 160 pixels |

The overlap is recorded in exact source-image pixels. Adjacent crops must repeat the overlap rather than merely meeting at an edge. Duplicate lines are reconciled during column assembly.

The experimental source regions and profiles are defined in [tile-config-v0.json](../pilot/tile-config-v0.json). They are page-specific observations, not a universal automatic layout rule.

The first generation pass showed that column bounds must be visually checked: the initial `f14` left-column box was slightly too narrow and was widened before evaluation. This is evidence against adopting one unverified automatic crop for the complete volume.

## Generation

Install the image dependency if necessary:

```sh
python3 -m pip install -r requirements.txt
```

Then generate the experimental tiles:

```sh
python3 scripts/make_page_tiles.py pilot/tile-config-v0.json
```

Generated JPEGs and their manifest are written under `.cache/tiles/`, which is ignored by Git. The manifest records every crop box, profile, position, dimensions, and SHA-256 checksum.

## Review procedure

1. Inspect the complete page and identify headers, columns, continuations, catchwords, and exceptional marks.
2. Read one column from top to bottom using one tile profile.
3. Mark the first and last repeated line in each adjacent overlap.
4. Create entry-level enlargements for any unresolved letter sequence.
5. Assemble the column while removing only overlap duplication.
6. Reinspect the full column for omissions and reordering.
7. Inspect the full page again for cross-column and cross-page continuations.
8. Perform a separate second visual pass before consulting Wikisource.

Semantic and morphological reasoning may confirm or challenge a visual reading, but it must be recorded separately from what is visible in the image.

## Evaluation

For each profile, record:

- elapsed transcription and review time;
- number of unresolved readings;
- errors found during the second visual pass;
- missed or duplicated boundary lines;
- frequency of additional entry-level enlargement;
- whether surrounding context was sufficient.

The chosen version 1 profile may differ by page condition. The goal is a documented default and an explicit escalation rule, not one crop size imposed on every page.

### First timed result

The sixth-column profile makes individual letter sequences noticeably easier to inspect in the available viewing interface. The quarter-column profile retains more surrounding context and is useful for orientation. The current working hypothesis is therefore:

```text
quarter-column view for context
sixth-column view for primary transcription
entry-level crop for unresolved readings
```

The first timed second pass applied this method to `bnf-f0248`. All 12 sixth-column tiles were read, all 10 adjacent boundaries were checked, and the quarter-column views supplied orientation. The 3-minute-47-second visual comparison found six proposed corrections, with no missed or duplicated boundary lines and no need for a smaller entry crop. Full evidence is recorded in the [page-level review](../pilot/second-pass/bnf-f0248.md).

This result supports the working hypothesis but does not yet make it a version 1 decision. At least one page with degraded or irregular print should test the escalation to entry-level crops.
