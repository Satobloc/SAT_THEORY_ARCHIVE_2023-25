#!/usr/bin/env python3
"""
Nathan Corpus Extractor

Raw, non-editing extraction/survey tool for SAT_THEORY_ARCHIVE_2023-25.

Goals:
- Survey text-like archive files for likely Nathan/User-authored passages.
- Extract mechanically identifiable Nathan/User passages without polishing.
- Preserve source metadata, date signals, version signals, and resume/progress markers.
- Chunk output files safely.

This is intentionally conservative about final inclusion and broad about review candidates.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
REQUEST_PATH = REPO_ROOT / "_AI_REQUESTS" / "nathan_corpus_extract_request.json"
OUTPUT_DIR = REPO_ROOT / "_NATHAN_CORPUS"

DEFAULT_MAX_CHARS_PER_PART = 200_000

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".json", ".jsonl", ".yaml", ".yml",
    ".tex", ".py", ".js", ".ts", ".html", ".htm", ".xml", ".rst", ".log"
}

SKIP_DIR_PARTS = {
    ".git", ".github", "_NATHAN_CORPUS"
}

# Do not scan generated output as input, except PDF text bridge files are useful.
SKIP_FILE_PATTERNS = [
    re.compile(r"NATHAN_CORPUS_", re.I),
]

ASSISTANT_LABELS = {
    "chatgpt", "assistant", "ai", "system", "model", "notebooklm", "gemini", "claude", "copilot"
}

USER_LABEL_HINTS = {
    "user", "human", "me", "nathan", "satobloc", "satoblock", "author"
}

SPEAKER_LINE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?P<label>[A-Za-z0-9_ .@+\-]{2,80})\s*[:：]\s*(?P<rest>.*)$"
)

CHAT_EXPORT_RE = re.compile(r"^\s*(User|Nathan|Human|Assistant|ChatGPT|System)\s*$", re.I)

ISO_DATE_RE = re.compile(r"\b(20\d{2}|19\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])\b")
US_DATE_RE = re.compile(r"\b(0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.](20\d{2}|19\d{2})\b")
MONTH_DATE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:20\d{2}|19\d{2})\b",
    re.I,
)
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


def load_request() -> dict:
    if REQUEST_PATH.exists():
        try:
            return json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"mode": "survey_only", "request_error": str(exc)}
    return {"mode": "survey_only"}


def is_text_like(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if not path.suffix and path.name.upper() in {"LICENSE", "README", "NOTICE"}:
        return True
    return False


def should_skip(path: Path) -> bool:
    rel_parts = set(path.relative_to(REPO_ROOT).parts)
    if rel_parts & SKIP_DIR_PARTS:
        return True
    name = path.name
    return any(p.search(name) for p in SKIP_FILE_PATTERNS)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace(os.sep, "/")


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
    low = normalize_label(label).lower()
    low_simple = re.sub(r"[^a-z0-9@._+-]+", "", low)
    if low_simple in ASSISTANT_LABELS or any(x in low_simple for x in ("chatgpt", "assistant", "notebooklm")):
        return "assistant"
    if low_simple in USER_LABEL_HINTS or "nathan" in low_simple or "satobloc" in low_simple or "@" in low_simple:
        return "user"
    # Project rule from Nathan: most non-ChatGPT usernames are probably him.
    if re.search(r"[A-Za-z0-9_@.+-]{3,}", low_simple) and low_simple not in ASSISTANT_LABELS:
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
    for m in MONTH_DATE_RE.finditer(text):
        found.append(m.group(0))
    # Years are weaker but useful in old fragments and version folders.
    for m in YEAR_RE.finditer(text):
        found.append(m.group(1))
    return sorted(set(found))


def most_recent_date_signal(dates: Sequence[str]) -> str:
    # Prefer ISO full dates for max; otherwise lexicographic year/month text is only a signal.
    iso = [d for d in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)]
    if iso:
        return max(iso)
    years = [d for d in dates if re.fullmatch(r"\d{4}", d)]
    if years:
        return max(years)
    return dates[-1] if dates else ""


def extract_versions(text: str) -> List[str]:
    found: List[str] = []
    for pat in VERSION_PATTERNS:
        for m in pat.finditer(text):
            found.append(re.sub(r"\s+", " ", m.group(0).strip()))
    return sorted(set(found))


def find_labels(lines: Sequence[str]) -> List[str]:
    labels = []
    for line in lines[:20000]:
        m = SPEAKER_LINE_RE.match(line)
        if not m:
            continue
        label = normalize_label(m.group("label"))
        if len(label) <= 80:
            kind = label_kind(label)
            if kind in {"user", "probable_user", "assistant"}:
                labels.append(label)
    return sorted(set(labels))[:100]


def split_speaker_passages(source: str, lines: Sequence[str], file_dates: List[str], file_versions: List[str]) -> Tuple[List[Passage], List[Passage], List[str]]:
    passages: List[Passage] = []
    reviews: List[Passage] = []
    warnings: List[str] = []
    current_label: Optional[str] = None
    current_kind: str = "unknown"
    current_start = 1
    buffer: List[str] = []
    nearest_date = ""
    nearest_version = ""

    def flush(end_line: int) -> None:
        nonlocal buffer, current_label, current_kind, current_start, nearest_date, nearest_version
        if current_label is None or not buffer:
            buffer = []
            return
        text = "\n".join(buffer).strip("\n")
        if not text.strip():
            buffer = []
            return
        p_dates = extract_dates(text)
        p_versions = extract_versions(text)
        base = Passage(
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
            passages.append(base)
        elif current_kind == "unknown" and looks_like_nathan(text):
            base.confidence = "review"
            base.method = "style/topic candidate"
            base.review = True
            reviews.append(base)
        buffer = []

    for idx, line in enumerate(lines, start=1):
        line_dates = extract_dates(line)
        if line_dates:
            nearest_date = most_recent_date_signal(line_dates)
        line_versions = extract_versions(line)
        if line_versions:
            nearest_version = "; ".join(line_versions[:4])

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


def looks_like_nathan(text: str) -> bool:
    low = text.lower()
    signals = 0
    for token in ["sat", "filament", "timesheet", "worldline", "theta", "θ", "drag", "epistem", "ontolog", "no.", "ok.", "actually", "not because", "scalar-angular"]:
        if token in low:
            signals += 1
    if "..." in text or "…" in text:
        signals += 1
    return signals >= 4 and len(text.strip()) > 120


def survey_and_extract_file(path: Path, mode: str) -> Tuple[FileSurvey, List[Passage], List[Passage], List[str]]:
    source = rel(path)
    fs = FileSurvey(path=source, file_type=path.suffix.lower() or "extensionless", size_bytes=path.stat().st_size)
    text, err = read_text_safely(path)
    if text is None:
        fs.status = "skipped"
        fs.warning = err
        return fs, [], [], [f"{source}: {err}"]
    lines = text.splitlines()
    fs.lines = len(lines)
    fs.status = "scanned"
    file_text_sample = source + "\n" + text[:500000]
    fs.date_signals = extract_dates(file_text_sample)
    fs.version_signals = extract_versions(source + "\n" + text[:300000])
    fs.labels = find_labels(lines)
    passages, reviews, warnings = split_speaker_passages(source, lines, fs.date_signals, fs.version_signals)
    fs.extracted_passages = len(passages)
    fs.review_candidates = len(reviews)
    return fs, passages, reviews, warnings


def discover_files() -> List[Path]:
    files: List[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path):
            continue
        if is_text_like(path):
            files.append(path)
    return sorted(files, key=lambda p: rel(p).lower())


def write_status(total: int, scanned: int, passages: int, parts: int, current: str, status: str, warnings: List[str], request: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pct = 0 if total == 0 else scanned / total
    bar_len = 24
    done = int(pct * bar_len)
    bar = "#" * done + "-" * (bar_len - done)
    content = f"""# NATHAN CORPUS EXTRACTION STATUS

