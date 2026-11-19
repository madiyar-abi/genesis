# Round 12

- [x] T1 (lead) Reject reversed seed ranges in evaluation commands — files: auditenv/{run,verify,fuzz,analyze,attack}.py, tests/test_seed_ranges.py — accept: previously green empty verifier invocation exits nonzero, valid lists and ranges retain order.
- [ ] T2 (gemini1) Audit the public config selections against SPEC §6 — files: night/LOG.md — accept: count clean and interacting episodes from generated truth for both 20-company evaluation splits.
- [x] T3 (gemini2) Verify the chart is reproducible from the current measurement inputs — files: night/LOG.md — accept: regenerate into a temporary file and compare to docs/baselines.svg.
- [x] T4 (gemini3) Check documented trajectory fields and terminal coverage — files: night/LOG.md — accept: report file, episode and terminal/truncation counts for each policy file and any missing required fields.
- [x] T5 (lead) Verify committed export directories independently — files: night/LOG.md — accept: verify --dir succeeds for train, dev and hard.
- [x] T8 (lead) Preserve active episode settings after rejected resets — files: auditenv/env.py, reset regression tests — accept: rejected config preserves eval isolation and remaining budget.
- [x] T6 (lead) Rehearse the numbered recording script — files: docs/DEMO.md, auditenv/demo.py, tests/test_demo.py — accept: reproduce the payment evidence, four matches and closed return with the printed commands.
- [x] T7 (lead) Verify slide outline and submission handoff — files: docs/PITCH.md, README.md, HANDOFF.md, auditenv/check.py, tests/test_paired_transform.py — accept: current metrics match slides, official check and SPEC review pass.
