# Round 14
- [x] T1 (lead) Surface actionable unit-test failures in the official command — files: auditenv/check.py, tests/test_check_failures.py, REVIEW.md — accept: injected synthetic failure names test and assertion; official check passes.
- [x] T2 (gemini1) Correct public smoke versus withheld cohort wording — files: docs/CHECKS.md — accept: verify seeds and policy against run_remote.
- [x] T3 (gemini2) Check README closed-run instructions against real CLI and clarify public smoke scope — files: README.md — accept: public two-episode smoke passes.
- [ ] T4 (gemini3) Verify public split metrics tables against measured JSON — files: docs/DESIGN.md only if drift — accept: sync_docs --check.
- [x] T5 (lead) Verify generator hashes and exported splits — files: no product files — accept: golden check and all three verify --dir commands pass.
- [x] T8 (lead) Preserve alternative evidence under paired relabelling — files: auditenv/check.py, tests/test_paired_transform.py, REVIEW.md — accept: dropping a valid alternative fails the paired gate.
- [x] T6 (lead) Rehearse numbered 2–3 minute video script — files: docs/DEMO.md — accept: five prompts and closed grader result match.
- [x] T7 (lead) Review pitch slide sequence and measurements — files: docs/PITCH.md — accept: metrics match official check and all SPEC sections reviewed.
