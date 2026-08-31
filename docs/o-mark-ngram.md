# Character N-gram model for marked `o`

## Question and boundary

This experiment tests a deliberately narrow linguistic decision. It assumes
that visual inspection or OCR has already established that a printed `o`
carries one of the two relevant marks, and asks a character language model to
choose between circumflex `ô` and caron `ǒ`. It does **not** detect whether a
mark is present, distinguish ink from damage, or override the scan.

The implementation follows the state-based lattice pattern used in
`jfconv-scripts/decoder.py`: at a disputed position the decoder branches into
the two Unicode candidates, advances a KenLM `State` with `BaseScore`, merges
equivalent states, and scores the end of the run. Spaces are represented by an
explicit character token. The corpus contains Roman-type runs only, so an
italic Portuguese context cannot silently influence a Japanese Roman-type
choice.

## Single-page held-out pilot

The model was trained on canonical Level 1 data from `f13`–`f150`; `f151` was
excluded completely and used only after its human correction Issue had been
applied. The training material comprises 10,006 Roman runs, 131,092 character
tokens, 1,404 `ǒ` tokens, and 702 `ô` tokens. The held-out page contains 46
choices: 21 `ǒ` and 25 `ô`.

| Method | Correct | Accuracy |
| --- | ---: | ---: |
| always choose training-majority `ǒ` | 21/46 | 45.65% |
| memorize the marked word; otherwise choose `ǒ` | 40/46 | 86.96% |
| character 2-gram | **43/46** | **93.48%** |
| character 3-gram | 42/46 | 91.30% |
| character 4-gram | 41/46 | 89.13% |
| character 5-gram | 37/46 | 80.43% |

The 2-gram result was 22/22 on word signatures seen during training and 21/24
on unseen signatures. Thus its improvement is not merely a dictionary lookup.
It chose all 20 held-out `Vôqina`, `Vôqini`, `Vôqinari`, and `Vôyubi`
occurrences correctly. Its three errors were `Vǒ` read as `Vô`, `Daixô` read
as `Daixǒ`, and `Danchǒ` read as `Danchô`.

The result does not support selecting the maximum order merely because it is
available. KenLM does back off through shorter histories, but sparse and noisy
higher-order observations can still receive enough weight to hurt this small
conditional task. Exploratory singleton pruning of the 5-gram model did not
reverse the ranking. The currently selected model is therefore the 2-gram;
orders through five remain in the evaluation so that the choice can be retested
as reviewed data grows. This single page is strongly biased toward the repeated
`Vôqina` family and must not be read as a general accuracy estimate.

## Page-level ten-fold cross-validation

To measure that bias, pages `f13`–`f151` were shuffled with fixed seed `1603`
and partitioned into ten folds. Each fold withheld 13 or 14 complete physical
pages—roughly one tenth of the available pages—and trained on all the others.
No line from a test page appeared in that fold's training corpus. Across the
139 pages, the test folds contain 2,152 marked-`o` occurrences: 1,425 `ǒ` and
727 `ô`.

| Method | Correct | Accuracy |
| --- | ---: | ---: |
| fold-specific majority `ǒ` | 1,425/2,152 | 66.22% |
| memorized word signature, majority fallback | 1,472/2,152 | 68.40% |
| character 2-gram | **1,522/2,152** | **70.72%** |
| character 3-gram | 1,473/2,152 | 68.45% |
| character 4-gram | 1,486/2,152 | 69.05% |
| character 5-gram | 1,509/2,152 | 70.12% |

The ten 2-gram fold scores range from 64.14% to 77.61%. Only 578 test
occurrences had a word signature seen in the corresponding training fold; the
model reached 76.30% on those. The other 1,574 occurrences were unseen word
signatures and reached only 68.68%. This confirms that the 93.48% f151 result
was dominated by its repeated local vocabulary. The N-gram still adds evidence
beyond memorizing complete words, but the general gain is modest: 4.50
percentage points over the majority baseline and 2.32 points over the
word-signature baseline.

The order ranking also becomes much less decisive: the 5-gram is only 0.60
points below the 2-gram. The 2-gram remains the empirical winner, but the
present evidence supports neither a strong claim about optimal order nor an
automatic accent decision.

## Confidence and proposed use

The model returns the log10 score difference between the two complete
candidates. On f151 alone, requiring an absolute margin of 0.6 retained 25/46
choices and all 25 were correct. The broader cross-validation does not sustain
that apparent calibration: the same cutoff retains 731/2,152 choices (33.97%
coverage) at 78.66% accuracy. Even a margin of 1.0 reaches only 83.80% accuracy
at 10.04% coverage. A score margin is therefore useful for ranking uncertainty,
not for licensing automatic changes.

For now:

- use the selected 2-gram result only as a weak candidate-ordering cue during
  the pre-human reading pass;
- preserve both candidate scores and route a low-margin choice to enlarged
  scan inspection;
- never use this model to infer that an accent exists;
- continue to prefer explicit human scan confirmation over the model;
- rerun the complete order sweep when a materially larger corrected corpus is
  available.

## Reproduction

The evaluator requires the KenLM Python binding and the `lmplz` executable. It
builds each requested order, decodes with KenLM states, and records every
held-out occurrence as well as aggregate and confidence-threshold results.

```sh
python scripts/evaluate_o_mark_ngram.py \
  --lmplz /path/to/lmplz \
  --work-dir .cache/o-mark-ngram/f151 \
  --output experiments/ocr/f0151-o-mark-ngram-results.json
```

The single-page tracked result is
[`experiments/ocr/f0151-o-mark-ngram-results.json`](../experiments/ocr/f0151-o-mark-ngram-results.json).
The page-level cross-validation is reproduced with
`scripts/cross_validate_o_mark_ngram.py`; its aggregate and per-fold results
are tracked in
[`experiments/ocr/f0013-f0151-o-mark-ngram-cross-validation.json`](../experiments/ocr/f0013-f0151-o-mark-ngram-cross-validation.json).
Generated corpus and ARPA files remain under ignored `.cache/`; the tracked
script is the model recipe, and the result file fixes the exact selection and
validation evidence.
