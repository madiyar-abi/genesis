2026-11-22 05:00 lead — Round 22 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/CASE_UPDATES/r20–r21 archive. Baseline check at 774570d: exit 0, 50.6 s. Decision: fix the round-21 refund FX artefact at the root (refund Dr 2900 at the rate of the receipt it returns, difference to 7900). Reason: every jury clean episode D01–D05 is generated with ensure_distractors and so contains a refund; a foreign one leaves the customer's 2900 below zero in base currency, which a jury "accounting equalities" check on clean books can fail (up to 5 × 1.25 points). Round 21 deferred it only for time; ~13 h remain and the change follows the round-20 re-export path. Rounding residue on AR (a few minor units) stays documented. Wrote TASKS.md: codex1 clean-room D-matrix + ledger_identity/text_auditor after FIX; codex2 clean-room paired transform + policy_text/chronology update + rule-ambiguity review; rb jury_run/scenarios; gemini sweeps gated on the FIX commit.

2026-11-22 05:06 codex2 — Y1 complete on baseline 8cf7071. Ran `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r22.paired_cleanroom` (exit 0, 58.52 s). Used public deterministic generation for reproducible seeds 55000–55009 in both difficulties. Ran the required 5/5/10 matrix and also combined shuffle + rename for D01–D10 to satisfy the task's combined-transform instruction. Each original policy trace was replayed, copied tables and oracle evidence documents were retrieved through the adapter, and closed and offline grades were compared at equal inspection cost. The table shows mean scores and exact episode-level agreement across all seven score fields. Oracle F1 was 1.0000 throughout.

| Scenario | Reconcile original F1 / return | Combined copy F1 / return | Oracle original → copy | Combined equal | Matrix equal |
|---|---:|---:|---:|---:|---:|
| D01 | 1.0000 / 0.9400 | 1.0000 / 0.9400 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D02 | 1.0000 / 0.9400 | 1.0000 / 0.9400 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D03 | 1.0000 / 0.9400 | 1.0000 / 0.9400 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D04 | 1.0000 / 0.9400 | 1.0000 / 0.9400 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D05 | 1.0000 / 0.9400 | 1.0000 / 0.9400 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D06 | 1.0000 / 0.9373 | 1.0000 / 0.9373 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D07 | 1.0000 / 0.9373 | 1.0000 / 0.9373 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D08 | 1.0000 / 0.9373 | 1.0000 / 0.9373 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D09 | 1.0000 / 0.9418 | 1.0000 / 0.9418 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D10 | 1.0000 / 0.9398 | 1.0000 / 0.9398 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D11 | 1.0000 / 0.9390 | 1.0000 / 0.9390 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D12 | 1.0000 / 0.9402 | 1.0000 / 0.9402 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D13 | 1.0000 / 0.9402 | 1.0000 / 0.9402 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D14 | 1.0000 / 0.9394 | 1.0000 / 0.9394 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D15 | 1.0000 / 0.9394 | 1.0000 / 0.9394 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D16 | 1.0000 / 0.9396 | 1.0000 / 0.9396 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D17 | 1.0000 / 0.9396 | 1.0000 / 0.9396 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D18 | 1.0000 / 0.9396 | 1.0000 / 0.9396 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D19 | 1.0000 / 0.9402 | 1.0000 / 0.9402 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D20 | 1.0000 / 0.9402 | 1.0000 / 0.9402 | 1.0000 → 1.0000 | 20/20 | 20/20 |

Free-text locations searched: fx.csv.date, fx.csv.rate, fx.csv.source_currency, fx.csv.target_currency, invoices.jsonl.currency, invoices.jsonl.due_at, invoices.jsonl.issued_at, invoices.jsonl.line_items[].description, ledger.csv.account, ledger.csv.credit_minor, ledger.csv.currency, ledger.csv.debit_minor, ledger.csv.timestamp, manifest.json.base_currency, manifest.json.generator_version, manifest.json.period_end, manifest.json.period_start, manifest.json.rounding, manifest.json.schema_version, manifest.json.timezone, payments.jsonl.currency, payments.jsonl.timestamp, policy.json.base_currency, policy.json.findings.affected_ids.duplicate_invoice, policy.json.findings.affected_ids.fx_error, policy.json.findings.affected_ids.payment_allocation, policy.json.findings.affected_ids.period_cutoff, policy.json.findings.amount, policy.json.findings.evidence, policy.json.findings.tolerance, policy.json.fx.conversion, policy.json.fx.direction, policy.json.fx.rate_date, policy.json.ledger.accounts.1000, policy.json.ledger.accounts.1200, policy.json.ledger.accounts.2900, policy.json.ledger.accounts.4000, policy.json.ledger.accounts.6100, policy.json.ledger.accounts.6200, policy.json.ledger.accounts.6300, policy.json.ledger.accounts.6400, policy.json.ledger.accounts.7900, policy.json.ledger.credit_note, policy.json.ledger.currency, policy.json.ledger.expense, policy.json.ledger.invoice, policy.json.ledger.payment, policy.json.period.end, policy.json.period.rule, policy.json.period.start, policy.json.rounding, policy.json.timezone, task.txt
Embedded IDs: none found
Discrepancies: 0

A smoke check exercised embedded replacements, a longer ID sharing a prefix, and distinct structured namespaces sharing a spelling. Harness-only errors corrected during development: `AssertionError: Same-action original replay changed observable transitions` (snapshot before the policy can mutate its observation) and `KeyError: 'document'` (adapter returns the document directly). Full gate `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.check`: exit 0, 563 tests, 69.52 s, `ALL CHECKS PASSED in 69.5 s`. Next: Y2 and Y3 once the lead publishes FIX.