Repository: Satobloc/SAT_THEORY_ARCHIVE_2023-25
Generated UTC: {datetime.now(timezone.utc).isoformat()}
Mode: {request.get('mode', 'survey_only')}
Request ID: {request.get('request_id', '')}
Status: {status}

Progress: [{bar}] {pct*100:.1f}%
Files scanned: {scanned} / {total}
Passages extracted: {passages}
Output parts written: {parts}
Current / last source: {current}

Safety settings:
- max_chars_per_part: {request.get('max_chars_per_part', DEFAULT_MAX_CHARS_PER_PART)}
- include_confidence: {request.get('include_confidence', [])}
- include_review_candidates: {request.get('include_review_candidates', True)}
- stop_after_files: {request.get('stop_after_files', None)}

Warnings count: {len(warnings)}

Last warnings:
"""
    for w in warnings[-20:]:
        content += f"- {w}\n"
    (OUTPUT_DIR / "NATHAN_CORPUS_EXTRACTION_STATUS.txt").write_text(content, encoding="utf-8")


def passage_header(p: Passage) -> str:
    return f"""================================================================================
PASSAGE ID: {p.passage_id}
SOURCE: {p.source}
LINES: {p.start_line}-{p.end_line}
DETECTED LABEL: {p.label}
CONFIDENCE: {p.confidence}
EXTRACTION METHOD: {p.method}

