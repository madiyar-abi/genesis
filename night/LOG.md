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

## 2026-11-19 21:42 lead
- D4 done. Hard-mode leak fixed in the generator: State.retype (moved from inject._retype) now also keys in by hand
  12 % of ordinary invoices and 50 % of credit-note re-issues (hard mode only; default RNG path untouched — the 60
  default golden hashes and episodes/train|dev are byte-identical). Miner hard: duplicate max precision 1.000 → 0.467.
  Re-exported episodes/hard (verify 20/20), regenerated trajectories/train_hard_*, golden hashes, chart.
- Effect: plain reconcile on hard F1 0.611 → 0.752 (gate ≤ 0.8 still passes) because half the re-issue traps are
  now re-typed and the exact-match script skips them. Kept: re-typing re-issues is needed, otherwise
  "re-typed + has a twin ⇒ duplicate" stays a 2-feature shortcut. Prose numbers updated in README/DESIGN/PITCH.
- Decision (not asking): default-mode miner signals (entity+currency+total pair 0.996, last-day 2900/7900 → fx 0.70,
  large 2900 → allocation 0.75–0.78) documented in DESIGN §10 instead of fixed — fixing them regenerates all default
  data and doc numbers for little gain (each hint names a record, the amount still needs reconciling).
- tests/test_hardening seed-7 test now derives row ids from truth (hard ids moved), default ids still asserted.

## 2026-11-19 21:44 codex
- M1 done: raw non-null ID values are listed once per table, feature and value in Markdown and JSON, outside the precision rankings and flags. Null stays eligible as a missing-reference signal, and identifier shapes and suffixes stay eligible. Added miner, bench, sensitivity and chart Makefile targets. Targeted tests (3) and make dry run passed. Seeds 0–199 covered 400 episodes, with 9,718 excluded values and no entity_id flags. Official check passed (277 tests and all gates); fuzz passed (3,000 episodes, zero problems). Next: idle unless the lead adds another codex task.

## 2026-11-19 21:46 lead
- J1/J2 refreshed for round 2: DEMO (276 tests, hard paired checks, F1 0.75 in hard mode, optional mutation-test
  step, wrap-up mentions miner + sensitivity), PITCH slides 6 and 8 (mutants, sensitivity, golden hashes, hard
  paired, stress max 57, miner). Numbers re-checked: demo rewards unchanged, fuzz 0-999 3 000 episodes 0 problems,
  mutate 15/15, verify train/dev/hard dirs valid. Will re-check once more before DONE.
- Dispatched an independent jury-style review subagent (read-only) against SPEC §09/§10.

## 2026-11-19 21:46 lead
- Merged codex M1 (reviewed). Review fix: the excluded-identifier table printed every raw id value (2 661 lines for
  50 seeds); now lists only values with support >= min_support and prints the total count (215 lines).

## 2026-11-19 21:47 lead
- Decision: skip H1 (expert difficulty) and E5 (rule-search baseline), marked [!]. Reason: SPEC §10 scores
  correctness of env/grader, not difficulty ("Высокая награда oracle сама по себе не даёт баллов за сложность";
  "недоказанные улучшения обучения баллов не дают"); H1 would add a third generator path (high risk to the
  verified data), E5 could read as model training. Time goes to the jury-style review findings instead.

## 2026-11-19 21:56 lead
- Jury-style review (subagent) done; details in REVIEW.md "Round 2". Fixed R2-1 (stale duplicate evidence rule in the
  agent-facing policy text → -1 for a literal follower; re-exported train/dev/hard: exactly 40 policy.json files
  changed; trajectories + golden hashes regenerated; new PolicyTextTests) and R2-2 (check failed with
  AUDITENV_SECRET set; unit tests now run with the public key). check exit 0 (278 tests), secret check exit 0.
- Next: review defects 3–6 (unknown action params accepted, grading crash on non-str keys, loose reset input,
  stale README lines).

## 2026-11-19 22:00 lead
- Fixed review defects 3–6 (REVIEW.md R2-3..R2-6): unknown action params → bad_params; validate_findings never
  raises; reset rejects non-int seeds / NaN-inf time limits / non-bool distractors / non-int transform_seed, server no
  longer int()-coerces seeds; README/CONTRACT/load.py doc fixes; test counts 282 everywhere. New
  tests/test_contract_strict.py. check exit 0 (282 tests), golden unchanged, sync_docs ok.
- Assumption: rejecting time_limit_s=inf is fine (the case fixes a 60 s limit; nobody needs to disable it).

## 2026-11-19 22:01 lead
- Final SPEC pass found a conflict in my R2-3 fix: SPEC §04 "submit завершает эпизод" — a submit with extra action
  keys was a non-terminating bad_params. Now it terminates as an invalid submission (−1, reason kept, logged).
  Test added; CONTRACT/REVIEW updated; test counts 283. check exit 0.

## 2026-11-19 22:24 gemini
- Implemented G1: created `docs/CHECKS.md` mapping all 5 jury criteria from `night/SPEC.md` §10 (Contract and Isolation 25, Data and Ground Truth 25, Reward Reliability 25, Reproducibility and Generalization 15, Engineering and Explanation 10) to code locations, verification commands, and measured pass counts from execution.
- Verified that all commands in `docs/CHECKS.md` pass with exit code 0 (`auditenv.check`, `auditenv.verify --seeds 0-199`, `scripts/mutate_reward.py`, `scripts/golden.py --check`, `auditenv.attack`, `tests.test_fuzz`, etc.).
- Verified that all 76 file and test method references exist in the repository via automated validation.
- Next: check if any remaining tasks are tagged (gemini).
