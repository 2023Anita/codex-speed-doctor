# Contributing

Thank you for helping improve Codex Speed Doctor. The project favors small,
evidence-backed changes that preserve its read-only-first safety model.

## Before opening a pull request

1. Keep diagnosis read-only by default.
2. Put every mutation behind explicit user confirmation.
3. Treat Codex session and SQLite state as sensitive local metadata.
4. Add a failing regression test before changing behavior.
5. Avoid automatic deletion, live SQLite mutation, credential access, or remote
   diagnostic uploads.

## Local verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  python3 -m unittest discover -s tests -v

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  python3 -m codex_speed_doctor.cli --json --log-growth-seconds 0
```

## Pull request scope

- Keep one pull request focused on one behavior or documentation outcome.
- Explain the observed problem, the safety boundary, and the verification used.
- Never include real session content, local private paths, credentials, tokens,
  cookies, or private diagnostic logs in fixtures or screenshots.
- Update README, safety documentation, Roadmap, and Pages copy when public
  behavior changes.

## Visual contributions

Generated images must not contain private paths, credentials, real session
names, or essential text. Keep explanatory copy in Markdown or HTML so it
remains accessible and translatable.
