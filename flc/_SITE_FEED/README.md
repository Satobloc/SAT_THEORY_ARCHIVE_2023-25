# flc live site feed

This directory is the public, machine-readable bridge between the reconstructed archive and the `floating liars' club` site.

Frontend entry order:

1. `latest.json`
2. `site-bundle.json`
3. `story-index.json`
4. `stories/<slug>.json`
5. source PDFs / facsimile

`story-index.json` and the per-story files are derived from the current auto-digitize text layer. Their wording and page order are provisional until reviewed; every story record retains source identity and page membership.

The intended reader behavior is editorial-first: story titles/bylines become links when `text_href` is present, while facsimile remains available beside the text. The reconstruction-status route should expose feed version/timestamp and whether the frontend is reading the live backend or a packaged fallback.
