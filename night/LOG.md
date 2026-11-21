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
2026-11-21 21:48 gemini3a — T13 complete: verified relative markdown links and backticked repo paths across README.md, docs/CHECKS.md, docs/DESIGN.md, docs/CONTRACT.md, docs/DEMO.md, docs/PITCH.md.
Command: python3 /tmp/r18-gemini3a/check_links.py (exit 0)
- README.md: 14 markdown links checked, 85 repo paths checked; 0 missing
- docs/CHECKS.md: 0 markdown links checked, 201 repo paths checked; 0 missing
- docs/DESIGN.md: 1 markdown links checked, 13 repo paths checked; 0 missing
- docs/CONTRACT.md: 0 markdown links checked, 11 repo paths checked; 0 missing
- docs/DEMO.md: 0 markdown links checked, 1 repo paths checked; 0 missing
- docs/PITCH.md: 0 markdown links checked, 2 repo paths checked; 0 missing
Total: 15 markdown links, 313 repo paths checked across 6 files. 0 missing.
Next: T14.

2026-11-21 21:49 gemini3a — T14 complete: verified all CLI command lines and flags in README.md and docs/*.md.
Command: python3 /tmp/r18-gemini3a/check_flags.py (exit 0)
Number of command lines checked: 67 across 6 files (README.md, docs/CHECKS.md, docs/CONTRACT.md, docs/DEMO.md, docs/DESIGN.md, docs/PITCH.md).
Result: 0 unknown flags.
Next: T15.
2026-11-21 21:49 codex1 — T20. `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r18-codex1/pairs.py` exited 0 in 52.61 s. Seeds 0–49 in each mode. All surrogate IDs were renamed across the exported files. Because CONTRACT §2 defines fx_id by date and currencies, shifted all dates forward one 400-year Gregorian cycle to change every FX ID while preserving weekdays, periods and rate lookups. Shuffled all four tables. Both runs of `python -m auditenv.verify --dir <transformed split>` reported `50/50 episodes valid; episodes with problems: 0`. Closed rewards and grader-side oracle rewards matched across all 100 pairs, zero mismatches. No code fix required. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0 in 173.15 s, `ALL CHECKS PASSED in 172.9 s`. Next: defensive contract and isolation checks.

2026-11-21 21:49 lead — T98: fresh `auditenv.demo --seed 2003` matches every number in docs/DEMO.md (326 rows, 69 invoices, 21 inspection steps, 0.958, 0.333, 286 / 351331 minor units, 22 actions, TP 4) and the check (dev reconcile F1 1.000, hard 0.752). No edit needed.

2026-11-21 21:49 lead — T99: `sync_docs --check` clean against a fresh `check --json`. Found one untracked stale number: `scripts/mutate_reward.py` now runs 22 mutants (22/22 killed, re-run tonight) but PITCH slide 8, CHECKS.md, README "Other commands" and HANDOFF "How to run" said 15. Fixed all four; historical round notes in HANDOFF left as they were.

2026-11-21 21:50 lead — T30 (part): engineering/§09 review subagent scored Engineering 10/10, no blocking issue; Docker job green in CI run 44925790975. Gap fixed: 10 of the 20 episode ids in trajectories.jsonl (hard train, seeds 1100–1109) are not under episodes/, so a juror cross-checking sees unknown ids. README now says where they come from with the export command; checked that the 20 trajectory ids = episodes/train ∪ a fresh export of configs/train_hard.json. Not done (optional, no point at stake): stamping generator/config versions into check --json.

2026-11-21 21:54 lead — T30 (part): docs-claims review subagent checked ~150 claims in README, CHECKS, DESIGN, CONTRACT; fixed the 10 verified defects: README + CONTRACT said `episode_over` costs a step (env.step returns before counting it — now "free and changes nothing"); README said jury_run scenarios come from `judge_adapter.generate_episode` (it uses the public generator, seeds 3001–3020); README's invalid-submission list lacked unknown key and wrong episode_id; CHECKS test counts 69→70 (jury blocks), 10→12 (verify_semantics), 10→11 (verify_redteam), 2→3 README snippets, 11→14 limitations; DESIGN fuzz actions 20 312→20 319, hard random>0 50→47 (re-ran `fuzz --seeds 0-199 --hard`: 47/600, 0 dirty), and the 0.964 payment_allocation cue (2900 amount repeated in ≥4 ledger rows, 217/225) that DESIGN §10 omitted.
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
2026-11-21 21:51 gemini3a — T15 complete: checked all `tests/<file>.py::<Class>::<method>` references in docs/CHECKS.md.
Command: python3 /tmp/r18-gemini3a/check_test_refs.py (exit 0)
Checked 138 `tests/<file>.py::<Class>::<method>` references (and 9 class references).
Result: 0 missing.
All assigned gemini3a tasks (T13, T14, T15) complete.
2026-11-21 21:50 gemini3b — T16: Fresh clone in path with spaces ('/tmp/r18 gemini3b clone'). Ran: (1) `env -u AUDITENV_SECRET uv run python -m auditenv.check` — exit 0, wall 177.55s, last line: 'ALL CHECKS PASSED in 177.4 s'; (2) `env -u AUDITENV_SECRET uv run python -m auditenv.demo` — exit 0, wall 0.30s, last line: 'Done. Full check: uv run python -m auditenv.check'; (3) `env -u AUDITENV_SECRET uv run python judge_adapter.py --help` — exit 0, wall 0.07s, no CLI implemented (exits 0 with empty output). Removed clone. Next: T17.

2026-11-21 21:56 lead — Merged codex1 (T20, T21 + fix), rb (T25), gemini1b (T4–T6), gemini3a (T13–T15), gemini3b (T16); reviewed each diff (only codex1 touched code: closed reset no longer prints the grader key path; regression test added). `auditenv.check` on the merged tip: 526 tests, ALL CHECKS PASSED in 101.0 s. REVIEW.md → "Round 18" written. Topped up gemini1b (T40–T42) and gemini3a (T43–T44).

2026-11-21 21:57 lead — T30 (part): data-ambiguity review subagent — independent definition-only checker matched truth on 44 000 episodes (seeds 20000–20999 × default, hard, heavy, D01–D20 × 2 difficulties), 0 contradictory/ambiguous episodes. The 0.4 % duplicate-cue misses are equal totals with different line items (legitimately not duplicates). Recorded in REVIEW; added a DESIGN §10 bullet on the baseline's unstated 3-day duplicate window (never changes a result) and bumped CHECKS' limitation count to 15. T30 done.
2026-11-21 21:54 codex1 — T19. `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r18-codex1/contract_cases.py` exited 0 in 0.15 s: `116 total contract cases passed; peak step time 0.000241 s`. Independent fixed-input reset/step checks covered malformed envelopes and argument types, extra and missing keys, cursor/limit extremes, long Unicode/NUL IDs, calculator grammar/length boundaries, malformed submissions, interleaved adapters, reset while open, and calls after both terminal states. JSON serialization with allow_nan=False succeeded. Active steps cost one; after the episode ended its balance remained fixed as required by C15/C17. Zero defects found. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0 in 117.17 s: `ALL CHECKS PASSED in 117.0 s`. No queued codex1 tasks.
2026-11-21 21:55 gemini1a — T1: seed sweeps on seeds 7000-7999 (default + hard).
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 7000-7999`
  Exit code: 0
  Wall time: 193.53 s
  Summary:
  default mode, seeds 7000-7999: 3000 episodes (1986 dirty, 1014 clean) in 193.4 s
    episodes with a problem (exception / verifier / oracle): 0
    random explorer reward > 0: 254/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
    flag-all reward < 0: 3000/3000
  FUZZ PASSED
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 7000-7999 --hard`
  Wall time: 350.80 s
  hard mode, seeds 7000-7999: 3000 episodes (1986 dirty, 1014 clean) in 350.6 s
    random explorer reward > 0: 268/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
Problems: 0 problems found across 6,000 episodes (default + hard).
Next: T2 (config fuzz sweep: 3000 configs starting at 40000).
2026-11-21 21:55 gemini3b — T17: Other Python versions (3.12, 3.13) in fresh clone. Command `env -u AUDITENV_SECRET uv run --python 3.12 python -m auditenv.check` exited 2 in 9.17s; last line: 'error: The requested interpreter resolved to Python 3.12.12, which is incompatible with the project\'s Python requirement: `==3.11.*` (from `project.requires-python`)'. Command `env -u AUDITENV_SECRET uv run --python 3.13 python -m auditenv.check` exited 2 in 0.04s; last line: 'error: The requested interpreter resolved to Python 3.13.9, which is incompatible with the project\'s Python requirement: `==3.11.*` (from `project.requires-python`)'. Verified with `--no-project` that the codebase itself is fully compatible with both: all 521 unit tests and all gates pass cleanly on Python 3.12.12 (113.3s, exit 0, 'ALL CHECKS PASSED in 113.3 s') and Python 3.13.9 (111.3s, exit 0, 'ALL CHECKS PASSED in 111.3 s'). Removed worktree. Next: T18.
2026-11-21 21:55 gemini2a — T7: full unit suite ran three times with different hash seeds and timezones. All 3 runs passed with 0 failures:
- Run 1: `PYTHONHASHSEED=1 TZ=UTC env -u AUDITENV_SECRET uv run python -m unittest discover -s tests -t .` -> exit 0, wall time 76.17s (unittest 75.721s), `Ran 523 tests in 75.721s\n\nOK`.
- Run 2: `PYTHONHASHSEED=4242 TZ=Asia/Almaty env -u AUDITENV_SECRET uv run python -m unittest discover -s tests -t .` -> exit 0, wall time 140.48s (unittest 140.219s), `Ran 523 tests in 140.219s\n\nOK`.
- Run 3: `PYTHONHASHSEED=random TZ=America/New_York env -u AUDITENV_SECRET uv run python -m unittest discover -s tests -t .` -> exit 0, wall time 89.30s (unittest 89.069s), `Ran 523 tests in 89.069s\n\nOK`.
Failing tests: 0 (none). No flakiness or timezone/hashseed sensitivity found across 523 tests.

2026-11-21 22:00 lead (Claude, took over from the previous lead engine) — Merged gemini2a's WIP commit (T7; its LOG.md carried stash conflict markers — removed, kept every entry, dropped one duplicated codex1 T20 line). codex1 was idle: queued T45 (loader red-team via adapter/verify --dir), T46 (JSON-lines server red-team over a pipe), T47 (multi-cue shortcut cheater, evidence only — a generator fix would change default episodes). Started a lead subagent that re-reads the published jury check page line by line against judge_adapter + tests/test_judge_*. Next: merge workers every ~30 min. Assumption: marathon workers all alive (ps shows all 9 night.sh workers).

2026-11-21 22:06 gemini2a — T8: ran four jury test modules (`tests.test_judge_contract`, `tests.test_judge_reward`, `tests.test_judge_scenarios`, `tests.test_judge_paired`) 5 times consecutively.
Command: `env -u AUDITENV_SECRET uv run python -m unittest tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired`
- Run 1: exit code 0, wall time 2.34 s -> `Ran 71 tests in 2.256s`, `OK`
- Run 2: exit code 0, wall time 2.34 s -> `Ran 71 tests in 2.254s`, `OK`
- Run 3: exit code 0, wall time 2.39 s -> `Ran 71 tests in 2.304s`, `OK`
- Run 4: exit code 0, wall time 2.71 s -> `Ran 71 tests in 2.624s`, `OK`
- Run 5: exit code 0, wall time 2.98 s -> `Ran 71 tests in 2.872s`, `OK`
Result: 0 differing runs, 0 failures across all 5 runs (71 tests each). No flakiness detected in the jury modules. Next: T9.

