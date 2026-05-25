from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_LARGE_SESSION_MB = 50
LOG_WATCH_MB = 64
LOG_CLEANUP_MB = 100


@dataclass(frozen=True)
class PathSize:
    name: str
    bytes: int


@dataclass(frozen=True)
class SessionSummary:
    total_threads: int
    active_threads: int
    archived_threads: int
    active_sessions_gb: float
    large_active_sessions: list[PathSize]


@dataclass(frozen=True)
class LogSummary:
    logs_mb: float
    level_counts: dict[str, int]
    warning_targets: dict[str, int]
    model_related_events: int


@dataclass(frozen=True)
class PluginSkillSummary:
    plugin_count: int
    skill_count: int
    plugin_cache_mb: float
    skills_mb: float


@dataclass(frozen=True)
class ModelCacheSummary:
    exists: bool
    size_kb: float
    age_hours: float | None


@dataclass(frozen=True)
class ProcessSummary:
    codex_processes: int
    node_processes: int
    top_node_mb: list[float]


@dataclass(frozen=True)
class Report:
    codex_home: str
    read_only: bool
    sessions: SessionSummary
    logs: LogSummary
    plugins_and_skills: PluginSkillSummary
    model_cache: ModelCacheSummary
    processes: ProcessSummary
    recommendations: list[str]


def size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


def mb(value: int) -> float:
    return round(value / 1024 / 1024, 1)


def gb(value: int) -> float:
    return round(value / 1024 / 1024 / 1024, 3)


def open_sqlite_readonly(path: Path) -> sqlite3.Connection | None:
    if not path.exists():
        return None
    try:
        uri = path.resolve(strict=False).as_uri() + "?mode=ro"
        return sqlite3.connect(uri, uri=True)
    except sqlite3.Error:
        return None


def query_one(conn: sqlite3.Connection, sql: str, default: tuple[int, ...]) -> tuple:
    try:
        row = conn.execute(sql).fetchone()
        return row if row is not None else default
    except sqlite3.Error:
        return default


def summarize_sessions(codex_home: Path, large_session_mb: int) -> SessionSummary:
    state_db = codex_home / "state_5.sqlite"
    sessions_root = codex_home / "sessions"
    large_threshold = large_session_mb * 1024 * 1024
    total_threads = active_threads = archived_threads = 0
    active_paths: list[Path] = []

    conn = open_sqlite_readonly(state_db)
    if conn is not None:
        try:
            total_threads, active_threads, archived_threads = query_one(
                conn,
                """
                select
                  count(*),
                  sum(case when archived_at is null then 1 else 0 end),
                  sum(case when archived_at is not null then 1 else 0 end)
                from threads
                """,
                (0, 0, 0),
            )
            rows = conn.execute(
                "select rollout_path from threads where archived_at is null and rollout_path is not null"
            ).fetchall()
            active_paths = [Path(row[0]) for row in rows if row and row[0]]
        except sqlite3.Error:
            active_paths = []
        finally:
            conn.close()

    if not active_paths and sessions_root.exists():
        active_paths = [path for path in sessions_root.rglob("*.jsonl") if path.is_file()]

    large: list[PathSize] = []
    active_total = 0
    for path in active_paths:
        try:
            if not path.exists() or not path.is_file():
                continue
            item_size = path.stat().st_size
        except OSError:
            continue
        active_total += item_size
        if item_size >= large_threshold:
            large.append(PathSize(name=path.name, bytes=item_size))
    large.sort(key=lambda item: item.bytes, reverse=True)

    return SessionSummary(
        total_threads=int(total_threads or 0),
        active_threads=int(active_threads or 0),
        archived_threads=int(archived_threads or 0),
        active_sessions_gb=gb(active_total),
        large_active_sessions=large[:10],
    )


def summarize_logs(codex_home: Path) -> LogSummary:
    log_files = list(codex_home.glob("logs_2.sqlite*"))
    logs_total = sum(path.stat().st_size for path in log_files if path.is_file())
    conn = open_sqlite_readonly(codex_home / "logs_2.sqlite")
    level_counts: dict[str, int] = {}
    warning_targets: dict[str, int] = {}
    model_related_events = 0
    if conn is not None:
        try:
            level_counts = {
                str(level): int(count)
                for level, count in conn.execute(
                    "select level, count(*) from logs group by level"
                ).fetchall()
            }
            warning_targets = {
                str(target): int(count)
                for target, count in conn.execute(
                    """
                    select target, count(*)
                    from logs
                    where level in ('WARN', 'ERROR')
                    group by target
                    order by count(*) desc
                    limit 12
                    """
                ).fetchall()
            }
            model_related_events = int(
                query_one(
                    conn,
                    """
                    select count(*)
                    from logs
                    where lower(coalesce(feedback_log_body, '')) like '%model%'
                       or lower(coalesce(feedback_log_body, '')) like '%auth%'
                       or lower(coalesce(feedback_log_body, '')) like '%login%'
                       or lower(coalesce(feedback_log_body, '')) like '%timeout%'
                       or lower(coalesce(feedback_log_body, '')) like '%network%'
                    """,
                    (0,),
                )[0]
            )
        except sqlite3.Error:
            pass
        finally:
            conn.close()
    return LogSummary(
        logs_mb=mb(logs_total),
        level_counts=level_counts,
        warning_targets=warning_targets,
        model_related_events=model_related_events,
    )


