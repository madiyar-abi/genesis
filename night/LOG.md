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
2026-11-22 00:30 rb — Z1 done: night/r20/scenarios_adapter.py plays all D01–D20 through judge_adapter, closed mode
  (generate_episode with the default grader key, AUDITENV_SECRET unset), seeds 32000–32004, default + hard, policies
  reconcile / reconcile_hard and flag_all driven via JuryPolicy (jury-shaped observations only; scores read from the
  grader-side env.grader_log; the script never opens truth/provenance). Command:
  `env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py` → exit 0, wall 7.0 s, 400 runs
  (20 scenarios × 2 difficulties × 5 seeds × 2 policies), all submissions valid, every closed step reward 0.0
  (asserted), max episode time 0.024 s of the 60 s limit. Mean grader return per scenario (min F1 over the 5 seeds):
| scenario | default reconcile return (min F1) | default flag_all return | hard reconcile_hard return (min F1) | hard flag_all return |
|---|---|---|---|---|
| D01 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D02 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D03 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D04 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D05 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D06 | 0.956 (1.000) | -1.000 | 0.914 (1.000) | -1.000 |
| D07 | 0.956 (1.000) | -1.000 | 0.914 (1.000) | -1.000 |
| D08 | 0.956 (1.000) | -1.000 | 0.914 (1.000) | -1.000 |
| D09 | 0.961 (1.000) | -1.000 | 0.916 (1.000) | -1.000 |
| D10 | 0.959 (1.000) | -1.000 | 0.914 (1.000) | -1.000 |
| D11 | 0.961 (1.000) | -1.000 | 0.920 (1.000) | -1.000 |
| D12 | 0.960 (1.000) | -1.000 | 0.920 (1.000) | -1.000 |
| D13 | 0.960 (1.000) | -1.000 | 0.920 (1.000) | -1.000 |
| D14 | 0.962 (1.000) | -1.000 | 0.918 (1.000) | -1.000 |
| D15 | 0.962 (1.000) | -1.000 | 0.918 (1.000) | -1.000 |
| D16 | 0.963 (1.000) | -1.000 | 0.922 (1.000) | -1.000 |
| D17 | 0.963 (1.000) | -1.000 | 0.922 (1.000) | -1.000 |
| D18 | 0.963 (1.000) | -1.000 | 0.922 (1.000) | -1.000 |
| D19 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D20 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
  Flags: 0 — reconcile/reconcile_hard F1 = 1.000 on every scenario × difficulty × seed; flag_all return −1.000
  everywhere (never > 0). Notes (return below the README jury_run mean 0.959, F1 still 1.000 — not defects):
  D06–D08 default reconcile 0.956 (22.8 mean steps vs the 21.4-scenario average; README's 0.959 is a 20-scenario
  mean on seeds 3001–3020, per-scenario return varies with the 0.002/step inspection cost); all 20 hard scenarios
  reconcile_hard 0.914–0.922 (41–44 mean steps: hard books need ~2× the inspections; README's table is default
  difficulty, no hard jury_run mean is documented). Assumptions: policies run in-process behind JuryPolicy instead
  of policy_worker subprocesses because reconcile_hard is not in policy_worker.POLICIES and product code is
  off-limits for workers — isolation is equivalent (the policy object receives only reset/step observations);
  "documented value in README" taken as the jury_run table (reconcile return 0.959 / F1 1.000, flag_all −1.000).
  Full per-seed results: /tmp/r20-rb/z1.json, full output /tmp/r20-rb/z1.out. Next: Z2.
2026-11-22 00:31 rb — Z2 done: `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base <B>
  --json /tmp/r20-rb/j<B>.json` for B = 20000, 21000, 22000, 23000. All four exit 0; wall times (time -p real):
  2.75 s, 2.87 s, 2.74 s, 2.83 s. Policy tables (P/R/F1 micro, mean return, mean steps, max steps, mean/max s):
  B=20000 (seeds 20001–20020): random_explorer 0.000/0.000/0.000 −1.000 33.0/33 0.040/0.045;
    reconcile 1.000/1.000/1.000 0.960 20.8/24 0.041/0.048; flag_all 0.000/0.000/0.000 −1.000 3.5/4 0.036/0.040;
    oracle 1.000/1.000/1.000 1.000 1.0/1 0.006/0.008.
  B=21000 (seeds 21001–21020): random_explorer 0.000/0.000/0.000 −0.903 33.0/33 0.041/0.049;
    reconcile 1.000/1.000/1.000 0.960 21.1/23 0.044/0.052; flag_all 0.000/0.000/0.000 −1.000 3.6/4 0.037/0.043;
    oracle 1.000/1.000/1.000 1.000 1.0/1 0.006/0.008.
  B=22000 (seeds 22001–22020): random_explorer 0.000/0.000/0.000 −1.000 33.0/33 0.039/0.043;
    reconcile 1.000/1.000/1.000 0.960 21.0/24 0.040/0.045; flag_all 0.000/0.000/0.000 −1.000 3.6/4 0.036/0.041;
    oracle 1.000/1.000/1.000 1.000 1.0/1 0.006/0.008.
  B=23000 (seeds 23001–23020): random_explorer 0.000/0.000/0.000 −0.903 33.0/33 0.042/0.049;
    reconcile 1.000/1.000/1.000 0.960 20.9/25 0.042/0.055; flag_all 0.000/0.000/0.000 −1.000 3.6/4 0.037/0.040;
    oracle 1.000/1.000/1.000 1.000 1.0/1 0.006/0.008.
  Flags: 0 — oracle F1 = 1.000 and reconcile F1 = 1.000 in all four runs (tp/fp/fn 20/0/0 each); no run's
  random/flag_all mean return > −0.5 (worst −0.903). Note (explained, not a defect): random_explorer's mean
  −0.9032 at B=21000 and B=23000 = 19×(−1) + one clean scenario where it submitted empty findings, the correct
  answer on clean books (F1 1.0, reward 0.936 = 1 − 0.002×32 inspections). Reproduced with a scratch replay
  (/tmp/r20-rb/z2_random_check.py, public generator as jury_run uses): B=21000 → D01 seed 21001, B=23000 → D04
  seed 23004, both 0/0/0, reward 0.9360. Micro F1 stays 0.000 because a clean episode contributes no tp/fp/fn.
  JSON tables: /tmp/r20-rb/j{20000,21000,22000,23000}.json; raw outputs j<B>.out. Both rb tasks (Z1, Z2) done.
