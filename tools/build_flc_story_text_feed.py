#!/usr/bin/env python3
"""Build the public flc story-text feed from current derived text.

Preferred source order:
1. spread-aware logical-page/story parser output;
2. legacy whole-spread OCR association as fallback.

Facsimile remains source of record; all machine text is provisional until
reviewed against the scan.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FLC = ROOT / "flc"
AUTO = FLC / "_AUTO_DIGITIZE_TEST"
PARSED = FLC / "_PARSED_TEXT"
OUT = FLC / "_SITE_FEED"
CATALOG = OUT / "story_catalog.json"
RAW_REPO = "https://raw.githubusercontent.com/Satobloc/SAT_THEORY_ARCHIVE_2023-25/main"
RAW_FEED = f"{RAW_REPO}/flc/_SITE_FEED"
RAW_FLC = f"{RAW_REPO}/flc"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("’", "'")
    s = re.sub(r"[^a-z0-9']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def safe_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def printed_page_candidates(page_text: str) -> list[int]:
    candidates: set[int] = set()
    for m in re.finditer(r"(?m)(?:^|\s)[\-–—]\s*(\d{1,3})\s*[\-–—](?:\s|$)", page_text):
        n = int(m.group(1))
        if 1 <= n <= 200:
            candidates.add(n)
    for line in page_text.splitlines():
        t = line.strip()
        if re.fullmatch(r"\d{1,3}", t):
            n = int(t)
            if 1 <= n <= 200:
                candidates.add(n)
    return sorted(candidates)


def alias_score(page_text: str, aliases: list[str]) -> int:
    p = norm(page_text)
    best = 0
    for alias in aliases:
        a = norm(alias)
        if not a:
            continue
        if a in p:
            best = max(best, len(a))
            continue
        toks = [t for t in a.split() if len(t) >= 4]
        if len(toks) >= 2 and all(t in p for t in toks):
            best = max(best, sum(map(len, toks)))
    return best


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    catalog = load_json(CATALOG)
    story_dir = OUT / "stories"
    story_dir.mkdir(parents=True, exist_ok=True)
    built_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    index: dict[str, Any] = {
        "schema_version": 3,
        "project_id": catalog["project_id"],
        "display_name": catalog["display_name"],
        "short_name": catalog["short_name"],
        "built_utc": built_at,
        "self_url": f"{RAW_FEED}/story-index.json",
        "latest_url": f"{RAW_FEED}/latest.json",
        "text_policy": "Machine-derived provisional text. Prefer spread-aware logical-page OCR when available; source facsimile remains authoritative; reviewed text may supersede this layer without changing story ids/routes.",
        "issues": [],
    }
    total_stories = 0
    text_ready = 0
    spread_ready = 0

    for issue in catalog["issues"]:
        source_file = issue["source_file"]
        stem = Path(source_file).stem
        issue_auto = AUTO / stem
        issue_parsed = PARSED / stem
        text_path = issue_auto / "embedded_text.txt"
        manifest_path = issue_auto / "manifest.json"
        parsed_manifest_path = issue_parsed / "manifest.json"
        pages: list[str] = []
        source_sha = None
        if text_path.exists():
            pages = text_path.read_text(encoding="utf-8", errors="replace").split("\f")
            if pages and not pages[-1].strip():
                pages.pop()
        if parsed_manifest_path.exists():
            source_sha = load_json(parsed_manifest_path).get("source_sha256")
        elif manifest_path.exists():
            source_sha = load_json(manifest_path).get("source_sha256")

        # Legacy contents/index exclusion. This is only used by the fallback
        # whole-spread OCR path; the spread parser builds logical pages first.
        page_story_hits: dict[int, set[str]] = {}
        for i, page_text in enumerate(pages, 1):
            for story in issue["stories"]:
                if alias_score(page_text, story.get("aliases", [story["title"]])):
                    page_story_hits.setdefault(i, set()).add(story["id"])
        index_pages = {p for p, ids in page_story_hits.items() if len(ids) >= 3}

        issue_index: dict[str, Any] = {
            "id": issue["id"],
            "display_title": issue["display_title"],
            "source_file": source_file,
            "source_pdf_url": f"{RAW_FLC}/{source_file}",
            "story_count": len(issue["stories"]),
            "text_source_available": text_path.exists(),
            "spread_parser_available": parsed_manifest_path.exists(),
            "spread_parser_manifest": f"flc/_PARSED_TEXT/{stem}/manifest.json" if parsed_manifest_path.exists() else None,
            "excluded_index_pages": sorted(index_pages),
            "stories": [],
        }

        for story in issue["stories"]:
            total_stories += 1
            parsed_story_path = issue_parsed / "stories" / f"{story['slug']}.json"
            parsed_story: dict[str, Any] | None = None
            if parsed_story_path.exists():
                candidate = load_json(parsed_story_path)
                if candidate.get("display_text"):
                    parsed_story = candidate

            matched: list[dict[str, Any]] = []
            logical_pages: list[dict[str, Any]] = []
            display_text: str | None = None
            text_source_kind: str | None = None
            text_state: str
            review_state: str
            order_basis: str | None
            first_pdf_page: int | None = None
            machine_source: str | None = None

            if parsed_story is not None:
                display_text = parsed_story["display_text"]
                logical_pages = parsed_story.get("logical_pages", [])
                text_state = parsed_story.get("text_state", "spread-split-ocr-provisional")
                review_state = parsed_story.get("review_state", "auto-only")
                order_basis = parsed_story.get("reading_order_basis", "printed-page-reconstruction")
                text_source_kind = "spread-aware-logical-page-ocr"
                machine_source = str(parsed_story_path.relative_to(ROOT))
                if logical_pages:
                    first_pdf_page = logical_pages[0].get("pdf_page")
                text_ready += 1
                spread_ready += 1
            else:
                # Fallback: legacy whole-spread OCR title association. Useful as
                # a discovery layer, but it can interleave facing pages.
                for i, page_text in enumerate(pages, 1):
                    if i in index_pages:
                        continue
                    score = alias_score(page_text, story.get("aliases", [story["title"]]))
                    if score:
                        clean = page_text.rstrip()
                        matched.append({
                            "pdf_page": i,
                            "printed_page_candidates": printed_page_candidates(page_text),
                            "match_score": score,
                            "text": clean,
                            "text_sha256": sha256_text(clean),
                        })

                matched = list({p["pdf_page"]: p for p in matched}.values())
                exact_printed = [p["printed_page_candidates"][0] for p in matched if len(p["printed_page_candidates"]) == 1]
                can_sort_printed = bool(matched) and len(exact_printed) == len(matched) and len(set(exact_printed)) == len(exact_printed)
                if can_sort_printed:
                    matched.sort(key=lambda p: p["printed_page_candidates"][0])
                    order_basis = "printed-page-candidates"
                else:
                    matched.sort(key=lambda p: p["pdf_page"])
                    order_basis = "source-pdf-order-provisional" if matched else None

                display_text = "\n\n".join(p["text"] for p in matched) if matched else None
                text_state = "whole-spread-ocr-provisional" if matched else "text-not-yet-derived"
                review_state = "auto-only" if matched else "unavailable"
                text_source_kind = "legacy-whole-spread-ocr" if matched else None
                machine_source = str(text_path.relative_to(ROOT)) if text_path.exists() else None
                first_pdf_page = matched[0]["pdf_page"] if matched else None
                if matched:
                    text_ready += 1

            rel_story = f"stories/{story['slug']}.json"
            text_url = f"{RAW_FEED}/{rel_story}" if display_text else None
            facsimile_route = f"/?issue={issue['id']}&page={first_pdf_page}" if first_pdf_page else f"/?issue={issue['id']}&page=1"

            editorial_note = (
                "Spread-aware machine reconstruction: facing pages were separated geometrically before OCR text was assembled in printed-page order. Verify page numbering, story boundaries, paragraphing, and wording against the facsimile before treating as reviewed transcription."
                if parsed_story is not None
                else "Legacy whole-spread OCR association. Facing pages may be interleaved; use as discovery/fallback text only until the spread-aware parser supersedes it."
            )

            record = {
                "schema_version": 3,
                "project_id": catalog["project_id"],
                "story_id": story["id"],
                "slug": story["slug"],
                "route": f"/stories/{story['slug']}/",
                "data_url": f"{RAW_FEED}/{rel_story}",
                "title": story["title"],
                "author": story["author"],
                "issue_id": issue["id"],
                "issue_title": issue["display_title"],
                "text_state": text_state,
                "text_source_kind": text_source_kind,
                "review_state": review_state,
                "reading_order_basis": order_basis,
                "source_pdf": f"flc/{source_file}",
                "source_pdf_url": f"{RAW_FLC}/{source_file}",
                "source_pdf_sha256": source_sha,
                "facsimile_route": facsimile_route,
                "machine_text_source": machine_source,
                "logical_pages": logical_pages,
                "legacy_matched_spreads": matched,
                "display_text": display_text,
                "display_text_sha256": sha256_text(display_text) if display_text else None,
                "frontend": {
                    "show_story_link": bool(display_text),
                    "default_view": "text" if display_text else "facsimile",
                    "available_views": ["text", "facsimile"] if display_text else ["facsimile"],
                    "text_label": "Machine text — provisional" if display_text else None,
                },
                "editorial_note": editorial_note,
            }
            safe_write(story_dir / f"{story['slug']}.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
            issue_index["stories"].append({
                "id": story["id"],
                "slug": story["slug"],
                "title": story["title"],
                "author": story["author"],
                "route": record["route"],
                "data_url": record["data_url"],
                "text_state": text_state,
                "text_source_kind": text_source_kind,
                "text_href": rel_story if display_text else None,
                "text_url": text_url,
                "facsimile_route": facsimile_route,
                "logical_pages": logical_pages,
                "matched_pdf_pages": [p["pdf_page"] for p in matched],
                "reading_order_basis": order_basis,
            })
        index["issues"].append(issue_index)

    index["summary"] = {
        "story_count": total_stories,
        "stories_with_machine_text": text_ready,
        "stories_with_spread_parsed_text": spread_ready,
        "issues_with_text_source": sum(1 for i in index["issues"] if i["text_source_available"]),
        "issues_with_spread_parser": sum(1 for i in index["issues"] if i["spread_parser_available"]),
    }
    safe_write(OUT / "story-index.json", json.dumps(index, indent=2, ensure_ascii=False) + "\n")

    latest = {
        "schema_version": 3,
        "project_id": catalog["project_id"],
        "display_name": catalog["display_name"],
        "short_name": catalog["short_name"],
        "built_utc": built_at,
        "self_url": f"{RAW_FEED}/latest.json",
        "site_bundle": "site-bundle.json",
        "site_bundle_url": f"{RAW_FEED}/site-bundle.json",
        "story_index": "story-index.json",
        "story_index_url": f"{RAW_FEED}/story-index.json",
        "summary": index["summary"],
        "tunnel_status": "story feed generated / spread-aware parser preferred when available",
        "frontend_instruction": "Fetch story_index_url on page load with cache disabled or a cache-busting query. If a story has text_url, make its title/byline a link to route and fetch text_url for provisional text; keep facsimile_route beside it. Prefer spread-split-ocr-provisional over legacy whole-spread OCR when reporting text quality."
    }
    safe_write(OUT / "latest.json", json.dumps(latest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(latest["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