def summarize_plugins_and_skills(codex_home: Path) -> PluginSkillSummary:
    plugins_root = codex_home / "plugins"
    skills_root = codex_home / "skills"
    plugin_cache = plugins_root / "cache"
    plugin_count = count_dirs(plugin_cache, depth=3)
    skill_count = count_skill_files(skills_root)
    return PluginSkillSummary(
        plugin_count=plugin_count,
        skill_count=skill_count,
        plugin_cache_mb=mb(size_bytes(plugin_cache)),
        skills_mb=mb(size_bytes(skills_root)),
    )


def count_dirs(root: Path, depth: int) -> int:
    if not root.exists():
        return 0
    root_parts = len(root.parts)
    count = 0
    for path in root.rglob("*"):
        if path.is_dir() and len(path.parts) - root_parts <= depth:
            count += 1
    return count


def count_skill_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("SKILL.md") if path.is_file())


def summarize_model_cache(codex_home: Path) -> ModelCacheSummary:
    path = codex_home / "models_cache.json"
    if not path.exists():
        return ModelCacheSummary(exists=False, size_kb=0.0, age_hours=None)
    age_seconds = time.time() - path.stat().st_mtime
    return ModelCacheSummary(
        exists=True,
        size_kb=round(path.stat().st_size / 1024, 1),
        age_hours=round(age_seconds / 3600, 1),
    )


