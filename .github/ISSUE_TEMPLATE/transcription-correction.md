---
name: Transcription correction
about: Propose one or more corrections for a single scanned page
title: "[f000] Transcription corrections"
labels: transcription-correction
assignees: ""
---

Thank you for checking the scan against the transcription.

The review page has copied a JSON payload to your clipboard. Paste it in the code block below. Please do not alter the `before` text or `base_commit`; add explanations through each change's optional `comment` field. In schema 2, `second_opinion: true` asks for detailed machine review of that item; unmarked changes are treated as exact human-confirmed corrections.

In an `after` value, `[Fotoqe]` forces roman type and `{P.}` forces italic type. These delimiters are correction notation and are not printed characters; typeface spans cannot be nested or overlap.

```json
PASTE CORRECTION JSON HERE
```

Additional context, if needed:
