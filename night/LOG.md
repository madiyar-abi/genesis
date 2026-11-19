# LOG — night/2026-11-19 (append-only)

## 2026-11-19 13:39 — lead
- Read SPEC.md. Wrote docs/CONTRACT.md (all interfaces: tables, errors, env API, findings, matcher, policies) and night/TASKS.md (T1–T22; codex: T2 T4 T11 T18; gemini: T3 T12 T16).
- T1 done: pyproject (uv, py3.11, zero deps, package=false), auditenv/, tests/, LICENSE (MIT), uv.lock.
- Assumptions: package name `auditenv`; stdlib only, tests via unittest (no pytest dep);
  ledger kept in base currency only; all truth amounts = ledger misstatement in base currency;
  invoice_refs carry explicit per-invoice amounts (remittance advice); evidence ids = doc_id / row_id;
  run deadline for this session 2026-11-20 09:00 (from the prompt, overrides NIGHT.md 07:00 default).
- Next: T5 generator (lead).

## 2026-11-19 13:40 — codex
- T2 done: bounded decimal calculator. Targeted and full unittest runs passed.
- Assumptions: whitespace may surround expressions; unary signs preserve literal digits, and binary operations use precision 28.
- Next: T4 metrics.

## 2026-11-19 13:41 — codex
- T4 done: P/R/F1 and six-place terminal reward. Ten targeted tests and the full suite passed.
- Next: T11 once lead marks T7 done. T18 is independent.

## 2026-11-19 13:41 — codex
- T18 done: Python 3.11 slim Dockerfile and build-context exclusions. Task grep checks and full unittest suite passed.
- Assumptions: T18 can proceed while T11 waits for T7. The image runs the stdlib check entry point directly. Docker execution deferred because Docker is unavailable locally and T17 owns the check module.
- Next: T11 after T7 is checked on the lead branch, with integrated acceptance once the T13 runner is available.

## 2026-11-19 13:41 — gemini
- T3 done: auditenv/schema.py (validate_findings, normalize_finding) + tests/test_schema.py (42 tests, all pass).
- Constants: ISSUE_TYPES (4 types), MAX_FINDINGS=30, MAX_EVIDENCE=10, MAX_EXPLANATION=1000, MAX_AFFECTED=10.
- Assumption: affected_ids containing non-string integers are rejected (spec says non-empty strings).
- Next: T12 (after T8) or T16 (after T9) — both blocked; will IDLE until dependencies met.

## 2026-11-19 13:46 — lead
- Merged codex (T2 calculator, T4 metrics, T18 Dockerfile) and gemini (T3 schema); reviewed, 56 tests pass. Added scripts/resolve_notes.py (auto-resolves TASKS/LOG conflicts per NIGHT.md rule).
- T5 done: auditenv/money.py, generator.py (hidden history → correct ledger → render with random id styles/order), inject.py (all 4 types + I1/I2 already, ahead of T8/T9), tests/test_generator.py (7 tests over 40 seeds).
- Unblocked T11/T12 to start before T7 (pure-function part testable on generate()).
- Assumptions: expense journals carry no ids (schema has no journal id) → grouped by timestamp in checks;
  period window for documents = prior 35 days .. next 7 days; FX table covers period −60 .. +15 days, only foreign→base pairs.
- Next: T6 matcher, T7 env (lead).

## 2026-11-19 13:48 — codex
- T11 done: RandomExplorer and FlagAll. Five seeds each via run_episode produced repeatable trajectories and negative mean FlagAll reward. Targeted tests and full available suite passed.
- Assumptions: policies reserve the final available step for submit; FlagAll keeps paging after reaching the findings cap, uses base currency at a naive 1:1, and takes absolute payment amounts to satisfy the nonnegative claim schema.
- Next: rerun the full suite after the lead publishes T7 tests. No other codex tasks are open.

## 2026-11-19 13:50 — lead
- T6/T7 code in (matcher.py, env.py) + oracle + run.py; end-to-end oracle = 1.0. Tests for T6/T7 and T15 being written by subagents.
- T8/T9/T10 done: transform.py (relabel all ids, permute rows; truth/provenance remapped), verify.py (independent verifier:
  revert provenance → zero discrepancies; post-injection discrepancies recomputed from records == truth; evidence coverage).
  `uv run python -m auditenv.verify --seeds 0-199` → 0 problems on 600 episodes.
