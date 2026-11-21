# Round 19

Use Python 3.11 via uv. For evidence tasks append measured counts and any mismatch to night/LOG.md. Escalate mismatches to lead.

- [x] gemini1a-1 (gemini1a) Verify public train/dev exports — files: night/LOG.md — accept: `uv run python -m auditenv.verify --dir episodes/train` exits zero and count recorded.
- [ ] gemini1a-2 (gemini1a) Verify public train/dev exports — files: night/LOG.md — accept: `uv run python -m auditenv.verify --dir episodes/dev` exits zero and count recorded.
- [ ] gemini1b-1 (gemini1b) Verify hard exports and golden records — files: night/LOG.md — accept: `uv run python -m auditenv.verify --dir episodes/hard` exits zero and count recorded.
- [ ] gemini1b-2 (gemini1b) Verify hard exports and golden records — files: night/LOG.md — accept: `uv run python -m unittest tests.test_golden` exits zero and count recorded.
- [ ] gemini2a-1 (gemini2a) Verify trajectories and public replay — files: night/LOG.md — accept: `uv run python -m unittest tests.test_trajectory_files` exits zero and count recorded.
- [ ] gemini2a-2 (gemini2a) Verify trajectories and public replay — files: night/LOG.md — accept: `uv run python -m unittest tests.test_run` exits zero and count recorded.
- [ ] gemini2b-1 (gemini2b) Verify published jury maps and examples — files: night/LOG.md — accept: `uv run python -m unittest tests.test_checks_map` exits zero and count recorded.
- [ ] gemini2b-2 (gemini2b) Verify published jury maps and examples — files: night/LOG.md — accept: `uv run python -m unittest tests.test_readme_snippets` exits zero and count recorded.
- [ ] gemini3a-1 (gemini3a) Verify reward boundary and mutation coverage — files: night/LOG.md — accept: `uv run python -m unittest tests.test_judge_reward` exits zero and count recorded.
- [ ] gemini3a-2 (gemini3a) Verify reward boundary and mutation coverage — files: night/LOG.md — accept: `uv run python -m unittest tests.test_mutate_reward` exits zero and count recorded.
- [ ] gemini3b-1 (gemini3b) Verify paired replay and independent transforms — files: night/LOG.md — accept: `uv run python -m unittest tests.test_judge_paired` exits zero and count recorded.
- [ ] gemini3b-2 (gemini3b) Verify paired replay and independent transforms — files: night/LOG.md — accept: `uv run python -m unittest tests.test_paired_transform` exits zero and count recorded.
- [ ] codex2-1 (codex2) Verify accounting scenario and ledger invariants — files: night/LOG.md — accept: `uv run python -m unittest tests.test_judge_scenarios` exits zero and count recorded.
- [ ] codex2-2 (codex2) Verify accounting scenario and ledger invariants — files: night/LOG.md — accept: `uv run python -m unittest tests.test_allocation_posting tests.test_payment_entities` exits zero and count recorded.
- [ ] rb-1 (rb) Verify schema and baseline compatibility — files: night/LOG.md — accept: `uv run python -m unittest tests.test_schemas` exits zero and count recorded.
- [ ] rb-2 (rb) Verify schema and baseline compatibility — files: night/LOG.md — accept: `uv run python -m unittest tests.test_jury_run` exits zero and count recorded.
- [ ] K1 (codex1) Use private grader key by default for hidden server queues including abandonment and startup validation, preserve explicit public runs and existing configured secret behavior. Test first — files: auditenv/server.py, auditenv/env.py, judge_adapter.py, auditenv/grader_key.py, tests/test_server_secret.py, tests/test_server*.py — accept: server and grader key tests pass with isolated key location; no key in policy channels.
- [ ] K2 (codex1) Audit internal server callers for explicit public fixtures; adjust as needed — files: auditenv/check.py, auditenv/jury_run.py, tests/test_check_failures.py — accept: public remote baseline check passes.
- [ ] F (lead) Correct ordinary refund chronology, including clean default books seed 0 — files: generator, regression tests, generated artifacts and derived metrics — accept: causal ordering on default and hard sweeps, all derived artifacts verified.
- [ ] R (lead) Review results, closed-server documentation and SPEC acceptance — files: README.md, docs/CONTRACT.md, REVIEW.md, HANDOFF.md — accept: full check, fuzz, reward search, miner and docs sync verified.
- [x] D (lead) Verify numbered recording script against actual demo — files: docs/DEMO.md — accept: timed demo fits 2–3 minute script.
- [x] P (lead) Verify slide outline and numbers — files: docs/PITCH.md — accept: slide facts match current code and measured results.
