# Round 4

- [ ] T1 (gemini1) Reject incorrect combined document counts and apply size checks to actual records in _structure — files: auditenv/verify.py (only _structure), tests/test_manifest_counts.py — accept: seed 7 with documents=20 fails and original passes.
- [ ] T2 (lead) Make verify --dir reject empty and incomplete indexed splits and report unreadable episode files — files: auditenv/verify.py (CLI only), tests/test_verify_dir.py — accept: invalid splits exit nonzero and train/dev/hard pass.
- [ ] T3 (gemini2) Check all three public exports against fresh output recursively and record reproduction commands in the log — files: night/LOG.md — accept: 3 identical directories.
- [ ] T4 (gemini3) Check committed trajectories against fresh runner output, document any timing fields and reproducibility evidence — files: night/LOG.md — accept: compare every JSONL step on each split and record results.
- [ ] T5 (deepseek) Independently verify all 80 golden hashes and reward mutation checks on this branch — files: night/LOG.md — accept: both scripts pass and record counts.
- [x] T8 (lead) Verify quantity times unit price on each invoice line — files: auditenv/verify.py (Books), tests/test_verify.py — accept: seed 7 clean invoice with doubled quantity is rejected.
- [ ] T6 (lead) Rehearse the demo and verify timing cues and output — files: docs/DEMO.md — accept: five sections show scripted seed results.
- [ ] T7 (lead) Check pitch against current metrics and update inaccurate claims — files: docs/PITCH.md — accept: slide narrative and measured claims verified.
