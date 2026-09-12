# Missing-leaf supplementation pilot

## Status — 2026-09-12

Source-identification pilot complete for printed folios **110–111** (four
sides). No canonical transcription, geometry, existing ID, or public reading
order has been changed. The replacement images are a different physical
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

## Integration work still to do

1. Make the page model and reading-order index accept source-specific IDs;
   preserve all existing Gallica URLs and human-correction references.
2. Add four source-labelled page records, deriving geometry afresh from the
   Bodleian images (they include rulers, adjacent-page slivers and different
   margins). Do not copy Gallica coordinates or scale the entire scan to fit.
3. Generate OCR, conduct the shared commented AI review and second pass, then
   present the result for human review. Mark each page as a Bodleian supplement.
4. Deploy only after verifying navigation, issue submission, reading hints,
   image attribution and the joins in the actual UI.
5. Map and visually verify the other six gaps separately. The 110–111 pilot
   does not establish their exact canvas mappings or scan quality.
