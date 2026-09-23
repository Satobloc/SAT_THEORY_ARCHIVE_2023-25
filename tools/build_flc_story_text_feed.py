#!/usr/bin/env python3
"""Build the public FLC story-text feed from current derived text.

Preferred source order:
1. page-aware column OCR, reordered by printed page number and bounded by the
   source-reviewed contents table;
2. legacy whole-page layout OCR association as fallback.

Facsimile remains source of record. Machine text is provisional until reviewed
against the scan.
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def legacy_story_text(issue: dict[str, Any], story: dict[str, Any], pages: list[str]) -> tuple[str | None, list[dict[str, Any]]]:
    """Fallback discovery text only; not trusted reading order."""
    excluded = {int(issue["contents_pdf_page"])} if issue.get("contents_pdf_page") else set()
    matched: list[dict[str, Any]] = []
    for i, page_text in enumerate(pages, 1):
        if i in excluded:
            continue
        score = alias_score(page_text, story.get("aliases", [story["title"]]))
        if score:
            clean = page_text.rstrip()
            matched.append({
                "pdf_page": i,
                "match_score": score,
                "text": clean,
                "text_sha256": sha256_text(clean),
            })
    matched.sort(key=lambda p: p["pdf_page"])
    display = "\n\n".join(p["text"] for p in matched) if matched else None
    return display, matched


def main() -> int:
    catalog = load_json(CATALOG)
    OUT.mkdir(parents=True, exist_ok=True)
    story_dir = OUT / "stories"
    story_dir.mkdir(parents=True, exist_ok=True)
    built_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    index: dict[str, Any] = {
        "schema_version": 4,
        "project_id": catalog["project_id"],
        "display_name": catalog["display_name"],
        "short_name": catalog["short_name"],
        "built_utc": built_at,
        "self_url": f"{RAW_FEED}/story-index.json",
        "latest_url": f"{RAW_FEED}/latest.json",
        "text_policy": "Machine-derived provisional text. Prefer page-aware column OCR reordered by printed page number; source facsimile remains authoritative.",
        "issues": [],
    }

    total_stories = 0
    machine_text_count = 0
    page_aware_count = 0
    complete_range_count = 0

    for issue in catalog["issues"]:
        source_file = issue["source_file"]
        stem = Path(source_file).stem
        issue_auto = AUTO / stem
        issue_parsed = PARSED / stem
        legacy_text_path = issue_auto / "embedded_text.txt"
        legacy_manifest_path = issue_auto / "manifest.json"
        parsed_manifest_path = issue_parsed / "manifest.json"
        parsed_index_path = issue_parsed / "story-text-index.json"

        legacy_pages: list[str] = []
        if legacy_text_path.exists():
            legacy_pages = legacy_text_path.read_text(encoding="utf-8", errors="replace").split("\f")
            if legacy_pages and not legacy_pages[-1].strip():
                legacy_pages.pop()

        source_sha = None
        parser_manifest = None
        if parsed_manifest_path.exists():
            parser_manifest = load_json(parsed_manifest_path)
            source_sha = parser_manifest.get("source_sha256")
        elif legacy_manifest_path.exists():
            source_sha = load_json(legacy_manifest_path).get("source_sha256")

        parsed_story_index = load_json(parsed_index_path) if parsed_index_path.exists() else None
        issue_index: dict[str, Any] = {
            "id": issue["id"],
            "display_title": issue["display_title"],
            "source_file": source_file,
            "source_pdf_url": f"{RAW_FLC}/{source_file}",
            "story_count": len(issue["stories"]),
            "contents_pdf_page": issue.get("contents_pdf_page"),
            "contents_page_review_state": catalog.get("contents_page_review_state"),
            "legacy_text_source_available": legacy_text_path.exists(),
            "page_parser_available": parsed_manifest_path.exists(),
            "page_parser_manifest": f"flc/_PARSED_TEXT/{stem}/manifest.json" if parsed_manifest_path.exists() else None,
            "page_parser_summary": {
                "parser_version": parser_manifest.get("parser_version"),
                "geometry_model": parser_manifest.get("geometry_model"),
                "printed_pages_detected_directly": parser_manifest.get("printed_pages_detected_directly"),
                "printed_pages_resolved_after_local_interpolation": parser_manifest.get("printed_pages_resolved_after_local_interpolation"),
                "duplicate_page_number_conflicts": parser_manifest.get("duplicate_page_number_conflicts"),
            } if parser_manifest else None,
            "stories": [],
        }

        parsed_status_by_slug = {}
        if parsed_story_index:
            parsed_status_by_slug = {s["slug"]: s for s in parsed_story_index.get("stories", [])}

        for story in issue["stories"]:
            total_stories += 1
            parsed_story_path = issue_parsed / "stories" / f"{story['slug']}.json"
            parsed_story = load_json(parsed_story_path) if parsed_story_path.exists() else None
            use_parsed = bool(parsed_story and parsed_story.get("display_text"))

            if use_parsed:
                display_text = parsed_story["display_text"]
                text_state = parsed_story.get("text_state", "page-aware-column-ocr-provisional")
                text_source_kind = "page-aware-column-ocr"
                review_state = parsed_story.get("review_state", "structure-source-reviewed/text-auto-only")
                order_basis = parsed_story.get("reading_order_basis")
                text_completeness = parsed_story.get("text_completeness")
                pages_meta = parsed_story.get("pages", [])
                missing_printed_pages = parsed_story.get("missing_printed_pages", [])
                unplaced_candidates = parsed_story.get("unplaced_candidate_pages", [])
                legacy_matches: list[dict[str, Any]] = []
                machine_source = str(parsed_story_path.relative_to(ROOT))
                first_pdf_page = pages_meta[0].get("pdf_page") if pages_meta else None
                page_aware_count += 1
                if text_completeness == "page-range-complete / text-unreviewed":
                    complete_range_count += 1
            else:
                display_text, legacy_matches = legacy_story_text(issue, story, legacy_pages)
                text_state = "legacy-whole-page-layout-ocr-provisional" if display_text else "text-not-yet-derived"
                text_source_kind = "legacy-whole-page-layout-ocr" if display_text else None
                review_state = "auto-only" if display_text else "unavailable"
                order_basis = "source-pdf-order-provisional" if display_text else None
                text_completeness = "unknown / potentially partial" if display_text else "unavailable"
                pages_meta = []
                missing_printed_pages = parsed_status_by_slug.get(story["slug"], {}).get("missing_printed_pages", [])
                unplaced_candidates = []
                machine_source = str(legacy_text_path.relative_to(ROOT)) if legacy_text_path.exists() else None
                first_pdf_page = legacy_matches[0]["pdf_page"] if legacy_matches else None

            if display_text:
                machine_text_count += 1

            rel_story = f"stories/{story['slug']}.json"
            text_url = f"{RAW_FEED}/{rel_story}" if display_text else None
            facsimile_route = f"/?issue={issue['id']}&page={first_pdf_page or 1}"

            if use_parsed:
                editorial_note = (
                    "Story boundary comes from the source-reviewed printed contents table. Text is assembled from page-aware OCR in recovered printed-page order. Missing printed pages and unplaced candidates are explicit; wording and page-number reconstruction remain provisional until checked against the facsimile."
                )
            else:
                editorial_note = (
                    "Legacy fallback association from whole-page OCR in source PDF order. Useful for discovery, but page order and completeness are not established. Prefer the page-aware parser when available."
                )

            record = {
                "schema_version": 4,
                "project_id": catalog["project_id"],
                "story_id": story["id"],
                "slug": story["slug"],
                "route": f"/stories/{story['slug']}/",
                "data_url": f"{RAW_FEED}/{rel_story}",
                "title": story["title"],
                "author": story["author"],
                "issue_id": issue["id"],
                "issue_title": issue["display_title"],
                "start_printed_page": story.get("start_printed_page"),
                "text_state": text_state,
                "text_source_kind": text_source_kind,
                "text_completeness": text_completeness,
                "review_state": review_state,
                "reading_order_basis": order_basis,
                "source_pdf": f"flc/{source_file}",
                "source_pdf_url": f"{RAW_FLC}/{source_file}",
                "source_pdf_sha256": source_sha,
                "facsimile_route": facsimile_route,
                "machine_text_source": machine_source,
                "pages": pages_meta,
                "missing_printed_pages": missing_printed_pages,
                "unplaced_candidate_pages": unplaced_candidates,
                "legacy_matched_pdf_pages": [p["pdf_page"] for p in legacy_matches],
                "display_text": display_text,
                "display_text_sha256": sha256_text(display_text) if display_text else None,
                "frontend": {
                    "show_story_link": bool(display_text),
                    "default_view": "text" if display_text else "facsimile",
                    "available_views": ["text", "facsimile"] if display_text else ["facsimile"],
                    "text_label": "Provisional machine text" if display_text else None,
                    "show_completeness_warning": text_completeness not in (None, "page-range-complete / text-unreviewed"),
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
                "text_completeness": text_completeness,
                "text_url": text_url,
                "facsimile_route": facsimile_route,
                "missing_printed_pages": missing_printed_pages,
                "reading_order_basis": order_basis,
            })

        index["issues"].append(issue_index)

    index["summary"] = {
        "story_count": total_stories,
        "stories_with_machine_text": machine_text_count,
        "stories_with_page_aware_text": page_aware_count,
        "stories_with_complete_page_ranges": complete_range_count,
        "issues_with_legacy_text_source": sum(1 for i in index["issues"] if i["legacy_text_source_available"]),
        "issues_with_page_parser": sum(1 for i in index["issues"] if i["page_parser_available"]),
    }
    safe_write(OUT / "story-index.json", json.dumps(index, indent=2, ensure_ascii=False) + "\n")

    latest = {
        "schema_version": 4,
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
        "tunnel_status": "story feed generated / page-aware column parser preferred when available",
        "frontend_instruction": "Fetch story_index_url fresh. If a story has text_url, link its title/byline to route and fetch text_url. Show text_completeness compactly when the recovered printed-page range is partial. Keep facsimile_route beside machine text."
    }
    safe_write(OUT / "latest.json", json.dumps(latest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(latest["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
