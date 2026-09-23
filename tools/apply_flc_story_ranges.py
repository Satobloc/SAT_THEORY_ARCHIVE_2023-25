#!/usr/bin/env python3
"""Apply reviewed contents-page story starts to spread-parsed logical pages.

The spread parser solves the geometric problem: one photographed PDF spread ->
two logical printed pages, with provisional printed page numbers and clean text.
This small second pass uses source-reviewed start-page numbers from
story_catalog.json to assemble story spans deterministically.

It does not make OCR wording authoritative. It only replaces fuzzy automatic
story-boundary guessing with the magazine's own printed contents table.
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
    logical_path = parsed_dir / "logical-pages.jsonl"
    if not logical_path.exists():
        raise SystemExit(f"missing logical page file: {logical_path}")

    logical_pages: list[dict[str, Any]] = []
    for line in logical_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            logical_pages.append(json.loads(line))

    resolved = [p for p in logical_pages if p.get("printed_page") is not None]
    resolved.sort(key=lambda p: (int(p["printed_page"]), p["pdf_page"], p["spread_side"]))

    starts = [int(s["start_printed_page"]) for s in issue["stories"]]
    if starts != sorted(starts) or len(starts) != len(set(starts)):
        raise SystemExit(f"story start pages are not strictly increasing: {starts}")

    story_dir = parsed_dir / "stories"
    story_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for idx, story in enumerate(issue["stories"]):
        start = int(story["start_printed_page"])
        if idx + 1 < len(issue["stories"]):
            end = int(issue["stories"][idx + 1]["start_printed_page"]) - 1
        else:
            end = issue.get("story_end_printed_page")
            end = int(end) if end is not None else None

        pages = [
            p for p in resolved
            if int(p["printed_page"]) >= start and (end is None or int(p["printed_page"]) <= end)
        ]
        display_text = "\n\n".join(
            p.get("clean_text", "").strip() for p in pages if p.get("clean_text", "").strip()
        ) or None

        record = {
            "schema_version": 2,
            "story_id": story["id"],
            "slug": story["slug"],
            "title": story["title"],
            "author": story["author"],
            "issue_id": issue["id"],
            "start_printed_page": start,
            "end_printed_page": end,
            "boundary_basis": "source-reviewed printed contents table",
            "text_state": "spread-split-ocr-provisional" if display_text else "logical-pages-not-yet-resolved",
            "review_state": "structure-source-reviewed/text-auto-only" if display_text else "unresolved",
            "reading_order_basis": "printed-page-reconstruction + source-reviewed story starts" if display_text else None,
            "logical_pages": [
                {
                    "logical_page_id": p["logical_page_id"],
                    "pdf_page": p["pdf_page"],
                    "spread_side": p["spread_side"],
                    "printed_page": p["printed_page"],
                    "printed_page_basis": p["printed_page_basis"],
                    "mean_ocr_confidence": p.get("mean_ocr_confidence"),
                }
                for p in pages
            ],
            "display_text": display_text,
            "display_text_sha256": sha256_text(display_text) if display_text else None,
            "editorial_note": "Story range comes from the printed contents table; page-number reconstruction and OCR wording remain provisional until checked against the facsimile."
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
            "logical_page_count": len(pages),
            "printed_pages": [p["printed_page"] for p in pages],
            "story_json": f"stories/{story['slug']}.json"
        })

    index_path = parsed_dir / "story-text-index.json"
    prior = load_json(index_path) if index_path.exists() else {}
    prior.update({
        "schema_version": 2,
        "issue_id": issue["id"],
        "issue_title": issue["display_title"],
        "story_boundary_method": "source-reviewed printed contents table",
        "stories": records,
    })
    safe_write(index_path, json.dumps(prior, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({
        "issue_id": issue["id"],
        "stories": len(records),
        "stories_with_text": sum(1 for r in records if r["text_state"] == "spread-split-ocr-provisional"),
        "boundary_method": "source-reviewed printed contents table"
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
