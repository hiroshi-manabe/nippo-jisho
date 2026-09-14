# Raw OCR character positions

`scripts/recognize_nippo_calamari.py --positions` retains Calamari's extended
prediction JSON alongside the usual text and typeface runs. This is optional
and does not modify canonical transcription, review status, or page geometry.

Example (run with the local Calamari environment's Python):

```sh
.cache/ocr-model/venv-calamari-arm64/bin/python scripts/recognize_nippo_calamari.py \
  .cache/ocr-model/page-refresh-v2/images/bnf-f0201/*.png \
  --prepared --positions --model models/local/nippo-calamari-v2-styled \
  --output .cache/ocr-model/character-positions-v1/bnf-f0201.json
```

Each line's `position_evidence` includes the source SHA256, source/prepared
dimensions, and unmodified model predictions (apart from the temporary image
path being replaced with the source path). Styled labels retain their original
private-use encoding; decode them with the model's existing decoder. Positions
are not indices into NFC-normalized or human-corrected text.

`global_start` / `global_end` are horizontal CTC alignment positions in the
prepared line image. They are not tight glyph rectangles: many have zero width,
and model rounding/padding can put some positions outside the image. Preserve
the evidence; any later display must derive usable highlight regions and handle
these cases explicitly. Mapping to the scan additionally requires the crop's
original extraction/rectification geometry. The existing page-refresh prepared
manifest retains that provenance.

Initial collection: f201, 95 lines, 3,236 voted character positions. This checks
output collection, not visual alignment accuracy. No whole-book run or UI
integration has yet been performed.

## f230 alignment pilot

`build_character_alignment_pilot.py` aligns raw decoded CTC characters to a
snapshot of the current Level 1 text. The standalone HTML embeds the saved OCR
crops and highlights estimated horizontal regions on hover, tap, or keyboard
focus. It is read-only; it neither changes canonical files nor uses local edits.
Substitutions and insertions are marked uncertain; multi-character replacements
share a region. These are text-alignment categories, not visual confidence.
Repeated strings and combining marks can still align incorrectly.

Output: `exports/character-alignment/f230.html`. The first run covered 85 of 87
body lines, with 2,736 matching characters and 15 uncertain ones. Saved OCR crops
were unavailable for `c1b-l001` and `c1b-l003`; these remain explicitly unavailable.
Short lines retain a consistent image scale rather than stretching to full width.
The baseline SHA256 identifies the transcription snapshot. Rebuild after changes.

The pilot also overlays translucent SVG transcription directly on the line
images, preserving roman/italic style. Opacity, font size, and horizontal/vertical
offset controls are display-only; a hold button temporarily hides the overlay.
Font size and baseline are approximate (initially 32 and 35 respectively in the
48-pixel prepared image), not measured glyph geometry. Historical letterforms
will not exactly match Georgia. Uncertain replacement groups distribute their
characters across the shared region. This is not forced alignment.

The missing ordinary `c1b-l003` was subsequently recovered with a visually
isolated native crop (770,1811,665,78), excluding the adjacent decorated G.
`scripts/prepare_f230_alignment_gap.py` reproduces the crop. Run the recognizer
with `--positions` (without `--prepared`) on it, then pass its predictions to
the builder via `--extra-predictions`. The pilot now covers 86/87 body lines;
only the decorated-initial line remains unavailable. Canonical geometry is
unchanged.

## Optional main-UI display

f230 now ships `site/assets/alignment/bnf-f0230.json` and the display-only
`site/assets/aligned-text.js`. The option appears in column view only when that
snapshot matches the current baseline text/typeface runs. Missing lines retain
the ordinary image. Enabled lines show the same rectified OCR crop used for
alignment, avoiding an inaccurate mapping onto a different canonical rectangle.
Disable the option to use the ordinary scan/context image.

On/off, size (12–32, default 26), vertical offset (−40–40, default 40), horizontal
offset and opacity (default opaque) persist in browser local storage. Settings
are collapsed by default and can be reset. Local corrections do not change the
aligned baseline text; editing and submission remain unchanged. There is no
character-highlighting interaction. No scheduler integration is enabled.

## Original-scan mapping experiment

`map_f230_alignment_to_scan.py` runs in the Kraken environment. It replays
extraction using saved boundaries/baselines, checks the prepared images against
all 85 saved crops pixel-for-pixel, and reuses the content-dependent trimming
box on floating-point x/y coordinate fields. A constant field excludes pixels
blended with polygon padding. Local affine fits map character anchors and glyph
axes back to native coordinates, including three piecewise-warped lines.
The supplemental c1b-l003 uses its known rectangular crop transform.

Results stay in `.cache/ocr-model/character-positions-v1/f230-native-mapping.json`.
`build_native_alignment_pilot.py` creates
`exports/character-alignment/f230-native.html` from ordinary canonical scan
rectangles. This is a separate experiment, not a production UI replacement.
Glyph shapes, baseline estimates and CTC positions remain approximate; local
affine fits are not an exact inverse warp of each complete letter outline.

The original-scan mapping is now used by f230's production optional display.
The original `.line-crop` stays in place, including its existing image loading
and context toggle. A pointer-transparent SVG layer follows the current crop
rectangle and uses mapped character axes; it does not intercept editing.
Whitespace is shown as `␣` only in this layer. Browser settings are unchanged.
The earlier rectified-image production description above describes the initial
implementation, now superseded. No periodic generation has been enabled.
