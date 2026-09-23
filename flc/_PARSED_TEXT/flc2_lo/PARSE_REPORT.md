# FLC spread parse — november 2002

- Parser: `2026-09-23.1`
- Source: `flc2_lo.pdf`
- Physical PDF spreads: 41
- Logical page records: 82
- Logical pages with detected/inferred printed number: 42
- Story text spans currently resolved: 2 / 8

## What changed

The parser no longer asks whole-spread OCR to pretend that two facing printed pages are one text stream. It uses OCR geometry to separate left/right logical pages first, then reconstructs printed-page order and only then assembles story text.

## Limits

- OCR wording remains provisional.
- Printed page numbers may be inferred from the facing page when parity is clear.
- Story boundaries are automatic title-anchor candidates, smoothed by printed-page order; they are not reviewed facts.
- Illustrations, ads, pull quotes, and other page furniture are not yet semantically segmented.

## Story status

- **Elders in the Love Garden** — spread-split-ocr-provisional; pages [3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 6, 7, 8, 8, 9, 10]
- **Two Skirmishes in the Never-ending War in Rural Ohio** — story-span-not-yet-resolved; pages unresolved
- **Timothy** — story-span-not-yet-resolved; pages unresolved
- **The Dreams a Sleeping Lion** — story-span-not-yet-resolved; pages unresolved
- **The Memory of Flesh** — spread-split-ocr-provisional; pages [27, 28, 28, 29, 29, 30, 30, 31, 32, 33, 38, 39, 92, 99]
- **The Recovery of Sunken Vessels** — story-span-not-yet-resolved; pages unresolved
- **A Cover Letter** — story-span-not-yet-resolved; pages unresolved
- **Concrete Afternoon** — story-span-not-yet-resolved; pages unresolved
