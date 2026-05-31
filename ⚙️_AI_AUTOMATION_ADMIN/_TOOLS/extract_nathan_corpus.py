#!/usr/bin/env python3
"""Nathan Corpus Extractor: raw extraction of Nathan/User words."""
from __future__ import annotations
import csv, json, os, re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
ADMIN_DIR = REPO_ROOT / "⚙️_AI_AUTOMATION_ADMIN"
REQUEST_PATH = ADMIN_DIR / "_AI_REQUESTS" / "nathan_corpus_extract_request.json"
OUTPUT_DIR = REPO_ROOT / "📚_NATHAN_WORDS_EXTRACTED"
TOOLS_DIR = OUTPUT_DIR / "⚒️_extraction_logs_and_indexes"
DEFAULT_MAX_CHARS_PER_PART = 200_000
TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".jsonl", ".yaml", ".yml", ".tex", ".py", ".js", ".ts", ".html", ".htm", ".xml", ".rst", ".log"}
SKIP_DIR_PARTS = {".git", ".github", "_NATHAN_CORPUS", "📚_NATHAN_WORDS_EXTRACTED", "⚙️_AI_AUTOMATION_ADMIN"}
ASSISTANT_LABELS = {"chatgpt", "assistant", "ai", "system", "model", "notebooklm", "gemini", "claude", "copilot"}
USER_LABEL_HINTS = {"user", "human", "me", "nathan", "satobloc", "satoblock", "author"}
SPEAKER_LINE_RE = re.compile(r"^\s*(?:#{1,6}\s*)?(?P<label>[A-Za-z0-9_ .@+\-]{2,80})\s*[:：]\s*(?P<rest>.*)$")
ISO_DATE_RE = re.compile(r"\b(20\d{2}|19\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])\b")
US_DATE_RE = re.compile(r"\b(0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.](20\d{2}|19\d{2})\b")
MONTH_DATE_RE = re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:20\d{2}|19\d{2})\b", re.I)
YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")
VERSION_PATTERNS = [re.compile(r"\bSAT\s*(?:-|_)?\s*(?:Mark\s*)?[VvXxIi0-9]+\b"), re.compile(r"\bSAT\s*(?:-|_)?\s*[A-Z]\b"), re.compile(r"\bSAT[_\s-]*(?:XYZ|RMS|QG|O)\b", re.I), re.compile(r"\bMark\s+[VvXxIi0-9]+\b")]

@dataclass
class Passage:
    source: str; start_line: int; end_line: int; label: str; text: str; confidence: str; method: str
    file_most_recent_date: str = ""; nearest_prior_date: str = ""; passage_dates: str = ""
    file_version_signal: str = ""; nearest_prior_version: str = ""; passage_versions: str = ""
    review: bool = False; passage_id: str = ""
@dataclass
class FileSurvey:
    path: str; file_type: str; size_bytes: int; lines: int = 0; status: str = "pending"
    labels: List[str] = field(default_factory=list); date_signals: List[str] = field(default_factory=list); version_signals: List[str] = field(default_factory=list)
    extracted_passages: int = 0; review_candidates: int = 0; warning: str = ""

def load_request() -> dict:
    try: return json.loads(REQUEST_PATH.read_text(encoding="utf-8")) if REQUEST_PATH.exists() else {"mode":"survey_only"}
    except Exception as exc: return {"mode":"survey_only", "request_error": str(exc)}
def is_text_like(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or (not path.suffix and path.name.upper() in {"LICENSE", "README", "NOTICE"})
def should_skip(path: Path) -> bool:
    return bool(set(path.relative_to(REPO_ROOT).parts) & SKIP_DIR_PARTS)
def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace(os.sep, "/")
def read_text_safely(path: Path) -> Tuple[Optional[str], str]:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try: return path.read_text(encoding=enc), ""
        except UnicodeDecodeError: continue
        except Exception as exc: return None, str(exc)
    return None, "Could not decode as text"
def normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip()).strip("#*[]() ")
def label_kind(label: str) -> str:
    low = re.sub(r"[^a-z0-9@._+-]+", "", normalize_label(label).lower())
    if low in ASSISTANT_LABELS or any(x in low for x in ("chatgpt", "assistant", "notebooklm")): return "assistant"
    if low in USER_LABEL_HINTS or "nathan" in low or "satobloc" in low or "@" in low: return "user"
    if re.search(r"[A-Za-z0-9_@.+-]{3,}", low) and low not in ASSISTANT_LABELS: return "probable_user"
    return "unknown"
