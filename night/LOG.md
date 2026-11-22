2026-11-22 05:00 lead — Round 22 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/CASE_UPDATES/r20–r21 archive. Baseline check at 774570d: exit 0, 50.6 s. Decision: fix the round-21 refund FX artefact at the root (refund Dr 2900 at the rate of the receipt it returns, difference to 7900). Reason: every jury clean episode D01–D05 is generated with ensure_distractors and so contains a refund; a foreign one leaves the customer's 2900 below zero in base currency, which a jury "accounting equalities" check on clean books can fail (up to 5 × 1.25 points). Round 21 deferred it only for time; ~13 h remain and the change follows the round-20 re-export path. Rounding residue on AR (a few minor units) stays documented. Wrote TASKS.md: codex1 clean-room D-matrix + ledger_identity/text_auditor after FIX; codex2 clean-room paired transform + policy_text/chronology update + rule-ambiguity review; rb jury_run/scenarios; gemini sweeps gated on the FIX commit.

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
