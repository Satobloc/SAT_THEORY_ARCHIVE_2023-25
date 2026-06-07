#!/usr/bin/env python3
"""
Folder Indexer Utility

Creates or updates <target>/..findex.txt and appends a simple tree block
to ..[🎛️_NATHAN_DASH]/🗄️_ARCHIVE_INDEX.txt.

Detailed run logs go to .[⚙️_AI_FILES]/LOGS/folder_indexer/.
"""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
DASH = ROOT / "..[🎛️_NATHAN_DASH]"
AI = ROOT / ".[⚙️_AI_FILES]"
DEFAULT_SETTINGS = DASH / "⚒️_FOLDER_INDEXER.txt"
DEFAULT_LOG_DIR = AI / "LOGS" / "folder_indexer"
GENERATED_MARKER = "GENERATED_BY_FOLDER_INDEXER"

DEFAULTS = {
    "TARGET_FOLDER": ".",
    "INDEX_FILENAME": "..findex.txt",
    "MAX_RUNTIME_SECONDS": "120",
    "MAX_DEPTH": "1",
    "MAX_ENTRIES": "5000",
    "INCLUDE_FILES": "YES",
    "INCLUDE_DIRS": "YES",
    "FOLLOW_SYMLINKS": "NO",
    "UPDATE_GENERATED_INDEX": "YES",
    "CREATE_TIMESTAMPED_IF_PROTECTED": "YES",
    "MASTER_INDEX": "..[🎛️_NATHAN_DASH]/🗄️_ARCHIVE_INDEX.txt",
    "APPEND_TO_MASTER_INDEX": "YES",
    "SKIP_DIRS": ".git,.github,..[🎛️_NATHAN_DASH],.[⚙️_AI_FILES],..📚_NATHAN_WORDS_EXTRACTED,📚_NATHAN_WORDS_EXTRACTED,_NATHAN_CORPUS",
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def yes(value: str) -> bool:
    return str(value).strip().upper() in {"YES", "Y", "TRUE", "1", "ON"}

def safe_path(path_text: str) -> Path:
    p = (ROOT / path_text).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"Refusing path outside repository: {path_text}")
    return p

def rel(path: Path) -> str:
    return "." if path == ROOT else str(path.relative_to(ROOT)).replace(os.sep, "/")

def load_settings(path: Path) -> Dict[str, str]:
    settings = dict(DEFAULTS)
    if not path.exists():
        return settings
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        settings[key.strip().upper().replace(" ", "_")] = value.strip()
    return settings

def should_skip_dir(path: Path, skip_names: set[str]) -> bool:
    r = rel(path)
    return path.name in skip_names or r in skip_names

def list_entries(target: Path, settings: Dict[str, str]):
    max_runtime = int(settings["MAX_RUNTIME_SECONDS"])
    max_depth = int(settings["MAX_DEPTH"])
    max_entries = int(settings["MAX_ENTRIES"])
    include_files = yes(settings["INCLUDE_FILES"])
    include_dirs = yes(settings["INCLUDE_DIRS"])
    follow_symlinks = yes(settings["FOLLOW_SYMLINKS"])
    skip_names = {x.strip() for x in settings.get("SKIP_DIRS", "").split(",") if x.strip()}

    start = time.monotonic()
    warnings: list[str] = []
    counts = {"dirs_seen": 0, "files_seen": 0, "entries_written": 0, "dirs_skipped": 0, "time_limited": 0, "entry_limited": 0}
    children: dict[Path, list[Path]] = {}

    queue: list[tuple[Path, int]] = [(target, 0)]
    while queue:
        if time.monotonic() - start >= max_runtime:
            counts["time_limited"] = 1
            warnings.append("STOPPED: MAX_RUNTIME_SECONDS reached")
            break
        if counts["entries_written"] >= max_entries:
            counts["entry_limited"] = 1
            warnings.append("STOPPED: MAX_ENTRIES reached")
            break

        current, depth = queue.pop(0)
        try:
            entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception as exc:
            warnings.append(f"Could not list {rel(current)}: {exc}")
            continue

        shown: list[Path] = []
        for entry in entries:
            if entry.is_symlink() and not follow_symlinks:
                continue
            if entry.is_dir():
                counts["dirs_seen"] += 1
                if should_skip_dir(entry, skip_names):
                    counts["dirs_skipped"] += 1
                    continue
                if include_dirs:
                    shown.append(entry)
                    counts["entries_written"] += 1
                if depth < max_depth:
                    queue.append((entry, depth + 1))
            elif entry.is_file() and include_files:
                counts["files_seen"] += 1
                shown.append(entry)
                counts["entries_written"] += 1
            if counts["entries_written"] >= max_entries:
                counts["entry_limited"] = 1
                warnings.append("STOPPED: MAX_ENTRIES reached while listing")
                break
        children[current] = shown
    return children, warnings, counts

