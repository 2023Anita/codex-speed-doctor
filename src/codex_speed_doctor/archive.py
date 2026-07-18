from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ArchivePlanItem:
    slug: str
    handoff: Path
    source: Path
    relative_source: Path
    thread_id: str


def codex_processes_running() -> list[str]:
    try:
        output = subprocess.check_output(["ps", "-axo", "pid=,comm=,args="], text=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"unable to inspect Codex processes: {exc}") from exc
    hits: list[str] = []
    for line in output.splitlines():
        lower = line.lower()
        is_blocker = any(
            marker in lower
            for marker in (
                "/applications/codex.app/contents/macos/codex",
                "codex app-server",
                "openai.codex",
                "com.openai.codex/web/crashpad",
            )
        )
        if is_blocker:
            hits.append(line.strip())
    return hits


def write_status(status_file: str | None, state: str, **details: object) -> None:
    if not status_file:
        return
    path = Path(status_file).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "state": state,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        **details,
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_status(status_file: str | None) -> dict[str, object] | None:
    if not status_file:
        return None
    path = Path(status_file).expanduser().resolve()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def wait_for_codex_exit(status_file: str | None = None) -> None:
    last_log = 0.0
    while codex_processes_running():
        blockers = codex_processes_running()
        write_status(status_file, "waiting", blockers=blockers)
        now = time.time()
        if now - last_log >= 30 or last_log == 0:
            print(f"waiting_for_codex_exit blockers={len(blockers)}", flush=True)
            for blocker in blockers:
                print(f"blocking_codex_process {blocker}", flush=True)
            last_log = now
        time.sleep(2)


def sqlite_backup(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(src)
    target = sqlite3.connect(dst)
    source.backup(target)
    target.close()
    source.close()


def read_manifest(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"manifest line {line_number} is not valid JSON: {exc}") from exc
        missing = [key for key in ("slug", "handoff", "source") if key not in item]
        if missing:
            raise ValueError(f"manifest line {line_number} is missing keys: {', '.join(missing)}")
        rows.append(
            {
                "slug": str(item["slug"]),
                "handoff": str(item["handoff"]),
                "source": str(item["source"]),
            }
        )
    if not rows:
        raise ValueError("manifest has no archive records")
    return rows


def preflight_manifest(path: Path, codex_home: Path) -> list[ArchivePlanItem]:
    manifest = path.expanduser().resolve()
    codex_home = codex_home.expanduser().resolve()
    sessions_root = (codex_home / "sessions").resolve()
    state_db = codex_home / "state_5.sqlite"
    if not manifest.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest}")
    if not sessions_root.is_dir():
        raise FileNotFoundError(f"Codex sessions root not found: {sessions_root}")
    if not state_db.is_file():
        raise FileNotFoundError(f"Codex state database not found: {state_db}")

    rows = read_manifest(manifest)
    seen_sources: set[Path] = set()
    plan: list[ArchivePlanItem] = []
    conn = sqlite3.connect(f"file:{state_db}?mode=ro", uri=True)
    try:
        for item in rows:
            handoff = Path(item["handoff"]).expanduser()
            raw_source = Path(item["source"]).expanduser()
            if not handoff.is_absolute():
                raise ValueError(f"handoff path must be absolute for {item['slug']}: {handoff}")
            if not handoff.is_file():
                raise FileNotFoundError(f"handoff not found for {item['slug']}: {handoff}")
            if not raw_source.is_absolute():
                raise ValueError(f"source path must be absolute for {item['slug']}: {raw_source}")

            source = raw_source.resolve()
            if not source.is_file():
                raise FileNotFoundError(f"source session not found for {item['slug']}: {source}")
            if source.suffix != ".jsonl":
                raise ValueError(f"source session must be a JSONL file for {item['slug']}: {source}")
            try:
                relative_source = source.relative_to(sessions_root)
            except ValueError as exc:
                raise ValueError(
                    f"source is outside Codex sessions root for {item['slug']}: {source}"
                ) from exc
            if source in seen_sources:
                raise ValueError(f"duplicate source session in manifest: {source}")
            seen_sources.add(source)

            row = conn.execute(
                "select id from threads where rollout_path in (?, ?) and archived_at is null",
                (str(source), str(raw_source)),
            ).fetchone()
            if row is None:
                raise ValueError(
                    f"source session is not an active thread in state_5.sqlite for {item['slug']}: {source}"
                )
            plan.append(
                ArchivePlanItem(
                    slug=item["slug"],
                    handoff=handoff.resolve(),
                    source=source,
                    relative_source=relative_source,
                    thread_id=str(row[0]),
                )
            )
    finally:
        conn.close()
    return plan


