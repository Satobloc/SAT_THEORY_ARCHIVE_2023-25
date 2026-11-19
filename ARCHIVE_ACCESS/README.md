# Archive Access Layer (AAL)

**Status:** Initial operational layer, 2026-11-18  
**Scope:** Navigation, retrieval, provenance, and bounded indexing for this archive.  
**Non-goal:** This layer does not decide theory truth, premise authority, or mathematical correctness.

## Cold start

1. Read the repository root README.
2. Read the current AI onboarding documents linked from the root README. Do not guess their paths; use the root's current links and `..findex.txt` where necessary.
3. Open the Nathan Dashboard under `..[🎛️_NATHAN_DASH]/!_DASHBOARD.md` for programme routing and current operational context.
4. For current SAT/H(s)H theory work, cross to [HsH BEDROCK](https://github.com/Satobloc/HsH/blob/main/BEDROCK.md). The historical archive does not override current premise state.
5. Use the current BigBook index, derivation index, mathematical repository, and archive indexes only for their declared purposes. Inspect the underlying source before relying on substantive claims.
6. Before editing tools or cursor state, inspect their existing contracts and current state.

## Existing navigation assets (do not duplicate)

- Root README: public orientation and entry links.
- `..findex.txt`: broad historical file navigation.
- `.[⚙️_AI_FILES]/INDEXES/SAT26_BIGBOOK_INDEX_2026-10-05.md`: embedded-document routing within SAT26_BIGBOOK.
- `..[🎛️_NATHAN_DASH]/..Derivation_Index.md`: provisional machinery-to-source map; not proof.
- `..MATHEMATICAL_REPOSITORY`: equation/provenance clearinghouse.
- `..[🎛️_NATHAN_DASH]/!_DASHBOARD.md`: programme switchboard; statuses on linked artifacts govern.
- `.[⚙️_AI_FILES]/CURSORS/🪧_WAYFINDING.txt`: cursor-state policy (currently a stub).

## Evidence and authority boundaries

Every retrieval result should distinguish:
- source presence;
- extraction/index metadata;
- authorship/provenance;
- historical/current status;
- theory authority/status;
- mathematical validity and review;
- quarantine/sandbox state.

These are not interchangeable. A search hit, index entry, polished document, or repeated assistant statement is not proof. A historical source may be essential for reconstruction without controlling current theory. When current theory status matters, consult HsH BEDROCK and its linked controls.

## Search/report contract

For each search task, record:
- **Question / scope**
- **Repositories and paths searched**
- **Search method** (exact term, indexed search, filename scan, full-text scan, OCR, semantic pass)
- **Coverage** (complete, bounded, partial, unavailable)
- **Exact source locator** (path, page/line/section, commit/ref where relevant)
- **Evidence excerpt or faithful summary**
- **Status distinctions** (historical/current/quarantined/sandbox; source/index/review)
- **Unresolved gaps and next cursor**

Never report a search as comprehensive if any relevant directory, branch, file family, or extraction layer was unavailable or truncated.

## Initial retrieval roadmap

1. Establish which index is authoritative for the requested material and date.
2. Query the smallest useful index first.
3. Resolve hits to exact underlying source files.
4. Inspect source context, not only snippets.
5. Compare contradictory or superseded sources explicitly.
6. Return a compact findings table plus reproducible search manifest.
7. Update an existing index only after verifying its generation/update contract; do not hand-edit generated indexes casually.

## Mersearch integration

For three-repository source archaeology, use the existing HsH Mersearch worker route: [MERSEARCH_WORKER_START_HERE](https://github.com/Satobloc/HsH/blob/main/WORKSPACES/COMMON/MERSEARCH_WORKER_START_HERE.md) and [MERSEARCH_RELEASES](https://github.com/Satobloc/HsH/blob/main/WORKSPACES/COMMON/MERSEARCH_RELEASES.md). The deployed bridge searches the SAT archive, HsH, and HSH_RESOURCES. Its shared request file is a single occupied slot: read `WORKSPACES/COMMON/MERSEARCH_REQUEST.json` first and never overwrite a pending/retry request. GitHub code search is only a fallback and must not be reported as a Mersearch result.

## Next infrastructure work

- [ ] Inventory every existing index, manifest, extraction layer, and cursor with owner/tool and freshness date.
- [ ] Determine the canonical full-text search route for large files and nested conversation exports.
- [ ] Audit current index generation workflows and identify stale or duplicate layers.
- [ ] Build a read-only search utility with bounded batches, resume cursor, SHA-256 source identity, and coverage report.
- [ ] Add a validation pass comparing sampled hits to direct source inspection.
- [ ] Connect the access layer to HsH's three-repository MERSEARCH route; do not replace MERSEARCH with one-repository GitHub search.

## Safe operation

This directory contains navigation and workflow documentation only. Do not move, rename, normalize, deduplicate, or rewrite source records as part of indexing. Generated indexes must remain reproducible and traceable to source paths and content hashes.
