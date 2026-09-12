# Cross-Repository Maintenance Map

Status: active archive machinery / point-of-use wayfinding

Purpose: show where automatic maintenance and human-reviewed navigation belong across the three SAT/H(s)H repositories. This is not theory content and does not establish claim status.

## Core rule

Do not force identical machinery onto repositories with different jobs.

There are **two public cross-linking repositories** and **one private reference repository**:

**`Satobloc/HsH` ↔ `Satobloc/SAT_THEORY_ARCHIVE_2023-25`**

These two public project-record repositories should cross-link bidirectionally when useful for provenance, chronology, navigation, or development traceability.

`Satobloc/HSH_RESOURCES` is private/reference-only. It may retain exact archived-copy paths and hashes internally, but public HsH/archive work should not depend on private HSH_RESOURCES links. External evidence crosses that boundary as a Chicago-style citation to the original source, an attributed quotation/extract with location information, or a sourced summary/paraphrase; private/raw project data should be represented by an appropriate public-safe extract or summary with provenance.

| Repository | Primary role | Automatic layer | Human/LLM-reviewed layer | Point-of-use outbound route |
|---|---|---|---|---|
| `Satobloc/SAT_THEORY_ARCHIVE_2023-25` | Historical/developmental preservation, provenance, mathematical quarry | structural indexing; sharded index-history maintenance; bounded Archive Admin tasks | derivation/provenance maps, folder summaries, historical interpretation | current HsH/provenance ↔ `Satobloc/HsH`; external evidence → public citation/quotation/summary derived from private reference work |
| `Satobloc/HsH` | Live synthesis, formalization, audits, source-conversation preservation | structural index; developmental-conversation date tagging; LIVE/development chronology | synthesis status, internal provenance, equation/dependency/citation ledgers | historical source ↔ main archive; external evidence → Chicago citation/original-source identifier at point of use |
| `Satobloc/HSH_RESOURCES` | Private external papers, datasets, extracted text, empirical/prior-art evidence | PDF/OCR extraction; structural resource index; bibliography-coverage accounting; analytics | bibliographic metadata, read status, relevance/comparison judgment, citation handoff | internal handoff ID → public citation/quotation/summary at the HsH/archive point of use; private repo link is not the public route |

## Automatic maintenance contracts

### SAT_THEORY_ARCHIVE_2023-25

Structural index maintenance is intentionally conservative rather than push-on-every-file.

- Tool: `.[⚙️_AI_FILES]/TOOLS/index_folder.py`
- Config: `.[⚙️_AI_FILES]/CONFIG/folder_indexer_full_archive.txt`
- Workflow: `.github/workflows/full-archive-index.yml`
- Automatic cadence: Monday / Wednesday / Friday scheduled full refresh, plus manual dispatch.
- Local/current index: `..findex.txt`
- Human router: `..[🎛️_NATHAN_DASH]/🗄️_ARCHIVE_INDEX.txt`
- Historical index shards/state: `.[⚙️_AI_FILES]/INDEXES/archive_index_history/`
- Logs: `.[⚙️_AI_FILES]/LOGS/folder_indexer/` and `.[⚙️_AI_FILES]/LOGS/archive_index_router/`

The full-index workflow intentionally does **not** use `[skip archive-admin]`; its generated commit should trigger Archive Admin so any appended Dashboard index block is absorbed into the sharded history router. Generated-source conflicts are not resolved by rebasing over newer source changes.

For mixed historical folders, do not automatically rename every apparent conversation file. Conversation dating should be applied only to deliberately designated conversation-export locations using the date utility/request machinery. HsH is the preferred home for automatically maintained conversation chronology.

Archive-side shared methods, reconstruction aids, and cross-repo maintenance notes live in `.[⚙️_AI_FILES]/SHARED_RESOURCES/`. Active current-build cross-agent coordination belongs in `Satobloc/HsH/WORKSPACES/COMMON/`.

### HsH

- Date tool: `tools/date_conversation_exports.py`
- Chronology tool: `tools/index_conversation_chronology.py`
- Structural tool: `tools/index_archive.py`
- Workflow: `.github/workflows/maintain-navigation.yml`
- Development chronology: `indexes/CONVERSATION_CHRONOLOGY.md`
- LIVE chronology: `indexes/LIVE_CONVERSATION_CHRONOLOGY.md`
- Date manifests: `indexes/manifests/`
- Structural index: `indexes/STRUCTURAL_INDEX.md` / `indexes/index-state.json`
- Focused working areas: `WORKSPACES/<name>/`
- Cross-agent common room: `WORKSPACES/COMMON/`

Policy:

- stable `DEVELOPMENT_FULL_CONVOS/` exports may be automatically date-prefixed using first/last active-branch user/assistant message dates in `America/New_York`;
- mutable `LIVE CONVOS/` receives generated date/chronology metadata without automatic filename renaming;
- collisions or unparseable files remain visible in manifests rather than being silently forced;
- generated maintenance commits carry `[skip hsh-maintenance]`;
- semantic theory status is never inferred from structural/date machinery;
- workspaces are noncanonical workbenches; durable results must be promoted into the appropriate provenance/timeline, ledger, audit, synthesis, formalization, or index layer.

### HSH_RESOURCES