- Bug found by the verifier and fixed: retainer labels used ISO week → two invoices could get the same label (false duplicate in clean books). Now labelled by service-week dates.
- Fix: duplicate copy is always issued strictly after the original; truth amount = later copy's AR debit (documented in policy + CONTRACT).
- Next: T13 tests, T14 server, T17 check command.

## 2026-11-19 13:52 — lead
- T6/T7/T13/T14/T15 done. Subagent-written tests reviewed: tests/test_matcher.py (33), tests/test_env.py (30),
  tests/test_reward_attacks.py (12, all SPEC §05 properties over 12 seeds); plus tests/test_run.py, tests/test_server.py.
  Full suite: 150 tests OK in ~4 s.
- T14: auditenv/server.py (JSON-lines stdio; --episodes hidden list → client seeds ignored; --grader-log JSONL) + client.py (RemoteEnv).
- Env config validation tightened (bool max_steps, time_limit_s type). CONTRACT updated (error codes time_limit/invalid_findings, get_document kind, scenario key).
- Known design limit (for DESIGN.md): with 12 issues, missing one finding at 0 steps (0.913) beats full answer after 60 steps (0.88) — step cost vs F1 granularity.
- Next: merge workers, T17 check command.

## 2026-11-19 13:54 — lead
- Merged codex T11 (random explorer, flag-all). Reviewed: observation-only, deterministic per seed.
- T17 done: auditenv/check.py + Makefile. `uv run python -m auditenv.check` → ALL CHECKS PASSED (~6 s):
  tests, verifier (200 episodes), baselines on dev (micro P/R/F1), 20 paired checks, out-of-process eval.
- run.py: --config now reads the per-episode format `{episodes:[{seed, config}]}` (T16 spec updated accordingly).
- Assumption: check uses a built-in fallback dev list until configs/dev.json exists.
- Next: T19–T22 docs; merge gemini T12/T16 and codex T23 when pushed.

## 2026-11-19 13:55 — gemini
- T12 done: auditenv/policies/reconcile.py (reconcile_findings, Reconcile policy) + tests/test_reconcile.py (all pass).
- Reconcile baseline: pages ledger, invoices, payments, fx (max 50 rows/page); fetches line_items for duplicate candidates via get_document; rule-based detection for duplicate_invoice, period_cutoff, fx_error, payment_allocation.
- Results on dev seeds 2000–2009: Mean F1 = 1.000, 0 error steps (0.00%), ~22 steps/episode.
- Next: T16 episode export (after T9).

## 2026-11-19 13:55 — codex
- T23 done: grader-side Markdown and JSON failure analysis. Oracle recalls every tested type and scenario with zero FPs; FlagAll records FPs. T7 environment and T11 baseline tests also passed.
- Assumptions: recall is zero for groups with no issues, means are per episode, steps include submit, and explicit seeds must exist in the supplied config. Reconcile verification awaits T12.
- Next: no open codex tasks.

## 2026-11-19 13:56 — lead
- Merged gemini T12 (Reconcile: obs-only, pages all tables + get_document for duplicate candidates) and codex T23 (analyze.py).
  Check: reconcile micro-F1 1.000, return 0.956, 22.8 steps on dev — the books are solvable within budget from the records alone.
- Added T26 (codex) NaiveReconcile to measure that distractors/timezones trip naive rules (honest difficulty evidence).
- Next: T19 design note with measured numbers, T21/T22.
## 2026-11-19 13:56 — codex
- T24 done: six Draft 2020-12 JSON Schemas with stdlib smoke checks against generated manifests, truth and real environment trajectories. Full suite passed.
- Assumptions: action schemas describe intended valid inputs; list cursor and limit are optional as in the environment, and the manifest includes the optional generator version. Episode-ID equality is enforced by the grader.
- Next: T25 experimental reward.

## 2026-11-19 13:56 — lead
- Merged gemini T12 (Reconcile: obs-only, pages all tables + get_document for duplicate candidates) and codex T23 (analyze.py).
  Check: reconcile micro-F1 1.000, return 0.956, 22.8 steps on dev — the books are solvable within budget from the records alone.
- Added T26 (codex) NaiveReconcile to measure that distractors/timezones trip naive rules (honest difficulty evidence).
- Next: T19 design note with measured numbers, T21/T22.

