# Troubleshooting Slow Codex Startup

## Symptom: UI stalls at "loading models"

Likely causes:

- model list request is slow or blocked
- account/provider state is slow to resolve
- `models_cache.json` is stale or suspicious
- app-server startup is blocked by local initialization work

Suggested checks:

```bash
codex-speed-doctor
codex-speed-doctor --json
```

If the report shows model/auth/network related log events, back up `models_cache.json` before trying a rebuild.

## Symptom: new windows are slow after many long chats

Likely cause:

- active sessions are too large
- important old chats are still in the hot active session path
- any active session above 50 MB deserves priority handoff review

Suggested fix:

1. Create handoff notes for important long-running sessions.
2. Archive huge active sessions that no longer need to be resumed directly.
3. Start fresh Codex threads from the handoff notes.

Do not archive first and explain later. The handoff should capture the task
goal, repo/path, completed work, key files, constraints, and next steps.

## Symptom: `logs_2.sqlite` keeps growing

Interpretation:

- below 64 MB: usually no log maintenance needed
- 64 MB or above: watch growth and investigate repeated warnings
- 100 MB or above: prepare backup-first log rotation after Codex is closed

Suggested fix:

1. Run `codex-speed-doctor` and note `logs_mb`, `log_watch_mb`, and
   `log_cleanup_mb`.
2. Review warning targets before touching the log database.
3. Close Codex fully.
4. Back up or move `logs_2.sqlite`, `logs_2.sqlite-wal`, and
   `logs_2.sqlite-shm` together.
5. Reopen Codex and verify that a fresh log database was created.

Do not delete log files in place while Codex is running.

## Symptom: deferred archive stays in `waiting`

Meaning:

- the archive job has not failed by default
- Codex app-server processes are still alive
- reopening Codex too quickly can create new blockers

Suggested fix:

1. Quit Codex fully.
2. Check `status.json` and `archive.log` from a normal Terminal.
3. Stop old Codex app-server processes only after confirming they are stale.
4. Reopen Codex after the status becomes `done` or `failed`.

Newer deferred jobs remove their `launchctl` label after completion. The archive
worker also exits cleanly if a previous run already wrote `state: done`.

## Symptom: logs show skill loader warnings

Likely causes:

- invalid `SKILL.md`
- stale skill cache
- missing referenced files
- malformed frontmatter

Suggested fix:

1. Back up `~/.codex/skills`.
2. Inspect the specific skill named by the log target or detailed log output.
3. Move one suspicious skill out of the load path.
4. Restart Codex and compare startup time.

## Symptom: logs show plugin manifest warnings

Likely causes:

- stale plugin cache
- malformed plugin manifest
- missing plugin skill files

Suggested fix:

1. Back up `~/.codex/plugins`.
2. Move only the suspicious plugin folder out of the load path.
3. Restart Codex and verify.

Do not delete plugin folders as a first step.
