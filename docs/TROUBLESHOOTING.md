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

Suggested fix:

1. Create handoff notes for important long-running sessions.
2. Archive huge active sessions that no longer need to be resumed directly.
3. Start fresh Codex threads from the handoff notes.

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