def summarize_processes() -> ProcessSummary:
    if platform.system() == "Windows":
        return ProcessSummary(codex_processes=0, node_processes=0, top_node_mb=[])
    try:
        output = subprocess.check_output(
            ["ps", "-axo", "pid=,rss=,comm=,args="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return ProcessSummary(codex_processes=0, node_processes=0, top_node_mb=[])

    codex = 0
    node_memory: list[float] = []
    for line in output.splitlines():
        lower = line.lower()
        parts = line.split(None, 3)
        if len(parts) < 3:
            continue
        rss_kb = parse_int(parts[1])
        if "codex" in lower and ("app-server" in lower or "openai.codex" in lower or "codex desktop" in lower):
            codex += 1
        if "node" in Path(parts[2]).name.lower():
            node_memory.append(round(rss_kb / 1024, 1))
    node_memory.sort(reverse=True)
    return ProcessSummary(
        codex_processes=codex,
        node_processes=len(node_memory),
        top_node_mb=node_memory[:5],
    )


def parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def build_recommendations(report: Report) -> list[str]:
    recommendations: list[str] = []
    if report.sessions.large_active_sessions:
        count = len(report.sessions.large_active_sessions)
        recommendations.append(
            f"{count} active session(s) are above {DEFAULT_LARGE_SESSION_MB} MB. Treat them as priority handoff/archive candidates: create handoffs first, then archive only after confirmation."
        )
    if report.logs.logs_mb >= LOG_CLEANUP_MB:
        recommendations.append(
            f"logs_2.sqlite is above {LOG_CLEANUP_MB} MB. Plan backup-first log rotation after closing Codex; do not delete logs in place."
        )
    elif report.logs.logs_mb >= LOG_WATCH_MB:
        recommendations.append(
            f"logs_2.sqlite is above {LOG_WATCH_MB} MB. Watch growth and rotate logs later with a backup-first workflow."
        )
    warning_targets = report.logs.warning_targets
    if any("skill" in target.lower() for target in warning_targets):
        recommendations.append(
            "Skill loader warnings detected. Inspect the affected SKILL.md files before disabling anything."
        )
    if any("plugin" in target.lower() or "manifest" in target.lower() for target in warning_targets):
        recommendations.append(
            "Plugin manifest warnings detected. Back up plugin cache before moving suspicious plugin folders out of the load path."
        )
    if report.logs.model_related_events:
        recommendations.append(
            "Model/auth/network related events exist in logs. If the UI stalls at model loading, back up models_cache.json before forcing a rebuild."
        )
    if not recommendations:
        recommendations.append(
            "No obvious local-state bottleneck found. Check account status, network latency, or provider availability next."
        )
    return recommendations


def collect_report(codex_home: Path, large_session_mb: int) -> Report:
    sessions = summarize_sessions(codex_home, large_session_mb)
    logs = summarize_logs(codex_home)
    plugins_and_skills = summarize_plugins_and_skills(codex_home)
    model_cache = summarize_model_cache(codex_home)
    processes = summarize_processes()
    draft = Report(
        codex_home=str(codex_home),
        read_only=True,
        sessions=sessions,
        logs=logs,
        plugins_and_skills=plugins_and_skills,
        model_cache=model_cache,
        processes=processes,
        recommendations=[],
    )
    return Report(
        codex_home=draft.codex_home,
        read_only=draft.read_only,
        sessions=draft.sessions,
        logs=draft.logs,
        plugins_and_skills=draft.plugins_and_skills,
        model_cache=draft.model_cache,
        processes=draft.processes,
        recommendations=build_recommendations(draft),
    )


def render_text(report: Report, details: bool) -> str:
    lines: list[str] = []
    lines.append("Codex Speed Doctor")
    lines.append("==================")
    lines.append("mode: read-only")
    lines.append(f"codex_home: {report.codex_home if details else '~/.codex'}")
    lines.append("")
    lines.append("Sessions")
    lines.append(f"- total_threads: {report.sessions.total_threads}")
    lines.append(f"- active_threads: {report.sessions.active_threads}")
    lines.append(f"- archived_threads: {report.sessions.archived_threads}")
    lines.append(f"- active_sessions_gb: {report.sessions.active_sessions_gb}")
    lines.append(f"- large_session_threshold_mb: {DEFAULT_LARGE_SESSION_MB}")
    if report.sessions.large_active_sessions:
        lines.append("- large_active_sessions:")
        for index, item in enumerate(report.sessions.large_active_sessions, start=1):
            name = item.name if details else f"session_{index:03d}"
            lines.append(f"  - {name}: {mb(item.bytes)} MB")
    else:
        lines.append("- large_active_sessions: none")
    lines.append("")
    lines.append("Logs")
    lines.append(f"- logs_mb: {report.logs.logs_mb}")
    lines.append(f"- log_watch_mb: {LOG_WATCH_MB}")
    lines.append(f"- log_cleanup_mb: {LOG_CLEANUP_MB}")
    lines.append(f"- level_counts: {format_mapping(report.logs.level_counts)}")
    lines.append(f"- warning_targets: {format_mapping(report.logs.warning_targets)}")
    lines.append(f"- model_auth_network_events: {report.logs.model_related_events}")
    lines.append("")
    lines.append("Plugins and Skills")
    lines.append(f"- plugin_cache_mb: {report.plugins_and_skills.plugin_cache_mb}")
    lines.append(f"- plugin_dirs_sampled: {report.plugins_and_skills.plugin_count}")
    lines.append(f"- skills_mb: {report.plugins_and_skills.skills_mb}")
    lines.append(f"- skill_files: {report.plugins_and_skills.skill_count}")
    lines.append("")
    lines.append("Model Cache")
    lines.append(f"- exists: {str(report.model_cache.exists).lower()}")
    lines.append(f"- size_kb: {report.model_cache.size_kb}")
    lines.append(f"- age_hours: {report.model_cache.age_hours}")
    lines.append("")
    lines.append("Processes")
    lines.append(f"- codex_processes: {report.processes.codex_processes}")
    lines.append(f"- node_processes: {report.processes.node_processes}")
    lines.append(f"- top_node_mb: {report.processes.top_node_mb}")
    lines.append("")
    lines.append("Recommendations")
    for item in report.recommendations:
        lines.append(f"- {item}")
    return "\n".join(lines)


def redact_report(report: Report) -> Report:
    redacted_sessions = [
        PathSize(name=f"session_{index:03d}", bytes=item.bytes)
        for index, item in enumerate(report.sessions.large_active_sessions, start=1)
    ]
    return Report(
        codex_home="~/.codex",
        read_only=report.read_only,
        sessions=SessionSummary(
            total_threads=report.sessions.total_threads,
            active_threads=report.sessions.active_threads,
            archived_threads=report.sessions.archived_threads,
            active_sessions_gb=report.sessions.active_sessions_gb,
            large_active_sessions=redacted_sessions,
        ),
        logs=report.logs,
        plugins_and_skills=report.plugins_and_skills,
        model_cache=report.model_cache,
        processes=report.processes,
        recommendations=report.recommendations,
    )


def format_mapping(mapping: dict[str, int]) -> str:
    if not mapping:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(mapping.items()))


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only diagnostics for slow Codex Desktop or CLI startup."
    )
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")),
        help="Path to Codex home. Defaults to CODEX_HOME or ~/.codex.",
    )
    parser.add_argument(
        "--large-session-mb",
        type=int,
        default=DEFAULT_LARGE_SESSION_MB,
        help="Threshold for flagging large active sessions.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show local paths and session filenames. Default output is pseudonymous.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    codex_home = Path(args.codex_home).expanduser().resolve()
    if not codex_home.exists():
        print(f"Codex home not found: {codex_home}", file=sys.stderr)
        return 2
    report = collect_report(codex_home, args.large_session_mb)
    if args.json:
        output_report = report if args.details else redact_report(report)
        print(json.dumps(asdict(output_report), indent=2, ensure_ascii=False))
    else:
        print(render_text(report, details=args.details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
