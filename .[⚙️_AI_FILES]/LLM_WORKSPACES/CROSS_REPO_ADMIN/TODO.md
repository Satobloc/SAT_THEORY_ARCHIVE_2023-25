# CROSS-REPO ADMIN — PRIORITY TODO

Last updated: 2026-09-10
Controlling conversation: `6aa20c62-b418-83ea-bbe4-a88534605c77` — “🧮 H(s)H Archive Audit Thread”

This is the durable working queue for the cross-repository admin remit. Update it when Nathan establishes a durable correction, priority, dependency, or completed milestone.

## P0 — continuity / retrieval discipline

- [ ] Before substantial resumed work, consult this TODO, `RECORD.md`, the controlling conversation export/log, and the relevant repo front page/control docs.
- [ ] Treat `..[🎛️_NATHAN_DASH]/🗄️_ARCHIVE_INDEX.txt` as a LARGE historical master ledger, not an empty file. A prior direct contents call returned empty content despite live metadata showing ~1.69 MB; alternate retrieval succeeded. Do not overwrite/reinitialize it on the basis of an empty connector response.
- [ ] Use master Archive Index → newest relevant index block/local `..findex` → folder summary/derivation/catalog → logs → exact source path as the default Archive retrieval hierarchy. Search is supplemental.
- [ ] Preserve exact paths, stable IDs, hashes, timestamps, and coverage limits wherever available.

## P0 — cross-repo administrative standard

- [ ] Finish audit of all three repos' front pages, remits, tools, requests/configs, indexes, and logs before extending machinery.
- [ ] Standardize capabilities rather than forcing identical structures: entry point, machine inventory, human index, tool docs, progress/state ledger, auditable logs, provenance IDs, cross-repo pointers.
- [ ] Build a lightweight cross-repo accessibility layer that joins each repo's canonical local indexes rather than rescanning/copying source material.
- [ ] Preserve repo boundaries: Archive = preservation/wayfinding; HSH_RESOURCES = external-resource extraction/index/bibliography; HsH = live theorybuilding/full-convo preservation/navigation/QC.

## P0 — Archive

- [ ] Split the BIG Dashboard `🗄️_ARCHIVE_INDEX.txt` into navigable chunks WITHOUT destroying its accumulated historical-ledger function.
- [ ] Keep a compact master/router that points to chunked historical index material and makes latest applicable runs easy to identify.
- [ ] Run/create a new root-directory structural index and compare it with the last full-archive indexing state to identify additions/changes since last indexing.
- [ ] Verify the previously located newest whole-main-archive block: 2026-09-05, `TARGET: .`, depth 8, 50,000-entry ceiling; inspect corresponding folder-indexer log before using it as comparison baseline.
- [ ] Use/extend scripts under `.[⚙️_AI_FILES]/TOOLS`; durable additions should follow script + request/config + log + auditable output conventions.
- [ ] Preserve generated index/run history; do not collapse operational provenance into a single current snapshot.
- [ ] Investigate repeated append/idempotency problem in AI control notes without rewriting source history.

## P0/P1 — HSH_RESOURCES

- [ ] Read and preserve the exact `PRIOR_ART` note before finalizing bibliography/theorybuilding policy language.
- [ ] Reinforce firewall: external resources are for prior-art recognition, chronology/comparison, empirical constraint, and standard-physics terminology/legibility; they are NOT the conceptual substrate for building H(s)H.
- [ ] Avoid importing outside ontology, assumptions, goals, conventions, preferred interpretations, or habits into theorybuilding except where explicitly adopted and provenance-tracked.
- [ ] Reconcile PDF extraction coverage; make extraction resumable/hash-aware; log failures and extractor/version.
- [ ] Maintain machine-readable resource manifest separately from human-readable bibliography/index.
- [ ] Build master Chicago-style citation index with stable resource identity, exact path, bibliographic metadata, source type, coverage/read status, duplicate group, and neutral description.
- [ ] Add citation-use backlinks: where/when a resource is cited during theory development, what role the citation serves, and exact HsH/Archive source pointer.
- [ ] Treat folder placement (including `PRIOR_ART`) separately from reviewed relationship/classification.
- [ ] Keep `EXPOSURE_STATS` and `PDF_SPECS` as separate administrative threads.
- [ ] Plan future Exposure/Priority administrative unit joining public chronology, independent-development evidence, podcast/audience evidence, GitHub exposure, field-influence patterns, and external publication chronology.

## P0/P1 — HsH

- [ ] First operational priority: automatically date-tag original FULL CONVOS on upload or via daily reconciliation.
- [ ] Make internal/native conversation timestamp + stable conversation ID authoritative; filenames may be normalized for navigation but are not canonical identity.
- [ ] Preserve raw conversation bodies; maintain hashes/IDs so renames and moves remain traceable.
- [ ] Build detailed evolving CONVOS index/content map: dates, IDs, paths, concepts, equations/constructions, terminology transitions, attachments, and status.
- [ ] Build theory-use/provenance ledger mapping FULL CONVO passages → synthesis/derivation/solver artifact → claim/construction → relation type/confidence.
- [ ] Support bidirectional in-repo and cross-repo pointers while keeping outside legibility separate from internal theory ontology.

## P1 — action-plan persistence

- [ ] Maintain `.[⚙️_AI_FILES]/‼️_CROSS_REPO_ADMIN_ACTION_PLAN.md` as the durable high-priority operating plan.
- [ ] Update this TODO whenever the controlling conversation establishes a new durable priority/correction.
- [ ] Record meaningful completed operations in normal repo logs and update workspace resume state rather than relying on chat recall.
