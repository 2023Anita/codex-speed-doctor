# Codex Speed Doctor

> Diagnose first. Preserve context. Change local state only with evidence and consent.

[![Version](https://img.shields.io/badge/version-0.5.0-149bd7)](docs/ROADMAP.md)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-1167a8)](pyproject.toml)
[![CI](https://github.com/2023Anita/codex-speed-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/2023Anita/codex-speed-doctor/actions/workflows/ci.yml)
[![Default](https://img.shields.io/badge/default-read--only-f3c84b)](docs/SAFETY.md)
[![License](https://img.shields.io/badge/license-MIT-e54b4b)](LICENSE)

**Languages**: [中文](#中文简介) · [English](#english) · [日本語](#日本語) · [한국어](#한국어)
**Live page**: [2023anita.github.io/codex-speed-doctor](https://2023anita.github.io/codex-speed-doctor/)

![A software engineer and Doraemon inspecting Codex local state together](docs/assets/hero-codex-diagnostic.png)

*The project’s visual metaphor: an engineer investigates the evidence while Doraemon brings the right tool—never a magic “delete everything” button.*

## 中文简介

Codex Speed Doctor 是一个本地优先、默认只读的 Codex Desktop / CLI 诊断工具。它帮助你判断卡顿究竟来自大会话、日志增长、插件或 Skill warning、model cache，还是残留进程，而不是一上来就清理文件。

这个项目来自 Anita 的真实工作方式：长期使用 Codex 完成科研、数据分析、教学材料和复杂项目，因此既重视性能，也重视对话上下文不能轻易丢失。

核心原则只有一句：**像工程师一样先测量，像研究者一样保留证据，再进行可恢复的维护。**

## English

Codex Speed Doctor is a local-first, read-only-by-default diagnostic tool for slow Codex Desktop or CLI startup. It separates oversized sessions, log growth, plugin or Skill warnings, model-cache state, and process blockers before recommending any maintenance.

## 日本語

Codex Speed Doctor は、Codex Desktop / CLI の遅延原因を調べるローカル優先・既定読み取り専用の診断ツールです。session、log、plugin、Skill、model cache、process blocker を分けて確認してから、安全な次の一手を示します。

## 한국어

Codex Speed Doctor는 느린 Codex Desktop / CLI의 원인을 확인하는 로컬 우선, 기본 읽기 전용 진단 도구입니다. session, log, plugin, Skill, model cache, process blocker를 분리해 확인한 뒤 안전한 다음 조치를 제안합니다.

## What changed in v0.5.0

This release turns the archive workflow from “backup-aware” into a stricter, preflight-gated operation.

| Change | Before | v0.5.0 | Advantage |
| --- | --- | --- | --- |
| Session path boundary | An absolute manifest path could point outside the sessions tree | Every source must resolve under `<codex_home>/sessions` | Prevents unrelated files from being moved |
| Thread-state validation | A file could be archived without a matching active thread | Every source must match an active `state_5.sqlite` record | Filesystem and database state stay aligned |
| Blocker detection | Process checks focused mainly on app-server | Desktop, app-server, OpenAI Codex helpers, and relevant Crashpad processes are blockers | Maintenance waits for the real writers to exit |
| Fail-closed behavior | A failed `ps` inspection could look like “nothing is running” | Process-inspection failure stops the archive | Unknown state is never treated as safe |
| Full preflight | Validation and mutation were partly interleaved | Handoff, source, thread, uniqueness, and destination are checked before backup directories are created | Invalid plans fail without partial work |
| Regression coverage | Core archive flow was tested | New tests cover boundary escape, unregistered sessions, blocker matching, and inspection failure | Safety behavior remains reviewable and repeatable |

### Why this is better than coarse cleanup

- It distinguishes **evidence** from assumptions.
- It preserves valuable work with a handoff before moving a large session.
- It treats SQLite main/WAL/SHM files as one group.
- It produces backups, manifests, indexes, and restore scripts.
- It refuses to mutate when the environment cannot be proven safe.

## Quick start

Run directly from the repository:

```bash
git clone https://github.com/2023Anita/codex-speed-doctor.git
cd codex-speed-doctor
PYTHONPATH=src python3 -m codex_speed_doctor.cli
```

Install editable commands:

```bash
python3 -m pip install -e .
codex-speed-doctor
```

Useful read-only modes:

```bash
# Machine-readable, pseudonymous report
codex-speed-doctor --json

# Static snapshot without the five-second growth sample
codex-speed-doctor --log-growth-seconds 0

# Reveal local filenames and paths only when explicitly needed
codex-speed-doctor --details
```

## What it diagnoses

![Doraemon guiding a map of Codex local-state areas](docs/assets/local-state-map.png)

*Doraemon’s inspection map: conversation scrolls represent sessions, the open logbook represents logs, modular blocks represent plugins, the stitched manual represents Skills, and the tool chest represents model cache. The laptop stays at the center because the report evaluates these signals together.*

| Area | Evidence collected | Why it matters |
| --- | --- | --- |
| Sessions | Active/archived thread counts, active size, large files | Large active conversations can remain in the startup path |
| Logs | SQLite file-group size, levels, warning targets, sampled growth | Separates historical volume from active disk burn |
| Plugins | Cache footprint and manifest warning targets | Identifies load-time noise before disabling anything |
| Skills | `SKILL.md` count, footprint, loader warnings | Finds malformed or unexpectedly heavy skill surfaces |
| Model cache | Presence, size, and age | Adds local evidence for “loading models” stalls |
| Processes | Codex and Node process summary | Distinguishes disk state from live-process pressure |

## Practical thresholds

Thresholds are review prompts—not permission to clean automatically.

- Active session above **50 MB** → review for handoff.
- `logs_2.sqlite*` at or above **64 MB** → watch growth.
- `logs_2.sqlite*` at or above **100 MB** → plan backup-first rotation after Codex exits.
- TRACE at or above **70%** plus byte or row growth → active log-burn signal.
- High TRACE without sampled growth → historical TRACE-heavy logging.

## Handoff-first archive

![Doraemon and an engineer preserving a handoff before archive](docs/assets/handoff-archive-flow.png)

*The red thread is continuity: first understand the large conversation, then distill a concise handoff, and only then place the selected session into a recoverable archive. The path loops back because restoration remains possible.*

The workflow is deliberately staged:

1. **Diagnose** — measure before changing anything.
2. **Handoff** — preserve goal, completed work, files, constraints, and next steps.
3. **Confirm** — show the exact selected sessions and mutation.
4. **Preflight** — validate path containment, active thread state, uniqueness, and destination.
5. **Archive** — wait for blockers, back up SQLite, move selected files, and update thread state.
6. **Verify** — rerun diagnosis and retain restore artifacts.

Manifest format:

```jsonl
{"slug":"long-running-task","handoff":"/absolute/path/handoff.md","source":"/absolute/path/rollout.jsonl"}
```

Deferred archive from inside Codex:

```bash
codex-speed-doctor-defer-archive --manifest "/absolute/path/manifest.jsonl"
```

Direct worker from Terminal after Codex is closed:

```bash
codex-speed-doctor-archive \
  --manifest "/absolute/path/manifest.jsonl" \
  --wait-for-codex-exit
```

Generated artifacts include a `state_5.sqlite` backup, `moved-sessions.jsonl`, `restore-selected-sessions.py`, and `archive-index.md`.

## Safety model

![Doraemon guarding the read-only diagnostic boundary](docs/assets/safety-boundary.png)

*Doraemon guards the central read-only workspace. Credentials remain sealed, backups remain separate, and the process gate must be clear before a confirmed maintenance action can enter.*

Default behavior:

- read-only and pseudonymous report
- no automatic cleanup or archive
- no `auth.json`, API-key, token, or cookie readout
- no raw session paths unless `--details` is explicitly used
- no archive when process inspection fails
- no session source outside `<codex_home>/sessions`
- no live log rotation

Read the full [safety boundary](docs/SAFETY.md) and [troubleshooting guide](docs/TROUBLESHOOTING.md).

## Log rotation rules

Treat the following as one SQLite group:

```text
~/.codex/logs_2.sqlite
~/.codex/logs_2.sqlite-wal
~/.codex/logs_2.sqlite-shm
```

Do not live-rotate, truncate only the main database, add insert-blocking triggers, or symlink the database to `/tmp` as a normal remedy.

## Project layout

```text
src/codex_speed_doctor/
├── cli.py              # read-only diagnosis
├── archive.py          # preflight + backup-first archive
└── defer_archive.py    # macOS deferred launcher

tests/
├── test_cli.py
└── test_archive.py

docs/
├── index.html          # multilingual GitHub Pages site
├── SAFETY.md
├── TROUBLESHOOTING.md
├── ROADMAP.md
└── assets/             # generated explanatory illustrations

.github/workflows/ci.yml # Python 3.10–3.13 verification
```

## Development and verification

```bash
python3 -m pip install -e .
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m codex_speed_doctor.cli --json --log-growth-seconds 0
```

Current verification baseline: **14 tests passing** on Python 3.13, plus Python syntax and HTML parse checks.

Contributions are welcome when they preserve the safety model. Read
[CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request and use
[SECURITY.md](SECURITY.md) for vulnerability reporting.

## Design note

The v0.5.0 visual system uses ChatGPT-generated Japanese hand-drawn illustrations with a Doraemon collaboration motif. Explanatory text remains in HTML and Markdown so it stays accurate, searchable, translatable, and accessible.

Doraemon is a third-party fictional character. This independent open-source project is not affiliated with or endorsed by the character’s rights holders.

## Author

Built by **Anita** from real long-running Codex workflows across research, data analysis, teaching, writing, and agentic engineering.

## License

Code is released under the [MIT License](LICENSE). Third-party character rights are not granted by this repository’s MIT license.