2026-11-22 00:48 lead — Merged gemini1a/1b/2a/2b/3a/3b and rb: all evidence green (fuzz 6k+6k+3k+3k episodes, verify 3000/3000, stress 0 imperfect max 58 steps, suite 561 OK under 3 hashseeds/TZs and 2 locales, exports byte-identical, golden 80/80, mutants 22/22, miner 16 flagged = DESIGN §10, jury modules 5x, red-team 10x, D01-D20 through adapter F1 1.000 on 400 runs, jury_run 4 seed bases). No defect. Topped up queues (G19-G24, Z3-Z4). codex1 rate-limited until 02:41, codex2 until 01:04: X1 retagged lead (subagent).
2026-11-22 00:49 gemini2a — G21: Resource-leak and warning run (python -X dev -W error::ResourceWarning -m unittest discover -s tests -t .). Ran 561 tests in 49.960s, OK, wall time 50.07s. ResourceWarnings: 0. Total warning/error lines: 0 (no warnings or errors found).
2026-11-22 00:52 lead — X3 (subagent): night/r20/adapter_reality.py, 20/20 checks pass twice: fresh HOME (key 0600, same episode_id across processes), read-only/missing HOME (per-process fallback, cross-process scoring still agrees), 8-process race x 20 rounds (one key, no partial file), relative/space/non-ASCII/NFD/symlink/trailing-slash episode_dir, leak scan of every observation (no key, path, seed or truth field), two JudgeEnv interleaved. No defect. Noted: with unwritable HOME closed episodes are not reproducible across processes (documented in README); stderr warning names the key path (grader-side only, documented).
2026-11-22 01:02 lead — X1 (subagent): night/r20/chronology.py, an independent public-data checker (12,600 episodes: seeds 30000-30299 x default/hard/D01-D20 both difficulties). Found a real defect: a 30 % in-period posting lag (generator.py) let a receipt credit AR for an invoice up to 3 days before the invoice was booked (575 rows in 520 of 3,000 clean episodes; repro D01 default seed 30010 RCPT0548981 vs 2608-742998). Fix: _post_before_payment moves such an invoice's two rows to its issue instant in place (no new random draws, so 65/80 golden hashes and the demo are unchanged). Regression test_cash_is_applied_after_the_invoice_is_posted failed in 29 subtests before, passes after. After fix: checker exit 0, the remaining 32 hits are the injected prior-period period_cutoff invoice itself (explained). Re-exported dev/train/hard, regenerated 7 trajectory files + trajectories.jsonl + golden. check 562 tests all gates 54.2 s; sync_docs no drift; fuzz 0-999 and 0-199 --hard pass; attack 0/11000; verify 600/600 and splits 10/10/20. Assumption: dropping the lag (post at issue) is the least invasive fix, preferred over moving payments (which reshuffled the RNG stream and changed the demo company).

2026-11-22 01:15 codex2 — Y1 fresh-clone sweep at 299c5e7 (Python 3.11.14).
Cloned with `git clone /Users/caliskan/Projects/genesis /tmp/r20-codex2/clone` and checked out the fetched round tip by SHA. Commands ran at the clone root with `AUDITENV_SECRET` unset. Scratch output paths were moved under `/tmp/r20-codex2`; demo stdin received blank lines. CONTRACT has no shell fences. Shell control-flow blocks are timed as a unit. Full output is in `/tmp/r20-codex2/command-*.txt`.

