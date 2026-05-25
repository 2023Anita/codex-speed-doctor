from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from codex_speed_doctor.archive import read_manifest, write_status


def validate_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path}")
    rows = read_manifest(path)
    for item in rows:
        handoff = Path(item["handoff"]).expanduser()
        source = Path(item["source"]).expanduser()
        if not handoff.is_absolute():
            raise ValueError(f"handoff path must be absolute for {item['slug']}: {handoff}")
        if not source.is_absolute():
            raise ValueError(f"source path must be absolute for {item['slug']}: {source}")
        if not handoff.exists():
            raise FileNotFoundError(f"handoff not found for {item['slug']}: {handoff}")
        if not source.exists():
            raise FileNotFoundError(f"source session not found for {item['slug']}: {source}")
    return rows


def build_archive_command(
    python: str,
    manifest: Path,
    codex_home: Path,
    status_file: Path,
) -> list[str]:
    return [
        python,
        "-m",
        "codex_speed_doctor.archive",
        "--manifest",
        str(manifest),
        "--codex-home",
        str(codex_home),
        "--wait-for-codex-exit",
        "--status-file",
        str(status_file),
    ]


def launch_with_launchctl(label: str, command: list[str], log_path: Path) -> None:
    if platform.system() != "Darwin" or shutil.which("launchctl") is None:
        raise RuntimeError("launchctl is only available on macOS")
    # `launchctl submit` can leave a labelled job around after the worker exits
    # on some Codex Desktop runs. Wrap the worker so the label is removed after
    # completion; otherwise a finished archive can be re-run and overwrite the
    # status file with another `waiting` state.
    shell_command = (
        f"{shlex.join(command)}; "
        "exit_code=$?; "
        f"launchctl remove {shlex.quote(label)} >/dev/null 2>&1 || true; "
        "exit $exit_code"
    )
    subprocess.run(
        [
            "launchctl",
            "submit",
            "-l",
            label,
            "-o",
            str(log_path),
            "-e",
            str(log_path),
            "--",
            "/bin/zsh",
            "-lc",
            shell_command,
        ],
        check=True,
    )


def launch_with_terminal(command: list[str], log_path: Path) -> None:
    if platform.system() != "Darwin" or shutil.which("osascript") is None:
        raise RuntimeError("Terminal fallback is only available on macOS")
    shell_command = (
        f"{shlex.join(command)} >> {shlex.quote(str(log_path))} 2>&1; "
        "echo; echo 'Deferred Codex archive command finished. You can close this Terminal window.'"
    )
    script = f'tell application "Terminal" to do script {json.dumps(shell_command)}'
    subprocess.run(["osascript", "-e", 'tell application "Terminal" to activate', "-e", script], check=True)


def defer(args: argparse.Namespace) -> int:
    codex_home = Path(args.codex_home).expanduser().resolve()
    manifest = Path(args.manifest).expanduser().resolve()
    rows = validate_manifest(manifest)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_id = f"deferred-archive-{stamp}-{os.getpid()}"
    jobs_root = Path(args.jobs_root).expanduser().resolve() if args.jobs_root else codex_home / "archive_jobs"
    job_dir = jobs_root / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    log_path = job_dir / "archive.log"
    status_path = job_dir / "status.json"
    command = build_archive_command(sys.executable, manifest, codex_home, status_path)
    label = f"local.codex-speed-doctor.{job_id}"

    write_status(
        status_path,
        "queued",
        job_id=job_id,
        manifest=str(manifest),
        codex_home=str(codex_home),
        log_path=str(log_path),
        records=len(rows),
        command=command,
    )

    backend = "dry-run"
    if not args.dry_run:
        write_status(status_path, "launching", job_id=job_id, backend=args.backend, log_path=str(log_path), command=command)
        try:
            if args.backend in ("auto", "launchctl"):
                launch_with_launchctl(label, command, log_path)
                backend = "launchctl"
            else:
                raise RuntimeError("launchctl skipped by backend selection")
        except Exception as exc:
            if args.backend == "launchctl":
                write_status(status_path, "failed", job_id=job_id, backend="launchctl", error=f"{type(exc).__name__}: {exc}")
                raise
            launch_with_terminal(command, log_path)
            backend = "terminal"

    print(f"job_id {job_id}")
    print(f"backend {backend}")
    print(f"job_dir {job_dir}")
    print(f"log_path {log_path}")
    print(f"status_path {status_path}")
    return 0


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a deferred Codex session archive job.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--jobs-root", help="Directory for deferred archive job metadata.")
    parser.add_argument(
        "--backend",
        choices=("auto", "launchctl", "terminal"),
        default="auto",
        help="How to start the independent archive worker. Defaults to launchctl with Terminal fallback.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate and create job metadata without launching.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return defer(args)
    except Exception as exc:
        print(f"defer_archive_failed {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
