#!/usr/bin/env python3
"""
Archive Admin Tool

Manifest-driven admin utility for SAT archive control/tooling folders.
Designed for bounded, logged operations. Default behavior avoids overwrite.

Dashboard manifest location:
  ..[🎛️_NATHAN_DASH]/⚒️_ADMIN_TASK.txt

Logs:
  .[⚙️_AI_FILES]/LOGS/archive_admin/
"""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
DASH = ROOT / "..[🎛️_NATHAN_DASH]"
AI = ROOT / ".[⚙️_AI_FILES]"
TASK = DASH / "⚒️_ADMIN_TASK.txt"
LOG_DIR = AI / "LOGS" / "archive_admin"

DELETE_ALLOWLIST_PREFIXES = {
    ".AI_READING_PLAN",
    ".⚙️_AI_AUTOMATION_ADMIN",
    "_AI_INSTRUCTIONS",
    "_AI_REQUESTS",
    "_TOOLS",
    "⚙️_AI_AUTOMATION_ADMIN",
    ".github/workflows/index_folder.py",
    ".github/workflows/⚒️_FOLDER_INDEXER.txt",
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace(os.sep, "/")

def safe_path(text: str) -> Path:
    p = (ROOT / text).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"Refusing path outside repository: {text}")
    return p

def deletion_allowed(path_text: str) -> bool:
    return any(path_text == p or path_text.startswith(p + "/") for p in DELETE_ALLOWLIST_PREFIXES)

def copy_any(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return f"MISS source: {rel(src)}"
    if dst.exists():
        return f"SKIP destination exists: {rel(dst)}"
    if src.is_dir():
        shutil.copytree(src, dst)
        return f"COPY_TREE {rel(src)} -> {rel(dst)}"
    shutil.copy2(src, dst)
    return f"COPY_FILE {rel(src)} -> {rel(dst)}"

def run_task() -> list[str]:
    log = [f"ARCHIVE ADMIN RUN", f"UTC: {utc_now()}", ""]
    if not TASK.exists():
        log.append(f"No task file found: {rel(TASK)}")
        return log

    lines = TASK.read_text(encoding="utf-8").splitlines()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        cmd = parts[0].upper()

        if cmd == "MKDIR" and len(parts) >= 2:
            target = safe_path(" ".join(parts[1:]))
            target.mkdir(parents=True, exist_ok=True)
            log.append(f"MKDIR {rel(target)}")

        elif cmd == "COPY" and len(parts) >= 3:
            src = safe_path(parts[1])
            dst = safe_path(parts[2])
            log.append(copy_any(src, dst))

        elif cmd == "DELETE" and len(parts) >= 2:
            path_text = " ".join(parts[1:])
            target = safe_path(path_text)
            if not deletion_allowed(path_text):
                log.append(f"REFUSE DELETE outside allowlist: {path_text}")
                continue
            if not target.exists():
                log.append(f"DELETE skip missing: {path_text}")
                continue
            if target.is_dir():
                shutil.rmtree(target)
                log.append(f"DELETE_TREE {path_text}")
            else:
                target.unlink()
                log.append(f"DELETE_FILE {path_text}")

        else:
            log.append(f"UNKNOWN/INVALID: {line}")

    return log

def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = run_task()
    log_path = LOG_DIR / f"archive_admin_{stamp()}.txt"
    log_path.write_text("\\n".join(log) + "\\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
