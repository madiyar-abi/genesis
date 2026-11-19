# CHECKS.md — Jury Criteria Verification Map

Mapping of the five evaluation criteria from `night/SPEC.md` §10 (100 points total) to code locations, reproducible verification commands, and measured pass counts.

---

## 1. Contract and Isolation (Контракт и изоляция — 25 points)

> **Criterion (`night/SPEC.md` §10):** 25 × passed/20 fixed checks of reset/step, schemas, limits, termination, invalid inputs, and leak-free isolation.

| What the jury checks | Where it lives | Command to see it | Measured result |
|---|---|---|---|
| Reset/step lifecycle, observation structure, step counter decrement | `tests/test_env.py::ResetTests::test_reset_observation_and_info` | `uv run python -m unittest tests.test_env` | 32/32 tests pass |
| Bounded errors for invalid actions, unknown tables, bad limits/cursors (error code, message ≤ 200 chars, step consumed) | `tests/test_jury.py::ContractTests::test_invalid_action_name`, `tests/test_jury.py::ContractTests::test_invalid_table`, `tests/test_env.py::ToolTests::test_unknown_action` | `uv run python -m unittest tests.test_jury tests.test_env` | 66/66 tests pass |
| Deterministic pagination and stable cursor traversal over records | `tests/test_jury.py::ContractTests::test_cursor_beyond_data`, `tests/test_jury.py::ContractTests::test_cursor_exactly_at_end_gives_empty_page` | `uv run python -m unittest tests.test_jury` | 34/34 tests pass |
| Lookup error bounds: missing ID consumes a step and returns bounded `not_found` error | `tests/test_jury.py::ContractTests::test_get_record_unknown_id`, `tests/test_jury.py::ContractTests::test_get_document_unknown_doc` | `uv run python -m unittest tests.test_jury` | 34/34 tests pass |
| Safe decimal calculator rejecting execution, globals, syntax errors, and division by zero | `tests/test_jury.py::ContractTests::test_calculator_rejects_code_and_division_by_zero`, `tests/test_jury.py::ContractTests::test_calculator_decimal_arithmetic` | `uv run python -m unittest tests.test_jury` | 34/34 tests pass |
| Property-based randomized action fuzzing against `schemas/action.schema.json` and strict JSON observation validation | `tests/test_fuzz.py::EnvFuzzTests::test_seeded_actions_preserve_step_contract` | `uv run python -m tests.test_fuzz` | 20,312 episode actions validated (0 failures) |
| Step limit enforcement: exactly 100 steps truncation, step 101 returns `episode_over` | `tests/test_jury.py::ContractTests::test_step_101_and_actions_after_truncated` | `uv run python -m unittest tests.test_jury` | 34/34 tests pass |
| 60-second wall-clock limit truncation tested deterministically via injectable clock | `tests/test_clock.py::ClockTests::test_default_limit_truncates_and_grades_empty_answer`, `tests/test_clock.py::ClockTests::test_custom_limit_in_eval_mode_keeps_grade_private` | `uv run python -m unittest tests.test_clock` | 2/2 tests pass |
| Submission termination and rejection of post-terminal actions | `tests/test_jury.py::ContractTests::test_resubmission_and_actions_after_terminated` | `uv run python -m unittest tests.test_jury` | 34/34 tests pass |
| Tool suite boundary: exactly five actions supported (`list_records`, `get_record`, `get_document`, `calculator`, `submit`) | `tests/test_jury.py::ContractTests::test_tools_list_is_exactly_five_actions` | `uv run python -m unittest tests.test_jury` | 34/34 tests pass |
| Zero truth leakage: no grader keys or paths in observations or info in train and eval modes | `tests/test_jury.py::LeakTests::test_no_truth_keys_or_paths_in_any_observation`, `tests/test_jury.py::LeakTests::test_eval_info_is_empty_on_every_step`, `tests/test_env.py::LeakageTests::test_no_truth_leakage` | `uv run python -m unittest tests.test_jury tests.test_env` | 66/66 tests pass |
| Out-of-process eval isolation: hidden evaluation over subprocess stdin/stdout pipe (JSON lines), secret grader log, 1 MiB line bound, strict UTF-8 | `auditenv/check.py::run_remote`, `tests/test_server.py::ServerTest::test_eval_mode_hides_reward_and_logs_grader_side`, `tests/test_server.py::ServerTest::test_oversized_line_is_read_in_bounded_chunks`, `tests/test_server.py::ServerTest::test_subprocess_size_and_invalid_utf8_recovery` | `uv run python -m auditenv.check` | policy saw no reward/truth; 2 results in the grader log |

---

## 2. Data and Ground Truth (Данные и эталон — 25 points)

> **Criterion (`night/SPEC.md` §10):** 25 × valid/20 hidden episodes: pre-injection accounting balance, post-injection discrepancy match, and independent evidence sufficiency.

