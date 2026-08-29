# External Geometry Horizontal-Completeness Audit

## Scope and result

The audit covers every external-AI geometry result available on 2026-08-13: Gallica leaves `f31` through `f71`, comprising 41 pages, 82 columns, and 3,830 transcription-line crops.

The f31 human review exposed a systematic omission in the delegated procedure. Its vertical line positions were useful, but the fixed column-2 crop stopped before the outer ends of many printed lines. A full-page montage of every delegated result showed that this was a template-level risk rather than an isolated f31 error: odd-page right columns were most visibly affected, while the remaining columns also lacked a reliable complete-glyph safety margin.

All delegated vertical coordinates were retained. Each affected line crop and context crop was widened horizontally to conservative boundaries slightly beyond both printed column rules. This covers skew, long italic continuations, internal section layouts, catchword-adjacent text, and glyphs extending beyond the nominal text measure. The canonical geometry records the previous column box and the audit method under `horizontal_completeness_review`; audited columns use `external_ai_width_rechecked`.

The adjustment is reproducible with:

```sh
python3 scripts/recheck_external_geometry_width.py --apply
```

## Historical lesson

Recognizing the assigned line from a full scan was not evidence that its isolated UI crop was complete. Reviews had to verify all four edges of the actual returned crop, with explicit attention to the first and last printed glyph. A conservative rule-to-rule crop remained acceptable when tight per-line bounds added no practical value.

The external-AI workflow was retired on 2026-08-30, but this failure remains relevant to ordinary project-side geometry review: completion requires a final top-to-bottom sweep of the isolated crops for each column, specifically checking for a repeated clipped outer edge. This supplements rather than replaces per-line inspection.

## Revised f72–f85 batch

The independently revised returns for `f72` through `f85` were imported on 2026-08-14 after the first return had been rejected for poor quality. Their 1,327 line rectangles were checked in 28 column contact sheets. That check established line order and vertical readability, but a later dedicated right-edge audit found that it had not reliably established horizontal completeness. The fixed column-2 box on `f73`–`f85` ended at or too near the outer rule, and the even-page column-1 box on `f74`–`f84` stopped before the central rule. Those canonical boxes and every dependent line and context crop were widened on 2026-08-16 after a full-height scan comparison.

These columns use the deliberately conservative provenance value `ai_bulk_geometry_sanity_checked`: the isolated crops passed the project-side visual audit, but the response files do not contain per-line `geometry_action` evidence and retain partly standardized crop heights. A regression test now requires every crop and context crop in both external-AI batches (`f31`–`f85`) to retain complete horizontal coverage.

## f86–f100 batch

The `f86`–`f100` returns were inspected in 30 complete column contact sheets on 2026-08-16. Their vertical sequence was usable except for the f94 lineation discrepancy described below, but their fixed-width rectangles did not reliably preserve the outermost text. On f94, for example, the end of printed `acumu` extended beyond the submitted column-1 bound. All 1,414 imported rectangles were therefore widened to conservative rule-to-rule boundaries and assigned `external_ai_width_rechecked`. A subsequent full-height boundary audit found the f86 and f88 column-1 right margins still too close to the central rule; those two columns were widened again to match the manually verified even-page bound.

The f94 discrepancy proved to be a canonical error rather than a missing scan row: the scan prints `Ajũtar, & acumu` on one line and immediately begins the next entry, while the old transcription invented a separate continuation `lar.`. Removing that false line restored the correct 47-row sequence and allowed the returned downstream rectangles to align with their stable IDs.
