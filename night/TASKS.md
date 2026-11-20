# Round 18

Workers record their evidence in night/LOG.md and mark their task here. Run from the repository root with AUDITENV_SECRET unset.

- [ ] T1 (gemini1) Verify the committed train export accounting data with the directory CLI and count invoices and payments across its companies — files: night/LOG.md — accept: all ten verify, record both counts.
- [ ] T2 (gemini2) Audit dev episode sizes against SPEC §03 suggested ranges — files: night/LOG.md — accept: record observed ledger and document min/max from the ten manifests and disclose exceptions.
- [ ] T3 (gemini3) Examine hard evaluation cohort composition — files: night/LOG.md — accept: independently count issue-free companies and scenario frequencies from committed provenance, reporting all 20 companies.
- [ ] T4 (deepseek) Verify all generator golden hashes — files: night/LOG.md — accept: scripts/golden.py --check exits zero.
- [ ] T5 (lead) Detect invoice booking legs posted at different instants — files: auditenv/verify.py, tests/test_verify_round18.py, REVIEW.md — accept: reproduce a false pass, reject it after the fix, and pass the full check.
- [x] T6 (lead) Rehearse the 2–3 minute demo script — files: docs/DEMO.md — accept: run the five prompts and compare amounts, steps and return.
- [ ] T7 (lead) Verify the jury slide outline — files: docs/PITCH.md — accept: compare metrics with fresh check JSON and run sync_docs --check.
