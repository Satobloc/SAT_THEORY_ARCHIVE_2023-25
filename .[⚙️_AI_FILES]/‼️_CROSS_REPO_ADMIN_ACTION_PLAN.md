# ‼️ CROSS-REPO ADMIN ACTION PLAN

Status: ACTIVE / HIGH PRIORITY
Established by Nathan: 2026-09-10
Controlling thread: `🧮 H(s)H Archive Audit Thread` — conversation ID `6aa20c62-b418-83ea-bbe4-a88534605c77`
Working continuity area: `.[⚙️_AI_FILES]/LLM_WORKSPACES/CROSS_REPO_ADMIN/`

## Mission
Bring the three SAT/H(s)H repositories toward a compatible administrative standard while preserving their intentionally different roles.

- `SAT_THEORY_ARCHIVE_2023-25`: preservation, provenance, historical wayfinding.
- `HSH_RESOURCES`: external-resource extraction, indexing, bibliography, comparison/priority evidence.
- `HsH`: live theorybuilding, original full-conversation preservation/navigation, current-status/QC, cross-repo wayfinding.

Standardize capabilities, metadata and interfaces; do not homogenize directory structures or merge evidentiary roles.

## Phase 0 — Grounding and continuity
1. Use each repo's front page/control docs, remit conversations and existing tools before designing replacements.
2. Read the cross-repo workspace TODO/RECORD and controlling conversation before substantial resumed work.
3. Preserve exact paths, stable IDs, hashes, timestamps, coverage states and logs.
4. Index first; semantic tagging second.

## Phase 1 — Archive
1. Treat the large Dashboard `🗄️_ARCHIVE_INDEX.txt` as the historical master index ledger. Do not interpret an empty connector read as an empty file.
2. Split the large accumulated index into navigable chunks while preserving dated historical run blocks and provenance.
3. Retain/create a compact master router so the newest applicable index run and older historical runs remain easy to reach.
4. Generate a fresh root structural index and compare it with the last applicable whole-archive run to identify additions/changes since last indexing.
5. Use/extend repo machinery in `.[⚙️_AI_FILES]/TOOLS` with script + config/request + log + auditable output conventions.
6. Keep detailed operational metadata in logs; keep human navigation readable.
7. Address repeated-append/idempotency problems in control-layer automation without rewriting archived source history.

## Phase 2 — HSH_RESOURCES
1. Read and preserve the exact `PRIOR_ART` instruction before final policy edits.
2. Reconcile PDF text-extraction coverage; make extraction resumable, hash-aware and logged.
3. Maintain separate machine manifest and human-readable resource/bibliography index.
4. Recover actual title/authors/identifiers from source content/metadata rather than guessing from filenames.
5. Build a Chicago-style master citation index with citation-use backlinks into theory development.
6. Keep folder placement separate from reviewed semantic relation.
7. Enforce theorybuilding firewall: external resources may support prior-art recognition, chronology/comparison, empirical constraints and standard-physics terminology/legibility; they must not silently supply H(s)H ontology, assumptions, goals, interpretations, conventions or habits.
8. Keep `EXPOSURE_STATS` and `PDF_SPECS` separate. Prepare `EXPOSURE_STATS` for a later cross-repo priority/timeline/independent-development/audience/GitHub-exposure administrative unit.

## Phase 3 — HsH
1. First operational priority: automatically date-tag FULL CONVOS on upload and/or via daily reconciliation.
2. Preserve native conversation timestamp, stable conversation ID and content identity; filename dates are navigation aids, not canonical identity.
3. Build an expanding structural CONVOS index before semantic mapping.
4. Add detailed content mapping for concepts, equations/constructions, terminology transitions, attachments and current status.
5. Build a theory-use/provenance ledger mapping exact FULL CONVO passages to synthesis/derivation/solver artifacts and later claims/constructions.
6. Provide bidirectional in-repo and cross-repo navigation while preserving raw original conversations.

## Phase 4 — Cross-repo accessibility layer
1. Each repository remains authoritative for its local index and records.
2. Cross-repo machinery joins canonical local records; it should not create another duplicate source archive.
3. Prefer stable native ID + content identity/hash + current exact path over path-only identity.
4. Expose both machine-readable registry data and a concise human router.
5. Track relationship type, provenance, confidence, and coverage so links do not imply stronger semantic claims than supported.

## Phase 5 — Exposure / priority administrative unit
Develop separately after core indexing is stable. Connect:
- public SAT/H(s)H chronology;
- podcast publication/audience evidence;
- GitHub publication/exposure evidence;
- independent-development chronology;
- external publication chronology;
- field-influence/contact patterns.

Keep `documented exposure`, `opportunity for exposure`, `independent-development evidence`, and `inferred influence` distinct.

## Persistent operating records
Detailed live priorities: `LLM_WORKSPACES/CROSS_REPO_ADMIN/TODO.md`
Durable decisions/corrections/resume state: `LLM_WORKSPACES/CROSS_REPO_ADMIN/RECORD.md`
Controlling sources/remit pointers: `LLM_WORKSPACES/CROSS_REPO_ADMIN/SOURCES.md`

Normal tool/action provenance belongs under the relevant repository's standard LOGS system.
