2026-11-22 05:00 lead — Round 22 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/CASE_UPDATES/r20–r21 archive. Baseline check at 774570d: exit 0, 50.6 s. Decision: fix the round-21 refund FX artefact at the root (refund Dr 2900 at the rate of the receipt it returns, difference to 7900). Reason: every jury clean episode D01–D05 is generated with ensure_distractors and so contains a refund; a foreign one leaves the customer's 2900 below zero in base currency, which a jury "accounting equalities" check on clean books can fail (up to 5 × 1.25 points). Round 21 deferred it only for time; ~13 h remain and the change follows the round-20 re-export path. Rounding residue on AR (a few minor units) stays documented. Wrote TASKS.md: codex1 clean-room D-matrix + ledger_identity/text_auditor after FIX; codex2 clean-room paired transform + policy_text/chronology update + rule-ambiguity review; rb jury_run/scenarios; gemini sweeps gated on the FIX commit.
2026-11-22 05:12 lead — L1 FIX done. Regression first: tests.test_generator...test_refund_clears_the_unapplied_cash_it_returns (D03 config, seeds 0–39 × default/hard: each customer's 2900 balance in base currency never below 0, >10 foreign refunds, some with 7900) failed on the old code (e.g. -29596), passes now. Rule (CONTRACT §2, policy.json ledger.payment): a refund debits 2900 at the payment-date rate of the receipt it returns = the same customer's (ledger entity_id) latest earlier payment in that currency whose amount − Σ invoice_refs equals the refunded amount (refund-date rate if none); cash at the refund-date rate; difference 7900. generator.State.refunded_receipt + verify.Books.refunded_receipt implement it independently; old generator now fails verify --seeds 0-199 (266/600), new passes 600/600. RNG stream preserved: the realised-FX row takes the cash row's tie (no random draw) and the expense filler target excludes those rows — compared with the old generator on 660 episodes (15 seeds × default/hard/heavy/D01–D20 both difficulties): invoices, payments, fx, truth types/ids/amounts and every non-2900/7900 ledger row identical; only row ids after an inserted 7900 row renumber. Snapshot counts updated (+57/+68 payment rows on 100 heavy seeds = the new 7900 rows; seed-7 hardening row ids R390/R445 → R391/R446). Re-exported episodes, trajectories, golden (80). check exit 0 (51.4 s), sync_docs no drift (no measured number changed), fuzz 0-999 3000 eps + hard 0-199 600 eps PASSED. night/r21/ledger_identity --classify on 41000–41299: refund class (a) 0 (was 920), rounding (b) 415 unchanged, 1985 "other" = all its old-rule fx check on the new refund 7900 rows (codex1 X2 updates the checker). DESIGN §10/README/PITCH limitation text: refund artefact removed, rounding residue stays. DESIGN worked-example row ids re-checked on the new exports: unchanged.
2026-11-22 05:14 gemini2a — G5 done. Command: env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 6000-7999. Exit code 0, wall time 44.4 s. Output: "6000/6000 episodes valid; episodes with problems: 0". 0 problems found across 6,000 episodes on seeds 6000–7999.
2026-11-22 05:13 gemini2b — G7 complete. Re-exported all three splits into scratch dirs /tmp/r22-gemini2b/{dev,train,hard} via auditenv.export and diffed against committed episodes: dev diff exit 0, train diff exit 0, hard diff exit 0. All files byte-for-byte identical.
2026-11-22 05:13 gemini3a — G9 done: Four jury modules ran 3 times via env -u AUDITENV_SECRET uv run python -m unittest tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired. Run 1: Ran 73 tests in 2.050s, OK (wall time 2.142s, exit code 0). Run 2: Ran 73 tests in 1.976s, OK (wall time 2.033s, exit code 0). Run 3: Ran 73 tests in 2.002s, OK (wall time 2.060s, exit code 0). All runs exit 0 with 73/73 tests passing cleanly.
2026-11-22 05:13 gemini3a — G10 done: Attack search and sensitivity check. (1) env -u AUDITENV_SECRET uv run python -m auditenv.attack (exit 0, 0.425s): "=== HANDOFF R1 Automated Attack Search: PASSED ===", seeds: 20 (clean 5, dirty 15), total mutations: 11000, violations detected: 0. (2) uv run python scripts/sensitivity.py (exit 0, 2.173s): dev & hard rankings invariant across step costs (0.001, 0.002, 0.005) and tolerances (0, 1, 100 minor units); "Ranking unchanged across all settings: oracle > reconcile > naive_reconcile > random > flag_all" (dev) and "oracle > reconcile_hard > reconcile > naive_reconcile > random > flag_all" (hard); re-grade with default parameters reproduced every env reward exactly.
2026-11-22 05:13 gemini3b — G11: ran env -u AUDITENV_SECRET uv run python -m auditenv.verify --dir episodes/<split> on all 3 splits. episodes/dev: 10/10 episodes valid; episodes with problems: 0 (exit 0, wall time 0.114 s). episodes/hard: 20/20 episodes valid; episodes with problems: 0 (exit 0, wall time 0.320 s). episodes/train: 10/10 episodes valid; episodes with problems: 0 (exit 0, wall time 0.103 s). Total 40/40 episodes valid across dev, hard, train.
2026-11-22 05:14 gemini3b — G12: ran yes '' | uv run python -m auditenv.demo (exit 0, wall time 0.129 s). Final reward/score lines: terminal reward 0.958 = clip(2*F1 - 1 - 0.002*21 steps) P=1.00 R=1.00 F1=1.00; ISS-1 351331 USD TP, ISS-2 286 USD TP, ISS-3 428234 USD TP, ISS-4 800599 USD TP; oracle 1.000, reconcile 0.958, silence -1.000, guessed -1.000, repeat twice 0.333, flag-everything -1.000, random -1.000, clean silence 1.000, clean guessed -1.000, clean reconcile 0.958; policy side: 22 steps, rewards seen = [0.0], final info = {}; grader log : reward 0.958, F1 1.00, TP 4 FP 0 FN 0. Comparison with docs/DEMO.md: all numbers match exactly (0 differences).

2026-11-22 05:13 gemini1b — G3 stress test on seeds 12000-12299:
Command 1: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 12000-12299` -> exit 0, wall time 7.37 s. Summary: `reconcile on 1200 default episodes (seeds 12000-12299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 33, truncated 0 (7.3 s)`
Command 2: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 12000-12299` -> exit 0, wall time 20.48 s. Summary: `reconcile_hard on 1200 hard episodes (seeds 12000-12299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 57, truncated 0 (20.5 s)`
Task G3 complete.
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
2026-11-22 05:31 lead — FIX2 (AR settlement residue). Measured first: a fully paid invoice paid in ≥2 parts kept ±1 minor unit in 1200 in 54/300 default and 60/300 hard D02 episodes (jury D02 = "correct split payment", and every D01–D05 episode has a split). Regression tests.test_generator...test_fully_paid_invoice_closes_its_receivable (D02 seeds 0–39 × both difficulties) failed on FIX1 (20 receivables ±1), passes now. Rule (CONTRACT §2, policy.json ledger.payment): the ref that completes an invoice (with earlier payments' refs it adds up to total_minor) credits convert(total) − Σ convert(earlier refs); difference 7900. Generator: State.settle() applied on top of the per-document posting (no random draw), once at booking and again after all payments exist (merged receipts are created out of date order — first attempt missed them: verify flagged "over-allocated" on seeds 13/50/131/132). inject.payment_allocation never picks a split's last part (same draw, steps to the next eligible candidate), so truth "expected AR credit for the ref" and the evidence rule stay as published. verify.Books.settling_credit and policies/reconcile.py implement the rule. Compared with FIX1 on 660 episodes: 21 differ (only where the injected allocation hit a last part); everything else identical outside payment 1200/2900/7900 rows. Old generator fails the new verifier (458/600). Re-exported; naive reconcile dev numbers moved (F1 0.286 → 0.288, return −0.480 → −0.478; sync_docs + DESIGN sensitivity row updated); reconcile/oracle/hard unchanged; DESIGN worked examples re-checked: unchanged. Snapshot counts updated (heavy hard: +1 payment row, 7 invoices moved clean→issue). check exit 0 (565 tests, 56.0 s), sync_docs no drift, golden 80/80, fuzz 0-999 + hard 0-199 PASSED, stress reconcile 1200 eps imperfect 0, attack 0 violations, mutants 22/22. ledger_identity --classify 41000–41299: (a) 0, (b) 0 (was 415); its 3700 "other" are all the old rules it encodes (2835 fx rows on refunds/last parts, 865 ar_close expecting the old residue). README/PITCH limitation bullets removed, DESIGN §10 describes the fix.

2026-11-22 05:20 codex1 — X2 after a8538c7. Derived the 2900 debit from the latest earlier receipt with the same ledger entity, currency and exact unallocated amount. With no such receipt the policy uses the refund date. The audit derives 7900 from that debit and the refund-date cash credit. Class (a) still detects the pre-fix refund-rate residue.

`PYTHONPATH=. /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r21.ledger_identity --classify --seeds 41000-41299 > /tmp/r22-codex1/41000-41299.log 2>&1` (exit 0, real 48.08 s). `Classified 415 clean violations: (a) 0, (b) 415, (c) 0.`

| Config | Difficulty | FX refund (a) | AR rounding (b) | Other (c) | Max (a) base minor | Max (a) % |
|---|---|---:|---:|---:|---:|---:|
| D01 | default | 0 | 33 | 0 | 0 | 0.000000% |
| D01 | hard | 0 | 50 | 0 | 0 | 0.000000% |
| D02 | default | 0 | 33 | 0 | 0 | 0.000000% |
| D02 | hard | 0 | 50 | 0 | 0 | 0.000000% |
| D03 | default | 0 | 33 | 0 | 0 | 0.000000% |
| D03 | hard | 0 | 50 | 0 | 0 | 0.000000% |
| D04 | default | 0 | 33 | 0 | 0 | 0.000000% |
| D04 | hard | 0 | 50 | 0 | 0 | 0.000000% |
| D05 | default | 0 | 33 | 0 | 0 | 0.000000% |
| D05 | hard | 0 | 50 | 0 | 0 | 0.000000% |

Checks executed / mismatches

| Config | Difficulty | journal | ar_running | ar_close | unapplied_running | refund_2900 | fx | trial |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| D01 | default | 45,672 / 0 | 19,152 / 33 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D01 | hard | 167,997 / 0 | 21,081 / 50 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |
| D02 | default | 45,672 / 0 | 19,152 / 33 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D02 | hard | 167,997 / 0 | 21,081 / 50 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |
| D03 | default | 45,672 / 0 | 19,152 / 33 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D03 | hard | 167,997 / 0 | 21,081 / 50 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |
| D04 | default | 45,672 / 0 | 19,152 / 33 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D04 | hard | 167,997 / 0 | 21,081 / 50 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |
| D05 | default | 45,672 / 0 | 19,152 / 33 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D05 | hard | 167,997 / 0 | 21,081 / 50 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |

Classified violation records below are quoted for D01. D02–D05 repeat every line with the same seed, difficulty, check and row IDs.

```text
- D01/default seed 41007 class b ar_running (R2706): observed -1, expected 0; F0057818
- D01/default seed 41019 class b ar_running (GL-000793): observed -1, expected 0; INV-355747
- D01/default seed 41028 class b ar_running (L02017): observed -1, expected 0; F0606872
- D01/default seed 41034 class b ar_running (R229): observed -1, expected 0; 2503-857257
- D01/default seed 41039 class b ar_running (R988): observed -1, expected 0; SI-2025-984723
- D01/default seed 41045 class b ar_running (R4175): observed -1, expected 0; F0254951
- D01/default seed 41074 class b ar_running (GL-003948): observed -1, expected 0; 2601-593279
- D01/default seed 41082 class b ar_running (GL-005049): observed -1, expected 0; F0880818
- D01/default seed 41094 class b ar_running (R3306): observed -1, expected 0; INV-357622
- D01/default seed 41100 class b ar_running (R1817): observed -1, expected 0; 2510-112034
- D01/default seed 41127 class b ar_running (GL-002840): observed -1, expected 0; F0686931
- D01/default seed 41137 class b ar_running (GL-001286): observed -1, expected 0; 2501-410390
- D01/default seed 41141 class b ar_running (R3610): observed -1, expected 0; INV-054288
- D01/default seed 41166 class b ar_running (GL-004004): observed -1, expected 0; 2506-422686
- D01/default seed 41174 class b ar_running (GL-000390): observed -1, expected 0; SI-2025-590188
- D01/default seed 41182 class b ar_running (GL-000759): observed -1, expected 0; SI-2026-721173
- D01/default seed 41192 class b ar_running (GL-004483): observed -1, expected 0; 2611-659303
- D01/default seed 41195 class b ar_running (GL-003793): observed -1, expected 0; F0615449
- D01/default seed 41199 class b ar_running (R2679): observed -1, expected 0; F0107215
- D01/default seed 41212 class b ar_running (L01373): observed -1, expected 0; SI-2025-273988
- D01/default seed 41222 class b ar_running (GL-002092): observed -1, expected 0; INV-911729
- D01/default seed 41225 class b ar_running (R4394): observed -1, expected 0; INV-763469
- D01/default seed 41225 class b ar_running (R4436): observed -1, expected 0; INV-981731
- D01/default seed 41239 class b ar_running (R1295): observed -1, expected 0; 2611-562598
- D01/default seed 41243 class b ar_running (GL-005203): observed -1, expected 0; F0481630
- D01/default seed 41245 class b ar_running (R2721): observed -1, expected 0; INV-988106
- D01/default seed 41248 class b ar_running (L00515): observed -1, expected 0; F0370420
- D01/default seed 41258 class b ar_running (R1435): observed -1, expected 0; SI-2026-923475
- D01/default seed 41262 class b ar_running (GL-001158): observed -1, expected 0; F0515687
- D01/default seed 41270 class b ar_running (GL-000401): observed -1, expected 0; INV-215118
- D01/default seed 41292 class b ar_running (L02096): observed -1, expected 0; INV-931351
- D01/default seed 41293 class b ar_running (GL-003102): observed -1, expected 0; 2503-365156
- D01/default seed 41293 class b ar_running (GL-003276): observed -1, expected 0; 2503-133260
- D01/hard seed 41005 class b ar_running (GL-005749): observed -1, expected 0; INV-064884
- D01/hard seed 41013 class b ar_running (R2646): observed -1, expected 0; INV-859119
- D01/hard seed 41017 class b ar_running (L03233): observed -1, expected 0; INV-758326
- D01/hard seed 41037 class b ar_running (L03201): observed -1, expected 0; 2611-778760
- D01/hard seed 41037 class b ar_running (L03244): observed -1, expected 0; 2611-453884
- D01/hard seed 41040 class b ar_running (R5101): observed -1, expected 0; 2609-004130
- D01/hard seed 41052 class b ar_running (R1027): observed -1, expected 0; SI-2026-798836
- D01/hard seed 41063 class b ar_running (L01469): observed -1, expected 0; 2609-768605
- D01/hard seed 41065 class b ar_running (R4601): observed -1, expected 0; F0032065
- D01/hard seed 41096 class b ar_running (R648): observed -1, expected 0; SI-2026-466918
- D01/hard seed 41098 class b ar_running (L04227): observed -1, expected 0; 2612-160441
- D01/hard seed 41100 class b ar_running (GL-005821): observed -1, expected 0; 2612-882562
- D01/hard seed 41103 class b ar_running (R2401): observed -1, expected 0; F0054592
- D01/hard seed 41106 class b ar_running (L03292): observed -1, expected 0; 2507-119107
- D01/hard seed 41112 class b ar_running (R4842): observed -1, expected 0; 2508-594384
- D01/hard seed 41115 class b ar_running (L03814): observed -1, expected 0; 2507-425960
- D01/hard seed 41118 class b ar_running (GL-004927): observed -1, expected 0; INV-114883
- D01/hard seed 41123 class b ar_running (R4880): observed -1, expected 0; INV-019033
- D01/hard seed 41128 class b ar_running (GL-001786): observed -1, expected 0; SI-2026-305268
- D01/hard seed 41137 class b ar_running (R1542): observed -1, expected 0; F0267943
- D01/hard seed 41151 class b ar_running (L00532): observed -1, expected 0; INV-263286
- D01/hard seed 41156 class b ar_running (R5500): observed -1, expected 0; 2508-592873
- D01/hard seed 41164 class b ar_running (R3355): observed -1, expected 0; 2504-064452
- D01/hard seed 41170 class b ar_running (R3853): observed -1, expected 0; INV-886051
- D01/hard seed 41170 class b ar_running (R3783): observed -1, expected 0; INV-044439
- D01/hard seed 41174 class b ar_running (R1948): observed -1, expected 0; 2501-044446
- D01/hard seed 41179 class b ar_running (R5285): observed -1, expected 0; 2502-263509
- D01/hard seed 41185 class b ar_running (L05076): observed -1, expected 0; SI-2026-814573
- D01/hard seed 41194 class b ar_running (L05631): observed -1, expected 0; INV-589999
- D01/hard seed 41204 class b ar_running (R3491): observed -1, expected 0; INV-929188
- D01/hard seed 41212 class b ar_running (GL-003946): observed -1, expected 0; 2603-669849
- D01/hard seed 41216 class b ar_running (R2148): observed -1, expected 0; SI-2025-019680
- D01/hard seed 41216 class b ar_running (R2146): observed -1, expected 0; SI-2025-363180
- D01/hard seed 41234 class b ar_running (GL-002416): observed -1, expected 0; SI-2025-000350
- D01/hard seed 41240 class b ar_running (GL-002596): observed -1, expected 0; F0438164
- D01/hard seed 41249 class b ar_running (R4435): observed -1, expected 0; SI-2026-018892
- D01/hard seed 41251 class b ar_running (GL-004129): observed -1, expected 0; 2602-317250
- D01/hard seed 41253 class b ar_running (L01045): observed -1, expected 0; 2502-305985
- D01/hard seed 41253 class b ar_running (L00833): observed -1, expected 0; 2502-633501
- D01/hard seed 41262 class b ar_running (GL-003336): observed -1, expected 0; INV-882581
- D01/hard seed 41266 class b ar_running (GL-002148): observed -1, expected 0; F0818242
- D01/hard seed 41266 class b ar_running (GL-001994): observed -1, expected 0; F0254037
- D01/hard seed 41278 class b ar_running (GL-000895): observed -1, expected 0; SI-2025-730616
- D01/hard seed 41279 class b ar_running (L01297): observed -1, expected 0; F0674420
- D01/hard seed 41282 class b ar_running (R4407): observed -1, expected 0; F0128741
- D01/hard seed 41290 class b ar_running (R5260): observed -1, expected 0; F0617458
- D01/hard seed 41291 class b ar_running (R5757): observed -1, expected 0; 2604-148765
- D01/hard seed 41292 class b ar_running (GL-005682): observed -1, expected 0; INV-315947
- D01/hard seed 41295 class b ar_running (R3381): observed -1, expected 0; F0203109
- D01/hard seed 41299 class b ar_running (R3081): observed -1, expected 0; SI-2025-343694
```

`PYTHONPATH=. /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r21.ledger_identity --classify --seeds 53000-53299 > /tmp/r22-codex1/53000-53299.log 2>&1` (exit 0, real 48.19 s). `Classified 365 clean violations: (a) 0, (b) 365, (c) 0.`

| Config | Difficulty | FX refund (a) | AR rounding (b) | Other (c) | Max (a) base minor | Max (a) % |
|---|---|---:|---:|---:|---:|---:|
| D01 | default | 0 | 43 | 0 | 0 | 0.000000% |
| D01 | hard | 0 | 30 | 0 | 0 | 0.000000% |
| D02 | default | 0 | 43 | 0 | 0 | 0.000000% |
| D02 | hard | 0 | 30 | 0 | 0 | 0.000000% |
| D03 | default | 0 | 43 | 0 | 0 | 0.000000% |
| D03 | hard | 0 | 30 | 0 | 0 | 0.000000% |
| D04 | default | 0 | 43 | 0 | 0 | 0.000000% |
| D04 | hard | 0 | 30 | 0 | 0 | 0.000000% |
| D05 | default | 0 | 43 | 0 | 0 | 0.000000% |
| D05 | hard | 0 | 30 | 0 | 0 | 0.000000% |

Checks executed / mismatches

| Config | Difficulty | journal | ar_running | ar_close | unapplied_running | refund_2900 | fx | trial |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| D01 | default | 45,979 / 0 | 19,326 / 43 | 15,544 / 0 | 1,573 / 0 | 501 / 0 | 8,086 / 0 | 300 / 0 |
| D01 | hard | 168,571 / 0 | 20,320 / 30 | 15,970 / 0 | 1,613 / 0 | 507 / 0 | 7,803 / 0 | 300 / 0 |
| D02 | default | 45,979 / 0 | 19,326 / 43 | 15,544 / 0 | 1,573 / 0 | 501 / 0 | 8,086 / 0 | 300 / 0 |
| D02 | hard | 168,571 / 0 | 20,320 / 30 | 15,970 / 0 | 1,613 / 0 | 507 / 0 | 7,803 / 0 | 300 / 0 |
| D03 | default | 45,979 / 0 | 19,326 / 43 | 15,544 / 0 | 1,573 / 0 | 501 / 0 | 8,086 / 0 | 300 / 0 |
| D03 | hard | 168,571 / 0 | 20,320 / 30 | 15,970 / 0 | 1,613 / 0 | 507 / 0 | 7,803 / 0 | 300 / 0 |
| D04 | default | 45,979 / 0 | 19,326 / 43 | 15,544 / 0 | 1,573 / 0 | 501 / 0 | 8,086 / 0 | 300 / 0 |
| D04 | hard | 168,571 / 0 | 20,320 / 30 | 15,970 / 0 | 1,613 / 0 | 507 / 0 | 7,803 / 0 | 300 / 0 |
| D05 | default | 45,979 / 0 | 19,326 / 43 | 15,544 / 0 | 1,573 / 0 | 501 / 0 | 8,086 / 0 | 300 / 0 |
| D05 | hard | 168,571 / 0 | 20,320 / 30 | 15,970 / 0 | 1,613 / 0 | 507 / 0 | 7,803 / 0 | 300 / 0 |

Classified violation records below are quoted for D01. D02–D05 repeat every line with the same seed, difficulty, check and row IDs.

```text
- D01/default seed 53005 class b ar_running (R2372): observed -1, expected 0; 2512-533111
- D01/default seed 53014 class b ar_running (L04542): observed -1, expected 0; INV-297913
- D01/default seed 53015 class b ar_running (GL-004755): observed -1, expected 0; INV-682983
- D01/default seed 53019 class b ar_running (GL-000232): observed -1, expected 0; F0453621
- D01/default seed 53027 class b ar_running (L04782): observed -1, expected 0; SI-2025-228459
- D01/default seed 53031 class b ar_running (L02375): observed -1, expected 0; F0497510
- D01/default seed 53033 class b ar_running (L03163): observed -1, expected 0; F0975303
- D01/default seed 53035 class b ar_running (GL-002967): observed -1, expected 0; 2504-733412
- D01/default seed 53046 class b ar_running (L05113): observed -1, expected 0; INV-996587
- D01/default seed 53053 class b ar_running (GL-005157): observed -1, expected 0; INV-729112
- D01/default seed 53053 class b ar_running (GL-005263): observed -1, expected 0; INV-003802
- D01/default seed 53060 class b ar_running (R2600): observed -1, expected 0; F0546644
- D01/default seed 53073 class b ar_running (R124): observed -1, expected 0; SI-2025-901187
- D01/default seed 53090 class b ar_running (GL-004140): observed -1, expected 0; INV-691822
- D01/default seed 53095 class b ar_running (GL-003407): observed -1, expected 0; SI-2026-384820
- D01/default seed 53096 class b ar_running (L03047): observed -1, expected 0; SI-2026-050238
- D01/default seed 53097 class b ar_running (R1359): observed -1, expected 0; 2503-904072
- D01/default seed 53102 class b ar_running (GL-002176): observed -1, expected 0; F0654039
- D01/default seed 53106 class b ar_running (L00419): observed -1, expected 0; INV-647087
- D01/default seed 53108 class b ar_running (R1956): observed -1, expected 0; F0227212
- D01/default seed 53141 class b ar_running (GL-002589): observed -1, expected 0; SI-2025-551605
- D01/default seed 53146 class b ar_running (GL-002777): observed -1, expected 0; INV-752034
- D01/default seed 53148 class b ar_running (L01944): observed -1, expected 0; INV-775157
- D01/default seed 53157 class b ar_running (GL-001967): observed -1, expected 0; INV-761491
- D01/default seed 53162 class b ar_running (L03063): observed -1, expected 0; SI-2026-072906
- D01/default seed 53172 class b ar_running (L00529): observed -1, expected 0; INV-724349
- D01/default seed 53176 class b ar_running (L01403): observed -1, expected 0; INV-885684
- D01/default seed 53178 class b ar_running (L04305): observed -1, expected 0; 2607-219433
- D01/default seed 53186 class b ar_running (GL-004136): observed -1, expected 0; INV-277872
- D01/default seed 53190 class b ar_running (L04731): observed -1, expected 0; INV-154024
- D01/default seed 53198 class b ar_running (L05189): observed -1, expected 0; 2606-895350
- D01/default seed 53203 class b ar_running (GL-001402): observed -1, expected 0; 2602-273351
- D01/default seed 53205 class b ar_running (GL-004053): observed -1, expected 0; 2604-945844
- D01/default seed 53205 class b ar_running (GL-004083): observed -1, expected 0; 2604-470016
- D01/default seed 53209 class b ar_running (L04915): observed -1, expected 0; SI-2026-637784
- D01/default seed 53210 class b ar_running (L05008): observed -1, expected 0; 2507-309485
- D01/default seed 53221 class b ar_running (L02516): observed -1, expected 0; 2611-530535
- D01/default seed 53225 class b ar_running (L03484): observed -1, expected 0; SI-2025-967568
- D01/default seed 53229 class b ar_running (L00676): observed -1, expected 0; 2603-859730
- D01/default seed 53248 class b ar_running (L02805): observed -1, expected 0; SI-2025-206439
- D01/default seed 53263 class b ar_running (GL-002417): observed -1, expected 0; INV-256806
- D01/default seed 53275 class b ar_running (L02226): observed -1, expected 0; 2609-504536
- D01/default seed 53280 class b ar_running (L03648): observed -1, expected 0; 2506-626387
- D01/hard seed 53001 class b ar_running (GL-001066): observed -1, expected 0; INV-887584
- D01/hard seed 53002 class b ar_running (GL-001438): observed -1, expected 0; F0021326
- D01/hard seed 53006 class b ar_running (L03081): observed -1, expected 0; INV-844332
- D01/hard seed 53013 class b ar_running (R2902): observed -1, expected 0; 2506-119791
- D01/hard seed 53021 class b ar_running (L05152): observed -1, expected 0; INV-373108
- D01/hard seed 53027 class b ar_running (R4133): observed -1, expected 0; F0218495
- D01/hard seed 53039 class b ar_running (L05562): observed -1, expected 0; SI-2025-702310
- D01/hard seed 53049 class b ar_running (GL-001006): observed -1, expected 0; SI-2025-915074
- D01/hard seed 53053 class b ar_running (GL-001594): observed -1, expected 0; 2511-778920
- D01/hard seed 53067 class b ar_running (R4171): observed -1, expected 0; SI-2025-706698
- D01/hard seed 53076 class b ar_running (GL-000896): observed -1, expected 0; INV-034548
- D01/hard seed 53094 class b ar_running (R1804): observed -1, expected 0; SI-2026-124571
- D01/hard seed 53119 class b ar_running (GL-003789): observed -1, expected 0; INV-449128
- D01/hard seed 53125 class b ar_running (GL-001923): observed -1, expected 0; 2505-445033
- D01/hard seed 53136 class b ar_running (GL-003782): observed -1, expected 0; INV-542252
- D01/hard seed 53142 class b ar_running (GL-005061): observed -1, expected 0; SI-2025-462467
- D01/hard seed 53160 class b ar_running (L02977): observed -1, expected 0; 2606-648145
- D01/hard seed 53167 class b ar_running (R6077): observed -1, expected 0; INV-979222
- D01/hard seed 53171 class b ar_running (L03554): observed -1, expected 0; SI-2025-244398
- D01/hard seed 53173 class b ar_running (GL-002028): observed -1, expected 0; F0204798
- D01/hard seed 53174 class b ar_running (L01633): observed -1, expected 0; 2502-700718
- D01/hard seed 53203 class b ar_running (L02153): observed -1, expected 0; F0001841
- D01/hard seed 53210 class b ar_running (GL-005268): observed -1, expected 0; 2511-540730
- D01/hard seed 53239 class b ar_running (R1568): observed -1, expected 0; INV-674152
- D01/hard seed 53279 class b ar_running (GL-001709): observed -1, expected 0; INV-415063
- D01/hard seed 53280 class b ar_running (L05445): observed -1, expected 0; F0663254
- D01/hard seed 53284 class b ar_running (R5311): observed -1, expected 0; 2610-114888
- D01/hard seed 53287 class b ar_running (L01862): observed -1, expected 0; F0638660
- D01/hard seed 53288 class b ar_running (R1396): observed -1, expected 0; F0588856
- D01/hard seed 53299 class b ar_running (L03308): observed -1, expected 0; SI-2026-888051
```

`PYTHONPATH=. /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.check > /tmp/r22-codex1/fix-check.log 2>&1` (exit 0, real 110.67 s). `ALL CHECKS PASSED in 110.6 s`. Next: X3.

2026-11-22 05:22 codex1 — X3 after a8538c7. `PYTHONPATH=. /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r21.text_auditor --seeds 54000-54099 > /tmp/r22-codex1/x3.log 2>&1` (exit 0, real 84.56 s). `Discrepancy entries: 0`. F1 1.000 in all 42 config/difficulty groups (4,200 episodes). Auditor source unchanged: its payment FX check compares account 1000 against the transaction-date conversion. The allocation check uses 2900 only to supply evidence for a missing AR credit, without pricing the refund debit. The existing CLI uses its built-in /tmp/r21-codex1 path for automatically cleaned episode exports.

| Config | Difficulty | Scored | Mean F1 | Mean precision | Mean recall |
|---|---|---:|---:|---:|---:|
| baseline | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| baseline | hard | 100 | 1.000000 | 0.960000 | 0.960000 |
| D01 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D01 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D02 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D02 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D03 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D03 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D04 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D04 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D05 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D05 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D06 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D06 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D07 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D07 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D08 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D08 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D09 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D09 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D10 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D10 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D11 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D11 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D12 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D12 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D13 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D13 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D14 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D14 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D15 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D15 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D16 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D16 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D17 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D17 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D18 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D18 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D19 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D19 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D20 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D20 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |

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
2026-11-22 05:16 rb — Z2 done (post-FIX: a8538c7 merged into night/2026-11-22-r22-rb).
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py` → exit 0, wall 5 s. Summary: "Z1: 20 scenarios x 2 difficulties x 5 seeds (32000-32004) x 2 policies = 400 closed runs through judge_adapter, 4.5 s total". All 40 reconcile/reconcile_hard rows: mean F1 1.000, min F1 1.000 (D01–D05 clean tp/fp/fn 0/0/0; D06–D20 5/0/0 per difficulty). All 40 flag_all rows: return -1.000, F1 0.000 — none > 0. FLAGS (0). The script's 23 NOTES only compare per-scenario mean return (0.914–0.962) against the README 20-scenario mean 0.959; F1 is 1.000 everywhere, so no reconcile shortfall to call out (per-scenario return varies with inspection cost 0.002/step, as the notes themselves state). Mean steps: default 20.0–22.8, hard 41.2–44.2; max steps 50 (≤100 budget).
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.extreme_configs` → exit 0, wall 14 s. Final line: "Outcomes: {'valid': 300, 'rejected': 72, 'failure': 0}. Total: 372." All 300 valid configs: exact issue counts as configured, reconcile F1=1.0; empty submission F1=1.0 only on the 0-issue configs, 0.0 otherwise. All 72 rejections are `ValueError: at most 12 issues per episode` (expected). No failures, no traceback. Full outputs: /tmp/r22-rb/z2_scenarios.out, /tmp/r22-rb/z2_extreme.out. Next: Z3.
2026-11-22 05:17 rb — Z3 done (post-FIX, a8538c7 in HEAD; fetch+merge origin/night/2026-11-22-r22 → already up to date).
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.jury_copy` → exit 0, wall 3 s. Reference seeds dev [2000, 2002, 2003, 2004, 2009], hard [9100, 9105, 9109, 9112, 9119]. All 10 rewrite variants (CSV columns shuffled, CRLF, CSV BOM, JSON BOM, JSONL BOM, no final newline, pretty JSON, compact JSON, JSONL keys reversed, combined): 10 accepted / 0 rejected / 10 scores equal each. Final line: "Semantically equivalent rewrite discrepancies: 0".
  `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 30000 --json /tmp/r22-rb/j30000.json` → exit 0, wall 3 s; `--seed-base 31000 --json /tmp/r22-rb/j31000.json` → exit 0, wall 2 s. JSON confirms 20 episodes per policy per run (D01–D20, seeds 30001–30020 / 31001–31020). Tables:
  B=30000: random_explorer P/R/F1 0/0/0 return -0.903 steps 33.0 max 33 time 0.038 s max 0.046 s; reconcile 1.000/1.000/1.000 return 0.961 steps 20.4 max 23 time 0.036 s max 0.041 s; flag_all 0/0/0 return -1.000 steps 3.5 max 4 time 0.033 s max 0.035 s; oracle 1.000/1.000/1.000 return 1.000 steps 1.0 time 0.006 s max 0.007 s.
  B=31000: random_explorer 0/0/0 return -0.903 steps 33.0 max 33 time 0.037 s max 0.043 s; reconcile 1.000/1.000/1.000 return 0.962 steps 19.9 max 24 time 0.037 s max 0.043 s; flag_all 0/0/0 return -1.000 steps 3.6 max 4 time 0.032 s max 0.034 s; oracle 1.000/1.000/1.000 return 1.000 steps 1.0 time 0.005 s max 0.007 s.
  No call-outs: oracle and reconcile F1 = 1.000 in both runs; random return -0.903 and flag_all -1.000, both ≤ -0.5. All rb tasks (Z1–Z3) complete. Full outputs: /tmp/r22-rb/z3_jury_copy.out, /tmp/r22-rb/z3_j30000.out, /tmp/r22-rb/z3_j31000.out.

2026-11-22 05:18 gemini1a — G1: ran `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 16000-16999` (exit 0, wall time 60.72 s: default mode, seeds 16000-16999: 3000 episodes (1986 dirty, 1014 clean), 0 problems, FUZZ PASSED) and `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 16000-16999 --hard` (exit 0, wall time 242.27 s: hard mode, seeds 16000-16999: 3000 episodes (1991 dirty, 1009 clean), 0 problems, FUZZ PASSED). 0 problems found across 6,000 episodes. Next: G2.
2026-11-22 05:22 gemini1a — G2: ran `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 78000` (exit 0, wall time 155.10 s: config sweep, cases 78000-80999: 3000 random configs (1176 hard) in 155.0 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 56, FUZZ PASSED). 0 problems found across 3,000 configs; max steps 56. All assigned tasks (G1, G2) complete.

2026-11-22 05:20 gemini1b — G4 fuzz sweep on seeds 17000-17999 (default + hard):
Command 1: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 17000-17999` -> exit 0, wall time 79.27 s.
Summary:
default mode, seeds 17000-17999: 3000 episodes (1989 dirty, 1011 clean) in 79.2 s
  episodes with a problem (exception / verifier / oracle): 0
  random explorer reward > 0: 252/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
  flag-all reward < 0: 3000/3000
FUZZ PASSED

Command 2: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 17000-17999 --hard` -> exit 0, wall time 287.16 s.
Summary:
hard mode, seeds 17000-17999: 3000 episodes (1991 dirty, 1009 clean) in 287.1 s
  episodes with a problem (exception / verifier / oracle): 0
  random explorer reward > 0: 237/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
  flag-all reward < 0: 3000/3000
FUZZ PASSED
Task G4 complete.
2026-11-22 05:18 gemini2a — G6 done. Command: env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 81000. Exit code 0, wall time 162.0 s. Summary: "config sweep, cases 81000-83999: 3000 random configs (1177 hard) in 162.0 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 55. FUZZ PASSED". Max steps: 55.
2026-11-22 05:21 gemini2b — G8 complete.
- scripts/golden.py --check: exit 0, "All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2b/tests/golden_hashes.json."
- scripts/mutate_reward.py: exit 0, "22/22 mutants killed."
- scripts/shortcut_miner.py --seeds 5000-5999 --report-only: exit 0 (41.2 s), 16 flagged total (duplicate_invoice: 2/2, payment_allocation: 8/1, fx_error: 3/0, period_cutoff: 0/0).
- scripts/shortcut_miner.py --seeds 5000-5999 --report-only --hard: exit 0 (84.3 s), 11 affected flagged (duplicate_invoice: 0/0, payment_allocation: 9/2, fx_error: 2/0, period_cutoff: 0/0).
All miner values with precision > 0.5 match the known surface cues documented in docs/DESIGN.md §10 (duplicate counts, period-end acct2900/acct7900 rows, acct2900 amount counts for payment allocation and fx error). Zero undocumented miner values.
2026-11-22 05:16 gemini3b — G13: ran env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r22-gemini3b/c.json (exit 0, wall time 79.2 s; 564 unit tests, all gates passed) then uv run python scripts/sync_docs.py --check --json /tmp/r22-gemini3b/c.json (exit 0, wall time 0.065 s). Drift lines verbatim: "All documentation tables match measured data." (zero drift).
2026-11-22 05:39 lead — Merged all 9 worker branches (21 tasks done, all evidence green on FIX1: verify 6000–7999 6000/6000, fuzz 16000–17999 default+hard, config sweeps 78000–83999, stress 12000–12299, re-export diff 0, golden/mutants/miner, jury modules ×3, attack 0, demo, check+sync; codex1 X1 D-matrix 8000 eps 0 failures, X2 ledger_identity updated to the refund rule → (a) 0, X3 text auditor 54000–54099; codex2 Y1 clean-room paired 0 discrepancies / no ids in free text, Y2 policy_text 56000–56199 0 unexpected + chronology 0 unexplained in clean configs, Y3 refund-rule ambiguity 0 on 12000 eps; rb jury_run 28000–31000, scenarios, extreme configs, jury_copy). Acted on Y3: 28 refunds in default/hard (none in D01–D05) fell back to the refund-date rate because two overpayments of one customer merged into one receipt (default seeds 255, 284). FIX3: never merge two overpayments (no random draw added; 2 more of 660 compared episodes change) → 0 fallbacks on seeds 0–999 default and hard; regression extended (fails 4× without the fix). CONTRACT wording made explicit (booked receipt, ledger entity_id) per Y3. Heavy-hard snapshot counts updated; naive reconcile hard F1 0.186 → 0.185 (sync_docs). check exit 0 (55.8 s), sync no drift, golden 80/80, fuzz 0-999 + hard 0-199 PASSED, verify 600/600, attack 0. DESIGN worked examples re-checked.

2026-11-22 05:45 codex1 — X4 at c8cfe6f (generator d0fbb34). The ledger audit indexes earlier public payment refs by invoice and timestamp. A ref that completes an invoice credits the invoice-date conversion of its total less the sum of earlier converted refs. The old independent-rounding residue detector, class (b), remains in place.

`PYTHONPATH=. /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r21.ledger_identity --classify --seeds 41000-41299 > /tmp/r22-codex1/x4-41000-41299.log 2>&1` (exit 0, real 40.72 s). `Classified 0 clean violations: (a) 0, (b) 0, (c) 0.`

| Config | Difficulty | journal | ar_running | ar_close | unapplied_running | refund_2900 | fx | trial |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| D01 | default | 45,672 / 0 | 19,152 / 0 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D01 | hard | 167,997 / 0 | 21,081 / 0 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |
| D02 | default | 45,672 / 0 | 19,152 / 0 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D02 | hard | 167,997 / 0 | 21,081 / 0 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |
| D03 | default | 45,672 / 0 | 19,152 / 0 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D03 | hard | 167,997 / 0 | 21,081 / 0 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |
| D04 | default | 45,672 / 0 | 19,152 / 0 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D04 | hard | 167,997 / 0 | 21,081 / 0 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |
| D05 | default | 45,672 / 0 | 19,152 / 0 | 15,463 / 0 | 1,582 / 0 | 500 / 0 | 8,029 / 0 | 300 / 0 |
| D05 | hard | 167,997 / 0 | 21,081 / 0 | 16,515 / 0 | 1,507 / 0 | 474 / 0 | 8,041 / 0 | 300 / 0 |

`PYTHONPATH=. /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r21.ledger_identity --classify --seeds 57000-57299 > /tmp/r22-codex1/x4-57000-57299.log 2>&1` (exit 0, real 41.48 s). `Classified 0 clean violations: (a) 0, (b) 0, (c) 0.`

| Config | Difficulty | journal | ar_running | ar_close | unapplied_running | refund_2900 | fx | trial |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| D01 | default | 46,690 / 0 | 19,123 / 0 | 15,457 / 0 | 1,516 / 0 | 456 / 0 | 7,958 / 0 | 300 / 0 |
| D01 | hard | 170,701 / 0 | 20,706 / 0 | 16,362 / 0 | 1,607 / 0 | 504 / 0 | 7,938 / 0 | 300 / 0 |
| D02 | default | 46,690 / 0 | 19,123 / 0 | 15,457 / 0 | 1,516 / 0 | 456 / 0 | 7,958 / 0 | 300 / 0 |
| D02 | hard | 170,701 / 0 | 20,706 / 0 | 16,362 / 0 | 1,607 / 0 | 504 / 0 | 7,938 / 0 | 300 / 0 |
| D03 | default | 46,690 / 0 | 19,123 / 0 | 15,457 / 0 | 1,516 / 0 | 456 / 0 | 7,958 / 0 | 300 / 0 |
| D03 | hard | 170,701 / 0 | 20,706 / 0 | 16,362 / 0 | 1,607 / 0 | 504 / 0 | 7,938 / 0 | 300 / 0 |
| D04 | default | 46,690 / 0 | 19,123 / 0 | 15,457 / 0 | 1,516 / 0 | 456 / 0 | 7,958 / 0 | 300 / 0 |
| D04 | hard | 170,701 / 0 | 20,706 / 0 | 16,362 / 0 | 1,607 / 0 | 504 / 0 | 7,938 / 0 | 300 / 0 |
| D05 | default | 46,690 / 0 | 19,123 / 0 | 15,457 / 0 | 1,516 / 0 | 456 / 0 | 7,958 / 0 | 300 / 0 |
| D05 | hard | 170,701 / 0 | 20,706 / 0 | 16,362 / 0 | 1,607 / 0 | 504 / 0 | 7,938 / 0 | 300 / 0 |

`PYTHONPATH=. /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.check > /tmp/r22-codex1/x4-check.log 2>&1` (exit 0, real 120.18 s). `ALL CHECKS PASSED in 120.1 s` Next: X5.

2026-11-22 05:48 codex1 — X5 at c8cfe6f (generator d0fbb34). Updated the text auditor: the completing ref credits the
invoice's converted total less the sum of earlier converted refs, using the invoice-date rate throughout.
Added `--scratch` to keep both the temporary exports and the grader key under /tmp/r22-codex1 for this run.

Old-rule witness: `PYTHONPATH=. AUDITENV_KEY_FILE=/tmp/r22-codex1/key /usr/bin/time -p env -u AUDITENV_SECRET uv run python /tmp/r22-codex1/x5_witness.py`
(exit 0, real 0.14 s). D01 seed 58001 hard: the old rule emitted a false `payment_allocation` of 1 GBP minor unit
for invoice F0753393 and payment PAY-564014 (ledger row L03921). `Old FP=1; updated FP=0`.

`PYTHONPATH=. AUDITENV_KEY_FILE=/tmp/r22-codex1/key /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r21.text_auditor --seeds 58000-58099 --scratch /tmp/r22-codex1 > /tmp/r22-codex1/x5.log 2>&1`
(exit 0, real 118.84 s). `Discrepancy entries: 0` Mean F1 1.000 in all 42 config/difficulty groups (4,200 episodes).

| Config | Difficulty | Scored | Mean F1 | Mean precision | Mean recall |
|---|---|---:|---:|---:|---:|
| baseline | default | 100 | 1.000000 | 0.990000 | 0.990000 |
| baseline | hard | 100 | 1.000000 | 0.980000 | 0.980000 |
| D01 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D01 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D02 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D02 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D03 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D03 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D04 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D04 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D05 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D05 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D06 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D06 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D07 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D07 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D08 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D08 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D09 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D09 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D10 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D10 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D11 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D11 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D12 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D12 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D13 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D13 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D14 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D14 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D15 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D15 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D16 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D16 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D17 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D17 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D18 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D18 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D19 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D19 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D20 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D20 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |

`PYTHONPATH=. /usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.check > /tmp/r22-codex1/x5-check.log 2>&1`
(exit 0, real 136.37 s). `ALL CHECKS PASSED in 136.3 s` No further codex1 assignments at this revision.
2026-11-22 05:46 codex2 — Y4 complete on c8cfe6f (generator d0fbb34). Policy audit indexes public remittance refs by invoice_id and payment instant, uses strictly earlier refs, and checks the completing credit as the converted total less the separately converted earlier refs. Chronology tests ordering and source-currency totals, so it required no code change.

- `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/policy_text.py --seeds 59000-59199` → exit 0 in 120.78 s. `OBSERVED completing_remittances: 24500`. `Audited 8400 episodes across 42 configurations; 33026869 checks, 0 unexpected failures.`
- `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 59000-59299` → exit 0 in 157.66 s. Summary and all dirty-scenario exceptions verbatim below.
- `env -u AUDITENV_SECRET uv run python -m auditenv.check` → exit 0 in 117.16 s, 565 tests. `ALL CHECKS PASSED in 117.1 s`.

```text
episodes checked: 12600 (seeds 59000-59299, 42 configs)
unexplained violations: 21 (0 in clean configs)
  default/default seed=59203 f_ar_before_booking ids=['RCPT0566178', 'F0470250', 'R4336'] ar credit 2026-02-02T12:35:00+01:00 booking 2026-02-02T17:32:00+01:00
  default/default seed=59217 f_ar_before_booking ids=['RCPT0471290', 'INV-184960', 'GL-000706'] ar credit 2026-12-02T18:37:00+05:00 booking 2026-12-04T19:01:00+05:00
  default/default seed=59217 f_ar_before_booking ids=['RCPT0924208', 'INV-184960', 'GL-000712'] ar credit 2026-12-03T11:29:00+05:00 booking 2026-12-04T19:01:00+05:00
  default/default seed=59268 f_ar_before_booking ids=['PAY-490822', '2610-096760', 'R1560'] ar credit 2026-10-02T10:11:00+05:30 booking 2026-10-03T19:52:00+05:30
  default/default seed=59294 f_ar_before_booking ids=['PAY-930048', '2601-145501', 'L00342'] ar credit 2026-01-01T22:40:00+05:00 booking 2026-01-03T14:35:00+05:00
  hard/hard seed=59029 f_ar_before_booking ids=['PAY-336392', 'INV-421168', 'R4183'] ar credit 2026-05-02T13:18:00+05:00 booking 2026-05-02T17:18:00+05:00
  hard/hard seed=59147 f_ar_before_booking ids=['BNK-975340', '2507-946254', 'L02117'] ar credit 2025-07-02T14:20:00+05:00 booking 2025-07-04T11:21:00+05:00
  D14/default seed=59029 f_ar_before_booking ids=['PAY-185794', 'F0858586', 'R4443'] ar credit 2026-04-02T14:57:00+05:30 booking 2026-04-02T19:08:00+05:30
  D14/default seed=59079 f_ar_before_booking ids=['PAY-965190', '2505-024697', 'R293'] ar credit 2025-05-02T13:31:00+05:00 booking 2025-05-04T18:47:00+05:00
  D14/default seed=59193 f_ar_before_booking ids=['BNK-626695', 'INV-503027', 'R1144'] ar credit 2025-02-01T11:22:00+03:00 booking 2025-02-02T10:11:00+03:00
  D14/default seed=59216 f_ar_before_booking ids=['RCPT0778160', '2601-862816', 'L02006'] ar credit 2026-01-01T19:50:00+09:00 booking 2026-01-04T12:53:00+09:00
  D14/hard seed=59064 f_ar_before_booking ids=['RCPT0155948', 'F0623287', 'R2178'] ar credit 2025-02-01T22:22:00+01:00 booking 2025-02-03T15:16:00+01:00
  D14/hard seed=59072 f_ar_before_booking ids=['RCPT0505170', 'INV-862826', 'GL-000545'] ar credit 2026-10-01T00:20:00-05:00 booking 2026-10-01T11:13:00-05:00
  D14/hard seed=59126 f_ar_before_booking ids=['PAY-665354', 'INV-499788', 'L03697'] ar credit 2026-01-04T09:55:00-03:00 booking 2026-01-04T14:05:00-03:00
  D15/default seed=59029 f_ar_before_booking ids=['PAY-185794', 'F0858586', 'R4443'] ar credit 2026-04-02T14:57:00+05:30 booking 2026-04-02T19:08:00+05:30
  D15/default seed=59079 f_ar_before_booking ids=['PAY-965190', '2505-024697', 'R293'] ar credit 2025-05-02T13:31:00+05:00 booking 2025-05-04T18:47:00+05:00
  D15/default seed=59193 f_ar_before_booking ids=['BNK-626695', 'INV-503027', 'R1144'] ar credit 2025-02-01T11:22:00+03:00 booking 2025-02-02T10:11:00+03:00
  D15/default seed=59216 f_ar_before_booking ids=['RCPT0778160', '2601-862816', 'L02006'] ar credit 2026-01-01T19:50:00+09:00 booking 2026-01-04T12:53:00+09:00
  D15/hard seed=59064 f_ar_before_booking ids=['RCPT0155948', 'F0623287', 'R2178'] ar credit 2025-02-01T22:22:00+01:00 booking 2025-02-03T15:16:00+01:00
  D15/hard seed=59072 f_ar_before_booking ids=['RCPT0505170', 'INV-862826', 'GL-000545'] ar credit 2026-10-01T00:20:00-05:00 booking 2026-10-01T11:13:00-05:00
  D15/hard seed=59126 f_ar_before_booking ids=['PAY-665354', 'INV-499788', 'L03697'] ar credit 2026-01-04T09:55:00-03:00 booking 2026-01-04T14:05:00-03:00
```

2026-11-22 05:49 codex2 — Y5 complete. Reviewed 7efcfb7 and swept the generator at d0fbb34. The expected AR credit is derivable from public documents, including prior-period invoices with no published AR debit. The formula uses nominal invoice-date value and independently converted earlier refs, including refs on unposted payments by rule. It groups by exact invoice_id, so duplicate documents and reissues never pool references. Published wording should explicitly define strictly earlier payment instants, clarify prior-period nominal amounts, and qualify exact closure for a tied final installment.

`PYTHONPATH=. env -u AUDITENV_SECRET uv run python /tmp/r22-codex2/completing_ref_review.py` → exit 0, 126.53 s, seeds 0–999 × default/hard/D01–D20 in both difficulties. Counts are scenario executions, with some identical configurations. Credit note means an invoice-level 1200 reversal; reissues and duplicate candidates use a public same-content signature (hard mode normalized text), with credit-noted originals separated.

| Case | Count |
|---|---:|
| completing | 124,905 |
| rounding change | 12,099 |
| tied instant groups | 3 |
| tied full installments | 3 |
| multiple completing refs | 0 |
| out-of-period completing | 0 |
| earlier out-of-period refs | 0 |
| prior-period invoices without AR debit | 375,755 |
| prior-period completing without AR debit | 33,357 |
| credit notes | 52,607 |
| completing credit note | 0 |
| reissues | 52,607 |
| completing reissue | 0 |
| duplicate candidates | 15,280 |
| completing duplicate candidate | 559 |
| overpayment full refs | 198,657 |
| completing overpayment full refs | 0 |
| posting mismatch | 0 |

Checked 42000 episodes and 124905 completing refs; 3 tied full installments, 0 multiple-completion groups, 0 posting mismatches.

The three tied installments were the same base-currency case under D06–D08. They jointly reached the total and each ref had its ordinary credit, so the invoice closed. No sampled tie produced a nonzero residual. A foreign synthetic tie can leave one minor unit without leaving the credit rule ambiguous.

```text
CASE D06/default (877, 'completion tie', 'SI-2025-283512', '2025-01-18T22:58:00+00:00', 0, 128700, [('RCPT0967996', 55219), ('RCPT0192502', 73481)])
CASE D07/default (877, 'completion tie', 'SI-2025-283512', '2025-01-18T22:58:00+00:00', 0, 128700, [('RCPT0967996', 55219), ('RCPT0192502', 73481)])
CASE D08/default (877, 'completion tie', 'SI-2025-283512', '2025-01-18T22:58:00+00:00', 0, 128700, [('RCPT0967996', 55219), ('RCPT0192502', 73481)])
D06/default seed=877 invoice_id=SI-2025-283512 instant=2025-01-18T22:58:00+00:00 USD->USD rate=1; nominal=128700, credits={'RCPT0967996': [('GL-000361', 55219)], 'RCPT0192502': [('GL-000356', 73481)]}, prior posted credit=0, nominal less credits=0
D07/default seed=877 invoice_id=SI-2025-283512 instant=2025-01-18T22:58:00+00:00 USD->USD rate=1; nominal=128700, credits={'RCPT0967996': [('GL-000361', 55219)], 'RCPT0192502': [('GL-000356', 73481)]}, prior posted credit=0, nominal less credits=0
D08/default seed=877 invoice_id=SI-2025-283512 instant=2025-01-18T22:58:00+00:00 USD->USD rate=1; nominal=128700, credits={'RCPT0967996': [('GL-000361', 55219)], 'RCPT0192502': [('GL-000356', 73481)]}, prior posted credit=0, nominal less credits=0
Synthetic same-instant P2/P3: no single completing ref under strict instant order; 153 credits vs 152 nominal debit, so 1 minor unit remains. An arbitrary row-order tie-break would change which ref gets 50.
Synthetic prior invoice: nominal 152, earlier out-of-period ref 101 converting to 51, in-period final ref 202 posting 101. The public nominal invoice amount and prior reference suffice without an in-period invoice debit.
```

Proposed exact replacement for the completing-reference clause in CONTRACT §2 and policy.json ledger.payment:

> For each invoice_ref on an in-period payment, group public references by exact invoice_id. Earlier references are those on any payment whose timestamp is strictly earlier as an instant, including out-of-period payments. Use the invoice's company-local issue-date rate and round each conversion to base minor units with ROUND_HALF_UP. If there is at least one earlier reference and its source amount plus those of the other earlier references and the current reference equals the invoice total_minor, credit 1200 with convert(total_minor) minus the sum of the separately converted earlier references. Use the invoice document total even if no original debit appears in the public ledger. Otherwise credit the converted current reference. References on payments at the same instant do not count as earlier than one another. A final installment split across simultaneous payments can leave a rounding difference. The journal's balancing difference goes to 7900.
2026-11-22 05:42 gemini1b — G15 stress test on seeds 13000-13299:
Command 1: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 13000-13299` -> exit 0, wall time 8.70 s. Summary: `reconcile on 1200 default episodes (seeds 13000-13299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 32, truncated 0 (8.7 s)`
Command 2: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 13000-13299` -> exit 0, wall time 21.51 s. Summary: `reconcile_hard on 1200 hard episodes (seeds 13000-13299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 59, truncated 0 (21.5 s)`
Task G15 complete.
2026-11-22 05:48 gemini2b — G17 complete (final generator d0fbb34+).
- Re-exported all three splits into scratch dirs /tmp/r22-gemini2b/final/{dev,train,hard} via auditenv.export and diffed against committed episodes:
  - diff dev exit: 0
  - diff train exit: 0
  - diff hard exit: 0
- scripts/golden.py --check: exit 0 ("All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2b/tests/golden_hashes.json.")
- scripts/mutate_reward.py: exit 0 ("22/22 mutants killed.").
2026-11-22 05:52 lead — Merged top-up results so far: codex1 X4 ledger_identity on the FIX2 rule → 0 clean violations on 41000–41299 and 57000–57299; X5 text auditor updated (old per-ref rule gave a 1-minor-unit FP, D01 hard seed 58001) → F1 1.000, 0 discrepancies on 58000–58099; codex2 Y4 policy_text 59000–59199 0 unexpected (24,500 completing remittances checked), chronology 59000–59299 0 unexplained in clean configs; Y5 FIX2 review: 124,905 completing refs, 0 posting mismatches, 0 out-of-period/credit-note/reissue completions; 3 same-instant final parts (base currency, closed anyway). Acted on Y5 wording: CONTRACT §2 and policy.json now say "strictly earlier timestamp, booked or not" and that two final parts at the same instant keep the per-ref rule. Re-exported (policy text), check exit 0, sync no drift, golden 80/80. PITCH/DEMO re-verified: demo seed 2003 output matches DEMO.md (326 rows, 69 invoices, 286 / 351 331, 0.958, 22 steps); PITCH hard-split facts (20 FP, 6 missed duplicates, 46 issues) re-derived with auditenv.analyze; 20,000-config fuzz for the "59 actions" claim running.

2026-11-22 05:51 codex2 — Y6 complete on final generator d0fbb34. Added `--seeds` with the original 55000–55009 range as the default. `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r22.paired_cleanroom --seeds 60000-60009` → exit 0 in 75.99 s. Both the official matrix and the combined shuffle-and-rename pass agreed for all 400 original/copy pairs. Oracle and reconcile/reconcile_hard F1 were 1.0000 throughout.

| Scenario | Reconcile original F1 / return | Combined copy F1 / return | Oracle original → copy | Combined equal | Matrix equal |
|---|---:|---:|---:|---:|---:|
| D01 | 1.0000 / 0.9397 | 1.0000 / 0.9397 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D02 | 1.0000 / 0.9397 | 1.0000 / 0.9397 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D03 | 1.0000 / 0.9397 | 1.0000 / 0.9397 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D04 | 1.0000 / 0.9397 | 1.0000 / 0.9397 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D05 | 1.0000 / 0.9397 | 1.0000 / 0.9397 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D06 | 1.0000 / 0.9365 | 1.0000 / 0.9365 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D07 | 1.0000 / 0.9365 | 1.0000 / 0.9365 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D08 | 1.0000 / 0.9365 | 1.0000 / 0.9365 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D09 | 1.0000 / 0.9410 | 1.0000 / 0.9410 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D10 | 1.0000 / 0.9395 | 1.0000 / 0.9395 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D11 | 1.0000 / 0.9405 | 1.0000 / 0.9405 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D12 | 1.0000 / 0.9398 | 1.0000 / 0.9398 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D13 | 1.0000 / 0.9398 | 1.0000 / 0.9398 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D14 | 1.0000 / 0.9411 | 1.0000 / 0.9411 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D15 | 1.0000 / 0.9411 | 1.0000 / 0.9411 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D16 | 1.0000 / 0.9410 | 1.0000 / 0.9410 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D17 | 1.0000 / 0.9410 | 1.0000 / 0.9410 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D18 | 1.0000 / 0.9410 | 1.0000 / 0.9410 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D19 | 1.0000 / 0.9388 | 1.0000 / 0.9388 | 1.0000 → 1.0000 | 20/20 | 20/20 |
| D20 | 1.0000 / 0.9388 | 1.0000 / 0.9388 | 1.0000 → 1.0000 | 20/20 | 20/20 |

Free-text locations searched: fx.csv.date, fx.csv.rate, fx.csv.source_currency, fx.csv.target_currency, invoices.jsonl.currency, invoices.jsonl.due_at, invoices.jsonl.issued_at, invoices.jsonl.line_items[].description, ledger.csv.account, ledger.csv.credit_minor, ledger.csv.currency, ledger.csv.debit_minor, ledger.csv.timestamp, manifest.json.base_currency, manifest.json.generator_version, manifest.json.period_end, manifest.json.period_start, manifest.json.rounding, manifest.json.schema_version, manifest.json.timezone, payments.jsonl.currency, payments.jsonl.timestamp, policy.json.base_currency, policy.json.findings.affected_ids.duplicate_invoice, policy.json.findings.affected_ids.fx_error, policy.json.findings.affected_ids.payment_allocation, policy.json.findings.affected_ids.period_cutoff, policy.json.findings.amount, policy.json.findings.evidence, policy.json.findings.tolerance, policy.json.fx.conversion, policy.json.fx.direction, policy.json.fx.rate_date, policy.json.ledger.accounts.1000, policy.json.ledger.accounts.1200, policy.json.ledger.accounts.2900, policy.json.ledger.accounts.4000, policy.json.ledger.accounts.6100, policy.json.ledger.accounts.6200, policy.json.ledger.accounts.6300, policy.json.ledger.accounts.6400, policy.json.ledger.accounts.7900, policy.json.ledger.credit_note, policy.json.ledger.currency, policy.json.ledger.expense, policy.json.ledger.invoice, policy.json.ledger.payment, policy.json.period.end, policy.json.period.rule, policy.json.period.start, policy.json.rounding, policy.json.timezone, task.txt
Embedded IDs: none found
Discrepancies: 0

The `--seeds 60009-60000` input exited 2 with `paired_cleanroom.py: error: reversed seed range '60009-60000'`. `env -u AUDITENV_SECRET uv run python -m auditenv.check` → exit 0 in 86.68 s, 565 tests. `ALL CHECKS PASSED in 86.6 s`.
2026-11-22 05:50 gemini1a — G14: ran `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 18000-18999` (exit 0, wall time 128.00 s: default mode, seeds 18000-18999: 3000 episodes (1986 dirty, 1014 clean) in 127.9 s; problems: 0; FUZZ PASSED) and `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 18000-18999 --hard` (exit 0, wall time 298.81 s: hard mode, seeds 18000-18999: 3000 episodes (1989 dirty, 1011 clean) in 298.8 s; problems: 0; FUZZ PASSED). 0 problems found across 6,000 episodes on final generator. Task G14 complete.
2026-11-22 05:55 gemini3a — G18 done: Jury modules twice, attack search, sensitivity comparison on final generator (d0fbb34). (1) Four jury modules twice: Run 1 Ran 73 tests in 2.357s, OK (wall 2.429s, exit 0); Run 2 Ran 73 tests in 2.465s, OK (wall 2.529s, exit 0). (2) env -u AUDITENV_SECRET uv run python -m auditenv.attack (exit 0, wall 0.417s): "=== HANDOFF R1 Automated Attack Search: PASSED ===", 20 seeds (5 clean, 15 dirty), 11,000 mutations, 0 violations. (3) uv run python scripts/sensitivity.py (exit 0, wall 2.172s): default parameters reproduced every env reward; dev & hard rankings invariant under step costs (0.001, 0.002, 0.005) and tolerances (0, 1, 100). Comparison with docs/DESIGN.md §6 "Sensitivity" table: all values match byte-for-byte at 3 decimal places (dev: oracle 1.000, reconcile 0.978/0.956/0.891, naive_reconcile -0.465/-0.478/-0.517, random -0.803/-0.807/-0.817, flag_all -1.000; hard: oracle 1.000, reconcile_hard 0.958/0.916/0.790, reconcile 0.329/0.293/0.186, naive_reconcile -0.683/-0.704/-0.765); 0 differences called out.
2026-11-22 05:59 rb — Z4 done: re-checks on the final generator (HEAD 58bd488, includes FIX a8538c7, FIX2 and the
Y5 completing-ref wording f713586/58bd488). Merged origin/night/2026-11-22-r22 (fast-forward). All commands from
repo root; full logs in /tmp/r22-rb/z4_*.log.
- `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py` — exit 0, 4 s wall.
  Summary: "Z1: 20 scenarios x 2 difficulties x 5 seeds (32000-32004) x 2 policies = 400 closed runs through
  judge_adapter, 4.3 s total". FLAGS (0): none. Every scenario×difficulty row: reconcile/reconcile_hard mean F1
  1.000, min F1 1.000; flag_all mean return −1.000 everywhere (never > 0, never > −0.5). Max steps 50 (D06–D08
  hard), max episode time 0.013 s.
  Call-out (Z2 criterion, same as Z2 on FIX): 23 NOTES where per-scenario mean return is below the README
  20-scenario mean 0.959 — hard rows 0.914–0.922 and default D06–D08 0.956. Adapter's own note explains it:
  "README value is a 20-scenario mean, per-scenario return varies with inspection cost 0.002/step"; F1 is 1.000
  in all of them, so this is expected per-scenario variance, not a regression.
- `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.extreme_configs` — exit 0, 11 s wall.
  Summary: "Outcomes: {'valid': 300, 'rejected': 72, 'failure': 0}. Total: 372." All 72 rejections are the
  expected "ValueError: at most 12 issues per episode" guard. All 300 valid configs: exact issue counts,
  reconcile F1=1.0 (0 valid rows with F1 != 1.0).
- `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.jury_copy` — exit 0, 1 s wall.
  10 rewrite variants (CSV columns shuffled, CRLF, CSV/JSON/JSONL BOM, no final newline, pretty/compact JSON,
  JSONL keys reversed, combined) × 10 reference episodes: Accepted 10, Rejected 0, Scores equal 10 each.
  Summary: "Semantically equivalent rewrite discrepancies: 0".
- `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 32000` — exit 0, 2 s wall.
  Seeds 32001–32020: random_explorer F1 0.000 return −1.000; reconcile F1 1.000 return 0.960 (max 25 steps);
  flag_all F1 0.000 return −1.000; oracle F1 1.000 return 1.000. No Z1 call-outs (oracle/reconcile F1 = 1,
  random/flag_all return ≤ −0.5).
- `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 33000` — exit 0, 2 s wall.
  Seeds 33001–33020: identical policy table (reconcile 1.000/0.960, max 24 steps; oracle 1.000/1.000;
  random_explorer and flag_all −1.000). No Z1 call-outs.
Assumption: "final generator" = current origin/night/2026-11-22-r22 HEAD at merge time (58bd488); scenarios_adapter
uses its built-in seed base 32000–32004 (no flag needed). No product code touched; only night/TASKS.md (Z4 [x])
and this log.
