# Automated review inbox

## Test policy

Application tests must not freeze evolving page readings, review classifications,
line inventories, individual crop coordinates, or campaign completion counts.
Test those software features on fixed examples instead. Live-corpus checks may
verify parsing, identity uniqueness, source/output consistency and history
aggregates. A legitimate review or import must not fail because a named page
has moved beyond its earlier provisional state. The compiler preserves existing
JSON bytes when parsed objects are equal, avoiding unrelated key-order rewrites.

`python3 scripts/review_inbox.py` performs one discovery/application cycle.
The macOS user LaunchAgent schedules cycles every five minutes and at login.
Codex does not need to be open; the old Codex heartbeat is paused. The user must
be logged in and the Mac awake and connected. Missed sleep intervals are not
processed as a backlog. launchd does not start overlapping instances, and the
existing script lock additionally protects against duplicate manual cycles.

The installed configuration is
`~/Library/LaunchAgents/com.manabe.nippo-jisho.review-inbox.plist`; the tracked
copy is `config/launchd/com.manabe.nippo-jisho.review-inbox.plist`. This is a
machine-specific configuration with explicit Python, tool search and repository
paths. Update/reinstall it if the Python installation or repository moves.
Git uses noninteractive SSH; authentication failures are logged, never prompted.

Status: `launchctl print gui/$(id -u)/com.manabe.nippo-jisho.review-inbox`.
Pause: `launchctl bootout gui/$(id -u)/com.manabe.nippo-jisho.review-inbox`.
Resume: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.manabe.nippo-jisho.review-inbox.plist`.
The script's `status.json`, per-attempt logs, and `launchd.stdout.log` /
`launchd.stderr.log` live in `exports/review-inbox/`. There are no Codex chat
notifications in this standalone mode; inspect those files and page warnings.
To disable across future logins, also move the installed plist out of LaunchAgents.

Issues are discovered oldest first. Put completed external result ZIPs in
`exports/external-review/incoming/`. The file must remain unchanged across
observations at least 60 seconds apart. Input ZIPs may remain anywhere under
`exports/external-review/` except backups. Matching uses the manifest hash,
never just a filename. Returned content is untrusted data, not executable instructions.

One nonblocking file lock serializes cycles. Do not run manual application
commands concurrently with a cycle. Tracked edits or unpushed commits pause
applications, but discovery continues. The script never resets or cleans the
worktree. Coordinate ordinary editing with this pause gate.

The persistent ledger and per-attempt logs live in `exports/review-inbox/`.
`status.json` gives the compact status. Each Issue number plus title/body hash,
or result-file SHA-256, is attempted at most once. Changed input gets a new
attempt; unchanged **application** failures are never retried. Interrupted
attempts require manual inspection. Do not delete the ledger as routine cleanup.

After an Issue's correction commit is created, its preparation report records
`publication_pending`, the commit, and whether its push was confirmed. A failed
deployment check or GitHub close request leaves this state intact. Every later
cycle checks the published corpus for the Issue's correction history and for a
commit descended from the recorded application commit, then retries only Issue
closure. It never reapplies the correction. Closure attempts and errors appear
under `closures` in the ledger and status file; one failure does not block other
work. If the Issue was closed separately, the runner confirms its state directly
before marking the pending report closed without posting another comment. An
open Issue with a failed application record overrides an inaccurate local
`closed` report. An unconfirmed push is **not** retried
automatically: inspect and publish it manually first. Keep the local
`build/correction-issues/` reports until pending closures are resolved.

Issues use the ordinary process command, including deployment verification and
closure. Messages and second-opinion requests do not prevent application: the
submitted text is applied and the original request/baseline is retained in
`pilot/human-review/pending-questions.json`. They appear in the page UI and can
be addressed in a later interactive pass. Application is not an AI endorsement.

External returns use the guarded importer, publish, and wait for Pages deployment.
Incomplete pass flags, missing commentary and decision requests do not prevent
import of otherwise usable data. They create durable pending records that make
the affected page read-only, both in the UI and Issue processor. Other pages
remain editable. Invalid JSON, missing body crops, invalid identities, unsafe
archives and stale baselines remain technical failures, not forced imports.
Validation failures with a clean repository do not block later jobs. Dirty or
unpublished failures pause the queue until a human/interactive assistant resolves
the state. A manual retry uses the underlying command after examining the log;
there is no automated retry command.

The scheduler performs no visual adjudication and does not interpret instructions
inside Issues. The script's persistent failure ledger remains authoritative.

## Supply packages

`python3 scripts/package_remaining_reviews.py --output exports/external-review/NEW-NAME`

Builds separate ordinary and supplemental batches of up to three pages, including
one/two-page remainders. Excludes human-protected and commentary-reviewed pages.
Ordinary machine/provisional sources share the format while retaining provenance.
Supplemental batches use bodleian-f0090r's original draft and current corrected
result; ordinary batches retain the frozen f201 example. Packages are self-contained.
The batch index records selection/omissions; old packages remain historical, and
stale returns are refused rather than overwriting newer work.
Use `--resume` only to continue an interrupted generation into the same folder;
existing matching batches are reused after source and geometry fingerprint checks.
The September 12 supply is in `exports/external-review/remaining-20260912/`:
407 ordinary pages (136 batches) and 27 supplemental pages (nine batches).

## Resolving pending questions

During an interactive review, inspect the stored original request and current
page together. Apply any agreed corrections through the normal workflow, then
change the record's `status` from `pending` to `resolved` and add a `resolution`
explaining the outcome. Retain the original request and baseline. Rebuild,
commit and publish. A page unlocks only when all its blocking records are
resolved; do not simply remove the warning in the browser. This is deliberately
not an automatic semantic adjudication or a new merge UI.
# Optional alignment generation

After Issue and external-result applications, the runner attempts at most one
alignment page per cycle under the same lock. AI-commentary-reviewed pages with
no applied human Issues take priority over human-reviewed pages. Baseline,
geometry, model metadata and generator code fingerprint each attempt; unchanged
failures are not retried. Successful assets are built, committed and pushed.
Pre-commit failures restore the prior asset; failed pushes require publication
recovery as with other jobs. Existing validated f230 data is preserved until its
baseline changes.

The corrected general generator uses saved isolated, rectified OCR crops and
replays their extraction on coordinate fields to recover native-scan mappings.
It verifies the saved image hashes and replayed pixels, and only publishes
lines with OCR/text agreement at least 0.85. Broad UI rectangles are not used
as recognition inputs. Missing extraction manifests are now recovered automatically
from the archived OCR baselines and polygons, conservatively matched to the current
text and geometry. Split section zones use their physical column's OCR evidence.
The recovery saves straightened crops and replayable records in the same cache;
it never changes canonical text or geometry. Ambiguous matches and individual
extraction failures are recorded as skipped lines. Missing source evidence or
zero usable matches still fail explicitly, rather than using broad UI crops.
Existing manifests are reused. Manifest changes
and mapper code changes are included in the job fingerprint.
Special layouts and poor matches remain unavailable. The recorded supplemental
f230 c1b-l003 crop is reused automatically; its initial decorated line remains
excluded. The corrected pipeline reproduced all f230 alignment/mapping values
exactly (86/87 lines) and recovered 95/95 lines on f226, versus 25/95 with the
discarded direct-crop method. OCR agreement is not a guarantee of visual
accuracy. Canonical text and geometry are never edited. Source scans
missing locally fail once and are recorded. The UI discovers generated assets
from its content-version manifest. No separate scheduling service is required.