| What the jury checks | Where it lives | Command to see it | Measured result |
|---|---|---|---|
| Double-entry journal balance: debits equal credits before and after error injections | `tests/test_jury.py::DataTests::test_balanced_before_and_after_errors`, `auditenv/check.py::run_verifier` | `uv run python -m auditenv.check` | 200/200 episodes valid |
| Independent re-derivation of ground truth from transaction records (pre-injection ledger vs injected ledger == truth) | `tests/test_verify.py::VerifyTest::test_generated_episodes_verify`, `tests/test_verify.py::VerifyTest::test_truth_currency_must_match_ledger_currency`, `auditenv/verify.py::verify_episode` | `uv run python -m auditenv.verify --seeds 0-199` | 600/600 episodes valid; episodes with problems: 0 |
| Independent sufficiency of evidence: every evidence ID is reachable through tools and proves the finding | `tests/test_jury.py::DataTests::test_every_evidence_id_reachable_through_the_tools`, `tests/test_hardening.py::DuplicateEvidenceTest::test_duplicate_evidence_sets_contain_all_four_alternatives`, `tests/test_hardening.py::AllocationEvidenceTest::test_partial_allocation_needs_the_posted_ar_credit`, `tests/test_verify.py::VerifyTest::test_nothing_allocated_evidence_must_cover_the_whole_ref` | `uv run python -m unittest tests.test_hardening tests.test_jury tests.test_verify` | 55/55 tests pass |
| Hard-mode data integrity and solvability from transaction records | `auditenv/check.py::run_hard`, `tests/test_hardening.py::DuplicateEvidenceTest::test_missing_evidence_rejected_default_and_hard` | `uv run python -m auditenv.check` | 50/50 hard episodes valid |
| Accounting edge cases: zero-exponent currencies, split and unidentified payments, midnight timezone handling | `tests/test_jury.py::EdgeCaseDataTests::test_zero_exponent_currency`, `tests/test_jury.py::EdgeCaseDataTests::test_refunds_split_multi_invoice_and_unidentified_payments`, `tests/test_jury.py::EdgeCaseDataTests::test_midnight_documents_use_the_company_timezone` | `uv run python -m unittest tests.test_jury` | 34/34 tests pass |
| Exported public splits verification: train, dev, and hard episodes match schemas and verify clean | `tests/test_jury.py::DataTests::test_twenty_episodes_exported`, `tests/test_load.py::TestVerifyLoadedEpisodes::test_verify_dev`, `tests/test_load.py::TestVerifyLoadedEpisodes::test_verify_train`, `tests/test_load.py::TestVerifyLoadedEpisodes::test_verify_hard` | `uv run python -m unittest tests.test_load` | 9/9 tests pass (10/10 dev, 20/20 hard, 10/10 train valid) |

---

## 3. Reward Reliability (Надёжность награды — 25 points)

> **Criterion (`night/SPEC.md` §10):** 25 × passed/20 checks of matching, clean books, false positives, duplicates, step costs, and adversarial submissions.

| What the jury checks | Where it lives | Command to see it | Measured result |
|---|---|---|---|
| Exact matching (TP) and one-to-one claim assignment: duplicate claims do not multiply TP | `tests/test_jury.py::RewardTests::test_exact_match_is_tp`, `tests/test_jury.py::RewardTests::test_duplicate_finding_is_one_tp_and_one_fp`, `tests/test_reward_attacks.py::TestRewardAttacks::test_duplicates_give_no_gain` | `uv run python -m unittest tests.test_jury tests.test_reward_attacks` | 51/51 tests pass |
| Strict False Positive penalties: wrong issue type, wrong amount outside tolerance, currency mismatch, guessed IDs, missing evidence | `tests/test_jury.py::RewardTests::test_each_wrong_field_is_a_false_positive`, `tests/test_reward_attacks.py::TestRewardAttacks::test_guessed_affected_ids_are_fp`, `tests/test_reward_attacks.py::TestRewardAttacks::test_unsupported_evidence_is_fp`, `tests/test_reward_attacks.py::TestRewardAttacks::test_foreign_currency_is_fp` | `uv run python -m unittest tests.test_jury tests.test_reward_attacks` | 51/51 tests pass |
| Clean company evaluation: silence receives maximum return (1.0), false accusations penalized | `tests/test_jury.py::RewardTests::test_clean_company_silence_vs_accusation`, `tests/test_reward_attacks.py::TestRewardAttacks::test_silence_beats_false_accusations_on_clean_books` | `uv run python -m unittest tests.test_jury tests.test_reward_attacks` | 51/51 tests pass |
| Flag-all attack penalisation: submitting all possible findings is strongly penalized | `auditenv/check.py::run_baselines`, `tests/test_jury.py::RewardTests::test_flag_all_is_strongly_negative`, `tests/test_reward_attacks.py::TestRewardAttacks::test_flag_everything_is_bad` | `uv run python -m auditenv.check` | flag-all attack is penalised — mean return -1.000 |
| Reward formula bounds [-1.0, 1.0] and step economy penalty | `tests/test_jury.py::RewardTests::test_reward_formula_edge_cases`, `tests/test_reward_attacks.py::TestRewardAttacks::test_step_economy_only_slightly_separates_equal_answers` | `uv run python -m unittest tests.test_jury tests.test_reward_attacks` | 51/51 tests pass |
| Reward mutation testing: 15 single-line mutations of matcher and metrics logic | `scripts/mutate_reward.py`, `tests/test_mutate_reward.py::RewardMutationTest::test_patterns_match_exactly_once` | `uv run python scripts/mutate_reward.py` | 15/15 mutants killed |
| Automated randomized attack search: 11,000 mutations across 10 attack families | `auditenv/attack.py`, `tests/test_reward_attacks.py::TestRewardAttacks::test_handoff_r1_automatic_attack_search` | `uv run python -m auditenv.attack` | 11000 mutations tested, 0 violations detected |

