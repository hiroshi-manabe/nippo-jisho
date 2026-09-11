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

## Contract v2 — delegated structural review

The f216–f218 schema-1 return exposed missing physical rows on f216 and f217,
plus header/catchword corrections on all three pages. Those changes were withheld
solely because of the original contract. This return is preserved for separate
local integration; it is not automatically upgraded or applied by this change.

New packages use schema 2. Full resulting Markdown is authoritative for physical
zone membership and order. The external reviewer may correct furniture, move
lines, alter placement, insert omitted rows, and split/merge/remove records.
Every structural edit has `{before: [IDs], after: [IDs], reason: "..."}`; IDs
unaffected by an edit must remain stable. All inserted/removed IDs must be
accounted for, all resulting body lines need comments and valid native crops,
and source identity/review metadata remain immutable. Explicit mappings and the
Git diff preserve traceability; no semantic rereview is required for import.

`uncertainties` is nonblocking documentation of the reviewer's chosen reading.
`decision_requests` blocks application only when intervention is genuinely needed.
Applied structural edits do not block. The importer rebuilds body geometry by
zone, generates context crops, removes obsolete membership, regenerates the UI,
and retains snapshots and receipts. Old schema-1 files retain their original
strict rules; there is no silent conversion.

The remaining f219–f236 packages are regenerated in
`exports/external-review/production-v2-f0219-f0236/`. Use these instead of the
original schema-1 packages. Keep the f216–f218 input/result pair unchanged.

## Legacy contract v1 (for existing returns only)

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
Both versions support compact canonical pages only; other pages stop rather
than being silently promoted.

For self-contained consecutive three-page packages:

`python3 scripts/external_ai_review.py batches --start 216 --end 237 --size 3 --output exports/external-review/production-f0216-f0236`

This creates seven full batches through f236. The incomplete f237 remainder is
explicitly listed as held in `batch-index.json`. Unsupported or human-protected
groups are listed as omitted, not silently regrouped. Every ZIP includes the
f201 example, full references and native images; send each ZIP independently.
Keep returned `PACKAGE-ID-result.zip` beside its corresponding input ZIP.

`python3 scripts/external_ai_review.py apply INPUT.zip RESULT.zip`

requires a clean tracked worktree, a production package, unchanged baselines and
geometry, and complete results. It builds the public UI but does not commit or
push unless `--publish` is supplied. On failure, restore only snapshotted files;
never reset unrelated work. The backup records the previous HEAD. After a
published import, rollback with `git revert IMPORT-COMMIT`, rebuild and push.
Publication build success is not proof of successful remote deployment; inspect
the deployment before reporting it live.
