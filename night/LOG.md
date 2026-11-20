# Round 17 log

2026-11-20 09:02 lead — Started round 17 (open improvement round, Claude Code lead). Wrote night/TASKS.md: T1–T4 worker evidence tasks on angles no earlier round covered (clone path with spaces/non-ASCII, timezone independence of exports, C-locale/ascii output encoding, config sweep on a new range). Next: three read-only red-team subagents (SPEC §04–§06 conformance of reward/contract; data ambiguity/solvability; observation-side leakage), findings → REVIEW.md Round 17 and tasks T5+. Assumption: deepseek still lacks an API key (r13–r16); lead takes T4 over after 1 h.
2026-11-20 09:08 lead — T98 rehearsed seed 2003. Four matches, 21 inspections, 0.958 return, closed policy saw [0.0]. Fresh reconcile micro-F1 1.000 dev and 0.752 hard. Script matches. Next: verify standalone exported task validation (T5).
2026-11-20 09:08 gemini3 — T3. Locale / output-encoding robustness, evidence only (9 runs):
1. `env -u AUDITENV_SECRET LC_ALL=C LANG=C uv run python -m auditenv.demo`: exit code 0, last line: `Done. Full check: uv run python -m auditenv.check`
2. `env -u AUDITENV_SECRET PYTHONIOENCODING=ascii uv run python -m auditenv.demo`: exit code 0, last line: `Done. Full check: uv run python -m auditenv.check`
3. `env -u AUDITENV_SECRET PYTHONUTF8=0 LC_ALL=C uv run python -m auditenv.demo`: exit code 0, last line: `Done. Full check: uv run python -m auditenv.check`
4. `env -u AUDITENV_SECRET LC_ALL=C LANG=C uv run python -m auditenv.verify --seeds 0-9`: exit code 0, last line: `30/30 episodes valid; episodes with problems: 0`
5. `env -u AUDITENV_SECRET PYTHONIOENCODING=ascii uv run python -m auditenv.verify --seeds 0-9`: exit code 0, last line: `30/30 episodes valid; episodes with problems: 0`
6. `env -u AUDITENV_SECRET PYTHONUTF8=0 LC_ALL=C uv run python -m auditenv.verify --seeds 0-9`: exit code 0, last line: `30/30 episodes valid; episodes with problems: 0`
7. `env -u AUDITENV_SECRET LC_ALL=C LANG=C uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json`: exit code 0, last line: `| Total | 103 |`
8. `env -u AUDITENV_SECRET PYTHONIOENCODING=ascii uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json`: exit code 0, last line: `| Total | 103 |`
9. `env -u AUDITENV_SECRET PYTHONUTF8=0 LC_ALL=C uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json`: exit code 0, last line: `| Total | 103 |`
No UnicodeEncodeError or traceback occurred across any run. All 9 runs completed with exit code 0. Assumption: evidence only, no code changes required. What's next: check for remaining (gemini3) tasks, else IDLE.
