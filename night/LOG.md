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

## 2026-11-19 20:57 gemini
- C2 done: bounded request size and bad bytes in auditenv/server.py (MAX_LINE = 1 << 20, read stdin as bytes via sys.stdin.buffer, strict UTF-8 decoding, keep serving after error). Added tests in tests/test_server.py: in-process serve() with BytesIO / StringIO and subprocess test sending 10 MB line, invalid UTF-8, then valid reset and clean close. Tests green, check exit 0.
- Next: P1 golden hashes (scripts/golden.py, tests/golden_hashes.json, tests/test_golden.py).

## 2026-11-19 21:00 gemini
- P1 done: scripts/golden.py generates 80 canonical hashes across seeds 0–19 × 4 configs, writes tests/golden_hashes.json, and supports --check to exit 1 on drift. tests/test_golden.py recomputes all 80 hashes in 0.4s and asserts equality with actionable guidance on intentional drift. scripts/golden.py --check exits 0.
- Next: E2 timing benchmark (scripts/bench.py, tests/test_bench.py).

## 2026-11-19 21:04 gemini
- E2 done: scripts/bench.py measures wall time (perf_counter, median of 3) for generate() (0.24s default / 0.85s hard for 100 seeds), verify (1.45s for 300 eps), and full episodes per policy on dev and hard. Prints Python version, platform, and formatted markdown table; supports --json for metrics export. tests/test_bench.py smoke tests function API and CLI smoke test in 2.7s.
- Next: Check TASKS.md for remaining gemini tasks.
