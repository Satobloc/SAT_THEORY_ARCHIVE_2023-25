#!/usr/bin/env python3
"""Archive master-index maintenance utilities.

Administrative/navigation machinery only.  This tool never modifies SAT source
artifacts.  Its chunk operation is deliberately non-destructive: the Dashboard
master index remains untouched while exact-byte chunks, a manifest, a baseline
root-index block, and logs are generated under .[⚙️_AI_FILES]/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
AI = ROOT / ".[⚙️_AI_FILES]"
DASH = ROOT / "..[🎛️_NATHAN_DASH]"
MASTER = DASH / "🗄️_ARCHIVE_INDEX.txt"
INDEX_HOME = AI / "INDEXES" / "archive_index_history"
CHUNK_LOGS = AI / "LOGS" / "archive_index_chunker"
DELTA_LOGS = AI / "LOGS" / "archive_index_delta"
BASELINE_BLOCK = INDEX_HOME / "BASELINE_ROOT_BLOCK.txt"
BASELINE_INFO = INDEX_HOME / "BASELINE_INFO.json"
CURRENT_ROOT_INDEX = ROOT / "..findex.txt"

SEP_RE = re.compile(r"(?m)^-{20,}\r?\n(?=INDEXED_UTC:\s*)")
LEGACY_RE = re.compile(r"(?m)^\[INDEXED\.[^\n]+\]\s*$")
TREE_RE = re.compile(r"```text\s*\r?\n(.*?)```", re.DOTALL)
HEADER_FIELD_RE = re.compile(r"(?m)^([A-Z][A-Z0-9_]+):\s*(.*?)\s*$")
TREE_LINE_RE = re.compile(r"^((?:(?:│   )|(?:    ))*)(?:├── |└── )(.*)$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def logical_segments(text: str) -> list[str]:
    """Split ledger at known historical-run boundaries without dropping bytes."""
    starts = {m.start() for m in SEP_RE.finditer(text)}
    starts.update(m.start() for m in LEGACY_RE.finditer(text))
    ordered = sorted(starts)
    if not ordered:
        return [text]
    segments: list[str] = []
    if ordered[0] > 0:
        segments.append(text[: ordered[0]])
    for i, start in enumerate(ordered):
        end = ordered[i + 1] if i + 1 < len(ordered) else len(text)
        segments.append(text[start:end])
    return [s for s in segments if s]


def group_segments(segments: list[str], target_bytes: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for segment in segments:
        size = len(segment.encode("utf-8"))
        if current and current_size + size > target_bytes:
            chunks.append("".join(current))
            current = []
            current_size = 0
        current.append(segment)
        current_size += size
        # A single historical block may exceed target_bytes; keep it whole.
        if current_size >= target_bytes:
            chunks.append("".join(current))
            current = []
            current_size = 0
    if current:
        chunks.append("".join(current))
    return chunks


def header_fields(block: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in HEADER_FIELD_RE.finditer(block)}


def block_timestamp(block: str) -> str | None:
    fields = header_fields(block)
    if fields.get("INDEXED_UTC"):
        return fields["INDEXED_UTC"]
    m = re.search(r"(?m)^\[INDEXED\.([^\]]+)\]", block)
    return m.group(1).strip() if m else None


def latest_root_block(segments: list[str]) -> str | None:
    candidates: list[str] = []
    for segment in segments:
        if re.search(r"(?m)^TARGET:\s*\.\s*$", segment):
            candidates.append(segment)
    return candidates[-1] if candidates else None


def extract_tree(text: str) -> str | None:
    m = TREE_RE.search(text)
    return m.group(1) if m else None


def task_chunk(target_bytes: int) -> int:
    if not MASTER.exists():
        raise FileNotFoundError(f"Master index missing: {MASTER}")
    data = MASTER.read_bytes()
    text = data.decode("utf-8", errors="strict")
    original_sha256 = sha256(data)
    blob_sha1 = git_blob_sha1(data)
    segments = logical_segments(text)
    chunks = group_segments(segments, target_bytes)

    snapshot_rel = Path("snapshots") / original_sha256[:16]
    snapshot_dir = INDEX_HOME / snapshot_rel
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    chunk_records: list[dict[str, Any]] = []
    reassembled_parts: list[bytes] = []
    byte_cursor = 0
    for i, chunk in enumerate(chunks, 1):
        chunk_data = chunk.encode("utf-8")
        name = f"chunk_{i:03d}.txt"
        path = snapshot_dir / name
        path.write_bytes(chunk_data)
        record = {
            "chunk": name,
            "bytes": len(chunk_data),
            "sha256": sha256(chunk_data),
            "byte_start": byte_cursor,
            "byte_end_exclusive": byte_cursor + len(chunk_data),
            "first_indexed_utc": None,
            "last_indexed_utc": None,
        }
        timestamps = [x for x in (block_timestamp(s) for s in logical_segments(chunk)) if x]
        if timestamps:
            record["first_indexed_utc"] = timestamps[0]
            record["last_indexed_utc"] = timestamps[-1]
        chunk_records.append(record)
        reassembled_parts.append(chunk_data)
        byte_cursor += len(chunk_data)

    reassembled = b"".join(reassembled_parts)
    exact = reassembled == data
    if not exact:
        raise RuntimeError("Chunk reassembly does not exactly reproduce master index bytes")

    root_block = latest_root_block(segments)
    root_meta: dict[str, Any] | None = None
    if root_block is not None:
        root_tree = extract_tree(root_block)
        root_meta = {
            "indexed_utc": block_timestamp(root_block),
            "fields": header_fields(root_block),
            "bytes": len(root_block.encode("utf-8")),
            "sha256": sha256(root_block.encode("utf-8")),
            "tree_found": root_tree is not None,
        }
        write_text(snapshot_dir / "latest_root_block.txt", root_block)
        write_text(BASELINE_BLOCK, root_block)
        if root_tree is not None:
            write_text(snapshot_dir / "latest_root_tree.txt", root_tree)

    manifest = {
        "schema": 1,
        "generated_utc": utc_now(),
        "source": str(MASTER.relative_to(ROOT)).replace(os.sep, "/"),
        "source_bytes": len(data),
        "source_sha256": original_sha256,
        "source_git_blob_sha1": blob_sha1,
        "logical_segments": len(segments),
        "target_chunk_bytes": target_bytes,
        "chunk_count": len(chunks),
        "exact_reassembly_verified": exact,
        "snapshot_directory": str(snapshot_dir.relative_to(ROOT)).replace(os.sep, "/"),
        "chunks": chunk_records,
        "latest_root_block": root_meta,
    }
    write_json(snapshot_dir / "manifest.json", manifest)
    write_json(BASELINE_INFO, manifest)

    router = [
        "# Archive Master Index — chunk router",
        "",
        "This is a generated administrative navigation layer. The historical Dashboard",
        "master index remains the source ledger and was NOT modified by the chunk run.",
        "",
        f"Generated UTC: {manifest['generated_utc']}",
        f"Source: `{manifest['source']}`",
        f"Source bytes: {manifest['source_bytes']}",
        f"Source SHA-256: `{original_sha256}`",
        f"Source Git blob SHA-1: `{blob_sha1}`",
        f"Exact byte reassembly verified: **{'YES' if exact else 'NO'}**",
        f"Logical historical segments found: {len(segments)}",
        f"Chunks: {len(chunks)}",
        f"Snapshot: `{manifest['snapshot_directory']}`",
        "",
        "## Chunks",
    ]
    for rec in chunk_records:
        dates = ""
        if rec["first_indexed_utc"]:
            dates = f" — {rec['first_indexed_utc']} → {rec['last_indexed_utc']}"
        router.append(
            f"- `{snapshot_rel.as_posix()}/{rec['chunk']}` — {rec['bytes']} bytes{dates}"
        )
    if root_meta:
        router.extend([
            "",
            "## Pre-refresh root baseline",
            f"Latest root block date: `{root_meta.get('indexed_utc')}`",
            f"Baseline copy: `BASELINE_ROOT_BLOCK.txt`",
            "This baseline was captured before the next requested root refresh.",
        ])
    write_text(INDEX_HOME / "README.md", "\n".join(router) + "\n")

    CHUNK_LOGS.mkdir(parents=True, exist_ok=True)
    log_path = CHUNK_LOGS / f"chunk_{stamp()}.txt"
    log = [
        "ARCHIVE INDEX CHUNK RUN",
        f"UTC: {utc_now()}",
        f"SOURCE: {manifest['source']}",
        f"SOURCE_BYTES: {len(data)}",
        f"SOURCE_SHA256: {original_sha256}",
        f"SOURCE_GIT_BLOB_SHA1: {blob_sha1}",
        f"LOGICAL_SEGMENTS: {len(segments)}",
        f"CHUNKS: {len(chunks)}",
        f"TARGET_CHUNK_BYTES: {target_bytes}",
        f"EXACT_REASSEMBLY_VERIFIED: {'YES' if exact else 'NO'}",
        f"LATEST_ROOT_BLOCK_UTC: {root_meta.get('indexed_utc') if root_meta else 'NOT_FOUND'}",
        "MASTER_INDEX_MODIFIED: NO",
    ]
    write_text(log_path, "\n".join(log) + "\n")
    print("\n".join(log))
    return 0


def parse_tree_entries(tree: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    stack: list[str] = []
    for raw in tree.splitlines():
        line = raw.rstrip("\r\n")
        if not line or line in {"./", "."}:
            continue
        m = TREE_LINE_RE.match(line)
        if not m:
            continue
        prefix, shown_name = m.groups()
        depth = len(prefix) // 4
        is_dir = shown_name.endswith("/")
        name = shown_name[:-1] if is_dir else shown_name
        if depth < len(stack):
            stack = stack[:depth]
        while len(stack) < depth:
            stack.append("<unknown>")
        path_parts = stack[:depth] + [name]
        path = "/".join(path_parts)
        entries[path] = "dir" if is_dir else "file"
        if is_dir:
            if len(stack) == depth:
                stack.append(name)
            else:
                stack[depth] = name
                stack = stack[: depth + 1]
    return entries


def warnings_in(text: str) -> list[str]:
    warnings: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if "Index truncated at MAX_ENTRIES=" in stripped or stripped.startswith("- STOPPED:"):
            warnings.append(stripped.lstrip("- "))
    return warnings


def task_compare() -> int:
    if not BASELINE_BLOCK.exists():
        raise FileNotFoundError("No pre-refresh BASELINE_ROOT_BLOCK.txt. Run chunk task first.")
    if not CURRENT_ROOT_INDEX.exists():
        raise FileNotFoundError("Current root ..findex.txt missing")

    baseline_text = BASELINE_BLOCK.read_text(encoding="utf-8", errors="strict")
    current_text = CURRENT_ROOT_INDEX.read_text(encoding="utf-8", errors="strict")
    baseline_tree = extract_tree(baseline_text)
    current_tree = extract_tree(current_text)
    if baseline_tree is None or current_tree is None:
        raise RuntimeError("Could not locate ```text tree in baseline or current root index")

    before = parse_tree_entries(baseline_tree)
    after = parse_tree_entries(current_tree)
    before_keys = set(before)
    after_keys = set(after)
    added = sorted(after_keys - before_keys)
    removed = sorted(before_keys - after_keys)
    type_changed = sorted(p for p in before_keys & after_keys if before[p] != after[p])

    baseline_fields = header_fields(baseline_text)
    current_fields = header_fields(current_text)
    baseline_warnings = warnings_in(baseline_text)
    current_warnings = warnings_in(current_text)
    complete_for_claims = not baseline_warnings and not current_warnings

    ts = stamp()
    out_dir = INDEX_HOME / "deltas"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = {
        "schema": 1,
        "generated_utc": utc_now(),
        "comparison_type": "structural_path_delta",
        "limitations": [
            "This compares indexed path/type structure only; it does not detect content-only edits to unchanged paths.",
            "Completeness depends on both index runs' depth/entry limits and warnings.",
        ],
        "baseline_fields": baseline_fields,
        "current_fields": current_fields,
        "baseline_warnings": baseline_warnings,
        "current_warnings": current_warnings,
        "no_truncation_warning_observed": complete_for_claims,
        "counts": {
            "baseline_entries": len(before),
            "current_entries": len(after),
            "added": len(added),
            "removed": len(removed),
            "type_changed": len(type_changed),
        },
        "added": [{"path": p, "type": after[p]} for p in added],
        "removed": [{"path": p, "type": before[p]} for p in removed],
        "type_changed": [
            {"path": p, "before": before[p], "after": after[p]} for p in type_changed
        ],
    }
    json_path = out_dir / f"root_delta_{ts}.json"
    write_json(json_path, report_json)

    md = [
        "# Root structural index delta",
        "",
        f"Generated UTC: {report_json['generated_utc']}",
        f"Baseline indexed UTC: `{baseline_fields.get('INDEXED_UTC', 'unknown')}`",
        f"Current indexed UTC: `{current_fields.get('INDEXED_UTC', 'unknown')}`",
        "",
        "This is a structural path/type comparison, not a content-diff. An unchanged",
        "path may still contain edited content; future hash manifests can add that capability.",
        "",
        f"Baseline entries: {len(before)}",
        f"Current entries: {len(after)}",
        f"Added: {len(added)}",
        f"Removed: {len(removed)}",
        f"Type changed: {len(type_changed)}",
        "",
        f"No truncation/stop warning observed in either compared index: **{'YES' if complete_for_claims else 'NO'}**",
    ]
    if baseline_warnings or current_warnings:
        md.extend(["", "## Coverage warnings"])
        for w in baseline_warnings:
            md.append(f"- Baseline: {w}")
        for w in current_warnings:
            md.append(f"- Current: {w}")

    def add_section(title: str, values: list[str], kind_map: dict[str, str] | None = None) -> None:
        md.extend(["", f"## {title}"])
        if not values:
            md.append("None.")
            return
        limit = 1000
        for p in values[:limit]:
            suffix = f" ({kind_map[p]})" if kind_map else ""
            md.append(f"- `{p}`{suffix}")
        if len(values) > limit:
            md.append(f"- … {len(values) - limit} additional entries; see JSON report for complete list.")

    add_section("Added", added, after)
    add_section("Removed", removed, before)
    md.extend(["", "## Type changes"])
    if type_changed:
        for p in type_changed:
            md.append(f"- `{p}`: {before[p]} → {after[p]}")
    else:
        md.append("None.")

    md_path = out_dir / f"root_delta_{ts}.md"
    write_text(md_path, "\n".join(md) + "\n")
    write_text(INDEX_HOME / "LATEST_ROOT_DELTA.md", "\n".join(md) + "\n")

    DELTA_LOGS.mkdir(parents=True, exist_ok=True)
    log_path = DELTA_LOGS / f"delta_{ts}.txt"
    log = [
        "ARCHIVE ROOT INDEX DELTA",
        f"UTC: {utc_now()}",
        f"BASELINE_INDEXED_UTC: {baseline_fields.get('INDEXED_UTC', 'unknown')}",
        f"CURRENT_INDEXED_UTC: {current_fields.get('INDEXED_UTC', 'unknown')}",
        f"BASELINE_ENTRIES: {len(before)}",
        f"CURRENT_ENTRIES: {len(after)}",
        f"ADDED: {len(added)}",
        f"REMOVED: {len(removed)}",
        f"TYPE_CHANGED: {len(type_changed)}",
        f"NO_TRUNCATION_WARNING_OBSERVED: {'YES' if complete_for_claims else 'NO'}",
        f"REPORT_MD: {md_path.relative_to(ROOT).as_posix()}",
        f"REPORT_JSON: {json_path.relative_to(ROOT).as_posix()}",
        "LIMITATION: structural path/type delta only; unchanged-path content edits are not detected.",
    ]
    write_text(log_path, "\n".join(log) + "\n")
    print("\n".join(log))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, choices=["chunk", "compare"])
    parser.add_argument("--target-bytes", type=int, default=180_000)
    args = parser.parse_args()
    if args.task == "chunk":
        return task_chunk(args.target_bytes)
    return task_compare()


if __name__ == "__main__":
    raise SystemExit(main())
