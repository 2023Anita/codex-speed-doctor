# Security Policy

Codex Speed Doctor reads local Codex metadata and includes optional maintenance
commands. Safety issues involving path validation, SQLite consistency, process
detection, credential exposure, or unintended mutation are treated as security
issues.

## Supported version

Security fixes are applied to the latest release line, currently `0.5.x`.

## Reporting

Please use GitHub's private security-advisory reporting for this repository when
available. Do not open a public issue containing:

- credentials, API keys, tokens, cookies, or authentication files
- private session content or rollout JSONL excerpts
- private local paths that identify people or confidential projects
- unredacted diagnostic databases or logs

Include a minimal reproduction with synthetic paths and fixtures.

## Security invariants

- The default diagnostic command is read-only.
- Credential files are not read or printed.
- Archive sources must stay under the configured Codex sessions root.
- Archive sources must correspond to active thread records.
- Process-inspection failure is fail-closed.
- Mutating workflows require explicit confirmation and backup-first execution.
- Live log rotation and automatic deletion are outside the supported workflow.

See [docs/SAFETY.md](docs/SAFETY.md) for the complete operational boundary.
