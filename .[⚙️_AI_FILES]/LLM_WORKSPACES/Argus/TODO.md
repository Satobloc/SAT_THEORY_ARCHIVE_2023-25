# Argus — Priority Queue

## Immediate — infrastructure first

1. Re-enter archive work through the documented control route: root `README.md` → `.[⚙️_AI_FILES]/🪧_WAYFINDING.txt` → `ORIENTATION.txt` → `INSTITUTIONAL_MAP.txt` → `RESOURCES.txt` → `WATERCOOLER.txt` / `GUESTBOOK` as relevant; then consult Nathan's dashboard before changing machinery.
2. Audit and harden **automatic date-tagging, structural indexing, citation capture, and wayfinding** across all three repositories. Treat the repositories differently according to their jobs rather than cloning one architecture everywhere.
3. Establish point-of-use cross-repo pointers:
   - historical/archive machinery in `SAT_THEORY_ARCHIVE_2023-25` must point to live HsH and external-resource machinery where relevant;
   - HsH synthesis/ledger machinery must point directly to the exact HSH_RESOURCES source/citation record it uses;
   - HSH_RESOURCES bibliography machinery must include a citation-handoff field/register pointing back to the HsH location where a source is needed or used.
4. Make the HSH_RESOURCES bibliography state the theorybuilding boundary explicitly: SAT/H(s)H development proceeds in-house from its own Fundamental Intuitions/developmental genealogy; external literature is used for citation, prior-art comparison, standard mathematical/empirical context, constraints, and deliberately provenance-labeled imports—not silently as a source of governing assumptions.
5. Verify that automatic workflows are actually triggered by ordinary repository activity, are collision/loop safe, emit auditable manifests/logs, and do not rewrite historical/source content unnecessarily.
6. Build automated **coverage** machinery separately from human/semantic judgment. A machine may identify unindexed/uncited/unprocessed items; it should not decide relevance, novelty, or theoretical authority.

## Repo-specific maintenance model

### `Satobloc/SAT_THEORY_ARCHIVE_2023-25`
- Conservative historical/provenance archive.
- Preserve source paths/content.
- Structural index refresh should be automatic but not create uncontrolled dashboard growth; use the installed sharded index router/absorb machinery.
- Conversation date tagging should be confined to deliberately designated conversation-export locations, not sprayed across mixed historical folders.
- Archive Admin remains the normal request-driven executor for bounded archive operations.

### `Satobloc/HsH`
- Live theorybuilding + source-conversation preservation.
- Automatically maintain structural index and developmental-conversation chronology after ordinary pushes.
- Date-prefix stable/developmental exports where safe; treat moving `LIVE CONVOS` more conservatively, favoring generated chronology/metadata over filename churn unless explicitly configured otherwise.
- Maintain a source-side citation ledger at the synthesis point of use.

### `Satobloc/HSH_RESOURCES`
- External evidence/resource repository.
- Existing PDF upload → extraction → structural-index automation is the base layer.
- Add automatic bibliography-coverage accounting without pretending metadata/relevance judgments are automatic.
- Human bibliography remains distinct from machine inventory.
- Maintain a source-side citation handoff register containing the destination repo/path/claim that needs the source.

## Deferred until machinery is stable

- Individual FULL_CONVO ↔ focused-document provenance tracing.
- Claim-level prior-art adjudication beyond cases needed to test the citation machinery.
- Orphan and deep-source hunting beyond cases needed to test indexing/wayfinding coverage.
- Mathematical vetting candidates beyond ensuring there is a clean route for them into the appropriate indexes/ledgers.

## Validation questions

- Does a newly uploaded source automatically appear in the correct structural index?
- Does a newly uploaded developmental conversation automatically acquire or expose reliable Eastern-time date metadata without destructive source edits?
- Can a team member standing in HsH find the relevant HSH_RESOURCES citation record without knowing repository architecture first?
- Can a team member standing in the HSH_RESOURCES bibliography see exactly where a citation is needed in HsH?
- Can we tell automatically what bibliography coverage is missing without conflating “not processed” with “not relevant”?
- Are generated outputs, logs, human-readable indexes, source artifacts, and semantic judgments still separate layers?
- Are workflow-generated commits loop-safe and auditable?
