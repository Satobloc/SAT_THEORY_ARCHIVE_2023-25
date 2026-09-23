# First FLC page batch → live site feed

**Status:** provisional page identity, preview, and facsimile navigation. The PDF scans remain the source of record.

`site-feed.json` contains three issues and 138 ordered **PDF-page** records. The generated `pages/*.webp` files are small contact-sheet previews, not replacements for the scan. Every issue carries the exact original path and SHA-256. Every page carries its PDF page number, thumbnail path and SHA-256, two reproducible visual measurements, and separate null fields for the printed page, piece, and page role. `auto-only` is a review state, never a claim that a page's literary role has been identified.

## How the website uses this

1. Load `site-feed.json` from this directory on the archive's public `main` branch. Check `schema_version`, counts, source path allowlist, and each record's page range before display. Keep a packaged copy for offline/source outage display and say when it is used.
2. Build the issue shelf and page atlas from `issues[].pages[]`. A click selects an exact PDF page. The original PDF is linked beside it, and page rendering uses the unchanged original.
3. New reviewed records may populate `printed_page`, `piece_id`, `page_role`, and later an explicit `reading_order`/`pieces` layer. The site should distinguish PDF order from reviewed reading order and hide unreviewed prose or credits.
4. If editorial review changes a page identity or attribution, add a dated, source-located review record. Never edit the scan, and do not promote OCR guesses silently.

## Safe update path

Run `build_flc_page_feed.py` from the repository root after changing source PDFs or adding an approved issue identity. Inspect the diff and page sample before committing. The builder is deterministic for unchanged inputs and has no automated Git push. To add human review, keep it in a **separate overlay file** with editor, date, PDF locator, evidence, and a review state; the builder's auto-only records can then be regenerated without erasing editorial work. The site can load such a reviewed overlay once the contract and editorial checks are established.

The private `HSH_RESOURCES/MAG_RECON/FLC/RUN_001` editorial probe informed this boundary: booklet imposition and mixed text/image roles require direct review. Its private location is not a public website dependency. See the [FLC source desk](../README.md) and the [cross-site home](../../SITE_WORK_HOME/README.md).
