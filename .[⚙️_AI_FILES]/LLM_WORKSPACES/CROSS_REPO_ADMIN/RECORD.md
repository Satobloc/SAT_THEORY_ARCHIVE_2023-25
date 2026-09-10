# CROSS-REPO ADMIN — WORKING RECORD

## Remit
Nathan assigned this role responsibility for cross-repository administration spanning:
- `Satobloc/SAT_THEORY_ARCHIVE_2023-25`
- `Satobloc/HSH_RESOURCES`
- `Satobloc/HsH`

Goal: bring the three repositories toward a common standard of capability, coverage, provenance, logging, and cross-repo navigability while preserving their different purposes and local remits.

## Current repo roles
- Archive: preservation, historical provenance, wayfinding, structural indexing, durable institutional memory.
- HSH_RESOURCES: external-resource PDF extraction, machine/human indexing, bibliography/citation tracking, comparison and priority evidence. Not a theory-generation corpus.
- HsH: live theorybuilding, original full-conversation preservation and navigation, current-status logging, provenance/QC, cross-repo wayfinding.

Named remit references supplied by Nathan include GitKeeper for HSH_RESOURCES and Meridian/Janus/CoreTeam for HsH. Their full conversations are evidence for existing local practices and should be consulted before structural changes.

## Standing correction: BIG Archive Index
Do not repeat the 2026-09-10 retrieval mistake.

Established earlier in the controlling thread:
- `..[🎛️_NATHAN_DASH]/🗄️_ARCHIVE_INDEX.txt` is approximately 1.69 MB.
- A direct contents call returned an empty content field because of a large-object/retrieval-path issue.
- Alternate blob/resource retrieval exposed the actual content.
- The file is an accumulated historical ledger of folder-index runs, not merely a current tree.
- Each block can carry date, target, depth, entry ceiling, skip/include settings, and the resulting tree.
- The newest whole-main-archive block previously located was dated 2026-09-05 with `TARGET: .`, depth 8, and a 50,000-entry ceiling, excluding control folders/generated indexes.

RULE: an empty read of a known large archive object is a retrieval discrepancy, not evidence the file is empty. Check size/metadata, alternate retrieval, logs, and controlling conversation before drawing conclusions or mutating the file.

## Default Archive retrieval hierarchy
`master Archive Index` → `newest relevant index block / local ..findex` → `folder summary / derivation index / other catalog` → `run logs as needed` → `exact source path` → broad search only as supplement/recovery.

Negative search/index results remain unresolved unless the relevant scope is known to be exhaustive.

## Administrative design decision
Standardize capabilities and metadata contracts, not directory shapes.

Desired common affordances:
- explicit entry point;
- structural/machine inventory;
- human-readable index;
- documented tools/configs;
- state/progress ledger;
- auditable run logs;
- stable provenance identifiers;
- cross-repository pointers.

## Cross-repo navigation principle
Prefer pointers over copies. Each repo remains authoritative for its own local records. A future cross-repo layer should join canonical local identities/indexes rather than duplicate source corpora.

## Theorybuilding contamination boundary
External literature in HSH_RESOURCES is for prior-art recognition, chronology/comparison, empirical constraints, and terminology/legibility to standard physics. It must not silently determine H(s)H ontology, assumptions, goals, interpretations, conventions, or preferred machinery. Any deliberate import must be explicit and provenance-tracked.

The exact existing `PRIOR_ART` note remains a source-of-truth to read before finalizing repository policy text.

## Resume point
1. Bootstrap personal LLM workspace and persistent cross-repo TODO/action plan.
2. Next major Archive operation: retrieve the real large master index through a large-object-safe route, identify/chunk its historical blocks, then create a fresh root structural index and delta against the last applicable run.
3. In parallel/after local tool audit: HsH conversation date-tagging automation and HSH_RESOURCES extraction/bibliography reconciliation.

## Logging discipline
Important corrections, priorities, and decisions from the controlling conversation should be copied into `TODO.md` or this RECORD when they become durable. Tool executions and mutations belong in the repository's ordinary LOGS system; this file records state and resume logic, not a replacement execution log.
