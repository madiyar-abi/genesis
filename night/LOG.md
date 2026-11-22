2026-11-22 05:00 lead — Round 22 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/CASE_UPDATES/r20–r21 archive. Baseline check at 774570d: exit 0, 50.6 s. Decision: fix the round-21 refund FX artefact at the root (refund Dr 2900 at the rate of the receipt it returns, difference to 7900). Reason: every jury clean episode D01–D05 is generated with ensure_distractors and so contains a refund; a foreign one leaves the customer's 2900 below zero in base currency, which a jury "accounting equalities" check on clean books can fail (up to 5 × 1.25 points). Round 21 deferred it only for time; ~13 h remain and the change follows the round-20 re-export path. Rounding residue on AR (a few minor units) stays documented. Wrote TASKS.md: codex1 clean-room D-matrix + ledger_identity/text_auditor after FIX; codex2 clean-room paired transform + policy_text/chronology update + rule-ambiguity review; rb jury_run/scenarios; gemini sweeps gated on the FIX commit.
2026-11-22 05:12 lead — L1 FIX done. Regression first: tests.test_generator...test_refund_clears_the_unapplied_cash_it_returns (D03 config, seeds 0–39 × default/hard: each customer's 2900 balance in base currency never below 0, >10 foreign refunds, some with 7900) failed on the old code (e.g. -29596), passes now. Rule (CONTRACT §2, policy.json ledger.payment): a refund debits 2900 at the payment-date rate of the receipt it returns = the same customer's (ledger entity_id) latest earlier payment in that currency whose amount − Σ invoice_refs equals the refunded amount (refund-date rate if none); cash at the refund-date rate; difference 7900. generator.State.refunded_receipt + verify.Books.refunded_receipt implement it independently; old generator now fails verify --seeds 0-199 (266/600), new passes 600/600. RNG stream preserved: the realised-FX row takes the cash row's tie (no random draw) and the expense filler target excludes those rows — compared with the old generator on 660 episodes (15 seeds × default/hard/heavy/D01–D20 both difficulties): invoices, payments, fx, truth types/ids/amounts and every non-2900/7900 ledger row identical; only row ids after an inserted 7900 row renumber. Snapshot counts updated (+57/+68 payment rows on 100 heavy seeds = the new 7900 rows; seed-7 hardening row ids R390/R445 → R391/R446). Re-exported episodes, trajectories, golden (80). check exit 0 (51.4 s), sync_docs no drift (no measured number changed), fuzz 0-999 3000 eps + hard 0-199 600 eps PASSED. night/r21/ledger_identity --classify on 41000–41299: refund class (a) 0 (was 920), rounding (b) 415 unchanged, 1985 "other" = all its old-rule fx check on the new refund 7900 rows (codex1 X2 updates the checker). DESIGN §10/README/PITCH limitation text: refund artefact removed, rounding residue stays. DESIGN worked-example row ids re-checked on the new exports: unchanged.

2026-11-22 05:07 codex1 — X1 on 8cf7071. Ran `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r22.d_matrix > /tmp/r22-codex1/final.log 2> /tmp/r22-codex1/final.stderr` (exit 0, real 76.13 s). `8000 episodes; 0 failed per-episode checks`. The default private grader key is retained under /tmp/r22-codex1/key for local reproduction. The six clean checks apply to each of D01–D05, whose config repeats. Refunds match an earlier same-entity, same-currency unapplied receipt of the refunded amount and the ledger rule published by this pre-fix revision.

| Scenario | Requirement (episodes out of 400) |
|---|---|
| D01 | truth count/types: 400/400; legitimate equal totals: 400/400; correct split: 400/400; correct refund: 400/400; first day: 400/400; last day: 400/400 |
| D02 | truth count/types: 400/400; legitimate equal totals: 400/400; correct split: 400/400; correct refund: 400/400; first day: 400/400; last day: 400/400 |
| D03 | truth count/types: 400/400; legitimate equal totals: 400/400; correct split: 400/400; correct refund: 400/400; first day: 400/400; last day: 400/400 |
| D04 | truth count/types: 400/400; legitimate equal totals: 400/400; correct split: 400/400; correct refund: 400/400; first day: 400/400; last day: 400/400 |
| D05 | truth count/types: 400/400; legitimate equal totals: 400/400; correct split: 400/400; correct refund: 400/400; first day: 400/400; last day: 400/400 |
| D06 | truth count/types: 400/400; legitimate equal totals: 400/400; duplicate candidates have distinct invoice/document IDs: 400/400 |
| D07 | truth count/types: 400/400; legitimate equal totals: 400/400; duplicate candidates have distinct invoice/document IDs: 400/400 |
| D08 | truth count/types: 400/400; legitimate equal totals: 400/400; duplicate candidates have distinct invoice/document IDs: 400/400 |
| D09 | truth count/types: 400/400; one allocation shortfall: 400/400; missing allocation: 400/400 |
| D10 | truth count/types: 400/400; one allocation shortfall: 400/400; partial allocation: 400/400 |
| D11 | truth count/types: 400/400; one allocation shortfall: 400/400 |
| D12 | truth count/types: 400/400; one different-date published FX rate: 400/400 |
| D13 | truth count/types: 400/400; one different-date published FX rate: 400/400 |
| D14 | truth count/types: 400/400; one outside invoice booked inside company period: 400/400 |
| D15 | truth count/types: 400/400; one outside invoice booked inside company period: 400/400 |
| D16 | truth count/types: 400/400; one different-date published FX rate: 400/400; partial allocation and wrong FX on same period-end payment: 400/400 |
| D17 | truth count/types: 400/400; one different-date published FX rate: 400/400; partial allocation and wrong FX on same period-end payment: 400/400 |
| D18 | truth count/types: 400/400; one different-date published FX rate: 400/400; partial allocation and wrong FX on same period-end payment: 400/400 |
| D19 | truth count/types: 400/400; one different-date published FX rate: 400/400; one outside invoice booked inside company period: 400/400; same next-period invoice booked inside at wrong FX: 400/400 |
| D20 | truth count/types: 400/400; one different-date published FX rate: 400/400; one outside invoice booked inside company period: 400/400; same next-period invoice booked inside at wrong FX: 400/400 |

D06–D08 duplicate candidates have the same entity, currency, total, numeric line items and case/punctuation-normalized descriptions. Each episode had 1, 3 or 4 candidate pairs and every candidate pair had distinct invoice and document IDs. Equal totals with differing line signatures also appeared in every episode. This check does not identify the injected pair uniquely when multiple signatures match. The truth read is limited to issue count and types.

D09–D11 observed allocation modes: missing, partial. D11 exhibited both modes. D16–D18 each varied across 20 currency pairs, 8 company timezones, 400 posted/expected AR fractions and 28 invoice ages in days. The payment stayed on period close. An FX date offset of +1 matched throughout; the six observed sets of possible offsets include collisions from rounding. D19–D20 each varied across 20 currency pairs, 8 company timezones, 1–3 days from close to issue and booking on either the close or the day before it. There were 11 distinct sets of possible FX offsets. Matching rounded amounts can leave the applied date ambiguous. Scenarios within each interaction group use the same config and repeat the same samples.

Repository check: `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.check > /tmp/r22-codex1/check.log 2>&1` (exit 0, real 58.35 s). `ALL CHECKS PASSED in 58.3 s`. Next: X2 and X3 after the lead's refund fix reaches the round branch.

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
2026-11-22 05:03 rb — Z1 done. `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 28000 --json /tmp/r22-rb/j28000.json` → exit 0, wall 1 s; `--seed-base 29000 --json /tmp/r22-rb/j29000.json` → exit 0, wall 2 s (both at 8cf7071, pre-FIX; Z1 has no FIX gate). JSON confirms 20 episodes per policy per run. Tables:
  B=28000: random_explorer P/R/F1 0/0/0 return -0.903 steps 33.0 max 33 time 0.023 s max 0.024 s; reconcile 1.000/1.000/1.000 return 0.960 steps 21.1 max 24 time 0.023 s max 0.025 s; flag_all 0/0/0 return -1.000 steps 3.6 max 4 time 0.020 s max 0.022 s; oracle 1.000/1.000/1.000 return 1.000 steps 1.0 time 0.003 s max 0.004 s.
  B=29000: random_explorer 0/0/0 return -0.903 steps 33.0 max 33 time 0.022 s max 0.023 s; reconcile 1.000/1.000/1.000 return 0.960 steps 21.0 max 24 time 0.022 s max 0.023 s; flag_all 0/0/0 return -1.000 steps 3.6 max 4 time 0.020 s max 0.023 s; oracle 1.000/1.000/1.000 return 1.000 steps 1.0 time 0.003 s max 0.004 s.
  No call-outs: oracle F1 = 1.000 and reconcile F1 = 1.000 in both runs; random return -0.903 and flag_all -1.000, both ≤ -0.5. Next: Z2/Z3 are gated on the FIX commit (`generator: realised FX on refunds`), not yet on origin/night/2026-11-22-r22 — will re-check after fetch.

2026-11-22 05:20 codex2 — Y2 complete after a8538c7. The policy audit now selects the latest earlier receipt from public payment docs and ledger cash-row entity_id, checks the refund's receipt-date 2900 debit or refund-date fallback, and checks its balancing 7900 posting. The separate cash-date check is unchanged. chronology.py already checks the cash row at the payment's own date and orders balances in source currency, so no change was needed.

- `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/policy_text.py --seeds 56000-56199` → exit 0 in 130.32 s. `Audited 8400 episodes across 42 configurations; 33185851 checks, 0 unexpected failures.`
- `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 56000-56299` → exit 0 in 171.27 s. Summary and all dirty-scenario exceptions verbatim below.
- `env -u AUDITENV_SECRET uv run python -m auditenv.check` → exit 0 in 115.76 s, 564 tests. `ALL CHECKS PASSED in 115.6 s`.

```text
episodes checked: 12600 (seeds 56000-56299, 42 configs)
unexplained violations: 17 (0 in clean configs)
  hard/hard seed=56084 f_ar_before_booking ids=['PAY-630849', 'SI-2026-560478', 'R3132'] ar credit 2026-06-01T12:47:00+00:00 booking 2026-06-03T14:56:00+00:00
  hard/hard seed=56190 f_ar_before_booking ids=['RCPT0160344', 'SI-2026-839100', 'R4510'] ar credit 2026-09-01T14:04:00+03:00 booking 2026-09-03T10:31:00+03:00
  hard/hard seed=56253 f_ar_before_booking ids=['BNK-388929', 'SI-2025-175976', 'L04256'] ar credit 2025-03-02T14:44:00+05:30 booking 2025-03-03T14:34:00+05:30
  D14/default seed=56058 f_ar_before_booking ids=['BNK-526508', 'F0218797', 'R1775'] ar credit 2026-04-01T00:07:00+01:00 booking 2026-04-03T13:28:00+01:00
  D14/default seed=56060 f_ar_before_booking ids=['BNK-494520', 'F0443443', 'GL-004830'] ar credit 2026-06-01T13:14:00-05:00 booking 2026-06-02T10:33:00-05:00
  D14/default seed=56128 f_ar_before_booking ids=['PAY-279453', 'F0874503', 'R4350'] ar credit 2025-04-03T13:32:00+01:00 booking 2025-04-04T21:45:00+01:00
  D14/hard seed=56018 f_ar_before_booking ids=['RCPT0641841', 'F0873471', 'GL-004990'] ar credit 2026-06-02T10:42:00+00:00 booking 2026-06-03T13:45:00+00:00
  D14/hard seed=56023 f_ar_before_booking ids=['RCPT0592601', 'SI-2025-347712', 'L03747'] ar credit 2025-03-01T00:43:00+01:00 booking 2025-03-04T21:59:00+01:00
  D14/hard seed=56114 f_ar_before_booking ids=['BNK-507723', '2604-864602', 'GL-003765'] ar credit 2026-04-01T11:05:00+03:00 booking 2026-04-02T12:50:00+03:00
  D14/hard seed=56230 f_ar_before_booking ids=['BNK-526067', '2608-861501', 'L03041'] ar credit 2026-08-01T14:52:00+09:00 booking 2026-08-03T11:18:00+09:00
  D15/default seed=56058 f_ar_before_booking ids=['BNK-526508', 'F0218797', 'R1775'] ar credit 2026-04-01T00:07:00+01:00 booking 2026-04-03T13:28:00+01:00
  D15/default seed=56060 f_ar_before_booking ids=['BNK-494520', 'F0443443', 'GL-004830'] ar credit 2026-06-01T13:14:00-05:00 booking 2026-06-02T10:33:00-05:00
  D15/default seed=56128 f_ar_before_booking ids=['PAY-279453', 'F0874503', 'R4350'] ar credit 2025-04-03T13:32:00+01:00 booking 2025-04-04T21:45:00+01:00
  D15/hard seed=56018 f_ar_before_booking ids=['RCPT0641841', 'F0873471', 'GL-004990'] ar credit 2026-06-02T10:42:00+00:00 booking 2026-06-03T13:45:00+00:00
  D15/hard seed=56023 f_ar_before_booking ids=['RCPT0592601', 'SI-2025-347712', 'L03747'] ar credit 2025-03-01T00:43:00+01:00 booking 2025-03-04T21:59:00+01:00
  D15/hard seed=56114 f_ar_before_booking ids=['BNK-507723', '2604-864602', 'GL-003765'] ar credit 2026-04-01T11:05:00+03:00 booking 2026-04-02T12:50:00+03:00
  D15/hard seed=56230 f_ar_before_booking ids=['BNK-526067', '2608-861501', 'L03041'] ar credit 2026-08-01T14:52:00+09:00 booking 2026-08-03T11:18:00+09:00
```

Next: Y3 public-data ambiguity audit.

2026-11-22 05:22 codex2 — Y3 complete. Reviewed the a8538c7 diff. Verdict: the published rule yields a unique 2900 debit and 7900 posting in the audited books. CONTRACT §§1–2 together identify the customer, company-local FX dates, currency exponents, and rounding. The public policy supplies the same conversion and ordering rules across its ledger, FX and rounding fields, but should make the ledger join explicit. The verifier limits candidates to booked payments. An unbooked payment has no public ledger customer, so the wording should explicitly exclude it. The exact identity can tie at the same instant in a constructed case, but the company-local FX date and converted amount cannot differ.

`PYTHONPATH=. env -u AUDITENV_SECRET uv run python /tmp/r22-codex2/refund_ambiguity.py` → exit 0 in 43.28 s, seeds 0–999. For each posted refund, grouped public journals by payment_id, indexed receipt remainders by public entity_id, currency and source amount, and compared independently rounded signed totals for 1000, 2900 and 7900. D01–D05 share a config within each difficulty, so the table counts scenario executions. The 28 fallbacks followed the published rule.

| Config | refunds | foreign | fallback | multiple earlier candidates | tied latest receipts | ambiguous debit | unidentified refund customer | unknown-earlier | posting mismatch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| default | 1508 | 606 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| hard | 1429 | 581 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| D01/default | 1683 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D01/hard | 1731 | 706 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D02/default | 1683 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D02/hard | 1731 | 706 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D03/default | 1683 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D03/hard | 1731 | 706 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D04/default | 1683 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D04/hard | 1731 | 706 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D05/default | 1683 | 696 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| D05/hard | 1731 | 706 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Total | 20007 | 8197 | 28 | 0 | 0 | 0 | 0 | 0 | 0 |

Checked 12000 episodes; 0 tied identities, 0 ambiguous posting amounts, 0 posting mismatches.

Synthetic: two earlier EUR 100.00 remainders at USD/EUR 1.10 and 1.20 select the latest; with refund-date rate 1.30 the debit is USD 120.00 and realised FX debit is USD 10.00. Two receipts at identical instants can tie for identity, and share the same company date and rate.

Proposed exact replacement for the refund portion of CONTRACT §2 and policy.json ledger.payment:

> For a refund (negative amount_minor), use its absolute amount in the payment currency. Join each payment to its booked ledger rows by payment_id. The eligible receipts are earlier positive payments with the same non-null ledger entity_id and payment currency whose amount_minor minus the sum of invoice_refs amount_minor equals the refunded amount. Treat null invoice_refs as an empty list. Compare payment timestamps as instants and use the latest eligible receipt. Receipts tied at the latest instant use the same FX date. If no receipt qualifies, use the refund timestamp instead. Debit 2900 using that company-local date's rate and credit 1000 using the refund's company-local date's rate. Convert both amounts to base minor units separately with ROUND_HALF_UP using the published currency exponents. Post the difference to 7900, debiting it when the cash credit is larger and crediting it when the 2900 debit is larger. Omit the 7900 row when the difference is zero.