def extract_dates(text: str) -> List[str]:
    found=[]
    for m in ISO_DATE_RE.finditer(text):
        y,mo,d=m.groups(); found.append(f"{int(y):04d}-{int(mo):02d}-{int(d):02d}")
    for m in US_DATE_RE.finditer(text):
        mo,d,y=m.groups(); found.append(f"{int(y):04d}-{int(mo):02d}-{int(d):02d}")
    found += [m.group(0) for m in MONTH_DATE_RE.finditer(text)] + [m.group(1) for m in YEAR_RE.finditer(text)]
    return sorted(set(found))
def most_recent_date_signal(dates: Sequence[str]) -> str:
    iso=[d for d in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)]
    if iso: return max(iso)
    years=[d for d in dates if re.fullmatch(r"\d{4}", d)]
    return max(years) if years else (dates[-1] if dates else "")
def extract_versions(text: str) -> List[str]:
    found=[]
    for pat in VERSION_PATTERNS: found += [re.sub(r"\s+", " ", m.group(0).strip()) for m in pat.finditer(text)]
    return sorted(set(found))
def compact_versions(values: str, max_items:int=4) -> str:
    return "; ".join([p.strip() for p in values.split(";") if p.strip()][:max_items])
def best_date(p: Passage) -> str:
    return p.passage_dates or p.nearest_prior_date or p.file_most_recent_date
def best_version(p: Passage) -> str:
    return p.passage_versions or p.nearest_prior_version or compact_versions(p.file_version_signal)
def find_labels(lines: Sequence[str]) -> List[str]:
    labels=[]
    for line in lines[:20000]:
        m=SPEAKER_LINE_RE.match(line)
        if m:
            label=normalize_label(m.group("label"))
            if label_kind(label) in {"user","probable_user","assistant"}: labels.append(label)
    return sorted(set(labels))[:100]
def looks_like_nathan(text: str) -> bool:
    low=text.lower(); signals=0
    for token in ["sat","filament","timesheet","worldline","theta","θ","drag","epistem","ontolog","no.","ok.","actually","not because","scalar-angular"]:
        if token in low: signals += 1
    if "..." in text or "…" in text: signals += 1
    return signals >= 4 and len(text.strip()) > 120

def split_speaker_passages(source: str, lines: Sequence[str], file_dates: List[str], file_versions: List[str]):
    passages=[]; reviews=[]; warnings=[]; current_label=None; current_kind="unknown"; current_start=1; buffer=[]; nearest_date=""; nearest_version=""
    def flush(end_line:int):
        nonlocal buffer,current_label,current_kind,current_start,nearest_date,nearest_version
        if current_label is None or not buffer: buffer=[]; return
        text="\n".join(buffer).strip("\n")
        if not text.strip(): buffer=[]; return
        p_dates=extract_dates(text); p_versions=extract_versions(text)
        p=Passage(source,current_start,end_line,current_label,text,"certain" if current_kind=="user" else "likely" if current_kind=="probable_user" else "exclude","explicit speaker label" if current_kind=="user" else "non-ChatGPT speaker label" if current_kind=="probable_user" else "excluded assistant/system label",most_recent_date_signal(file_dates),nearest_date,"; ".join(p_dates),"; ".join(file_versions[:12]),nearest_version,"; ".join(p_versions))
        if current_kind in {"user","probable_user"}: passages.append(p)
        elif current_kind=="unknown" and looks_like_nathan(text): p.confidence="review"; p.method="style/topic candidate"; p.review=True; reviews.append(p)
        buffer=[]
    for idx,line in enumerate(lines,start=1):
        ld=extract_dates(line); lv=extract_versions(line)
        if ld: nearest_date=most_recent_date_signal(ld)
        if lv: nearest_version="; ".join(lv[:4])
        m=SPEAKER_LINE_RE.match(line)
        if m:
            label=normalize_label(m.group("label")); kind=label_kind(label)
            if kind in {"user","probable_user","assistant"}:
                flush(idx-1); current_label=label; current_kind=kind; current_start=idx; rest=m.group("rest"); buffer=[rest] if rest else []; continue
        if current_label is not None: buffer.append(line)
    flush(len(lines)); return passages,reviews,warnings

