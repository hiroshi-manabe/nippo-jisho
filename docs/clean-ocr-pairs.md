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

The high-recall build is written separately to
`.cache/ocr-model/usable-lines-v2`. It has the same manifest layout plus a
`quality_tier` on every final pair and a `baseline-images/` directory for the
small number of conservative crops reused as fallbacks.

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

## High-recall version 2

Version 1 answered “which lines are unquestionably easy?” Version 2 instead
targets a rejection rate of at most 10% while retaining explicit evidence for
every recovered pair. It uses a separate profile so that the conservative
artifact and its thresholds remain reproducible:

```sh
python3 scripts/build_clean_ocr_pairs.py --profile high-recall

arch -arm64 .cache/ocr-model/venv-arm64/bin/python \
  scripts/align_clean_ocr_pairs.py \
  --dataset .cache/ocr-model/usable-lines-v2 \
  --recognition-dataset .cache/ocr-model/dataset-v2 \
  --run .cache/ocr-model/runs/trocr-small-v1 \
  --prediction-cache .cache/ocr-model/probe-predictions-v1.jsonl \
  --crop-prediction-cache \
    .cache/ocr-model/usable-lines-v2/crop-predictions.jsonl \
  --baseline-dataset .cache/ocr-model/clean-lines-v1 \
  --visual-accepts experiments/ocr/usable-lines-v2-visual-accepts.json \
  --alignment-policy high-recall \
  --maximum-cer 0.45 --automatic-cer 0.20 \
  --minimum-margin 0.02 --maximum-displacement 3
```

The visual stage expands beyond legacy review rectangles when neighbouring
line centres provide safer boundaries. Selected positional and proportion
conditions that are too conservative as hard exclusions—such as a band near
an expanded crop edge—become diagnostic flags. Crops with those flags, plus
crops whose overlapping-image probe has CER above 50%, must pass a second
recognition probe on the actual isolated training image. This second check
caught a real wrong-line pair during development and prevented it from
entering the final corpus.

The final corpus has three provenance tiers:

- `strict`: the 8,049 pairs accepted by version 1; when a newly expanded crop
  is less certain, the audited version-1 crop is copied into the version-2
  artifact instead (16 pairs);
- `recovered`: 3,596 additional pairs accepted by the relaxed visual rules and
  the correspondence checks;
- `visually-confirmed`: eight otherwise complete pairs whose isolated-crop OCR
  score was poor but whose scan crops were individually inspected and recorded
  in a tracked allowlist.

| Stage | Accepted lines | Share of 12,930 candidates |
| --- | ---: | ---: |
| Provisional visual isolation | 12,920 | 99.92% |
| Final image–text correspondence | **11,653** | **90.12%** |

The final rejection rate is **9.88%**. The set contains 9,277 training, 1,177
development, and 1,199 test pairs on the unchanged page-disjoint split, and it
retains 407,634 of 426,077 characters (95.67%). All identifiers, images, and
checksums pass integrity checks. Visual auditing covered 100 random recovered
pairs, 100 random all-tier pairs, every one of the 164 sequence-shifted pairs,
all 16 baseline fallbacks, and all eight explicit visual accepts; no wrong-line
association remained in those audits.

These audits estimate gross line-association quality, not diplomatic
transcription correctness. The complete aggregate record is
[`experiments/ocr/usable-lines-v2-results.json`](../experiments/ocr/usable-lines-v2-results.json).

## Interpretation

“Accepted” means suitable for the next isolated-crop training experiment, not
that the line has been independently retranscribed or made error-free. The
criteria preserve evidence and provenance even in the high-recall profile.
Rejected lines retain their normal general-purpose visual-AI and human-review
route; they are not omitted from the transcription project.
