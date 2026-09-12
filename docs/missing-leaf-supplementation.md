# Missing-leaf supplementation

## Status — 2026-09-12

All seven gaps are prepared as **OCR-only, AI-unreviewed** supplements,
including replacement of the original four-page pilot's simplified structure.
The minimum standard is the ordinary f251 automated preparation, not f231's
earlier visual checking. Existing Gallica IDs and text stay unchanged. These
images represent a different physical witness, not recovered Paris photographs.

The completed preparation retains **2,763 detected lines/fragments across 28
sides**. All source images are available on the Cloudflare mirror. Sampled
top/middle/bottom crops from both columns of one recto per gap were inspected;
this is a preparation sanity check, not an exhaustive line-reading review.
The 223r internal heading is separated even though OCR misreads its lettering.

## Common preparation standard

Use the ordinary automated structural inference for all 28 sides: separate
running headers, internal headings, column text and provisional furniture.
This does **not** establish final physical lineation or constitute the commented
AI review. Keep every detected fragment, including ambiguous bottom material;
do not resolve a catchword versus displaced continuation merely by its position.

`structure_bodleian_supplement.py` adapts the Bodleian source frame to the shared
`bootstrap_ocr_level1.infer_column` implementation. The source's rulers and
facing-page slivers require different header windows and column bands. Rectified
OCR fragments are not whole-column duplicate readings: disable duplicate-row
collapse for them. Preserve their original styled OCR text and stable IDs.

Display crops use a consistent full-column width and the detected polygon's
vertical extent plus padding. OCR's tight/rectified recognition image is retained
separately; short fragments must not be enlarged to fill a full display row.
Native segmentation, baseline polygons, rectified images and predictions remain
cached for later review. These geometric defaults are provisional, not a promise
that every crop has already been read by an AI or human.

No detailed linguistic review, reading commentary or final review pass is part
of this preparation. Review status stays machine-only/AI-unreviewed. Canonical
Markdown storage is an editing mechanism, not evidence of greater reliability.

## Complete source mapping

The seven four-side source contact sheets were inspected for printed recto
numbers, signatures and layout. The neighboring Gallica rectos were also checked
to confirm that each insertion bridges the corresponding missing folio pair.
Versos follow their explicitly labelled rectos in the Bodleian manifest.

| Printed folios (r/v for each) | Bodleian signatures | Insert between Gallica views |
| --- | --- | --- |
| 90–91 | Z2r–Z3v | f190 / f191 |
| 110–111 | Ee2r–Ee3v | f226 / f227 |
| 158–159 | Rr2r–Rr3v | f318 / f319 |
| 222–223 | Kkk2r–Kkk3v | f442 / f443 |
| 234–235 | Nnn2r–Nnn3v | f462 / f463 |
| 286–287 | c2r–c3v | f562 / f563 |
| 310–311 | i2r–i3v | f606 / f607 |

IDs use `bodleian-f0090r` etc. Existing pilot line IDs remain unchanged even
when a line moves out of the body zone; no Gallica page is renumbered.

`python3 scripts/acquire_bodleian_supplements.py` resolves unique signature labels,
downloads and fully decodes all images, and records source URLs, actual dimensions
and hashes in `sources/bodleian-supplement-sources.json`. Run
`scripts/prepare_bodleian_supplements.py` in the Kraken environment to recognize
and prepare them (`--replace-draft` explicitly replaces unreviewed drafts).
Human-corrected supplements are protected from replacement. Earlier pilot
Markdown is also retained in Git and backed up in the ignored OCR cache.
`scripts/inspect_bodleian_supplements.py` recreates the source contact sheets.

## Scope and evidence