def survey_and_extract_file(path: Path, mode: str):
    source=rel(path); fs=FileSurvey(source,path.suffix.lower() or "extensionless",path.stat().st_size)
    text,err=read_text_safely(path)
    if text is None: fs.status="skipped"; fs.warning=err; return fs,[],[],[f"{source}: {err}"]
    lines=text.splitlines(); fs.lines=len(lines); fs.status="scanned"; fs.date_signals=extract_dates(source+"\n"+text[:500000]); fs.version_signals=extract_versions(source+"\n"+text[:300000]); fs.labels=find_labels(lines)
    passages,reviews,warnings=split_speaker_passages(source,lines,fs.date_signals,fs.version_signals); fs.extracted_passages=len(passages); fs.review_candidates=len(reviews); return fs,passages,reviews,warnings

def discover_files() -> List[Path]:
    return sorted([p for p in REPO_ROOT.rglob("*") if p.is_file() and not should_skip(p) and is_text_like(p)], key=lambda p: rel(p).lower())
def ensure_dirs(): OUTPUT_DIR.mkdir(parents=True,exist_ok=True); TOOLS_DIR.mkdir(parents=True,exist_ok=True)
def write_status(total, scanned, passages, parts, current, status, warnings, request):
    ensure_dirs(); pct=0 if total==0 else scanned/total; bar_len=24; done=int(pct*bar_len); bar="#"*done+"-"*(bar_len-done)
    content=f"""# Nathan Words Extraction

Status: {status}
Mode: {request.get('mode','survey_only')}
Progress: [{bar}] {pct*100:.1f}%
Files scanned: {scanned} / {total}
Passages found: {passages}
Readable text files written: {parts}
Last source scanned: {current}
Warnings: {len(warnings)}
Generated UTC: {datetime.now(timezone.utc).isoformat()}

Open the AA/AB text files in this folder to read extracted text.
Detailed logs and indexes are in ⚒️_extraction_logs_and_indexes.
"""
    (OUTPUT_DIR/"00_START_HERE_STATUS.txt").write_text(content,encoding="utf-8")
def passage_header(p: Passage) -> str:
    bits=[f"{p.passage_id} | {p.label} | {p.confidence}", f"source: {p.source} lines {p.start_line}-{p.end_line}"]
    d=best_date(p); v=best_version(p)
    if d: bits.append(f"date: {d}")
    if v: bits.append(f"version: {v}")
    return "\n---\n"+"\n".join(bits)+"\n---\n\n"
def write_chunked(passages: List[Passage], prefix: str, max_chars:int) -> int:
    if not passages: return 0
    part=1; chars=0; current=[]; last_id=""
    def finish(part_no,chunks,last):
        if chunks: (OUTPUT_DIR/f"{prefix}_PART_{part_no:04d}.txt").write_text("".join(chunks)+f"\n---\nEND PART {part_no:04d}. Last completed passage: {last}\n",encoding="utf-8")
    for p in passages:
        block=passage_header(p)+p.text.rstrip()+"\n"
        if current and chars+len(block)>max_chars: finish(part,current,last_id); part+=1; current=[]; chars=0
        current.append(block); chars+=len(block); last_id=p.passage_id
    finish(part,current,last_id); return part
