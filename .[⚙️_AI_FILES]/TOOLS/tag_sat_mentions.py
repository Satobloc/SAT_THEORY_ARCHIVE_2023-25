#!/usr/bin/env python3
"""First-pass extractor for SAT/version-name mentions and nearby date expressions.

This is evidence extraction, not interpretation. It records raw strings, paths,
line numbers, context, and nearby date-like text.
"""
from __future__ import annotations

import argparse, csv, json, os, re, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
AI = ROOT / ".[⚙️_AI_FILES]"
OUT = AI / "TAGS"
LOGS = AI / "LOGS" / "tag_sat_mentions"
TEXT_EXTS = {".txt", ".md", ".markdown", ".rst", ".tex", ".bib", ".csv", ".tsv", ".json", ".jsonl", ".yaml", ".yml", ".py", ".sh", ".html", ".htm"}
SKIP_DIRS = {".git", "__pycache__", ".[⚙️_AI_FILES]/TAGS", ".[⚙️_AI_FILES]/LOGS", ".[⚙️_AI_FILES]/TEMP"}
MONTHS = "jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december"

DATE_PATTERNS = [
    ("iso", re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b")),
    ("numeric", re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")),
    ("month_day_year", re.compile(rf"\b(?:{MONTHS})\.?\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{2,4}})?\b", re.I)),
    ("month_year", re.compile(rf"\b(?:{MONTHS})\.?\s+\d{{4}}\b", re.I)),
    ("season_year", re.compile(r"\b(?:spring|summer|fall|autumn|winter)\s+\d{4}\b", re.I)),
    ("relative", re.compile(r"\b(?:today|yesterday|tomorrow|tonight|last\s+(?:week|month|year|night|spring|summer|fall|autumn|winter)|next\s+(?:week|month|year|spring|summer|fall|autumn|winter)|this\s+(?:week|month|year|spring|summer|fall|autumn|winter)|recently|earlier\s+today|later\s+today)\b", re.I)),
    ("year", re.compile(r"\b(?:19|20)\d{2}\b")),
]

SAT_PATTERNS = [
    ("sat_dot_dash", re.compile(r"(?<![A-Za-z0-9])SAT[._-][A-Za-z0-9][A-Za-z0-9._\-()+]*", re.I)),
    ("sat_spaced", re.compile(r"(?<![A-Za-z0-9])SAT\s+[A-Za-z0-9][A-Za-z0-9._\-()+]*(?:\s+[A-Za-z0-9][A-Za-z0-9._\-()+]*){0,4}", re.I)),
    ("sat_compact", re.compile(r"(?<![A-Za-z0-9])SAT(?:x|xy|xyz|o|4d)\b", re.I)),
    ("sat_bare", re.compile(r"(?<![A-Za-z0-9])SAT(?![A-Za-z0-9])", re.I)),
    ("satobloc", re.compile(r"\bSatobloc\b", re.I)),
    ("stringing_along", re.compile(r"\bStringing[-\s]+Along\s+Theory\b", re.I)),
    ("scalar_angular_torsion", re.compile(r"\bScalar[-\s]+Angular[-\s]+Torsion(?:\s+Theory)?\b", re.I)),
    ("scalar_angular", re.compile(r"\bScalar[-\s]+Angular(?:\s+Theory)?\b", re.I)),
    ("chronophysical", re.compile(r"\b(?:The\s+)?Chronophysical\s+(?:Proposition|Framework|Theory)\b", re.I)),
]

def now(): return datetime.now(timezone.utc).isoformat()
def stamp(): return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
def rel(p: Path): return "." if p == ROOT else str(p.relative_to(ROOT)).replace(os.sep, "/")

def skip(p: Path, include_ai: bool) -> bool:
    r = rel(p)
    if not include_ai and (r == ".[⚙️_AI_FILES]" or r.startswith(".[⚙️_AI_FILES]/")): return True
    return any(r == s or r.startswith(s + "/") or p.name == s for s in SKIP_DIRS)

def read_text(p: Path):
    try: data = p.read_bytes()
    except Exception: return None
    if b"\x00" in data[:4096]: return None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try: return data.decode(enc)
        except UnicodeDecodeError: pass
    return None

def dates_near(text: str):
    hits, seen = [], set()
    for fam, pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            key = (m.group(0), m.start(), fam)
            if key not in seen:
                seen.add(key); hits.append({"text": m.group(0), "family": fam})
    return hits

def clean(s: str, n=500):
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n-1] + "…" if len(s) > n else s

def find_rows(path: Path, text: str):
    rows, lines = [], text.splitlines()
    for i, line in enumerate(lines, start=1):
        ctx = "\n".join(lines[max(0, i-2):min(len(lines), i+1)])
        ds = dates_near(ctx)
        occupied = []
        for fam, pat in SAT_PATTERNS:
            for m in pat.finditer(line):
                span = m.span()
                if any(not (span[1] <= a or span[0] >= b) for a, b in occupied):
                    continue
                occupied.append(span)
                rows.append({
                    "path": rel(path), "line": i, "raw_mention": m.group(0).strip(),
                    "mention_family": fam,
                    "nearby_dates": [d["text"] for d in ds],
                    "nearby_date_families": [d["family"] for d in ds],
                    "context": clean(ctx),
                })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-files", type=int, default=250)
    ap.add_argument("--max-runtime-seconds", type=int, default=120)
    ap.add_argument("--include-ai-files", action="store_true")
    ap.add_argument("--suffix", default="test")
    args = ap.parse_args()
    start, rows, scanned, unreadable = time.monotonic(), [], 0, 0
    stop = "complete"
    for p in ROOT.rglob("*"):
        if time.monotonic() - start > args.max_runtime_seconds:
            stop = "time_limit"; break
        if scanned >= args.max_files:
            stop = "file_limit"; break
        if not p.is_file() or p.suffix.lower() not in TEXT_EXTS or skip(p, args.include_ai_files):
            continue
        txt = read_text(p)
        if txt is None:
            unreadable += 1; continue
        scanned += 1
        rows.extend(find_rows(p, txt))
    OUT.mkdir(parents=True, exist_ok=True); LOGS.mkdir(parents=True, exist_ok=True)
    base = f"sat_mentions_{args.suffix}"
    jsonl, csvp, summary = OUT / f"{base}.jsonl", OUT / f"{base}.csv", OUT / f"{base}_summary.md"
    with jsonl.open("w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    fields = ["path","line","raw_mention","mention_family","nearby_dates","nearby_date_families","context"]
    with csvp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows:
            rr = dict(r); rr["nearby_dates"] = "; ".join(rr["nearby_dates"]); rr["nearby_date_families"] = "; ".join(rr["nearby_date_families"]); w.writerow(rr)
    fams = Counter(r["mention_family"] for r in rows); files = Counter(r["path"] for r in rows)
    summary.write_text("\n".join([
        "# SAT Mention Extraction", "", f"Generated UTC: {now()}", f"Stopped reason: {stop}", f"Files scanned: {scanned}", f"Unreadable selected files: {unreadable}", f"Rows: {len(rows)}", "", "## Mention families", "", *[f"- {k}: {v}" for k,v in fams.most_common()], "", "## Top files", "", *[f"- {k}: {v}" for k,v in files.most_common(30)], "", "Outputs:", f"- {rel(jsonl)}", f"- {rel(csvp)}", ""]), encoding="utf-8")
    (LOGS / f"{base}_{stamp()}.txt").write_text(f"SAT MENTION EXTRACTION\nUTC: {now()}\nFILES_SCANNED: {scanned}\nROWS: {len(rows)}\nSTOPPED_REASON: {stop}\nOUTPUT: {rel(summary)}\n", encoding="utf-8")
    print(f"SAT mention extraction complete: {len(rows)} rows from {scanned} files")

if __name__ == "__main__": main()
