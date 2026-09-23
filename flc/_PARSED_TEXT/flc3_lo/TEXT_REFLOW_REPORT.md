# FLC text reflow pass

- Version: `2026-09-23.2`
- Pages reflowed: 48
- Layout counts: `{"single-or-mixed-block-crop": 16, "two-column-block-crop": 28, "word-fallback": 4}`
- TSV parser: literal physical-line/tab parser; stray OCR quote marks cannot consume following TSV records.
- Main method: discover text blocks on the page, crop them from the scan, OCR each crop independently, then order left-column blocks before right-column blocks.
- Full-width/centre blocks on two-column pages are preserved as supplemental metadata rather than silently injected into prose.
- Source scans and printed-page assignments are unchanged.
- Wording remains provisional until checked against the facsimile.
