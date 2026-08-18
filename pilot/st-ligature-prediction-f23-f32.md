# `ſt` / `st` prediction pilot: f23–f32

## Input and target

The completed f13–f22 specialist audit supplies 136 labeled scan occurrences:
108 short-`s`–`t` sorts and 28 genuine long-`ſ`–`t` sorts. The next review scope,
f23–f32, contains 111 occurrences still provisionally transcribed `ſt`.

## Rejected automatic experiment

A small image classifier was tested before making any initial checks. Each
occurrence was cropped from the native scan, normalized, represented by local
gradient histograms and low-resolution pixels, and classified by a
class-balanced radial-basis SVM. Validation held out one complete page at a
time, preventing ink and layout from the test page from leaking into training.

The result was unusable: balanced accuracy was 0.500, with confusion matrix
`[[108, 0], [28, 0]]` (`TN, FP / FN, TP`). In other words, it called every
held-out occurrence short. Those outputs were rejected and do not determine
any checkbox state.

## Initial checks used in the UI

The second pass used the same labeled data as visual controls. Enlarged f23–f32
tiles were compared with the confirmed β-like short sort and the descending
long-`ſ` sort from f13–f22. Only readings judged sufficiently distinct were
prechecked; ambiguous forms were deliberately left unchecked. The 28
version-bound prechecks are recorded in
[`st-ligature-prechecks-f23-f32.tsv`](st-ligature-prechecks-f23-f32.tsv).

These are predictions, not accepted transcription. The specialist UI loads
them as editable initial state, and the human reviewer may clear any or all of
them. If a source line changes, its stale precheck is not applied.

## Learning value

This pilot establishes two useful facts for subsequent batches:

- the 136 labels are not enough for a naive crop-level image classifier that
  generalizes across pages;
- the labels are already useful as control specimens for a faster comparison
  pass and as a benchmark against which future classifiers can be measured.

After f23–f32 is reviewed, its accepted labels should be appended to the
training corpus before another automatic experiment. A future model should
first solve glyph localization explicitly rather than resizing a broad text
crop and expecting the classifier to discover the target sort unaided.
