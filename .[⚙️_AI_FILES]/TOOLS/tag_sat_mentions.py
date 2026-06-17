#!/usr/bin/env python3
"""Extract SAT/theory-version mentions and nearby date expressions.

This is a conservative first-pass tagger. It does not interpret documents.
It records observed mention strings, nearby date strings, file paths, line
numbers, and short context snippets so later semantic tagging can build on
explicit evidence rather than folder-title inference.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
AI = ROOT / ".[⚙️_AI_FILES]"
OUT_DIR = AI / "TAGS"
LOG_DIR = AI / "LOGS" / "tag_sat_mentions"

DEFAULT_TEXT_EXTS = {
    ".txt", ".md", ".markdown", ".rst", ".tex", ".bib", ".csv", ".tsv",
    ".json", ".jsonl", ".yaml", ".yml", ".py", ".sh", ".html", ".htm",
}

DEFAULT_SKIP_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".[⚙️_AI_FILES]/TAGS", ".[⚙️_AI_FILES]/LOGS", ".[⚙️_AI_FILES]/TEMP",
}

MONTHS = (
    "jan", "january", "feb", "february", "mar", "march", "apr", "april",
    "may", "jun", "june", "jul", "july", "aug", "august", "sep", "sept",
    "september", "oct", "october", "nov", "november", "dec", "december",
)

DATE_PATTERNS = [
    ("iso_date", re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b")),
    ("slash_date", re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")),
    ("dash_date", re.compile(r"\b\d{1,2}-\d{1,2}-\d{2,4}\b")),
    ("month_day_year", re.compile(r"\b(?:" + "|".join(MONTHS) + r")\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{2,4})?\b", re.I)),
    ("day_month_year", re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:" + "|".join(MONTHS) + r")\.?\s*,?\s*\d{2,4}\b", re.I)),
    ("month_year", re.compile(r"\b(?:" + "|".join(MONTHS) + r")\.?\s+\d{4}\b", re.I)),
    ("year", re.compile(r"\b(?:19|20)\d{2}\b")),
    ("relative_date", re.compile(r"\b(?:today|yesterday|tomorrow|tonight|last\s+(?:week|month|year|night|spring|summer|fall|autumn|winter)|next\s+(?:week|month|year|spring|summer|fall|autumn|winter)|this\s+(?:week|month|year|spring|summer|fall|autumn|winter)|earlier\s+today|later\s+today|recently)\b", re.I)),
]

THEORY_PATTERNS = [
    ("satobloc", "Satobloc", re.compile(r"\bSatobloc\b", re.I)),
    ("stringing_along_theory", "Stringing-Along Theory", re.compile(r"\bStringing[-\s]+Along\s+Theory\b", re.I)),
    ("scalar_angular_torsion", "Scalar-Angular-Torsion", re.compile(r"\bScalar[-\s]+Angular[-\s]+Torsion(?:\s+Theory)?\b", re.I)),
    ("scalar_angular_theory", "Scalar-Angular Theory", re.compile(r"\bScalar[-\s]+Angular(?:\s+Theory)?\b", re.I)),
    ("chronophysical_proposition", "Chronophysical Proposition", re.compile(r"\b(?:The\s+)?Chronophysical\s+Proposition\b", re.I)),
    ("sat_mark", "SAT Mark", re.compile(r"\bSAT\s*[-._ ]?\s*Mark\s+(?:[IVXLC]+|\d+)\b", re.I)),
    ("sat_vnext", "SAT vNext", re.compile(r"\bSAT\s*[-._ ]?\s*v\s*Next\b", re.I)),
    ("sat_4d_compound", "SAT.4D compound", re.compile(r"\bSAT\s*[-._ ]?\s*4D(?:\s*[-._ ]\s*[A-Za-z0-9]+|\s*\([^\n\r)]{1,80}\))+\b", re.I)),
    ("sat_letter_version", "SAT letter/version", re.compile(r"\bSAT\s*[-._ ]?\s*(?:[XYZO]|XY|XYZ|X\s*Y|O|v)\b", re.I)),
    ("sat_compact_suffix", "SAT compact suffix", re.compile(r"\bSAT(?:x|xy|xyz|o)\b", re.I)),
    ("sat_caps_compound", "SAT compound", re.compile(r"\bSAT(?:\s*[-._ ]\s*[A-Z0-9][A-Z0-9+()]{0,20}){1,6}\b")),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace(os.sep, "/") if path != ROOT else "."


def should_skip(path: Path, skip_dirs: set[str]) -> bool:
    r = rel(path)
    return any(r == s or r.startswith(s + "/") or path.name == s for s in skip_dirs)


def iter_files(max_files: int, max_runtime: int, text_exts: set[str], skip_dirs: set[str]):
    start = time.monotonic()
    count = 0
    for path in ROOT.rglob("*"):
        if time.monotonic() - start > max_runtime:
            yield "__TIME_LIMIT__", None
            return
        if path.is_dir():
            continue
        if should_skip(path, skip_dirs):
            continue
        if path.suffix.lower() not in text_exts:
            continue
        count += 1
        if count > max_files:
            yield "__FILE_LIMIT__", None
            return
        yield "file", path


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except Exception:
        return None
    if b"\x00" in data[:4096]:
        return None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def find_dates(text: str) -> list[dict[str, str]]:
    hits = []
    seen = set()
    for family, pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            item = (m.group(0), m.start(), m.end(), family)
            if item in seen:
                continue
            seen.add(item)
            hits.append({"date_text": m.group(0), "date_family": family, "start": m.start(), "end": m.end()})
    hits.sort(key=lambda x: (int(x["start"]), int(x["end"])))
    return hits


def normalize_context(s: str, limit: int = 360) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[: limit - 1] + "…" if len(s) > limit else s


def line_context(lines: list[str], idx: int) -> str:
    start = max(0, idx - 1)
    end = min(len(lines), idx + 2)
    return "\n".join(lines[start:end])


def classify_confidence(family: str, mention: str) -> str:
    if family in {"satobloc", "stringing_along_theory", "scalar_angular_torsion", "chronophysical_proposition", "sat_mark", "sat_vnext", "sat_4d_compound"}:
        return "high"
    if family in {"scalar_angular_theory", "sat_letter_version", "sat_compact_suffix"}:
        return "medium"
    if family == "sat_caps_compound":
        return "medium" if len(mention) > 4 else "low"
    return "unknown"


def extract_mentions(path: Path, text: str) -> list[dict[str, object]]:
    rows = []
    lines = text.splitlines()
    for line_no, line in enumerate(lines, start=1):
        context = line_context(lines, line_no - 1)
        dates = find_dates(context)
        date_texts = [d["date_text"] for d in dates]
        date_families = [d["date_family"] for d in dates]
        for family, canonical, pat in THEORY_PATTERNS:
            for m in pat.finditer(line):
                mention = m.group(0).strip()
                rows.append({
                    "path": rel(path),
                    "line": line_no,
                    "mention_text": mention,
                    "canonical_tag": canonical,
                    "mention_family": family,
                    "confidence": classify_confidence(family, mention),
                    "dates_in_context": date_texts,
                    "date_families": date_families,
                    "context": normalize_context(context),
                })
    return rows


def write_outputs(rows: list[dict[str, object]], meta: dict[str, object]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = OUT_DIR / "sat_mentions.jsonl"
    csv_path = OUT_DIR / "sat_mentions.csv"
    summary_path = OUT_DIR / "sat_mentions_summary.md"
    meta_path = OUT_DIR / "sat_mentions_run_meta.json"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    fields = ["path", "line", "mention_text", "canonical_tag", "mention_family", "confidence", "dates_in_context", "date_families", "context"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["dates_in_context"] = "; ".join(row.get("dates_in_context", []))
            out["date_families"] = "; ".join(row.get("date_families", []))
            writer.writerow(out)

    tag_counts = Counter(str(r["canonical_tag"]) for r in rows)
    family_counts = Counter(str(r["mention_family"]) for r in rows)
    file_counts = Counter(str(r["path"]) for r in rows)
    dated = sum(1 for r in rows if r.get("dates_in_context"))

    lines = [
        "# SAT Mention Tagging Summary",
        "",
        f"Generated UTC: {meta['generated_utc']}",
        f"Files scanned: {meta['files_scanned']}",
        f"Files unreadable/skipped after selection: {meta['files_unreadable']}",
        f"Mention rows: {len(rows)}",
        f"Rows with nearby date expressions: {dated}",
        "",
        "This is an evidence list, not a semantic interpretation. Folder and file titles are treated as historical text, not authoritative descriptions.",
        "",
        "## Top canonical tags",
        "",
    ]
    for tag, n in tag_counts.most_common(30):
        lines.append(f"- {tag}: {n}")
    lines.extend(["", "## Mention families", ""])
    for fam, n in family_counts.most_common(30):
        lines.append(f"- {fam}: {n}")
    lines.extend(["", "## Top files by mention count", ""])
    for p, n in file_counts.most_common(50):
        lines.append(f"- {p}: {n}")
    lines.extend(["", "## Outputs", "", "- .[⚙️_AI_FILES]/TAGS/sat_mentions.jsonl", "- .[⚙️_AI_FILES]/TAGS/sat_mentions.csv", "- .[⚙️_AI_FILES]/TAGS/sat_mentions_run_meta.json", ""])
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    meta["mention_rows"] = len(rows)
    meta["rows_with_dates"] = dated
    meta["top_canonical_tags"] = tag_counts.most_common(30)
    meta["top_mention_families"] = family_counts.most_common(30)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    log_path = LOG_DIR / f"tag_sat_mentions_{stamp()}.txt"
    log_path.write_text("\n".join([
        "SAT MENTION TAGGING RUN",
        f"UTC: {meta['generated_utc']}",
        f"FILES_SCANNED: {meta['files_scanned']}",
        f"FILES_UNREADABLE: {meta['files_unreadable']}",
        f"MENTION_ROWS: {len(rows)}",
        f"ROWS_WITH_DATES: {dated}",
        f"OUTPUT_JSONL: {rel(jsonl_path)}",
        f"OUTPUT_CSV: {rel(csv_path)}",
        f"OUTPUT_SUMMARY: {rel(summary_path)}",
        f"OUTPUT_META: {rel(meta_path)}",
    ]) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-files", type=int, default=50000)
    parser.add_argument("--max-runtime-seconds", type=int, default=900)
    parser.add_argument("--include-ai-files", action="store_true")
    args = parser.parse_args()

    skip_dirs = set(DEFAULT_SKIP_DIRS)
    if not args.include_ai_files:
        skip_dirs.add(".[⚙️_AI_FILES]")

    rows = []
    files_scanned = 0
    files_unreadable = 0
    stopped_reason = "complete"

    for kind, path in iter_files(args.max_files, args.max_runtime_seconds, DEFAULT_TEXT_EXTS, skip_dirs):
        if kind == "__TIME_LIMIT__":
            stopped_reason = "time_limit"
            break
        if kind == "__FILE_LIMIT__":
            stopped_reason = "file_limit"
            break
        assert path is not None
        text = read_text(path)
        if text is None:
            files_unreadable += 1
            continue
        files_scanned += 1
        rows.extend(extract_mentions(path, text))

    meta = {
        "generated_utc": utc_now(),
        "tool": "tag_sat_mentions.py",
        "max_files": args.max_files,
        "max_runtime_seconds": args.max_runtime_seconds,
        "include_ai_files": args.include_ai_files,
        "stopped_reason": stopped_reason,
        "files_scanned": files_scanned,
        "files_unreadable": files_unreadable,
        "note": "First-pass regex extraction of SAT/theory-version mentions and nearby date expressions. Not a semantic interpretation.",
    }
    write_outputs(rows, meta)
    print(f"SAT mention tagging complete: {len(rows)} rows from {files_scanned} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
