# `algũa` / `alguã` Tilde-Position Audit

## Result

The Level 1 corpus is not uniform. A scan-level audit of the complete `algũa` / `alguã` family found **388 occurrences on 387 lines**:

- **243** print the tilde over `u`: for example `algũa`, `dalgũa`, and `Algũas`;
- **145** print the tilde over final `a`: for example `alguã`, `dalguã`, and `nalguã`.

The previously uniform transcription has therefore been corrected at the 145 final-`a` occurrences and retained at the other 243. The initiating example, `bnf-f0019:c2b-l011`, reads `alguã`; the clear forms on `bnf-f0014:c1-l044`, `c2-l029`, `c2-l039`, and `c2-l042` remain `algũa`. Enlarged line review later reassigned five initially classified final-`a` cases on `f47`–`f51` to tilde-over-`u`; human Issue review likewise reassigned `bnf-f0026:c2-l013`, `bnf-f0027:c2-l046`, `bnf-f0029:c2-l026`, three occurrences on `bnf-f0030`, `bnf-f0032:c2-l034` and `c2-l044`, `bnf-f0035:c2-l017`, four occurrences on `bnf-f0036`, `bnf-f0040:c2-l009` and `c2-l039`, `bnf-f0041:c2-l036`, and `bnf-f0042:c1-l004`, while Issue #16 reassigned `bnf-f0028:c2-l033` to final-`a`.

The occurrence ledger is [tilde-position-audit.tsv](tilde-position-audit.tsv). It records the page, line identifier, previous text, scan-adjudicated source text, and vowel carrying the mark. Capitalization, plurality, and contraction (`d-`, `n-`) are retained independently of the tilde position.

## Method

1. Inventory every case-insensitive occurrence of the `algua` family in the canonical Level 1 sources, including plural and contracted forms.
2. Recover each line from the Gallica master using the reviewed line geometry.
3. Enlarge the word and compare the mark's horizontal position with the `u`, final `a`, and secure specimens of both settings. The clear `f14` forms supplied `ũa` comparators and the four clear `f19` forms supplied `uã` comparators.
4. Reinspect weak, damaged, or displaced marks in wider line context. Record an occurrence-level decision rather than applying a lexical replacement.

The scan is authoritative. The spelling of another occurrence, a modern dictionary form, or an editorial transcription can identify a suspicious case but cannot decide where this compositor placed this mark.

## Historical interpretation

The variation is compatible with early Portuguese practice. Priscila Farias's survey of sixteenth-century grammars and printing describes the tilde as a sign for omitted nasal material, notes variation in its placement across vowel sequences, and shows that movable-type composition could displace a detached mark horizontally. João de Barros and Fernão de Oliveira provide near-contemporary grammatical context, but neither supplies a rule that licenses normalization of this dictionary's individual sorts.

Accordingly, Level 1 preserves the printed carrier: `algũa` and `alguã` are source-level variants, not two normalizations of one inferred abstract form. It does not expand either form to `alguma` or move the tilde to a preferred vowel.

## Scope

This audit covers only the `algua` family present in the current 129-page Level 1 corpus. It does not silently generalize its decisions to separate families such as `hũa` or `nenhũa`. Those require their own occurrence inventories if systematic doubt arises. The separately completed [`nhãa` / `nhaã` audit](nhaa-position-audit.md) uses the same occurrence-level principle and found final-`a` placement in all 64 current cases.

## References

- Priscila Lena Farias, [“About a J-shaped tilde: investigations on the status and form of the tilde in Portuguese grammar and typography”](https://www.researchgate.net/publication/258048288_About_a_J-shaped_tilde_investigations_on_the_status_and_form_of_the_tilde_in_Portuguese_grammar_and_typography).
- Rolf Kemmler et al., [“Dos Ortógrafos Portugueses aos *Portugaliae Monumenta Linguistica*”](https://scielo.pt/scielo.php?pid=S0807-89672024000100146&script=sci_arttext), including its semidiplomatic transcription criteria.
- Biblioteca Nacional de Portugal, [João de Barros, *Grammatica da lingua portuguesa* (1540)](https://fontesdoportugues.bnportugal.gov.pt/index.php/gramatica-norma-e-ensino/3-gramatica/1-barros-joao-de-1496-1570).
- ALFA, [study of orthography in Fernão de Oliveira's *Grammatica da lingoagem portuguesa* (1536)](https://periodicos.fclar.unesp.br/alfa/article/view/1393).
