# Round 11

- [x] T1 (lead) Preserve distinct configurations sharing a seed in failure analysis, with and without seed selection — files: auditenv/analyze.py, tests/test_analyze.py, REVIEW.md — accept: two same-seed entries both contribute to the report, missing explicit seeds still fail, unit and official checks pass.
- [ ] T2 (gemini1) Add deterministic action replay of all seven committed trajectory files against their training configs, with public secret environment isolated — files: tests/test_trajectory_files.py — accept: compare every observation, reward and termination flag, all reset records and episode boundaries; run the trajectory test module.
- [ ] T3 (gemini2) Verify measured hard-mode failure explanations with analyze on both reconciliation policies — files: night/LOG.md — accept: record exact commands, TP/FN by type and FP reason counts for both; compare docs/DESIGN.md and flag discrepancies.
- [ ] T4 (gemini3) Audit per-policy step counts and timing claims in jury materials against benchmark outputs and stated methodology — files: night/LOG.md — accept: list exact commands and reproducible step counts, identify any unsupported timing claim.
- [ ] T5 (deepseek) Check public export integrity against all three versioned configs — files: night/LOG.md — accept: regenerate splits in a temporary directory and diff all files, log command and counts.
- [x] T6 (lead) Verify the numbered 2–3 minute demo script against the public recording command — files: docs/DEMO.md — accept: match IDs, amounts, steps and scores.
- [ ] T7 (lead) Verify slide outline, run commands and metrics; sync jury documentation — files: docs/PITCH.md, docs/CHECKS.md, docs/DESIGN.md, README.md — accept: metrics sync passes and slide claims trace to measured results.
