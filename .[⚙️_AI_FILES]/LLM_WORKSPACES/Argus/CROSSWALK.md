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
