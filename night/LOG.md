# Round 17 log

2026-11-20 09:02 lead — Started round 17 (open improvement round, Claude Code lead). Wrote night/TASKS.md: T1–T4 worker evidence tasks on angles no earlier round covered (clone path with spaces/non-ASCII, timezone independence of exports, C-locale/ascii output encoding, config sweep on a new range). Next: three read-only red-team subagents (SPEC §04–§06 conformance of reward/contract; data ambiguity/solvability; observation-side leakage), findings → REVIEW.md Round 17 and tasks T5+. Assumption: deepseek still lacks an API key (r13–r16); lead takes T4 over after 1 h.
2026-11-20 09:08 lead — T98 rehearsed seed 2003. Four matches, 21 inspections, 0.958 return, closed policy saw [0.0]. Fresh reconcile micro-F1 1.000 dev and 0.752 hard. Script matches. Next: verify standalone exported task validation (T5).
2026-11-20 09:08 gemini1 — Completed T1 (Jury-environment robustness in non-ASCII / spaced path). Cloned branch night/2026-11-20-r17 into '/tmp/r17 жюри clone'. Ran all 3 commands with env -u AUDITENV_SECRET:
1. `env -u AUDITENV_SECRET uv run python -m auditenv.check`: exit 0, wall time 47.98s, last line: "ALL CHECKS PASSED in 47.9 s"
2. `env -u AUDITENV_SECRET uv run python -m auditenv.demo`: exit 0, wall time 0.15s, last line: "Done. Full check: uv run python -m auditenv.check"
3. `env -u AUDITENV_SECRET uv run python -m auditenv.verify --dir episodes/dev`: exit 0, wall time 0.09s, last line: "10/10 episodes valid; episodes with problems: 0"
Zero non-zero exits and zero tracebacks; all 385 tests and verifiers passed without issues in non-ASCII path with spaces. Removed clone directory. Next: check for further unchecked tasks tagged (gemini1).
