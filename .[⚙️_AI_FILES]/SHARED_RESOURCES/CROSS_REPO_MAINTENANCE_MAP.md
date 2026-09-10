# Cross-Repository Maintenance Map

Status: active archive machinery / point-of-use wayfinding

Purpose: show where automatic maintenance and human-reviewed navigation belong across the three SAT/H(s)H repositories. This is not theory content and does not establish claim status.

## Core rule

Do not force identical machinery onto repositories with different jobs.

| Repository | Primary role | Automatic layer | Human/LLM-reviewed layer | Point-of-use outbound route |
|---|---|---|---|---|
| `Satobloc/SAT_THEORY_ARCHIVE_2023-25` | Historical/developmental preservation, provenance, mathematical quarry | structural indexing; sharded index-history maintenance; bounded Archive Admin tasks | derivation/provenance maps, folder summaries, historical interpretation | current HsH → `Satobloc/HsH`; external evidence/citations → `Satobloc/HSH_RESOURCES` |
| `Satobloc/HsH` | Live synthesis, formalization, audits, source-conversation preservation | structural index; developmental-conversation date tagging; LIVE/development chronology | synthesis status, internal provenance, equation/dependency/citation ledgers | external citation/source record → `Satobloc/HSH_RESOURCES/indexes/HUMAN_BIBLIOGRAPHY.md`; historical source → main archive |
| `Satobloc/HSH_RESOURCES` | External papers, datasets, extracted text, empirical/prior-art evidence | PDF extraction; structural resource index; bibliography-coverage accounting | bibliographic metadata, read status, relevance/comparison judgment, citation handoff | actual theory point of use → `Satobloc/HsH/ledgers/CITATION_LEDGER.md` |

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

### HsH

- Date tool: `tools/date_conversation_exports.py`
- Chronology tool: `tools/index_conversation_chronology.py`
- Structural tool: `tools/index_archive.py`
- Workflow: `.github/workflows/maintain-navigation.yml`
- Development chronology: `indexes/CONVERSATION_CHRONOLOGY.md`
- LIVE chronology: `indexes/LIVE_CONVERSATION_CHRONOLOGY.md`
- Date manifests: `indexes/manifests/`
- Structural index: `indexes/STRUCTURAL_INDEX.md` / `indexes/index-state.json`

Policy:

- stable `DEVELOPMENT_FULL_CONVOS/` exports may be automatically date-prefixed using first/last active-branch user/assistant message dates in `America/New_York`;
- mutable `LIVE CONVOS/` receives generated date/chronology metadata without automatic filename renaming;
- collisions or unparseable files remain visible in manifests rather than being silently forced;
- generated maintenance commits carry `[skip hsh-maintenance]`;
- semantic theory status is never inferred from structural/date machinery.

### HSH_RESOURCES

- Extraction: `tools/extract_papers.py`
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

## Citation handoff — source side ↔ theory side

A real external citation need has two point-of-use surfaces:

**Source side**
`Satobloc/HSH_RESOURCES/indexes/HUMAN_BIBLIOGRAPHY.md` → `Citation handoff register`

**Theory side**
`Satobloc/HsH/ledgers/CITATION_LEDGER.md`

Use the same stable ID on both sides:

`CITE-YYYY-NNN`

Required fields should include:

- exact HSH_RESOURCES source path;
- exact HsH destination path and, where possible, section/claim/equation anchor;
- citation role: `STD`, `EMPIRICAL`, `PRIOR_ART`, `COMPARISON`, `CONSTRAINT`, or `DELIBERATE_IMPORT`;
- why the citation is needed;
- status: `NEEDED`, `PLACED`, `VERIFIED`, `REJECTED`, or `SUPERSEDED`;
- verification/backlink notes.

Do not populate citation obligations automatically from keyword or embedding resemblance. A workflow may surface a candidate or missing-coverage item; an LLM/human reviewer must decide that an actual citation relationship exists.

## Theorybuilding boundary

The internal Fundamental Intuitions and SAT → SAT-O → 4DHH → Blockwave/Satobloc → H(s)H genealogy are the generative theorybuilding line.

External sources are used for proper credit, established definitions/results, empirical evidence and constraints, prior-art comparison, independent-development assessment, and deliberately labeled imports. Discovery of a related external research programme does not silently replace the internal construction with that programme's assumptions.

This boundary is repeated at the **point of use** in both:

- `Satobloc/HSH_RESOURCES/indexes/HUMAN_BIBLIOGRAPHY.md`
- `Satobloc/HsH/ledgers/CITATION_LEDGER.md`

## Internal provenance is not external citation

Keep these separate:

- **Internal provenance:** where a statement/equation/construction developed inside SAT/H(s)H.
- **External citation:** what outside result, observation, constraint, comparison, or antecedent should be credited at the statement's current point of use.

A synthesis item can and often should carry both relationships.

## Validation checklist

A maintenance pass should be able to answer these without deep source archaeology:

1. Does a newly uploaded item enter the correct structural index automatically?
2. Does a parseable developmental conversation acquire/expose reliable Eastern-time date metadata automatically?
3. Are mutable LIVE files protected from unnecessary rename churn?
4. Can a reader standing in HsH reach the exact external citation record from the point of use?
5. Can a reviewer standing in the resource bibliography see where a source is needed in HsH?
6. Can machine reports expose unprocessed bibliography coverage without calling it irrelevant?
7. Are source artifacts, generated catalogs, logs, human-reviewed metadata, and semantic judgments still distinct layers?
8. Do generated commits avoid workflow loops and avoid rebasing generated artifacts over newer source changes?

## Failure posture

Maintenance failure should preserve evidence and fail or warn visibly rather than silently rewriting around an error.

- collisions: retain manifest/status and do not force rename;
- parse failures: retain source and record skipped/unparseable status;
- concurrent source push: prefer a later fresh maintenance pass over rebasing generated outputs onto a newer tree;
- incomplete structural traversal: mark coverage as partial;
- missing citation counterpart: leave status unresolved rather than inventing a backlink.
