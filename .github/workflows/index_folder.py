#!/usr/bin/env python3
"""
Folder Indexer Utility

Creates a lightweight index file inside a specified folder and writes a run log
under .[⚙️_AI_FILES]/LOGS/folder_indexer/.

Reads settings from:
  .[🎛️_DASHBOARD]/⚒️_FOLDER_INDEXER.txt

Safe overwrite rule:
- Updates 000_FOLDER_INDEX.txt only if it contains GENERATED_BY_FOLDER_INDEXER.
- If an existing index is protected/manual, writes a timestamped generated index.
"""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
DEFAULT_SETTINGS = ROOT / ".[🎛️_DASHBOARD]" / "⚒️_FOLDER_INDEXER.txt"
DEFAULT_LOG_DIR = ROOT / ".[⚙️_AI_FILES]" / "LOGS" / "folder_indexer"
GENERATED_MARKER = "GENERATED_BY_FOLDER_INDEXER"

DEFAULTS = {
    "TARGET_FOLDER": ".",
    "INDEX_FILENAME": "000_FOLDER_INDEX.txt",
    "MAX_RUNTIME_SECONDS": "120",
    "MAX_DEPTH": "1",
    "MAX_ENTRIES": "5000",
    "INCLUDE_FILES": "YES",
    "INCLUDE_DIRS": "YES",
    "FOLLOW_SYMLINKS": "NO",
    "UPDATE_GENERATED_INDEX": "YES",
    "CREATE_TIMESTAMPED_IF_PROTECTED": "YES",
    "SKIP_DIRS": ".git,.github,.[🎛️_DASHBOARD],.[⚙️_AI_FILES],..📚_NATHAN_WORDS_EXTRACTED,📚_NATHAN_WORDS_EXTRACTED,_NATHAN_CORPUS",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def safe_path(path_text: str) -> Path:
    p = (ROOT / path_text).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"Refusing path outside repository: {path_text}")
    return p


def yes(value: str) -> bool:
    return str(value).strip().upper() in {"YES", "Y", "TRUE", "1", "ON"}


def load_settings(path: Path) -> Dict[str, str]:
    settings = dict(DEFAULTS)
    if not path.exists():
        return settings

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().upper().replace(" ", "_")
        settings[key] = value.strip()

    return settings


def file_info(path: Path) -> Tuple[int, str]:
    try:
        st = path.stat()
        size = st.st_size
        mtime = datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat()
        return size, mtime
    except Exception:
        return -1, "unknown"


def should_skip_dir(path: Path, skip_names: set[str]) -> bool:
    try:
        rel = str(path.relative_to(ROOT)).replace(os.sep, "/")
    except Exception:
        rel = path.name
    return path.name in skip_names or rel in skip_names


