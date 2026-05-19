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

## Non-Goals

- Reading credential files
- Uploading local diagnostics
- Automatic cleanup
- Killing local developer processes
- Replacing Codex maintenance tools
