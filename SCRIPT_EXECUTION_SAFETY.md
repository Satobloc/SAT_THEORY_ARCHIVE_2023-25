# Script Execution Safety — Required

All scripts, bots, GitHub Actions, extraction jobs, indexing/tagging utilities, local tools, and automated write processes operating on this repository must follow the authoritative project-wide standard:

`Satobloc/HsH/WORKSPACES/COMMON/CROSS_REPO_SCRIPT_EXECUTION_STANDARD.md`

This repository is `[[GLASS]]` in that standard.

Minimum requirements before unattended write-capable execution:
- declare exact read/write scope;
- preserve source artifacts;
- respect quarantine/sandbox routing before file access;
- re-fetch current target state before semantic writes;
- use current-SHA/CAS or fetch/rebase protection;
- never force-push or blindly overwrite collisions;
- isolate temp/output namespaces per run;
- validate outputs and reject unexpected diffs;
- retain enough source/run provenance to reproduce or audit the result.

For extraction/OCR/image/conversion work: write derived outputs to dedicated output trees and never replace original source files in place.

If a script cannot satisfy these rules, it should be treated as needing a safety upgrade before unattended use.