def build_index(settings: Dict[str, str]) -> Tuple[str, List[str], Dict[str, int]]:
    target = safe_path(settings["TARGET_FOLDER"])
    max_runtime = int(settings["MAX_RUNTIME_SECONDS"])
    max_depth = int(settings["MAX_DEPTH"])
    max_entries = int(settings["MAX_ENTRIES"])
    include_files = yes(settings["INCLUDE_FILES"])
    include_dirs = yes(settings["INCLUDE_DIRS"])
    follow_symlinks = yes(settings["FOLLOW_SYMLINKS"])
    skip_names = {x.strip() for x in settings.get("SKIP_DIRS", "").split(",") if x.strip()}

    start = time.monotonic()
    rows: List[str] = []
    warnings: List[str] = []
    counts = {
        "dirs_seen": 0,
        "files_seen": 0,
        "entries_written": 0,
        "dirs_skipped": 0,
        "files_skipped": 0,
        "time_limited": 0,
        "entry_limited": 0,
    }

    if not target.exists() or not target.is_dir():
        raise ValueError(f"TARGET_FOLDER is not a directory: {settings['TARGET_FOLDER']}")

    target_rel = "." if target == ROOT else str(target.relative_to(ROOT)).replace(os.sep, "/")

    rows.append("# Folder Index")
    rows.append("")
    rows.append(f"{GENERATED_MARKER}: YES")
    rows.append(f"Generated UTC: {utc_now()}")
    rows.append(f"Target folder: {target_rel}")
    rows.append(f"Max depth: {max_depth}")
    rows.append(f"Max entries: {max_entries}")
    rows.append("")
    rows.append("## Contents")
    rows.append("")

    queue: List[Tuple[Path, int]] = [(target, 0)]

    while queue:
        if time.monotonic() - start >= max_runtime:
            counts["time_limited"] = 1
            warnings.append("Stopped by MAX_RUNTIME_SECONDS")
            break

        if counts["entries_written"] >= max_entries:
            counts["entry_limited"] = 1
            warnings.append("Stopped by MAX_ENTRIES")
            break

        current, depth = queue.pop(0)
        current_rel = "." if current == ROOT else str(current.relative_to(ROOT)).replace(os.sep, "/")

        try:
            entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception as exc:
            warnings.append(f"Could not list {current_rel}: {exc}")
            continue

        if depth > 0:
            rows.append("")
            rows.append(f"### {current_rel}/")
            rows.append("")

        for entry in entries:
            if time.monotonic() - start >= max_runtime:
                counts["time_limited"] = 1
                warnings.append("Stopped by MAX_RUNTIME_SECONDS while listing entries")
                break

            if counts["entries_written"] >= max_entries:
                counts["entry_limited"] = 1
                warnings.append("Stopped by MAX_ENTRIES while listing entries")
                break

            if entry.is_symlink() and not follow_symlinks:
                continue

            indent = "  " * depth

            if entry.is_dir():
                counts["dirs_seen"] += 1

                if should_skip_dir(entry, skip_names):
                    counts["dirs_skipped"] += 1
                    continue

                if include_dirs:
                    rows.append(f"{indent}- [DIR] {entry.name}/")
                    counts["entries_written"] += 1

                if depth < max_depth:
                    queue.append((entry, depth + 1))

            elif entry.is_file():
                counts["files_seen"] += 1

                if not include_files:
                    counts["files_skipped"] += 1
                    continue

                size, mtime = file_info(entry)
                rows.append(f"{indent}- [FILE] {entry.name} | {size} bytes | modified UTC {mtime}")
                counts["entries_written"] += 1

    rows.append("")
    rows.append("## Run Summary")
    rows.append("")

    for key in sorted(counts):
        rows.append(f"- {key}: {counts[key]}")

    if warnings:
        rows.append("")
        rows.append("## Warnings")
        rows.append("")
        for warning in warnings:
            rows.append(f"- {warning}")

    return "\n".join(rows) + "\n", warnings, counts


def write_index(settings: Dict[str, str], content: str) -> Tuple[Path, str]:
    target = safe_path(settings["TARGET_FOLDER"])
    index_path = target / settings["INDEX_FILENAME"]

    update_generated = yes(settings["UPDATE_GENERATED_INDEX"])
    timestamp_if_protected = yes(settings["CREATE_TIMESTAMPED_IF_PROTECTED"])

    if index_path.exists():
        try:
            existing = index_path.read_text(encoding="utf-8", errors="ignore")[:500]
        except Exception:
            existing = ""

        if GENERATED_MARKER in existing and update_generated:
            index_path.write_text(content, encoding="utf-8")
            return index_path, "updated_generated_index"

        if timestamp_if_protected:
            alt = target / f"000_FOLDER_INDEX_GENERATED_{stamp()}.txt"
            alt.write_text(content, encoding="utf-8")
            return alt, "wrote_timestamped_index_because_existing_file_was_protected"

        raise FileExistsError(f"Index file exists and is not generated/protected: {index_path}")

    index_path.write_text(content, encoding="utf-8")
    return index_path, "created_index"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default=str(DEFAULT_SETTINGS), help="Plain text settings file")
    parser.add_argument("--dry-run", action="store_true", help="Do not write index file")
    args = parser.parse_args()

    settings_path = safe_path(args.settings)
    settings = load_settings(settings_path)
    DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_lines = [
        "FOLDER INDEXER RUN LOG",
        f"UTC: {utc_now()}",
        f"Settings file: {args.settings}",
        f"Dry run: {args.dry_run}",
        "",
    ]

    try:
        content, warnings, counts = build_index(settings)

        if args.dry_run:
            log_lines.append("Index not written: dry run")
            print(content)
        else:
            index_path, action = write_index(settings, content)
            log_lines.append(f"Index action: {action}")
            log_lines.append(f"Index path: {str(index_path.relative_to(ROOT)).replace(os.sep, '/')}")

        log_lines.append("")
        log_lines.append("Counts:")

        for key in sorted(counts):
            log_lines.append(f"- {key}: {counts[key]}")

        if warnings:
            log_lines.append("")
            log_lines.append("Warnings:")
            for warning in warnings:
                log_lines.append(f"- {warning}")

    except Exception as exc:
        log_lines.append(f"ERROR: {exc}")
        log_path = DEFAULT_LOG_DIR / f"folder_indexer_ERROR_{stamp()}.txt"
        log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        raise

    log_path = DEFAULT_LOG_DIR / f"folder_indexer_{stamp()}.txt"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
