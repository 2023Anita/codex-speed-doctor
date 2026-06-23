from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from codex_speed_doctor.cli import collect_report, redact_report, render_text


def make_state_db(path: Path, session_file: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("create table threads (archived_at integer, rollout_path text)")
    conn.execute("insert into threads values (null, ?)", (str(session_file),))
    conn.execute("insert into threads values (123, ?)", (str(session_file),))
    conn.commit()
    conn.close()


def make_logs_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        create table logs (
            level text not null,
            target text not null,
            feedback_log_body text
        )
        """
    )
    conn.execute(
        "insert into logs values ('WARN', 'codex_core_skills::loader', 'model cache warning')"
    )
    conn.execute(
        "insert into logs values ('WARN', 'codex_core_plugins::manifest', 'plugin manifest warning')"
    )
    conn.commit()
    conn.close()


def make_trace_logs_db(path: Path, trace_rows: int, info_rows: int) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        create table logs (
            level text not null,
            target text not null,
            feedback_log_body text
        )
        """
    )
    conn.executemany(
        "insert into logs values ('TRACE', 'codex_api::endpoint::responses_websocket', '')",
        [() for _ in range(trace_rows)],
    )
    conn.executemany(
        "insert into logs values ('INFO', 'codex_otel.log_only', '')",
        [() for _ in range(info_rows)],
    )
    conn.commit()
    conn.close()


class CliTests(unittest.TestCase):
    def test_collect_report_flags_large_session_and_warnings(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            sessions_dir = codex_home / "sessions"
            sessions_dir.mkdir(parents=True)
            session_file = sessions_dir / "rollout-test.jsonl"
            session_file.write_bytes(b"x" * 2 * 1024 * 1024)
            make_state_db(codex_home / "state_5.sqlite", session_file)
            make_logs_db(codex_home / "logs_2.sqlite")
            (codex_home / "skills" / "demo").mkdir(parents=True)
            (codex_home / "skills" / "demo" / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
            (codex_home / "plugins" / "cache" / "demo").mkdir(parents=True)
            (codex_home / "models_cache.json").write_text("{}", encoding="utf-8")

            report = collect_report(codex_home, large_session_mb=1)

            self.assertTrue(report.read_only)
            self.assertEqual(report.sessions.total_threads, 2)
            self.assertEqual(report.sessions.active_threads, 1)
            self.assertEqual(report.sessions.archived_threads, 1)
            self.assertEqual(report.sessions.large_active_sessions[0].name, "rollout-test.jsonl")
            self.assertIn("codex_core_skills::loader", report.logs.warning_targets)
            self.assertEqual(report.logs.total_rows, 2)
            self.assertEqual(report.plugins_and_skills.skill_count, 1)
            self.assertTrue(
                any("above 50 MB" in item for item in report.recommendations)
            )

    def test_render_text_hides_session_filename_by_default(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            sessions_dir = codex_home / "sessions"
            sessions_dir.mkdir(parents=True)
            session_file = sessions_dir / "private-rollout.jsonl"
            session_file.write_bytes(b"x" * 2 * 1024 * 1024)
            make_state_db(codex_home / "state_5.sqlite", session_file)

            report = collect_report(codex_home, large_session_mb=1)
            text = render_text(report, details=False)

            self.assertNotIn("private-rollout.jsonl", text)
            self.assertIn("session_001", text)
            self.assertIn("large_session_threshold_mb: 50", text)

    def test_redact_report_hides_local_path_and_session_filename(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            sessions_dir = codex_home / "sessions"
            sessions_dir.mkdir(parents=True)
            session_file = sessions_dir / "private-rollout.jsonl"
            session_file.write_bytes(b"x" * 2 * 1024 * 1024)
            make_state_db(codex_home / "state_5.sqlite", session_file)

            report = redact_report(collect_report(codex_home, large_session_mb=1))

            self.assertEqual(report.codex_home, "~/.codex")
            self.assertEqual(report.sessions.large_active_sessions[0].name, "session_001")

    def test_logs_above_cleanup_threshold_get_backup_first_recommendation(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            codex_home.mkdir(parents=True)
            make_logs_db(codex_home / "logs_2.sqlite")
            wal_path = codex_home / "logs_2.sqlite-wal"
            wal_path.write_bytes(b"")
            with wal_path.open("r+b") as handle:
                handle.truncate(101 * 1024 * 1024)

            report = collect_report(codex_home, large_session_mb=50)
            text = render_text(report, details=False)

            self.assertIn("log_cleanup_mb: 100", text)
            self.assertTrue(
                any("backup-first log rotation" in item for item in report.recommendations)
            )

    def test_trace_dominant_without_growth_is_historical_not_active_burn(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            codex_home.mkdir(parents=True)
            make_trace_logs_db(codex_home / "logs_2.sqlite", trace_rows=8, info_rows=2)

            report = collect_report(
                codex_home, large_session_mb=50, log_growth_seconds=0
            )

            self.assertEqual(report.logs.total_rows, 10)
            self.assertEqual(report.logs.trace_percent, 80.0)
            self.assertEqual(report.logs.growth_rows_delta, 0)
            self.assertTrue(
                any("historical rather than an active burn" in item for item in report.recommendations)
            )
            self.assertFalse(
                any("active log-burn condition" in item for item in report.recommendations)
            )

    def test_trace_dominant_with_growth_flags_active_log_burn(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            codex_home.mkdir(parents=True)
            make_trace_logs_db(codex_home / "logs_2.sqlite", trace_rows=8, info_rows=2)

            def grow_logs(_seconds: float) -> None:
                conn = sqlite3.connect(codex_home / "logs_2.sqlite")
                conn.execute(
                    "insert into logs values ('TRACE', 'codex_api::endpoint::responses_websocket', '')"
                )
                conn.commit()
                conn.close()

            with patch("codex_speed_doctor.cli.time.sleep", side_effect=grow_logs):
                report = collect_report(
                    codex_home, large_session_mb=50, log_growth_seconds=1
                )

            self.assertEqual(report.logs.trace_percent, 72.73)
            self.assertEqual(report.logs.growth_rows_delta, 1)
            self.assertTrue(
                any("active log-burn condition" in item for item in report.recommendations)
            )


if __name__ == "__main__":
    unittest.main()
