# Argus — Provenance Crosswalk (Working)

This is a working audit artifact in the Argus workspace. It records only relationships that have been checked directly enough to merit persistence. It is not yet the canonical cross-repository provenance index.

## XW-001 — `0.239 Radians in Science`

### Source-conversation identity

**Conversation ID:** `699e4a02-26e4-832a-86ea-ad1dcaf3c4e3`

Two repository files are confirmed snapshots of the same ChatGPT conversation because they carry the identical conversation ID and title:

1. `Satobloc/SAT_THEORY_ARCHIVE_2023-25/0.239 Radians in Science — raw.json`
   - title: `0.239 Radians in Science`
   - conversation create time: 2026-02-25 01:02:10 UTC
   - snapshot/update time recorded inside export: 2026-06-11 19:27:27 UTC
   - first surviving Git ingest found in this audit: 2026-09-08 05:46:55 UTC

2. `Satobloc/HsH/DEVELOPMENT_FULL_CONVOS/SAT_CONVOS_9/0.239 Radians in Science — raw (1).json`
   - same title and conversation ID
   - same conversation create time
   - later snapshot/update time recorded inside export: 2026-09-08 22:28:18 UTC
   - first surviving Git ingest found in this audit: 2026-09-10 08:44:41 UTC

**Relationship:** same source conversation, different-time exports. The HsH copy is a later continuation snapshot; the root main-archive copy is an earlier snapshot. They must not be counted as independent evidentiary sources.

**Confidence:** exact / very high (identical conversation ID and title; differing internal update times establish snapshot relation).

### Candidate downstream focused-document family

Searches in `SAT_THEORY_ARCHIVE_2023-25` locate the explicit formulation:

`Misalignment Threshold: The 0.239 Radian Projection Constant must be recovered as the fundamental baseline for all small-angle diffraction thresholds within the HSUCV lattice.`

in a repeated focused-document family including:

- `2026/HOMESTRETCH/STREAMLINE 11MAR26.txt`
- `SAT EARLY 2026 — HOMESTRETCH/STREAMLINE 11MAR26.txt`
- `HsH-SAT Roundup 2/STREAMLINE 11MAR26.txt`
- `HYPERFOAM THEORY/HELIUM STANDARD ATOM.txt`
- `2026 discussions/HELIUM STANDARD ATOM 2.txt`
- `2026/SAT CORE — HELIUM STANDARD ATOM 2.txt`
- `SAT 2026 CONCEPTS/2026 LEGACY - HELIUM STANDARD ATOM.txt`
- `HsH-SAT Roundup 2/SAT CORE — HELIUM STANDARD ATOM 2.txt`
- `SAT 2026 ROUNDUP DOCS/2026 LEGACY - HELIUM STANDARD ATOM.txt`

The conversation began 2026-02-25, before the `11MAR26` filename date. However, a direct extraction/synthesis relationship between the conversation and these focused documents is **not yet established** because the very large HsH export is only partially retrievable/searchable through the current connector. Search silence inside that oversized file is not evidence that the wording is absent.

The surviving Git ingest of `2026/HOMESTRETCH/STREAMLINE 11MAR26.txt` found in this audit is 2026-06-01 00:02:56 UTC; this is a repository-ingest date, not the formulation date.

**Current relationship classification:** chronologically plausible source-development relationship; exact focused-document provenance unresolved.

### Audit significance

This resolves a previously ambiguous duplicate/source issue: the root main-archive raw conversation and the HsH FULL_CONVOS file are not two separate conversations or independent records. The later HsH snapshot should be preferred for completeness when technically retrievable, while the earlier main-archive snapshot remains useful as a frozen provenance state showing what the conversation contained no later than its June 11 internal export update.

### Coverage limit / next action

Obtain or parse the full 5.74 MB HsH export through a route that permits exact-text comparison across the entire conversation. Then search for the focused-document language and nearby antecedent formulations (0.239 projection constant, 14.1°/0.246 obscuration threshold, diffraction/misalignment language), recording message timestamps and exact textual transformations where found.

## XW-002 — Q-suppressed mass → three-class stability → UV Finiteness Lock

### Source-development record

**Conversation:** `Satobloc/HsH/DEVELOPMENT_FULL_CONVOS/SAT_CONVOS_10/25.08.12•25.08.12•Rating the SAT theory — raw.json`  
**Conversation ID:** `689b1815-628c-832c-b3e5-23ca5bc3302a`  
**Conversation creation date:** 2025-08-12 (internal export timestamp; filename independently encodes the same date).

The opening user turn attached a source snapshot titled `SAT 17Jun2025.txt`. The export's preserved attachment quotation explicitly contains:

- topological mass suppression `m_eff = m0 / Q`;
- the curvature-modified QMC Dirac mass term `m0/Q(φ) + αR(φ)`;
- discrete phase-lock classes `n = 1,2,3`;
- attribution of the Q construction to the June SAT.O8/QMC development layer.