def write_restore_script(manifest: Path, state_db: Path, backup_root: Path) -> None:
    restore = backup_root / "restore-selected-sessions.py"
    restore.write_text(
        f'''#!/usr/bin/env python3
import json
import shutil
import sqlite3
from pathlib import Path

manifest = Path(r"{manifest}")
state_db = Path(r"{state_db}")
conn = sqlite3.connect(state_db)
conn.execute("pragma busy_timeout=10000")
for line in manifest.read_text(encoding="utf-8").splitlines():
    rec = json.loads(line)
    src = Path(rec["archived_path"])
    dest = Path(rec["original_path"])
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
    if rec.get("thread_id"):
        conn.execute(
            "update threads set rollout_path=?, archived=0, archived_at=NULL where id=?",
            (str(dest), rec["thread_id"]),
        )
conn.commit()
conn.close()
print("restored selected sessions")
''',
        encoding="utf-8",
    )
    restore.chmod(0o755)


def write_index(records: list[dict[str, object]], backup_root: Path, archive_root: Path) -> None:
    index = backup_root / "archive-index.md"
    lines = [
        "# Codex Session Archive Index",
        "",
        f"- Backup root: `{backup_root}`",
        f"- Archive root: `{archive_root}`",
        f"- Restore script: `{backup_root / 'restore-selected-sessions.py'}`",
        "",
    ]
    for rec in records:
        lines.extend(
            [
                f"## {rec['slug']}",
                "",
                f"- Handoff: `{rec['handoff']}`",
                f"- Thread ID: `{rec.get('thread_id') or 'not-found'}`",
                f"- Original session: `{rec['original_path']}`",
                f"- Archived session: `{rec['archived_path']}`",
                f"- Status: `{rec['status']}`",
                f"- Size MB: `{rec['size_mb']}`",
                "",
            ]
        )
    index.write_text("\n".join(lines), encoding="utf-8")


def archive(args: argparse.Namespace) -> int:
    codex_home = Path(args.codex_home).expanduser().resolve()
    state_db = codex_home / "state_5.sqlite"
    existing_status = read_status(args.status_file)
    if existing_status and existing_status.get("state") == "done":
        print("archive_already_done")
        return 0

    if args.wait_for_codex_exit:
        wait_for_codex_exit(args.status_file)
    elif codex_processes_running():
        write_status(args.status_file, "skipped", reason="codex_running")
        print("apply_skipped_codex_running")
        return 3

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = codex_home / "backups" / f"selected-session-archive-{stamp}"
    archive_root = codex_home / "archived_sessions" / f"selected-session-archive-{stamp}"
    plan = preflight_manifest(Path(args.manifest), codex_home)
    destinations = [archive_root / item.relative_source for item in plan]
    if len(set(destinations)) != len(destinations):
        raise ValueError("archive manifest resolves to duplicate destination paths")
    existing_destinations = [path for path in destinations if path.exists()]
    if existing_destinations:
        raise FileExistsError(f"archive destination already exists: {existing_destinations[0]}")

    write_status(
        args.status_file,
        "archiving",
        codex_home=str(codex_home),
        manifest=str(Path(args.manifest).expanduser().resolve()),
    )
    backup_root.mkdir(parents=True, exist_ok=True)
    archive_root.mkdir(parents=True, exist_ok=True)

    sqlite_backup(state_db, backup_root / "state_5.sqlite")
    for name in ["session_index.jsonl", ".codex-global-state.json"]:
        src = codex_home / name
        if src.exists():
            shutil.copy2(src, backup_root / name)

    conn = sqlite3.connect(state_db)
    conn.execute("pragma busy_timeout=10000")
    now = int(time.time())
    records: list[dict[str, object]] = []
    moved_manifest = backup_root / "moved-sessions.jsonl"

    with moved_manifest.open("w", encoding="utf-8") as handle:
        for item in plan:
            source = item.source
            dest = archive_root / item.relative_source
            thread_id = item.thread_id
            size_mb = round(source.stat().st_size / 1024 / 1024, 1) if source.exists() else 0.0
            status = "missing"
            if source.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                status = "archived"
            if thread_id:
                conn.execute(
                    "update threads set rollout_path=?, archived=1, archived_at=? where id=?",
                    (str(dest), now, thread_id),
                )
            record = {
                "slug": item.slug,
                "handoff": str(item.handoff),
                "thread_id": thread_id,
                "original_path": str(source),
                "archived_path": str(dest),
                "status": status,
                "size_mb": size_mb,
            }
            records.append(record)
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"{status} {item.slug} {size_mb}MB", flush=True)

    conn.commit()
    try:
        conn.execute("pragma wal_checkpoint(truncate)")
    except sqlite3.Error as exc:
        print(f"wal_checkpoint_skipped {exc}", flush=True)
    conn.close()

    write_restore_script(moved_manifest, state_db, backup_root)
    write_index(records, backup_root, archive_root)
    write_status(
        args.status_file,
        "done",
        backup_root=str(backup_root),
        archive_root=str(archive_root),
        moved_manifest=str(moved_manifest),
        records=records,
    )
    print(f"backup_root {backup_root}")
    print(f"archive_root {archive_root}")
    print(f"manifest {moved_manifest}")
    print("done")
    return 0


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive selected Codex sessions from a manifest.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--wait-for-codex-exit", action="store_true")
    parser.add_argument("--status-file", help="Write JSON status updates for deferred archive jobs.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return archive(args)
    except Exception as exc:
        write_status(args.status_file, "failed", error=f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
