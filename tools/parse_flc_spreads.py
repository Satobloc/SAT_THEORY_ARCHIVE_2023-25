#!/usr/bin/env python3
"""Parse photographed FLC spreads into logical pages and provisional story text.

The source PDFs are photographs/scans of open magazine spreads. Treating one PDF
page as one text page causes two separate printed pages to be interleaved by OCR.
This parser instead:

1. renders each physical PDF page (spread);
2. runs Tesseract TSV so every OCR word keeps x/y geometry;
3. finds the left/right text populations for the spread;
4. reconstructs two logical printed pages;
5. detects/infer printed page numbers where possible;
6. uses known story titles + printed-page order to build provisional story spans;
7. emits source-linked, reviewable derived text.

No source PDF is modified. All text remains machine-derived/provisional until
reviewed against the facsimile.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

PARSER_VERSION = "2026-09-23.1"


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


def safe_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
            item: dict[str, Any] = {"text": text, "conf": conf}
            for key in ("left", "top", "width", "height", "block_num", "par_num", "line_num", "word_num"):
                item[key] = int(row.get(key) or 0)
            words.append(item)
        except (ValueError, TypeError):
            continue
    if not width or not height:
        if words:
            width = max(w["left"] + w["width"] for w in words)
            height = max(w["top"] + w["height"] for w in words)
    return width, height, words


def block_geometry(words: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    by_block: dict[int, list[dict[str, Any]]] = {}
    for word in words:
        by_block.setdefault(word["block_num"], []).append(word)
    out: dict[int, dict[str, Any]] = {}
    for block, group in by_block.items():
        x0 = min(w["left"] for w in group)
        y0 = min(w["top"] for w in group)
        x1 = max(w["left"] + w["width"] for w in group)
        y1 = max(w["top"] + w["height"] for w in group)
        out[block] = {
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
            "width": x1 - x0,
            "height": y1 - y0,
            "cx": (x0 + x1) / 2,
            "cy": (y0 + y1) / 2,
            "word_count": len(group),
        }
    return out


def weighted_two_cluster_split(words: list[dict[str, Any]], page_width: int) -> tuple[float, set[int], dict[str, Any]]:
    """Find the left/right logical-page populations from OCR block geometry."""
    blocks = block_geometry(words)
    vertical_furniture: set[int] = set()
    points: list[tuple[float, float]] = []

    for block, g in blocks.items():
        bw = max(1, g["width"])
        bh = max(1, g["height"])
        near_outer_edge = g["x0"] < page_width * 0.16 or g["x1"] > page_width * 0.84
        if bh > bw * 2.0 and bw < page_width * 0.13 and near_outer_edge:
            vertical_furniture.add(block)
        if g["word_count"] >= 5 and bw > page_width * 0.07 and bh <= bw * 2.2:
            points.append((g["cx"], float(g["word_count"])))

    if len(points) < 2:
        return page_width / 2, vertical_furniture, {"basis": "midpoint-fallback"}

    c_left = page_width * 0.30
    c_right = page_width * 0.70
    for _ in range(30):
        left: list[tuple[float, float]] = []
        right: list[tuple[float, float]] = []
        for x, weight in points:
            (left if abs(x - c_left) <= abs(x - c_right) else right).append((x, weight))
        if not left or not right:
            return page_width / 2, vertical_furniture, {"basis": "midpoint-fallback"}
        new_left = sum(x * weight for x, weight in left) / sum(weight for _, weight in left)
        new_right = sum(x * weight for x, weight in right) / sum(weight for _, weight in right)
        if abs(new_left - c_left) + abs(new_right - c_right) < 0.5:
            c_left, c_right = new_left, new_right
            break
        c_left, c_right = new_left, new_right

    if c_left > c_right:
        c_left, c_right = c_right, c_left
    split = (c_left + c_right) / 2
    return split, vertical_furniture, {
        "basis": "weighted-ocr-block-clusters",
        "left_cluster_center": round(c_left, 2),
        "right_cluster_center": round(c_right, 2),
    }


def line_fragments(words: list[dict[str, Any]], vertical_furniture: set[int]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for word in words:
        if word["block_num"] in vertical_furniture:
            continue
        key = (word["block_num"], word["par_num"], word["line_num"])
        groups.setdefault(key, []).append(word)

    frags: list[dict[str, Any]] = []
    for key, group in groups.items():
        group.sort(key=lambda w: w["left"])
        x0 = min(w["left"] for w in group)
        y0 = min(w["top"] for w in group)
        x1 = max(w["left"] + w["width"] for w in group)
        y1 = max(w["top"] + w["height"] for w in group)
        frags.append(
            {
                "key": key,
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "yc": (y0 + y1) / 2,
                "text": " ".join(w["text"] for w in group),
                "mean_conf": round(statistics.mean(w["conf"] for w in group), 2),
            }
        )
    return frags


def merge_same_baseline(frags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not frags:
        return []
    heights = [max(1, f["y1"] - f["y0"]) for f in frags]
    tolerance = max(7.0, statistics.median(heights) * 0.72)
    frags = sorted(frags, key=lambda f: (f["yc"], f["x0"]))
    buckets: list[list[dict[str, Any]]] = []
    for frag in frags:
        if not buckets:
            buckets.append([frag])
            continue
        center = statistics.median(f["yc"] for f in buckets[-1])
        if abs(frag["yc"] - center) <= tolerance:
            buckets[-1].append(frag)
        else:
            buckets.append([frag])

    lines: list[dict[str, Any]] = []
    for bucket in buckets:
        bucket.sort(key=lambda f: f["x0"])
        lines.append(
            {
                "x0": min(f["x0"] for f in bucket),
                "y0": min(f["y0"] for f in bucket),
                "x1": max(f["x1"] for f in bucket),
                "y1": max(f["y1"] for f in bucket),
                "yc": statistics.mean(f["yc"] for f in bucket),
                "text": " ".join(f["text"] for f in bucket),
                "mean_conf": round(statistics.mean(f["mean_conf"] for f in bucket), 2),
            }
        )
    return lines


def page_number_candidates(
    side_words: list[dict[str, Any]], side: str, page_width: int, page_height: int
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for word in side_words:
        raw = word["text"].strip()
        token = raw.replace("~", "-").replace("–", "-").replace("—", "-")
        m = re.fullmatch(r"[^0-9]{0,3}(\d{1,3})[^0-9]{0,3}", token)
        if not m or len(token) > 9:
            continue
        n = int(m.group(1))
        if not (1 <= n <= 200):
            continue
        cx = word["left"] + word["width"] / 2
        cy = word["top"] + word["height"] / 2
        outer = cx < page_width * 0.18 if side == "L" else cx > page_width * 0.82
        if not outer:
            continue
        score = 4.0
        if "-" in token:
            score += 3.0
        if page_height * 0.15 < cy < page_height * 0.85:
            score += 1.0
        if word["conf"] >= 40:
            score += 1.0
        candidates.append(
            {
                "number": n,
                "token": raw,
                "score": score,
                "x": round(cx, 1),
                "y": round(cy, 1),
                "confidence": round(word["conf"], 2),
            }
        )
    return sorted(candidates, key=lambda x: (-x["score"], -x["confidence"]))


def clean_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in lines:
        text = line["text"].strip()
        if not text:
            continue
        t = text.replace("~", "-").replace("–", "-").replace("—", "-")
        if re.fullmatch(r"[- ]*\d{1,3}[- ]*", t):
            continue
        if len(text) <= 2 and not re.search(r"[A-Za-z]", text):
            continue
        out.append(line)
    return out


def reflow(lines: list[dict[str, Any]]) -> str:
    lines = clean_lines(lines)
    if not lines:
        return ""
    median_height = statistics.median(max(1, line["y1"] - line["y0"]) for line in lines)
    paragraphs: list[str] = []
    current: list[str] = []
    previous: dict[str, Any] | None = None

    for line in lines:
        text = line["text"].strip()
        paragraph_break = False
        if previous is not None:
            gap = line["y0"] - previous["y1"]
            indent = line["x0"] - previous["x0"]
            if gap > median_height * 1.18:
                paragraph_break = True
            elif indent > median_height * 1.9 and gap > -median_height * 0.2:
                paragraph_break = True
        if paragraph_break and current:
            paragraphs.append(" ".join(current).strip())
            current = []

        if current and current[-1].endswith("-") and text and text[0].islower():
            current[-1] = current[-1][:-1] + text
        else:
            current.append(text)
        previous = line

    if current:
        paragraphs.append(" ".join(current).strip())
    return "\n\n".join(p for p in paragraphs if p)


def alias_score(text: str, aliases: list[str]) -> int:
    page = norm(text)
    best = 0
    for alias in aliases:
        a = norm(alias)
        if not a:
            continue
        if a in page:
            best = max(best, len(a) + 20)
            continue
        tokens = [t for t in a.split() if len(t) >= 4]
        if len(tokens) >= 2 and all(t in page for t in tokens):
            best = max(best, sum(len(t) for t in tokens))
    return best


def infer_pair(left: int | None, right: int | None) -> tuple[int | None, int | None, str]:
    if left and right and right == left + 1:
        return left, right, "both-detected-consecutive"
    if right and right % 2 == 1 and not left:
        return right - 1, right, "right-detected-left-inferred"
    if left and left % 2 == 0 and not right:
        return left, left + 1, "left-detected-right-inferred"
    if left or right:
        return left, right, "detected-without-safe-pair-inference"
    return None, None, "unresolved"


def choose_detected(candidates: list[dict[str, Any]]) -> int | None:
    if not candidates:
        return None
    top = candidates[0]
    if top["score"] < 5:
        return None
    return int(top["number"])


def logical_record(
    pdf_page: int,
    side: str,
    printed_page: int | None,
    detected_page: int | None,
    pair_basis: str,
    split_x: float,
    split_meta: dict[str, Any],
    raw_text: str,
    clean_text: str,
    candidates: list[dict[str, Any]],
    story_hits: list[dict[str, Any]],
    mean_conf: float | None,
) -> dict[str, Any]:
    return {
        "pdf_page": pdf_page,
        "spread_side": side,
        "logical_page_id": f"pdf-{pdf_page:03d}-{side.lower()}",
        "printed_page": printed_page,
        "printed_page_detected": detected_page,
        "printed_page_basis": pair_basis,
        "split_x": round(split_x, 2),
        "split_basis": split_meta,
        "page_number_candidates": candidates,
        "story_hits": story_hits,
        "mean_ocr_confidence": mean_conf,
        "raw_text_sha256": sha256_text(raw_text),
        "clean_text_sha256": sha256_text(clean_text),
        "clean_text": clean_text,
        "review_state": "auto-only",
    }


def build_story_spans(logical_pages: list[dict[str, Any]], issue: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    resolved = [p for p in logical_pages if p["printed_page"] is not None]
    resolved.sort(key=lambda p: (p["printed_page"], p["pdf_page"], p["spread_side"]))

    anchors: list[dict[str, Any]] = []
    for story in issue["stories"]:
        candidates: list[tuple[int, int, dict[str, Any]]] = []
        for page in resolved:
            hits = {hit["story_id"]: hit["score"] for hit in page["story_hits"]}
            if story["id"] in hits and len(page["story_hits"]) < 3:
                candidates.append((page["printed_page"], -hits[story["id"]], page))
        if candidates:
            candidates.sort(key=lambda x: (x[0], x[1]))
            start_page, neg_score, page = candidates[0]
            anchors.append(
                {
                    "story_id": story["id"],
                    "slug": story["slug"],
                    "title": story["title"],
                    "catalog_order": issue["stories"].index(story),
                    "start_printed_page": start_page,
                    "score": -neg_score,
                    "anchor_logical_page_id": page["logical_page_id"],
                }
            )

    # Preserve catalog order. If automatic anchors conflict, do not force a
    # nonsensical span through the conflict; mark the offending anchor ignored.
    accepted: list[dict[str, Any]] = []
    last_page = -1
    for anchor in sorted(anchors, key=lambda a: a["catalog_order"]):
        if anchor["start_printed_page"] > last_page:
            anchor["accepted"] = True
            accepted.append(anchor)
            last_page = anchor["start_printed_page"]
        else:
            anchor["accepted"] = False
            anchor["reason"] = "non-monotonic automatic start candidate"

    spans: dict[str, list[dict[str, Any]]] = {story["id"]: [] for story in issue["stories"]}
    accepted_by_start = sorted(accepted, key=lambda a: a["start_printed_page"])
    for i, anchor in enumerate(accepted_by_start):
        start = anchor["start_printed_page"]
        end = accepted_by_start[i + 1]["start_printed_page"] - 1 if i + 1 < len(accepted_by_start) else math.inf
        for page in resolved:
            if start <= page["printed_page"] <= end:
                spans[anchor["story_id"]].append(page)

    return spans, anchors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--issue-id", required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dpi", type=int, default=100)
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
        raise SystemExit(f"issue id {args.issue_id!r} not found in {args.catalog}")

    source_sha = sha256_file(source)
    manifest_path = out / "manifest.json"
    story_index_path = out / "story-text-index.json"
    if not args.force and manifest_path.exists() and story_index_path.exists():
        previous = load_json(manifest_path)
        if (
            previous.get("parser_version") == PARSER_VERSION
            and previous.get("source_sha256") == source_sha
            and previous.get("dpi") == args.dpi
        ):
            print(json.dumps({"reused": True, "issue_id": args.issue_id, "out": str(out)}))
            return 0

    out.mkdir(parents=True, exist_ok=True)
    logical_dir = out / "logical_pages"
    story_dir = out / "stories"
    logical_dir.mkdir(exist_ok=True)
    story_dir.mkdir(exist_ok=True)

    physical_count = page_count(source)
    generated = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    logical_pages: list[dict[str, Any]] = []
    spread_diagnostics: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="flc-spread-parser-") as tmp_name:
        tmp = Path(tmp_name)
        prefix = tmp / "spread"
        render = run(
            [
                "pdftoppm",
                "-jpeg",
                "-jpegopt",
                "quality=78",
                "-r",
                str(args.dpi),
                str(source),
                str(prefix),
            ],
            timeout=max(900, physical_count * 20),
        )
        if render.returncode != 0:
            raise RuntimeError(f"pdftoppm failed: {render.stderr[-2000:]}")

        images = sorted(tmp.glob("spread-*.jpg"))
        if len(images) != physical_count:
            raise RuntimeError(f"render count mismatch: expected {physical_count}, got {len(images)}")

        for pdf_page, image in enumerate(images, 1):
            ocr = run(["tesseract", str(image), "stdout", "--psm", "3", "-l", "eng", "tsv"], timeout=180)
            if ocr.returncode != 0:
                spread_diagnostics.append(
                    {
                        "pdf_page": pdf_page,
                        "status": "ocr-failed",
                        "stderr": ocr.stderr[-1000:],
                    }
                )
                continue

            width, height, words = parse_tsv(ocr.stdout)
            split_x, vertical_furniture, split_meta = weighted_two_cluster_split(words, width)
            sides: dict[str, dict[str, Any]] = {}
            for side in ("L", "R"):
                side_words = [
                    w
                    for w in words
                    if ((w["left"] + w["width"] / 2 < split_x) if side == "L" else (w["left"] + w["width"] / 2 >= split_x))
                ]
                raw_text = " ".join(w["text"] for w in side_words)
                frags = line_fragments(side_words, vertical_furniture)
                lines = merge_same_baseline(frags)
                clean_text = reflow(lines)
                candidates = page_number_candidates(side_words, side, width, height)
                detected = choose_detected(candidates)

                story_hits: list[dict[str, Any]] = []
                for story in issue["stories"]:
                    score = alias_score(raw_text + "\n" + clean_text, story.get("aliases", [story["title"]]))
                    if score:
                        story_hits.append(
                            {
                                "story_id": story["id"],
                                "slug": story["slug"],
                                "title": story["title"],
                                "score": score,
                            }
                        )
                story_hits.sort(key=lambda h: (-h["score"], h["story_id"]))
                sides[side] = {
                    "words": side_words,
                    "raw_text": raw_text,
                    "clean_text": clean_text,
                    "candidates": candidates,
                    "detected": detected,
                    "story_hits": story_hits,
                    "mean_conf": round(statistics.mean(w["conf"] for w in side_words), 2) if side_words else None,
                }

            left_page, right_page, pair_basis = infer_pair(sides["L"]["detected"], sides["R"]["detected"])
            for side, printed_page in (("L", left_page), ("R", right_page)):
                s = sides[side]
                rec = logical_record(
                    pdf_page,
                    side,
                    printed_page,
                    s["detected"],
                    pair_basis,
                    split_x,
                    split_meta,
                    s["raw_text"],
                    s["clean_text"],
                    s["candidates"],
                    s["story_hits"],
                    s["mean_conf"],
                )
                logical_pages.append(rec)
                safe_write(logical_dir / f"{rec['logical_page_id']}.txt", s["clean_text"] + "\n")

            spread_diagnostics.append(
                {
                    "pdf_page": pdf_page,
                    "status": "parsed",
                    "width": width,
                    "height": height,
                    "split_x": round(split_x, 2),
                    "split_basis": split_meta,
                    "vertical_furniture_blocks": sorted(vertical_furniture),
                    "left_detected": sides["L"]["detected"],
                    "right_detected": sides["R"]["detected"],
                    "left_printed": left_page,
                    "right_printed": right_page,
                    "pair_basis": pair_basis,
                }
            )

    spans, anchors = build_story_spans(logical_pages, issue)
    story_index: dict[str, Any] = {
        "schema_version": 1,
        "parser_version": PARSER_VERSION,
        "project_id": catalog["project_id"],
        "issue_id": issue["id"],
        "issue_title": issue["display_title"],
        "source_file": issue["source_file"],
        "source_sha256": source_sha,
        "generated_utc": generated,
        "method": "spread-aware Tesseract TSV -> logical left/right pages -> printed-page reconstruction -> title-anchor story spans",
        "review_state": "auto-only",
        "stories": [],
    }

    for story in issue["stories"]:
        pages = sorted(spans.get(story["id"], []), key=lambda p: p["printed_page"] if p["printed_page"] is not None else 9999)
        display_text = "\n\n".join(p["clean_text"].strip() for p in pages if p["clean_text"].strip()) or None
        record = {
            "schema_version": 1,
            "parser_version": PARSER_VERSION,
            "story_id": story["id"],
            "slug": story["slug"],
            "title": story["title"],
            "author": story["author"],
            "issue_id": issue["id"],
            "text_state": "spread-split-ocr-provisional" if display_text else "story-span-not-yet-resolved",
            "review_state": "auto-only" if display_text else "unresolved",
            "reading_order_basis": "printed-page-reconstruction" if display_text else None,
            "logical_pages": [
                {
                    "logical_page_id": p["logical_page_id"],
                    "pdf_page": p["pdf_page"],
                    "spread_side": p["spread_side"],
                    "printed_page": p["printed_page"],
                    "printed_page_basis": p["printed_page_basis"],
                    "mean_ocr_confidence": p["mean_ocr_confidence"],
                }
                for p in pages
            ],
            "display_text": display_text,
            "display_text_sha256": sha256_text(display_text) if display_text else None,
            "editorial_note": "Automatically reconstructed from spread geometry and provisional OCR. Verify story boundaries, page order, paragraphing, and wording against the facsimile before treating as reviewed transcription.",
        }
        safe_write(story_dir / f"{story['slug']}.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        if display_text:
            safe_write(story_dir / f"{story['slug']}.txt", display_text + "\n")
        story_index["stories"].append(
            {
                "story_id": story["id"],
                "slug": story["slug"],
                "title": story["title"],
                "author": story["author"],
                "text_state": record["text_state"],
                "reading_order_basis": record["reading_order_basis"],
                "logical_page_count": len(pages),
                "printed_pages": [p["printed_page"] for p in pages],
                "story_json": f"stories/{story['slug']}.json",
            }
        )

    logical_jsonl = "\n".join(json.dumps(p, ensure_ascii=False) for p in logical_pages) + "\n"
    safe_write(out / "logical-pages.jsonl", logical_jsonl)
    safe_write(story_index_path, json.dumps(story_index, indent=2, ensure_ascii=False) + "\n")
    safe_write(out / "spread-diagnostics.json", json.dumps(spread_diagnostics, indent=2, ensure_ascii=False) + "\n")
    safe_write(out / "story-anchors.json", json.dumps(anchors, indent=2, ensure_ascii=False) + "\n")

    resolved_pages = [p for p in logical_pages if p["printed_page"] is not None]
    ready_stories = [s for s in story_index["stories"] if s["text_state"] == "spread-split-ocr-provisional"]
    report = [
        f"# FLC spread parse — {issue['display_title']}",
        "",
        f"- Parser: `{PARSER_VERSION}`",
        f"- Source: `{issue['source_file']}`",
        f"- Physical PDF spreads: {physical_count}",
        f"- Logical page records: {len(logical_pages)}",
        f"- Logical pages with detected/inferred printed number: {len(resolved_pages)}",
        f"- Story text spans currently resolved: {len(ready_stories)} / {len(issue['stories'])}",
        "",
        "## What changed",
        "",
        "The parser no longer asks whole-spread OCR to pretend that two facing printed pages are one text stream. It uses OCR geometry to separate left/right logical pages first, then reconstructs printed-page order and only then assembles story text.",
        "",
        "## Limits",
        "",
        "- OCR wording remains provisional.",
        "- Printed page numbers may be inferred from the facing page when parity is clear.",
        "- Story boundaries are automatic title-anchor candidates, smoothed by printed-page order; they are not reviewed facts.",
        "- Illustrations, ads, pull quotes, and other page furniture are not yet semantically segmented.",
        "",
        "## Story status",
        "",
    ]
    for s in story_index["stories"]:
        report.append(f"- **{s['title']}** — {s['text_state']}; pages {s['printed_pages'] or 'unresolved'}")
    report.append("")
    safe_write(out / "PARSE_REPORT.md", "\n".join(report))

    manifest = {
        "schema_version": 1,
        "parser_version": PARSER_VERSION,
        "source": str(source),
        "source_sha256": source_sha,
        "source_preserved": True,
        "issue_id": issue["id"],
        "dpi": args.dpi,
        "physical_pdf_pages": physical_count,
        "logical_page_records": len(logical_pages),
        "logical_pages_with_printed_number": len(resolved_pages),
        "stories_with_provisional_text": len(ready_stories),
        "generated_utc": generated,
        "review_state": "auto-only",
    }
    safe_write(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
