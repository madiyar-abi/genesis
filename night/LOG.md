2026-11-20 04:16 lead — Published round 11 assignments. The repeated-seed reproduction uses two configs sharing seed 1. Use the public seed domain for artifact checks and the 18:00 local freeze.
2026-11-20 04:17 lead — T1 Failure reports now retain each configuration sharing a seed. The full and filtered report regressions failed before the fix and pass after it. Explicit seed ordering and missing-seed errors are preserved.
2026-11-20 04:17 lead — T6 The five Enter prompts in the 2:40 demo script reproduced the two PAY-136430 discrepancies, 21 inspections, four matches and a closed-run return of 0.958.
2026-11-20 04:17 lead — T5 The DeepSeek launcher reported a missing API key, so the lead reassigned its export check. For split/config pairs train/train, dev/dev and hard/eval_hard, ran env -u AUDITENV_SECRET uv run python -m auditenv.export --config "configs/$cfg.json" --out "$tmpdir/$split" and diff -qr "episodes/$split" "$tmpdir/$split". All 81 train, 81 dev and 161 hard files matched.
2026-11-20 04:22 gemini2 — T3 Verified measured hard-mode failure explanations using auditenv.analyze on configs/eval_hard.json for reconciliation policies. Exact commands and outputs:
1) `uv run python -m auditenv.analyze --policy reconcile --config configs/eval_hard.json`
- Metrics: P=0.651, R=0.891, F1=0.752, return=0.288, steps=43.2
- TP/FN by type: duplicate_invoice TP=3 FN=5 (recall 3/8 = 0.375), payment_allocation TP=12 FN=0 (recall 1.0), fx_error TP=15 FN=0 (recall 1.0), period_cutoff TP=11 FN=0 (recall 1.0)
- Scenario TP/FN: single TP=29 FN=5, I1 TP=6 FN=0, I2 TP=6 FN=0
- FP reasons: no_matching_issue=22 (total FP=22)
2) `uv run python -m auditenv.analyze --policy reconcile_hard --config configs/eval_hard.json`
- Metrics: P=1.000, R=1.000, F1=1.000, return=0.916, steps=43.2
- TP/FN by type: duplicate_invoice TP=8 FN=0 (recall 1.0), payment_allocation TP=12 FN=0 (recall 1.0), fx_error TP=15 FN=0 (recall 1.0), period_cutoff TP=11 FN=0 (recall 1.0)
- Scenario TP/FN: single TP=34 FN=0, I1 TP=6 FN=0, I2 TP=6 FN=0
- FP reasons: total FP=0
3) `uv run python -m auditenv.analyze --policy naive_reconcile --config configs/eval_hard.json`
- Metrics: P=0.105, R=0.630, F1=0.181, return=-0.711, steps=33.4
- TP/FN by type: duplicate_invoice TP=8 FN=0 (recall 1.0), payment_allocation TP=2 FN=10 (recall 0.167), fx_error TP=10 FN=5 (recall 0.667), period_cutoff TP=9 FN=2 (recall 0.818)
- Scenario TP/FN: single TP=24 FN=10, I1 TP=0 FN=6, I2 TP=5 FN=1
- FP reasons: no_matching_issue=234, wrong_amount=8, wrong_type=3, wrong_evidence=1 (total FP=246)
Comparison to docs/DESIGN.md: All hard-mode metrics in §9 (table metrics for all policies, plus the failure analysis text stating reconcile has duplicate recall 3/8, all other types 100%, and 22 false positives all no_matching_issue) match the measured analyze results with 0 discrepancies.
2026-11-20 04:24 lead — T3 Reviewed the hard split across both policies. Default reconciliation missed five duplicates and returned 22 unmatched false positives. The hard rules matched all 46 issues. Both averaged 43.2 actions.
