#!/usr/bin/env python3
"""
Forwarding entry point for the Nathan corpus extractor.

The working extractor currently also exists at:
⚙️_AI_AUTOMATION_ADMIN/_TOOLS/extract_nathan_corpus.py

This dotted admin folder is the preferred visible location because it sorts to the top of the repository.
"""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "⚙️_AI_AUTOMATION_ADMIN" / "_TOOLS" / "extract_nathan_corpus.py"

if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
