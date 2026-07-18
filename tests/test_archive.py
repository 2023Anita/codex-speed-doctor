from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from codex_speed_doctor import archive


def make_threads_db(path: Path, session_file: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        create table threads (
            id text primary key,
            title text,
            rollout_path text,
            archived integer default 0,
            archived_at integer
        )
        """
    )
    conn.execute(
        "insert into threads values (?, ?, ?, 0, NULL)",
        ("thread-test", "Test Thread", str(session_file)),
    )
    conn.commit()
    conn.close()


def make_archive_fixture(tmp: str) -> tuple[Path, Path, Path, Path, Path]:
    root = Path(tmp)
    codex_home = root / ".codex"
    session_file = codex_home / "sessions" / "2026" / "05" / "19" / "rollout-test.jsonl"
    session_file.parent.mkdir(parents=True)
    session_file.write_text('{"type":"session_meta"}\n', encoding="utf-8")
    handoff = root / "handoff.md"
    handoff.write_text("# Handoff\n", encoding="utf-8")
    manifest = root / "manifest.jsonl"
    manifest.write_text(
        json.dumps({"slug": "test-session", "handoff": str(handoff), "source": str(session_file)}) + "\n",
        encoding="utf-8",
    )
    make_threads_db(codex_home / "state_5.sqlite", session_file)
    status_file = root / "status.json"
    return codex_home, session_file, handoff, manifest, status_file


class ArchiveTests(unittest.TestCase):
    def test_process_detection_includes_desktop_app_server_and_helpers(self) -> None:
        process_output = "\n".join(
            [
                "101 /Applications/Codex.app/Contents/MacOS/Codex /Applications/Codex.app/Contents/MacOS/Codex",
                "102 codex /Applications/Codex.app/Contents/Resources/codex app-server",
                "103 helper /Applications/Codex.app/Contents/Frameworks/openai.codex.helper",
                "104 crashpad browser_crashpad_handler --database=/tmp/com.openai.codex/web/Crashpad",
                "105 python python3 unrelated.py",
            ]
        )
        with mock.patch.object(subprocess, "check_output", return_value=process_output):
            blockers = archive.codex_processes_running()

        self.assertEqual(len(blockers), 4)
        self.assertFalse(any("unrelated.py" in blocker for blocker in blockers))

    def test_process_detection_failure_is_fail_closed(self) -> None:
        with mock.patch.object(
            subprocess, "check_output", side_effect=subprocess.CalledProcessError(1, "ps")
        ):
            with self.assertRaisesRegex(RuntimeError, "inspect Codex processes"):
                archive.codex_processes_running()

    def test_archive_rejects_source_outside_sessions_root(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home, session_file, handoff, manifest, status_file = make_archive_fixture(tmp)
            outside = Path(tmp) / "outside.jsonl"
            outside.write_text('{"type":"session_meta"}\n', encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {"slug": "outside", "handoff": str(handoff), "source": str(outside)}
                )
                + "\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                manifest=str(manifest),
                codex_home=str(codex_home),
                wait_for_codex_exit=False,
                status_file=str(status_file),
            )
            with mock.patch.object(archive, "codex_processes_running", return_value=[]):
                with self.assertRaisesRegex(ValueError, "outside Codex sessions root"):
                    archive.archive(args)

            self.assertTrue(outside.exists())
            self.assertTrue(session_file.exists())
            self.assertFalse((codex_home / "backups").exists())

    def test_archive_rejects_session_not_registered_as_active(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home, session_file, handoff, manifest, status_file = make_archive_fixture(tmp)
            unregistered = session_file.with_name("rollout-unregistered.jsonl")
            unregistered.write_text('{"type":"session_meta"}\n', encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "slug": "unregistered",
                        "handoff": str(handoff),
                        "source": str(unregistered),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                manifest=str(manifest),
                codex_home=str(codex_home),
                wait_for_codex_exit=False,
                status_file=str(status_file),
            )
            with mock.patch.object(archive, "codex_processes_running", return_value=[]):
                with self.assertRaisesRegex(ValueError, "not an active thread"):
                    archive.archive(args)

            self.assertTrue(unregistered.exists())
            self.assertFalse((codex_home / "backups").exists())

    def test_archive_moves_session_and_writes_restore_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home, session_file, _handoff, manifest, status_file = make_archive_fixture(tmp)
            args = argparse.Namespace(
                manifest=str(manifest),
                codex_home=str(codex_home),
                wait_for_codex_exit=False,
                status_file=str(status_file),
            )
            with mock.patch.object(archive, "codex_processes_running", return_value=[]):
                rc = archive.archive(args)

            self.assertEqual(rc, 0)
            self.assertFalse(session_file.exists())
            archived = list((codex_home / "archived_sessions").rglob("rollout-test.jsonl"))
            self.assertEqual(len(archived), 1)
            conn = sqlite3.connect(codex_home / "state_5.sqlite")
            row = conn.execute("select archived, archived_at, rollout_path from threads where id=?", ("thread-test",)).fetchone()
            conn.close()
            self.assertEqual(row[0], 1)
            self.assertIsNotNone(row[1])
            self.assertEqual(Path(row[2]).resolve(), archived[0].resolve())
            backups = list((codex_home / "backups").glob("selected-session-archive-*"))
            self.assertEqual(len(backups), 1)
            self.assertTrue((backups[0] / "moved-sessions.jsonl").exists())
            self.assertTrue((backups[0] / "restore-selected-sessions.py").exists())
            self.assertTrue((backups[0] / "archive-index.md").exists())
            status = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(status["state"], "done")
            self.assertEqual(status["records"][0]["status"], "archived")

    def test_archive_skips_when_codex_is_running_without_wait(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home, session_file, _handoff, manifest, status_file = make_archive_fixture(tmp)
            args = argparse.Namespace(
                manifest=str(manifest),
                codex_home=str(codex_home),
                wait_for_codex_exit=False,
                status_file=str(status_file),
            )
            with mock.patch.object(archive, "codex_processes_running", return_value=["123 codex app-server"]):
                rc = archive.archive(args)

            self.assertEqual(rc, 3)
            self.assertTrue(session_file.exists())
            status = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(status["state"], "skipped")
            self.assertEqual(status["reason"], "codex_running")

    def test_archive_done_status_is_idempotent(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home, session_file, _handoff, manifest, status_file = make_archive_fixture(tmp)
            status_file.write_text(
                json.dumps({"state": "done", "archive_root": "/already/done"}) + "\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                manifest=str(manifest),
                codex_home=str(codex_home),
                wait_for_codex_exit=True,
                status_file=str(status_file),
            )
            with mock.patch.object(archive, "wait_for_codex_exit") as wait_mock:
                rc = archive.archive(args)

            self.assertEqual(rc, 0)
            self.assertTrue(session_file.exists())
            wait_mock.assert_not_called()

    def test_defer_archive_dry_run_writes_queued_status_without_moving_session(self) -> None:
        with TemporaryDirectory() as tmp:
            codex_home, session_file, _handoff, manifest, _status_file = make_archive_fixture(tmp)
            jobs_root = Path(tmp) / "jobs"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "codex_speed_doctor.defer_archive",
                    "--manifest",
                    str(manifest),
                    "--codex-home",
                    str(codex_home),
                    "--jobs-root",
                    str(jobs_root),
                    "--dry-run",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            self.assertTrue(session_file.exists())
            status_path = next(
                Path(line.split(" ", 1)[1])
                for line in result.stdout.splitlines()
                if line.startswith("status_path ")
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(status["state"], "queued")
            self.assertEqual(status["records"], 1)
            self.assertIn("codex_speed_doctor.archive", status["command"])


if __name__ == "__main__":
    unittest.main()