## 2026-11-19 13:57 — codex
- T25 done: amount-weighted experimental terminal reward. Five targeted tests and full suite passed.
- Assumptions: use the shared invalid-submission penalty and reward rounding. A zero weighted denominator receives F1=1 only when truth and findings are both empty.
- Next: no open codex tasks.

## 2026-11-19 13:59 — lead
- Merged codex T24 (schemas/*.json + test) and T25 (experimental.py). Experimental materiality-weighted reward now computed grader-side in env._finish (grader log + check column "exp_ret"); shared reward untouched, never shown to policies.
- Generator config validation: n_invoices ∈ [10,100] (documents stay ≤ 200; 120+ could exceed), error counts non-negative ints, unknown types rejected.
- Reconcile stress test: 1200 episodes (300 seeds × 4 configs) → 0 imperfect, max 32 steps → truth always findable from records.
- Docs: README (T20 draft), DESIGN.md draft (T19; results placeholders until T16/T26).
- Next: DEMO.md, PITCH.md drafts; merge T16/T26.
## 2026-11-19 13:58 — codex
- T26 done: NaiveReconcile uses only table listings. Seeds 2000–2009: FPs on 10/10 clean distractor episodes, mean dirty F1 0.431414 vs Reconcile 1.000000 (one error of each type plus I1 and I2). Determinism and full suite passed.
- Assumptions: skip FX checks if the written-date rate is absent; flag later equal-total bookings against the first; cap findings at 30. The policy is available directly through run_episode.
- Also verified T23 with Reconcile after T12 landed. Next: no open codex tasks.

## 2026-11-19 14:00 — lead
- Merged codex T26 (NaiveReconcile): dev micro-F1 0.195 vs Reconcile 1.000; I1 recall 0.0 — distractors/timezones defeat naive rules.
- auditenv/demo.py (narrated 5-section demo) + docs/DEMO.md (T21 draft) + docs/PITCH.md (T22 draft). Numbers from check/analyze output.
- Added T27 (lead) trajectories after T16.
- Next: wait for gemini T16 (export/configs), then refresh numbers in DESIGN/PITCH/DEMO, final SPEC pass.
## 2026-11-19 14:00 — gemini
- T16 done: auditenv/export.py, configs/train.json (1000–1009), configs/dev.json (2000–2009), configs/eval_example.json (9000–9019, 5 clean, 5 interacting, 10 mixed), episodes/train, episodes/dev, tests/test_export.py.
- Export format: public/{manifest.json,ledger.csv,invoices.jsonl,payments.jsonl,fx.csv,policy.json}, grader/{truth.json,provenance.json}, index.json.
- Verified: export twice is byte-identical; all 40 episodes pass independent verifier; tests/test_export passes; auditenv.check passes all gates.
- All assigned gemini tasks (T3, T12, T16) complete.

## 2026-11-19 14:02 — lead
- Merged gemini T16: configs/{train,dev,eval_example}.json (config_version 1.0), auditenv/export.py, episodes/{train,dev} (10+10, 1.8 MB). Check uses configs/dev.json now: reconcile F1 1.000 / return 0.958; naive F1 0.325; random −0.614; flag-all −1.000; oracle 1.000.
- T27 done: trajectories/train_{reconcile,random,naive_reconcile}.jsonl (train split, mode train, 3.6 MB) + tests/test_trajectory_files.py.

## 2026-11-19 14:05 — codex
- T29 blocked: added the seeded 40-episode step contract fuzz test. The test exercised more than 3,000 actions in 0.121 s, then reported these uncaught input-validation errors.
- Episode 0, step 17: {"type":"get_record","table":{"a":{"b":1}},"id":{"a":{"b":1}}} raises TypeError (unhashable dict). Episode 0, step 22: {"type":"get_record","table":[],"id":[]} raises TypeError (unhashable list).
- Episode 6, step 54: {"type":"list_records","table":"ledger","cursor":"ledger:²","limit":200} raises ValueError because the digit test accepts a character that integer parsing rejects.
- Assumptions: use train and eval in alternation, keeping random submits near the end so the run reaches its action minimum. As assigned, the lead owns fixes in env.py. Re-run `uv run python -m unittest tests.test_fuzz` after those fixes.
