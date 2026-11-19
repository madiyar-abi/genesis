# Round 7

- [ ] T1 (gemini1) Cross-check the published chart against measured dev and hard tables and correct any discrepancy — files: docs/baselines.svg, scripts/chart.py — accept: regenerate chart from official check metrics and compare all plotted values.
- [ ] T2 (gemini2) Check payment posting entity identity in generated books — files: tests/test_payment_entities.py — accept: independently compare payment ledger entity IDs with their payment documents across 100 heavy seeds per difficulty, record counts and a reproduction command in LOG.
- [ ] T3 (gemini3) Audit README offline reproduction instructions — files: README.md — accept: run documented local quick start and verify Docker instructions against Dockerfile and CI, correct stale directions.
- [ ] T4 (deepseek) Audit the jury evidence map against discovered tests — files: docs/CHECKS.md — accept: resolve each referenced test and correct stale mappings, run referenced verifier test module.
- [ ] T5 (lead) Reject unidentified receipts and refunds posted to the wrong account — files: auditenv/verify.py, tests/test_verify.py, REVIEW.md — accept: regression fails before and passes after, full check and seed sweep green.
- [ ] T6 (lead) Rehearse the numbered 2–3 minute video script — files: docs/DEMO.md — accept: public seed 2003 walkthrough matches each shown result.
- [ ] T7 (lead) Check slide outline against integrated metrics — files: docs/PITCH.md — accept: ten slides with matched results and accurate reproduction commands.
