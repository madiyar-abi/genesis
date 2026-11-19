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

## 2026-11-19 20:57 codex
- E3a done. Makefile dry run confirms all five commands, including hard stress because the CLI supports it. make fuzz (3,000 episodes), make test (264 tests), and make stress (1,200 episodes per mode) passed. The golden target points to the script owned by P1; only its command was checked on this branch. Next: idle unless the lead adds a codex task.

## 2026-11-19 20:57 gemini
- C2 done: bounded request size and bad bytes in auditenv/server.py (MAX_LINE = 1 << 20, read stdin as bytes via sys.stdin.buffer, strict UTF-8 decoding, keep serving after error). Added tests in tests/test_server.py: in-process serve() with BytesIO / StringIO and subprocess test sending 10 MB line, invalid UTF-8, then valid reset and clean close. Tests green, check exit 0.
- Next: P1 golden hashes (scripts/golden.py, tests/golden_hashes.json, tests/test_golden.py).

## 2026-11-19 21:00 gemini
- P1 done: scripts/golden.py generates 80 canonical hashes across seeds 0–19 × 4 configs, writes tests/golden_hashes.json, and supports --check to exit 1 on drift. tests/test_golden.py recomputes all 80 hashes in 0.4s and asserts equality with actionable guidance on intentional drift. scripts/golden.py --check exits 0.
- Next: E2 timing benchmark (scripts/bench.py, tests/test_bench.py).

## 2026-11-19 21:04 gemini
- E2 done: scripts/bench.py measures wall time (perf_counter, median of 3) for generate() (0.24s default / 0.85s hard for 100 seeds), verify (1.45s for 300 eps), and full episodes per policy on dev and hard. Prints Python version, platform, and formatted markdown table; supports --json for metrics export. tests/test_bench.py smoke tests function API and CLI smoke test in 2.7s.
- Next: Check TASKS.md for remaining gemini tasks.

## 2026-11-19 21:33 lead
- Usage limit hit 20:53–21:30 (all three subagents paused, resumed after reset).
- D2 done: decision documented in DESIGN §7 — nothing-allocated evidence = payment doc + invoice doc + 2900 row
  (+ invoice-date FX); the missing AR credit is an absence, proven by the whole-ledger recomputation (verify step 3).
  Tightened verify._sufficient: for base-currency payments the 2900 credit must cover the whole referenced amount
  (no data change; verify 600/600, dev/train/hard dirs all valid). Test in tests/test_verify.py.

## 2026-11-19 21:33 lead
- E3b done (subagent, reviewed): configs/train_hard.json (seeds 1100–1109, disjoint from all splits),
  trajectories/train_hard_{random,naive_reconcile,reconcile,reconcile_hard}.jsonl (~10.5 MB), regenerate commands
  in README (reproduce byte-for-byte), test_trajectory_files covers them, CI badge at the top of README.
  Note: the D4 hard-mode leak fix will require regenerating these files.

## 2026-11-19 21:34 lead
- R3 done (subagent, reviewed): scripts/sensitivity.py re-grades each baseline episode with the real matcher, step
  cost 0.001/0.002/0.005 and tolerance 0/0.1%/1% patched in a context manager (default re-grade == env reward,
  asserted). Ranking unchanged on dev and hard. Table in DESIGN §6. Shared reward untouched.

## 2026-11-19 21:37 codex
- Synced the lead branch, preserving both sides of the log in chronological order. Official check passed (267 tests and all gates); fuzz passed (3,000 episodes, zero problems). R2, C3 and E3a remain complete. Next: idle until another codex task is assigned.
## 2026-11-19 21:37 lead
- Merged codex (R2, C3, E3a) and gemini (C2, P1, E2); reviewed diffs. LOG conflicts resolved keeping all entries
  in time order. Review fix on C2: `for line in inp` read a whole over-long line into memory before rejecting it;
  now `_lines()` reads with readline(MAX_LINE + 1) and drains the rest in bounded chunks (new test). check exit 0
  (276 tests, 23.7 s), golden 80/80, mutate 15/15 killed.
- D4 miner results (subagent): real hard-mode leak — re-typed description style (all caps / lower / "name - REF")
  only appears on duplicate copies (precision 1.000). Weaker default-mode signals: entity+currency+total pair
  (0.996, duplicate definition itself, no near-miss decoys in default), I1 always on the last day (fx_error 0.70),
  large 2900 amounts (0.745). Fixing the hard leak first (lead).

## 2026-11-19 21:37 lead
- C2/P1/E2 marked done after review. E2 timing table pasted into DESIGN §9 (scripts/bench.py output).
- Committed scripts/shortcut_miner.py + test (D4 still open: leak fixes next).

## 2026-11-19 21:44 codex
- M1 done: raw non-null ID values are listed once per table, feature and value in Markdown and JSON, outside the precision rankings and flags. Null stays eligible as a missing-reference signal, and identifier shapes and suffixes stay eligible. Added miner, bench, sensitivity and chart Makefile targets. Targeted tests (3) and make dry run passed. Seeds 0–199 covered 400 episodes, with 9,718 excluded values and no entity_id flags. Official check passed (277 tests and all gates); fuzz passed (3,000 episodes, zero problems). Next: idle unless the lead adds another codex task.
