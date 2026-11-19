# Auditenv pitch outline

## 1. How can we score an audit finding?

- An invoice can look like a duplicate even when a credit note reverses the original booking.
- To evaluate an auditor, we need to know which entries are wrong, by how much, and which records establish the error.

## 2. A synthetic company with a verifiable answer

- The generator builds balanced books, injects configured errors, and records each change.
- A policy investigates the public records and submits findings with evidence IDs. The grader checks each finding against the recorded discrepancy.
- The same company can be replayed with different policies.

## 3. Live demo

- Run `env -u AUDITENV_SECRET uv run python -m auditenv.demo --seed 2003`. Follow the scripted policy as it pages through ledger entries and submits four findings.
- Show the training result. All four findings match. After 21 inspection steps, the return is 0.958.
- Show the closed run. Over 22 actions including submission, the policy receives only zero rewards and ends with empty info. The separate grader records four true positives and zero false positives or misses.

## 4. From company history to evidence

- Each episode can contain duplicate invoices, missing or partial payment allocations, FX conversion errors, and period cutoff errors.
- One scenario partially allocates a period-end foreign payment and converts its cash entry at the wrong day’s rate. Another backdates a next-period foreign invoice and converts it using a rate from the booking date or an earlier day.
- Clean books include split payments, refunds, and recurring charges. Hard episodes add credit-note reissues and retyped invoice lines.
- The verifier independently derives discrepancies from the records and checks the evidence cited for each issue. It also rejects books that break the published posting policy, such as an account used outside its journal type or a mislabelled customer.

## 5. How the environment runs

- Python 3.11 and its standard library implement a JSON reset/step interface. The policy and closed grader communicate across processes.
- The policy can list up to 50 records per page, retrieve a record or document, and calculate with decimals. Submission ends the episode.
- The default limits are a 100-action budget including submission and a 60-second time limit.
- For private evaluation, a grader-held secret keys episode generation and the public episode identifier.

## 6. How the grader scores an answer

- A match requires the correct issue type, affected IDs, currency, amount, and one complete evidence set. The amount tolerance in minor units is `max(1, expected_minor // 1000)`.
- Each truth issue matches once. Repeated findings count as false positives.
- Terminal return is `clip(2 × F1 − 1 − 0.002 × inspection_steps, −1, 1)`. Invalid submissions score −1. On clean books, an empty answer has F1 of 1.
- On the demo company, repeating every oracle finding in one submission earns 0.333. Flagging everything earns −1.

## 7. Results

Show `docs/baselines.svg` on the slide. The table gives micro-averaged precision, recall, and F1, plus mean episode return, on 10 dev and 20 hard episodes.

| policy | split | P | R | F1 | return |
|---|---|---|---|---|---|
| oracle (grader-side) | dev | 1.000 | 1.000 | 1.000 | 1.000 |
| reconcile (policy-aware) | dev | 1.000 | 1.000 | 1.000 | 0.957 |
| naive reconcile | dev | 0.169 | 0.700 | 0.273 | −0.506 |
| random explorer | dev | 0.000 | 0.000 | 0.000 | −0.807 |
| flag-everything | dev | 0.000 | 0.000 | 0.000 | −1.000 |
| reconcile_hard | hard | 1.000 | 1.000 | 1.000 | 0.916 |
| reconcile (default) | hard | 0.651 | 0.891 | 0.752 | 0.288 |
| oracle (grader-side) | hard | 1.000 | 1.000 | 1.000 | 1.000 |

- Both reconciliation policies averaged 43.2 actions on hard episodes. The default rules produced 22 false positives and missed five findings. With line normalization and credit-note handling, the policy found all 46 issues with zero false positives.

## 8. How the jury can reproduce the checks

- Run `env -u AUDITENV_SECRET uv run python -m auditenv.check` for tests, independent verification, baseline comparisons, paired episodes, and the closed-process check.
- Paired checks cover 20 default and 20 hard episodes. They replay actions and compare oracle results after IDs and row order change.
- Run `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 20000` to vary company size, error mix and difficulty. Across 20,000 cases, including 8,037 hard cases, the verifier reported zero problems. The oracle and the rule policy for each difficulty reached F1 1.0 within 59 actions.
- A separate mutation test, `uv run python scripts/mutate_reward.py`, caught 15 of 15 deliberately introduced matcher and reward changes.

## 9. Limits and next experiment

- The simulator covers synthetic receivables and uses fixed UTC offsets. Its benchmark measures performance on the generated cases.
- The reported baselines are scripted. A next experiment would compare a learned policy with these baselines on held-out companies under the same investigation budget.

## 10. Team

- [Add confirmed team member names and each person’s contribution before exporting the deck.]
- Genesis Hackathon 2026, FinTech case.
