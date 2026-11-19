# Pitch outline (one heading = one slide)

Numbers come from `uv run python -m auditenv.check` / `auditenv.analyze` on the dev split
(10 episodes, seeds 2000–2009) unless stated otherwise. Re-run before the final slides.

## 1. Problem
- AI auditors need practice on books with known, verifiable errors — real ledgers can't be shared
  and have no answer key.
- Reward functions for audit are easy to game: flag everything, guess ids, write a persuasive story.
- RL needs thousands of reproducible episodes with a grader that can't leak the answer.

## 2. Solution: auditenv
- Reproducible RL environment: synthetic company → correct double-entry books → injected errors
  with a recorded cause.
- Agent reads records only through 5 narrow tools (`reset/step`, JSON, 100 steps, 50 rows/page).
- Published matcher + terminal reward `clip(2·F1 − 1 − 0.002·steps, −1, 1)`; findings need the
  right type, ids, amount, currency **and** evidence.
- Python 3.11 standard library, zero dependencies, one check command, Dockerfile.

## 3. Live demo
- `uv run python -m auditenv.check` → all gates pass in ~8 s.
- `uv run python -m auditenv.demo` → company → investigation → findings → reward 0.958.
- Same books, other answers: silence −1, guessed ids −1, repeated answer 0.33, flag-everything −1.
- Closed run in a separate process: the policy sees reward 0, the grader log has the score.

## 4. What's hard in the data
- 4 independently configurable error types: duplicate invoice, missing/partial payment allocation,
  wrong FX date, period cutoff; 2 interacting scenarios (partial foreign payment at the period end;
  backdated foreign invoice at the wrong rate).
- Clean companies plus legitimate look-alikes: split/partial payments, refunds, unidentified receipts,
  weekly retainers with equal amounts, documents near midnight in other timezones.
- Ids, id formats, order, amounts, 6 currencies (incl. 0-decimal JPY) and 8 timezones vary per episode.
- Naive reconciliation: micro-F1 0.286, 102 false positives (22 on clean books), 0/2 on the interacting
  payment case; policy-aware reconciliation: F1 1.0 → solvable from the evidence, not by shortcuts.

## 5. How it works
- `generator` (history → ledger → inject → render) · `env` (tools, limits, modes) ·
  `matcher` (validate → normalise → one-to-one match → reward) · `verify` · `transform` · `server`.
- Truth + provenance are grader-only files; `eval` mode and the out-of-process server keep reward
  and diagnostics away from the policy; a grader-only key (`AUDITENV_SECRET`) makes hidden seeds unrecoverable.
- Independent verifier: revert the recorded changes → 0 discrepancies; re-apply → exactly the
  declared ones, recomputed from public records.

## 6. Results
- Checks: 187 unit tests (incl. a 3 000-action fuzz test); verifier 600/600 episodes valid; 20/20 paired checks (replay exact;
  relabel + permute keeps the oracle reward).
- Dev split (micro P/R/F1, mean return): oracle 1.0/1.0/1.0, 1.000 · reconcile 1.0/1.0/1.0, 0.957 ·
  naive 0.18/0.73/0.29, −0.488 · random 0/0/0, −0.807 · flag-all 0/0/0, −1.000.
- Reconcile stress test: 1 200 episodes, 0 imperfect, ≤ 30 steps → every error is findable in budget.
- 12 attack tests from the case (silence, false accusations, duplicates, flag-all, step cost, guessed
  ids, bad evidence, wrong currency, resubmit, malformed input, timeout, tolerance) all pass.

## 7. What's next
- More error families (payables, accruals, tax) and near-duplicate documents.
- Difficulty curriculum: bigger ledgers, more distractors, tighter budgets.
- Train a small local model against the environment and report a held-out comparison.
- Honest limits: synthetic data, receivables only, fixed UTC offsets, public generator needs secret seeds.

## 8. Team
- [names, roles — fill in]
- Built in 3.5 days for the Genesis Hackathon 2026, FinTech case.
