# The Floating Liars' Club — source and site feed

This is Nathan's literary magazine project. It is separate from the SAT/H(s)H research archive. The three `flc*_lo.pdf` scans are the unchanged source objects. The [separate FLC site](https://floating-liars-club.nathanmcknight.chatgpt.site/) is a reading surface over those objects.

| Scan | Date used by the first draft | PDF pages | Current status |
| --- | --- | ---: | --- |
| `flc1_lo.pdf` | October 2002 | 48 | Inaugural issue; page map provisional |
| `flc2_lo.pdf` | November 2002 | 41 | Issue identity provisional; page map provisional |
| `flc3_lo.pdf` | January 2003 | 49 | Issue #3; page map provisional |

## Feed and review

`_RECONSTRUCTION_V1/site-feed.json` and its `pages/` contact sheets are the **first dismantled, page-level site batch**. Each of the 138 pages has an exact PDF locator, source hash through its issue, thumbnail hash, and review fields. It is useful for a live page atlas and facsimile navigation. It is *not* a checked reading sequence or transcription: printed page numbers, story boundaries, bylines, editorial roles, and text are null until checked against the scan. PDF order may differ from reading order because of imposition.

The site reads this public feed from the archive and falls back to a matching packaged copy if the archive cannot be reached. Follow the [feed contract](_RECONSTRUCTION_V1/README.md) before changing fields or adding a reviewed layer. The original PDF link remains next to every displayed page.

Rebuild the first draft from the root of this repository with Python, PyMuPDF, and Pillow:

```sh
python '.[⚙️_AI_FILES]/TOOLS/build_flc_page_feed.py'
```

This tool writes only under `flc/_RECONSTRUCTION_V1`; it neither rewrites scans nor publishes anything by itself. Check counts, hashes, page previews, and representative scanned pages before promoting a changed batch. The [Sites work home](../SITE_WORK_HOME/README.md) holds cross-site routing and the music-site queue.

The older `_AUTO_DIGITIZE_TEST/flc1_lo` is a separate OCR/normalization trial. Its recorded diagnostic-render failure and mixed-column OCR are not treated as reviewed magazine text.
