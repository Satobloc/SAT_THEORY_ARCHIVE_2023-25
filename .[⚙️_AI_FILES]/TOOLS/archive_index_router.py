#!/usr/bin/env python3
"""Safely convert the Dashboard Archive Index from a monolith to a router.

The historical master ledger is preserved byte-for-byte in AI-side snapshot chunks.
Future INDEX_FOLDER appends may still land temporarily after the router sentinel;
`absorb` moves those complete appended blocks into an active monthly shard and then
restores the compact router. If absorb fails, the Dashboard append remains in place.

Administrative/navigation machinery only; never edits SAT source artifacts.
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
HOME = AI / "INDEXES" / "archive_index_history"
SNAPS = HOME / "snapshots"
ACTIVE = HOME / "active"
LOGS = AI / "LOGS" / "archive_index_router"
STATE = HOME / "ROUTER_STATE.json"
HISTORY = HOME / "HISTORY.md"
SENTINEL = "<!-- ARCHIVE_INDEX_APPEND_BUFFER: repo indexer appends below; workflow absorbs to AI shard -->"
ROUTER_MARKER = "ARCHIVE_INDEX_MODE: SHARDED_HISTORY_ROUTER"
SEP_RE = re.compile(r"(?m)^-{20,}\r?\n(?=INDEXED_UTC:\s*)")
LEGACY_RE = re.compile(r"(?m)^\[INDEXED\.[^\n]+\]\s*$")
FIELD_RE = re.compile(r"(?m)^([A-Z][A-Z0-9_]+):\s*(.*?)\s*$")
TEXT_BLOCK_RE = re.compile(r"```text\s*\r?\n.*?```", re.DOTALL)


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso() -> str:
    return now().isoformat()


def stamp() -> str:
    return now().strftime("%Y%m%d_%H%M%S")


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def logical_segments(text: str) -> list[str]:
    starts = {m.start() for m in SEP_RE.finditer(text)}
    starts.update(m.start() for m in LEGACY_RE.finditer(text))
    ordered = sorted(starts)
    if not ordered:
        return [text]
    out: list[str] = []
    if ordered[0] > 0:
        out.append(text[:ordered[0]])
    for i, s in enumerate(ordered):
        e = ordered[i + 1] if i + 1 < len(ordered) else len(text)
        out.append(text[s:e])
    return [x for x in out if x]


def group_segments(segments: list[str], target: int) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    size = 0
    for seg in segments:
        n = len(seg.encode("utf-8"))
        if buf and size + n > target:
            out.append("".join(buf)); buf = []; size = 0
        buf.append(seg); size += n
        if size >= target:
            out.append("".join(buf)); buf = []; size = 0
    if buf:
        out.append("".join(buf))
    return out


def block_date(text: str) -> str | None:
    fields = {m.group(1): m.group(2) for m in FIELD_RE.finditer(text)}
    if fields.get("INDEXED_UTC"):
        return fields["INDEXED_UTC"]
    m = re.search(r"(?m)^\[INDEXED\.([^\]]+)\]", text)
    return m.group(1).strip() if m else None


def load_state() -> dict[str, Any]:
    if not STATE.exists():
        return {}
    return json.loads(STATE.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def log(lines: list[str]) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    p = LOGS / f"router_{stamp()}.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def build_router(state: dict[str, Any]) -> str:
    snap = state.get("historical_snapshot", {})
    last = state.get("last_absorbed", {})
    lines = [
        "ARCHIVE INDEX ROUTER",
        ROUTER_MARKER,
        "",
        "Purpose: human-facing route into the accumulated structural-index history.",
        "The former monolithic Dashboard ledger is preserved byte-for-byte in AI-side",
        "snapshot chunks with hashes and a manifest. Future index blocks are stored in",
        "dated active shards so this Dashboard file remains small and readable.",
        "",
        "IMPORTANT",
        "- This is archive machinery/navigation, not SAT source content.",
        "- Do not infer source absence from index/search silence.",
        "- Use the newest applicable run for current structure and older runs for provenance.",
        "- Detailed index/run metadata belongs in AI indexes/logs.",
        "",
        f"MIGRATED_UTC: {state.get('migrated_utc', 'unknown')}",
        f"HISTORICAL_LEDGER_BYTES: {snap.get('bytes', 'unknown')}",
        f"HISTORICAL_LEDGER_SHA256: {snap.get('sha256', 'unknown')}",
        f"HISTORICAL_LEDGER_GIT_BLOB_SHA1: {snap.get('git_blob_sha1', 'unknown')}",
        f"EXACT_REASSEMBLY_VERIFIED: {snap.get('exact_reassembly_verified', False)}",
        f"HISTORICAL_SNAPSHOT: {snap.get('directory', 'unknown')}",
        f"HISTORICAL_MANIFEST: {snap.get('manifest', 'unknown')}",
        "",
        "CURRENT / ROUTING POINTERS",
        "- Current root structural index: `../..findex.txt` (repository root)",
        "- Human history router: `.[⚙️_AI_FILES]/INDEXES/archive_index_history/HISTORY.md`",
        "- Latest root structural delta: `.[⚙️_AI_FILES]/INDEXES/archive_index_history/LATEST_ROOT_DELTA.md`",
        "- Indexer logs: `.[⚙️_AI_FILES]/LOGS/folder_indexer/`",
        "- Router/sharding logs: `.[⚙️_AI_FILES]/LOGS/archive_index_router/`",
        "",
        f"LAST_ABSORBED_UTC: {last.get('absorbed_utc', 'none yet')}",
        f"LAST_ACTIVE_SHARD: {last.get('shard', 'none yet')}",
        "",
        "RETRIEVAL ORDER",
        "master router/history manifest → newest relevant shard or local `..findex` →",
        "folder summary/derivation/catalog → logs → exact source path → supplemental search",
        "",
        SENTINEL,
        "",
    ]
    return "\n".join(lines)


def rebuild_history(state: dict[str, Any]) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    snap = state.get("historical_snapshot", {})
    lines = [
        "# Archive structural-index history",
        "",
        "Human/AI router for preserved historical index snapshots and post-migration shards.",
        "",
        "## Historical monolithic ledger snapshot",
        f"- Migrated UTC: `{state.get('migrated_utc', 'unknown')}`",
        f"- Bytes: `{snap.get('bytes', 'unknown')}`",
        f"- SHA-256: `{snap.get('sha256', 'unknown')}`",
        f"- Git blob SHA-1: `{snap.get('git_blob_sha1', 'unknown')}`",
        f"- Exact reassembly verified: **{snap.get('exact_reassembly_verified', False)}**",
        f"- Directory: `{snap.get('directory', 'unknown')}`",
        f"- Manifest: `{snap.get('manifest', 'unknown')}`",
        "",
        "## Active shards",
    ]
    shards = sorted(ACTIVE.glob("*.txt")) if ACTIVE.exists() else []
    if not shards:
        lines.append("No post-migration shards yet.")
    else:
        for p in shards:
            data = p.read_bytes()
            dates = [d for d in (block_date(x) for x in logical_segments(data.decode('utf-8'))) if d]
            span = f" — {dates[0]} → {dates[-1]}" if dates else ""
            lines.append(f"- `{rel(p)}` — {len(data)} bytes — SHA-256 `{sha256(data)}`{span}")
    HISTORY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def snapshot_current(data: bytes, target_bytes: int) -> dict[str, Any]:
    text = data.decode("utf-8", errors="strict")
    segments = logical_segments(text)
    digest = sha256(data)
    directory = SNAPS / digest[:16]
    directory.mkdir(parents=True, exist_ok=True)
    chunks = group_segments(segments, target_bytes)
    records = []
    rebuilt: list[bytes] = []
    cursor = 0
    for i, chunk in enumerate(chunks, 1):
        b = chunk.encode("utf-8")
        name = f"chunk_{i:03d}.txt"
        (directory / name).write_bytes(b)
        dates = [d for d in (block_date(x) for x in logical_segments(chunk)) if d]
        records.append({
            "file": name, "bytes": len(b), "sha256": sha256(b),
            "byte_start": cursor, "byte_end_exclusive": cursor + len(b),
            "first_indexed_utc": dates[0] if dates else None,
            "last_indexed_utc": dates[-1] if dates else None,
        })
        rebuilt.append(b); cursor += len(b)
    exact = b"".join(rebuilt) == data
    if not exact:
        raise RuntimeError("Exact byte reassembly verification failed; refusing migration")
    manifest = {
        "schema": 1, "generated_utc": iso(), "source": rel(MASTER),
        "bytes": len(data), "sha256": digest, "git_blob_sha1": git_blob_sha1(data),
        "logical_segments": len(segments), "target_chunk_bytes": target_bytes,
        "chunk_count": len(chunks), "exact_reassembly_verified": exact,
        "chunks": records,
    }
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "bytes": len(data), "sha256": digest, "git_blob_sha1": git_blob_sha1(data),
        "logical_segments": len(segments), "chunk_count": len(chunks),
        "exact_reassembly_verified": exact, "directory": rel(directory),
        "manifest": rel(manifest_path),
    }


def finalize(target_bytes: int) -> int:
    if not MASTER.exists():
        raise FileNotFoundError(MASTER)
    data = MASTER.read_bytes()
    text = data.decode("utf-8", errors="strict")
    if ROUTER_MARKER in text:
        log(["ARCHIVE INDEX ROUTER FINALIZE", f"UTC: {iso()}", "NOOP: router already installed"])
        return 0
    if len(data) < 500_000 or "INDEXED_UTC:" not in text:
        raise RuntimeError("Master does not look like the expected large historical ledger; refusing migration")
    snap = snapshot_current(data, target_bytes)
    state = {
        "schema": 1, "migrated_utc": iso(), "mode": "SHARDED_HISTORY_ROUTER",
        "historical_snapshot": snap, "last_absorbed": {},
    }
    save_state(state)
    rebuild_history(state)
    MASTER.write_text(build_router(state), encoding="utf-8")
    written = MASTER.read_text(encoding="utf-8")
    if ROUTER_MARKER not in written or SENTINEL not in written:
        raise RuntimeError("Router rewrite verification failed")
    log([
        "ARCHIVE INDEX ROUTER FINALIZE", f"UTC: {iso()}",
        f"PRESERVED_BYTES: {snap['bytes']}", f"PRESERVED_SHA256: {snap['sha256']}",
        f"PRESERVED_GIT_BLOB_SHA1: {snap['git_blob_sha1']}",
        f"LOGICAL_SEGMENTS: {snap['logical_segments']}", f"CHUNKS: {snap['chunk_count']}",
        f"EXACT_REASSEMBLY_VERIFIED: {snap['exact_reassembly_verified']}",
        f"SNAPSHOT: {snap['directory']}", "DASHBOARD_REPLACED_WITH_ROUTER: YES",
    ])
    return 0


def absorb() -> int:
    if not MASTER.exists():
        return 0
    text = MASTER.read_text(encoding="utf-8", errors="strict")
    if ROUTER_MARKER not in text:
        print("Archive Index router not installed; absorb noop.")
        return 0
    if SENTINEL not in text:
        raise RuntimeError("Router marker present but append-buffer sentinel missing")
    _prefix, tail = text.split(SENTINEL, 1)
    payload = tail.lstrip("\r\n")
    if not payload.strip():
        print("Archive Index append buffer empty; absorb noop.")
        return 0
    if "INDEXED_UTC:" not in payload or "```text" not in payload:
        raise RuntimeError("Append buffer contains unrecognized material; leaving Dashboard untouched")
    opening_count = payload.count("```text")
    complete_blocks = len(TEXT_BLOCK_RE.findall(payload))
    if opening_count == 0 or complete_blocks != opening_count:
        raise RuntimeError(
            f"Append buffer appears incomplete ({complete_blocks}/{opening_count} complete text blocks); "
            "leaving Dashboard untouched"
        )

    ACTIVE.mkdir(parents=True, exist_ok=True)
    month = now().strftime("%Y-%m")
    shard = ACTIVE / f"{month}.txt"
    old = shard.read_bytes() if shard.exists() else b""
    pb = payload.encode("utf-8")
    shard.write_bytes(old + pb)
    if not shard.read_bytes().endswith(pb):
        raise RuntimeError("Shard append verification failed; Dashboard not cleaned")

    state = load_state()
    state["last_absorbed"] = {
        "absorbed_utc": iso(), "shard": rel(shard), "bytes": len(pb), "sha256": sha256(pb),
    }
    save_state(state)
    rebuild_history(state)
    MASTER.write_text(build_router(state), encoding="utf-8")
    log([
        "ARCHIVE INDEX ROUTER ABSORB", f"UTC: {iso()}", f"PAYLOAD_BYTES: {len(pb)}",
        f"PAYLOAD_SHA256: {sha256(pb)}", f"SHARD: {rel(shard)}",
        f"COMPLETE_TEXT_BLOCKS: {complete_blocks}",
        "SHARD_APPEND_VERIFIED: YES", "DASHBOARD_BUFFER_CLEANED: YES",
    ])
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=["finalize", "absorb"], required=True)
    p.add_argument("--target-bytes", type=int, default=180_000)
    a = p.parse_args()
    return finalize(a.target_bytes) if a.task == "finalize" else absorb()


if __name__ == "__main__":
    raise SystemExit(main())