Shirai and Tashiro Perez, [新出キリシタン版・リオ本『日葡辞書』について](https://k-rain.repo.nii.ac.jp/records/473),
report that Paris lacks folios 90–91, 110–111, 158–159, 222–223, 234–235,
286–287 and 310–311, all present in the Rio copy. These are **14 leaves / 28
page sides**, not 14 Gallica view numbers. Their description also notes Rio's
reversed Iii/Kkk gatherings: do not derive correspondence solely from scan order.

The Rio copy is a valuable alternative, with a
[2020 colour facsimile](https://catalogue.books-yagi.co.jp/books/view/2211), but
this investigation did not locate its complete public image manifest.

A directly usable source was found instead:

- Witness: **Bodleian Library, Arch. B d.13**, original 1603–1604 printing.
- [Digital Bodleian object](https://digital.bodleian.ox.ac.uk/objects/462146c4-dadb-4aa5-b324-2d45e30e5ddd/).
- [IIIF manifest](https://iiif.bodleian.ox.ac.uk/iiif/manifest/462146c4-dadb-4aa5-b324-2d45e30e5ddd.json),
  containing 829 canvases, labelled by signature rather than printed number.
- This is not the access-restricted Internet Archive scan of the 1960 facsimile.

## Verified pilot mapping

The four 1800-pixel survey images were inspected individually. Printed recto
numbers 110 and 111 and signatures Ee2/Ee3 agree with the manifest sequence.

| Proposed separate ID | Printed side | Canvas label | IIIF image UUID |
| --- | --- | --- | --- |
| `bodleian-f0110r` | 110r | fol. Ee2r | a32c467d-3e63-4aed-9a66-4c6196e67e8f |
| `bodleian-f0110v` | 110v | fol. Ee2v | 8f401794-f118-42db-b921-5bd59188d019 |
| `bodleian-f0111r` | 111r | fol. Ee3r | ddda9e3c-ba68-49a3-bb90-124326b91ed2 |
| `bodleian-f0111v` | 111v | fol. Ee3v | 9c250a70-e1bb-493d-8ef4-3efc0f72e6d8 |

Insert these in that order **between `bnf-f0226` and `bnf-f0227`**.
Existing Gallica IDs must not be renumbered or reused for the supplements.

Boundary evidence (identification excerpts, not a finished transcription):

- f226 ends `Fuqitçuqe, uru, eta. Fazer o vento che-`, with catchword `gar`.
  Bodleian 110r starts `gar a embarcação, ou dar com ella …`.
- 110r's catchword `cacaru.` repeats at the start of 110v.
- 110v's catchword `Furo` leads into the Furo entry at 111r.
- 111r's bottom continuation `¶ Cu-` leads into `¶ Cuchiuo …` at 111v.
- 111v ends the Futatocoro definition with `Marido, &`, with catchword
  `molher`; f227 begins `molher: palaura de molheres.`.

The last example restores the context of the current first-line review note
on f227. Update that note when the supplement is actually integrated, without
erasing the fact that the Paris witness itself is incomplete.

## Acquisition and attribution

Run `python3 scripts/download_bodleian_gap_pilot.py` for 1800px survey images,
or add `--width 0` to request the service's full image. The script resolves unique
signature labels, decodes the JPEGs and writes a checksum/provenance
record. Downloads and manifest snapshots go to the ignored directory
`.cache/sources/bodleian/pilot-110-111/`. Failed downloads must not be treated
as completed acquisitions.

Both variants were downloaded successfully. **The full-image response is
4000 pixels high**, not the approximately 8500-pixel height declared in the
manifest: actual sizes are 3511×4000 for rectos and 3509×4000 for versos.
All four full-image files were fully decoded successfully. The cache suffix
`-native.jpg` records the full-resolution request, not a guarantee that the
server delivered its underlying master. Do not label these files as native
master scans; investigate the service's resolution limit before needing more.

The object's manifest supplies **CC BY-NC 4.0** attribution; see
[Digital Bodleian terms](https://digital.bodleian.ox.ac.uk/terms/).
Keep image attribution and restrictions separate from the project's text
licensing. When displayed or mirrored, retain the source link and credit:

> Bodleian Library, Arch. B d.13. Photo: © Bodleian Libraries, University of
> Oxford. CC BY-NC 4.0.

Do not put these images under the Gallica credit or imply their image license
is the project's transcription license. No public image mirror was changed
during this pilot.

## OCR-only integration — 2026-09-12

`sources/supplemental-pages.json` supplies explicit reading-order anchors and
source metadata. The interface uses that order for page/column navigation and
batch submission, while old `#f226` links remain valid. New routes use, for
example, `#bodleian-f0110r`. Single and batch correction payloads retain their
existing schemas, accepting the new identifier in the `page` field.

`scripts/prepare_bodleian_supplements.py` uses fresh Kraken baselines/polygons,
rectified line images and the packaged styled Calamari v2 model. Run it in the
Kraken environment. It generated 99, 97, 98 and 98 detected lines respectively.
The original pilot retained headers and bottom fragments in its body sequence.
That shortcut is superseded by the common structural preparation above;
**final furniture interpretation and physical lineation still need review**.
No language correction, NINJAL intervention, commentary review or
second visual pass was performed, as requested. Raw segmentation, extracted
lines and predictions remain in `.cache/ocr-model/bodleian-supplements/`.

Draft Markdown is stored in the normal Level 1 directory to support ordinary
corrections, but status is `visual_draft`, lineation is `unchecked`, geometry is
`ocr_bootstrap_unreviewed`, and AI review is false. The regular issue processor
can apply changes without promoting any of those review statuses. Re-running
the OCR preparation refuses to overwrite existing drafts by default.

The mirror builder includes separately credited `supplements/` image assets.
After renewing the expired Wrangler login, supplemental image delivery was
moved to Cloudflare alongside the Gallica images. The UI remains on GitHub
Pages. Its optional `--bundle-supplements` fallback can still obtain missing
cache files through IIIF, checking SHA-256 and dimensions, and bundle the images
in the Pages artifact. The normal build needs no source-image download. Images
remain untracked; neither route depends on live IIIF requests while reading.

## Subsequent review and expansion

1. When requested, conduct the shared commented AI review and second pass,
   including lineation, furniture and actual crop readability.
2. Preserve the distinction between verified source mapping, automated structural
   preparation, and later detailed review. None substitutes for the others.
