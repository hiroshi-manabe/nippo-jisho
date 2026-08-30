# Clean isolated-line OCR pairs

This dataset separates regular, cleanly isolatable physical lines from lines
that should continue through the general-purpose visual-AI workflow. It does
not replace the canonical transcription or geometry. Every accepted pair keeps
its page and line identifier, reviewed text, original review rectangle,
isolated source rectangle, and image checksum.

The intended routing is:

- clean isolated line → book-specific recognizer → human review;
- slanted, warped, damaged, decorated, displaced, or ambiguous line →
  general-purpose visual AI with page context → human review.

## Construction

`scripts/build_clean_ocr_pairs.py` processes `f13`–`f150` in two visual steps.
Within each physical block it places provisional boundaries near the midpoints
between neighbouring line centres. A horizontal ink projection then locates
the target band nearest the recorded position and creates a tight crop with a
small safety margin. Conservative checks reject duplicated geometry, irregular
spacing, clipped bands, implausible image/text proportions, excessive measured
skew, and irregular baselines.

```sh
python3 scripts/build_clean_ocr_pairs.py
```

Geometry alone cannot prove that the selected band belongs to the associated
text. Some historical review rectangles contain the preceding line more
prominently and expose the intended line only at the opposite edge. Therefore
`scripts/align_clean_ocr_pairs.py` uses the version 1 TrOCR model as an
alignment probe. The probe reads the original overlapping crop—the format on
which that model was trained—while the delivered training image remains the
new isolated crop. Dynamic monotonic alignment compares the approximate
readings with the reviewed line sequence and permits small, evidenced offsets.

```sh
arch -arm64 .cache/ocr-model/venv-arm64/bin/python \
  scripts/align_clean_ocr_pairs.py
```

A pair is accepted only when its isolated image passes the visual checks and
the probe reading supplies a sufficiently strong, sufficiently unambiguous
match. The probe never supplies the target transcription; the reviewed Level 1
text remains the target.

This check is not statistically independent on training pages because the
probe model learned from the same corpus. It is useful for detecting gross
line displacement, not for certifying the transcription. Deterministic contact
sheets therefore remain part of the dataset audit, and later model evaluation
must continue to use the frozen page-disjoint development and test sets.

## Local artifacts

The ignored `.cache/ocr-model/clean-lines-v1` directory contains:

- `images/`: isolated normalized line crops;
- `pairs.jsonl` and `rejected.jsonl`: visual-stage candidates;
- `aligned-pairs.jsonl`: final conservative image/text pairs;
- `aligned-train.jsonl`, `aligned-dev.jsonl`, and `aligned-test.jsonl`: the same
  frozen page-disjoint split used by the first model;
- `alignment-rejected.jsonl`: rejected records with explicit reasons;
- `summary.json`: criteria and coverage counts;
- `audit/`: deterministic visual contact sheets for accepted and rejected
  samples.

The generated images and manifests stay local and untracked. The scripts,
criteria, aggregate results, and tests are versioned so that the dataset can be
reproduced from the native scans and reviewed transcription.

## Version 1 yield

The first complete build covers `f13`–`f150`:

| Stage | Accepted lines | Share of 12,930 candidates |
| --- | ---: | ---: |
| Visual isolation | 8,547 | 66.10% |
| Final image–text correspondence | **8,049** | **62.25%** |

The final set contains 6,402 training, 820 development, and 827 test pairs on
the frozen page-disjoint split. It retains 294,709 of the source corpus's
426,077 characters (69.17%). All 8,049 target identifiers and source images are
unique, all image checksums pass, and a deterministic random audit of 100
accepted pairs found no incorrect or visibly contaminated pairing. All 52
pairs using an evidenced one-line offset to correct displaced legacy geometry
were separately inspected and also passed.

The two source characters absent from this conservative set are singletons:
`7` in the preliminary matter and `æ` in `& cæt.`. Both occur on lines rejected
for visual difficulty, so they remain in the general-purpose visual-AI route.
The complete tracked aggregate record is
[`experiments/ocr/clean-lines-v1-results.json`](../experiments/ocr/clean-lines-v1-results.json).

## Interpretation

“Accepted” means suitable for the next isolated-crop training experiment, not
that the line has been independently retranscribed or made error-free. The
criteria deliberately prefer precision over coverage. Rejected lines retain
their normal general-purpose visual-AI and human-review route; they are not
omitted from the transcription project.
