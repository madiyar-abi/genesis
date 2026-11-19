# LOG — round 2 (append-only)

## 2026-11-19 20:48 lead
- Started round 2 on night/2026-11-19-r2 (deadline per prompt: 2026-11-20 12:00). Wrote night/TASKS.md from
  night/ROUND2.md. Workers: codex → R2, C3, E3a; gemini → C2, P1, E2. Lead: P2, D4, D2, R3, H2, E3b, E4, H1, E5, J1, J2.
- Assumption: the prompt's deadline (2026-11-20 12:00) overrides NIGHT.md's default 07:00 for this run.
- Assumption: E2 bench output is pasted into DESIGN by the lead (docs stay lead-owned to avoid conflicts).

## 2026-11-19 20:50 lead
- P2 done: `run_paired(n, hard=True)` in auditenv/check.py (seeds 6000+, difficulty hard, replay with
  reconcile_hard + random, transform keeps oracle/reconcile_hard reward); new test in tests/test_hard.py.
  Transform already shuffles FX rows (transform.py) — no change needed. check exit 0 (20.1 s), sync_docs --check ok.
- Dispatched subagents: D4 shortcut miner, E4 SVG chart.

## 2026-11-19 20:51 lead
- E4 done (subagent, reviewed: rendered PNG, no overlaps): scripts/chart.py → docs/baselines.svg from check --json,
  tests/test_chart.py; linked from PITCH slide 7. Episode counts read from configs/*.json (not in metrics JSON).

## 2026-11-19 20:52 lead
- H2 done: per-config steps over 300 seeds (stress configs from auditenv/fuzz.py): default reconcile max 33,
  hard reconcile_hard max 58 (12 issues + 100 invoices), 0 imperfect, 0 truncated → ≤ 80 holds. Table in DESIGN §9.
- Dispatched subagents: R3 sensitivity (scripts/sensitivity.py), E3b hard trajectories + CI badge.

- 2026-11-19 20:55 codex — R2: all 15 isolated single-line mutants killed by the existing reward tests; the unmodified baseline, smoke tests, full check and 3,000-episode sweep passed. Used existing regression coverage because no mutant survived. Next: C3.

## 2026-11-19 20:56 codex
- C3 done. Fake-clock tests cover 59.9 s, exactly 60 s, late submit, empty-answer grade, post-terminal calls, a custom limit and eval isolation. Preserved the existing strict greater-than comparison. Targeted tests, full check (264 tests) and 3,000-episode sweep passed. Next: E3a.
