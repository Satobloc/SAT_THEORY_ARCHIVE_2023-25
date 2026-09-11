# XW-006 — Early Z3 Formalization Lineage

Status: provenance / mathematical-audit waypoint

## New finding

`DEV CONVERSATION/SAT FORMALIZATION ROUND 3ish.txt` predates the June 2026 `SAT AUDIT — Refine` rejection sequence in repository history and already contains an explicit Z3 field-theory formalization: a 1+1D angular field with a `cos(3 theta_4)` potential, three vacuum minima, domain-wall transitions, topological-sector language, and a proposed tau-braid algebra. Git history places the surviving repository ingest at 2025-10-27 23:41:06 UTC. This is a secure repository-visible upper bound, not necessarily the composition date.

The same byte-identical blob (sha `8cb6be0e8ef1d332425f27d1ea921911c1848a53`) survives under at least:
- `DEV CONVERSATION/SAT FORMALIZATION ROUND 3ish.txt`
- `Older Conversations/SAT FORMALIZATION ROUND 3ish.txt`

Other duplicate-path variants should be checked before counting this as multiple independent sources.

## Interpretation

This materially changes the M13 genealogy. The later failed `sum tau_i = 0 mod 3` Fusion Gate was not the first appearance of Z3 structure. An earlier branch had already *chosen* a Z3-symmetric potential / three-vacuum model and proposed topological-sector language. That earlier construction is mathematically legitimate as a model class, but the choice of `cos(3 theta_4)` is itself an assumption unless separately derived from deeper SAT/H(s)H geometry. Therefore:

1. `cos(3 theta_4)` -> three vacua / Z3 symmetry: VALID CONDITIONAL MODEL CONSTRUCTION.
2. three vacua -> domain walls / sector transitions: standard consequence within that chosen model class.
3. identifying those sectors with SAT tau states: MODEL IDENTIFICATION / requires justification.
4. promoting the resulting Z3 structure into `sum tau_i = 0 mod 3` as a universal fusion rule: NOT ESTABLISHED by the earlier model.
5. current H(s)H finite-core threefold geometry: genealogically related but not yet shown to derive the historical Z3 field potential or fusion law.

## External prior-art boundary

Z3 clock/Potts/chiral-clock models, three-state vacua, and domain-wall excitations are established prior art. This removes novelty from the generic `cos(3 theta)` / three-vacuum / Z3-domain-wall machinery. Any H(s)H-specific priority candidate would need to lie in an independently generated mapping from its finite-core geometry to a specific Z3 action, coupling, admissibility rule, or observable.

## Crosswalk value

Candidate source-development node:
`DEV CONVERSATION/SAT FORMALIZATION ROUND 3ish.txt`
  -> later SAT Z3 / tau-sector formulations
  -> `2026/SAT AUDIT — Refine .txt` Cycle-10/11 audit and rejection of the stronger modulo-3 gate

Classification: EARLIER MODEL FORMALIZATION -> LATER STRONGER REFORMULATION -> PARTIAL REJECTION.

Confidence: high for textual genealogy of Z3 machinery; medium for direct causal descent until message-level source-development chronology is recovered.

## Orphan / duplicate note

Because the same blob appears in multiple semantic folders (`DEV CONVERSATION`, `Older Conversations`, and likely additional copies), treat these as duplicate lineage, not independent corroboration. Prefer breadcrumbs/cross-references; do not move historical copies.

## Coverage limits

- Directly read the opening/model-building portion of the DEV CONVERSATION copy.
- Git ingest date checked for that path.
- Byte-identical SHA confirmed for the `Older Conversations` copy.
- Exact composition date and originating ChatGPT thread not yet recovered.
- External comparison here is category-level; no claim of exhaustive literature search.
