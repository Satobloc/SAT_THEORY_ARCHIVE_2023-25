#!/usr/bin/env python3
"""Build the public flc story-text feed from current auto-digitize output.

Fast Sites bridge: no OCR is run here. Existing derived text is packaged into
stable story records with absolute public data URLs. Facsimile remains source of
record; machine text is explicitly provisional.
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
        "schema_version": 2,
        "project_id": catalog["project_id"],
        "display_name": catalog["display_name"],
        "short_name": catalog["short_name"],
        "built_utc": built_at,
        "self_url": f"{RAW_FEED}/story-index.json",
        "latest_url": f"{RAW_FEED}/latest.json",
        "text_policy": "OCR-derived provisional text. Source facsimile remains authoritative; reviewed text may supersede this layer without changing story ids/routes.",
        "issues": [],
    }
    total_stories = 0
    text_ready = 0

    for issue in catalog["issues"]:
        source_file = issue["source_file"]
        stem = Path(source_file).stem
        issue_auto = AUTO / stem
        text_path = issue_auto / "embedded_text.txt"
        manifest_path = issue_auto / "manifest.json"
        pages: list[str] = []
        source_sha = None
        if text_path.exists():
            pages = text_path.read_text(encoding="utf-8", errors="replace").split("\f")
            if pages and not pages[-1].strip():
                pages.pop()
        if manifest_path.exists():
            source_sha = load_json(manifest_path).get("source_sha256")

        # Contents/index pages often mention many story titles and must not be
        # mistaken for story body text. Three or more title matches marks such a
        # page as navigation furniture for this first-pass extractor.
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
            "excluded_index_pages": sorted(index_pages),
            "stories": [],
        }

        for story in issue["stories"]:
            total_stories += 1
            matched = []
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

            state = "ocr-derived-provisional" if matched else "text-not-yet-derived"
            if matched:
                text_ready += 1

            rel_story = f"stories/{story['slug']}.json"
            text_url = f"{RAW_FEED}/{rel_story}" if matched else None
            first_pdf_page = matched[0]["pdf_page"] if matched else None
            record = {
                "schema_version": 2,
                "project_id": catalog["project_id"],
                "story_id": story["id"],
                "slug": story["slug"],
                "route": f"/stories/{story['slug']}/",
                "data_url": f"{RAW_FEED}/{rel_story}",
                "title": story["title"],
                "author": story["author"],
                "issue_id": issue["id"],
                "issue_title": issue["display_title"],
                "text_state": state,
                "review_state": "auto-only" if matched else "unavailable",
                "reading_order_basis": order_basis,
                "source_pdf": f"flc/{source_file}",
                "source_pdf_url": f"{RAW_FLC}/{source_file}",
                "source_pdf_sha256": source_sha,
                "facsimile_route": f"/?issue={issue['id']}&page={first_pdf_page}" if first_pdf_page else f"/?issue={issue['id']}&page=1",
                "ocr_source": str(text_path.relative_to(ROOT)) if text_path.exists() else None,
                "pages": matched,
                "display_text": "\n\n".join(p["text"] for p in matched) if matched else None,
                "frontend": {
                    "show_story_link": bool(matched),
                    "default_view": "text" if matched else "facsimile",
                    "available_views": ["text", "facsimile"] if matched else ["facsimile"],
                    "text_label": "OCR text — provisional" if matched else None
                },
                "editorial_note": "Machine-associated by visible title/running-title text. Check membership, reading order, and wording against facsimile before treating this as reviewed."
            }
            safe_write(story_dir / f"{story['slug']}.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
            issue_index["stories"].append({
                "id": story["id"],
                "slug": story["slug"],
                "title": story["title"],
                "author": story["author"],
                "route": record["route"],
                "data_url": record["data_url"],
                "text_state": state,
                "text_href": rel_story if matched else None,
                "text_url": text_url,
                "facsimile_route": record["facsimile_route"],
                "matched_pdf_pages": [p["pdf_page"] for p in matched],
                "reading_order_basis": order_basis
            })
        index["issues"].append(issue_index)

    index["summary"] = {
        "story_count": total_stories,
        "stories_with_machine_text": text_ready,
        "issues_with_text_source": sum(1 for i in index["issues"] if i["text_source_available"])
    }
    safe_write(OUT / "story-index.json", json.dumps(index, indent=2, ensure_ascii=False) + "\n")

    latest = {
        "schema_version": 2,
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
        "tunnel_status": "story feed generated / absolute frontend URLs ready",
        "frontend_instruction": "Fetch story_index_url on page load with cache disabled or a cache-busting query. If a story has text_url, make its title/byline a link to route and fetch text_url for provisional text; keep facsimile_route beside it."
    }
    safe_write(OUT / "latest.json", json.dumps(latest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(latest["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
