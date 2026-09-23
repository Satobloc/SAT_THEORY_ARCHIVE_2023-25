# FLC spread parse — october 2002 — inaugural issue

- Parser: `2026-09-23.1`
- Source: `flc1_lo.pdf`
- Physical PDF spreads: 48
- Logical page records: 96
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

- **The Lion in the Parking Lot** — story-span-not-yet-resolved; pages unresolved
- **The Dark Continent Episodes** — spread-split-ocr-provisional; pages [2, 2, 2, 2, 2, 3, 3, 4, 4, 4, 4, 5, 5, 6, 7, 8, 9, 10, 11, 12, 13]
- **Eye of the Angry God** — spread-split-ocr-provisional; pages [18, 19, 19, 32, 33, 38, 42, 43, 43, 50, 51]
- **Walking Along the Möbius Strip** — story-span-not-yet-resolved; pages unresolved
- **The Money Pig** — story-span-not-yet-resolved; pages unresolved
- **Eyesores** — story-span-not-yet-resolved; pages unresolved
- **Spytown** — story-span-not-yet-resolved; pages unresolved