| Source | Command | Exit | Wall s | Output |
|---|---|---:|---:|---|
| README.md:29 | `git clone https://github.com/madiyar-abi/genesis.git && cd genesis` | skipped | — | Task exclusion |
| README.md:30 | `uv run python -m auditenv.check` | 0 | 53.321 | ALL CHECKS PASSED in 53.2 s |
| README.md:40 | `docker build -t auditenv .` | skipped | — | Task exclusion |
| README.md:41 | `docker run --rm --network none auditenv` | skipped | — | Task exclusion |
| README.md:53 | `docker build --target policy -t genesis-policy .` | skipped | — | Task exclusion |
| README.md:54 | `uv run python -m auditenv.jury_run --policy-image genesis-policy` | skipped | — | Task exclusion |
| README.md:184 | `uv run python -m auditenv.run --policy reconcile --config configs/dev.json --out /tmp/r20-codex2/dev_reconcile.jsonl` | 0 | 0.113 |  |
| README.md:185 | `uv run python -m auditenv.run --policy random --seeds 2000-2009 --mode eval` | 0 | 0.079 |  |
| README.md:200 | `uv run python -m auditenv.run --policy reconcile_hard --config configs/train.json --config configs/train_hard.json --out trajectories.jsonl` | 0 | 0.250 |  |
| README.md:210 | `for p in random naive_reconcile reconcile; do uv run python -m auditenv.run --policy $p --config configs/train.json --out trajectories/train_$p.jsonl; done` | 0 | 0.269 |  |
| README.md:213 | `for p in random naive_reconcile reconcile reconcile_hard; do uv run python -m auditenv.run --policy $p --config configs/train_hard.json --out trajectories/train_hard_$p.jsonl; done` | 0 | 0.763 |  |
| README.md:334 | `uv run python -m auditenv.jury_run` | 0 | 1.614 |  |
| README.md:355 | `AUDITENV_SECRET="${GRADER_KEY:?Set GRADER_KEY in the organiser shell}" uv run python -m auditenv.server --episodes hidden.json --grader-log grader.jsonl` | skipped | — | Task exclusion |
| README.md:371 | `uv run python -c "from auditenv.check import run_remote; assert run_remote()"` | 0 | 0.078 | [PASS] out-of-process eval run — policy saw no reward/truth; 2 results in the grader log |
| README.md:379 | `uv run python -m unittest discover -s tests -t .` | 0 | 51.975 | Ran 562 tests in 51.852s |
| README.md:380 | `uv run python -m unittest tests.test_env` | 0 | 0.234 | Ran 33 tests in 0.178s |
| README.md:381 | `uv run python -c "from auditenv.check import run_remote; assert run_remote()"` | 0 | 0.104 | [PASS] out-of-process eval run — policy saw no reward/truth; 2 results in the grader log |
| README.md:382 | `uv run python -m auditenv.verify --seeds 0-199` | 0 | 5.485 | 600/600 episodes valid; episodes with problems: 0 |
| README.md:383 | `uv run python -m auditenv.verify --dir episodes/train` | 0 | 0.140 | 10/10 episodes valid; episodes with problems: 0 |
| README.md:384 | `uv run python -m auditenv.verify --dir episodes/dev` | 0 | 0.135 | 10/10 episodes valid; episodes with problems: 0 |
| README.md:385 | `uv run python -m auditenv.verify --dir episodes/hard` | 0 | 0.427 | 20/20 episodes valid; episodes with problems: 0 |
| README.md:386 | `uv run python -m auditenv.attack` | 0 | 0.500 | Total mutations tested: 11000; Total violations detected: 0 |
| README.md:387 | `uv run python -m tests.test_fuzz` | 0 | 1.172 | Python 3.11.14, 20319 episode actions, 20524 total step calls in 1.119 s |
| README.md:388 | `uv run python -m auditenv.check --json /tmp/r20-codex2/auditenv-metrics.json` | 0 | 76.342 | ALL CHECKS PASSED in 76.3 s |
| README.md:389 | `uv run python scripts/sync_docs.py --check --json /tmp/r20-codex2/auditenv-metrics.json` | 0 | 0.047 | All documentation tables match measured data. |
| README.md:390 | `uv run python -m auditenv.fuzz --seeds 0-999` | 0 | 86.569 | FUZZ PASSED |
| README.md:391 | `uv run python -m auditenv.fuzz --configs 3000` | 0 | 93.398 | config sweep, cases 0-2999: 3000 random configs (1186 hard) in 93.4 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 56 |
| README.md:392 | `uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299` | 0 | 7.237 | reconcile on 1200 default episodes (seeds 0-299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 33, truncated 0 (7.2 s) |
| README.md:393 | `uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json` | 0 | 0.088 |  |
| README.md:394 | `uv run python -m auditenv.demo` | 0 | 0.104 | grader log : reward 0.958, F1 1.00, TP 4 FP 0 FN 0 |
| README.md:395 | `uv run python -m auditenv.export --config configs/dev.json --out episodes/dev` | 0 | 0.081 | Exported 10 episodes to episodes/dev |
| README.md:396 | `uv run python -m auditenv.export --config configs/train.json --out episodes/train` | 0 | 0.080 | Exported 10 episodes to episodes/train |
| README.md:397 | `uv run python -m auditenv.export --config configs/eval_hard.json --out episodes/hard` | 0 | 0.257 | Exported 20 episodes to episodes/hard |
| README.md:398 | `uv run python scripts/mutate_reward.py` | 0 | 139.540 | 22/22 mutants killed. |
| README.md:399 | `uv run python scripts/sensitivity.py` | 0 | 1.860 |  |
| README.md:400 | `uv run python scripts/shortcut_miner.py --report-only` | 0 | 15.958 |  |
| README.md:401 | `uv run python scripts/golden.py --check` | 0 | 0.469 | All 80 golden hashes match /private/tmp/r20-codex2/clone/tests/golden_hashes.json. |
| README.md:402 | `uv run python scripts/bench.py` | 0 | 9.684 |  |
| README.md:403 | `uv run python scripts/chart.py` | 0 | 0.041 | wrote /private/tmp/r20-codex2/clone/docs/baselines.svg |
| README.md:404 | `make check` | 0 | 52.696 | ALL CHECKS PASSED in 52.6 s |
| README.md:405 | `make -n check test verify fuzz stress attack golden mutate miner bench sensitivity chart` | 0 | 0.008 |  |
| docs/DEMO.md:9 | `env -u AUDITENV_SECRET uv run python -m auditenv.demo --seed 2003 --pause` | 0 | 0.103 | grader log : reward 0.958, F1 1.00, TP 4 FP 0 FN 0 |

Output comparisons:
- README.md:123 reports hard reconcile F1 0.752. The check printed `[PASS] hard: default rules no longer suffice — reconcile F1 0.755`.
- README.md:340 reports 21.4 mean reconcile actions for the jury cohort. The replay printed:
  ```text
  reconcile         1.000  1.000  1.000    0.959    21.3    26    0.024   0.026
  ```
- Chart from the scratch metrics: `env -u AUDITENV_SECRET uv run python scripts/chart.py --json /tmp/r20-codex2/auditenv-metrics.json --out /tmp/r20-codex2/baselines.svg`, exit 0, 0.047 s, `wrote /tmp/r20-codex2/baselines.svg`. `cmp docs/baselines.svg /tmp/r20-codex2/baselines.svg` exited 1 and printed `docs/baselines.svg /tmp/r20-codex2/baselines.svg differ: char 3401, line 35`. Bar titles changed from `reconcile, dev: 0.957` to `reconcile, dev: 0.956`, `reconcile, hard: 0.288` to `reconcile, hard: 0.293`, `naive_reconcile, dev: −0.506` to `naive_reconcile, dev: −0.480`, and `naive_reconcile, hard: −0.711` to `naive_reconcile, hard: −0.704`. The chart command's implicit metrics path requires the README's original JSON path or an explicit `--json` when relocated.
- All 36 eligible entries exited 0, including both trajectory loops (seven invocations). The clone's episode and trajectory paths match HEAD after replay. The six exclusions were the GitHub clone, Docker build/run, the Docker-dependent jury run, and the organiser server. The bare chart command found an existing shared default-path metrics file, so the isolated chart comparison above used this sweep's own JSON.
- The demo reproduced 326 ledger rows, 69 invoices, 100 steps, payment PAY-136430, 286 and 351331 USD minor units, four matches in 22 actions with 21 inspections, return 0.958, oracle 1.000, repeats 0.333, silence −1.000 on dirty books and 1.000 on clean books. Hard F1 0.755 rounds to the script's approximate 0.75.
2026-11-22 01:09 gemini1a — G19: ran `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 12000-12999 --hard` (exit 0, wall time 217.1 s: hard mode, seeds 12000-12999: 3000 episodes (1994 dirty, 1006 clean), 0 problems, FUZZ PASSED) and `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 9000-9299` (exit 0, wall time 9.1 s: reconcile on 1200 default episodes (seeds 9000-9299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 32, truncated 0). 0 problems found across 4,200 episodes. All assigned tasks complete.
2026-11-22 01:09 gemini1b — G20 complete (config sweep 66000-68999 and hard stress reconcile_hard 9000-9299).
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 66000`
Exit code: 0, wall time: 138.77 s
Summary: `config sweep, cases 66000-68999: 3000 random configs (1229 hard) in 138.7 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 58`
Max steps: 58
FUZZ PASSED
Problems: 0
Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 9000-9299`
Exit code: 0, wall time: 31.35 s
Summary: `reconcile_hard on 1200 hard episodes (seeds 9000-9299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 57, truncated 0 (31.3 s)`
Max steps: 57
Problems: 0
2026-11-22 01:05 gemini2b — G22: Ran optimized-mode check and audited product code for assertions. Commands and results:
  - `env -u AUDITENV_SECRET uv run python -O -m auditenv.check`: exit 0, wall 53.591s (50.69s user, 2.18s system). Last line: "ALL CHECKS PASSED in 53.4 s" (562 unit tests, 200/200 verifier, all baselines/gates passed).
  - `grep -n "^\s*assert " auditenv/*.py auditenv/policies/*.py judge_adapter.py`: exit 1 (0 matches). Product code contains 0 assertions (proper exception handling throughout; python -O removes nothing required for validation).
2026-11-22 01:01 gemini3a — G23: Ran every test module alone (`env -u AUDITENV_SECRET uv run python -m unittest tests.$m >/tmp/r20-gemini3a/$m.out 2>&1`). Checked 71 test modules. All 71 modules exited with code 0 (0 non-zero exits, 0 failures, total wall time 46.63s). Outputs saved to /tmp/r20-gemini3a/*.out.
2026-11-22 01:00 gemini3b — G24: regenerated committed trajectories into /tmp/r20-gemini3b/. Commands:
  env -u AUDITENV_SECRET uv run python -m auditenv.run --policy reconcile_hard --config configs/train.json --config configs/train_hard.json --out /tmp/r20-gemini3b/trajectories.jsonl
  for p in random naive_reconcile reconcile; do env -u AUDITENV_SECRET uv run python -m auditenv.run --policy $p --config configs/train.json --out /tmp/r20-gemini3b/trajectories/train_$p.jsonl; done
  for p in random naive_reconcile reconcile reconcile_hard; do env -u AUDITENV_SECRET uv run python -m auditenv.run --policy $p --config configs/train_hard.json --out /tmp/r20-gemini3b/trajectories/train_hard_$p.jsonl; done
Diffs:
  diff -u trajectories.jsonl /tmp/r20-gemini3b/trajectories.jsonl -> exit 0 (identical)
  diff -ru trajectories /tmp/r20-gemini3b/trajectories -> exit 0 (all 7 files identical)
Differing files: none.
2026-11-22 01:14 lead — Merged top-up 1 (G19-G24): all green (hard fuzz 3000, stress 0 imperfect max 57/32 steps, config sweep 3000 max 58, -X dev 0 ResourceWarnings, -O check passes and 0 product asserts, 71 modules pass alone, trajectories byte-identical). Queued G25-G30 to re-test the generator fix.

2026-11-22 01:16 codex2 — Y2 jury README and contract claims audit (round tip 4b96d2f).

Evidence by claim group:

| Documentation | Evidence checked |
|---|---|
| README.md:61–72,239–265 (key source, public/closed generation, location, protocol, example) | Dockerfile:10–14; judge_adapter.py:37–56,72–121,125–143; auditenv/grader_key.py:15–59; auditenv/generator.py:60–64,108–113,123–139; tests/test_judge_contract.py:362–389; tests/test_readme_snippets.py:42–92 |
| README.md:74–84 (submission materials and sizes) | LICENSE:1; pyproject.toml and uv.lock; Dockerfile:1,10–14; configs/{train,dev,train_hard,eval_hard}.json; Y1 verify and byte-replay evidence, including 674 trajectory lines; auditenv/jury_run.py:28,36–63 and auditenv/policy_worker.py:10–42 |
| README.md:268–288 (call and observation shapes, flags, limits, errors, allowed tools, no grading feedback in closed mode) | judge_adapter.py:72–143; auditenv/env.py:17–38,89–110,123–168,187–238; auditenv/load.py:106–163; tests/test_judge_contract.py:80–359; tests/test_error_codes_doc.py:128–151 |
| README.md:290–328 (labels, amounts, matching and published scenarios, export, provenance, paired rules and minimal grading fixture) | auditenv/inject.py:61–272; auditenv/matcher.py:20–46,68–123; auditenv/jury.py:5–20; auditenv/generator.py:577–638,665–680; auditenv/verify.py:464–478; auditenv/load.py:117–139; auditenv/transform.py:25–66; tests/test_judge_scenarios.py:67–127; tests/test_judge_paired.py |
| README.md:330–349 (jury replay, metrics and test mapping) | auditenv/jury_run.py:36–63,66–118; auditenv/check.py:51–64,301–326; Y1 replay and four jury test modules |
| CONTRACT.md:3–62 (runtime, units, exponents, rates, manifest, IDs, journal and payment rules, dates, reversals) | pyproject.toml; auditenv/money.py:8–23,47–50; auditenv/generator.py:49–55,237–329,508–538,577–625,642–663; auditenv/verify.py:101–124 |
| CONTRACT.md:64–91 (truth shape, four kinds, amounts, evidence, duplicate equivalence and I1/I2) | auditenv/generator.py:597–603; auditenv/inject.py:61–272; auditenv/verify.py evidence checks; schemas/truth.schema.json; tests/test_judge_scenarios.py |
| CONTRACT.md:93–142 (native API, configuration, reset side effects, keys, result shapes, error and terminal behavior) | auditenv/env.py:17–38,56–110,123–168,187–238; auditenv/generator.py:67–105,540–569,705–719; auditenv/server.py:168–184,201–225; judge_adapter.py:37–41,84–91 |
| CONTRACT.md:144–189 (findings structure, grading math, policy/runner API) | auditenv/schema.py; auditenv/matcher.py:20–47,68–149; auditenv/metrics.py:4–17; auditenv/run.py:28–52; tests/test_judge_reward.py and tests/test_reward_attacks.py |

The four jury modules plus tests.test_readme_snippets, tests.test_error_codes_doc and tests.test_calculator ran with `env -u AUDITENV_SECRET AUDITENV_KEY_FILE=/tmp/r20-codex2/grader.key uv run python -m unittest tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired tests.test_readme_snippets tests.test_error_codes_doc tests.test_calculator`, exit 0. Output:
```text
Ran 85 tests in 2.032s

OK
```

Discrepancies and proposed wording:

| Doc line | Evidence | Correct text |
|---|---|---|
| README.md:248–251 | judge_adapter.py:90 calls `grader_key(warn=False)` on generated closed resets; auditenv/grader_key.py:32–35 gates both stderr messages on that flag. The mode is applied at file creation (line 43); existing permissions are untouched on read (55–59). | “When generating an export, the adapter may report the key path or fallback on grader stderr. Closed reset itself is quiet. On first creation, the key file has mode 0600.” |
| README.md:253 | Open reset passes `key=None` at judge_adapter.py:90–91; auditenv/generator.py:60–64,128–129 then uses the environment variable if present. | “Open mode uses the public generator when `AUDITENV_SECRET` is unset. The committed splits are public.” |
| README.md:271 | judge_adapter.py:85–88 filters a loaded episode's team config to the two limit keys, silently ignoring other keys. auditenv/load.py:149–163 checks structure, payment remittance invoice targets and balance. Full semantic journal checks are verifier-specific. | “Only `max_steps` and `time_limit_s` apply to a loaded episode. The loader validates structure, payment remittance invoice targets and journal balance.” |
| README.md:273 | judge_adapter.py:86–94 and auditenv/env.py:106–109 permit a lower initial budget. | “Reset returns `{task, manifest, policy, remaining_steps}`, with 100 remaining by default. Step returns `{result, error, remaining_steps}`.” |
| README.md:282 | auditenv/env.py:143–152 and judge_adapter.py:103–105,120–121. Closed submit reports accepted without validation feedback. An invalid train submit has null result and error `invalid_findings`. A timed-out action is truncated before submit handling. | “A processed submission ends the episode. Closed mode returns accepted with no correctness signal. Train mode can report `invalid_findings`.” |
| README.md:286–288 | auditenv/env.py:126–135,159–168 checks elapsed time when a step arrives, using the configured limits, and returns an `episode_over` response with the final flags and remaining budget. | “At the action limit (default 100), or on the next step once elapsed time exceeds the time limit (default 60 s from reset), the episode truncates with empty findings if a submission has not been processed.” |
| README.md:309 | Public-record probe on D01, which shares the D01–D05 config, seeds 0–199: default 199/200 and hard 200/200 have foreign-currency documents. Split refs, refunds, equal totals, unidentified receipts and ledger records on both boundary dates are 200/200 in each. | “Foreign-currency documents appeared in 199/200 default and 200/200 hard episodes.” |
| README.md:319 and CONTRACT.md:106–107 | `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r20-codex2/y2_public.py`, exit 0. With seed 25, `{n_invoices: 10, distractors: false, ensure_distractors: true, errors: {}}` prints `minimal ensure_distractors 25 refund: False split: True`. auditenv/generator.py:486–505 requires eligible full payments. | “`ensure_distractors` adds a split or refund when missing and suitable full payments are available. For D01–D05, the published configuration produced both on all 200 seeds per difficulty tested.” |
| README.md:326 | auditenv/matcher.py:20–28,39–46 also recognize invoice and payment IDs as public for validation, although generated evidence sets use doc, row and FX IDs. auditenv/transform.py:35–57 preserves FX IDs and emits distinct replacements. | “Generated evidence sets refer to row IDs, document IDs and FX IDs. Match validation accepts other known public IDs as extras. Keep row, document and FX evidence IDs distinct in a paired copy.” |
| README.md:327–328 | judge_adapter.py:85–88,130 both call auditenv/load.py:117–139, so the minimal fixture works for scoring and closed reset. The loader also accepts a missing truth issue scenario for grading. | “The shared loader accepts minimal jury fixtures without task or provenance files, explicit FX IDs or truth issue scenario labels. A missing task file yields an empty task string. The strict export verifier still requires complete exports.” |
| README.md:330–331,340 | auditenv/jury_run.py:36–43,78–86 keeps oracle in the grader while starting the three public policies as separate processes. Y1 printed `reconcile         1.000  1.000  1.000    0.959    21.3    26    0.024   0.026`. | “The three public policies run in separate processes over the jury protocol. The oracle runs grader-side.” Reconcile mean actions: 21.3. |
| CONTRACT.md:7 | Current night/TASKS.md is a round work queue assigning touched files. Many modules listed in the contract have no corresponding task in this round. | “Use the current `night/TASKS.md` for night task ownership.” |
| CONTRACT.md:38–40 | auditenv/verify.py:101–123 checks the sum against `max(payment.amount_minor, 0)`, so the documented inequality fails with a refund and zero refs. auditenv/generator.py:443–449 emits negative unreferenced payments. | “Positive remittance allocations sum to no more than the receipt amount. Refunds have negative payment amounts and no invoice refs.” |
| CONTRACT.md:51–55 | auditenv/generator.py:294–311 books a negative refund through signed cash and unapplied-cash postings. The current contract lists positive receipt directions only. | “For a refund, debit 2900 and credit 1000 at the payment-date rate.” |
| CONTRACT.md:113–117 | auditenv/grader_key.py:23–36 falls back to a process key when the key file cannot be used. auditenv/server.py:208–225 uses this helper by default for hidden queues. | “With no explicit secret, closed adapter generation and private queues use a random grader key file, with a per-process fallback if the file is unusable.” |
| CONTRACT.md:138–142,156 | auditenv/env.py:143–164 suppresses invalid-findings feedback and actual reward in eval. Run_server logging is optional on the filesystem, with in-memory grading at auditenv/env.py:171–184 and file append at auditenv/server.py:101–107. | “Invalid submissions terminate and are graded −1. Eval returns public reward 0.0 and keeps the grading result and error grader-side. With `--grader-log`, the server appends those results to the requested file.” |
2026-11-22 01:15 lead — L1 done. REVIEW.md Round 20, HANDOFF header, DESIGN posting-lag row updated. L2 waits for codex X2/Y1-Y3.
2026-11-22 01:32 gemini1a — G25: ran `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 33000-33299` (wall time 86.2 s, exit code 0).
  Totals line: `totals: a_pay_before_inv=0, a_ref_unknown=0, a_due_before_issue=0, b_cn_before_booking=0, b_cn_orphan=0, b_cn_not_full=0, b_reissue_before_orig=0, c_neg_credit=0, d_ledger_out_period=0, d_cutoff_item=3064, e_fx_missing=0, f_inv_booked_before_issue=2595, f_pay_posted_before_doc=0, f_ar_before_booking=26, f_inv_not_booked=0, f_pay_not_posted=0, f_overallocated=0, f_pay_entity=0, f_fx_posted=5057, c_tie=0`
  Unexplained violations line: `unexplained violations: 26 (0 in clean configs)`
  Logged for lead review: 26 instances of `f_ar_before_booking` (0 in clean configs, found in default/default (5), hard/hard (1), D14/default (6), D14/hard (4), D15/default (6), D15/hard (4)). Sample reproductions:
    default/default seed=33060 ids=['BNK-916419', 'INV-802246', 'GL-003665'] ar credit 2026-07-03T17:45:00+00:00 booking 2026-07-04T20:25:00+00:00
    hard/hard seed=33263 ids=['BNK-734657', '2609-638480', 'R469'] ar credit 2026-09-01T12:20:00+01:00 booking 2026-09-02T17:58:00+01:00
    D14/default seed=33011 ids=['RCPT0856798', 'F0453837', 'GL-003501'] ar credit 2026-05-04T14:57:00-05:00 booking 2026-05-04T19:37:00-05:00
2026-11-22 01:31 gemini1b — G26 complete (chronology and causality check on seeds 34000-34299).
Command: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 34000-34299`
Exit code: 0, wall time: 81.31 s
Totals line:
totals: a_pay_before_inv=0, a_ref_unknown=0, a_due_before_issue=0, b_cn_before_booking=0, b_cn_orphan=0, b_cn_not_full=0, b_reissue_before_orig=0, c_neg_credit=0, d_ledger_out_period=0, d_cutoff_item=3078, e_fx_missing=0, f_inv_booked_before_issue=2589, f_pay_posted_before_doc=0, f_ar_before_booking=13, f_inv_not_booked=0, f_pay_not_posted=0, f_overallocated=0, f_pay_entity=0, f_fx_posted=5036, c_tie=0
Unexplained violations line:
unexplained violations: 13 (0 in clean configs)
2026-11-22 01:35 gemini2a — G27: fuzz sweeps (default and hard, seeds 0-999) on generator fix 299c5e7. Default mode: exit 0, wall time 59.14s; summary: default mode, seeds 0-999: 3000 episodes (1987 dirty, 1013 clean) in 59.1 s; episodes with a problem (exception / verifier / oracle): 0; random explorer reward > 0: 246/3000 (0 on dirty books); flag-all reward < 0: 3000/3000; FUZZ PASSED. Hard mode: exit 0, wall time 146.82s; summary: hard mode, seeds 0-999: 3000 episodes (1991 dirty, 1009 clean) in 146.8 s; episodes with a problem (exception / verifier / oracle): 0; random explorer reward > 0: 268/3000 (0 on dirty books); flag-all reward < 0: 3000/3000; FUZZ PASSED. Total: 6000 episodes, 0 problems.
2026-11-22 01:28 gemini2b — G28: Ran config sweep and seed verification on generator fix 299c5e7. Commands and results:
  - `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 0`: exit 0, wall 1:28.40 (88.4 s). Summary: "config sweep, cases 0-2999: 3000 random configs (1186 hard) in 88.4 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 56" / "FUZZ PASSED".
  - `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 0-1999`: exit 0, wall 38.463s. Summary: "6000/6000 episodes valid; episodes with problems: 0".
  0 problems across 3,000 random configs and 6,000 generated episodes on seeds 0-1999.
2026-11-22 01:25 gemini3a — G29: Ran `env -u AUDITENV_SECRET uv run python -m auditenv.check` twice and `env -u AUDITENV_SECRET uv run python -X dev -W error::ResourceWarning -m unittest discover -s tests -t .`:
  - `auditenv.check` Run 1: exit 0, wall 51.27s, last line: "ALL CHECKS PASSED in 51.2 s"
  - `auditenv.check` Run 2: exit 0, wall 51.32s, last line: "ALL CHECKS PASSED in 51.2 s"
  - `python -X dev -W error::ResourceWarning -m unittest discover -s tests -t .`: exit 0, wall 50.67s, last line: "OK" (Ran 562 tests in 50.666s, zero ResourceWarnings or errors).
2026-11-22 01:21 gemini3b — G30: repeated G10 (export diff of dev/train/hard) and G24 (trajectory regeneration diff) on generator fix 299c5e7.
  Export diffs:
  - episodes/dev vs /tmp/r20-gemini3b/dev: diff exit code 0 (identical)
  - episodes/train vs /tmp/r20-gemini3b/train: diff exit code 0 (identical)
  - episodes/hard vs /tmp/r20-gemini3b/hard: diff exit code 0 (identical)
  Trajectory diffs:
  - trajectories.jsonl vs /tmp/r20-gemini3b/trajectories.jsonl: diff exit code 0 (identical)
  - trajectories/ vs /tmp/r20-gemini3b/trajectories/: diff exit code 0 (all 7 files identical)
  Differing files: none.

2026-11-22 01:22 codex2 — Y3 DESIGN and PITCH claims audit (round tip deb34dd).

Measurement runs (each used prefix `env -u AUDITENV_SECRET AUDITENV_KEY_FILE=/tmp/r20-codex2/grader.key uv run python` except the supplemental runs explicitly shown below):

| Command suffix | Exit | Wall s | Summary |
|---|---:|---:|---|
| `-m auditenv.check --json /tmp/r20-codex2/c.json` | 0 | 102.74 | `[PASS] unit tests — 562 tests, 0 failures, 0 errors`; `ALL CHECKS PASSED in 102.6 s` |
| `-m auditenv.analyze --policy naive_reconcile --config configs/dev.json` | 0 | 0.172 | 22 TP, 102 FP, 8 FN; F1 0.286; allocation recall 2/8 |
| `-m auditenv.analyze --policy reconcile --config configs/dev.json` | 0 | 0.192 | 30 TP, 0 FP/FN, F1 1.000 |
| `-m auditenv.analyze --policy reconcile --config configs/eval_hard.json` | 0 | 0.635 | 40 TP, 20 FP, 6 FN; F1 0.755; six missed duplicates, 43 actions mean |
| `-m auditenv.fuzz --seeds 0-199 --hard` | 0 | 57.273 | 600 episodes, 399 dirty/201 clean, 0 problems, random positive only on 47 clean, flag-all negative 600/600 |
| `-m auditenv.fuzz --stress reconcile_hard --seeds 0-299 --hard` | 0 | 36.403 | 1,200 episodes, imperfect 0, max steps 57, truncated 0 |
| `scripts/shortcut_miner.py --report-only --hard` | 0 | 94.800 | `Flagged values: 11`; customer/currency/total duplicate cue 4,878/13,690 |
| `-m auditenv.fuzz --configs 4000 --start 0` | 0 | 254.14 | 1,600 hard, 0 problems, max 56 |
| `-m auditenv.fuzz --configs 4000 --start 4000` | 0 | 253.32 | 1,625 hard, 0 problems, max 55 |
| `-m auditenv.fuzz --configs 4000 --start 8000` | 0 | 255.36 | 1,601 hard, 0 problems, max 56 |
| `-m auditenv.fuzz --configs 4000 --start 12000` | 0 | 255.83 | 1,609 hard, 0 problems, max 58 |
| `-m auditenv.fuzz --configs 4000 --start 16000` | 0 | 255.04 | 1,602 hard, 0 problems, max 59 |

The config sweep is deterministic by case number (auditenv/fuzz.py:82–108,117–142), so the five nonoverlapping shards replay exactly cases 0–19,999 of the documented command. All printed `FUZZ PASSED`. Combined 20,000 episodes, 8,037 hard, no problems, at most 59 actions. PITCH.md:62 reproduced. Full outputs are in `/tmp/r20-codex2/y3-*.out`.

Supplemental evidence:
- `env -u AUDITENV_SECRET uv run python scripts/sync_docs.py --check --json /tmp/r20-codex2/c.json`, exit 0, 0.051 s, `All documentation tables match measured data.` Includes the rounded DESIGN/PITCH deterministic tables. DESIGN dev times are host snapshots.
- Y1 default stress reproduced 1,200 episodes, 0 imperfect, max 33 and 0 truncations. For the four rows at DESIGN.md:323–326, ran `env -u AUDITENV_SECRET uv run python -m auditenv.run --policy POLICY --config /tmp/r20-codex2/DIFFICULTY-CASE.json` with 300 seeds per row and the matching configuration from auditenv.fuzz.STRESS. Recomputed median/nearest-rank p95/max from the printed action column. Results 22/26/28, 29/31/33, 44/50/53, 50/56/57 respectively.
- `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r20-codex2/y3_public.py` read public tables and checked current dev worked examples and counts. Used the Y1 dev reconcile trajectory for the replacement findings. For the naive FP breakdown, subtracted per-type TP counts from the terminal submitted types in `env -u AUDITENV_SECRET uv run python -m auditenv.run --policy naive_reconcile --config configs/dev.json --out /tmp/r20-codex2/naive.jsonl`. Both commands exited 0.

Source and measurement coverage:

| Documentation | Evidence checked |
|---|---|
| DESIGN.md:8–53 (design decisions, generator lifecycle, keys, units, size, time and postings) | auditenv/generator.py:49–55,60–113,123–155,176–206,237–329,346–418,540–569,577–639,705–719; auditenv/money.py:8–23,26–50; auditenv/env.py:17–38,106–109; auditenv/grader_key.py:15–59; Dockerfile:1–14 |
| DESIGN.md:55–106 (four issue families, interactions, worked examples and distractors) | auditenv/inject.py:45–272; auditenv/generator.py:346–418,424–538; current configurations and public records for seeds 2002, 2003 and 2005; Y1 dev trajectory and Y3 checked dev analysis |
| DESIGN.md:108–166 (API, isolation, matcher, reward, sensitivity) | auditenv/env.py:89–110,123–168,187–238; auditenv/server.py:92–128,168–195; auditenv/calculator.py; auditenv/schema.py; auditenv/matcher.py:26–46,68–149; auditenv/metrics.py:4–17; tests/test_reward_attacks.py and tests/test_judge_reward.py; Y1 sensitivity output |
| DESIGN.md:168–221 (verifier, evidence, repairs, replay and paired data) | auditenv/verify.py:101–124,170–214,343–428,464–478,663–707; schemas/manifest.schema.json; auditenv/transform.py:25–66; auditenv/check.py:165–259; night/archive/r1-LOG.md:50,229 and repository test coverage |
| DESIGN.md:223–345 (results, counts, analysis, measured sizing, budget, timing and edge cases) | Fresh check and analyze output below; Y1 sweep, stress, benchmark, golden and action test; hard sweep and stress; configs/dev.json and configs/eval_hard.json; scripts/bench.py:43–69,104–136; auditenv/experimental.py:8–48; .github/workflows/check.yml:41–63; listed test cases |
| DESIGN.md:347–398 (limitations and historical evidence) | Current shortcut miner output and public-data probe; auditenv/generator.py:402–505,508–538; auditenv/inject.py:45–75,233–272; auditenv/verify.py:29–54,92–124; auditenv/policies/reconcile.py:83–103; auditenv/metrics.py:14–17; REVIEW.md:315–320,393–400 and night/archive/r8-LOG.md:9 |
| PITCH.md:3–39 (purpose, demo, architecture, API, grader and reward) | Y1 demo output and grader replay; auditenv/generator.py:642–719; auditenv/inject.py:61–272; auditenv/env.py:17–38,89–110,123–168,187–238; auditenv/verify.py:663–707; auditenv/matcher.py:26–46,68–149; auditenv/metrics.py:4–17 |
| PITCH.md:41–74 (metrics, cohort structure, reproducibility, sweep, miner, training scope and team) | Fresh check JSON, hard analysis and fuzz below; tests/test_load.py and tests/test_trajectory_files.py; auditenv/check.py:165–259,301–326; Y1 chart regeneration and 22/22 mutations; current miner; no shipped model weights; SPEC.md:193–207 for deliverables |

Current discrepancies and suggested text:

| Doc line | Evidence | Correct text |
|---|---|---|
| DESIGN.md:14–18,116–121,241 | The native interface and stdio policy protocol expose only public observations. The default external worker uses the repo root and same account (auditenv/jury_run.py:43–50). Isolation flags apply only with the policy Docker image (44–46; Dockerfile:3–8). The smoke gate checks a two-episode public cohort for reward and particular grading markers (auditenv/check.py:262–283). Current `reconcile_hard` F1 is 1.000. | “The policy interface exposes public records. For untrusted processes use the isolated policy container. The two-episode out-of-process smoke test passed. Hard mode challenges the default rules, and a hard-aware rule script solves the benchmark.” |
| DESIGN.md:16 | Y1 tested 11,000 reward mutations on 20 seeds, with zero violations. auditenv/matcher.py:39–46,125–136 compares supplied fields, independent of intent, with the explanation excluded. A finite search cannot establish the unconditional claim that reward cannot be gamed. | “The matcher checks fields and evidence and disregards explanation text. The tested mutations did not beat the honest answer.” |
| DESIGN.md:34–39,217–218; PITCH.md:12 | auditenv/generator.py:108–113,123–129,705–719 includes the key and supports a transform. The same key/config/actions replay deterministically if the wall clock does not truncate. Public probes found default seed 27 with 434 ledger rows. The 230–420/900–1,400 ledger padding targets are in auditenv/generator.py:540–559, while strict bounds 200–2,000 rows and 20–200 documents are at auditenv/verify.py:427. | “With the same key, seed, version and config, including any transform seed, the episode is reproducible. Action replay is subject to the wall-clock limit. Default history is padded toward 230–420 ledger rows before injection. Strict exports allow 200–2,000 ledger rows and 20–200 documents.” |
| DESIGN.md:61,65–67,75–77 | auditenv/inject.py:45–53 uses local/UTC dates or offsets +1,+2,+3,+5,+7,−1,−2,−3,−5. I1 at 246–251 picks the first candidate with a ≥10-minor-unit difference, including the bank date when it qualifies, otherwise +1,+2,+3,−1, with +1 fallback. I1/I2 deliberately share a document between two issues (233–272). | “Single FX errors try the document’s local/UTC dates and selected nearby dates. I1 prioritizes the bank date if it qualifies, then tries +1, +2, +3 and −1. Interacting scenarios intentionally affect the same document twice.” |
| DESIGN.md:84–85,89 | At dev seed 2003, ep_14eca11ac929, public generation under configs/dev.json produced none of the claimed R1344/R1350/R1509/R1520 ledger IDs. The old PAY-874814 now remits USD 501.45 for INV-587848. The Y1 reconcile replay matched all four current findings. | “Duplicate INV-441644 and INV-588950 are both GBP 6,787.00 for CUST52061, identical lines, both issued Sept 26, with AR rows R4132/R4153; later AR debit 831,638 USD minor. PAY-779598 remits USD 8,371.00 for INV-336399 and row R4163 credits only unapplied cash; allocation shortfall 837,100 USD minor. I2 INV-959754 (GBP 8,974.00) issued Oct 1, booked Sept 30 in R4224 for 1,110,820 USD minor. Its issue-date rate 1.24037 yields 1,113,108, so FX error is 2,288 USD minor.” Seeds 2002 and 2005 examples still matched. |
| DESIGN.md:93–106 | auditenv/generator.py:361–378,424–481 uses random and conditional creation for several distractors. On seeds 0–199 in unforced default, 192/200 episodes had any split and 155/200 had any refund; hard 191/200 and 159/200. `errors: {}` plus nonzero `interacting` still injects issues (generator.py:93–96,561–569). | “Zero error and interaction counts specify clean books. With distractors enabled the generator can add these legitimate patterns; the available patterns vary by company.” |
| DESIGN.md:113–116,337–339 | auditenv/env.py:126–135,143–168 uses configured limits. It checks elapsed time on receipt of a step, before treating that action as a submit. Invalid `submit` returns details only in train mode (146–152). | “At the configured action limit or the next action after the deadline, the episode truncates with empty findings unless a submission was processed. Defaults are 100 actions and 60 s. The grader records −1 for invalid submissions; train also returns it publicly.” |
| DESIGN.md:145 | auditenv/metrics.py:14–17 subtracts 0.002 per inspection even when base F1 differs; DESIGN.md:387–389 gives the resulting counterexample. | “Step cost breaks equal-F1 ties and can reverse the ordering for small differences in F1.” |
| DESIGN.md:155–162 | Y1 `uv run python scripts/sensitivity.py` exited 0 in 1.860 s. Both rankings stay unchanged, but five rows have drift. | “At costs 0.001/0.002/0.005, then tolerances 0/1/100: dev reconcile 0.978/0.956/0.891 and 0.956/0.956/0.956; dev naive −0.467/−0.480/−0.519 and −0.480/−0.480/−0.480; hard reconcile_hard 0.958/0.916/0.790 and 0.916/0.916/0.916; hard reconcile 0.329/0.293/0.186 and 0.293/0.293/0.293; hard naive −0.683/−0.704/−0.765 and −0.704/−0.704/−0.704.” |
| DESIGN.md:220 | The paired gate checks original findings for zero TP on transformed dirty episodes. With zero truth issues, empty findings still score F1=1 (auditenv/check.py:230–249; auditenv/metrics.py:6–11). | “Translated oracle answers retain their grade; on dirty paired episodes the old unmodified answer earns zero TP.” |
| DESIGN.md:247–252 | Y1 default sweep printed `default mode, seeds 0-999: 3000 episodes (1987 dirty, 1013 clean) in 86.5 s` and `random explorer reward > 0: 246/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)`. The dirty oracle threshold enforced by the sweep is >0.9 (auditenv/fuzz.py:45–52); the summary does not assert exact 1.0 on each dirty episode. Hard positive count remains 47. | “1,987 dirty and 1,013 clean, 246 positive random returns, all clean. The seed sweep requires oracle score >0.9 on dirty episodes and 1.0 on clean episodes.” |
| DESIGN.md:258,261–265 | `auditenv.analyze --policy naive_reconcile --config configs/dev.json` printed `payment_allocation | 2 | 6 | 0.25` and `Total | 102`. Subtracting its per-type TP from counts of submitted types in the public dev trajectory gives 27 allocation, 30 duplicate, 27 FX and 18 cutoff FPs, with 22 on clean companies. | “Naive allocation recall 2/8, 102 total FPs, 27 allocation FPs.” |
| DESIGN.md:308–317 | Timing is tied to the Round 11 benchmark in night/archive/r11-LOG.md:39. Y1 benchmark on this revision measured 0.251/0.905 s for default/hard generation, 1.972 s for verifier, 2.65–5.94/6.95–12.60 ms for dev/hard single episodes. | “Historical Round 11 timing snapshot” if retaining the old table, or use the current host values with the same workload labels. |
| DESIGN.md:352–355 | auditenv/server.py:208–225 calls the same private-key helper for `--episodes` unless `--public` is selected. auditenv/grader_key.py:23–36 handles a missing env var and file fallback. A shared key can reproduce a company on another machine. | “Hidden server queues and the jury adapter use `AUDITENV_SECRET` or a persistent grader key by default, with process fallback if needed. Reproduction requires the same key. `--public` opts the server queue into public generation.” |
| DESIGN.md:357–375; PITCH.md:68 | Miner default 16 and hard 11 flagged values. Current duplicate feature is 4,918/4,936 (0.996) default and 4,878/13,690 (0.356) hard. Current hard retyped-token peak 44/96 (0.458); old 0.449/0.467 are historical. Default 2900 repeat amount 214/222 (0.964); 2900 period-end allocation cue 0.789. Other scoped historical rates at REVIEW.md:315–320 were retained as historical evidence rather than measured by this miner command. | “The invoice customer/currency/total heuristic has precision 0.996 default and 0.356 hard on the current run. The actual rule also checks line items. The default 2900 repeated-amount cue was 214 of 222, and the default 2900 period-end allocation cue was 0.789.” Qualify historical measurements by revision and configuration. |
| DESIGN.md:379–382 | Public refs and totals on seeds 0–199 yielded 4,688 default and 4,697 hard settled invoices, zero over-settlements. Code checks per-payment refs at auditenv/verify.py:101–124. The historical extra-future-payment example does not establish an unlimited generator guarantee. | “The verifier checks remittance amounts per payment. In the current 400-episode public sample, 0 of 9,385 settled invoices were over-settled.” |
| DESIGN.md:390–397 | Fresh check: default reconcile F1 1.000, hard 0.755, hard-aware 1.000. The Round 18 evidence applies to that sample (night/archive/r18-LOG.md:82; REVIEW.md:393–400), not all inputs or agents. The stated 44 groups require both difficulties for all 20 jury configs plus four non-jury groups; ‘default, hard, heavy’ alone names only three. | “The default rules score F1 0.755 on the hard split. The hard-aware policy scores 1.000. Learnability was not measured. In Round 18 an independent checker without a three-day restriction reproduced results on the documented sample.” Enumerate all four non-jury settings if retaining the 44,000 breakdown. |
| PITCH.md:24 | On 200 explicitly clean default episodes the public probe found a split on 186 and a refund on 148, with checkable generators at auditenv/generator.py:424–481. | “Clean books can include split payments, refunds and recurring charges.” |
| PITCH.md:43 | The deterministic table matches fresh check JSON, but the referenced docs/baselines.svg still shows older means. Y1 chart comparisons named four drifted labels. | “Use the chart regenerated from this revision’s check JSON.” |
2026-11-22 01:47 lead — Merged G25-G30 and codex2 Y1-Y3. Fix re-tests green (chronology 600 more seeds 0 unexplained in clean configs; fuzz 0-999 both difficulties; config sweep 3000; verify 0-1999 6000/6000; check x2; exports and trajectories byte-identical). codex2 found docs/baselines.svg stale (pre-r18 returns) — regenerated; sync_docs now renders the chart and reports drift (test_stale_chart_is_drift). Y1: 36/36 eligible README commands exit 0. Y2/Y3 doc discrepancies (stale numbers in prose, seed-2003 worked example ids, sensitivity rows, refund remittance/posting in CONTRACT, ensure_distractors wording, key defaults) delegated to a lead subagent that re-verifies each before editing.
2026-11-22 01:56 gemini1a — G31: ran `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 35000-35599` (wall time 167.0 s, exit code 0).
  Totals line: `totals: a_pay_before_inv=0, a_ref_unknown=0, a_due_before_issue=0, b_cn_before_booking=0, b_cn_orphan=0, b_cn_not_full=0, b_reissue_before_orig=0, c_neg_credit=0, d_ledger_out_period=0, d_cutoff_item=6178, e_fx_missing=0, f_inv_booked_before_issue=5271, f_pay_posted_before_doc=0, f_ar_before_booking=34, f_inv_not_booked=0, f_pay_not_posted=0, f_overallocated=0, f_pay_entity=0, f_fx_posted=10141, c_tie=0`
  Unexplained violations line: `unexplained violations: 34 (0 in clean configs)`
  Logged for lead review: 34 instances of `f_ar_before_booking` (0 in clean configs, found in default/default (8), hard/hard (6), D14/default (5), D14/hard (5), D15/default (5), D15/hard (5)). Sample reproductions:
    default/default seed=35012 ids=['PAY-609369', 'SI-2026-820954', 'GL-001535'] ar credit 2026-11-03T21:12:00+05:30 booking 2026-11-04T12:49:00+05:30
    hard/hard seed=35325 ids=['RCPT0071974', 'F0102081', 'R4524'] ar credit 2026-02-02T18:50:00+01:00 booking 2026-02-04T17:51:00+01:00
    D14/default seed=35043 ids=['RCPT0721714', 'INV-456057', 'R4120'] ar credit 2025-10-04T09:07:00+09:00 booking 2025-10-04T21:38:00+09:00
2026-11-22 01:55 gemini1b — G32 complete (chronology check on seeds 36000-36599).
Command: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 36000-36599`
Exit code: 0, wall time: 171.19 s
Totals line:
totals: a_pay_before_inv=0, a_ref_unknown=0, a_due_before_issue=0, b_cn_before_booking=0, b_cn_orphan=0, b_cn_not_full=0, b_reissue_before_orig=0, c_neg_credit=0, d_ledger_out_period=0, d_cutoff_item=6132, e_fx_missing=0, f_inv_booked_before_issue=5177, f_pay_posted_before_doc=0, f_ar_before_booking=46, f_inv_not_booked=0, f_pay_not_posted=0, f_overallocated=0, f_pay_entity=0, f_fx_posted=10061, c_tie=3
Unexplained violations line:
unexplained violations: 46 (0 in clean configs)
2026-11-22 01:54 lead — Applied codex2 Y2/Y3 doc corrections (subagent re-verified each; skipped rewording-only items and the CONTRACT:7 TASKS remark). check 563 tests pass, sync_docs no drift, doc tests 19 OK. Commit c8b8d70.
