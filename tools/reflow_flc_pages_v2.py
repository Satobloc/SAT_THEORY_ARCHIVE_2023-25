#!/usr/bin/env python3
"""Reflow FLC OCR with block-aware column crops.

This pass fixes two recurring failure modes in the earlier reflow:
1. Tesseract TSV is parsed by literal tab fields, not csv quoting. A stray
   double quote in OCR text can otherwise swallow the remainder of a TSV file
   into one giant `text` field.
2. Dense prose blocks are re-OCRed independently from cropped image regions,
   so left/right columns and illustration interruptions do not contaminate each
   other as badly as whole-page OCR.

The pass changes derived `clean_text` only. Source scans and printed-page
assignments remain untouched. OCR remains provisional.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

REFLOW_VERSION = "2026-09-23.2"


def run(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, errors="replace", timeout=timeout, check=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def parse_tsv_words(tsv: str) -> tuple[int, int, list[dict[str, Any]]]:
    """Parse Tesseract TSV without CSV quote semantics.

    Tesseract's TSV is literal tab-separated output. OCR text can contain an
    unmatched double quote. csv.DictReader then treats following physical TSV
    rows as one quoted field. Splitting each physical line into at most 12
    fields avoids that corruption.
    """
    width = height = 0
    words: list[dict[str, Any]] = []
    lines = tsv.splitlines()
    for i, line in enumerate(lines):
        if i == 0 or not line.strip():
            continue
        parts = line.split("\t", 11)
        if len(parts) != 12:
            continue
        level, _page, block, par, line_num, _word_num, left, top, w, h, conf, text = parts
        try:
            level_i = int(level)
            if level_i == 1:
                width, height = int(w), int(h)
                continue
            if level_i != 5:
                continue
            conf_f = float(conf)
            if conf_f < 0 or not text.strip():
                continue
            words.append({
                "text": text.strip(), "conf": conf_f,
                "left": int(left), "top": int(top),
                "width": int(w), "height": int(h),
                "block": int(block), "par": int(par), "line": int(line_num),
            })
        except (TypeError, ValueError):
            continue
    return width, height, words


def aggregate_blocks(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: dict[int, dict[str, Any]] = {}
    for word in words:
        b = blocks.setdefault(word["block"], {
            "block": word["block"], "words": [],
            "left": 10**9, "top": 10**9, "right": 0, "bottom": 0,
        })
        b["words"].append(word)
        b["left"] = min(b["left"], word["left"])
        b["top"] = min(b["top"], word["top"])
        b["right"] = max(b["right"], word["left"] + word["width"])
        b["bottom"] = max(b["bottom"], word["top"] + word["height"])
    out = []
    for b in blocks.values():
        b["word_count"] = len(b["words"])
        b["width"] = b["right"] - b["left"]
        b["height"] = b["bottom"] - b["top"]
        b["cx"] = (b["left"] + b["right"]) / 2
        b["cy"] = (b["top"] + b["bottom"]) / 2
        out.append(b)
    return out


def normalize_ocr_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paras = []
    for raw_para in re.split(r"\n\s*\n+", text):
        lines = [re.sub(r"\s+", " ", x).strip() for x in raw_para.splitlines() if x.strip()]
        if not lines:
            continue
        joined = lines[0]
        for line in lines[1:]:
            if re.search(r"[A-Za-z]-$", joined) and re.match(r"^[a-z]", line):
                joined = joined[:-1] + line
            else:
                joined += " " + line
        joined = re.sub(r"\s+", " ", joined).strip()
        if joined:
            paras.append(joined)
    return "\n\n".join(paras)


def ocr_crop(image: Image.Image, box: tuple[int, int, int, int], tmp: Path, name: str) -> str:
    crop = image.crop(box)
    path = tmp / f"{name}.png"
    crop.save(path)
    p = run(["tesseract", str(path), "stdout", "--psm", "4", "-l", "eng"], timeout=180)
    if p.returncode != 0:
        return ""
    return normalize_ocr_text(p.stdout)


def fallback_from_words(words: list[dict[str, Any]]) -> str:
    groups: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for word in words:
        groups.setdefault((word["block"], word["par"], word["line"]), []).append(word)
    lines = []
    for ws in groups.values():
        ws.sort(key=lambda w: w["left"])
        lines.append((min(w["top"] for w in ws), min(w["left"] for w in ws), " ".join(w["text"] for w in ws)))
    lines.sort()
    return normalize_ocr_text("\n".join(x[2] for x in lines))


def reflow_page(image_path: Path, tmp: Path) -> tuple[str, dict[str, Any]]:
    tsv = run(["tesseract", str(image_path), "stdout", "--psm", "3", "-l", "eng", "tsv"], timeout=240)
    if tsv.returncode != 0:
        return "", {"layout": "ocr-failed"}
    width, height, words = parse_tsv_words(tsv.stdout)
    if not words or width <= 0 or height <= 0:
        return "", {"layout": "empty"}

    blocks = aggregate_blocks(words)
    body = [b for b in blocks if b["word_count"] >= 18 and b["width"] >= width * 0.16 and b["height"] >= height * 0.045]
    if not body:
        return fallback_from_words(words), {"layout": "word-fallback", "block_count": len(blocks)}

    left = [b for b in body if b["cx"] < width * 0.49 and b["width"] < width * 0.58]
    right = [b for b in body if b["cx"] > width * 0.51 and b["width"] < width * 0.58]
    full = [b for b in body if b not in left and b not in right]
    left_words = sum(b["word_count"] for b in left)
    right_words = sum(b["word_count"] for b in right)
    two_col = left_words >= 30 and right_words >= 30

    im = Image.open(image_path).convert("RGB")
    margin = max(8, int(width * 0.006))

    def block_text(block: dict[str, Any], idx: int) -> str:
        box = (
            max(0, block["left"] - margin), max(0, block["top"] - margin),
            min(width, block["right"] + margin), min(height, block["bottom"] + margin),
        )
        return ocr_crop(im, box, tmp, f"b{block['block']}_{idx}")

    chunks: list[str] = []
    supplemental: list[str] = []
    ordered_blocks: list[dict[str, Any]] = []
    layout = "single-or-mixed-block-crop"

    if two_col:
        layout = "two-column-block-crop"
        left.sort(key=lambda b: (b["top"], b["left"]))
        right.sort(key=lambda b: (b["top"], b["left"]))
        ordered_blocks = left + right
        # Full-width blocks are preserved separately instead of injected into
        # prose at an arbitrary location. They are often titles, pull quotes,
        # ads, captions, or illustration text.
        for i, b in enumerate(sorted(full, key=lambda x: (x["top"], x["left"]))):
            t = block_text(b, 1000 + i)
            if t:
                supplemental.append(t)
    else:
        ordered_blocks = sorted(body, key=lambda b: (b["top"], b["left"]))

    for i, block in enumerate(ordered_blocks):
        text = block_text(block, i)
        if text:
            chunks.append(text)

    clean = "\n\n".join(c for c in chunks if c.strip())
    if not clean:
        clean = fallback_from_words(words)
        layout = "word-fallback-after-empty-crops"

    meta = {
        "layout": layout,
        "body_blocks": len(body),
        "left_blocks": len(left),
        "right_blocks": len(right),
        "full_or_centre_blocks": len(full),
        "left_words": left_words,
        "right_words": right_words,
        "supplemental_blocks": len(supplemental),
        "supplemental_text": supplemental,
    }
    return clean, meta


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
    layouts: dict[str, int] = {}
    changed = 0

    with tempfile.TemporaryDirectory(prefix="flc-reflow-v2-") as tmp_name:
        tmp = Path(tmp_name)
        prefix = tmp / "page"
        render = run(["pdftoppm", "-jpeg", "-jpegopt", "quality=90", "-r", str(args.dpi), str(source), str(prefix)], timeout=1800)
        if render.returncode != 0:
            raise RuntimeError(render.stderr[-2000:])
        images = sorted(tmp.glob("page-*.jpg"))
        for pdf_page, image_path in enumerate(images, 1):
            if pdf_page not in by_page:
                continue
            text, meta = reflow_page(image_path, tmp)
            if not text.strip():
                by_page[pdf_page].setdefault("flags", []).append("block-reflow-empty")
                continue
            rec = by_page[pdf_page]
            rec["pre_block_reflow_clean_text_sha256"] = rec.get("clean_text_sha256")
            rec["clean_text"] = text.strip()
            rec["clean_text_sha256"] = sha256_text(rec["clean_text"])
            rec["text_reflow"] = {
                "version": REFLOW_VERSION,
                "method": "tesseract block discovery -> independent image-crop OCR -> column block ordering",
                "dpi": args.dpi,
                **meta,
            }
            rec["reading_order_basis"] = (
                "independent OCR of detected left-column blocks then right-column blocks"
                if meta.get("layout") == "two-column-block-crop"
                else "independent OCR of detected text blocks in geometric order"
            )
            layouts[meta.get("layout", "unknown")] = layouts.get(meta.get("layout", "unknown"), 0) + 1
            changed += 1

    records = [by_page[int(r["pdf_page"])] for r in records]
    safe_write(records_path, "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n")

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["text_reflow"] = {
            "version": REFLOW_VERSION,
            "method": "block-crop OCR with literal TSV parsing",
            "dpi": args.dpi,
            "pages_reflowed": changed,
            "layout_counts": layouts,
            "review_state": "auto-only",
        }
        safe_write(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    safe_write(parsed / "TEXT_REFLOW_REPORT.md", "\n".join([
        "# FLC text reflow pass",
        "",
        f"- Version: `{REFLOW_VERSION}`",
        f"- Pages reflowed: {changed}",
        f"- Layout counts: `{json.dumps(layouts, sort_keys=True)}`",
        "- TSV parser: literal physical-line/tab parser; stray OCR quote marks cannot consume following TSV records.",
        "- Main method: discover text blocks on the page, crop them from the scan, OCR each crop independently, then order left-column blocks before right-column blocks.",
        "- Full-width/centre blocks on two-column pages are preserved as supplemental metadata rather than silently injected into prose.",
        "- Source scans and printed-page assignments are unchanged.",
        "- Wording remains provisional until checked against the facsimile.",
        "",
    ]))
    print(json.dumps({"pages_reflowed": changed, "layouts": layouts, "version": REFLOW_VERSION}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
