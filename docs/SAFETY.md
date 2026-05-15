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

It does not:

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

## Recommended Manual Fix Order

1. Create handoff notes for important giant active sessions.
2. Back up Codex local state.
3. Archive only the sessions you no longer need in the hot path.
4. Back up plugin and skill folders before moving suspicious items.
5. Back up `models_cache.json` before forcing Codex to rebuild it.

Never run a mutating cleanup while Codex is actively writing local state.
