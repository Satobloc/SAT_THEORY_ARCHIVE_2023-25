#!/usr/bin/env python3
"""Add focused printed-folio OCR candidates to FLC parsed page records.

Whole-page OCR often misses the small '-12-' style folios or confuses body
numbers with them. This pass renders each photographed page once, OCRs narrow
left/right margin crops, and records conservative page-number candidates for
the page-order solver. It does not itself assign printed pages.

Source scans are untouched. Existing candidates are preserved separately.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

VERSION = "2026-09-23.1"


def run(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, errors="replace", timeout=timeout, check=False)


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def parse_tsv(tsv: str) -> list[dict[str, Any]]:
    words = []
    for i, line in enumerate(tsv.splitlines()):
        if i == 0 or not line.strip():
            continue
        p = line.split("\t", 11)
        if len(p) != 12:
            continue
        try:
            if int(p[0]) != 5:
                continue
            conf = float(p[10])
            text = p[11].strip()
            if conf < 0 or not text:
                continue
            words.append({
                "text": text, "conf": conf,
                "block": int(p[2]), "par": int(p[3]), "line": int(p[4]),
                "left": int(p[6]), "top": int(p[7]),
                "width": int(p[8]), "height": int(p[9]),
            })
        except (ValueError, TypeError):
            continue
    return words


def number_from(raw: str, max_page: int) -> tuple[int | None, str]:
    s = raw.replace("–", "-").replace("—", "-").replace("~", "-")
    s = s.translate(str.maketrans({"I":"1", "l":"1", "|":"1", "!":"1", "O":"0", "o":"0"}))
    m = re.fullmatch(r"[^0-9]{0,3}(\d{1,3})[^0-9]{0,3}", s.strip())
    if not m:
        return None, s
    n = int(m.group(1))
    return (n if 1 <= n <= max_page else None), s


def candidates(words: list[dict[str, Any]], side: str, max_page: int, crop_h: int) -> list[dict[str, Any]]:
    raw_candidates = []
    for w in words:
        n, normalized = number_from(w["text"], max_page)
        if n is None:
            continue
        has_digit = bool(re.search(r"\d", w["text"]))
        framed = "-" in normalized
        if not has_digit and not framed:
            continue
        score = 3.0
        if framed:
            score += 5.0
        if normalized.strip().startswith("-") and normalized.strip().endswith("-"):
            score += 4.0
        if w["conf"] >= 50:
            score += 1.0
        if w["conf"] >= 80:
            score += 1.0
        cy = w["top"] + w["height"] / 2
        if crop_h * 0.05 <= cy <= crop_h * 0.95:
            score += 0.5
        raw_candidates.append({
            "number": n, "raw_token": w["text"], "normalized_token": normalized,
            "score": round(score, 2), "confidence": round(w["conf"], 2),
            "margin_side": side, "source": "focused-margin-ocr",
        })

    # Combine OCR tokens on one physical line, especially '-', '12', '-'.
    groups: dict[tuple[int,int,int], list[dict[str, Any]]] = {}
    for w in words:
        groups.setdefault((w["block"], w["par"], w["line"]), []).append(w)
    for group in groups.values():
        group.sort(key=lambda w: w["left"])
        raw = "".join(w["text"] for w in group)
        if len(raw) > 16:
            continue
        n, normalized = number_from(raw, max_page)
        if n is None:
            continue
        framed = "-" in normalized
        if not framed and not re.fullmatch(r"\d{1,3}", normalized.strip()):
            continue
        conf = sum(w["conf"] for w in group) / len(group)
        score = 4.0 + (5.0 if framed else 0.0)
        if normalized.strip().startswith("-") and normalized.strip().endswith("-"):
            score += 4.0
        if conf >= 50:
            score += 1.0
        if conf >= 80:
            score += 1.0
        raw_candidates.append({
            "number": n, "raw_token": raw, "normalized_token": normalized,
            "score": round(score, 2), "confidence": round(conf, 2),
            "margin_side": side, "source": "focused-margin-ocr-line",
        })

    best: dict[int, dict[str, Any]] = {}
    for c in raw_candidates:
        n = int(c["number"])
        if n not in best or (c["score"], c["confidence"]) > (best[n]["score"], best[n]["confidence"]):
            best[n] = c
    return sorted(best.values(), key=lambda c: (-c["score"], -c["confidence"], c["number"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--parsed-dir", type=Path, required=True)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--margin-fraction", type=float, default=0.22)
    args = ap.parse_args()

    for tool in ("pdftoppm", "tesseract"):
        if not shutil.which(tool):
            raise SystemExit(f"required tool missing: {tool}")

    parsed = args.parsed_dir.resolve()
    records_path = parsed / "page-records.jsonl"
    records = [json.loads(x) for x in records_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_page = {int(r["pdf_page"]): r for r in records}
    max_page = len(records) + 8
    pages_with_candidates = 0

    with tempfile.TemporaryDirectory(prefix="flc-folio-") as td:
        tmp = Path(td)
        prefix = tmp / "page"
        p = run(["pdftoppm", "-jpeg", "-jpegopt", "quality=88", "-r", str(args.dpi), str(args.source.resolve()), str(prefix)], timeout=1800)
        if p.returncode != 0:
            raise RuntimeError(p.stderr[-2000:])
        for pdf_page, image_path in enumerate(sorted(tmp.glob("page-*.jpg")), 1):
            if pdf_page not in by_page:
                continue
            im = Image.open(image_path).convert("RGB")
            w, h = im.size
            mw = max(80, int(w * args.margin_fraction))
            found = []
            for side, box in (
                ("left", (0, 0, mw, h)),
                ("right", (w-mw, 0, w, h)),
            ):
                crop = im.crop(box)
                cp = tmp / f"p{pdf_page:03d}-{side}.png"
                crop.save(cp)
                tsv = run(["tesseract", str(cp), "stdout", "--psm", "11", "-l", "eng", "tsv"], timeout=120)
                if tsv.returncode == 0:
                    found.extend(candidates(parse_tsv(tsv.stdout), side, max_page, h))
            best: dict[int, dict[str, Any]] = {}
            for c in found:
                n = int(c["number"])
                if n not in best or (c["score"], c["confidence"]) > (best[n]["score"], best[n]["confidence"]):
                    best[n] = c
            merged = sorted(best.values(), key=lambda c: (-c["score"], -c["confidence"], c["number"]))
            by_page[pdf_page]["focused_folio_candidates"] = merged
            by_page[pdf_page].setdefault("folio_refinement", {})["version"] = VERSION
            if merged:
                pages_with_candidates += 1

    records = [by_page[int(r["pdf_page"])] for r in records]
    safe_write(records_path, "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n")
    report = {
        "version": VERSION, "pdf_pages": len(records),
        "pages_with_focused_candidates": pages_with_candidates,
        "method": "left/right margin crop -> Tesseract sparse-text TSV -> conservative number candidates",
        "review_state": "auto-only",
    }
    safe_write(parsed / "FOLIO_REFINEMENT_REPORT.json", json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
