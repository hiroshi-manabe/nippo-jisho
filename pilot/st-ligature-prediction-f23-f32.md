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

## Human result and retired initial checks

The second pass used the same labeled data as visual controls. Enlarged f23–f32
tiles were compared with the confirmed β-like short sort and the descending
long-`ſ` sort from f13–f22. Only readings judged sufficiently distinct were
prechecked; ambiguous forms were deliberately left unchecked. The 28
version-bound prechecks were formerly recorded in a TSV that remains available
through Git history.

These were predictions, not accepted transcription. In the completed human
review, the reviewer cleared all 28 because their classifications were not
useful. Issue #46 then supplied 97 short-`st` replacements and retained 14
genuine long-`ſt` forms. The precheck file remains only as experiment
provenance; no live checkbox state or current ledger is retained.

## Learning value

This pilot establishes two useful facts for subsequent batches:

- the 136 labels are not enough for a naive crop-level image classifier that
  generalizes across pages;
- the labels remain useful as a benchmark, but the attempted visual-control
  prechecks did not save human review effort.

The accepted f23–f32 labels are recorded in the transcription and retention
ledger. The f33–f100 task therefore starts completely unchecked. Any future
automatic experiment should first solve glyph localization explicitly rather
than resizing a broad text crop and expecting the classifier to discover the
target sort unaided.
