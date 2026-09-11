# Shared scan-grounded AI review procedure

This procedure applies equally to the local assistant and an external reviewer.
It supplements the detailed [human review workflow](human-review-workflow.md#general-ai-commented-page-review).

## Inputs and authority

Start from the exact supplied baseline, not a remembered or cached page. The
current draft uses styled Calamari v2 OCR; refreshing recognition did not certify
display geometry. Retained OCR exceptions are not certified readings either.
Read native-resolution JPEGs, not reduced chat previews. Use full-page context
and individual line crops; enlarge difficult marks without treating interpolation
as new evidence. Saved OCR detections and existing rectangles are alternative
location evidence, never proof that the right physical row was selected.

Consult the transcription cheat sheet, historical-language notes, and generated
kana readings. Kana is a derived, fallible aid, not canonical text. Consult
NINJAL after independently reading the entry: it helps identify vocabulary but
does not establish this copy's case, spacing, accents or allographs. Investigate
genuine lexical uncertainties in neighboring entries and research when useful;
cite any additional source in the relevant comment. Do not silently modernize.
There is no routine requirement to consult Wikisource, reread all old Issues,
rerun OCR, or run a language model over every page.

## Two complete passes

1. Read every physical body line against the scan, interpreting Japanese and
   Portuguese together. Use kana to expose malformed Japanese, and consider
   morphology and the Portuguese explanation. Write a substantive English note
   during reading for every body line, including short continuations. Explain
   meaning or connection, not merely “checked.” Discuss suspicious words and
   uncertainty explicitly. Preserve useful conclusions, not an internal thought
   transcript. Notes must agree with the final text.
2. After reaching the end, return to the beginning for a separate complete scan
   pass. Treat first-pass text and comments as provisional. Check omissions,
   wrong-row associations, meaningful confusions, typography and graphic detail.
   Amend comments when subsequent corrections invalidate their explanation.

For meaning-changing alternatives (f/ſ, q/g, word identity and morphology),
linguistic evidence guides reinspection. For arbitrary graphic distinctions
(s/ſ, accents, spacing, punctuation, terminal hyphens), respect aligned OCR
unless there is positive contrary evidence. Neither a dictionary lookup nor an
AI's recurring visual impression overrules the scan. Preserve printed anomalies
with a note rather than silently emending them.

## Geometry and physical structure

Actually render each proposed crop and verify that the assigned line can be
read in it: beginning, end, accents, ascenders and descenders. Include the right
rule/context so that absent trailing material can be distinguished from clipped
material. Permit overlap when necessary. For slanted lines include their entire
extent. Mere numeric bounds validation or a column overview does not meet this
requirement. Full-page context resolves displaced fragments and catchwords.

Keep stable IDs; do not renumber to hide a missing or displaced row. Check page
furniture as well as text; furniture does not need routine line commentary.
The schema-2 external interchange delegates structural correction to the reviewer:
return corrected Markdown and crops with explicit before/after ID mappings and
reasons. Preserve unaffected IDs and account for removed material. Chosen readings
may carry nonblocking uncertainty notes; request intervention only when a usable
choice cannot be delivered. Schema-1 legacy packages remain restricted.
Mark Japanese words embedded in Portuguese and citation labels
for optional whole-word typeface toggling, irrespective of current font. Do not
mark ordinary Japanese headwords solely because they are Japanese.

## Completion

Both full passes, substantive body-note coverage and actual crop inspection are
required. Automated checks establish completeness and consistency, not accuracy.
Record reviewer provenance honestly; external completion is not a local visual
review or human approval. Human corrections remain an independent history.

Local integration regenerates compiled records and kana/UI data, validates,
commits and pushes. Check publication before claiming the live site is updated.
