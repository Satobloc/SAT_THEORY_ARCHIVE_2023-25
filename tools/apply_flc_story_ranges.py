#!/usr/bin/env python3
"""Apply source-reviewed FLC contents-page story ranges to parsed pages.

The page parser establishes one record per photographed magazine page, attempts
to recover its printed page number, and produces column-aware OCR text. This
second pass uses the magazine's own printed contents table to assemble story
text in printed-page order.

Story boundaries are therefore source-guided. OCR wording and unresolved page
numbers remain provisional and are reported explicitly rather than guessed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--issue-id", required=True)
    ap.add_argument("--parsed-dir", type=Path, required=True)
    args = ap.parse_args()

    catalog = load_json(args.catalog)
    issue = next((i for i in catalog["issues"] if str(i["id"]) == str(args.issue_id)), None)
    if issue is None:
        raise SystemExit(f"issue {args.issue_id!r} not found")

    missing = [s["title"] for s in issue["stories"] if "start_printed_page" not in s]
    if missing:
        raise SystemExit(f"catalog missing start_printed_page for: {missing}")

    parsed_dir = args.parsed_dir
    page_records_path = parsed_dir / "page-records.jsonl"
    if not page_records_path.exists():
        raise SystemExit(f"missing parsed page records: {page_records_path}")

    all_pages: list[dict[str, Any]] = []
    for line in page_records_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            all_pages.append(json.loads(line))

    resolved = [p for p in all_pages if p.get("printed_page") is not None]
    resolved.sort(key=lambda p: (int(p["printed_page"]), int(p["pdf_page"])))
    unresolved = [p for p in all_pages if p.get("printed_page") is None]

    starts = [int(s["start_printed_page"]) for s in issue["stories"]]
    if starts != sorted(starts) or len(starts) != len(set(starts)):
        raise SystemExit(f"story start pages are not strictly increasing: {starts}")

    story_dir = parsed_dir / "stories"
    story_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for idx, story in enumerate(issue["stories"]):
        start = int(story["start_printed_page"])
        if idx + 1 < len(issue["stories"]):
            end: int | None = int(issue["stories"][idx + 1]["start_printed_page"]) - 1
        else:
            raw_end = issue.get("story_end_printed_page")
            end = int(raw_end) if raw_end is not None else None

        pages = [
            p for p in resolved
            if int(p["printed_page"]) >= start and (end is None or int(p["printed_page"]) <= end)
        ]
        pages.sort(key=lambda p: int(p["printed_page"]))

        expected_numbers = list(range(start, end + 1)) if end is not None else None
        resolved_numbers = [int(p["printed_page"]) for p in pages]
        missing_numbers = [n for n in expected_numbers if n not in resolved_numbers] if expected_numbers is not None else []

        # Do not insert unnumbered pages into reading text: their order is not
        # established. But surface strong candidates for editorial review.
        unplaced_candidates = []
        for page in unresolved:
            hits = [h for h in page.get("story_hits", []) if h.get("story_id") == story["id"]]
            if hits:
                unplaced_candidates.append({
                    "pdf_page": page["pdf_page"],
                    "story_hit_score": max(h.get("score", 0) for h in hits),
                    "reason": "story title/running-title OCR hit but printed page unresolved",
                })

        display_text = "\n\n".join(
            p.get("clean_text", "").strip() for p in pages if p.get("clean_text", "").strip()
        ) or None

        if display_text:
            if expected_numbers is not None and not missing_numbers:
                completeness = "page-range-complete / text-unreviewed"
            elif expected_numbers is not None:
                completeness = "page-range-partial / text-unreviewed"
            else:
                completeness = "open-ended-range / text-unreviewed"
        else:
            completeness = "unresolved"

        record = {
            "schema_version": 3,
            "story_id": story["id"],
            "slug": story["slug"],
            "title": story["title"],
            "author": story["author"],
            "issue_id": issue["id"],
            "start_printed_page": start,
            "end_printed_page": end,
            "boundary_basis": "source-reviewed printed contents table",
            "text_state": "page-aware-column-ocr-provisional" if display_text else "printed-pages-not-yet-resolved",
            "text_completeness": completeness,
            "review_state": "structure-source-reviewed/text-auto-only" if display_text else "unresolved",
            "reading_order_basis": "printed-page-number reconstruction + source-reviewed story starts" if display_text else None,
            "expected_printed_pages": expected_numbers,
            "resolved_printed_pages": resolved_numbers,
            "missing_printed_pages": missing_numbers,
            "unplaced_candidate_pages": unplaced_candidates,
            "pages": [
                {
                    "pdf_page": p["pdf_page"],
                    "printed_page": p["printed_page"],
                    "printed_page_basis": p["printed_page_basis"],
                    "reading_order_basis": p.get("reading_order_basis"),
                    "clean_text_sha256": p.get("clean_text_sha256"),
                }
                for p in pages
            ],
            "display_text": display_text,
            "display_text_sha256": sha256_text(display_text) if display_text else None,
            "editorial_note": "Story range comes from the printed contents table. PDF page order is ignored. Page-number recovery, column reading order, paragraphing and OCR wording remain provisional until checked against the facsimile. Unnumbered pages are surfaced as candidates rather than silently inserted."
        }
        safe_write(story_dir / f"{story['slug']}.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        if display_text:
            safe_write(story_dir / f"{story['slug']}.txt", display_text + "\n")

        records.append({
            "story_id": story["id"],
            "slug": story["slug"],
            "title": story["title"],
            "author": story["author"],
            "start_printed_page": start,
            "end_printed_page": end,
            "boundary_basis": record["boundary_basis"],
            "text_state": record["text_state"],
            "text_completeness": completeness,
            "resolved_page_count": len(pages),
            "expected_page_count": len(expected_numbers) if expected_numbers is not None else None,
            "missing_printed_pages": missing_numbers,
            "unplaced_candidate_pdf_pages": [p["pdf_page"] for p in unplaced_candidates],
            "resolved_printed_pages": resolved_numbers,
            "story_json": f"stories/{story['slug']}.json"
        })

    index_path = parsed_dir / "story-text-index.json"
    index = {
        "schema_version": 3,
        "issue_id": issue["id"],
        "issue_title": issue["display_title"],
        "story_boundary_method": "source-reviewed printed contents table",
        "page_parser": "one photographed page -> column-aware OCR -> printed page number",
        "stories": records,
    }
    safe_write(index_path, json.dumps(index, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({
        "issue_id": issue["id"],
        "stories": len(records),
        "stories_with_text": sum(1 for r in records if r["text_state"] == "page-aware-column-ocr-provisional"),
        "complete_page_ranges": sum(1 for r in records if r["text_completeness"] == "page-range-complete / text-unreviewed"),
        "boundary_method": "source-reviewed printed contents table"
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
