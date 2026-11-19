# Pitch outline (one heading = one slide, 10 slides)

Numbers come from `uv run python -m auditenv.check`, `auditenv.analyze`, `auditenv.fuzz` and
`auditenv.demo` on the committed code (dev split = 10 episodes, seeds 2000–2009; hard split = 20
episodes, seeds 9100–9119). Re-run the check before exporting the final slides.

## 1. Problem: why an RL environment for audit
- AI auditors need practice on books with known, verifiable errors; real ledgers can't be shared
  and have no answer key.
- Audit rewards are easy to game: flag everything, guess ids, write a persuasive story.
- RL needs thousands of reproducible episodes and a grader that cannot leak the answer.

## 2. Solution: auditenv
- Synthetic company → correct double-entry books → errors injected as recorded changes → truth with evidence.
- The agent investigates only through 5 read-only tools and submits findings with evidence.
- One published matcher and reward; closed evaluation in a separate process.
- Python 3.11 standard library, zero dependencies, one check command, Docker (built and run in CI).

## 3. Architecture
- `generator` (history → ledger → inject → render) → `env` (reset/step, tools, limits, train/eval) →
  `matcher` (validate → normalise → one-to-one match → reward).
- Independent `verify` (revert the recorded changes → 0 discrepancies; re-apply → exactly the truth),
  `transform` (new ids + permuted rows), `server`/`client` (grader in another process).
- Truth and provenance are grader-only; `episode_id` is an HMAC; a grader-only key makes hidden seeds unrecoverable.

## 4. Generator: 4 errors, 2 interacting scenarios, clean books
- Duplicate invoice · missing/partial payment allocation · wrong FX date · period cutoff — each
  configurable by count; I1 (late partial foreign payment) and I2 (backdated foreign invoice at the wrong rate).
- Clean companies plus legitimate look-alikes: split/partial payments, refunds, unidentified receipts,
  weekly retainers with equal amounts, documents near midnight in other timezones.
- 6 currencies (incl. 0-decimal JPY), 8 timezones, randomised id formats, order and amounts.
- Opt-in hard mode: credit-note reissues, re-typed duplicates, 3× larger ledger.

## 5. Environment and contract (live demo here)
- `reset(seed, config) → (obs, info)`, `step(action) → (obs, reward, terminated, truncated, info)`, JSON only.
- `list_records` (≤ 50 rows, stable cursors), `get_record`, `get_document`, `calculator` (decimal
  arithmetic only), `submit`. 100 steps incl. submit, 60 s; every error costs a step.
- Demo: `uv run python -m auditenv.demo` → company → investigation → 4 findings → reward 0.958;
  the closed run: policy sees reward 0 and empty info, the grader log has the score.

## 6. Reward and matcher
- TP = type + canonical ids + currency + amount within max(1, 0.1 %) + one complete evidence set;
  one-to-one matching; repeats are FP.
- `reward = clip(2·F1 − 1 − 0.002·steps, −1, 1)`; invalid submission −1; F1 = 1 for silence on clean books.
- Same books, other answers (demo): silence −1, guessed ids −1, answer repeated twice 0.33,
  flag-everything −1; clean company: silence 1.0, guessed ids −1.

## 7. Results
- Dev split (micro P/R/F1 · mean return): oracle 1.0/1.0/1.0 · 1.000; reconcile 1.0/1.0/1.0 · 0.957;
  naive 0.17/0.70/0.27 · −0.506; random 0/0/0 · −0.807; flag-all 0/0/0 · −1.000.
- Naive rules: 103 false accusations (22 on clean books), allocation recall 1/8, I1 0/2 →
  distractors and timezones defeat shortcuts.
- Hard split: reconcile drops to 0.47/0.87/0.61 · −0.095 (45 false accusations); with the two policy rules
  (`reconcile_hard`) 1.0 · 0.917; oracle 1.0 → harder, still solvable.

## 8. Reproducibility and tests
- 231 unit tests incl. a 3 000-action fuzz test and `tests/test_jury.py` (the jury checklist as tests).
- Verifier 600/600 generated + 20/20 exported episodes; seed sweep 3 000 default + 600 hard episodes:
  0 exceptions, 0 verifier problems, oracle 1.0 everywhere, flag-all negative on all.
- 20/20 paired checks: replay is byte-exact; relabel + permute keeps the oracle answer and reward.
- Stress: 1 200 episodes (reconcile) and 1 200 hard (reconcile_hard): every error found within budget.

## 9. Team
- [names, roles — fill in]
- Built for the Genesis Hackathon 2026, FinTech case.

## 10. Q&A (backup)
- Limits: synthetic data, receivables only, fixed UTC offsets, no trained model; hidden runs need `AUDITENV_SECRET`.
- Next: payables/accruals/tax, near-duplicates with changed amounts, difficulty curriculum, a small
  local model trained against the environment with a held-out comparison.
- Links: repo README (one command), `docs/DESIGN.md` (results, examples, limitations), `REVIEW.md`.
