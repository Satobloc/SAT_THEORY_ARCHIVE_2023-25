#!/usr/bin/env python3
"""
Batched Nathan Corpus Extractor

Purpose:
- Recursively crawl the archive in bounded batches.
- Extract likely Nathan/User-authored text without editing.
- Keep human-readable output in ..📚_NATHAN_WORDS_EXTRACTED.
- Keep logs/indexes/cursor in the hammer folder.
- Avoid runaway recursion, runaway output size, and giant single files.
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
ADMIN_DIR = REPO_ROOT / ".⚙️_AI_AUTOMATION_ADMIN"
REQUEST_PATH = ADMIN_DIR / "_AI_REQUESTS" / "nathan_corpus_extract_request.json"
OUTPUT_DIR = REPO_ROOT / "..📚_NATHAN_WORDS_EXTRACTED"
LOG_DIR = OUTPUT_DIR / "⚒️_extraction_logs_and_indexes"
CURSOR_PATH = LOG_DIR / "crawl_cursor.json"
SOURCE_INDEX_PATH = LOG_DIR / "NATHAN_CORPUS_SOURCE_INDEX.csv"
VERSION_INDEX_PATH = LOG_DIR / "NATHAN_CORPUS_VERSION_DATE_INDEX.csv"

DEFAULT_REQUEST = {
    "mode": "extract",
    "crawl_strategy": "recursive_batched",
    "max_runtime_seconds": 1200,
    "max_files_per_run": 2000,
    "max_dirs_per_run": 5000,
    "max_passages_per_run": 25000,
    "max_output_files_per_run": 100,
    "max_chars_per_part": 200000,
    "max_total_output_chars_per_run": 20000000,
    "max_single_passage_chars": 50000,
    "resume": True,
    "follow_symlinks": False,
    "include_confidence": ["certain", "likely"],
    "include_review_candidates": True,
    "dedupe_now": False,
    "root_scan_dirs": ["."],
}

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".json", ".jsonl", ".yaml", ".yml",
    ".tex", ".py", ".js", ".ts", ".html", ".htm", ".xml", ".rst", ".log"
}

SKIP_DIR_NAMES = {
    ".git", ".github", ".⚙️_AI_AUTOMATION_ADMIN", "⚙️_AI_AUTOMATION_ADMIN",
    "..📚_NATHAN_WORDS_EXTRACTED", "📚_NATHAN_WORDS_EXTRACTED", "_NATHAN_CORPUS"
}

ASSISTANT_LABELS = {"chatgpt", "assistant", "ai", "system", "model", "notebooklm", "gemini", "claude", "copilot"}
USER_LABEL_HINTS = {"user", "human", "me", "nathan", "satobloc", "satoblock", "author"}

SPEAKER_LINE_RE = re.compile(r"^\s*(?:#{1,6}\s*)?(?P<label>[A-Za-z0-9_ .@+\-]{2,80})\s*[:：]\s*(?P<rest>.*)$")
ISO_DATE_RE = re.compile(r"\b(20\d{2}|19\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])\b")
US_DATE_RE = re.compile(r"\b(0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.](20\d{2}|19\d{2})\b")
MONTH_DATE_RE = re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:20\d{2}|19\d{2})\b", re.I)
YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")
VERSION_PATTERNS = [
    re.compile(r"\bSAT\s*(?:-|_)?\s*(?:Mark\s*)?[VvXxIi0-9]+\b"),
    re.compile(r"\bSAT\s*(?:-|_)?\s*[A-Z]\b"),
    re.compile(r"\bSAT[_\s-]*(?:XYZ|RMS|QG|O)\b", re.I),
    re.compile(r"\bMark\s+[VvXxIi0-9]+\b"),
]

@dataclass
class Passage:
    source: str
    start_line: int
    end_line: int
    label: str
    text: str
    confidence: str
    method: str
    file_most_recent_date: str = ""
    nearest_prior_date: str = ""
    passage_dates: str = ""
    file_version_signal: str = ""
    nearest_prior_version: str = ""
    passage_versions: str = ""
    review: bool = False
    passage_id: str = ""

@dataclass
class FileSurvey:
    path: str
    file_type: str
    size_bytes: int
    lines: int = 0
    status: str = "pending"
    labels: List[str] = field(default_factory=list)
    date_signals: List[str] = field(default_factory=list)
    version_signals: List[str] = field(default_factory=list)
    extracted_passages: int = 0
    review_candidates: int = 0
    warning: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_request() -> dict:
    request = dict(DEFAULT_REQUEST)
    if REQUEST_PATH.exists():
        try:
            request.update(json.loads(REQUEST_PATH.read_text(encoding="utf-8")))
        except Exception as exc:
            request["request_error"] = str(exc)
    return request


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace(os.sep, "/")


def is_text_like(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or (not path.suffix and path.name.upper() in {"LICENSE", "README", "NOTICE"})


def should_skip_dir(path: Path) -> bool:
    return path.name in SKIP_DIR_NAMES


def read_text_safely(path: Path) -> Tuple[Optional[str], str]:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc), ""
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            return None, str(exc)
    return None, "Could not decode as text"


def normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip()).strip("#*[]() ")


def label_kind(label: str) -> str:
    low = re.sub(r"[^a-z0-9@._+-]+", "", normalize_label(label).lower())
    if low in ASSISTANT_LABELS or any(x in low for x in ("chatgpt", "assistant", "notebooklm")):
        return "assistant"
    if low in USER_LABEL_HINTS or "nathan" in low or "satobloc" in low or "@" in low:
        return "user"
    if re.search(r"[A-Za-z0-9_@.+-]{3,}", low) and low not in ASSISTANT_LABELS:
        return "probable_user"
    return "unknown"


def extract_dates(text: str) -> List[str]:
    found: List[str] = []
    for m in ISO_DATE_RE.finditer(text):
        y, mo, d = m.groups()
        found.append(f"{int(y):04d}-{int(mo):02d}-{int(d):02d}")
    for m in US_DATE_RE.finditer(text):
        mo, d, y = m.groups()
        found.append(f"{int(y):04d}-{int(mo):02d}-{int(d):02d}")
    found.extend(m.group(0) for m in MONTH_DATE_RE.finditer(text))
    found.extend(m.group(1) for m in YEAR_RE.finditer(text))
    return sorted(set(found))


def most_recent_date_signal(dates: Sequence[str]) -> str:
    iso = [d for d in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)]
    if iso:
        return max(iso)
    years = [d for d in dates if re.fullmatch(r"\d{4}", d)]
    return max(years) if years else (dates[-1] if dates else "")


def extract_versions(text: str) -> List[str]:
    found: List[str] = []
    for pat in VERSION_PATTERNS:
        found.extend(re.sub(r"\s+", " ", m.group(0).strip()) for m in pat.finditer(text))
    return sorted(set(found))


def compact_versions(values: str, max_items: int = 4) -> str:
    return "; ".join([p.strip() for p in values.split(";") if p.strip()][:max_items])


def best_date(p: Passage) -> str:
    return p.passage_dates or p.nearest_prior_date or p.file_most_recent_date


def best_version(p: Passage) -> str:
    return p.passage_versions or p.nearest_prior_version or compact_versions(p.file_version_signal)


def find_labels(lines: Sequence[str]) -> List[str]:
    labels: List[str] = []
    for line in lines[:20000]:
        m = SPEAKER_LINE_RE.match(line)
        if m:
            label = normalize_label(m.group("label"))
            if label_kind(label) in {"user", "probable_user", "assistant"}:
                labels.append(label)
    return sorted(set(labels))[:100]


def looks_like_nathan(text: str) -> bool:
    low = text.lower()
    signals = 0
    for token in ["sat", "filament", "timesheet", "worldline", "theta", "θ", "drag", "epistem", "ontolog", "no.", "ok.", "actually", "not because", "scalar-angular"]:
        if token in low:
            signals += 1
    if "..." in text or "…" in text:
        signals += 1
    return signals >= 4 and len(text.strip()) > 120


def split_speaker_passages(source: str, lines: Sequence[str], file_dates: List[str], file_versions: List[str], max_single_passage_chars: int) -> Tuple[List[Passage], List[Passage], List[str]]:
    passages: List[Passage] = []
    reviews: List[Passage] = []
    warnings: List[str] = []
    current_label: Optional[str] = None
    current_kind = "unknown"
    current_start = 1
    buffer: List[str] = []
    nearest_date = ""
    nearest_version = ""

    def trim_text(text: str, source_label: str) -> str:
        if len(text) <= max_single_passage_chars:
            return text
        warnings.append(f"{source_label}: passage trimmed from {len(text)} chars to {max_single_passage_chars}")
        return text[:max_single_passage_chars] + "\n\n[TRIMMED BY max_single_passage_chars]"

    def flush(end_line: int) -> None:
        nonlocal buffer, current_label, current_kind, current_start, nearest_date, nearest_version
        if current_label is None or not buffer:
            buffer = []
            return
        text = "\n".join(buffer).strip("\n")
        if not text.strip():
            buffer = []
            return
        text = trim_text(text, f"{source} lines {current_start}-{end_line}")
        p_dates = extract_dates(text)
        p_versions = extract_versions(text)
        p = Passage(
            source=source,
            start_line=current_start,
            end_line=end_line,
            label=current_label,
            text=text,
            confidence="certain" if current_kind == "user" else "likely" if current_kind == "probable_user" else "exclude",
            method="explicit speaker label" if current_kind == "user" else "non-ChatGPT speaker label" if current_kind == "probable_user" else "excluded assistant/system label",
            file_most_recent_date=most_recent_date_signal(file_dates),
            nearest_prior_date=nearest_date,
            passage_dates="; ".join(p_dates),
            file_version_signal="; ".join(file_versions[:12]),
            nearest_prior_version=nearest_version,
            passage_versions="; ".join(p_versions),
        )
        if current_kind in {"user", "probable_user"}:
            passages.append(p)
        elif current_kind == "unknown" and looks_like_nathan(text):
            p.confidence = "review"
            p.method = "style/topic candidate"
            p.review = True
            reviews.append(p)
        buffer = []

    for idx, line in enumerate(lines, start=1):
        ld = extract_dates(line)
        lv = extract_versions(line)
        if ld:
            nearest_date = most_recent_date_signal(ld)
        if lv:
            nearest_version = "; ".join(lv[:4])
        m = SPEAKER_LINE_RE.match(line)
        if m:
            label = normalize_label(m.group("label"))
            kind = label_kind(label)
            if kind in {"user", "probable_user", "assistant"}:
                flush(idx - 1)
                current_label = label
                current_kind = kind
                current_start = idx
                rest = m.group("rest")
                buffer = [rest] if rest else []
                continue
        if current_label is not None:
            buffer.append(line)
    flush(len(lines))
    return passages, reviews, warnings


def process_file(path: Path, request: dict) -> Tuple[FileSurvey, List[Passage], List[Passage], List[str]]:
    source = rel(path)
    fs = FileSurvey(source, path.suffix.lower() or "extensionless", path.stat().st_size)
    text, err = read_text_safely(path)
    if text is None:
        fs.status = "skipped"
        fs.warning = err
        return fs, [], [], [f"{source}: {err}"]
    lines = text.splitlines()
    fs.lines = len(lines)
    fs.status = "scanned"
    fs.date_signals = extract_dates(source + "\n" + text[:500000])
    fs.version_signals = extract_versions(source + "\n" + text[:300000])
    fs.labels = find_labels(lines)
    passages, reviews, warnings = split_speaker_passages(source, lines, fs.date_signals, fs.version_signals, int(request["max_single_passage_chars"]))
    fs.extracted_passages = len(passages)
    fs.review_candidates = len(reviews)
    return fs, passages, reviews, warnings


def initial_cursor(request: dict) -> dict:
    roots = request.get("root_scan_dirs") or ["."]
    pending_dirs = []
    for root in roots:
        p = (REPO_ROOT / root).resolve()
        if p.exists() and p.is_dir():
            pending_dirs.append(rel(p) if p != REPO_ROOT else ".")
    return {
        "pending_dirs": pending_dirs,
        "pending_files": [],
        "completed_dirs": [],
        "completed_files": [],
        "runs_completed": 0,
        "global_passage_count": 0,
        "next_output_part": 0,
        "created_utc": utc_now(),
        "updated_utc": utc_now(),
        "last_stop_reason": "initialized",
    }


def load_cursor(request: dict) -> dict:
    if request.get("resume", True) and CURSOR_PATH.exists():
        try:
            return json.loads(CURSOR_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return initial_cursor(request)


def save_cursor(cursor: dict) -> None:
    cursor["updated_utc"] = utc_now()
    CURSOR_PATH.write_text(json.dumps(cursor, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def path_from_rel(r: str) -> Path:
    return REPO_ROOT if r == "." else (REPO_ROOT / r)


def add_dir_children(cursor: dict, dir_rel: str, request: dict, counters: dict, warnings: List[str]) -> None:
    d = path_from_rel(dir_rel)
    try:
        entries = sorted(d.iterdir(), key=lambda p: p.name.lower())
    except Exception as exc:
        warnings.append(f"Could not list directory {dir_rel}: {exc}")
        return
    for entry in entries:
        if not request.get("follow_symlinks", False) and entry.is_symlink():
            continue
        if entry.is_dir():
            if should_skip_dir(entry):
                counters["dirs_skipped"] += 1
                continue
            cursor["pending_dirs"].append(rel(entry))
            counters["dirs_discovered"] += 1
        elif entry.is_file():
            if is_text_like(entry):
                cursor["pending_files"].append(rel(entry))
                counters["files_discovered"] += 1
            else:
                counters["files_skipped_non_text"] += 1


def passage_header(p: Passage) -> str:
    bits = [f"{p.passage_id} | {p.label} | {p.confidence}", f"source: {p.source} lines {p.start_line}-{p.end_line}"]
    d = best_date(p)
    v = best_version(p)
    if d:
        bits.append(f"date: {d}")
    if v:
        bits.append(f"version: {v}")
    return "\n---\n" + "\n".join(bits) + "\n---\n\n"


def append_part(passages: List[Passage], prefix: str, cursor: dict, request: dict, run_state: dict) -> int:
    max_chars = int(request["max_chars_per_part"])
    max_output_files = int(request["max_output_files_per_run"])
    max_total_chars = int(request["max_total_output_chars_per_run"])
    parts_written = 0
    current_chunks: List[str] = []
    current_chars = 0
    last_id = ""

    def finish() -> None:
        nonlocal parts_written, current_chunks, current_chars, last_id
        if not current_chunks:
            return
        part_no = int(cursor.get("next_output_part", 0))
        filename = f"{part_no:03d}_{prefix}_PART_{part_no:03d}.txt"
        footer = f"\n---\nEND PART {part_no:03d}. Last completed passage: {last_id}\n"
        (OUTPUT_DIR / filename).write_text("".join(current_chunks) + footer, encoding="utf-8")
        cursor["next_output_part"] = part_no + 1
        parts_written += 1
        current_chunks = []
        current_chars = 0

    for p in passages:
        if parts_written >= max_output_files:
            run_state["stop_reason"] = "max_output_files_per_run"
            break
        block = passage_header(p) + p.text.rstrip() + "\n"
        if run_state["output_chars"] + len(block) > max_total_chars:
            run_state["stop_reason"] = "max_total_output_chars_per_run"
            break
        if current_chunks and current_chars + len(block) > max_chars:
            finish()
            if parts_written >= max_output_files:
                run_state["stop_reason"] = "max_output_files_per_run"
                break
        current_chunks.append(block)
        current_chars += len(block)
        run_state["output_chars"] += len(block)
        last_id = p.passage_id
    finish()
    return parts_written


def append_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_status(cursor: dict, request: dict, counters: dict, warnings: List[str], status: str) -> None:
    content = f"""# Nathan Words Extraction

