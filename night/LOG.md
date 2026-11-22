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
