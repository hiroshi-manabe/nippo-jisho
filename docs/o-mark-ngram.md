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

## Held-out experiment

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
as reviewed data grows.

## Confidence and proposed use

The model returns the log10 score difference between the two complete
candidates. On this one held-out page, requiring an absolute margin of 0.6
retained 25/46 choices and all 25 were correct. This threshold is a
**post-hoc diagnostic on f151**, not an independently validated guarantee. A
second human-corrected held-out page is required before it becomes a default
automation rule.

For now:

- use the selected 2-gram result to prioritize `ô` versus `ǒ` during the
  pre-human reading pass;
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

The complete tracked result is
[`experiments/ocr/f0151-o-mark-ngram-results.json`](../experiments/ocr/f0151-o-mark-ngram-results.json).
Generated corpus and ARPA files remain under ignored `.cache/`; the tracked
script is the model recipe, and the result file fixes the exact selection and
validation evidence.
