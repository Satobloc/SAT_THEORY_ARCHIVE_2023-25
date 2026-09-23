# FLC spread parse — january 2003 — issue #3

- Parser: `2026-09-23.1`
- Source: `flc3_lo.pdf`
- Physical PDF spreads: 49
- Logical page records: 98
- Logical pages with detected/inferred printed number: 43
- Story text spans currently resolved: 2 / 7

## What changed

The parser no longer asks whole-spread OCR to pretend that two facing printed pages are one text stream. It uses OCR geometry to separate left/right logical pages first, then reconstructs printed-page order and only then assembles story text.

## Limits

- OCR wording remains provisional.
- Printed page numbers may be inferred from the facing page when parity is clear.
- Story boundaries are automatic title-anchor candidates, smoothed by printed-page order; they are not reviewed facts.
- Illustrations, ads, pull quotes, and other page furniture are not yet semantically segmented.

## Story status

- **A Buried Mystery** — story-span-not-yet-resolved; pages unresolved
- **The Gilgamesh Golem** — spread-split-ocr-provisional; pages [5, 5, 5]
- **The Nature of Fireflies** — story-span-not-yet-resolved; pages unresolved
- **Work and Play** — spread-split-ocr-provisional; pages [6, 7, 8, 10, 14, 21, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34, 35, 39, 40, 41, 41, 42, 42, 43, 46, 47, 84, 88]
- **Strange Forms of the Surfacing Dead** — story-span-not-yet-resolved; pages unresolved
- **The Man Who Died a Thousand Deaths** — story-span-not-yet-resolved; pages unresolved
- **Save the Kildans** — story-span-not-yet-resolved; pages unresolved
