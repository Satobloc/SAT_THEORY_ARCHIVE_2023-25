#!/usr/bin/env python3
"""Rebuild the provisional FLC page feed from the unchanged public PDFs.

Usage: python '.[⚙️_AI_FILES]/TOOLS/build_flc_page_feed.py'
The only write root is flc/_RECONSTRUCTION_V1. This script deliberately does not
guess printed-page order, story boundaries, contributor roles, or wording.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import fitz
from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "flc"
OUTPUT = SOURCE / "_RECONSTRUCTION_V1"
IMAGES = OUTPUT / "pages"
ISSUES = (
    ("01", "flc1_lo.pdf", "October 2002", "2002-10", "Inaugural issue", 48),
    ("02", "flc2_lo.pdf", "November 2002", "2002-11", "Issue two", 41),
    ("03", "flc3_lo.pdf", "January 2003", "2003-01", "Issue three", 49),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    issues = []
    for identifier, filename, date, date_iso, label, expected_pages in ISSUES:
        path = SOURCE / filename
        source_hash = sha256(path.read_bytes())
        pdf = fitz.open(path)
        if pdf.page_count != expected_pages:
            raise ValueError(f"{filename}: expected {expected_pages} pages, found {pdf.page_count}")
        pages = []
        for index in range(pdf.page_count):
            page = pdf[index]
            # Small, source-faithful contact sheet; the original PDF remains
            # the only full-resolution source and is never modified here.
            pix = page.get_pixmap(matrix=fitz.Matrix(320 / page.rect.width, 320 / page.rect.width), alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            image_bytes = io.BytesIO()
            image.save(image_bytes, format="WEBP", quality=72, method=5)
            data = image_bytes.getvalue()
            name = f"{path.stem}-{index + 1:03d}.webp"
            target = IMAGES / name
            if not target.exists() or target.read_bytes() != data:
                target.write_bytes(data)
            grey = image.convert("L")
            # Measurements help triage pages; they are not semantic page labels.
            ink_coverage = sum(v for v in grey.histogram()[:180]) / (pix.width * pix.height)
            pages.append({
                "id": f"{identifier}-{index + 1:03d}",
                "pdf_page": index + 1,
                "printed_page": None,
                "piece_id": None,
                "page_role": None,
                "review_state": "auto-only",
                "thumbnail": f"pages/{name}",
                "thumbnail_sha256": sha256(data),
                "preview_ink_coverage": round(ink_coverage, 4),
                "preview_contrast": round(ImageStat.Stat(grey).stddev[0], 2),
            })
        pdf.close()
        issues.append({
            "id": identifier,
            "date": date,
            "date_iso": date_iso,
            "label": label,
            "source_path": f"flc/{filename}",
            "source_sha256": source_hash,
            "pages": pages,
            "issue_review_state": "provisional identity; page sequence unreviewed",
        })
    feed = {
        "schema_version": 1,
        "edition": "FLC page reconstruction / first draft",
        "status": "page identity and previews; story and printed-page order pending review",
        "provenance": "Public flc source PDFs; deterministic page rendering with PyMuPDF and Pillow; page labels are PDF order.",
        "issues": issues,
    }
    target = OUTPUT / "site-feed.json"
    payload = json.dumps(feed, indent=2, ensure_ascii=False) + "\n"
    if not target.exists() or target.read_text(encoding="utf-8") != payload:
        target.write_text(payload, encoding="utf-8")
    print(f"{sum(len(issue['pages']) for issue in issues)} pages, {len(issues)} issues, {target}")


if __name__ == "__main__":
    main()
