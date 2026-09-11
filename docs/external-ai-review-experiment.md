# External AI review experiment, 2026-09

Goal: replace the expensive local page-reading pass with external review, not
add another full AI review. The shared procedure remains authoritative for both.

## Stages and checkpoints

1. Keep implicit practices explicit in `shared-ai-review-procedure.md`.
2. Freeze this plan and the versioned output contract below.
3. Package f201 as OCR input plus local reviewed example; f202–f204 as blind
   targets. Native scans, geometry, generated kana, and page-specific NINJAL
   references accompany the instructions. Freeze OCR at `fa1b73ca`, local review
   at `6d59395e`, human result at `a6b22a76`. These references are resolved to full
   commits in the manifest. Human results and local target reviews stay in a
   separate evaluator ZIP, never in the handoff ZIP. Historical reference docs
   come from the OCR baseline to avoid later target-specific discoveries.
4. The user transfers the input ZIP to the external AI and returns its result
   ZIP. No automated external service invocation is assumed.
5. Validate and compare OCR, local review and external review against the frozen
   human text. Report per-page character edit distance, exact lines, styling
   disagreements, corrected/worsened lines and all differing lines. Human text
   is a reference, not infallible truth. Geometry equivalence is not coordinate
   equality: sample actual crops, plus consequential/ambiguous text differences
   and commentary quality. Do not redo the entire review. Checkpoint: promising
   enough for a live trial? Three pages cannot establish broad reliability.
6. Prepare a small human-unreviewed production batch only after that decision.
7. Validate and import with a script, regenerate UI, commit and push if explicitly
   requested. Preserve a before snapshot and Git parent for rollback. Checkpoint:
   the user reviews the live pages normally and assesses actual correction work.

## Contract v1 (conservative first implementation)

Input ZIP contains `manifest.json`, `README.md`, `references/`, `example/`,
`targets/`, and a `result-template/`. Return the template contents **at ZIP root**
in `PACKAGE-ID-result.zip`: `result.json`, and `pages/bnf-fNNNN.md` plus
`pages/bnf-fNNNN.geometry.json` for each target. No images are returned.

Edit the complete compact Markdown, retaining metadata, zones, IDs, placements,
indentation and furniture. Add substantive `[line-id note] English commentary`
for every body line. Set each crop in the geometry JSON to native `[x,y,w,h]`.
Use finite integer coordinates fully inside the native image. `result.json`
identifies the input-manifest SHA-256 and reviewer, contains per-page completion
booleans (both passes, crop inspection), uncertainties, structural-change reports,
and optional `typeface_terms` mapping line IDs to exact visible terms.

Structural edits are intentionally blocked by this importer: report them in
`structural_changes`; do not pretend completion. Normal text, font, notes and
crop edits need no local semantic approval. Uncertainties stop automatic import
but can still be evaluated. No schema downgrade or partial silent application.

## Commands

`python3 scripts/external_ai_review.py package --evaluation --output exports/external-review`

`python3 scripts/external_ai_review.py validate INPUT.zip RESULT.zip`

`python3 scripts/external_ai_review.py evaluate INPUT.zip RESULT.zip EVALUATOR.zip --output exports/external-review/report.json`

Later, `package --pages 216 217 --output exports/external-review` freezes live
canonical pages. It refuses pages with human correction history or human status.
The first version supports compact canonical pages only; other pages stop rather
than being silently promoted.

`python3 scripts/external_ai_review.py apply INPUT.zip RESULT.zip`

requires a clean tracked worktree, a production package, unchanged baselines and
geometry, and complete results. It builds the public UI but does not commit or
push unless `--publish` is supplied. On failure, restore only snapshotted files;
never reset unrelated work. The backup records the previous HEAD. After a
published import, rollback with `git revert IMPORT-COMMIT`, rebuild and push.
Publication build success is not proof of successful remote deployment; inspect
the deployment before reporting it live.
