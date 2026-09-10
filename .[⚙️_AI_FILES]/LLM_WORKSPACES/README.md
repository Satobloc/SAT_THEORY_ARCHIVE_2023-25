# LLM WORKSPACES

Purpose: persistent AI-side working memory for named LLM instances or durable roles operating across the SAT/H(s)H repositories.

This is ARCHIVE MACHINERY, not SAT/H(s)H theory content and not Nathan's dashboard.

## Why this exists
Long-running LLM work can lose continuity between sessions, tools, or context windows. Each active instance/role may keep a small personal workspace here for:
- current remit and operating scope;
- priority queue / TODOs;
- decisions and corrections that must survive context loss;
- source/thread pointers needed to resume work;
- progress/resume points;
- handoff notes to other instances.

This layer supplements, and never replaces, canonical repo indexes, tool logs, source provenance, or the Nathan-facing Dashboard.

## Naming
Create one subfolder per durable instance or role:

`LLM_WORKSPACES/<INSTANCE_OR_ROLE>/`

Prefer stable role/name identifiers. If a role changes hands, preserve the old workspace and record the handoff rather than rewriting its history.

## Minimum workspace files
Recommended minimum:
- `TODO.md` — ordered actionable queue; update whenever a durable priority/correction is established.
- `RECORD.md` — remit, current state, decisions, corrections, resume point, and handoff notes.
- `SOURCES.md` — controlling conversation IDs/exports, repo waypoints, and other provenance pointers.

Additional files are allowed when useful, but do not turn this area into a duplicate archive.

## Operating rules
1. Before a major resumed task, read the instance/role TODO + RECORD and relevant controlling conversation/source pointers.
2. Record durable user corrections immediately. Do not rely on conversational memory alone.
3. Record exact repository paths and stable conversation/document IDs where available.
4. Distinguish observed source facts from inference and plans.
5. Do not copy large source documents here; point to them.
6. Tool/action provenance belongs in the repo's normal LOGS system. A workspace may link to those logs and summarize the current resume point.
7. If a connector/search result conflicts with already established repository metadata, treat it as a retrieval discrepancy until reconciled; do not overwrite established state on the basis of a single failed/empty read.
8. Archive work remains index-first, tag-second.

## Cross-repo use
The personal workspace may point into all three repositories, but the underlying repositories retain their distinct remits:
- `SAT_THEORY_ARCHIVE_2023-25` — preservation, provenance, historical wayfinding.
- `HSH_RESOURCES` — external-resource extraction, indexing, bibliography, comparison/priority evidence.
- `HsH` — live theorybuilding, original full-conversation preservation/navigation, current-status/QC and cross-repo wayfinding.

Standardize capabilities and metadata contracts where useful; do not force the three repositories into identical structures.

## First workspace
`CROSS_REPO_ADMIN/` is the working area for the cross-repository administrative remit established in the H(s)H Archive Audit thread.
