#!/usr/bin/env python3
"""Audit the derived flc story feed for structural/parser failures.

This is intentionally not literary or source-text review. It catches failures
we can detect mechanically before Sites consumes the feed:
- story pages outside source-reviewed printed-page ranges;
- duplicate printed pages inside one story;
- manual anchor drift;
- leaked Tesseract TSV rows / implausible numeric metadata in display text;
- stories marked complete while expected printed pages are missing.

Exit 1 on hard failures, 0 with optional warnings otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TSV_ROW = re.compile(
    r"(?:^|\s)[1-5]\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+"
    r"\d+\s+\d+\s+\d+\s+\d+\s+-?\d+(?:\.\d+)?(?:\s|$)"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ranges(issue: dict[str, Any]) -> dict[str, tuple[int, int | None]]:
    out = {}
    ss = issue["stories"]
    for i, story in enumerate(ss):
        start = int(story["start_printed_page"])
        if i + 1 < len(ss):
            end: int | None = int(ss[i + 1]["start_printed_page"]) - 1
        else:
            end = int(issue["story_end_printed_page"]) if issue.get("story_end_printed_page") is not None else None
        out[story["id"]] = (start, end)
    return out


def numeric_garbage_lines(text: str) -> list[str]:
    bad = []
    for line in text.splitlines():
        toks = line.split()
        if len(toks) < 12:
            continue
        numeric = sum(bool(re.fullmatch(r"-?\d+(?:\.\d+)?", t.strip(".,;:()[]{}"))) for t in toks)
        if numeric / max(1, len(toks)) >= 0.45:
            bad.append(line[:240])
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args()
    root = args.root.resolve()
    catalog = load(root / "flc/_SITE_FEED/story_catalog.json")
    index = load(root / "flc/_SITE_FEED/story-index.json")

    idx_issues = {str(i["id"]): i for i in index["issues"]}
    hard: list[dict[str, Any]] = []
    warn: list[dict[str, Any]] = []

    for issue in catalog["issues"]:
        iid = str(issue["id"])
        rr = ranges(issue)
        parsed_dir = root / "flc/_PARSED_TEXT" / Path(issue["source_file"]).stem
        page_records = []
        pr = parsed_dir / "page-records.jsonl"
        if pr.exists():
            page_records = [json.loads(x) for x in pr.read_text(encoding="utf-8").splitlines() if x.strip()]
        by_pdf = {int(r["pdf_page"]): r for r in page_records}

        # Source-reviewed anchors must survive every automatic pass unchanged.
        for anchor in issue.get("manual_page_anchors", []):
            pdf = int(anchor["pdf_page"])
            expected = int(anchor["printed_page"])
            got = by_pdf.get(pdf, {}).get("printed_page")
            basis = by_pdf.get(pdf, {}).get("printed_page_basis")
            if got != expected or basis != "source-reviewed-manual-anchor":
                hard.append({
                    "type": "manual-anchor-drift", "issue": iid,
                    "pdf_page": pdf, "expected_printed": expected,
                    "got": got, "basis": basis,
                })

        ii = idx_issues.get(iid)
        if ii is None:
            hard.append({"type": "issue-missing-from-index", "issue": iid})
            continue
        story_index = {s["id"]: s for s in ii["stories"]}

        for story in issue["stories"]:
            sid = story["id"]
            sidx = story_index.get(sid)
            if sidx is None:
                hard.append({"type": "story-missing-from-index", "issue": iid, "story": sid})
                continue
            story_path = root / "flc/_SITE_FEED/stories" / f"{story['slug']}.json"
            if not story_path.exists():
                hard.append({"type": "story-file-missing", "issue": iid, "story": sid})
                continue
            rec = load(story_path)
            start, end = rr[sid]
            nums = [int(p["printed_page"]) for p in rec.get("pages", []) if p.get("printed_page") is not None]

            outside = [n for n in nums if n < start or (end is not None and n > end)]
            if outside:
                hard.append({"type": "page-outside-story-range", "story": sid, "range": [start, end], "pages": outside})
            if len(nums) != len(set(nums)):
                hard.append({"type": "duplicate-printed-page-in-story", "story": sid, "pages": nums})

            missing = rec.get("missing_printed_pages", []) or []
            complete = rec.get("text_completeness") == "page-range-complete / text-unreviewed"
            if complete and missing:
                hard.append({"type": "false-complete-status", "story": sid, "missing": missing})

            text = rec.get("display_text") or ""
            tsv_hits = len(TSV_ROW.findall(text))
            noisy = numeric_garbage_lines(text)
            if tsv_hits:
                hard.append({"type": "tesseract-tsv-leak", "story": sid, "matches": tsv_hits})
            if noisy:
                hard.append({"type": "numeric-metadata-leak", "story": sid, "example": noisy[0]})

            if text and len(text) < 120 and rec.get("text_state") != "text-not-yet-derived":
                warn.append({"type": "suspiciously-short-text", "story": sid, "characters": len(text)})

    report = {
        "schema_version": 1,
        "hard_failure_count": len(hard),
        "warning_count": len(warn),
        "hard_failures": hard,
        "warnings": warn,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
