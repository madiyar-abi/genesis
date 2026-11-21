# Round 18 log

2026-11-21 21:42 lead (Claude) — Round 18 started (open improvement round, freeze 2026-11-22 18:00). No TASKS.md existed, so this is the first lead of the round. Wrote night/TASKS.md: 3 tasks per worker (gemini1a–3b evidence sweeps/doc integrity on new seeds, codex1/codex2 red-team the four jury blocks with fixes, rb doc-consistency tests). Assumption: the memory note "red-team passes beat sweeps" (r16) → the strong workers get red-team tasks, the Gemini workers get evidence on new seed ranges. Next: lead review (T30) while the check runs.

2026-11-21 21:48 gemini1b — T4 stress solvability on seeds 5000–5299.
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 5000-5299`
  Exit code: 0
  Wall time: 22.21 s
  Summary: reconcile on 1200 default episodes (seeds 5000-5299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 32, truncated 0 (22.0 s)
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 5000-5299`
  Exit code: 0
  Wall time: 70.77 s
  Summary: reconcile_hard on 1200 hard episodes (seeds 5000-5299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 57, truncated 0 (70.7 s)
Result: 0 imperfect, 0 truncated across 2,400 episodes. Max steps: 32 (default), 57 (hard).
Next: T5 (jury_run on seed bases 7000, 8000, 9000).

2026-11-21 21:49 lead — T98: fresh `auditenv.demo --seed 2003` matches every number in docs/DEMO.md (326 rows, 69 invoices, 21 inspection steps, 0.958, 0.333, 286 / 351331 minor units, 22 actions, TP 4) and the check (dev reconcile F1 1.000, hard 0.752). No edit needed.
2026-11-21 21:49 lead — T99: `sync_docs --check` clean against a fresh `check --json`. Found one untracked stale number: `scripts/mutate_reward.py` now runs 22 mutants (22/22 killed, re-run tonight) but PITCH slide 8, CHECKS.md, README "Other commands" and HANDOFF "How to run" said 15. Fixed all four; historical round notes in HANDOFF left as they were.

2026-11-21 21:50 lead — T30 (part): engineering/§09 review subagent scored Engineering 10/10, no blocking issue; Docker job green in CI run 44925790975. Gap fixed: 10 of the 20 episode ids in trajectories.jsonl (hard train, seeds 1100–1109) are not under episodes/, so a juror cross-checking sees unknown ids. README now says where they come from with the export command; checked that the 20 trajectory ids = episodes/train ∪ a fresh export of configs/train_hard.json. Not done (optional, no point at stake): stamping generator/config versions into check --json.

2026-11-21 21:54 lead — T30 (part): docs-claims review subagent checked ~150 claims in README, CHECKS, DESIGN, CONTRACT; fixed the 10 verified defects: README + CONTRACT said `episode_over` costs a step (env.step returns before counting it — now "free and changes nothing"); README said jury_run scenarios come from `judge_adapter.generate_episode` (it uses the public generator, seeds 3001–3020); README's invalid-submission list lacked unknown key and wrong episode_id; CHECKS test counts 69→70 (jury blocks), 10→12 (verify_semantics), 10→11 (verify_redteam), 2→3 README snippets, 11→14 limitations; DESIGN fuzz actions 20 312→20 319, hard random>0 50→47 (re-ran `fuzz --seeds 0-199 --hard`: 47/600, 0 dirty), and the 0.964 payment_allocation cue (2900 amount repeated in ≥4 ledger rows, 217/225) that DESIGN §10 omitted.
2026-11-21 21:49 codex1 — T20. `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r18-codex1/pairs.py` exited 0 in 52.61 s. Seeds 0–49 in each mode. All surrogate IDs were renamed across the exported files. Because CONTRACT §2 defines fx_id by date and currencies, shifted all dates forward one 400-year Gregorian cycle to change every FX ID while preserving weekdays, periods and rate lookups. Shuffled all four tables. Both runs of `python -m auditenv.verify --dir <transformed split>` reported `50/50 episodes valid; episodes with problems: 0`. Closed rewards and grader-side oracle rewards matched across all 100 pairs, zero mismatches. No code fix required. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0 in 173.15 s, `ALL CHECKS PASSED in 172.9 s`. Next: defensive contract and isolation checks.
2026-11-21 21:52 codex1 — T21. Closed reset without a supplied secret printed the test grader key path to stderr on both file success and fallback. Regression `JudgeContractTest.test_closed_reset_keeps_key_path_off_stderr` failed both subcases before the fix. Suppressed this grader diagnostic during closed reset; offline grader generation retains its existing warning contract. `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r18-codex1/privacy.py` exited 0 in 3.26 s: `40 fixtures, identical private-data differential transcripts; 80 expected reset errors; stream canaries absent`. Seeds 0–19 default and hard, all four tables paged, document lookup, tool errors, invalid submit. Changed truth and provenance while keeping public records fixed and compared every observation, reward, flag and info dict. Checked bad-directory and malformed-grader-file exceptions, stdout and stderr using synthetic markers. This distinguishes public invoice IDs and amounts from private annotations. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0 in 114.07 s: `ALL CHECKS PASSED in 114.0 s`. Next: T19.
2026-11-21 21:52 rb — T25 done: new tests/test_checks_map.py parses all 102 `tests/<file>.py::<Class>::<method>` references in docs/CHECKS.md (unique triples), imports each module and asserts class+method exist; fails with the full list of broken references. `env -u AUDITENV_SECRET uv run python -m unittest tests.test_checks_map` → Ran 2 tests, OK (0.109 s). Scratch-copy proof: copied docs/CHECKS.md to /tmp/r18-rb/CHECKS-scratch.md, renamed `test_c01_reset_returns_json_pair` → `..._RENAMED`; find_broken_references reported `tests/test_judge_contract.py::JudgeContractTest::test_c01_reset_returns_json_pair_RENAMED: method ... not found on JudgeContractTest` (also covered by the in-suite test_renamed_method_is_detected). `env -u AUDITENV_SECRET uv run python -m auditenv.check` exit 0, ALL CHECKS PASSED in 173.2 s. Assumption: reference regex only matches the documented `tests/<file>.py::Class::method` form (no bare module::method refs exist in CHECKS.md). Next: T26.
2026-11-21 21:50 gemini1b — T5 jury_run baseline evaluation on seed bases 7000, 8000, 9000.
Command 1: `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 7000 --json /tmp/r18-gemini1b/j7000.json` (exit 0, wall time 3.85 s)
```
policy                P      R     F1   return   steps   max   time s   max s
random_explorer   0.000  0.000  0.000   -1.000    33.0    33    0.059   0.071
reconcile         1.000  1.000  1.000    0.961    20.6    24    0.057   0.066
flag_all          0.000  0.000  0.000   -1.000     3.4     4    0.051   0.059
oracle            1.000  1.000  1.000    1.000     1.0     1    0.005   0.008
Command 2: `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 8000 --json /tmp/r18-gemini1b/j8000.json` (exit 0, wall time 3.81 s)
random_explorer   0.000  0.000  0.000   -0.903    33.0    33    0.056   0.062
reconcile         1.000  1.000  1.000    0.961    20.5    26    0.057   0.065
flag_all          0.000  0.000  0.000   -1.000     3.5     4    0.049   0.055
oracle            1.000  1.000  1.000    1.000     1.0     1    0.005   0.007
Command 3: `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 9000 --json /tmp/r18-gemini1b/j9000.json` (exit 0, wall time 3.71 s)
random_explorer   0.000  0.000  0.000   -1.000    33.0    33    0.054   0.058
reconcile         1.000  1.000  1.000    0.962    20.1    23    0.055   0.059
flag_all          0.000  0.000  0.000   -1.000     3.5     4    0.049   0.051
oracle            1.000  1.000  1.000    1.000     1.0     1    0.006   0.010
F1 stability analysis:
- No policy differed in F1 across runs (random_explorer: 0.000, reconcile: 1.000, flag_all: 0.000, oracle: 1.000 in all 3 runs; max diff = 0.000, well below threshold 0.2).
- Reconcile achieved F1 1.000 with mean return ~0.961 and average steps 20.1–20.6 (max steps 26).
Next: T6 (fuzz 3000 configs starting at 50000).
2026-11-21 21:54 gemini1b — T6 fuzz 3000 configs starting at 50000.
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 50000`
  Exit code: 0
  Wall time: 211.31 s (3m 31.31s)
  Summary: config sweep, cases 50000-52999: 3000 random configs (1222 hard) in 211.2 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 55
  FUZZ PASSED
Result: 0 problems across 3,000 random configurations (1,222 hard). Max steps: 55.
All gemini1b tasks (T4, T5, T6) complete.