---

## 4. Reproducibility and Generalization (Воспроизводимость и обобщение — 15 points)

> **Criterion (`night/SPEC.md` §10):** 15 × passed/20 paired checks: seed and action replay is exact; ID relabelling and permutations preserve oracle answer and reward under new IDs.

| What the jury checks | Where it lives | Command to see it | Measured result |
|---|---|---|---|
| Paired check — deterministic replay: identical seed, config, and action sequence produce bitwise identical transitions and rewards | `auditenv/check.py::run_paired`, `tests/test_jury.py::ReproducibilityTests::test_same_seed_byte_identical_different_seed_different` | `uv run python -m auditenv.check` | 20/20 pairs pass |
| Paired check — benign transform: ID permutation and relabelling preserves oracle answer and reward under new IDs, old IDs do not transfer | `auditenv/check.py::run_paired`, `tests/test_jury.py::ReproducibilityTests::test_transform_keeps_oracle_reward_with_new_ids` | `uv run python -m auditenv.check` | 20/20 pairs pass |
| Paired check — hard mode replay and transform with shuffled FX exchange table | `auditenv/check.py::run_paired` | `uv run python -m auditenv.check` | 20/20 pairs pass |
| Generator golden hash invariance: sha256 checksums of 20 seeds × 4 configs | `scripts/golden.py`, `tests/golden_hashes.json`, `tests/test_golden.py::GoldenHashesTest::test_generator_golden_hashes` | `uv run python scripts/golden.py --check` | All 80 golden hashes match |
| Secret keying isolation: `AUDITENV_SECRET` HMAC-keys episode ID and content without altering schema or structure | `tests/test_hardening.py::HardeningTest::test_secret_keys_episode_id_and_content` | `uv run python -m unittest tests.test_hardening` | 14/14 tests pass |

---

## 5. Engineering and Explanation (Инженерия и объяснение — 10 points)

> **Criterion (`night/SPEC.md` §10):** Five 0/1/2 rubric items: single-command run, versioned configs, trajectory logs, measured failure analysis, honest limitations.

| What the jury checks | Where it lives | Command to see it | Measured result |
|---|---|---|---|
| Single-command official run: runs unit tests, verifier, dev baselines, paired checks, out-of-process eval, and hard mode | `auditenv/check.py`, `Makefile` | `uv run python -m auditenv.check` | ALL CHECKS PASSED (295 unit tests, 200/200 verifier, 20/20 paired, 50/50 hard verifier, 20/20 hard paired) |
| Versioned episode configurations: version-controlled JSON definitions for evaluation splits | `configs/dev.json`, `configs/train.json`, `configs/eval_hard.json`, `configs/train_hard.json` | `uv run python -m unittest tests.test_load` | 9/9 tests pass (verifies all exported splits match versioned configs) |
| Standardized trajectory logs: step-by-step gym JSON-lines format with observation, action, reward, terminated, truncated | `trajectories/train_*.jsonl`, `trajectories/train_hard_*.jsonl`, `tests/test_trajectory_files.py::TrajectoryFilesTest::test_files` | `uv run python -m unittest tests.test_trajectory_files` | 1/1 test pass (all 7 trajectory files valid and non-empty) |
| Measured failure analysis: diagnostic tool breaking down policy errors by issue type, interaction scenario, and false-positive reason | `auditenv/analyze.py` | `uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json` | Detailed failure breakdown printed, exit code 0 |
| Transparent, honest limitations: measured constraints, synthetic scope, shortcut miner findings, and trade-offs | `docs/DESIGN.md` §10 | `python3 -c "assert '## 10. Honest limitations' in open('docs/DESIGN.md').read(); print('OK')"` | 11 documented limitations covering receivables-only scope, shortcut miner precision, FX timing cues, and step cost trade-offs |