Status: {status}
Mode: {request.get('mode')}
Strategy: {request.get('crawl_strategy')}
Generated UTC: {utc_now()}

This run:
- files processed: {counters.get('files_processed', 0)}
- dirs processed: {counters.get('dirs_processed', 0)}
- passages extracted: {counters.get('passages_extracted', 0)}
- review candidates: {counters.get('review_candidates', 0)}
- output parts written: {counters.get('parts_written', 0)}
- output chars written: {counters.get('output_chars', 0)}
- stop reason: {counters.get('stop_reason', '')}

Overall cursor:
- runs completed: {cursor.get('runs_completed', 0)}
- global passage count: {cursor.get('global_passage_count', 0)}
- next output part: {cursor.get('next_output_part', 0)}
- pending dirs: {len(cursor.get('pending_dirs', []))}
- pending files: {len(cursor.get('pending_files', []))}
- completed dirs: {len(cursor.get('completed_dirs', []))}
- completed files: {len(cursor.get('completed_files', []))}
- last stop reason: {cursor.get('last_stop_reason', '')}

Safety limits:
- max_runtime_seconds: {request.get('max_runtime_seconds')}
- max_files_per_run: {request.get('max_files_per_run')}
- max_dirs_per_run: {request.get('max_dirs_per_run')}
- max_passages_per_run: {request.get('max_passages_per_run')}
- max_output_files_per_run: {request.get('max_output_files_per_run')}
- max_total_output_chars_per_run: {request.get('max_total_output_chars_per_run')}
- max_chars_per_part: {request.get('max_chars_per_part')}
- max_single_passage_chars: {request.get('max_single_passage_chars')}