DATE SIGNALS:
- Source most recent mentioned date: {p.file_most_recent_date}
- Nearest prior date marker: {p.nearest_prior_date}
- Date(s) inside passage: {p.passage_dates}

VERSION SIGNALS:
- Folder/file/source version signal(s): {p.file_version_signal}
- Nearest prior version marker: {p.nearest_prior_version}
- Version(s) inside passage: {p.passage_versions}
================================================================================
"""


def write_chunked(passages: List[Passage], prefix: str, max_chars: int) -> int:
    if not passages:
        return 0
    part = 1
    chars = 0
    current: List[str] = []

    def finish(part_no: int, chunks: List[str]) -> None:
        if not chunks:
            return
        footer = f"\n# END {prefix} PART {part_no:04d}\nLast completed passage: {passages[min(len(passages)-1, written_indices[0])].passage_id if written_indices else ''}\n"
        out = OUTPUT_DIR / f"{prefix}_PART_{part_no:04d}.txt"
        out.write_text("".join(chunks) + footer, encoding="utf-8")

    written_indices = [-1]
    for i, p in enumerate(passages):
        block = passage_header(p) + "\n" + p.text.rstrip() + "\n\n"
        if current and chars + len(block) > max_chars:
            finish(part, current)
            part += 1
            current = []
            chars = 0
        current.append(block)
        chars += len(block)
        written_indices[0] = i
    finish(part, current)
    return part


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    request = load_request()
    mode = request.get("mode", "survey_only")
    max_chars = int(request.get("max_chars_per_part") or DEFAULT_MAX_CHARS_PER_PART)
    stop_after = request.get("stop_after_files")
    include_conf = set(request.get("include_confidence") or ["certain", "likely"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = discover_files()
    surveys: List[FileSurvey] = []
    all_passages: List[Passage] = []
    all_reviews: List[Passage] = []
    warnings: List[str] = []
    scanned = 0

    write_status(len(files), 0, 0, 0, "starting", "running", warnings, request)

    for idx, path in enumerate(files, start=1):
        if stop_after is not None and scanned >= int(stop_after):
            warnings.append(f"Stopped early because stop_after_files={stop_after}")
            break
        fs, passages, reviews, w = survey_and_extract_file(path, mode)
        scanned += 1
        surveys.append(fs)
        warnings.extend(w)
        for p in passages:
            if p.confidence in include_conf:
                p.passage_id = f"NATHAN-{len(all_passages)+1:06d}"
                all_passages.append(p)
        if request.get("include_review_candidates", True):
            for p in reviews:
                p.passage_id = f"NATHAN-REVIEW-{len(all_reviews)+1:06d}"
                all_reviews.append(p)
        if scanned % 25 == 0:
            write_status(len(files), scanned, len(all_passages), 0, fs.path, "running", warnings, request)

    # Survey files
    survey_lines = [
        "# NATHAN CORPUS SURVEY\n",
        f"Generated UTC: {datetime.now(timezone.utc).isoformat()}\n",
        f"Files discovered: {len(files)}\n",
        f"Files scanned: {scanned}\n",
        f"Passages identified for extraction: {len(all_passages)}\n",
        f"Review candidates: {len(all_reviews)}\n\n",
        "## Files with extracted passages or labels\n\n",
    ]
    for fs in surveys:
        if fs.extracted_passages or fs.review_candidates or fs.labels:
            survey_lines.append(f"- {fs.path}\n")
            survey_lines.append(f"  - status: {fs.status}; lines: {fs.lines}; size: {fs.size_bytes}\n")
            survey_lines.append(f"  - labels: {', '.join(fs.labels[:20])}\n")
            survey_lines.append(f"  - extracted passages: {fs.extracted_passages}; review candidates: {fs.review_candidates}\n")
            survey_lines.append(f"  - most recent date signal: {most_recent_date_signal(fs.date_signals)}\n")
            survey_lines.append(f"  - version signals: {', '.join(fs.version_signals[:10])}\n")
    (OUTPUT_DIR / "NATHAN_CORPUS_SURVEY.txt").write_text("".join(survey_lines), encoding="utf-8")

    write_csv(
        OUTPUT_DIR / "NATHAN_CORPUS_SOURCE_INDEX.csv",
        (fs.__dict__ | {
            "labels": "; ".join(fs.labels),
            "date_signals": "; ".join(fs.date_signals[:50]),
            "version_signals": "; ".join(fs.version_signals[:50]),
        } for fs in surveys),
        ["path", "file_type", "size_bytes", "lines", "status", "labels", "date_signals", "version_signals", "extracted_passages", "review_candidates", "warning"],
    )

    version_rows = []
    for p in all_passages + all_reviews:
        version_rows.append({
            "passage_id": p.passage_id,
            "source": p.source,
            "lines": f"{p.start_line}-{p.end_line}",
            "confidence": p.confidence,
            "source_most_recent_date": p.file_most_recent_date,
            "nearest_prior_date": p.nearest_prior_date,
            "passage_dates": p.passage_dates,
            "file_version_signal": p.file_version_signal,
            "nearest_prior_version": p.nearest_prior_version,
            "passage_versions": p.passage_versions,
        })
    write_csv(
        OUTPUT_DIR / "NATHAN_CORPUS_VERSION_DATE_INDEX.csv",
        version_rows,
        ["passage_id", "source", "lines", "confidence", "source_most_recent_date", "nearest_prior_date", "passage_dates", "file_version_signal", "nearest_prior_version", "passage_versions"],
    )

    parts = 0
    if mode == "extract":
        parts += write_chunked(all_passages, "NATHAN_CORPUS", max_chars)
        if all_reviews:
            parts += write_chunked(all_reviews, "NATHAN_CORPUS_REVIEW_CANDIDATES", max_chars)
    else:
        # Survey-only mode writes small sample files so the pattern can be inspected without flooding the repo.
        sample = all_passages[:25]
        review_sample = all_reviews[:25]
        if sample:
            parts += write_chunked(sample, "NATHAN_CORPUS_SAMPLE", max_chars)
        if review_sample:
            parts += write_chunked(review_sample, "NATHAN_CORPUS_REVIEW_SAMPLE", max_chars)

    if warnings:
        (OUTPUT_DIR / "NATHAN_CORPUS_EXTRACTION_WARNINGS.txt").write_text("\n".join(warnings) + "\n", encoding="utf-8")
    else:
        (OUTPUT_DIR / "NATHAN_CORPUS_EXTRACTION_WARNINGS.txt").write_text("No warnings.\n", encoding="utf-8")

    write_status(len(files), scanned, len(all_passages), parts, surveys[-1].path if surveys else "", "complete", warnings, request)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
