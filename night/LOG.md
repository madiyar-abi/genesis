# LOG — night/2026-11-19 (append-only)

## 2026-11-19 13:39 — lead
- Read SPEC.md. Wrote docs/CONTRACT.md (all interfaces: tables, errors, env API, findings, matcher, policies) and night/TASKS.md (T1–T22; codex: T2 T4 T11 T18; gemini: T3 T12 T16).
- T1 done: pyproject (uv, py3.11, zero deps, package=false), auditenv/, tests/, LICENSE (MIT), uv.lock.
- Assumptions: package name `auditenv`; stdlib only, tests via unittest (no pytest dep);
  ledger kept in base currency only; all truth amounts = ledger misstatement in base currency;
  invoice_refs carry explicit per-invoice amounts (remittance advice); evidence ids = doc_id / row_id;
  run deadline for this session 2026-11-20 09:00 (from the prompt, overrides NIGHT.md 07:00 default).
- Next: T5 generator (lead).

## 2026-11-19 13:41 — gemini
- T3 done: auditenv/schema.py (validate_findings, normalize_finding) + tests/test_schema.py (42 tests, all pass).
- Constants: ISSUE_TYPES (4 types), MAX_FINDINGS=30, MAX_EVIDENCE=10, MAX_EXPLANATION=1000, MAX_AFFECTED=10.
- Assumption: affected_ids containing non-string integers are rejected (spec says non-empty strings).
- Next: T12 (after T8) or T16 (after T9) — both blocked; will IDLE until dependencies met.
