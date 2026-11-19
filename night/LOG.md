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
## 2026-11-19 13:48 — codex
- T11 done: RandomExplorer and FlagAll. Five seeds each via run_episode produced repeatable trajectories and negative mean FlagAll reward. Targeted tests and full available suite passed.
- Assumptions: policies reserve the final available step for submit; FlagAll keeps paging after reaching the findings cap, uses base currency at a naive 1:1, and takes absolute payment amounts to satisfy the nonnegative claim schema.
- Next: rerun the full suite after the lead publishes T7 tests. No other codex tasks are open.
