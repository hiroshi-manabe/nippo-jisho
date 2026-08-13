# External Geometry Horizontal-Completeness Audit

## Scope and result

The audit covers every external-AI geometry result available on 2026-08-13: Gallica leaves `f31` through `f71`, comprising 41 pages, 82 columns, and 3,830 transcription-line crops.

The f31 human review exposed a systematic omission in the delegated procedure. Its vertical line positions were useful, but the fixed column-2 crop stopped before the outer ends of many printed lines. A full-page montage of every delegated result showed that this was a template-level risk rather than an isolated f31 error: odd-page right columns were most visibly affected, while the remaining columns also lacked a reliable complete-glyph safety margin.

All delegated vertical coordinates were retained. Each affected line crop and context crop was widened horizontally to conservative boundaries slightly beyond both printed column rules. This covers skew, long italic continuations, internal section layouts, catchword-adjacent text, and glyphs extending beyond the nominal text measure. The canonical geometry records the previous column box and the audit method under `horizontal_completeness_review`; audited columns use `external_ai_width_rechecked`.

The adjustment is reproducible with:

```sh
python3 scripts/recheck_external_geometry_width.py --apply
```

## Consequence for future delegation

Recognizing the assigned line from a full scan is not evidence that its isolated UI crop is complete. Future reviews must separately verify all four edges of the actual returned crop, with explicit attention to the first and last printed glyph. A conservative rule-to-rule crop is acceptable when tight per-line bounds do not add practical value.

The delegated-work README and response generator now carry this requirement directly. Completion includes a final top-to-bottom sweep of the returned isolated crops for each column, specifically checking for a repeated clipped outer edge. This supplements rather than replaces the per-line inspection.
