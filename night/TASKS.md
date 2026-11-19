# Round 6

- [ ] T1 (gemini1) Reject out-of-period postings in public and reverted journals using company-local dates, including a revenue credit moved to 2099 on clean seed 0 — files: auditenv/verify.py, tests/test_posting_period.py — accept: corruption rejected, clean and boundary examples pass.
- [ ] T2 (gemini2) Check whether I2 can use an earlier rate than the booking date. Correct the scenario description and verify against injector fallback — files: docs/CONTRACT.md, docs/DESIGN.md — accept: both descriptions cover actual date selection.
- [ ] T3 (gemini3) Align README I2 example with the implemented rate fallback, verify README check command and split descriptions — files: README.md — accept: claims agree with inject.py and check.py.
- [ ] T4 (deepseek) Verify generated FX row IDs and uniqueness of date/source/target keys on 100 heavy seeds in each difficulty; log exact command and result — files: night/LOG.md — accept: 200 episodes checked and any exceptions identified.
- [x] T5 (lead) Check public FX identity and reject ambiguous or incorrectly labelled rates — files: auditenv/verify.py (_structure only), tests/test_fx_identity.py — accept: label swap on a valid clean fixture is rejected and normal episodes pass.
- [x] T6 (lead) Rehearse numbered demo and verify both terminal outputs — files: docs/DEMO.md — accept: five pauses and narrated numbers match public replay.
- [x] T7 (lead) Correct pitch scenario and verify slide metrics — files: docs/PITCH.md — accept: ten slides, accurate I2 rate selection, synchronized measurements.
