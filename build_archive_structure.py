#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse

ROOT = Path.cwd()

def parse_manifest(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    actions = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        if line.startswith("DIR "):
            actions.append(("dir", line[4:].strip(), ""))
            i += 1
            continue

        if line.startswith("FILE "):
            file_path = line[5:].strip()
            text = ""
            i += 1
            if i < len(lines) and lines[i].strip() == "TEXT":
                i += 1
                buf = []
                while i < len(lines) and lines[i].strip() != "ENDTEXT":
                    buf.append(lines[i])
                    i += 1
                text = "\n".join(buf) + "\n"
                if i < len(lines) and lines[i].strip() == "ENDTEXT":
                    i += 1
            actions.append(("file", file_path, text))
            continue

        raise ValueError(f"Unrecognized manifest line {i+1}: {line}")

    return actions

def safe_path(relative: str) -> Path:
    p = (ROOT / relative).resolve()
    if ROOT not in p.parents and p != ROOT:
        raise ValueError(f"Refusing path outside repo: {relative}")
    return p

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", help="Path to structure manifest text file")
    ap.add_argument("--apply", action="store_true", help="Actually write files/folders")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = ap.parse_args()

    manifest = safe_path(args.manifest)
    actions = parse_manifest(manifest)

    log_lines = [
        f"STRUCTURE BUILD LOG",
        f"UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Manifest: {args.manifest}",
        f"Mode: {'APPLY' if args.apply else 'DRY RUN'}",
        f"Overwrite: {args.overwrite}",
        ""
    ]

    for kind, rel, text in actions:
        target = safe_path(rel)

        if kind == "dir":
            log_lines.append(f"DIR  {rel}")
            if args.apply:
                target.mkdir(parents=True, exist_ok=True)

        elif kind == "file":
            exists = target.exists()
            if exists and not args.overwrite:
                log_lines.append(f"SKIP existing file {rel}")
                continue
            log_lines.append(f"FILE {rel}")
            if args.apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")

    log_dir = ROOT / ".[🎛️_DASHBOARD]" / "[🗂️_LOGS]"
    log_name = f"structure_build_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"

    if args.apply:
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / log_name).write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    else:
        print("\n".join(log_lines))

if __name__ == "__main__":
    main()