def render_tree(root: Path, children: dict[Path, list[Path]]) -> str:
    lines = [f"{rel(root)}/"]
    def rec(parent: Path, prefix: str):
        entries = children.get(parent, [])
        for i, entry in enumerate(entries):
            last = i == len(entries) - 1
            branch = "└── " if last else "├── "
            name = entry.name + ("/" if entry.is_dir() else "")
            lines.append(prefix + branch + name)
            if entry.is_dir():
                rec(entry, prefix + ("    " if last else "│   "))
    rec(root, "")
    return "\n".join(lines) + "\n"

def write_local_index(target: Path, tree: str, settings: Dict[str, str]) -> tuple[Path, str]:
    index_path = target / settings["INDEX_FILENAME"]
    content = f"# Folder Index\\n\\n{GENERATED_MARKER}: YES\\nGenerated UTC: {utc_now()}\\n\\n```text\\n{tree}```\\n"
    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8", errors="ignore")[:500]
        if GENERATED_MARKER in existing and yes(settings["UPDATE_GENERATED_INDEX"]):
            index_path.write_text(content, encoding="utf-8")
            return index_path, "updated"
        if yes(settings["CREATE_TIMESTAMPED_IF_PROTECTED"]):
            alt = target / f"..findex.generated.{stamp()}.txt"
            alt.write_text(content, encoding="utf-8")
            return alt, "wrote_timestamped"
        raise FileExistsError(f"Protected index exists: {rel(index_path)}")
    index_path.write_text(content, encoding="utf-8")
    return index_path, "created"

def append_master(tree: str, settings: Dict[str, str]) -> Path | None:
    if not yes(settings["APPEND_TO_MASTER_INDEX"]):
        return None
    master = safe_path(settings["MASTER_INDEX"])
    master.parent.mkdir(parents=True, exist_ok=True)
    block = f"\\n[INDEXED.{utc_now()}]\\n\\n```text\\n{tree}```\\n"
    with master.open("a", encoding="utf-8") as f:
        f.write(block)
    return master

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default=str(DEFAULT_SETTINGS))
    args = parser.parse_args()

    settings = load_settings(safe_path(args.settings))
    target = safe_path(settings["TARGET_FOLDER"])
    DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)

    log = ["FOLDER INDEXER RUN", f"UTC: {utc_now()}", f"TARGET: {rel(target)}", ""]
    children, warnings, counts = list_entries(target, settings)
    tree = render_tree(target, children)
    index_path, action = write_local_index(target, tree, settings)
    master = append_master(tree, settings)

    log.append(f"LOCAL_INDEX: {rel(index_path)} ({action})")
    if master:
        log.append(f"MASTER_INDEX_APPENDED: {rel(master)}")
    log.append("")
    log.append("COUNTS:")
    for k in sorted(counts):
        log.append(f"- {k}: {counts[k]}")
    if warnings:
        log.append("")
        log.append("WARNINGS:")
        log.extend(f"- {w}" for w in warnings)

    (DEFAULT_LOG_DIR / f"folder_indexer_{stamp()}.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