Open the numbered 000/001/002 extraction files in this folder to read extracted text.
Logs, indexes, and the resume cursor are in ⚒️_extraction_logs_and_indexes.

Warnings this run: {len(warnings)}
"""
    if warnings:
        content += "\nRecent warnings:\n" + "\n".join(f"- {w}" for w in warnings[-25:]) + "\n"
    (OUTPUT_DIR / "000_START_HERE_STATUS.txt").write_text(content, encoding="utf-8")


def main() -> int:
    ensure_dirs()
    request = load_request()
    cursor = load_cursor(request)
    start = time.monotonic()
    include_conf = set(request.get("include_confidence") or ["certain", "likely"])
    warnings: List[str] = []
    counters = {
        "files_processed": 0,
        "dirs_processed": 0,
        "files_discovered": 0,
        "dirs_discovered": 0,
        "files_skipped_non_text": 0,
        "dirs_skipped": 0,
        "passages_extracted": 0,
        "review_candidates": 0,
        "parts_written": 0,
        "output_chars": 0,
        "stop_reason": "complete_or_idle",
    }
    run_state = {"output_chars": 0, "stop_reason": ""}

    while True:
        elapsed = time.monotonic() - start
        if elapsed >= int(request["max_runtime_seconds"]):
            counters["stop_reason"] = "max_runtime_seconds"
            break
        if counters["files_processed"] >= int(request["max_files_per_run"]):
            counters["stop_reason"] = "max_files_per_run"
            break
        if counters["dirs_processed"] >= int(request["max_dirs_per_run"]):
            counters["stop_reason"] = "max_dirs_per_run"
            break
        if counters["passages_extracted"] >= int(request["max_passages_per_run"]):
            counters["stop_reason"] = "max_passages_per_run"
            break
        if run_state.get("stop_reason"):
            counters["stop_reason"] = run_state["stop_reason"]
            break

        if cursor.get("pending_files"):
            file_rel = cursor["pending_files"].pop(0)
            path = path_from_rel(file_rel)
            if not path.exists() or not path.is_file():
                warnings.append(f"Missing file skipped: {file_rel}")
                continue
            fs, passages, reviews, w = process_file(path, request)
            warnings.extend(w)
            counters["files_processed"] += 1
            cursor["completed_files"].append(file_rel)

            extracted: List[Passage] = []
            for p in passages:
                if p.confidence in include_conf:
                    cursor["global_passage_count"] = int(cursor.get("global_passage_count", 0)) + 1
                    p.passage_id = f"NATHAN-{cursor['global_passage_count']:09d}"
                    extracted.append(p)
            review_out: List[Passage] = []
            if request.get("include_review_candidates", True):
                for p in reviews:
                    cursor["global_passage_count"] = int(cursor.get("global_passage_count", 0)) + 1
                    p.passage_id = f"NATHAN-REVIEW-{cursor['global_passage_count']:09d}"
                    review_out.append(p)

            counters["passages_extracted"] += len(extracted)
            counters["review_candidates"] += len(review_out)
            if request.get("mode") == "extract":
                counters["parts_written"] += append_part(extracted, "EXTRACTED_NATHAN_WORDS", cursor, request, run_state)
                counters["parts_written"] += append_part(review_out, "REVIEW_CANDIDATES_MAYBE_NATHAN", cursor, request, run_state)
            append_csv(
                SOURCE_INDEX_PATH,
                [{
                    "path": fs.path,
                    "file_type": fs.file_type,
                    "size_bytes": fs.size_bytes,
                    "lines": fs.lines,
                    "status": fs.status,
                    "labels": "; ".join(fs.labels),
                    "date_signals": "; ".join(fs.date_signals[:50]),
                    "version_signals": "; ".join(fs.version_signals[:50]),
                    "extracted_passages": fs.extracted_passages,
                    "review_candidates": fs.review_candidates,
                    "warning": fs.warning,
                }],
                ["path", "file_type", "size_bytes", "lines", "status", "labels", "date_signals", "version_signals", "extracted_passages", "review_candidates", "warning"],
            )
            append_csv(
                VERSION_INDEX_PATH,
                ({
                    "passage_id": p.passage_id,
                    "source": p.source,
                    "lines": f"{p.start_line}-{p.end_line}",
                    "confidence": p.confidence,
                    "date_signal": best_date(p),
                    "version_signal": best_version(p),
                } for p in extracted + review_out),
                ["passage_id", "source", "lines", "confidence", "date_signal", "version_signal"],
            )
        elif cursor.get("pending_dirs"):
            dir_rel = cursor["pending_dirs"].pop(0)
            d = path_from_rel(dir_rel)
            if not d.exists() or not d.is_dir():
                warnings.append(f"Missing directory skipped: {dir_rel}")
                continue
            add_dir_children(cursor, dir_rel, request, counters, warnings)
            counters["dirs_processed"] += 1
            cursor["completed_dirs"].append(dir_rel)
        else:
            counters["stop_reason"] = "crawl_complete"
            break

    counters["output_chars"] = run_state["output_chars"]
    cursor["runs_completed"] = int(cursor.get("runs_completed", 0)) + 1
    cursor["last_stop_reason"] = counters["stop_reason"]
    save_cursor(cursor)
    write_status(cursor, request, counters, warnings, "complete" if counters["stop_reason"] in {"crawl_complete", "complete_or_idle"} else "paused_by_limit")
    (LOG_DIR / "NATHAN_CORPUS_EXTRACTION_WARNINGS_LAST_RUN.txt").write_text("\n".join(warnings) + "\n" if warnings else "No warnings.\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
