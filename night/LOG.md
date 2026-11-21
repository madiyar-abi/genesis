2026-11-22 00:21 lead — Round 20 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/r19 archive. Wrote TASKS.md: independent defect hunts (codex1 chronology/policy-text/adapter reality, codex2 fresh-clone + claims audits, rb scenario adapter runs), evidence sweeps on unseen seeds for gemini workers. Baseline check running. Assumption: generator fixes stay with lead (one re-export owner) to avoid conflicting exports.
2026-11-22 00:23 lead — D: demo --seed 2003 reproduces every DEMO.md number (326 rows, 69 invoices, 21 inspections, 0.958, 286 / 351331 minor units, 0.333, 22 actions). P: sync_docs tables match, but prose on slide 7 and DESIGN §9 was stale since 20 Nov: analyze --config configs/eval_hard.json gives reconcile 20 FP (not 22), duplicate recall 2/8 (not 3/8, six missed, not five), mean 43 actions (not 43.2). Fixed PITCH.md and DESIGN.md; sync_docs does not cover prose numbers.
2026-11-22 00:26 gemini1b — G4 complete (stress solvability on seeds 8000-8299).
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 8000-8299`
Exit code: 0, wall time: 7.33 s
Summary: `reconcile on 1200 default episodes (seeds 8000-8299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 34, truncated 0 (7.2 s)`
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 8000-8299`
Exit code: 0, wall time: 20.65 s
Summary: `reconcile_hard on 1200 hard episodes (seeds 8000-8299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 58, truncated 0 (20.6 s)`
2026-11-22 00:32 gemini1b — G5 complete (fuzz sweeps on seeds 11000-11999).
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 11000-11999`
Exit code: 0, wall time: 82.12 s
Summary:
default mode, seeds 11000-11999: 3000 episodes (1991 dirty, 1009 clean) in 82.1 s
  episodes with a problem (exception / verifier / oracle): 0
  random explorer reward > 0: 222/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
  flag-all reward < 0: 3000/3000
FUZZ PASSED
Problems: 0
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --seeds 11000-11999`
Exit code: 0, wall time: 214.53 s
Summary:
hard mode, seeds 11000-11999: 3000 episodes (1987 dirty, 1013 clean) in 214.5 s
  episodes with a problem (exception / verifier / oracle): 0
  random explorer reward > 0: 234/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
  flag-all reward < 0: 3000/3000
FUZZ PASSED
Problems: 0
