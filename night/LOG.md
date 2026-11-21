2026-11-22 00:21 lead — Round 20 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/r19 archive. Wrote TASKS.md: independent defect hunts (codex1 chronology/policy-text/adapter reality, codex2 fresh-clone + claims audits, rb scenario adapter runs), evidence sweeps on unseen seeds for gemini workers. Baseline check running. Assumption: generator fixes stay with lead (one re-export owner) to avoid conflicting exports.
2026-11-22 00:23 lead — D: demo --seed 2003 reproduces every DEMO.md number (326 rows, 69 invoices, 21 inspections, 0.958, 286 / 351331 minor units, 0.333, 22 actions). P: sync_docs tables match, but prose on slide 7 and DESIGN §9 was stale since 20 Nov: analyze --config configs/eval_hard.json gives reconcile 20 FP (not 22), duplicate recall 2/8 (not 3/8, six missed, not five), mean 43 actions (not 43.2). Fixed PITCH.md and DESIGN.md; sync_docs does not cover prose numbers.
2026-11-22 00:31 gemini1a — G1: ran `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 10000-10999` (exit 0, wall time 56.1 s: default mode, seeds 10000-10999: 3000 episodes (1986 dirty, 1014 clean), 0 problems, FUZZ PASSED) and `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 10000-10999 --hard` (exit 0, wall time 229.2 s: hard mode, seeds 10000-10999: 3000 episodes (1988 dirty, 1012 clean), 0 problems, FUZZ PASSED). 0 problems found across 6,000 episodes. Next: G2.
2026-11-22 00:33 gemini1a — G2: ran `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 60000` (exit 0, wall time 129.8 s: config sweep, cases 60000-62999: 3000 random configs (1171 hard) in 129.8 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 58, FUZZ PASSED). 0 problems found across 3,000 configs; max steps 58. Next: G3.
2026-11-22 00:34 gemini1a — G3: ran `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 2000-2999` (exit 0, wall time 34.9 s: 3000/3000 episodes valid; episodes with problems: 0). All assigned tasks (G1-G3) complete.
2026-11-22 00:26 gemini1b — G4 complete (stress solvability on seeds 8000-8299).
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 8000-8299`
Exit code: 0, wall time: 7.33 s
Summary: `reconcile on 1200 default episodes (seeds 8000-8299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 34, truncated 0 (7.2 s)`
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 8000-8299`
Exit code: 0, wall time: 20.65 s
Summary: `reconcile_hard on 1200 hard episodes (seeds 8000-8299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 58, truncated 0 (20.6 s)`
2026-11-22 00:32 gemini1b — G5 complete (fuzz sweeps on seeds 11000-11999).
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 11000-11999`
Exit code: 0, wall time: 82.12 s
Summary:
default mode, seeds 11000-11999: 3000 episodes (1991 dirty, 1009 clean) in 82.1 s
  episodes with a problem (exception / verifier / oracle): 0
  random explorer reward > 0: 222/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
  flag-all reward < 0: 3000/3000
FUZZ PASSED
Problems: 0
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --seeds 11000-11999`
Exit code: 0, wall time: 214.53 s
Summary:
hard mode, seeds 11000-11999: 3000 episodes (1987 dirty, 1013 clean) in 214.5 s
  episodes with a problem (exception / verifier / oracle): 0
  random explorer reward > 0: 234/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
  flag-all reward < 0: 3000/3000
FUZZ PASSED
Problems: 0
2026-11-22 00:35 gemini1b — G6 complete (config sweep, cases 63000-65999).
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 63000`
Exit code: 0, wall time: 150.26 s
Summary: `config sweep, cases 63000-65999: 3000 random configs (1170 hard) in 150.2 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 57`
Max steps: 57
FUZZ PASSED
Problems: 0
2026-11-22 00:31 gemini2a — G7: full unit suite 3 times under different PYTHONHASHSEED and TZ. Run 1 (PYTHONHASHSEED=1 TZ=UTC): Ran 561 tests, OK, wall time 55.17s. Run 2 (PYTHONHASHSEED=4242 TZ=Asia/Almaty): Ran 561 tests, OK, wall time 65.54s. Run 3 (PYTHONHASHSEED=random TZ=Pacific/Kiritimati): Ran 561 tests, OK, wall time 64.02s. 0 failures across all 3 runs.
2026-11-22 00:35 gemini2a — G8: auditenv.check twice with auditenv.fuzz --seeds 0-999 --hard in background. Run 1: exit code 0, wall time 86.15s, last line: ALL CHECKS PASSED in 86.1 s. Run 2: exit code 0, wall time 80.31s, last line: ALL CHECKS PASSED in 80.2 s. Timing failures: none (0 timing failures). Background fuzz process was actively running throughout and terminated cleanly.
2026-11-22 00:37 gemini2a — G9: auditenv.check under locales LC_ALL=C LANG=C and LC_ALL=tr_TR.UTF-8. Run 1 (LC_ALL=C LANG=C): exit code 0, wall time 50.78s, last line: ALL CHECKS PASSED in 50.7 s. Run 2 (LC_ALL=tr_TR.UTF-8): exit code 0, wall time 50.36s, last line: ALL CHECKS PASSED in 50.3 s. 0 failures.
2026-11-22 00:27 gemini2b — G10: Re-exported splits to scratch dirs and diffed against committed exports. Commands and results:
  - `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/dev.json --out /tmp/r20-gemini2b/dev` (exit 0, wall 0.078s, "Exported 10 episodes to /tmp/r20-gemini2b/dev"). `diff -r episodes/dev /tmp/r20-gemini2b/dev` exit 0 (0 differing files).
  - `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/train.json --out /tmp/r20-gemini2b/train` (exit 0, wall 0.074s, "Exported 10 episodes to /tmp/r20-gemini2b/train"). `diff -r episodes/train /tmp/r20-gemini2b/train` exit 0 (0 differing files).
  - `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/eval_hard.json --out /tmp/r20-gemini2b/hard` (exit 0, wall 0.253s, "Exported 20 episodes to /tmp/r20-gemini2b/hard"). `diff -r episodes/hard /tmp/r20-gemini2b/hard` exit 0 (0 differing files).
  - `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/train_hard.json --out /tmp/r20-gemini2b/train_hard` (exit 0, wall 0.147s, "Exported 10 episodes to /tmp/r20-gemini2b/train_hard"). Committed `episodes/train_hard` does not exist (as documented in README line 195: hard train episodes are generated on demand into /tmp; `episodes/hard` holds eval_hard); verified exported directory with `env -u AUDITENV_SECRET uv run python -m auditenv.verify --dir /tmp/r20-gemini2b/train_hard` (exit 0: "10/10 episodes valid; episodes with problems: 0").
  All committed exports match byte for byte with fresh exports.
2026-11-22 00:31 gemini2b — G11: Checked golden hashes and ran reward mutation tests. Commands and results:
  - `uv run python scripts/golden.py --check` (exit 0, wall 0.650s): "All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2b/tests/golden_hashes.json."
  - `uv run python scripts/mutate_reward.py` (exit 0, wall 3:40.49 total / 219.12s user): "22/22 mutants killed."
  All 80 golden hashes match; all 22 reward/matcher/schema/metrics mutants successfully killed.
2026-11-22 00:33 gemini2b — G12: Ran `uv run python scripts/shortcut_miner.py` (seeds 0-999, configs random_mix/heavy, 2000 episodes, wall 22.4s, exit 1 due to flagged values without --report-only).
Max precision per issue type:
| type | affected max P | evidence max P | flagged (aff/ev) |
|---|---|---|---|
| duplicate_invoice | 0.996 | 0.996 | 2/2 |
| payment_allocation | 0.964 | 0.964 | 8/1 |
| fx_error | 0.704 | 0.308 | 3/0 |
| period_cutoff | 0.452 | 0.452 | 0/0 |

Total flagged values: 16 (precision > 0.5):
- affected duplicate_invoice (2): `invoices same_entity_currency_total_count == 2` (P=0.996), `invoices total_count_in_table == 2` (P=0.972).
- affected payment_allocation (8): `ledger amount_count_in_table@acct2900 == 4+` (P=0.964), `ledger day_rel_period@acct2900 == end-0` (P=0.789), `ledger amount_digits@acct2900 == 9` (P=0.750), `ledger position_decile@acct2900 == 9` (P=0.671), `ledger amount_count_in_table@acct2900 == 1` (P=0.622), `ledger day_rel_period@acct7900 == end-0` (P=0.568), `ledger amount_digits@acct2900 == 6` (P=0.566), `ledger payment_journal_size@acct2900 == 4+` (P=0.557).
- affected fx_error (3): `ledger day_rel_period@acct2900 == end-0` (P=0.704), `ledger position_decile@acct2900 == 9` (P=0.549), `ledger day_rel_period@acct7900 == end-0` (P=0.548).
- evidence duplicate_invoice (2): `invoices same_entity_currency_total_count == 2` (P=0.996), `invoices total_count_in_table == 2` (P=0.972).
- evidence payment_allocation (1): `ledger amount_count_in_table@acct2900 == 4+` (P=0.964).

Comparison with `docs/DESIGN.md` §10: Exactly 16 flagged values in default mode, precisely matching the 16 flagged values documented in DESIGN §10 (duplicate definitions at P=0.996, last-day 2900/7900 fx_error cues at P=0.70, 2900 payment_allocation hints at P=0.75-0.78 and repeated amount at P=0.964). 0 unlisted columns/features with precision > 0.5.

2026-11-22 00:26 gemini3a — G13: Ran four jury modules 5 times in a row (`env -u AUDITENV_SECRET uv run python -m unittest tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired`). All 5 runs passed: Run 1 (Ran 73 tests in 2.208s, OK, exit 0, wall 2.30s), Run 2 (Ran 73 tests in 2.279s, OK, exit 0, wall 2.34s), Run 3 (Ran 73 tests in 2.273s, OK, exit 0, wall 2.34s), Run 4 (Ran 73 tests in 2.258s, OK, exit 0, wall 2.32s), Run 5 (Ran 73 tests in 2.359s, OK, exit 0, wall 2.42s). Zero differing runs or failures. Next: G14.
2026-11-22 00:27 gemini3a — G14: Ran `env -u AUDITENV_SECRET uv run python -m auditenv.attack` (exit 0, wall 0.45s; 20 seeds evaluated, 11,000 mutations tested, 0 violations detected: PASSED) and `uv run python scripts/sensitivity.py` (exit 0, wall 2.35s; dev 10 episodes and hard 20 episodes evaluated across step cost and amount tolerance; rankings invariant: oracle > reconcile > naive_reconcile > random > flag_all on dev; oracle > reconcile_hard > reconcile > naive_reconcile > random > flag_all on hard; re-grade reproduced every env reward exactly). Next: G15.
2026-11-22 00:28 gemini3a — G15: Ran red-team modules 10 times (`env -u AUDITENV_SECRET uv run python -m unittest tests.test_load_redteam tests.test_server_redteam tests.test_jury_run`). All 10 runs passed: Run 1 (Ran 18 tests in 5.195s, OK, exit 0, wall 5.29s), Run 2 (Ran 18 tests in 5.254s, OK, exit 0, wall 5.33s), Run 3 (Ran 18 tests in 5.259s, OK, exit 0, wall 5.33s), Run 4 (Ran 18 tests in 5.309s, OK, exit 0, wall 5.39s), Run 5 (Ran 18 tests in 5.295s, OK, exit 0, wall 5.37s), Run 6 (Ran 18 tests in 5.453s, OK, exit 0, wall 5.54s), Run 7 (Ran 18 tests in 5.355s, OK, exit 0, wall 5.43s), Run 8 (Ran 18 tests in 5.377s, OK, exit 0, wall 5.46s), Run 9 (Ran 18 tests in 5.392s, OK, exit 0, wall 5.47s), Run 10 (Ran 18 tests in 5.111s, OK, exit 0, wall 5.19s). Zero failures. All gemini3a tasks complete.
2026-11-22 00:26 gemini3b — G16: verified all directories under episodes/. dev: 10/10 episodes valid; episodes with problems: 0. hard: 20/20 episodes valid; episodes with problems: 0. train: 10/10 episodes valid; episodes with problems: 0. Exit code 0.
2026-11-22 00:27 gemini3b — G17: demo --help exit 0. yes '' | env -u AUDITENV_SECRET uv run python -m auditenv.demo exit 0. Quoted final lines: "terminal reward 0.958 = clip(2*F1 - 1 - 0.002*21 steps)   P=1.00 R=1.00 F1=1.00", "policy side: 22 steps, rewards seen = [0.0], final info = {}", "grader log : reward 0.958, F1 1.00, TP 4 FP 0 FN 0". Comparison with docs/DEMO.md: all numbers (326 ledger rows, 69 invoices, 100 budget, 21 inspection steps, 22 actions, reward 0.958, 286 / 351331 minor units, repeated oracle 0.333, clean silence 1.000) match docs/DEMO.md exactly with zero differences.
2026-11-22 00:28 gemini3b — G18: auditenv.check --json /tmp/r20-gemini3b/c.json exit 0 (ALL CHECKS PASSED in 81.7 s). sync_docs.py --check --json /tmp/r20-gemini3b/c.json exit 0 ("All documentation tables match measured data."). Zero drift.
