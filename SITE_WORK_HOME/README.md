# Sites work home

This folder is the archive's routing desk for Nathan's Sites work. It is a plan and handoff, not a website deploy directory or a second copy of the scans. Each site retains its own source repository and publishing history.

| Public surface | Purpose | Source feed / controlling folder | Next work |
| --- | --- | --- | --- |
| [Glass Sausage Factory](https://glass-sausage-factory.nathanmcknight.chatgpt.site/) | SAT/H(s)H research record | `Satobloc/HsH/PUBLIC_SITE/`, theory controls in HsH | Smaller default type; a quiet large-text toggle; links under Nathan's other projects. |
| [The Floating Liars' Club](https://floating-liars-club.nathanmcknight.chatgpt.site/) | Literary magazine reading and reconstruction | [`../flc/_RECONSTRUCTION_V1/`](../flc/_RECONSTRUCTION_V1/) over unchanged `flc/*.pdf` | Review printed order, contents, contributor roles; promote checked story-level reading paths. |
| Music site | Dedicated listening / release home, **queued** | [Music-site brief](MUSIC_SITE_PLAN.md); Nathan's supplied Spotify routes | Design and build when release identities and artwork are reviewed. |

## Source to site, with one owner per fact

```text
original artifact / controlling repo
  -> derived batch with hashes, locators, and review state
  -> small public JSON feed + images when useful
  -> site reads the feed and keeps a dated fallback
  -> human checks the live route; corrections return to the source batch
```

Use source links on the public page. Keep classification guesses and raw OCR distinct from reviewed text. Prefer page-specific updates over copying complete PDFs into multiple Sites repositories. FLC's contract and builder are documented in its folder. HsH public site decisions belong in `HsH/PUBLIC_SITE/SITE_DEVELOPMENT_WORK_LOG.md` as well as the Sites checkout.

## Public and private layers

The public sites and this work home are discoverable. Sensitive scratch, experimental drafts, editorial feedback, and unpublished cross-project material belong in the **private** HSH_RESOURCES repository under `PRIVATE_WORKSPACE/`, with `PRIVATE_WORKSPACE/MAG_RECON/` for magazine work and `PRIVATE_WORKSPACE/SITES/` for cross-site work. Public pages should not fetch private repo files or expose private folder links. An owner-only workshop Site can eventually provide a convenient front door, with its access gate checked before linking it from a public home.

The public Glass Sausage Factory is meant to remain broadly inspectable. A private workshop is for drafts and routing, not a place to hide the public research record.
