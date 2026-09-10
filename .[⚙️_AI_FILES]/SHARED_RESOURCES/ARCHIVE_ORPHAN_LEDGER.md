# Archive Orphan Ledger

Status: live catalog / provenance aid

Purpose: record artifacts whose current location, filename, chronology, or linkage obscures their role in the SAT/H(s)H developmental record. Source files are left in place by default; this ledger adds breadcrumbs rather than rewriting history.

## Status legend

- OPEN — orphan relationship suspected but unresolved
- PARTIAL — some provenance or linkage resolved, further work remains
- RESOLVED — role/source relationship established sufficiently for navigation

---

## ORPH-0001 — `HSH_RESOURCES/PRIOR_ART/FileIndex.csv`

- **Status:** RESOLVED
- **Artifact type:** provenance metadata / local-filesystem index
- **Current path:** `Satobloc/HSH_RESOURCES/PRIOR_ART/FileIndex.csv`
- **Canonical/source-side counterpart:** `Satobloc/SAT_THEORY_ARCHIVE_2023-25/SAT_LOCALARCHIVE [OLD]/FileIndex.csv`
- **Why orphaned/misleading:** its placement under `PRIOR_ART` suggests external literature, but the file is an index of Nathan's older local SAT archive and records filesystem timestamps for SAT development documents.
- **Duplicate relationship:** the HSH_RESOURCES copy reproduces the same 11-row local-file index visible in the main archive counterpart.
- **Provenance value:** preserves creation/write/access timestamps for a compact sequence of late-April through June 1, 2025 SAT files.
- **Selected chronology anchors:**
  - `SATiii REWORK MARK III.txt` — CreationTime 2025-04-25 04:35:16; LastWriteTime 2025-04-25 04:35:18
  - `SATv EXPLORATIONS.txt` — 2025-05-07 13:11:12
  - `SATx-y FULL LOG.txt` — 2025-05-30 21:49:25 to 21:49:36
  - `SATxy CYCLETHROUGH3-4.txt` — 2025-05-31 00:25:39 to 00:31:02
  - `SAT-Y Hamiltonian+Quantum.txt` — 2025-05-31 01:19:03 to 01:39:00
  - `SAT FIRST LEG 3 of 3.txt` — 2025-06-01 06:32:07 to 06:37:19
  - `SAT RETRODICTED DATA JUNE 1 2025.txt` — 2025-06-01 09:30:11 to 09:35:13
- **Confidence:** high for file identity and filesystem timestamp record; medium for interpreting CreationTime as the intellectual creation time of all contained material, because copied/pasted content can predate the file.
- **Cross-reference:** `SAT_LOCALARCHIVE [OLD]/SATiii REWORK MARK III.txt` exists and contains the expected SAT Mark III developmental conversation/material.
- **Resolution note:** retain both copies where they are for provenance, but bibliography/prior-art tooling should classify this CSV as archive provenance rather than external prior art.

---

## Intake template

### ORPH-XXXX — `<path>`

- **Status:** OPEN / PARTIAL / RESOLVED
- **Artifact type:**
- **Current path:**
- **Why orphaned:**
- **Detected date evidence:**
- **Related concepts/claims/equations:**
- **Candidate source conversation(s):**
- **Candidate downstream document(s):**
- **Duplicate/lineage relationships:**
- **Confidence:**
- **Read status:**
- **Resolution note:**
