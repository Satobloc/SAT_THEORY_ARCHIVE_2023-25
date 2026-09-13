# SAT archive tagging layer

This directory is an **additive access/provenance layer** for `SAT_THEORY_ARCHIVE_2023-25`. It does not modify source documents or declare theory status by itself.

## Immediate priority

Focus first on the **earliest currently documented and dated SAT-relevant material**, then move forward chronologically. Cross-check old-archive artifacts against the conversation archive for exact timestamps and context where saved conversations exist.

The earliest known conversation anchor presently used by the project is the 2024-03-22 conversation titled **DIMENSIONAL GRAVITY**. This is a conversation-archive anchor, not a claim that no earlier SAT-relevant material exists elsewhere.

## Per-source record

For each source, record where recoverable:

- `source_id`
- `path`
- `source_family`
- `file_type`
- `original_or_derived`
- `machine_readable`
- `extraction_path`
- `source_date`
- `date_basis` (`embedded`, `filename`, `git`, `conversation_timestamp`, `internal_statement`, `inferred`, `unknown`)
- `date_confidence`
- `author/speaker`
- `coverage` (`full-read`, `full-text-indexed`, `extracted-text-indexed`, `metadata-only`, `filename-only`, `unavailable`)
- `topic_tags`
- `terminology_tags`
- `equation_ids`
- `theory_state_ids`
- `first_appearance_candidates`
- `related_conversation_ids`
- `related_sources`
- `chronology_notes`
- `review_status`

## Source-family tags

Initial source-family vocabulary:

- `GLOSSARY`
- `STANDARD-SAT-TRANSLATION`
- `TIMELINE-HISTORY`
- `GENERAL-ARCHIVE-NOTE`
- `CONCENTRATED-SUMMARY`
- `OFF-THE-CUFF-DICTATION`
- `THEORY-ROUNDUP`
- `EQUATION-ROUNDUP`
- `DERIVATION`
- `PREDICTION`
- `AUDIT`
- `PUBLIC-FORMULATION`
- `CONVERSATION-EXPORT`
- `IMAGE-SOURCE`
- `PDF-SOURCE`
- `EXTRACTED-TEXT`

Multiple source-family tags are allowed.

## Chronology tags

- `DATED-EXACT`
- `DATED-DAY`
- `DATED-MONTH`
- `DATED-YEAR`
- `DATE-INFERRED`
- `UNDATED`
- `EARLIEST-LOCATED-CANDIDATE`
- `FIRST-APPEARANCE-CANDIDATE`
- `TIMESTAMP-VERIFIED-BY-CONVO`
- `EARLIER-SOURCE-POSSIBLE`

Never convert a candidate into an absolute first appearance solely because nothing earlier has yet been indexed.

## Claim / relation tags

Where a source explicitly supports them:

- `DEFINES`
- `CLARIFIES`
- `REFINES`
- `CORRECTS`
- `SUPERSEDES`
- `REJECTS`
- `USES-EQUATION`
- `DERIVES-EQUATION`
- `MODIFIES-EQUATION`
- `TRANSLATES-TO`
- `STANDARD-ANALOGUE`
- `ROUNDUP-CONTAINS`
- `THEORY-STATE-OF`

These are provenance-bearing relations, not automatic semantic judgments.

## Accessibility rule

Original files remain canonical. PDF/OCR/image-derived text is an access layer only. Every derived text record should point back to the original source and retain extraction status/quality information.

## Ingestion behavior

New files should be detected and tagged provisionally; derived text generated where necessary; indexes rebuilt; terminology/equation/theory-state candidate links updated; and chronology searches rerun for affected concepts. Existing source records should be refined additively rather than silently replaced.
