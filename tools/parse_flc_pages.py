#!/usr/bin/env python3
"""Parse FLC scan pages into provisional readable text with printed-page order.

Important geometry: each PDF page is ONE photographed magazine page, usually
with two prose columns. The PDF page sequence is not reliable printed reading
order. Therefore the correct pipeline is:

    photographed page -> OCR layout -> column-aware text -> printed page number
    -> printed-page ordering -> source-reviewed story ranges

This deliberately does not split a PDF page into two facing pages. Earlier
experiments showed that doing so mistakes the magazine's two text columns for
separate pages.

Source PDFs are never modified. Machine text remains provisional until checked
against the facsimile.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

PARSER_VERSION = "2026-09-23.2"


def run(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
    )


def safe_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def page_count(pdf: Path) -> int:
    p = run(["pdfinfo", str(pdf)], 120)
    if p.returncode == 0:
        m = re.search(r"(?m)^Pages:\s+(\d+)\s*$", p.stdout)
        if m:
            return int(m.group(1))
    raise RuntimeError(f"could not determine PDF page count for {pdf}: {p.stderr[-500:]}")


def parse_tsv(tsv: str) -> tuple[int, int, list[dict[str, Any]]]:
    reader = csv.DictReader(io.StringIO(tsv), delimiter="\t")
    width = height = 0
    words: list[dict[str, Any]] = []
    for row in reader:
        try:
            level = int(row.get("level") or 0)
            if level == 1:
                width = int(row.get("width") or 0)
                height = int(row.get("height") or 0)
                continue
            if level != 5:
                continue
            text = (row.get("text") or "").strip()
            conf = float(row.get("conf") or -1)
            if not text or conf < 0:
                continue
            words.append(
                {
                    "text": text,
                    "conf": conf,
                    "left": int(row.get("left") or 0),
                    "top": int(row.get("top") or 0),
                    "width": int(row.get("width") or 0),
                    "height": int(row.get("height") or 0),
                    "block_num": int(row.get("block_num") or 0),
                    "par_num": int(row.get("par_num") or 0),
                    "line_num": int(row.get("line_num") or 0),
                    "word_num": int(row.get("word_num") or 0),
                }
            )
        except (ValueError, TypeError):
            continue
    return width, height, words


def normalize_numberish(raw: str) -> str:
    token = unicodedata.normalize("NFKC", raw)
    token = token.replace("–", "-").replace("—", "-").replace("~", "-")
    # Conservative OCR confusions seen in FLC margin numbers.
    trans = str.maketrans({"I": "1", "l": "1", "|": "1", "!": "1", "O": "0", "o": "0"})
    return token.translate(trans).strip()


def page_number_candidates(
    words: list[dict[str, Any]], page_width: int, page_height: int, max_printed_page: int
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for word in words:
        raw = word["text"].strip()
        if not raw or len(raw) > 10:
            continue
        cx = word["left"] + word["width"] / 2
        cy = word["top"] + word["height"] / 2
        outer = cx < page_width * 0.16 or cx > page_width * 0.84
        if not outer:
            continue

        token = normalize_numberish(raw)
        original_has_digit = bool(re.search(r"\d", raw))
        has_frame = "-" in token
        if not original_has_digit and not has_frame:
            continue
        m = re.fullmatch(r"[^0-9]{0,3}(\d{1,3})[^0-9]{0,3}", token)
        if not m:
            continue
        number = int(m.group(1))
        if not (1 <= number <= max_printed_page):
            continue

        score = 3.0
        if has_frame:
            score += 4.0
        if token.startswith("-") and token.endswith("-"):
            score += 3.0
        if page_height * 0.08 <= cy <= page_height * 0.92:
            score += 1.0
        if word["conf"] >= 50:
            score += 1.0
        if word["conf"] >= 80:
            score += 1.0
        # Conventional FLC placement: even page number toward the left outer
        # margin, odd page number toward the right outer margin.
        if (number % 2 == 0 and cx < page_width / 2) or (number % 2 == 1 and cx > page_width / 2):
            score += 2.0

        candidates.append(
            {
                "number": number,
                "raw_token": raw,
                "normalized_token": token,
                "score": round(score, 2),
                "confidence": round(word["conf"], 2),
                "x": round(cx, 1),
                "y": round(cy, 1),
            }
        )

    # Combine split tokens on the same OCR line in the outer margin, e.g.
    # '-', '19', '-'. This is deliberately secondary to a single strong token.
    by_line: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for word in words:
        cx = word["left"] + word["width"] / 2
        if cx < page_width * 0.16 or cx > page_width * 0.84:
            by_line.setdefault((word["block_num"], word["par_num"], word["line_num"]), []).append(word)
    for group in by_line.values():
        if not group:
            continue
        group.sort(key=lambda w: w["left"])
        raw = "".join(w["text"] for w in group)
        if len(raw) > 14:
            continue
        token = normalize_numberish(raw)
        m = re.fullmatch(r"[^0-9]{0,3}(\d{1,3})[^0-9]{0,3}", token)
        if not m:
            continue
        number = int(m.group(1))
        if not (1 <= number <= max_printed_page):
            continue
        cx = statistics.mean(w["left"] + w["width"] / 2 for w in group)
        cy = statistics.mean(w["top"] + w["height"] / 2 for w in group)
        conf = statistics.mean(w["conf"] for w in group)
        score = 4.0 + (4.0 if "-" in token else 0.0)
        if token.startswith("-") and token.endswith("-"):
            score += 3.0
        if (number % 2 == 0 and cx < page_width / 2) or (number % 2 == 1 and cx > page_width / 2):
            score += 2.0
        candidates.append(
            {
                "number": number,
                "raw_token": raw,
                "normalized_token": token,
                "score": round(score, 2),
                "confidence": round(conf, 2),
                "x": round(cx, 1),
                "y": round(cy, 1),
                "combined_line": True,
            }
        )

    # Deduplicate same number, retaining strongest evidence.
    best: dict[int, dict[str, Any]] = {}
    for candidate in candidates:
        n = candidate["number"]
        if n not in best or (candidate["score"], candidate["confidence"]) > (best[n]["score"], best[n]["confidence"]):
            best[n] = candidate
    return sorted(best.values(), key=lambda c: (-c["score"], -c["confidence"], c["number"]))


def choose_page_number(candidates: list[dict[str, Any]]) -> tuple[int | None, str]:
    if not candidates:
        return None, "unresolved"
    top = candidates[0]
    if top["score"] < 7:
        return None, "weak-candidate-only"
    if len(candidates) > 1 and candidates[1]["score"] >= top["score"] - 1 and candidates[1]["number"] != top["number"]:
        return None, "ambiguous-candidates"
    return int(top["number"]), "outer-margin-ocr"


def clean_body_text(text: str, issue: dict[str, Any]) -> str:
    """Keep prose order but remove obvious non-body page furniture."""
    title_norms = {norm(s["title"]) for s in issue["stories"]}
    author_norms = {norm(s["author"]) for s in issue["stories"]}
    lines: list[str] = []
    blank = False
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            if lines and not blank:
                lines.append("")
            blank = True
            continue
        blank = False
        n = norm(line)
        if not n:
            continue
        if re.fullmatch(r"[-–—~ ]*\d{1,3}[-–—~ ]*", line):
            continue
        if n in title_norms or n in author_norms:
            continue
        lines.append(line)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def story_hits(text: str, issue: dict[str, Any]) -> list[dict[str, Any]]:
    ntext = norm(text)
    hits: list[dict[str, Any]] = []
    for story in issue["stories"]:
        best = 0
        for alias in story.get("aliases", [story["title"]]):
            a = norm(alias)
            if a and a in ntext:
                best = max(best, len(a))
        if best:
            hits.append({"story_id": story["id"], "slug": story["slug"], "title": story["title"], "score": best})
    return sorted(hits, key=lambda h: (-h["score"], h["story_id"]))


def interpolate_local_sequences(records: list[dict[str, Any]]) -> None:
    """Fill only exact ±1-per-PDF-page runs bracketed by detected numbers."""
    changed = True
    while changed:
        changed = False
        known = [(i, r["printed_page"]) for i, r in enumerate(records) if r.get("printed_page") is not None]
        for (i, a), (j, b) in zip(known, known[1:]):
            gap = j - i
            if gap <= 1:
                continue
            delta = b - a
            if abs(delta) != gap:
                continue
            step = 1 if delta > 0 else -1
            for k in range(i + 1, j):
                if records[k].get("printed_page") is None:
                    records[k]["printed_page"] = a + step * (k - i)
                    records[k]["printed_page_basis"] = "exact-local-sequence-interpolation"
                    changed = True


def flag_duplicate_numbers(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_num: dict[int, list[int]] = {}
    for r in records:
        if r.get("printed_page") is not None:
            by_num.setdefault(int(r["printed_page"]), []).append(int(r["pdf_page"]))
    conflicts = []
    for number, pdf_pages in sorted(by_num.items()):
        if len(pdf_pages) > 1:
            conflicts.append({"printed_page": number, "pdf_pages": pdf_pages, "flag": "duplicate-printed-page-assignment"})
            for r in records:
                if r.get("printed_page") == number:
                    r.setdefault("flags", []).append("duplicate-printed-page-assignment")
    return conflicts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--issue-id", required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dpi", type=int, default=140)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    for tool in ("pdftoppm", "pdfinfo", "tesseract"):
        if not shutil.which(tool):
            raise SystemExit(f"required tool missing: {tool}")

    source = args.source.resolve()
    out = args.out.resolve()
    catalog = load_json(args.catalog)
    issue = next((x for x in catalog["issues"] if str(x["id"]) == str(args.issue_id)), None)
    if issue is None:
        raise SystemExit(f"issue id {args.issue_id!r} not found")

    source_sha = sha256_file(source)
    manifest_path = out / "manifest.json"
    page_records_path = out / "page-records.jsonl"
    if not args.force and manifest_path.exists() and page_records_path.exists():
        previous = load_json(manifest_path)
        if previous.get("parser_version") == PARSER_VERSION and previous.get("source_sha256") == source_sha and previous.get("dpi") == args.dpi:
            print(json.dumps({"reused": True, "issue_id": args.issue_id, "out": str(out)}))
            return 0

    out.mkdir(parents=True, exist_ok=True)
    pages_dir = out / "pages"
    pages_dir.mkdir(exist_ok=True)
    physical_count = page_count(source)
    max_printed_page = physical_count + 8
    generated = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    records: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="flc-page-parser-") as tmp_name:
        tmp = Path(tmp_name)
        prefix = tmp / "page"
        render = run([
            "pdftoppm", "-jpeg", "-jpegopt", "quality=82", "-r", str(args.dpi),
            str(source), str(prefix)
        ], timeout=max(900, physical_count * 20))
        if render.returncode != 0:
            raise RuntimeError(f"pdftoppm failed: {render.stderr[-2000:]}")
        images = sorted(tmp.glob("page-*.jpg"))
        if len(images) != physical_count:
            raise RuntimeError(f"render count mismatch: expected {physical_count}, got {len(images)}")

        for pdf_page, image in enumerate(images, 1):
            body = run(["tesseract", str(image), "stdout", "--psm", "3", "-l", "eng"], timeout=180)
            meta = run(["tesseract", str(image), "stdout", "--psm", "4", "-l", "eng", "tsv"], timeout=180)
            if body.returncode != 0 or meta.returncode != 0:
                records.append({
                    "pdf_page": pdf_page,
                    "printed_page": None,
                    "printed_page_basis": "ocr-failed",
                    "clean_text": body.stdout.strip() if body.stdout else "",
                    "flags": ["ocr-failed"],
                    "stderr": (body.stderr + "\n" + meta.stderr)[-1200:],
                })
                continue

            width, height, words = parse_tsv(meta.stdout)
            candidates = page_number_candidates(words, width, height, max_printed_page)
            printed_page, basis = choose_page_number(candidates)
            clean_text = clean_body_text(body.stdout, issue)
            record = {
                "pdf_page": pdf_page,
                "printed_page": printed_page,
                "printed_page_basis": basis,
                "page_number_candidates": candidates,
                "ocr_method": "tesseract-psm3-body + psm4-margin-metadata",
                "reading_order_basis": "tesseract automatic page-layout / two-column reading order",
                "body_text_sha256": sha256_text(body.stdout),
                "clean_text_sha256": sha256_text(clean_text),
                "clean_text": clean_text,
                "story_hits": story_hits(body.stdout, issue),
                "review_state": "auto-only",
                "flags": [],
            }
            if pdf_page == issue.get("contents_pdf_page"):
                record["page_role"] = "contents-source-reviewed"
            records.append(record)
            safe_write(pages_dir / f"pdf-{pdf_page:03d}.txt", clean_text + "\n")

    detected_before = sum(1 for r in records if r.get("printed_page") is not None)
    interpolate_local_sequences(records)
    conflicts = flag_duplicate_numbers(records)
    resolved_after = sum(1 for r in records if r.get("printed_page") is not None)

    safe_write(page_records_path, "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n")
    safe_write(out / "page-number-conflicts.json", json.dumps(conflicts, indent=2, ensure_ascii=False) + "\n")

    manifest = {
        "schema_version": 2,
        "parser_version": PARSER_VERSION,
        "geometry_model": "one PDF page = one photographed printed magazine page; page may contain multiple text columns",
        "source": str(source),
        "source_sha256": source_sha,
        "source_preserved": True,
        "issue_id": issue["id"],
        "dpi": args.dpi,
        "physical_pdf_pages": physical_count,
        "page_records": len(records),
        "printed_pages_detected_directly": detected_before,
        "printed_pages_resolved_after_local_interpolation": resolved_after,
        "duplicate_page_number_conflicts": len(conflicts),
        "generated_utc": generated,
        "review_state": "auto-only",
    }
    safe_write(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    report = [
        f"# FLC page parse — {issue['display_title']}",
        "",
        f"- Parser: `{PARSER_VERSION}`",
        f"- Source: `{issue['source_file']}`",
        f"- PDF/image pages: {physical_count}",
        f"- Printed page numbers detected directly: {detected_before}",
        f"- Printed page numbers resolved after conservative local interpolation: {resolved_after}",
        f"- Duplicate number conflicts: {len(conflicts)}",
        "",
        "## Geometry correction",
        "",
        "Each PDF page is treated as one photographed magazine page, commonly carrying two prose columns. The parser does not split those columns into separate logical pages. Tesseract's page-layout pass supplies body reading order; a separate margin-oriented pass recovers printed page numbers so the scrambled PDF sequence can be reordered.",
        "",
        "## Review boundary",
        "",
        "Printed page detection, column reading order, paragraphing and OCR wording remain provisional. Story start pages are applied in a separate source-guided step from the magazine contents pages.",
        "",
    ]
    safe_write(out / "PARSE_REPORT.md", "\n".join(report))
    print(json.dumps(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
