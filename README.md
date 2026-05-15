# Codex Speed Doctor

> Find why Codex feels slow before you clean anything.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-2563eb)](pyproject.toml)
[![MIT License](https://img.shields.io/badge/license-MIT-16a34a)](LICENSE)
[![Read Only First](https://img.shields.io/badge/default-read--only-0f766e)](docs/SAFETY.md)
[![Local First](https://img.shields.io/badge/local--first-diagnostics-0891b2)](docs/TROUBLESHOOTING.md)

**Languages**: [中文](#中文) · [English](#english) · [日本語](#日本語) · [한국어](#한국어)

The GitHub Pages page supports instant in-page switching between Chinese, English, Japanese, and Korean: [docs/index.html](docs/index.html).

## 中文

**中文**：Codex Speed Doctor 是一个本地优先、默认只读的诊断工具，用来判断 Codex Desktop 或 CLI 为什么变慢：是 active session 太大、日志膨胀、插件/Skill warning、model cache 异常，还是本地进程状态不对。

## English

**English**: Codex Speed Doctor is a local-first, read-only diagnostic tool for slow Codex Desktop or CLI startup. It checks oversized active sessions, large logs, plugin or skill warnings, model cache state, and local process pressure before you touch anything.

## 日本語

**日本語**: Codex Speed Doctor は、Codex Desktop または CLI の起動が遅い原因を調べるローカル優先・既定読み取り専用の診断ツールです。大きな active session、肥大化したログ、plugin/Skill warning、model cache の状態、ローカルプロセスの負荷を整理して確認します。

## 한국어

**한국어**: Codex Speed Doctor는 Codex Desktop 또는 CLI 시작이 느린 원인을 확인하는 로컬 우선, 기본 읽기 전용 진단 도구입니다. 큰 active session, 커진 로그, plugin/Skill warning, model cache 상태, 로컬 프로세스 압력을 점검합니다.

![Codex Speed Doctor hero](docs/assets/hero-codex-diagnostic.png)

## Quick Start

最快只读运行：

```bash
git clone https://github.com/2023Anita/codex-speed-doctor.git
cd codex-speed-doctor
PYTHONPATH=src python3 -m codex_speed_doctor.cli
```

安装成本地命令：

```bash
python3 -m pip install -e .
codex-speed-doctor
```

机器可读输出：

```bash
PYTHONPATH=src python3 -m codex_speed_doctor.cli --json
```

The default report is read-only and pseudonymous. It does not move sessions, delete files, rewrite config, or print raw local session paths.

## What It Diagnoses

![Local state map](docs/assets/local-state-map.png)

| Area | What it checks | Why it matters |
| --- | --- | --- |
| Sessions | active thread count, archived thread count, large active session files | Huge active sessions can stay in the hot startup path and make new windows feel slow. |
| Logs | `logs_2.sqlite` size, warning/error targets, model/auth/network related events | Logs reveal repeated loader, plugin, cache, or network failures without reading private chat content. |
| Plugins | plugin cache size and sampled plugin folders | Manifest or loader warnings can add startup work or noisy retries. |
| Skills | `SKILL.md` count and skill folder size | Broken or stale skills can produce loader warnings before the UI is ready. |
| Model cache | presence, size, and age of `models_cache.json` | A stale or suspicious cache can correlate with "loading models" stalls. |
| Processes | Codex process count, Node process count, top Node memory usage | Helps separate local-state pressure from a live process issue. |

## Recommended Workflow

![Handoff archive flow](docs/assets/handoff-archive-flow.png)

1. **Diagnose**: run `codex-speed-doctor` first and identify the actual bottleneck.
2. **Handoff**: for important long conversations, write a short continuation note before archiving anything.
3. **Archive**: move only the inactive giant sessions out of the active path using a backup-first maintenance workflow.
4. **Index**: keep a small handoff index so old work can be found by topic later.
5. **Restore**: keep the backup and restore script so a mistaken archive can be reversed.

This tool intentionally stops at diagnosis. Cleanup should be a separate, explicit step after you have reviewed the report.

## Safety Model

![Safety boundary](docs/assets/safety-boundary.png)

Default behavior:

- read-only report mode
- no automatic cleanup
- no session moves
- no worktree archive
- no `config.toml` rewrite
- no `auth.json` read or output
- no raw session filenames unless you explicitly pass `--details`

See [docs/SAFETY.md](docs/SAFETY.md) for the full boundary and [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for symptom-based fixes.

## Example Output

```text
Codex Speed Doctor
==================
mode: read-only
codex_home: ~/.codex

Sessions
- total_threads: 253
- active_threads: 94
- archived_threads: 159
- active_sessions_gb: 1.836
- large_active_sessions:
  - session_001: 638.0 MB
  - session_002: 484.0 MB

Logs
- logs_mb: 88.9
- level_counts: INFO=561, TRACE=1287, WARN=84
- warning_targets: codex_core_plugins::manifest=20, codex_core_skills::loader=64
- model_auth_network_events: 12

Plugins and Skills
- plugin_cache_mb: 245.3
- plugin_dirs_sampled: 42
- skills_mb: 18.7
- skill_files: 66

Model Cache
- exists: true
- size_kb: 24.1
- age_hours: 7.4

Recommendations
- Large active sessions are present. Create handoff notes for important threads, then archive the huge active sessions.
- Skill loader warnings detected. Inspect the affected SKILL.md files before disabling anything.
```

## Commands

```bash
# Default read-only report
codex-speed-doctor

# JSON output for automation
codex-speed-doctor --json

# Show local paths and raw session filenames
codex-speed-doctor --details

# Use a custom Codex home
codex-speed-doctor --codex-home "/path/to/.codex"

# Change the large-session threshold
codex-speed-doctor --large-session-mb 100
```

## GitHub Pages

The polished project page lives at [docs/index.html](docs/index.html). After publishing the repository, enable GitHub Pages from the `/docs` directory.

## Development

```bash
python3 -m pip install -e .
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m codex_speed_doctor.cli
PYTHONPATH=src python3 -m codex_speed_doctor.cli --json
```

## Design Assets

- [docs/assets/hero-codex-diagnostic.png](docs/assets/hero-codex-diagnostic.png)
- [docs/assets/local-state-map.png](docs/assets/local-state-map.png)
- [docs/assets/handoff-archive-flow.png](docs/assets/handoff-archive-flow.png)
- [docs/assets/safety-boundary.png](docs/assets/safety-boundary.png)
- [design/figma-brief.md](design/figma-brief.md)

## License

MIT
