#!/usr/bin/env python3
"""Conservatively solve FLC photographed-page -> printed-page assignments.

Evidence hierarchy:
1. source-reviewed manual anchors;
2. direct visible-margin page-number OCR, when compatible with story evidence;
3. exact local +/-1 runs bracketed by stronger assignments;
4. source-reviewed story ranges from the issue contents table;
5. exact set-completion/local-run deductions inside a story.

The solver is deliberately incomplete rather than inventive. It clears
contradictory assignments, resolves safe duplicates, and leaves ambiguous pages
unassigned with candidate metadata.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

SOLVER_VERSION = "2026-09-23.1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def issue_story_ranges(issue: dict[str, Any]) -> dict[str, tuple[int, int | None]]:
    stories = issue["stories"]
    out: dict[str, tuple[int, int | None]] = {}
    for i, story in enumerate(stories):
        start = int(story["start_printed_page"])
        if i + 1 < len(stories):
            end: int | None = int(stories[i + 1]["start_printed_page"]) - 1
        else:
            end = int(issue["story_end_printed_page"]) if issue.get("story_end_printed_page") is not None else None
        out[story["id"]] = (start, end)
    return out


def recompute_story_hits(record: dict[str, Any], issue: dict[str, Any]) -> list[dict[str, Any]]:
    text = norm(record.get("clean_text", ""))
    hits: dict[str, int] = {}
    for hit in record.get("story_hits", []):
        hits[hit["story_id"]] = max(hits.get(hit["story_id"], 0), int(hit.get("score", 0)))
    for story in issue["stories"]:
        best = hits.get(story["id"], 0)
        for alias in story.get("aliases", [story["title"]]):
            a = norm(alias)
            if a and a in text:
                best = max(best, len(a))
        if best:
            hits[story["id"]] = best
    by_id = {s["id"]: s for s in issue["stories"]}
    return sorted([
        {"story_id": sid, "slug": by_id[sid]["slug"], "title": by_id[sid]["title"], "score": score}
        for sid, score in hits.items() if sid in by_id
    ], key=lambda h: (-h["score"], h["story_id"]))


def unique_story(record: dict[str, Any], issue: dict[str, Any]) -> str | None:
    if int(record["pdf_page"]) <= int(issue.get("contents_pdf_page") or 0):
        return None
    hits = record.get("solver_story_hits", [])
    if not hits:
        return None
    top = hits[0]
    if int(top.get("score", 0)) < 8:
        return None
    if len(hits) > 1 and int(hits[1].get("score", 0)) >= int(top.get("score", 0)) - 3:
        return None
    return top["story_id"]


def compatible(record: dict[str, Any], printed: int, ranges: dict[str, tuple[int, int | None]], issue: dict[str, Any]) -> bool:
    sid = unique_story(record, issue)
    if sid is None:
        return True
    start, end = ranges[sid]
    return printed >= start and (end is None or printed <= end)


def clear_assignment(record: dict[str, Any], reason: str) -> None:
    if record.get("printed_page") is not None:
        record.setdefault("page_order_solver", {}).setdefault("cleared", []).append({
            "printed_page": record.get("printed_page"),
            "basis": record.get("printed_page_basis"),
            "reason": reason,
        })
    record["printed_page"] = None
    record["printed_page_basis"] = "solver-unresolved"


def candidate_score(record: dict[str, Any], number: int, issue: dict[str, Any], ranges: dict[str, tuple[int, int | None]]) -> float:
    score = 0.0
    for c in record.get("page_number_candidates", []):
        if int(c.get("number", -1)) == number:
            score = max(score, float(c.get("score", 0)) * 10 + min(10, float(c.get("confidence", 0)) / 10))
    basis = record.get("printed_page_basis")
    if record.get("printed_page") == number:
        if basis == "source-reviewed-manual-anchor":
            score += 1000
        elif basis == "outer-margin-ocr":
            score += 35
        elif basis == "exact-local-sequence-interpolation":
            score += 18
        elif basis and basis.startswith("solver-"):
            score += 15
    if compatible(record, number, ranges, issue):
        score += 25
    else:
        score -= 200
    return score


def resolve_duplicates(records: list[dict[str, Any]], issue: dict[str, Any], ranges: dict[str, tuple[int, int | None]], report: dict[str, Any]) -> None:
    by_num: dict[int, list[dict[str, Any]]] = {}
    for r in records:
        if r.get("printed_page") is not None:
            by_num.setdefault(int(r["printed_page"]), []).append(r)
    for number, contenders in sorted(by_num.items()):
        if len(contenders) < 2:
            continue
        ranked = sorted(((candidate_score(r, number, issue, ranges), r) for r in contenders), key=lambda x: x[0], reverse=True)
        winner_score, winner = ranked[0]
        second = ranked[1][0]
        manual = winner.get("printed_page_basis") == "source-reviewed-manual-anchor"
        if manual or winner_score >= second + 15:
            for _score, r in ranked[1:]:
                clear_assignment(r, f"duplicate printed page {number}; stronger contender pdf {winner['pdf_page']}")
            report["duplicate_resolutions"].append({"printed_page": number, "kept_pdf_page": winner["pdf_page"], "cleared_pdf_pages": [r["pdf_page"] for _, r in ranked[1:]]})
        else:
            for _score, r in ranked:
                clear_assignment(r, f"duplicate printed page {number}; no decisive contender")
            report["duplicate_resolutions"].append({"printed_page": number, "kept_pdf_page": None, "cleared_pdf_pages": [r["pdf_page"] for _, r in ranked]})


def used_numbers(records: list[dict[str, Any]]) -> set[int]:
    return {int(r["printed_page"]) for r in records if r.get("printed_page") is not None}


def interpolate_bracketed(records: list[dict[str, Any]], issue: dict[str, Any], ranges: dict[str, tuple[int, int | None]], report: dict[str, Any]) -> None:
    changed = True
    while changed:
        changed = False
        known = [(i, int(r["printed_page"])) for i, r in enumerate(records) if r.get("printed_page") is not None]
        used = used_numbers(records)
        for (i, a), (j, b) in zip(known, known[1:]):
            gap = j - i
            if gap <= 1 or abs(b - a) != gap:
                continue
            step = 1 if b > a else -1
            proposed = [(k, a + step * (k - i)) for k in range(i + 1, j)]
            if any(n in used for _, n in proposed):
                continue
            if not all(compatible(records[k], n, ranges, issue) for k, n in proposed):
                continue
            for k, n in proposed:
                if records[k].get("printed_page") is None:
                    records[k]["printed_page"] = n
                    records[k]["printed_page_basis"] = "solver-exact-bracketed-sequence"
                    report["sequence_assignments"].append({"pdf_page": records[k]["pdf_page"], "printed_page": n, "basis": "exact-bracketed"})
                    changed = True


def complete_story_runs(records: list[dict[str, Any]], issue: dict[str, Any], ranges: dict[str, tuple[int, int | None]], report: dict[str, Any]) -> None:
    for story in issue["stories"]:
        sid = story["id"]
        start, end = ranges[sid]
        if end is None:
            continue
        expected = list(range(start, end + 1))
        assigned = {int(r["printed_page"]): r for r in records if r.get("printed_page") in expected}
        missing = [n for n in expected if n not in assigned]
        candidates = [r for r in records if r.get("printed_page") is None and unique_story(r, issue) == sid]
        if not missing or not candidates:
            continue

        if len(missing) == 1 and len(candidates) == 1:
            r = candidates[0]
            r["printed_page"] = missing[0]
            r["printed_page_basis"] = "solver-story-singleton-completion"
            report["story_completion_assignments"].append({"story_id": sid, "pdf_page": r["pdf_page"], "printed_page": missing[0], "basis": "singleton"})
            continue

        # Exact contiguous local-run completion next to an established anchor.
        candidates_sorted = sorted(candidates, key=lambda r: int(r["pdf_page"]))
        pdfs = [int(r["pdf_page"]) for r in candidates_sorted]
        if len(candidates_sorted) != len(missing) or any(b - a != 1 for a, b in zip(pdfs, pdfs[1:])):
            continue
        by_pdf = {int(r["pdf_page"]): r for r in records}
        first_pdf, last_pdf = pdfs[0], pdfs[-1]
        before = by_pdf.get(first_pdf - 1)
        after = by_pdf.get(last_pdf + 1)
        ordered_numbers: list[int] | None = None
        if before and before.get("printed_page") is not None:
            bp = int(before["printed_page"])
            if bp + 1 == min(missing):
                ordered_numbers = sorted(missing)
            elif bp - 1 == max(missing):
                ordered_numbers = sorted(missing, reverse=True)
        if ordered_numbers is None and after and after.get("printed_page") is not None:
            ap = int(after["printed_page"])
            if ap - 1 == max(missing):
                ordered_numbers = sorted(missing)
            elif ap + 1 == min(missing):
                ordered_numbers = sorted(missing, reverse=True)
        if ordered_numbers is None:
            continue
        if any(n in used_numbers(records) for n in ordered_numbers):
            continue
        for r, n in zip(candidates_sorted, ordered_numbers):
            r["printed_page"] = n
            r["printed_page_basis"] = "solver-story-contiguous-run-completion"
            report["story_completion_assignments"].append({"story_id": sid, "pdf_page": r["pdf_page"], "printed_page": n, "basis": "contiguous-run"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--issue-id", required=True)
    ap.add_argument("--parsed-dir", type=Path, required=True)
    args = ap.parse_args()

    catalog = load_json(args.catalog)
    issue = next((x for x in catalog["issues"] if str(x["id"]) == str(args.issue_id)), None)
    if issue is None:
        raise SystemExit(f"issue {args.issue_id} not found")
    ranges = issue_story_ranges(issue)
    records_path = args.parsed_dir / "page-records.jsonl"
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records.sort(key=lambda r: int(r["pdf_page"]))

    report: dict[str, Any] = {
        "solver_version": SOLVER_VERSION,
        "issue_id": issue["id"],
        "manual_anchors": [],
        "invalidated_assignments": [],
        "duplicate_resolutions": [],
        "sequence_assignments": [],
        "story_completion_assignments": [],
    }

    for r in records:
        r["solver_story_hits"] = recompute_story_hits(r, issue)
        r.setdefault("page_order_solver", {})["version"] = SOLVER_VERSION

    by_pdf = {int(r["pdf_page"]): r for r in records}
    for anchor in issue.get("manual_page_anchors", []):
        pdf_page = int(anchor["pdf_page"])
        printed = int(anchor["printed_page"])
        if pdf_page not in by_pdf:
            continue
        r = by_pdf[pdf_page]
        r["printed_page"] = printed
        r["printed_page_basis"] = "source-reviewed-manual-anchor"
        r["page_order_solver"]["manual_anchor_note"] = anchor.get("note")
        report["manual_anchors"].append({"pdf_page": pdf_page, "printed_page": printed, "note": anchor.get("note")})

    # Clear story-incompatible non-manual assignments before resolving duplicates.
    for r in records:
        p = r.get("printed_page")
        if p is None or r.get("printed_page_basis") == "source-reviewed-manual-anchor":
            continue
        if not compatible(r, int(p), ranges, issue):
            report["invalidated_assignments"].append({"pdf_page": r["pdf_page"], "printed_page": p, "basis": r.get("printed_page_basis"), "reason": "outside unique story range"})
            clear_assignment(r, "assignment conflicts with unique story range")

    # If an unresolved page has one strong direct candidate compatible with its
    # story range, restore it before global duplicate resolution.
    for r in records:
        if r.get("printed_page") is not None:
            continue
        candidates = [c for c in r.get("page_number_candidates", []) if float(c.get("score", 0)) >= 7 and compatible(r, int(c["number"]), ranges, issue)]
        candidates.sort(key=lambda c: (float(c.get("score", 0)), float(c.get("confidence", 0))), reverse=True)
        if not candidates:
            continue
        top = candidates[0]
        runner = float(candidates[1].get("score", 0)) if len(candidates) > 1 else -999
        if float(top.get("score", 0)) >= 10 or float(top.get("score", 0)) >= runner + 2:
            r["printed_page"] = int(top["number"])
            r["printed_page_basis"] = "solver-compatible-margin-ocr"

    resolve_duplicates(records, issue, ranges, report)
    interpolate_bracketed(records, issue, ranges, report)
    complete_story_runs(records, issue, ranges, report)
    resolve_duplicates(records, issue, ranges, report)
    interpolate_bracketed(records, issue, ranges, report)
    complete_story_runs(records, issue, ranges, report)

    # Publish unresolved story-range candidates for editor/reviewer rather than guessing.
    for r in records:
        sid = unique_story(r, issue)
        if r.get("printed_page") is None and sid:
            start, end = ranges[sid]
            used = used_numbers(records)
            r["page_order_solver"]["story_range_candidate"] = {
                "story_id": sid,
                "candidate_printed_pages": [n for n in range(start, (end or start) + 1) if n not in used] if end is not None else None,
            }

    duplicates: dict[int, list[int]] = {}
    for r in records:
        if r.get("printed_page") is not None:
            duplicates.setdefault(int(r["printed_page"]), []).append(int(r["pdf_page"]))
    remaining_dups = {str(k): v for k, v in duplicates.items() if len(v) > 1}

    direct = sum(1 for r in records if r.get("printed_page_basis") in {"outer-margin-ocr", "solver-compatible-margin-ocr"})
    manual = sum(1 for r in records if r.get("printed_page_basis") == "source-reviewed-manual-anchor")
    resolved = sum(1 for r in records if r.get("printed_page") is not None)
    report["summary"] = {
        "pdf_pages": len(records),
        "resolved_printed_pages": resolved,
        "unresolved_pdf_pages": len(records) - resolved,
        "manual_anchor_count": manual,
        "direct_or_compatible_margin_ocr_count": direct,
        "remaining_duplicate_assignments": remaining_dups,
    }

    safe_write(records_path, "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n")
    safe_write(args.parsed_dir / "PAGE_ORDER_SOLVER_REPORT.json", json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    manifest_path = args.parsed_dir / "manifest.json"
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        manifest["page_order_solver"] = {"version": SOLVER_VERSION, **report["summary"]}
        safe_write(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps(report["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