- Extraction: `tools/extract_papers.py`
- OCR / image-text extraction: `tools/extract_image_text.py`
- Accessibility audit: `tools/audit_accessibility.py`
- Structural index: `tools/index_papers.py`
- Upload workflow: `.github/workflows/extract-papers.yml`
- Structural outputs: `indexes/RESOURCE_INDEX.md`, `indexes/index-state.json`
- Extracted page text: `derived/text/`
- Extraction manifests: `derived/manifests/`
- Bibliography coverage: `tools/update_bibliography_coverage.py`
- Coverage workflow: `.github/workflows/bibliography-coverage.yml`
- Generated coverage report: `indexes/BIBLIOGRAPHY_COVERAGE.md`
- Human bibliography/citation handoff: `indexes/HUMAN_BIBLIOGRAPHY.md`

The coverage reporter may say what structurally indexed PDF content is not yet represented in the human bibliography. It must not decide relevance, citation need, novelty, validity, or theoretical authority.

## Citation handoff — private source side ↔ public theory side

A real external citation need has two point-of-use surfaces with different visibility:

**Private source/retrieval side**
`Satobloc/HSH_RESOURCES/indexes/HUMAN_BIBLIOGRAPHY.md` → citation handoff register. This side may record exact HSH_RESOURCES paths, hashes, extraction locations, and review notes.

**Public theory side**
`Satobloc/HsH/ledgers/CITATION_LEDGER.md` and the actual public document/claim being supported. This side should expose the original bibliographic source in Chicago style (or an appropriately sourced quotation/extract/summary), not a private HSH_RESOURCES repository link.

Use the same stable ID on both sides:

`CITE-YYYY-NNN`

Required fields should include:

- private-side exact HSH_RESOURCES source path/hash when useful for retrieval;
- public-side original source identity: authorship/title/year plus DOI, arXiv ID, journal, dataset identifier, or other stable external locator as available;
- exact HsH destination path and, where possible, section/claim/equation anchor;
- citation role: `STD`, `EMPIRICAL`, `PRIOR_ART`, `COMPARISON`, `CONSTRAINT`, or `DELIBERATE_IMPORT`;
- why the citation is needed;
- status: `NEEDED`, `PLACED`, `VERIFIED`, `REJECTED`, or `SUPERSEDED`;
- exact page/location or quoted/summarized support where relevant;
- verification/backlink notes.

Do not populate citation obligations automatically from keyword or embedding resemblance. A workflow may surface a candidate or missing-coverage item; an LLM/human reviewer must decide that an actual citation relationship exists.

## Theorybuilding boundary

The internal Fundamental Intuitions and SAT → SAT-O → 4DHH → Blockwave/Satobloc → H(s)H genealogy are the generative theorybuilding line.

External sources are used for proper credit, established definitions/results, empirical evidence and constraints, prior-art comparison, independent-development assessment, and deliberately labeled imports. Discovery of a related external research programme does not silently replace the internal construction with that programme's assumptions.

This boundary is repeated at the **point of use** in both:

- `Satobloc/HSH_RESOURCES/indexes/HUMAN_BIBLIOGRAPHY.md` (private research/retrieval side)
- `Satobloc/HsH/ledgers/CITATION_LEDGER.md` (public point-of-use side)

## Internal provenance is not external citation

Keep these separate:

- **Internal provenance:** where a statement/equation/construction developed inside SAT/H(s)H. This is where HsH ↔ historical-archive cross-linking is especially useful.
- **External citation:** what outside result, observation, constraint, comparison, or antecedent should be credited at the statement's current point of use. This should resolve publicly to the original external source/citation, not to the private resource warehouse.

A synthesis item can and often should carry both relationships.

## Validation checklist

A maintenance pass should be able to answer these without deep source archaeology:

1. Does a newly uploaded item enter the correct structural index automatically?
2. Does a parseable developmental conversation acquire/expose reliable Eastern-time date metadata automatically?
3. Are mutable LIVE files protected from unnecessary rename churn?
4. Can a reader standing in HsH follow internal provenance into the historical archive and back without depending on HSH_RESOURCES?
5. Does every externally supported public claim expose a usable original-source citation/identifier or sourced quotation/summary rather than a dead/private repository link?
6. Can a private-side reviewer recover the exact archived resource copy/hash associated with a `CITE-YYYY-NNN` handoff?
7. Can machine reports expose unprocessed bibliography coverage without calling it irrelevant?
8. Are source artifacts, generated catalogs, logs, human-reviewed metadata, and semantic judgments still distinct layers?
9. Do generated commits avoid workflow loops and avoid rebasing generated artifacts over newer source changes?
10. Are cross-agent workspace handoffs promoted to durable repository layers rather than becoming a shadow synthesis in the common room?

## Failure posture

Maintenance failure should preserve evidence and fail or warn visibly rather than silently rewriting around an error.

- collisions: retain manifest/status and do not force rename;
- parse failures: retain source and record skipped/unparseable status;
- concurrent source push: prefer a later fresh maintenance pass over rebasing generated outputs onto a newer tree;
- incomplete structural traversal: mark coverage as partial;
- missing citation counterpart: leave status unresolved rather than inventing a backlink;
- private-only source reference in public work: replace with a proper original-source citation, sourced quotation/extract, or public-safe summary rather than publishing a nonfunctional dependency.
