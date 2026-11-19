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
