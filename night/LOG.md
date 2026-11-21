# Round 18 log

2026-11-21 21:42 lead (Claude) — Round 18 started (open improvement round, freeze 2026-11-22 18:00). No TASKS.md existed, so this is the first lead of the round. Wrote night/TASKS.md: 3 tasks per worker (gemini1a–3b evidence sweeps/doc integrity on new seeds, codex1/codex2 red-team the four jury blocks with fixes, rb doc-consistency tests). Assumption: the memory note "red-team passes beat sweeps" (r16) → the strong workers get red-team tasks, the Gemini workers get evidence on new seed ranges. Next: lead review (T30) while the check runs.

2026-11-21 21:48 gemini1b — T4 stress solvability on seeds 5000–5299.
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 5000-5299`
  Exit code: 0
  Wall time: 22.21 s
  Summary: reconcile on 1200 default episodes (seeds 5000-5299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 32, truncated 0 (22.0 s)
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 5000-5299`
  Exit code: 0
  Wall time: 70.77 s
  Summary: reconcile_hard on 1200 hard episodes (seeds 5000-5299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 57, truncated 0 (70.7 s)
Result: 0 imperfect, 0 truncated across 2,400 episodes. Max steps: 32 (default), 57 (hard).
Next: T5 (jury_run on seed bases 7000, 8000, 9000).
