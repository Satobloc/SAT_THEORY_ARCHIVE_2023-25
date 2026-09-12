SHARED RESOURCES INTAKE

Purpose:
This folder is the archive-side common area for useful, non-automatic resources created or discovered by archive users/AI instances. It is also the durable shared-resource counterpart to the current-build coordination area at Satobloc/HsH/WORKSPACES/COMMON/.

PUBLIC / PRIVATE REPOSITORY BOUNDARY:
- Satobloc/SAT_THEORY_ARCHIVE_2023-25 and Satobloc/HsH are the public project-record pair. Cross-link them bidirectionally when doing so improves provenance, chronology, navigation, or development traceability.
- Satobloc/HSH_RESOURCES is private/reference-only. Do not use a private HSH_RESOURCES GitHub link as the public evidence surface in this archive or in HsH.
- When reference material found in HSH_RESOURCES is used publicly, carry it across as a Chicago-style citation to the original source, an attributed quotation/extract with page/location information, or a sourced summary/paraphrase. Private/raw project data should be represented by an appropriate public-safe extract or summary with provenance.
- Internal/private research records may keep the exact HSH_RESOURCES path/hash for recovery; that locator is not the public citation.

WORKSPACE COORDINATION:
- Use HsH/WORKSPACES/<name>/ for substantial focused current-build work.
- Use HsH/WORKSPACES/COMMON/ for concise active handoffs, blockers, shared questions, and cross-agent coordination.
- Use this historical SHARED_RESOURCES folder for durable archive-side methods, reconstruction aids, heuristics, wayfinding, cross-repo maintenance notes, and resources useful to later archive workers.
- Do not let either common area become a substitute synthesis. Promote stable results to their proper ledgers, audits, timeline/provenance documents, synthesis, formalization, indexes, or source records.

Use this folder when an instance:

A) creates a resource that may help other users of the archive, such as:
- custom summaries
- analysis documents
- historical tracking notes
- extracted equations or important claims
- prediction logs or prediction-review tables
- correction notes
- custom tools/scripts
- strategy or workflow guides
- navigation aids

B) possesses or discovers a resource that appears missing from the archive or misplaced, such as:
- theory versions
- calculation corrections
- prediction logs
- effective guiding documents
- formalism notes
- important archive strategy notes

Do not use this folder for routine automatic outputs such as ordinary tool logs, routine folder indexes, or generated extraction chunks unless there is a specific reason to flag them for human review.

Required behavior:
1. Place the resource here or in a clearly named subfolder.
2. Add the resource to .[⚙️_AI_FILES]/RESOURCES.txt if it is now available for use.
3. Add a one-line note to .[⚙️_AI_FILES]/WATERCOOLER.txt under "Resource drops / triage notes".
4. If the item is only a candidate for later review, mark it clearly as NEEDS TRIAGE.

Suggested filename pattern:
YYYYMMDD_short-description.ext

Suggested one-line Watercooler format:
YYYY-MM-DD — RESOURCE DROP: <path> — <one-line purpose/status>.
