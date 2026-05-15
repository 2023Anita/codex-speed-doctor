from __future__ import annotations

import sqlite3
import unittest
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
            self.assertEqual(report.plugins_and_skills.skill_count, 1)
            self.assertTrue(any("Large active sessions" in item for item in report.recommendations))

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


if __name__ == "__main__":
    unittest.main()
