# Missing-leaf supplementation pilot

## Status — 2026-09-12

Four **OCR-only, AI-unreviewed** drafts now cover printed folios **110–111**.
Their distinct IDs are inserted between f226 and f227 in public reading order;
existing Gallica IDs and text are unchanged. The replacement images are a different physical
witness, not recovered photographs of the Paris copy.

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
The machine-only records retain headers and bottom fragments in their detected
column sequence: **furniture classification and physical lineation still need
review**. No language correction, NINJAL intervention, commentary review or
second visual pass was performed, as requested. Raw segmentation, extracted
lines and predictions remain in `.cache/ocr-model/bodleian-supplements/`.

Draft Markdown is stored in the normal Level 1 directory to support ordinary
corrections, but status is `visual_draft`, lineation is `unchecked`, geometry is
`ocr_bootstrap_unreviewed`, and AI review is false. The regular issue processor
can apply changes without promoting any of those review statuses. Re-running
the OCR preparation refuses to overwrite existing drafts by default.

The mirror builder can include separately credited `supplements/` image assets.
Cloudflare deployment authentication was unavailable during this integration,
so the public builder bundles these four images and derivatives into the
GitHub Pages artifact instead. It obtains missing cache files through IIIF and
requires their SHA-256 and dimensions to match the canonical source metadata.
Images remain untracked; ordinary Gallica images still use Cloudflare. This
avoids a live IIIF dependency while reading and does not require a new service.

## Subsequent review and expansion

1. When requested, conduct the shared commented AI review and second pass,
   including lineation, furniture and actual crop readability.
2. Map and visually verify the other six gaps separately. The 110–111 pilot
   does not establish their exact canvas mappings or scan quality.
