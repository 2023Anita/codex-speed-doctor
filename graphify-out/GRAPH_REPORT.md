# Graph Report - .  (2026-05-15)

## Corpus Check
- 3 files · ~232,546 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 36 nodes · 70 edges · 8 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `collect_report()` - 9 edges
2. `summarize_sessions()` - 7 edges
3. `summarize_plugins_and_skills()` - 7 edges
4. `summarize_logs()` - 6 edges
5. `redact_report()` - 5 edges
6. `main()` - 5 edges
7. `make_state_db()` - 4 edges
8. `CliTests` - 4 edges
9. `mb()` - 4 edges
10. `summarize_processes()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `collect_report()` --calls--> `Report`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 3 → community 1_
- `summarize_logs()` --calls--> `mb()`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 5 → community 4_
- `summarize_plugins_and_skills()` --calls--> `mb()`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 5 → community 2_
- `summarize_sessions()` --calls--> `open_sqlite_readonly()`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 4 → community 3_
- `collect_report()` --calls--> `summarize_logs()`  [EXTRACTED]
  src/codex_speed_doctor/cli.py → src/codex_speed_doctor/cli.py  _Bridges community 4 → community 1_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.48
Nodes (3): CliTests, make_logs_db(), make_state_db()

### Community 1 - "Community 1"
Cohesion: 0.29
Nodes (7): build_recommendations(), collect_report(), ModelCacheSummary, parse_int(), ProcessSummary, summarize_model_cache(), summarize_processes()

### Community 2 - "Community 2"
Cohesion: 0.6
Nodes (5): count_dirs(), count_skill_files(), PluginSkillSummary, size_bytes(), summarize_plugins_and_skills()

### Community 3 - "Community 3"
Cohesion: 0.4
Nodes (6): gb(), PathSize, redact_report(), Report, SessionSummary, summarize_sessions()

### Community 4 - "Community 4"
Cohesion: 0.5
Nodes (4): LogSummary, open_sqlite_readonly(), query_one(), summarize_logs()

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (3): format_mapping(), mb(), render_text()

### Community 6 - "Community 6"
Cohesion: 1.0
Nodes (2): main(), parse_args()

### Community 7 - "Community 7"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **Thin community `Community 6`** (2 nodes): `main()`, `parse_args()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 7`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `collect_report()` connect `Community 1` to `Community 2`, `Community 3`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `summarize_plugins_and_skills()` connect `Community 2` to `Community 1`, `Community 5`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `summarize_sessions()` connect `Community 3` to `Community 1`, `Community 2`, `Community 4`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._