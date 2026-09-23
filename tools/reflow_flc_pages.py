#!/usr/bin/env python3
"""Reflow FLC OCR into column-ordered, paragraph-aware page text.

This is a second-stage text parser. It deliberately leaves source PDFs and
printed-page assignments alone. It re-renders each photographed magazine page,
uses Tesseract word coordinates, reconstructs reading columns geometrically,
and replaces only the derived `clean_text` field in page-records.jsonl.

Why this exists:
- a photographed FLC page is usually one printed magazine page with two prose
  columns;
- whole-page OCR can interleave those columns;
- PDF order is a separate problem handled by parse_flc_pages.py;
- story ranges are a separate source-guided problem handled by
  apply_flc_story_ranges.py.

The output remains provisional OCR. The point here is to make the dump read in
human reading order before editorial correction, not to pretend the wording is
reviewed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path
from typing import Any

REFLOW_VERSION = "2026-09-23.1"


def run(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, errors="replace", timeout=timeout, check=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


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
            words.append({
                "text": text,
                "conf": conf,
                "left": int(row.get("left") or 0),
                "top": int(row.get("top") or 0),
                "width": int(row.get("width") or 0),
                "height": int(row.get("height") or 0),
                "block": int(row.get("block_num") or 0),
                "par": int(row.get("par_num") or 0),
                "line": int(row.get("line_num") or 0),
            })
        except (TypeError, ValueError):
            continue
    return width, height, words


def numberish(text: str) -> bool:
    return bool(re.fullmatch(r"\s*[-–—~]*\s*[0-9Il|!Oo]{1,3}\s*[-–—~]*\s*", text))


def line_groups(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for w in words:
        groups.setdefault((w["block"], w["par"], w["line"]), []).append(w)
    out = []
    for key, ws in groups.items():
        ws = sorted(ws, key=lambda w: w["left"])
        out.append({
            "key": key,
            "words": ws,
            "left": min(w["left"] for w in ws),
            "right": max(w["left"] + w["width"] for w in ws),
            "top": min(w["top"] for w in ws),
            "bottom": max(w["top"] + w["height"] for w in ws),
            "text": " ".join(w["text"] for w in ws),
            "mean_conf": statistics.mean(w["conf"] for w in ws),
        })
    return out


def split_visual_line(line: dict[str, Any], page_width: int) -> list[dict[str, Any]]:
    """Split a Tesseract line when a large centre gutter reveals two columns."""
    ws = line["words"]
    if len(ws) < 2:
        return [line]
    gaps = []
    for a, b in zip(ws, ws[1:]):
        gaps.append((b["left"] - (a["left"] + a["width"]), a, b))
    gap, _a, b = max(gaps, key=lambda x: x[0])
    cut = b["left"]
    centreish = page_width * 0.35 <= cut <= page_width * 0.65
    if gap < page_width * 0.055 or not centreish:
        return [line]
    parts = [
        [w for w in ws if w["left"] < cut],
        [w for w in ws if w["left"] >= cut],
    ]
    out = []
    for part in parts:
        if not part:
            continue
        out.append({
            "key": line["key"],
            "words": part,
            "left": min(w["left"] for w in part),
            "right": max(w["left"] + w["width"] for w in part),
            "top": min(w["top"] for w in part),
            "bottom": max(w["top"] + w["height"] for w in part),
            "text": " ".join(w["text"] for w in part),
            "mean_conf": statistics.mean(w["conf"] for w in part),
            "split_at_gutter": True,
        })
    return out or [line]


def clean_lines(lines: list[dict[str, Any]], page_width: int) -> list[dict[str, Any]]:
    kept = []
    for ln in lines:
        cx = (ln["left"] + ln["right"]) / 2
        # Outer-margin isolated page numbers are metadata, not prose.
        if numberish(ln["text"]) and (cx < page_width * 0.16 or cx > page_width * 0.84):
            continue
        if not ln["text"].strip():
            continue
        kept.append(ln)
    return kept


def join_column(lines: list[dict[str, Any]], col_left: float, page_width: int) -> str:
    if not lines:
        return ""
    lines = sorted(lines, key=lambda x: (x["top"], x["left"]))
    heights = [max(1, ln["bottom"] - ln["top"]) for ln in lines]
    med_h = statistics.median(heights) if heights else 20
    paras: list[str] = []
    current = ""
    prev = None
    for ln in lines:
        text = re.sub(r"\s+", " ", ln["text"]).strip()
        if not text:
            continue
        new_para = False
        if prev is not None:
            vertical_gap = ln["top"] - prev["bottom"]
            indent = ln["left"] - col_left
            # FLC body paragraphs generally either indent the first line or
            # leave an appreciably larger vertical gap. Keep thresholds
            # conservative so we do not manufacture paragraphs from noise.
            if vertical_gap > med_h * 0.95 or indent > page_width * 0.018:
                new_para = True
        if new_para and current:
            paras.append(current.strip())
            current = ""
        if current:
            # Repair only obvious line-wrap hyphenation. Preserve hyphens when
            # the next line begins with a capital or non-letter.
            if re.search(r"[A-Za-z]-$", current) and re.match(r"^[a-z]", text):
                current = current[:-1] + text
            else:
                current += " " + text
        else:
            current = text
        prev = ln
    if current:
        paras.append(current.strip())
    return "\n\n".join(p for p in paras if p)


def geometric_reflow(words: list[dict[str, Any]], width: int, height: int) -> tuple[str, dict[str, Any]]:
    base = []
    for ln in line_groups(words):
        base.extend(split_visual_line(ln, width))
    lines = clean_lines(base, width)
    if not lines:
        return "", {"layout": "empty"}

    left = [ln for ln in lines if (ln["left"] + ln["right"]) / 2 < width * 0.49]
    right = [ln for ln in lines if (ln["left"] + ln["right"]) / 2 >= width * 0.51]
    centre = [ln for ln in lines if ln not in left and ln not in right]

    left_words = sum(len(ln["words"]) for ln in left)
    right_words = sum(len(ln["words"]) for ln in right)
    left_span = (min((ln["top"] for ln in left), default=height), max((ln["bottom"] for ln in left), default=0))
    right_span = (min((ln["top"] for ln in right), default=height), max((ln["bottom"] for ln in right), default=0))
    overlap = max(0, min(left_span[1], right_span[1]) - max(left_span[0], right_span[0]))
    two_col = left_words >= 35 and right_words >= 35 and overlap >= height * 0.22

    if not two_col:
        # Single-column/frontmatter/ad page: geometric top-to-bottom order.
        ordered = sorted(lines, key=lambda x: (x["top"], x["left"]))
        text = join_column(ordered, min(ln["left"] for ln in ordered), width)
        return text, {
            "layout": "single-or-mixed",
            "left_words": left_words,
            "right_words": right_words,
            "centre_lines": len(centre),
        }

    # Full-width/centre material above both columns is usually a title/deck.
    body_top = min(min(ln["top"] for ln in left), min(ln["top"] for ln in right))
    top_centre = [ln for ln in centre if ln["top"] <= body_top + height * 0.12]
    body_centre = [ln for ln in centre if ln not in top_centre]

    chunks = []
    if top_centre:
        chunks.append(join_column(top_centre, min(ln["left"] for ln in top_centre), width))
    chunks.append(join_column(left, min(ln["left"] for ln in left), width))
    chunks.append(join_column(right, min(ln["left"] for ln in right), width))
    # Centre material inside the body is kept last rather than silently thrown
    # away; downstream cleaning can identify pull quotes / furniture. This is
    # safer than injecting it into an arbitrary prose position.
    if body_centre:
        chunks.append(join_column(body_centre, min(ln["left"] for ln in body_centre), width))
    return "\n\n".join(c for c in chunks if c.strip()), {
        "layout": "two-column-geometric",
        "left_words": left_words,
        "right_words": right_words,
        "centre_lines": len(centre),
        "body_centre_lines": len(body_centre),
        "column_order": "left-then-right",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--parsed-dir", type=Path, required=True)
    ap.add_argument("--dpi", type=int, default=180)
    args = ap.parse_args()

    for tool in ("pdftoppm", "tesseract"):
        if not shutil.which(tool):
            raise SystemExit(f"required tool missing: {tool}")

    source = args.source.resolve()
    parsed = args.parsed_dir.resolve()
    records_path = parsed / "page-records.jsonl"
    manifest_path = parsed / "manifest.json"
    if not records_path.exists():
        raise SystemExit(f"missing {records_path}")

    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_page = {int(r["pdf_page"]): r for r in records}
    changed = 0
    layouts: dict[str, int] = {}

    with tempfile.TemporaryDirectory(prefix="flc-reflow-") as tmp_name:
        tmp = Path(tmp_name)
        prefix = tmp / "page"
        render = run(["pdftoppm", "-jpeg", "-jpegopt", "quality=88", "-r", str(args.dpi), str(source), str(prefix)], timeout=1800)
        if render.returncode != 0:
            raise RuntimeError(render.stderr[-2000:])
        images = sorted(tmp.glob("page-*.jpg"))
        for pdf_page, image in enumerate(images, 1):
            if pdf_page not in by_page:
                continue
            tsv = run(["tesseract", str(image), "stdout", "--psm", "3", "-l", "eng", "tsv"], timeout=240)
            if tsv.returncode != 0:
                by_page[pdf_page].setdefault("flags", []).append("geometric-reflow-ocr-failed")
                continue
            width, height, words = parse_tsv(tsv.stdout)
            text, meta = geometric_reflow(words, width, height)
            if not text.strip():
                continue
            rec = by_page[pdf_page]
            rec["legacy_clean_text_sha256"] = rec.get("clean_text_sha256")
            rec["clean_text"] = text.strip()
            rec["clean_text_sha256"] = sha256_text(rec["clean_text"])
            rec["text_reflow"] = {
                "version": REFLOW_VERSION,
                "method": "word-coordinate geometric reflow",
                "dpi": args.dpi,
                **meta,
            }
            rec["reading_order_basis"] = (
                "word-coordinate geometric reflow / left-then-right columns"
                if meta.get("layout") == "two-column-geometric"
                else "word-coordinate geometric top-to-bottom reflow"
            )
            layouts[meta.get("layout", "unknown")] = layouts.get(meta.get("layout", "unknown"), 0) + 1
            changed += 1

    records = [by_page[int(r["pdf_page"])] for r in records]
    safe_write(records_path, "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n")

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["text_reflow"] = {
            "version": REFLOW_VERSION,
            "method": "word-coordinate geometric reflow",
            "dpi": args.dpi,
            "pages_reflowed": changed,
            "layout_counts": layouts,
            "review_state": "auto-only",
        }
        safe_write(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    report = parsed / "TEXT_REFLOW_REPORT.md"
    safe_write(report, "\n".join([
        "# FLC text reflow pass",
        "",
        f"- Version: `{REFLOW_VERSION}`",
        f"- Pages reflowed: {changed}",
        f"- Layout counts: `{json.dumps(layouts, sort_keys=True)}`",
        "- Method: Tesseract word coordinates -> gutter split -> left column -> right column -> conservative paragraph reconstruction.",
        "- Source PDF and printed-page assignments are unchanged.",
        "- OCR wording remains provisional; this pass addresses reading order and line/paragraph structure, not source verification.",
        "",
    ]))
    print(json.dumps({"pages_reflowed": changed, "layout_counts": layouts, "version": REFLOW_VERSION}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