A directly surviving main-archive sibling, `Satobloc/SAT_THEORY_ARCHIVE_2023-25/EARLY LOGGED/SAT OVERVIEW 17Jun2025.txt`, is internally dated `17Jun2025` and independently records a three-class/stability ceiling: exactly three stable binding/grouping patterns, only up to three-strand bindings, and the explicit falsifier that a stable four-filament bundle would contradict that SAT formulation.

**Important date distinction:** the June-17 date is document-internal provenance. The currently recovered Git history for the `EARLY LOGGED` copy begins only on 2026-09-07, so that Git timestamp must not be substituted for the document's developmental date or treated as an earlier public-release anchor.

### Downstream focused/formal family

Primary focused document checked:

- `Satobloc/SAT_THEORY_ARCHIVE_2023-25/10-31-2025 SAT FULL THEORY/PERFECT v2.txt`

That manuscript preserves the inverse-Q mass structure in the explicit expression
`m_Ψ = (T ℓ_f / c²)(1/Q)` and makes the earlier three-class/stability ceiling into a named `UV Finiteness Lock`, `Q ≤ 3`. It then adds several elements not established in the June/August source material inspected here:

- the claim that the Q ceiling is a formal UV-finiteness/stability constraint;
- Lean-4 consistency framing;
- a dimensional Q=1 anchor near `1.0073 × 10^-27 kg`;
- `R ≈ 0.007304`;
- explicit Q=2 and Q=3 ground-state mass values;
- a quadratic mass-spectrum presentation.

The same lock/reinterpretation appears across the later Satobloc/Blockwave integration family, including:

- `SATOBLOC/SATOBLOCK_inputs.txt`
- `leanchecks/SATOBLOCK_FULLTHEORY_leancheck.txt`
- `SATOBLOC/SATO-BLOCK-INT.txt`
- `SATOBLOC/SATOBLOCK-LIVE.txt`
- `SATOBLOC/SATOBLOCK_CONCEPT_DEVELOPMENT.txt`

### Relationship classification

**Source → downstream relation:** later reformulation / synthesis, not direct extraction.

The inverse-Q mass mechanism and the ≤3 stable-class ceiling demonstrably predate the checked `PERFECT v2` formulation. The later family combines those two earlier strands and promotes them into the stronger `Q ≤ 3 ⇒ UV Finiteness Lock` interpretation, then adds numerical calibration and formal-check machinery.

**Confidence:** high that the June/August QMC + three-class material is a developmental antecedent of the later Q/UV-lock family; medium-high that `PERFECT v2` directly descends from this exact conversation branch, because a message-level generation/edit trail for `PERFECT v2` itself has not yet been recovered.

### Reverse mapping

The June/August source layer feeds multiple later focused artifacts rather than a single manuscript. Conversely, `PERFECT v2` condenses at least two earlier components that should remain separately traceable:

1. Q-dependent mass suppression (`m0/Q`);
2. the three-class / no-stable-fourth-class constraint.

The later `UV Finiteness Lock` should therefore not be back-projected wholesale into the June source merely because both antecedent ingredients are present there.

### Mathematical-vetting note

The move from `Q ≤ 3` as a stable-state/topological ceiling to ultraviolet finiteness, renormalisability, or asymptotic safety is a separate mathematical claim and needs an explicit field-theoretic argument. A finite set of stable topological sectors does not by itself control high-momentum loop behavior. Treat the `UV Finiteness Lock` as an **OPEN / UNDERDEFINED vetting candidate** until the archive yields the missing argument or it is reformulated more narrowly.

This item is not currently exposed as its own row in `..[🎛️_NATHAN_DASH]/..Derivation_Index.md`; it merits a future dedicated derivation-index entry distinct from M13 (`Z3 Fusion Gate`).

### Orphan / breadcrumb note

`EARLY LOGGED/SAT OVERVIEW 17Jun2025.txt` and `EARLY LOGGED/SAT_D3_2_CurvedEigenmodes.py` are provenance-significant source artifacts whose current folder/late Git ingest does not advertise their relationship to the later Q/UV-lock manuscript family. Leave them in place, but add them to future breadcrumb/derivation mapping rather than relying on the `EARLY LOGGED` label.

### Coverage limits / next action

- The August-12 FULL_CONVO and its preserved opening attachment material were directly inspected in this audit.
- The June `SAT OVERVIEW 17Jun2025.txt` sibling and later `PERFECT v2` were directly inspected.
- Exact first emergence of the phrase `UV Finiteness Lock` has not yet been chronologically isolated.
- Current Git ingest dates do not establish original composition/public-exposure dates for the June or October-labeled documents.
- Next provenance step: date the earliest Satobloc/Blockwave file containing the lock phrase and, if possible, recover the conversation turn that performs the conceptual promotion from three-class stability to a UV claim.
