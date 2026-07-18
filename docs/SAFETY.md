# Safety Boundary

Codex Speed Doctor is designed as a diagnostic tool, not an automatic cleaner.

## Default Mode

The default mode is read-only.

It reads local metadata from:

- `~/.codex/state_5.sqlite`
- `~/.codex/logs_2.sqlite`
- `~/.codex/sessions`
- `~/.codex/plugins/cache`
- `~/.codex/skills`
- `~/.codex/models_cache.json`

It does not read, print, or modify:

- `~/.codex/auth.json`
- API keys
- provider credentials
- browser cookies
- private project files outside Codex metadata

## Privacy

Default output is pseudonymous:

- large session files are shown as `session_001`, `session_002`, and so on
- local paths are shown as `~/.codex`
- warning targets are grouped by logger target instead of printing full log bodies

Use `--details` only when you explicitly want local paths and session filenames.

## What This Tool Does Not Do

The default `codex-speed-doctor` diagnostic command does not:

- delete sessions
- move active sessions
- archive worktrees
- rotate logs
- rewrite `config.toml`
- disable plugins
- disable skills
- rebuild `models_cache.json`
- stop Node, Codex, or other developer processes

Those actions can be useful, but they should be done by a separate backup-first maintenance workflow after the user reviews the report.

## Thresholds Are Review Prompts

Codex Speed Doctor now reports practical maintenance thresholds:

- active sessions above 50 MB are priority handoff/archive candidates
- `logs_2.sqlite` above 64 MB is watch-worthy
- `logs_2.sqlite` above 100 MB should trigger a backup-first rotation plan
- TRACE at or above 70% plus continued log growth during the sample window is
  treated as active log burn

These thresholds do not grant permission to mutate local state. They only make
the next safe human decision clearer.

## Log Burn Safety

Codex Speed Doctor does not treat a large log file or a high TRACE share as
enough evidence for emergency cleanup. Active log burn requires both:

- TRACE is dominant, currently 70% or higher.
- `logs_2.sqlite*` bytes or `logs` rows continue growing during the sample.

This avoids destructive or misleading fixes for historical log volume. The
normal response is still backup-first log rotation after Codex exits.

Do not use these as default remedies:

- SQLite triggers that block inserts into `logs`.
- Symlinking `logs_2.sqlite` into `/tmp`.
- Moving or deleting only `logs_2.sqlite` while WAL/SHM sidecar files exist.

Those approaches can hide useful diagnostics or leave SQLite state harder to
reason about. Keep them out of routine maintenance unless the user explicitly
requests a high-risk experimental design review.

## Explicit Archive Commands

Archive support is intentionally separate from the read-only diagnostic command.
Use it only after you have selected exact sessions and created handoff notes.

- `codex-speed-doctor-defer-archive` starts an external job and waits for Codex
  to exit before mutating local state.
- `codex-speed-doctor-archive` performs the backup-first archive work directly.

Both commands require a manifest with explicit absolute paths. Before creating
backup or archive directories, preflight requires every source to be a unique
`.jsonl` under `<codex_home>/sessions`, verifies that its handoff exists, and
confirms that `state_5.sqlite` still registers it as an active thread. Sources
outside the sessions root, archived or unregistered threads, duplicate sources,
and destination collisions are rejected without moving files.

The archive worker backs up `state_5.sqlite`, moves selected session files into
`archived_sessions`, updates the selected thread records, and writes restore
artifacts. It does not delete sessions permanently.

Process detection is fail-closed. The worker treats Codex Desktop, app-server,
OpenAI Codex helpers, and relevant Crashpad processes as blockers. If process
inspection itself fails, archive work stops instead of assuming Codex has exited.

Deferred archive jobs are designed to avoid repeated execution after completion:
the launchd label is removed when the worker exits, and a worker that sees an
existing `done` status exits without moving files again.

## Recommended Manual Fix Order

1. Create handoff notes for important giant active sessions.
2. Back up Codex local state.
3. Archive only the sessions you no longer need in the hot path.
4. Back up plugin and skill folders before moving suspicious items.
5. Back up `models_cache.json` before forcing Codex to rebuild it.
6. Rotate logs only after Codex is closed, and move
   `~/.codex/logs_2.sqlite`, `~/.codex/logs_2.sqlite-wal`, and
   `~/.codex/logs_2.sqlite-shm` together.

Never run a mutating cleanup while Codex is actively writing local state.

When a deferred job remains in `waiting`, inspect blockers before taking action:

```bash
ps -axo pid=,comm=,args= | rg -i "codex|openai.codex|app-server|crashpad"
```

Only stop stale Codex processes from a normal Terminal after the user has closed
Codex. Do not start repeated kill loops from inside an active Codex session.
