# Roadmap

## v0.1

- Read-only local Codex diagnostics
- Pseudonymous text output
- JSON output
- Large active session detection
- Log warning target summary
- Plugin and skill footprint summary
- Model cache age and size summary

## Possible v0.2

- HTML report export
- Safer handoff checklist generator
- Plugin/Skill warning explainer
- CI fixtures for multiple Codex schema versions

## v0.2 Updates

- Backup-first session archive worker with manifest input
- Deferred archive launcher for starting archive jobs from inside Codex
- JSON status files for `queued`, `waiting`, `archiving`, `done`, `failed`, and `skipped`
- `launchctl` background execution with Terminal fallback on macOS
- Restore script and archive index generation for selected sessions

## v0.3 Updates

- Active sessions above 50 MB are highlighted as priority handoff/archive candidates
- `logs_2.sqlite` above 64 MB is reported as watch-worthy
- `logs_2.sqlite` above 100 MB triggers a backup-first log-rotation recommendation
- Deferred archive jobs remove their `launchctl` label after completion
- Archive workers exit cleanly when an existing status file already says `done`
- Troubleshooting docs now explain `waiting` as a live Codex app-server blocker state
- Troubleshooting docs now include Terminal-first blocker inspection and stale
  process cleanup for Codex Desktop, app-server, and crashpad helper blockers
- Log rotation guidance now clarifies that `~/.codex/logs_2.sqlite*` must be
  handled as one SQLite group and should not be live-rotated

## v0.4 Updates

- Log diagnostics now report `total_rows`, `trace_percent`,
  `growth_bytes_delta`, and `growth_rows_delta`
- Default CLI sampling watches `logs_2.sqlite*` growth for 5 seconds
- `--log-growth-seconds 0` supports a static snapshot without waiting
- Active log burn is defined as TRACE at or above 70% plus continued byte or row
  growth during the sample window
- README and safety docs now contrast this evidence-based path with coarse
  trigger, symlink, and live database mutation fixes

## Non-Goals

- Reading credential files
- Uploading local diagnostics
- Automatic cleanup
- Killing local developer processes
- Replacing Codex maintenance tools
