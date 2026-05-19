# Graph Report - .  (2026-05-19)

## Corpus Check
- 6 files · ~234,442 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 62 nodes · 115 edges · 10 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `collect_report()` - 9 edges
2. `archive()` - 9 edges
3. `summarize_sessions()` - 7 edges
4. `summarize_plugins_and_skills()` - 7 edges
5. `defer()` - 6 edges
6. `summarize_logs()` - 6 edges
7. `make_archive_fixture()` - 5 edges
8. `redact_report()` - 5 edges
9. `main()` - 5 edges
10. `ArchiveTests` - 4 edges

## Surprising Connections (you probably didn't know these)
- `collect_report()` --calls--> `Report`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 5 → community 6_
- `summarize_logs()` --calls--> `mb()`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 1 → community 7_
- `summarize_sessions()` --calls--> `open_sqlite_readonly()`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 7 → community 5_
- `collect_report()` --calls--> `summarize_logs()`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 7 → community 6_
- `collect_report()` --calls--> `summarize_plugins_and_skills()`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 1 → community 6_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.4
Nodes (10): archive(), codex_processes_running(), main(), parse_args(), read_manifest(), sqlite_backup(), wait_for_codex_exit(), write_index() (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.42
Nodes (8): count_dirs(), count_skill_files(), format_mapping(), mb(), PluginSkillSummary, render_text(), size_bytes(), summarize_plugins_and_skills()

### Community 2 - "Community 2"
Cohesion: 0.46
Nodes (7): build_archive_command(), defer(), launch_with_launchctl(), launch_with_terminal(), main(), parse_args(), validate_manifest()

### Community 3 - "Community 3"
Cohesion: 0.48
Nodes (3): ArchiveTests, make_archive_fixture(), make_threads_db()

### Community 4 - "Community 4"
Cohesion: 0.48
Nodes (3): CliTests, make_logs_db(), make_state_db()

### Community 5 - "Community 5"
Cohesion: 0.4
Nodes (6): gb(), PathSize, redact_report(), Report, SessionSummary, summarize_sessions()

### Community 6 - "Community 6"
Cohesion: 0.33
Nodes (6): build_recommendations(), collect_report(), main(), ModelCacheSummary, parse_args(), summarize_model_cache()

### Community 7 - "Community 7"
Cohesion: 0.5
Nodes (4): LogSummary, open_sqlite_readonly(), query_one(), summarize_logs()

### Community 8 - "Community 8"
Cohesion: 0.67
Nodes (3): parse_int(), ProcessSummary, summarize_processes()

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **Thin community `Community 9`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `collect_report()` connect `Community 6` to `Community 8`, `Community 1`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Why does `summarize_plugins_and_skills()` connect `Community 1` to `Community 6`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._