def write_csv(path:Path, rows:Iterable[Dict[str,object]], fieldnames:Sequence[str]):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames); w.writeheader(); [w.writerow(r) for r in rows]
def main():
    request=load_request(); mode=request.get("mode","survey_only"); max_chars=int(request.get("max_chars_per_part") or DEFAULT_MAX_CHARS_PER_PART); stop_after=request.get("stop_after_files"); include_conf=set(request.get("include_confidence") or ["certain","likely"])
    ensure_dirs(); files=discover_files(); surveys=[]; all_passages=[]; all_reviews=[]; warnings=[]; scanned=0; write_status(len(files),0,0,0,"starting","running",warnings,request)
    for path in files:
        if stop_after is not None and scanned>=int(stop_after): warnings.append(f"Stopped early because stop_after_files={stop_after}"); break
        fs,passages,reviews,w=survey_and_extract_file(path,mode); scanned+=1; surveys.append(fs); warnings.extend(w)
        for p in passages:
            if p.confidence in include_conf: p.passage_id=f"NATHAN-{len(all_passages)+1:06d}"; all_passages.append(p)
        if request.get("include_review_candidates",True):
            for p in reviews: p.passage_id=f"NATHAN-REVIEW-{len(all_reviews)+1:06d}"; all_reviews.append(p)
        if scanned%25==0: write_status(len(files),scanned,len(all_passages),0,fs.path,"running",warnings,request)
    survey=["# Nathan Corpus Survey\n",f"Generated UTC: {datetime.now(timezone.utc).isoformat()}\n",f"Files discovered: {len(files)}\n",f"Files scanned: {scanned}\n",f"Passages identified: {len(all_passages)}\n",f"Review candidates: {len(all_reviews)}\n\n"]
    for fs in surveys:
        if fs.extracted_passages or fs.review_candidates or fs.labels: survey.append(f"- {fs.path}\n  labels: {', '.join(fs.labels[:20])}\n  extracted: {fs.extracted_passages}; review: {fs.review_candidates}\n  date: {most_recent_date_signal(fs.date_signals)}\n  version: {', '.join(fs.version_signals[:8])}\n")
    (TOOLS_DIR/"NATHAN_CORPUS_SURVEY.txt").write_text("".join(survey),encoding="utf-8")
    write_csv(TOOLS_DIR/"NATHAN_CORPUS_SOURCE_INDEX.csv",(fs.__dict__|{"labels":"; ".join(fs.labels),"date_signals":"; ".join(fs.date_signals[:50]),"version_signals":"; ".join(fs.version_signals[:50])} for fs in surveys),["path","file_type","size_bytes","lines","status","labels","date_signals","version_signals","extracted_passages","review_candidates","warning"])
    write_csv(TOOLS_DIR/"NATHAN_CORPUS_VERSION_DATE_INDEX.csv",({"passage_id":p.passage_id,"source":p.source,"lines":f"{p.start_line}-{p.end_line}","confidence":p.confidence,"date_signal":best_date(p),"version_signal":best_version(p)} for p in all_passages+all_reviews),["passage_id","source","lines","confidence","date_signal","version_signal"])
    parts=0
    if mode=="extract":
        parts+=write_chunked(all_passages,"AA_EXTRACTED_NATHAN_WORDS",max_chars)
        if all_reviews: parts+=write_chunked(all_reviews,"AB_REVIEW_CANDIDATES_MAYBE_NATHAN",max_chars)
    else:
        parts+=write_chunked(all_passages[:100],"AA_SAMPLE_EXTRACTED_WORDS",max_chars)
        if all_reviews: parts+=write_chunked(all_reviews[:100],"AB_SAMPLE_REVIEW_CANDIDATES",max_chars)
    (TOOLS_DIR/"NATHAN_CORPUS_EXTRACTION_WARNINGS.txt").write_text("\n".join(warnings)+"\n" if warnings else "No warnings.\n",encoding="utf-8")
    write_status(len(files),scanned,len(all_passages),parts,surveys[-1].path if surveys else "","complete",warnings,request)
    return 0
if __name__=="__main__": raise SystemExit(main())
