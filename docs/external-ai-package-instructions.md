# Read this first — external page review

Extract this ZIP locally. The native JPEGs are the working images: do not rely
on reduced attachment previews. No access to our image server is needed.

Some targets originate as OCR-provisional candidates. Their input Markdown says
`lineation: unchecked`; keep that metadata unchanged in the return. Completion
is declared through the pass flags; the importer sets checked status only after
validation. `original-candidate.json`, when included, preserves the full original
wrapper/audit. Its previous warnings are context, not evidence that layout was
reviewed. Inspect headings, furniture, enlarged initials, transitions and omitted
rows along with ordinary text. Use the same schema-2 structural authority.

1. Read `references/shared-ai-review-procedure.md` and the compact Markdown
   format. Consult the cheat sheet and historical-language notes while reading;
   NINJAL is an attributed lexical aid, not a substitute transcription.
2. Inspect `example/input/` and `example/reviewed/`: f201 shows the draft and
   an actual reviewed result. This is an example, not an infallible answer key.
   Its historical review-status metadata is not an instruction to alter target
   metadata; the local importer sets the review stage after validation.
3. For each `targets/` page, follow the shared two-pass procedure. Read all lines
   against the native scan and write substantive English notes while reading.
   Inspect every final crop and then perform the separate complete second pass.
   The initial kana readings are fallible and may become stale after edits;
   reason from the revised Japanese rather than preserving a bad hint.
4. Copy `result-template/` to a working output directory. Edit its page Markdown
   and geometry files. Return the complete corrected pages, not patches. Under
   schema 2 you may correct furniture, placement, zones and physical lineation,
   including adding missing rows, moving catchwords, and splitting/merging rows.
   Make the changes in the Markdown and geometry, not merely in a prose report.
   Keep source/review metadata unchanged and preserve all unaffected IDs. Use
   fresh IDs such as `c1-l037a` for insertions; never renumber later rows.
   Every structural edit requires a `structural_changes` object with `before`
   and `after` ID lists and an explanatory `reason`. Insertions have empty
   `before`; removals have empty `after` and must explain why nothing is lost.
   Moves, furniture text corrections and indentation changes use the same ID
   in both lists. Splits/merges map the involved IDs; explain where text went.
5. In `result.json`, retain schema, package ID and input hash. Fill in reviewer
   identity (model/version if known), and set pass booleans to true only for
   completed work. `uncertainties` records nonblocking caveats about readings you
   have chosen and incorporated. Use `decision_requests` ONLY when you cannot
   deliver a usable choice without intervention; this blocks automatic import.
   An applied structural correction or ordinary damaged glyph is not itself a
   reason to stop. Keep useful uncertainties in the corresponding line notes
   as well, so the human sees them. Empty lists mean none. `typeface_terms` maps body
   line IDs to exact substrings: Japanese words embedded in Portuguese or
   citation labels for human whole-word font toggling, not ordinary headwords.
   Do not mark Japanese synonyms after `i,`, standalone Japanese example
   sentences, or their individual words and fragments. Mere proximity to
   Portuguese text is not enough: the Japanese term must occur *within a
   Portuguese explanation* (for example Fotoque in an otherwise Portuguese
   sentence). Citation labels may also be marked. An empty mapping is valid.
6. ZIP the output directory's contents at the root: `result.json` and `pages/`.
   Name it `PACKAGE-ID-result.zip`, substituting the manifest's package ID.
   Do not include scans, input files, or a parent directory. Do not manufacture
   completed artifacts if you run out of time: report which pages are pending.

## Output details

Geometry is `{ "source_size": [width,height], "crops": { "c1-l001": [x,y,w,h] } }`
in native pixels; origin top-left. Keep dimensions unchanged. Supply a crop for
every resulting body line, including additions. Remove crops for deleted IDs;
furniture crops are optional. Include full glyphs and right-edge context,
allowing overlap. Membership follows the returned Markdown zones, not ID prefixes.

Example structural records:

```json
[
  {"before": [], "after": ["c1-l037a", "c1-l037b"], "reason": "Two missing physical rows inserted after c1-l037; later IDs unchanged."},
  {"before": ["cw-l001"], "after": ["cw-l001"], "reason": "Corrected the catchword from the scan."}
]
```

Add notes after their physical lines, for example:

```
[c1-l002] Facumei. Aqiraca. *Clareza, & euidencia.*
[c1-l002 note] Aqiraca corresponds to “clear”; the Portuguese gives clarity and evidence. The headword requires contextual identification rather than modernizing its spelling.
```

Use `*...*` for printed italic, roman by default. The human correction UI's
square/curly-bracket shortcuts and tilde-moving asterisks are NOT this format.
Do not add kana to the canonical text. The importer regenerates it later.

Native scans: Source gallica.bnf.fr / Bibliothèque nationale de France.
NINJAL attribution and license are supplied separately in `references/`.
