# FLC page parse — october 2002 — inaugural issue

- Parser: `2026-09-23.2`
- Source: `flc1_lo.pdf`
- PDF/image pages: 48
- Printed page numbers detected directly: 11
- Printed page numbers resolved after conservative local interpolation: 19
- Duplicate number conflicts: 1

## Geometry correction

Each PDF page is treated as one photographed magazine page, commonly carrying two prose columns. The parser does not split those columns into separate logical pages. Tesseract's page-layout pass supplies body reading order; a separate margin-oriented pass recovers printed page numbers so the scrambled PDF sequence can be reordered.

## Review boundary

Printed page detection, column reading order, paragraphing and OCR wording remain provisional. Story start pages are applied in a separate source-guided step from the magazine contents pages.
