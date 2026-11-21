# Round 19

Use Python 3.11 via uv. For evidence tasks append measured counts and any mismatch to night/LOG.md. Escalate mismatches to lead.

- [x] gemini1a-1 (gemini1a) Verify public train/dev exports — files: night/LOG.md — accept: `uv run python -m auditenv.verify --dir episodes/train` exits zero and count recorded.
- [x] gemini1a-2 (gemini1a) Verify public train/dev exports — files: night/LOG.md — accept: `uv run python -m auditenv.verify --dir episodes/dev` exits zero and count recorded.
- [x] gemini1b-1 (gemini1b) Verify hard exports and golden records — files: night/LOG.md — accept: `uv run python -m auditenv.verify --dir episodes/hard` exits zero and count recorded.
- [x] gemini1b-2 (gemini1b) Verify hard exports and golden records — files: night/LOG.md — accept: `uv run python -m unittest tests.test_golden` exits zero and count recorded.
- [x] gemini2a-1 (gemini2a) Verify trajectories and public replay — files: night/LOG.md — accept: `uv run python -m unittest tests.test_trajectory_files` exits zero and count recorded.
- [x] gemini2a-2 (gemini2a) Verify trajectories and public replay — files: night/LOG.md — accept: `uv run python -m unittest tests.test_run` exits zero and count recorded.
- [x] gemini2b-1 (gemini2b) Verify published jury maps and examples — files: night/LOG.md — accept: `uv run python -m unittest tests.test_checks_map` exits zero and count recorded.
- [x] gemini2b-2 (gemini2b) Verify published jury maps and examples — files: night/LOG.md — accept: `uv run python -m unittest tests.test_readme_snippets` exits zero and count recorded.
- [x] gemini3a-1 (gemini3a) Verify reward boundary and mutation coverage — files: night/LOG.md — accept: `uv run python -m unittest tests.test_judge_reward` exits zero and count recorded.
- [x] gemini3a-2 (gemini3a) Verify reward boundary and mutation coverage — files: night/LOG.md — accept: `uv run python -m unittest tests.test_mutate_reward` exits zero and count recorded.
- [x] gemini3b-1 (gemini3b) Verify paired replay and independent transforms — files: night/LOG.md — accept: `uv run python -m unittest tests.test_judge_paired` exits zero and count recorded.
- [x] gemini3b-2 (gemini3b) Verify paired replay and independent transforms — files: night/LOG.md — accept: `uv run python -m unittest tests.test_paired_transform` exits zero and count recorded.
- [x] codex2-1 (lead) Verify accounting scenario and ledger invariants — files: night/LOG.md — accept: `uv run python -m unittest tests.test_judge_scenarios` exits zero and count recorded.
- [x] codex2-2 (lead) Verify accounting scenario and ledger invariants — files: night/LOG.md — accept: `uv run python -m unittest tests.test_allocation_posting tests.test_payment_entities` exits zero and count recorded.
- [x] rb-1 (rb) Verify schema and baseline compatibility — files: night/LOG.md — accept: `uv run python -m unittest tests.test_schemas` exits zero and count recorded.
- [x] rb-2 (rb) Verify schema and baseline compatibility — files: night/LOG.md — accept: `uv run python -m unittest tests.test_jury_run` exits zero and count recorded.
- [x] K1 (lead) Use private grader key by default for hidden server queues including abandonment and startup validation, preserve explicit public runs and existing configured secret behavior. Test first — files: auditenv/server.py, auditenv/env.py, judge_adapter.py, auditenv/grader_key.py, tests/test_server_secret.py, tests/test_server*.py — accept: server and grader key tests pass with isolated key location; no key in policy channels.
- [x] K2 (lead) Audit internal server callers for explicit public fixtures; adjust as needed — files: auditenv/check.py, auditenv/jury_run.py, tests/test_check_failures.py — accept: public remote baseline check passes.
- [x] F (lead) Correct ordinary refund chronology, including clean default books seed 0 — files: generator, regression tests, generated artifacts and derived metrics — accept: causal ordering on default and hard sweeps, all derived artifacts verified.
- [ ] gemini1a-3 (gemini1a) Verify verifier seeds 0-199 — files: night/LOG.md — accept: `uv run python -m auditenv.verify --seeds 0-199` exits zero and count recorded.
- [ ] gemini1a-4 (gemini1a) Verify export atomic replace on failure — files: night/LOG.md — accept: `uv run python -m unittest tests.test_export` exits zero and count recorded.
- [ ] gemini1b-3 (gemini1b) Verify posting period integrity — files: night/LOG.md — accept: `uv run python -m unittest tests.test_posting_period` exits zero and count recorded.
- [ ] gemini1b-4 (gemini1b) Verify payment refs and entities — files: night/LOG.md — accept: `uv run python -m unittest tests.test_payment_refs` exits zero and count recorded.
- [ ] gemini2a-3 (gemini2a) Verify doc commands and links — files: night/LOG.md — accept: `uv run python -m unittest tests.test_doc_links tests.test_doc_commands` exits zero and count recorded.
- [ ] gemini2a-4 (gemini2a) Verify hashseed determinism — files: night/LOG.md — accept: `uv run python -m unittest tests.test_hashseed` exits zero and count recorded.
- [ ] gemini2b-3 (gemini2b) Verify calculator and FX identity — files: night/LOG.md — accept: `uv run python -m unittest tests.test_calculator tests.test_fx_identity` exits zero and count recorded.
- [ ] gemini2b-4 (gemini2b) Verify clock injection and budget — files: night/LOG.md — accept: `uv run python -m unittest tests.test_clock` exits zero and count recorded.
- [ ] gemini3a-3 (gemini3a) Verify reward sensitivity — files: night/LOG.md — accept: `uv run python -m unittest tests.test_sensitivity` exits zero and count recorded.
- [ ] gemini3a-4 (gemini3a) Verify attack mutations — files: night/LOG.md — accept: `uv run python -m unittest tests.test_reward_attacks` exits zero and count recorded.
- [ ] gemini3b-3 (gemini3b) Verify contract strictness and error codes — files: night/LOG.md — accept: `uv run python -m unittest tests.test_contract_strict tests.test_error_codes_doc` exits zero and count recorded.
- [ ] gemini3b-4 (gemini3b) Verify truth identity and manifests — files: night/LOG.md — accept: `uv run python -m unittest tests.test_truth_identity tests.test_manifest_counts` exits zero and count recorded.
- [ ] rb-3 (rb) Verify baseline simple behaviors — files: night/LOG.md — accept: `uv run python -m unittest tests.test_baselines_simple` exits zero and count recorded.
- [ ] rb-4 (rb) Verify eval diagnostics and metrics — files: night/LOG.md — accept: `uv run python -m unittest tests.test_eval_diagnostics tests.test_metrics` exits zero and count recorded.
- [x] R (lead) Review results, closed-server documentation and SPEC acceptance — files: README.md, docs/CONTRACT.md, REVIEW.md, HANDOFF.md — accept: full check, fuzz, reward search, miner and docs sync verified.
- [x] D (lead) Verify numbered recording script against actual demo — files: docs/DEMO.md — accept: timed demo fits 2–3 minute script.
- [x] P (lead) Verify slide outline and numbers — files: docs/PITCH.md — accept: slide facts match current code and measured results.
