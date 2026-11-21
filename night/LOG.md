2026-11-22 03:38 lead — Round 21 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/r20 archive. Baseline check at 2f7b31e: exit 0, 50.9 s. Wrote TASKS.md: codex1 independent text-only auditor / double-entry re-derivation / extreme configs; codex2 jury-copy file-format robustness, slow-machine timing, README first read; rb chronology+policy_text+adapter on new seeds; gemini sweeps on unseen seeds. Assumption: generator/product fixes stay with lead (single re-export owner).
2026-11-22 03:43 gemini2b — G10 complete. Re-exported dev, train, and hard splits into /tmp/r21-gemini2b/ and diffed against committed episodes/:
- dev: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/dev.json --out /tmp/r21-gemini2b/dev` (exit 0, wall time 0.119s, "Exported 10 episodes to /tmp/r21-gemini2b/dev") && `diff -r episodes/dev /tmp/r21-gemini2b/dev` (exit 0, 0 files differ).
- train: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/train.json --out /tmp/r21-gemini2b/train` (exit 0, wall time 0.120s, "Exported 10 episodes to /tmp/r21-gemini2b/train") && `diff -r episodes/train /tmp/r21-gemini2b/train` (exit 0, 0 files differ).
- hard: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/eval_hard.json --out /tmp/r21-gemini2b/hard` (exit 0, wall time 0.374s, "Exported 20 episodes to /tmp/r21-gemini2b/hard") && `diff -r episodes/hard /tmp/r21-gemini2b/hard` (exit 0, 0 files differ).
All 40 exported episodes across all three splits are byte-for-byte identical to the committed exports (0 differing files). Next: G11.
2026-11-22 03:49 rb — Z1 done. Fresh-seed reruns of the round-20 independent checkers (no product changes).
  (1) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 42000-42299` → exit 0, wall 111 s.
  `episodes checked: 12600 (seeds 42000-42299, 42 configs)`
  Totals line verbatim: `totals: a_pay_before_inv=0, a_ref_unknown=0, a_due_before_issue=0, b_cn_before_booking=0, b_cn_orphan=0, b_cn_not_full=0, b_reissue_before_orig=0, c_neg_credit=0, d_ledger_out_period=0, d_cutoff_item=3057, e_fx_missing=0, f_inv_booked_before_issue=2615, f_pay_posted_before_doc=0, f_ar_before_booking=21, f_inv_not_booked=0, f_pay_not_posted=0, f_overallocated=0, f_pay_entity=0, f_fx_posted=5042, c_tie=1`
  `unexplained violations: 21 (0 in clean configs)` — all 21 are `f_ar_before_booking` in configs that inject period_cutoff
  (default/default 5, hard/hard 4, D14/default 2, D14/hard 4, D15/default 2, D15/hard 4), matching the lead's round-20
  explanation (night/archive/r20-LOG.md 02:44: remaining hits are the prior-period invoice itself). Clean D01–D05: 0.
  Sample reproductions verbatim:
    default/default seed=42089 f_ar_before_booking ids=['RCPT0400010', '2507-414083', 'L01292'] ar credit 2025-07-02T23:50:00+00:00 booking 2025-07-04T20:53:00+00:00
    hard/hard seed=42045 f_ar_before_booking ids=['BNK-318927', 'INV-908173', 'R163'] ar credit 2026-10-02T13:16:00+03:00 booking 2026-10-03T21:26:00+03:00
    D14/default seed=42037 f_ar_before_booking ids=['RCPT0739458', 'F0922045', 'GL-003378'] ar credit 2025-11-02T15:55:00+03:00 booking 2025-11-03T16:40:00+03:00
    D15/hard seed=42228 f_ar_before_booking ids=['RCPT0737735', '2511-562760', 'R185'] ar credit 2025-11-02T19:26:00+03:00 booking 2025-11-02T21:22:00+03:00
  Full output kept at /tmp/r21-rb/z1_chronology.out (all 21 lines listed there).
  (2) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/policy_text.py --seeds 42000-42199` → exit 0, wall 157 s.
  Final line verbatim: `Audited 8400 episodes across 42 configurations; 33043340 checks, 0 unexpected failures.`
  Next: Z2 (scenarios_adapter on seeds 43000–43004). Assumption: the 21 non-clean f_ar_before_booking hits are the known
  period_cutoff pattern, not a new defect — flagged for lead confirmation, no product code touched.

2026-11-22 03:47 codex1 — X1 text-only auditor. `env -u AUDITENV_SECRET uv run python -m night.r21.text_auditor` → exit 0, 150.76 s, 4,200 episodes.

| Config | Difficulty | Scored | Mean F1 | Mean precision | Mean recall |
|---|---|---:|---:|---:|---:|
| baseline | default | 100 | 1.000000 | 0.990000 | 0.990000 |
| baseline | hard | 100 | 1.000000 | 0.980000 | 0.980000 |
| D01 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D01 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D02 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D02 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D03 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D03 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D04 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D04 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D05 | default | 100 | 1.000000 | 0.000000 | 0.000000 |
| D05 | hard | 100 | 1.000000 | 0.000000 | 0.000000 |
| D06 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D06 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D07 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D07 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D08 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D08 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D09 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D09 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D10 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D10 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D11 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D11 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D12 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D12 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D13 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D13 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D14 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D14 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D15 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D15 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D16 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D16 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D17 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D17 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D18 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D18 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D19 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D19 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |
| D20 | default | 100 | 1.000000 | 1.000000 | 1.000000 |
| D20 | hard | 100 | 1.000000 | 1.000000 | 1.000000 |

Discrepancy entries: 0

Assumptions: use the public manifest for episode ID and currency exponents, compare hard-mode descriptions without case or punctuation, and use zero inspection steps because the audit reads public exports directly. Closed runs use the local default grader key. Clean episodes have F1 1 with precision and recall 0 by the grader convention. No misses or extras. `env -u AUDITENV_SECRET uv run python -m auditenv.check` → exit 0, ALL CHECKS PASSED in 148.2 s. Next: X2.
2026-11-22 03:50 gemini1a — G1 complete: ran fuzz sweep on seeds 13000-13999 default and hard modes. Commands: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 13000-13999` (exit 0, wall 61.2 s): default mode, seeds 13000-13999: 3000 episodes (1990 dirty, 1010 clean) in 61.2 s, episodes with a problem: 0, random explorer reward > 0: 229/3000, flag-all reward < 0: 3000/3000, FUZZ PASSED; `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 13000-13999 --hard` (exit 0, wall 400.9 s): hard mode, seeds 13000-13999: 3000 episodes (1980 dirty, 1020 clean) in 400.9 s, episodes with a problem: 0, random explorer reward > 0: 242/3000, flag-all reward < 0: 3000/3000, FUZZ PASSED. Total 6,000 episodes, 0 problems. Next: G2. Assumptions: none.
2026-11-22 03:42 gemini1b — G4 stress solvability on seeds 10000-10299: reconcile default 1200 episodes imperfect 0, max steps 33, truncated 0 (wall time 7.7 s); reconcile_hard 1200 hard episodes imperfect 0, max steps 57, truncated 0 (wall time 21.4 s). Next: G5.

2026-11-22 03:51 gemini1b — G5 fuzz sweep on seeds 14000-14999: default mode 3000 episodes (1983 dirty, 1017 clean) in 109.7 s, problems 0, random explorer reward > 0 on dirty books 0, flag-all < 0 3000/3000, FUZZ PASSED (wall time 109.8 s); hard mode 3000 episodes (1989 dirty, 1011 clean) in 423.5 s, problems 0, random explorer reward > 0 on dirty books 0, flag-all < 0 3000/3000, FUZZ PASSED (wall time 423.5 s). Next: G6.
2026-11-22 03:42 gemini3a — G13: Four jury modules 5 times (tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired). All 5 runs passed 73/73 tests cleanly.
  Run 1: Ran 73 tests in 2.094s, OK, exit 0, wall time 2s
  Run 2: Ran 73 tests in 2.083s, OK, exit 0, wall time 2s
  Run 3: Ran 73 tests in 2.225s, OK, exit 0, wall time 3s
  Run 4: Ran 73 tests in 2.249s, OK, exit 0, wall time 2s
  Run 5: Ran 73 tests in 2.528s, OK, exit 0, wall time 3s
  Total: 365 tests, 0 failures. Next: G14.
2026-11-22 03:42 gemini3a — G14: Ran attack search and sensitivity analysis. Both passed cleanly (exit 0).
  - auditenv.attack: PASSED, 20 seeds evaluated (5 clean, 15 dirty), 11,000 mutations tested across 10 families, 0 violations detected, elapsed 0.360 s, exit 0, wall time 0s.
  - scripts/sensitivity.py: PASSED, evaluated dev (10 episodes) and hard (20 episodes) across varied step cost (0.001, 0.002, 0.005) and amount tolerance (0, 1, 100 units). Ranking unchanged across all settings: dev (oracle > reconcile > naive_reconcile > random > flag_all), hard (oracle > reconcile_hard > reconcile > naive_reconcile > random > flag_all). Re-grade with default parameters reproduced every env reward exactly in 2.1 s, exit 0, wall time 3s. Next: G15.
2026-11-22 03:42 gemini3b — G16 complete: verified all splits under episodes/ (dev: 10/10 valid, exit 0, 0.13s; hard: 20/20 valid, exit 0, 0.35s; train: 10/10 valid, exit 0, 0.11s). Next: G17.
2026-11-22 03:47 gemini3a — G15: Ran full unit test suite under two hashseed/timezone settings. Both passed cleanly (0 failures).
  - Run 1 (PYTHONHASHSEED=7 TZ=America/St_Johns): Ran 563 tests in 106.623s, OK, exit code: 0, wall time: 107s
  - Run 2 (PYTHONHASHSEED=99 TZ=Pacific/Chatham): Ran 563 tests in 116.834s, OK, exit code: 0, wall time: 117s
  All G13-G15 tasks for gemini3a complete.
2026-11-22 03:42 gemini3b — G16 complete: verified all splits under episodes/ (dev: 10/10 valid, exit 0, 0.13s; hard: 20/20 valid, exit 0, 0.35s; train: 10/10 valid, exit 0, 0.11s). Next: G17.
2026-11-22 03:51 gemini2b — G11 complete:
- `uv run python scripts/golden.py --check` (exit 0, wall time 1.262s): "All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2b/tests/golden_hashes.json."
- `uv run python scripts/mutate_reward.py` (exit 0, wall time 407.340s): "22/22 mutants killed."
Next: G12.
2026-11-22 03:43 codex2 — Y1: `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m night.r21.jury_copy` exited 0 (2.19 s). Cohort chosen to include clean, interacting, and other dirty cases: dev 2000/2002/2003/2004/2009, hard 9100/9105/9109/9112/9119. Public reconciler reference answers reached F1 1.000, then the same inspection and submission actions were replayed through closed reset and independently scored.

| Variant | Accepted | Rejected | Scores equal |
|---|---:|---:|---:|
| CSV columns shuffled | 10 | 0 | 10 |
| CRLF | 10 | 0 | 10 |
| CSV BOM | 10 | 0 | 10 |
| JSON BOM | 10 | 0 | 10 |
| JSONL BOM | 10 | 0 | 10 |
| No final newline | 10 | 0 | 10 |
| Pretty JSON | 10 | 0 | 10 |
| Compact JSON | 10 | 0 | 10 |
| JSONL keys reversed | 10 | 0 | 10 |
| Combined | 10 | 0 | 10 |

Semantically equivalent rewrite discrepancies: 0. Combined uses compact JSON, all three BOMs, shuffled CSV, reversed JSONL keys, CRLF, and no final newline. Next: Y2 low-QoS and loaded timing.

2026-11-22 03:42 gemini1b — G4 stress solvability on seeds 10000-10299: reconcile default 1200 episodes imperfect 0, max steps 33, truncated 0 (wall time 7.7 s); reconcile_hard 1200 hard episodes imperfect 0, max steps 57, truncated 0 (wall time 21.4 s). Next: G5.
2026-11-22 03:42 gemini3a — G13: Four jury modules 5 times (tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired). All 5 runs passed 73/73 tests cleanly.
  Run 1: Ran 73 tests in 2.094s, OK, exit 0, wall time 2s
  Run 2: Ran 73 tests in 2.083s, OK, exit 0, wall time 2s
  Run 3: Ran 73 tests in 2.225s, OK, exit 0, wall time 3s
  Run 4: Ran 73 tests in 2.249s, OK, exit 0, wall time 2s
  Run 5: Ran 73 tests in 2.528s, OK, exit 0, wall time 3s
  Total: 365 tests, 0 failures. Next: G14.
2026-11-22 03:42 gemini3b — G16 complete: verified all splits under episodes/ (dev: 10/10 valid, exit 0, 0.13s; hard: 20/20 valid, exit 0, 0.35s; train: 10/10 valid, exit 0, 0.11s). Next: G17.

2026-11-22 03:51 codex2 — Y2: timed the four jury modules and closed jury runner under macOS low QoS, six parallel hard fuzz sweeps, and both conditions together.

Commands below are run from the repo root and prefixed with `/usr/bin/time -p`. Measured elapsed wall time is the `real` value. Set `TMPDIR=/tmp/r21-codex2 AUDITENV_KEY_FILE=/tmp/r21-codex2/timing.key` and unset `AUDITENV_GRADER_LOG` for scratch isolation.

```sh
taskpolicy -c background env -u AUDITENV_SECRET uv run python -m unittest tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired
taskpolicy -c background env -u AUDITENV_SECRET uv run python -m auditenv.jury_run
env -u AUDITENV_SECRET uv run python -m unittest tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired
env -u AUDITENV_SECRET uv run python -m auditenv.jury_run
env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 0-999 --hard
```

The two normal-priority commands were launched concurrently with six background copies of the last command. I also launched both low-QoS commands together while all six fuzz processes were active. macOS 26.6, four performance and six efficiency cores. Low QoS is the requested scheduling proxy.

| Condition | Run | Exit | Wall seconds | Summary |
|---|---|---:|---:|---|
| Low QoS | Four jury test modules | 0 | 7.32 | Ran 73 tests in 7.096s; OK |
| Low QoS | Jury runner | 0 | 7.32 | 20 jury scenarios D01-D20; maximum episode 0.451 s |
| Six fuzz processes | Four jury test modules | 0 | 7.40 | Ran 73 tests in 7.154s; OK |
| Six fuzz processes | Jury runner | 0 | 3.27 | 20 jury scenarios D01-D20; maximum episode 0.052 s |
| Low QoS plus fuzz | Four jury test modules | 0 | 423.94 | Ran 73 tests in 370.886s; OK |
| Low QoS plus fuzz | Jury runner | 0 | 424.04 | 20 jury scenarios D01-D20; maximum episode 54.050 s |

No timing-related failure appeared. The combined run's slowest episode was random_explorer at 54.050 s (5.950 s short of the 60 s episode limit), while reconcile peaked at 3.097 s. In all three runs, reconcile and oracle had F1 1.000 and mean returns 0.959 and 1.000 respectively; random_explorer and flag_all returned -1.000.

| Fuzz process | Exit | Wall seconds | Summary |
|---|---:|---:|---|
| 1 | 0 | 447.61 | 3000 episodes, 0 problems, FUZZ PASSED |
| 2 | 0 | 445.33 | 3000 episodes, 0 problems, FUZZ PASSED |
| 3 | 0 | 445.17 | 3000 episodes, 0 problems, FUZZ PASSED |
| 4 | 0 | 444.75 | 3000 episodes, 0 problems, FUZZ PASSED |
| 5 | 0 | 447.61 | 3000 episodes, 0 problems, FUZZ PASSED |
| 6 | 0 | 448.35 | 3000 episodes, 0 problems, FUZZ PASSED |

Next: Y3 fresh-clone README walkthrough.
2026-11-22 03:43 gemini2b — G10 complete. Re-exported dev, train, and hard splits into /tmp/r21-gemini2b/ and diffed against committed episodes/:
- dev: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/dev.json --out /tmp/r21-gemini2b/dev` (exit 0, wall time 0.119s, "Exported 10 episodes to /tmp/r21-gemini2b/dev") && `diff -r episodes/dev /tmp/r21-gemini2b/dev` (exit 0, 0 files differ).
- train: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/train.json --out /tmp/r21-gemini2b/train` (exit 0, wall time 0.120s, "Exported 10 episodes to /tmp/r21-gemini2b/train") && `diff -r episodes/train /tmp/r21-gemini2b/train` (exit 0, 0 files differ).
- hard: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/eval_hard.json --out /tmp/r21-gemini2b/hard` (exit 0, wall time 0.374s, "Exported 20 episodes to /tmp/r21-gemini2b/hard") && `diff -r episodes/hard /tmp/r21-gemini2b/hard` (exit 0, 0 files differ).
All 40 exported episodes across all three splits are byte-for-byte identical to the committed exports (0 differing files). Next: G11.
2026-11-22 03:42 gemini3a — G14: Ran attack search and sensitivity analysis. Both passed cleanly (exit 0).
  - auditenv.attack: PASSED, 20 seeds evaluated (5 clean, 15 dirty), 11,000 mutations tested across 10 families, 0 violations detected, elapsed 0.360 s, exit 0, wall time 0s.
  - scripts/sensitivity.py: PASSED, evaluated dev (10 episodes) and hard (20 episodes) across varied step cost (0.001, 0.002, 0.005) and amount tolerance (0, 1, 100 units). Ranking unchanged across all settings: dev (oracle > reconcile > naive_reconcile > random > flag_all), hard (oracle > reconcile_hard > reconcile > naive_reconcile > random > flag_all). Re-grade with default parameters reproduced every env reward exactly in 2.1 s, exit 0, wall time 3s. Next: G15.
2026-11-22 03:42 gemini3b — G17 complete: ran `yes '' | env -u AUDITENV_SECRET uv run python -m auditenv.demo` (exit 0, wall time 0.13s). Quoted final score lines: `terminal reward 0.958 = clip(2*F1 - 1 - 0.002*21 steps)   P=1.00 R=1.00 F1=1.00`; section 4 rewards: oracle 1.000, reconcile 0.958, silence -1.000, repeated twice 0.333, clean silence 1.000, clean reconcile 0.958; section 5 closed run: `policy side: 22 steps, rewards seen = [0.0], final info = {}`, `grader log : reward 0.958, F1 1.00, TP 4 FP 0 FN 0`. Compared with docs/DEMO.md: all numbers match exactly (326 ledger rows, 69 invoices, 100 budget steps; 21 inspect + 1 submit step; return 0.958; FX error 286 cents / $2.86, allocation error 351,331 cents / $3,513.31; oracle 1, repeated 0.333, silence -1; 22 actions, empty info, TP 4 FP 0 FN 0, return 0.958). Zero differences found. Next: G18.

2026-11-22 03:53 codex1 — X2 independent ledger identity audit. `env -u AUDITENV_SECRET uv run python -m night.r21.ledger_identity` → exit 1 as specified when unexplained violations exist, 186.64 s, 12,600 episodes. Table cells show checks / explained violations / unexplained violations.

Clean seed 41005 D01–D05/default: GL-005102 credits 83,185 GBP minor; GL-005178 debits 84,108 for a full EUR 98,314 refund at its later payment-date rate. Account 2900 ends at −923 GBP minor. Clean seed 41007 D01–D05/default: F0057818 booked at 2,042,681 EUR minor (R2494); individually rounded cash applications of 1,376,137 (R2558) and 666,545 (R2705) leave AR at −1. These exposures follow the specified date and rounding rules. Resolving either needs an accounting convention change.

Assumptions: pre-period invoices carry their face amount at the invoice-date rate as opening AR; account 2900 starts at zero; at tied instants increases precede decreases. FX checks use the public document rate and remittance, with zero required when there is no difference. The audit treats negative balances as violations even when a documented rate or rounding rule explains the arithmetic, because the task only exempts a violation caused by an injected error. `env -u AUDITENV_SECRET uv run python -m auditenv.check` → exit 0, ALL CHECKS PASSED in 148.1 s. Next: X3.

| Config | Difficulty | journal | ar_running | ar_close | unapplied_running | fx | trial |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline | default | 47,800 / 0 / 0 | 19,653 / 27 / 35 | 15,742 / 888 / 0 | 1,777 / 0 / 85 | 7,870 / 187 / 0 | 300 / 0 / 0 |
| baseline | hard | 168,387 / 0 / 0 | 21,111 / 43 / 43 | 16,590 / 843 / 0 | 1,756 / 0 / 78 | 7,815 / 168 / 0 | 300 / 0 / 0 |
| D01 | default | 45,672 / 0 / 0 | 19,152 / 0 / 33 | 15,463 / 0 / 0 | 1,582 / 0 / 104 | 8,029 / 0 / 0 | 300 / 0 / 0 |
| D01 | hard | 167,997 / 0 / 0 | 21,081 / 0 / 50 | 16,515 / 0 / 0 | 1,507 / 0 / 80 | 8,041 / 0 / 0 | 300 / 0 / 0 |
| D02 | default | 45,672 / 0 / 0 | 19,152 / 0 / 33 | 15,463 / 0 / 0 | 1,582 / 0 / 104 | 8,029 / 0 / 0 | 300 / 0 / 0 |
| D02 | hard | 167,997 / 0 / 0 | 21,081 / 0 / 50 | 16,515 / 0 / 0 | 1,507 / 0 / 80 | 8,041 / 0 / 0 | 300 / 0 / 0 |
| D03 | default | 45,672 / 0 / 0 | 19,152 / 0 / 33 | 15,463 / 0 / 0 | 1,582 / 0 / 104 | 8,029 / 0 / 0 | 300 / 0 / 0 |
| D03 | hard | 167,997 / 0 / 0 | 21,081 / 0 / 50 | 16,515 / 0 / 0 | 1,507 / 0 / 80 | 8,041 / 0 / 0 | 300 / 0 / 0 |
| D04 | default | 45,672 / 0 / 0 | 19,152 / 0 / 33 | 15,463 / 0 / 0 | 1,582 / 0 / 104 | 8,029 / 0 / 0 | 300 / 0 / 0 |
| D04 | hard | 167,997 / 0 / 0 | 21,081 / 0 / 50 | 16,515 / 0 / 0 | 1,507 / 0 / 80 | 8,041 / 0 / 0 | 300 / 0 / 0 |
| D05 | default | 45,672 / 0 / 0 | 19,152 / 0 / 33 | 15,463 / 0 / 0 | 1,582 / 0 / 104 | 8,029 / 0 / 0 | 300 / 0 / 0 |
| D05 | hard | 167,997 / 0 / 0 | 21,081 / 0 / 50 | 16,515 / 0 / 0 | 1,507 / 0 / 80 | 8,041 / 0 / 0 | 300 / 0 / 0 |
| D06 | default | 46,915 / 0 / 0 | 19,416 / 0 / 39 | 15,771 / 0 / 0 | 1,556 / 0 / 107 | 7,876 / 0 / 0 | 300 / 0 / 0 |
| D06 | hard | 168,573 / 0 / 0 | 21,020 / 0 / 41 | 16,582 / 0 / 0 | 1,427 / 0 / 75 | 7,866 / 0 / 0 | 300 / 0 / 0 |
| D07 | default | 46,915 / 0 / 0 | 19,416 / 0 / 39 | 15,771 / 0 / 0 | 1,556 / 0 / 107 | 7,876 / 0 / 0 | 300 / 0 / 0 |
| D07 | hard | 168,573 / 0 / 0 | 21,020 / 0 / 41 | 16,582 / 0 / 0 | 1,427 / 0 / 75 | 7,866 / 0 / 0 | 300 / 0 / 0 |
| D08 | default | 46,915 / 0 / 0 | 19,416 / 0 / 39 | 15,771 / 0 / 0 | 1,556 / 0 / 107 | 7,876 / 0 / 0 | 300 / 0 / 0 |
| D08 | hard | 168,573 / 0 / 0 | 21,020 / 0 / 41 | 16,582 / 0 / 0 | 1,427 / 0 / 75 | 7,866 / 0 / 0 | 300 / 0 / 0 |
| D09 | default | 47,618 / 0 / 0 | 19,468 / 0 / 38 | 16,003 / 300 / 0 | 1,740 / 0 / 61 | 8,029 / 119 / 0 | 300 / 0 / 0 |
| D09 | hard | 170,112 / 0 / 0 | 20,389 / 0 / 41 | 16,194 / 300 / 0 | 1,820 / 0 / 97 | 7,892 / 132 / 0 | 300 / 0 / 0 |
| D10 | default | 46,534 / 0 / 0 | 19,436 / 0 / 38 | 15,628 / 300 / 0 | 1,682 / 0 / 69 | 7,940 / 131 / 0 | 300 / 0 / 0 |
| D10 | hard | 167,843 / 0 / 0 | 20,757 / 0 / 35 | 16,210 / 300 / 0 | 1,742 / 0 / 69 | 8,013 / 105 / 0 | 300 / 0 / 0 |
| D11 | default | 46,306 / 0 / 0 | 19,370 / 0 / 46 | 15,711 / 300 / 0 | 1,806 / 0 / 88 | 8,040 / 117 / 0 | 300 / 0 / 0 |
| D11 | hard | 169,675 / 0 / 0 | 20,889 / 0 / 29 | 16,369 / 300 / 0 | 1,735 / 0 / 74 | 7,967 / 117 / 0 | 300 / 0 / 0 |
| D12 | default | 46,874 / 0 / 0 | 19,524 / 61 / 46 | 15,674 / 300 / 0 | 1,507 / 0 / 110 | 8,110 / 0 / 0 | 300 / 0 / 0 |
| D12 | hard | 169,841 / 0 / 0 | 20,786 / 57 / 23 | 16,318 / 300 / 0 | 1,443 / 0 / 60 | 7,972 / 0 / 0 | 300 / 0 / 0 |
| D13 | default | 46,874 / 0 / 0 | 19,524 / 61 / 46 | 15,674 / 300 / 0 | 1,507 / 0 / 110 | 8,110 / 0 / 0 | 300 / 0 / 0 |
| D13 | hard | 169,841 / 0 / 0 | 20,786 / 57 / 23 | 16,318 / 300 / 0 | 1,443 / 0 / 60 | 7,972 / 0 / 0 | 300 / 0 / 0 |
| D14 | default | 46,864 / 0 / 0 | 19,423 / 0 / 35 | 15,440 / 300 / 0 | 1,479 / 0 / 94 | 7,826 / 0 / 0 | 300 / 0 / 0 |
| D14 | hard | 166,667 / 0 / 0 | 21,270 / 0 / 38 | 16,338 / 300 / 0 | 1,518 / 0 / 90 | 8,001 / 0 / 0 | 300 / 0 / 0 |
| D15 | default | 46,864 / 0 / 0 | 19,423 / 0 / 35 | 15,440 / 300 / 0 | 1,479 / 0 / 94 | 7,826 / 0 / 0 | 300 / 0 / 0 |
| D15 | hard | 166,667 / 0 / 0 | 21,270 / 0 / 38 | 16,338 / 300 / 0 | 1,518 / 0 / 90 | 8,001 / 0 / 0 | 300 / 0 / 0 |
| D16 | default | 47,359 / 0 / 0 | 19,761 / 0 / 37 | 15,733 / 300 / 0 | 1,756 / 0 / 95 | 8,240 / 300 / 0 | 300 / 0 / 0 |
| D16 | hard | 168,258 / 0 / 0 | 21,102 / 0 / 35 | 16,375 / 300 / 0 | 1,718 / 0 / 84 | 8,057 / 300 / 0 | 300 / 0 / 0 |
| D17 | default | 47,359 / 0 / 0 | 19,761 / 0 / 37 | 15,733 / 300 / 0 | 1,756 / 0 / 95 | 8,240 / 300 / 0 | 300 / 0 / 0 |
| D17 | hard | 168,258 / 0 / 0 | 21,102 / 0 / 35 | 16,375 / 300 / 0 | 1,718 / 0 / 84 | 8,057 / 300 / 0 | 300 / 0 / 0 |
| D18 | default | 47,359 / 0 / 0 | 19,761 / 0 / 37 | 15,733 / 300 / 0 | 1,756 / 0 / 95 | 8,240 / 300 / 0 | 300 / 0 / 0 |
| D18 | hard | 168,258 / 0 / 0 | 21,102 / 0 / 35 | 16,375 / 300 / 0 | 1,718 / 0 / 84 | 8,057 / 300 / 0 | 300 / 0 / 0 |
| D19 | default | 46,743 / 0 / 0 | 19,634 / 0 / 38 | 15,966 / 300 / 0 | 1,457 / 0 / 96 | 7,912 / 0 / 0 | 300 / 0 / 0 |
| D19 | hard | 165,933 / 0 / 0 | 20,628 / 0 / 30 | 16,329 / 300 / 0 | 1,468 / 0 / 77 | 7,738 / 0 / 0 | 300 / 0 / 0 |
| D20 | default | 46,743 / 0 / 0 | 19,634 / 0 / 38 | 15,966 / 300 / 0 | 1,457 / 0 / 96 | 7,912 / 0 / 0 | 300 / 0 / 0 |
| D20 | hard | 165,933 / 0 / 0 | 20,628 / 0 / 30 | 16,329 / 300 / 0 | 1,468 / 0 / 77 | 7,738 / 0 / 0 | 300 / 0 / 0 |

Unexplained violations: 5274. Clean scenario violations: 1335.

Clean scenario violations:
- D01/default seed 41005 unapplied_running (GL-005178): observed -923, expected 0; CUST99859
- D01/default seed 41006 unapplied_running (GL-001878): observed -500336, expected 0; E0342
- D01/default seed 41007 ar_running (R2705): observed -1, expected 0; F0057818
- D01/default seed 41011 unapplied_running (L00316): observed -15, expected 0; C-5874
- D01/default seed 41012 unapplied_running (GL-005228): observed -87, expected 0; CUST57663
- D01/default seed 41013 unapplied_running (R3768): observed -168, expected 0; E6981
- D01/default seed 41014 unapplied_running (L03913): observed -2, expected 0; C-5080
- D01/default seed 41019 ar_running (GL-000793): observed -1, expected 0; INV-355747
- D01/default seed 41020 unapplied_running (L02377): observed -5, expected 0; E7129
- D01/default seed 41021 unapplied_running (R1433): observed -214, expected 0; E1968
- D01/default seed 41028 ar_running (L02016): observed -1, expected 0; F0606872
- D01/default seed 41028 unapplied_running (L02007): observed -56, expected 0; C-7863
- D01/default seed 41029 unapplied_running (R384): observed -128, expected 0; CUST43875
- D01/default seed 41032 unapplied_running (L00595): observed -86531, expected 0; C-2404
- D01/default seed 41034 ar_running (R229): observed -1, expected 0; 2503-857257
- D01/default seed 41039 ar_running (R988): observed -1, expected 0; SI-2025-984723
- D01/default seed 41043 unapplied_running (R3711): observed -667, expected 0; C-8659
- D01/default seed 41043 unapplied_running (R3858): observed -186, expected 0; C-7120
- D01/default seed 41044 unapplied_running (R4057): observed -32683, expected 0; E4613
- D01/default seed 41044 unapplied_running (R4054): observed -55854, expected 0; E9712
- D01/default seed 41045 ar_running (R4175): observed -1, expected 0; F0254951
- D01/default seed 41058 unapplied_running (L01321): observed -12, expected 0; C-0392
- D01/default seed 41059 unapplied_running (R2679): observed -41, expected 0; C-8026
- D01/default seed 41061 unapplied_running (R2190): observed -661, expected 0; CUST70335
- D01/default seed 41064 unapplied_running (R987): observed -47522, expected 0; CUST98460
- D01/default seed 41064 unapplied_running (R1036): observed -2977, expected 0; CUST42293
- D01/default seed 41066 unapplied_running (L04325): observed -555, expected 0; CUST55531
- D01/default seed 41068 unapplied_running (R1521): observed -64, expected 0; CUST07021
- D01/default seed 41071 unapplied_running (GL-000910): observed -132, expected 0; C-5747
- D01/default seed 41074 ar_running (GL-003948): observed -1, expected 0; 2601-593279
- D01/default seed 41080 unapplied_running (GL-004509): observed -14, expected 0; E9009
- D01/default seed 41081 unapplied_running (R4233): observed -225, expected 0; C-7364
- D01/default seed 41082 ar_running (GL-005049): observed -1, expected 0; F0880818
- D01/default seed 41084 unapplied_running (GL-001329): observed -91, expected 0; CUST52532
- D01/default seed 41084 unapplied_running (GL-001504): observed -16, expected 0; CUST14537
- D01/default seed 41086 unapplied_running (L03721): observed -214, expected 0; C-6213
- D01/default seed 41091 unapplied_running (R2905): observed -9, expected 0; C-1116
- D01/default seed 41094 ar_running (R3306): observed -1, expected 0; INV-357622
- D01/default seed 41100 ar_running (R1817): observed -1, expected 0; 2510-112034
- D01/default seed 41102 unapplied_running (L00536): observed -2, expected 0; CUST61593
- D01/default seed 41105 unapplied_running (GL-002236): observed -34, expected 0; CUST43566
- D01/default seed 41105 unapplied_running (GL-002244): observed -184, expected 0; CUST81946
- D01/default seed 41106 unapplied_running (GL-003529): observed -74, expected 0; C-0932
- D01/default seed 41113 unapplied_running (GL-004473): observed -115, expected 0; CUST50826
- D01/default seed 41115 unapplied_running (L04189): observed -224685, expected 0; E1486
- D01/default seed 41115 unapplied_running (L04274): observed -37185, expected 0; E5780
- D01/default seed 41116 unapplied_running (GL-002108): observed -73, expected 0; C-2466
- D01/default seed 41117 unapplied_running (GL-002803): observed -1, expected 0; E1961
- D01/default seed 41119 unapplied_running (GL-000964): observed -3, expected 0; E2473
- D01/default seed 41124 unapplied_running (GL-002245): observed -205, expected 0; C-6104
- D01/default seed 41125 unapplied_running (L00377): observed -1181, expected 0; CUST50140
- D01/default seed 41127 ar_running (GL-002840): observed -1, expected 0; F0686931
- D01/default seed 41128 unapplied_running (GL-002910): observed -97, expected 0; C-9525
- D01/default seed 41131 unapplied_running (L04366): observed -67, expected 0; C-2139
- D01/default seed 41131 unapplied_running (L04354): observed -353, expected 0; C-6052
- D01/default seed 41132 unapplied_running (R644): observed -46, expected 0; C-9933
- D01/default seed 41137 ar_running (GL-001286): observed -1, expected 0; 2501-410390
- D01/default seed 41140 unapplied_running (L01432): observed -446, expected 0; E0345
- D01/default seed 41141 ar_running (R3610): observed -1, expected 0; INV-054288
- D01/default seed 41142 unapplied_running (L03781): observed -10874, expected 0; CUST89097
- D01/default seed 41144 unapplied_running (L03241): observed -291, expected 0; E6937
- D01/default seed 41147 unapplied_running (L03708): observed -85, expected 0; E5990
- D01/default seed 41149 unapplied_running (R708): observed -60771, expected 0; C-9138
- D01/default seed 41150 unapplied_running (L01764): observed -742, expected 0; C-4875
- D01/default seed 41157 unapplied_running (L04564): observed -20455, expected 0; CUST09866
- D01/default seed 41158 unapplied_running (GL-000362): observed -1214, expected 0; E5459
- D01/default seed 41166 ar_running (GL-004004): observed -1, expected 0; 2506-422686
- D01/default seed 41170 unapplied_running (L01112): observed -27, expected 0; C-4024
- D01/default seed 41171 unapplied_running (L02781): observed -314, expected 0; C-5870
- D01/default seed 41173 unapplied_running (GL-001084): observed -132, expected 0; C-4096
- D01/default seed 41174 ar_running (GL-000390): observed -1, expected 0; SI-2025-590188
- D01/default seed 41174 unapplied_running (GL-000426): observed -286, expected 0; C-4736
- D01/default seed 41178 unapplied_running (L03744): observed -118378, expected 0; E8203
- D01/default seed 41182 ar_running (GL-000759): observed -1, expected 0; SI-2026-721173
- D01/default seed 41183 unapplied_running (L02610): observed -7, expected 0; CUST45617
- D01/default seed 41190 unapplied_running (GL-003022): observed -314, expected 0; C-6621
- D01/default seed 41192 ar_running (GL-004482): observed -1, expected 0; 2611-659303
- D01/default seed 41193 unapplied_running (GL-002517): observed -78, expected 0; CUST47530
- D01/default seed 41194 unapplied_running (L00725): observed -46, expected 0; E1812
- D01/default seed 41194 unapplied_running (L00782): observed -384, expected 0; E1022
- D01/default seed 41195 ar_running (GL-003793): observed -1, expected 0; F0615449
- D01/default seed 41196 unapplied_running (GL-003493): observed -44, expected 0; E4315
- D01/default seed 41197 unapplied_running (L02821): observed -3071, expected 0; CUST82232
- D01/default seed 41198 unapplied_running (L03718): observed -47, expected 0; CUST24584
- D01/default seed 41199 ar_running (R2679): observed -1, expected 0; F0107215
- D01/default seed 41203 unapplied_running (GL-002257): observed -220, expected 0; CUST44083
- D01/default seed 41205 unapplied_running (R4514): observed -12, expected 0; E5788
- D01/default seed 41208 unapplied_running (L02934): observed -49953, expected 0; CUST80841
- D01/default seed 41209 unapplied_running (GL-004432): observed -74, expected 0; C-3115
- D01/default seed 41212 ar_running (L01373): observed -1, expected 0; SI-2025-273988
- D01/default seed 41214 unapplied_running (R2379): observed -367, expected 0; E9465
- D01/default seed 41216 unapplied_running (R5038): observed -74, expected 0; C-8256
- D01/default seed 41220 unapplied_running (GL-002466): observed -26938, expected 0; E5508
- D01/default seed 41222 ar_running (GL-002092): observed -1, expected 0; INV-911729
- D01/default seed 41224 unapplied_running (L02932): observed -402, expected 0; E4306
- D01/default seed 41225 ar_running (R4393): observed -1, expected 0; INV-763469
- D01/default seed 41225 ar_running (R4435): observed -1, expected 0; INV-981731
- D01/default seed 41229 unapplied_running (GL-004718): observed -115, expected 0; C-5574
- D01/default seed 41234 unapplied_running (R2145): observed -46, expected 0; CUST28806
- D01/default seed 41234 unapplied_running (R2201): observed -21, expected 0; CUST09400
- D01/default seed 41236 unapplied_running (L02890): observed -55, expected 0; CUST67673
- D01/default seed 41239 ar_running (R1295): observed -1, expected 0; 2611-562598
- D01/default seed 41242 unapplied_running (R736): observed -119, expected 0; E9730
- D01/default seed 41243 ar_running (GL-005203): observed -1, expected 0; F0481630
- D01/default seed 41243 unapplied_running (GL-005212): observed -32, expected 0; CUST32225
- D01/default seed 41244 unapplied_running (L03904): observed -24475, expected 0; CUST93203
- D01/default seed 41244 unapplied_running (L04056): observed -49167, expected 0; CUST54052
- D01/default seed 41244 unapplied_running (L04053): observed -42070, expected 0; CUST05049
- D01/default seed 41245 ar_running (R2719): observed -1, expected 0; INV-988106
- D01/default seed 41247 unapplied_running (L01470): observed -3, expected 0; CUST42949
- D01/default seed 41248 ar_running (L00513): observed -1, expected 0; F0370420
- D01/default seed 41248 unapplied_running (L00432): observed -552, expected 0; E8174
- D01/default seed 41256 unapplied_running (GL-001834): observed -173, expected 0; C-4466
- D01/default seed 41257 unapplied_running (L00782): observed -34, expected 0; E4551
- D01/default seed 41258 ar_running (R1433): observed -1, expected 0; SI-2026-923475
- D01/default seed 41258 unapplied_running (R1238): observed -227031, expected 0; CUST78127
- D01/default seed 41262 ar_running (GL-001158): observed -1, expected 0; F0515687
- D01/default seed 41263 unapplied_running (R5022): observed -91, expected 0; CUST88062
- D01/default seed 41264 unapplied_running (R3651): observed -83, expected 0; C-1145
- D01/default seed 41265 unapplied_running (GL-001966): observed -170, expected 0; C-5923
- D01/default seed 41266 unapplied_running (L00492): observed -2186, expected 0; E7360
- D01/default seed 41267 unapplied_running (L03551): observed -1362, expected 0; E8408
- D01/default seed 41268 unapplied_running (R3548): observed -31589, expected 0; C-4687
- D01/default seed 41270 ar_running (GL-000401): observed -1, expected 0; INV-215118
- D01/default seed 41270 unapplied_running (GL-000443): observed -23, expected 0; CUST74275
- D01/default seed 41277 unapplied_running (L01581): observed -40, expected 0; E3442
- D01/default seed 41277 unapplied_running (L01680): observed -63, expected 0; E3442
- D01/default seed 41277 unapplied_running (L01733): observed -88, expected 0; E3442
- D01/default seed 41282 unapplied_running (GL-003747): observed -56670, expected 0; E8942
- D01/default seed 41283 unapplied_running (L04036): observed -57, expected 0; CUST56709
- D01/default seed 41287 unapplied_running (GL-004422): observed -33477, expected 0; C-5782
- D01/default seed 41287 unapplied_running (GL-004529): observed -16030, expected 0; C-6240
- D01/default seed 41289 unapplied_running (R446): observed -195, expected 0; CUST97557
- D01/default seed 41292 ar_running (L02096): observed -1, expected 0; INV-931351
- D01/default seed 41293 ar_running (GL-003102): observed -1, expected 0; 2503-365156
- D01/default seed 41293 ar_running (GL-003276): observed -1, expected 0; 2503-133260
- D01/default seed 41296 unapplied_running (L03801): observed -60, expected 0; C-9163
- D01/hard seed 41005 ar_running (GL-005749): observed -1, expected 0; INV-064884
- D01/hard seed 41008 unapplied_running (GL-003144): observed -51, expected 0; C-9667
- D01/hard seed 41011 unapplied_running (R3945): observed -229, expected 0; C-9377
- D01/hard seed 41013 ar_running (R2646): observed -1, expected 0; INV-859119
- D01/hard seed 41013 unapplied_running (R2930): observed -28, expected 0; CUST95480
- D01/hard seed 41015 unapplied_running (L05401): observed -98, expected 0; CUST95106
- D01/hard seed 41017 ar_running (L03233): observed -1, expected 0; INV-758326
- D01/hard seed 41018 unapplied_running (L03230): observed -23, expected 0; C-8778
- D01/hard seed 41020 unapplied_running (L01033): observed -303, expected 0; C-0028
- D01/hard seed 41020 unapplied_running (L01160): observed -5, expected 0; C-8284
- D01/hard seed 41024 unapplied_running (R3553): observed -143101, expected 0; E1698
- D01/hard seed 41024 unapplied_running (R3860): observed -188319, expected 0; E1698
- D01/hard seed 41025 unapplied_running (L02152): observed -10190, expected 0; C-6454
- D01/hard seed 41029 unapplied_running (R2704): observed -271, expected 0; CUST08113
- D01/hard seed 41029 unapplied_running (R2832): observed -19, expected 0; CUST09291
- D01/hard seed 41037 ar_running (L03201): observed -1, expected 0; 2611-778760
- D01/hard seed 41037 ar_running (L03244): observed -1, expected 0; 2611-453884
- D01/hard seed 41038 unapplied_running (GL-005437): observed -279331, expected 0; C-0425
- D01/hard seed 41040 ar_running (R5101): observed -1, expected 0; 2609-004130
- D01/hard seed 41045 unapplied_running (R3505): observed -103, expected 0; E2744
- D01/hard seed 41046 unapplied_running (L01489): observed -130, expected 0; E5006
- D01/hard seed 41049 unapplied_running (R3890): observed -315, expected 0; E7530
- D01/hard seed 41050 unapplied_running (L02856): observed -686, expected 0; CUST88801
- D01/hard seed 41052 ar_running (R1027): observed -1, expected 0; SI-2026-798836
- D01/hard seed 41053 unapplied_running (R2367): observed -63, expected 0; C-4903
- D01/hard seed 41061 unapplied_running (L02053): observed -26452, expected 0; CUST15073
- D01/hard seed 41063 ar_running (L01469): observed -1, expected 0; 2609-768605
- D01/hard seed 41065 ar_running (R4601): observed -1, expected 0; F0032065
- D01/hard seed 41073 unapplied_running (GL-001842): observed -420, expected 0; C-0848
- D01/hard seed 41078 unapplied_running (L01768): observed -170902, expected 0; E7114
- D01/hard seed 41079 unapplied_running (L05733): observed -20, expected 0; E5939
- D01/hard seed 41080 unapplied_running (R5253): observed -83, expected 0; C-3829
- D01/hard seed 41088 unapplied_running (GL-001810): observed -246, expected 0; C-6699
- D01/hard seed 41088 unapplied_running (GL-002196): observed -256, expected 0; C-6699
- D01/hard seed 41088 unapplied_running (GL-001984): observed -1, expected 0; C-3111
- D01/hard seed 41091 unapplied_running (GL-003949): observed -57, expected 0; E5263
- D01/hard seed 41092 unapplied_running (L03271): observed -4, expected 0; C-1933
- D01/hard seed 41093 unapplied_running (L02066): observed -2, expected 0; CUST65465
- D01/hard seed 41094 unapplied_running (R5650): observed -4, expected 0; E9227
- D01/hard seed 41096 ar_running (R648): observed -1, expected 0; SI-2026-466918
- D01/hard seed 41097 unapplied_running (R4467): observed -10407, expected 0; CUST02501
- D01/hard seed 41098 ar_running (L04227): observed -1, expected 0; 2612-160441
- D01/hard seed 41098 unapplied_running (L04443): observed -23291, expected 0; C-1225
- D01/hard seed 41099 unapplied_running (L02896): observed -26, expected 0; C-9785
- D01/hard seed 41099 unapplied_running (L03397): observed -9, expected 0; C-3675
- D01/hard seed 41100 ar_running (GL-005821): observed -1, expected 0; 2612-882562
- D01/hard seed 41103 ar_running (R2401): observed -1, expected 0; F0054592
- D01/hard seed 41106 ar_running (L03291): observed -1, expected 0; 2507-119107
- D01/hard seed 41108 unapplied_running (GL-003547): observed -174, expected 0; C-6620
- D01/hard seed 41112 ar_running (R4842): observed -1, expected 0; 2508-594384
- D01/hard seed 41115 ar_running (L03813): observed -1, expected 0; 2507-425960
- D01/hard seed 41118 ar_running (GL-004927): observed -1, expected 0; INV-114883
- D01/hard seed 41118 unapplied_running (GL-005060): observed -34, expected 0; CUST19568
- D01/hard seed 41123 ar_running (R4880): observed -1, expected 0; INV-019033
- D01/hard seed 41124 unapplied_running (L00585): observed -1, expected 0; CUST35077
- D01/hard seed 41128 ar_running (GL-001786): observed -1, expected 0; SI-2026-305268
- D01/hard seed 41134 unapplied_running (GL-005307): observed -201, expected 0; CUST34155
- D01/hard seed 41137 ar_running (R1542): observed -1, expected 0; F0267943
- D01/hard seed 41142 unapplied_running (GL-002585): observed -250, expected 0; C-5710
- D01/hard seed 41150 unapplied_running (L05035): observed -85, expected 0; CUST48458
- D01/hard seed 41151 ar_running (L00532): observed -1, expected 0; INV-263286
- D01/hard seed 41156 ar_running (R5500): observed -1, expected 0; 2508-592873
- D01/hard seed 41164 ar_running (R3355): observed -1, expected 0; 2504-064452
- D01/hard seed 41165 unapplied_running (R3538): observed -228, expected 0; CUST82075
- D01/hard seed 41170 ar_running (R3853): observed -1, expected 0; INV-886051
- D01/hard seed 41170 ar_running (R3783): observed -1, expected 0; INV-044439
- D01/hard seed 41172 unapplied_running (L02902): observed -136, expected 0; E2316
- D01/hard seed 41173 unapplied_running (L05206): observed -69, expected 0; E8466
- D01/hard seed 41174 ar_running (R1947): observed -1, expected 0; 2501-044446
- D01/hard seed 41174 unapplied_running (R1343): observed -104023, expected 0; C-2817
- D01/hard seed 41175 unapplied_running (L05070): observed -213, expected 0; C-7166
- D01/hard seed 41176 unapplied_running (GL-005340): observed -579, expected 0; E1431
- D01/hard seed 41179 ar_running (R5285): observed -1, expected 0; 2502-263509
- D01/hard seed 41185 ar_running (L05076): observed -1, expected 0; SI-2026-814573
- D01/hard seed 41194 ar_running (L05631): observed -1, expected 0; INV-589999
- D01/hard seed 41197 unapplied_running (L04940): observed -5371, expected 0; E9990
- D01/hard seed 41199 unapplied_running (GL-000525): observed -9, expected 0; CUST88252
- D01/hard seed 41200 unapplied_running (R3852): observed -10, expected 0; E9348
- D01/hard seed 41200 unapplied_running (R3947): observed -54, expected 0; E3676
- D01/hard seed 41201 unapplied_running (GL-004366): observed -14, expected 0; E0747
- D01/hard seed 41202 unapplied_running (R731): observed -67, expected 0; E8053
- D01/hard seed 41204 ar_running (R3490): observed -1, expected 0; INV-929188
- D01/hard seed 41204 unapplied_running (R3004): observed -33679, expected 0; C-2446
- D01/hard seed 41208 unapplied_running (R1128): observed -13, expected 0; C-8157
- D01/hard seed 41208 unapplied_running (R1712): observed -7, expected 0; C-8157
- D01/hard seed 41210 unapplied_running (R1520): observed -1, expected 0; E8676
- D01/hard seed 41211 unapplied_running (R1389): observed -1150, expected 0; E7884
- D01/hard seed 41212 ar_running (GL-003946): observed -1, expected 0; 2603-669849
- D01/hard seed 41216 ar_running (R2147): observed -1, expected 0; SI-2025-019680
- D01/hard seed 41216 ar_running (R2145): observed -1, expected 0; SI-2025-363180
- D01/hard seed 41216 unapplied_running (R2104): observed -66, expected 0; E3666
- D01/hard seed 41218 unapplied_running (R2840): observed -84, expected 0; C-6028
- D01/hard seed 41224 unapplied_running (GL-001578): observed -143, expected 0; E2277
- D01/hard seed 41232 unapplied_running (R5419): observed -198, expected 0; E5211
- D01/hard seed 41233 unapplied_running (GL-004739): observed -82, expected 0; C-3362
- D01/hard seed 41234 ar_running (GL-002416): observed -1, expected 0; SI-2025-000350
- D01/hard seed 41235 unapplied_running (GL-002070): observed -17333, expected 0; CUST16801
- D01/hard seed 41236 unapplied_running (GL-003576): observed -216, expected 0; CUST89445
- D01/hard seed 41240 ar_running (GL-002596): observed -1, expected 0; F0438164
- D01/hard seed 41243 unapplied_running (R2468): observed -38, expected 0; E7080
- D01/hard seed 41244 unapplied_running (L01940): observed -194678, expected 0; E7439
- D01/hard seed 41249 ar_running (R4435): observed -1, expected 0; SI-2026-018892
- D01/hard seed 41249 unapplied_running (R4476): observed -16, expected 0; E0639
- D01/hard seed 41251 ar_running (GL-004129): observed -1, expected 0; 2602-317250
- D01/hard seed 41253 ar_running (L01044): observed -1, expected 0; 2502-305985
- D01/hard seed 41253 ar_running (L00832): observed -1, expected 0; 2502-633501
- D01/hard seed 41262 ar_running (GL-003336): observed -1, expected 0; INV-882581
- D01/hard seed 41266 ar_running (GL-002148): observed -1, expected 0; F0818242
- D01/hard seed 41266 ar_running (GL-001994): observed -1, expected 0; F0254037
- D01/hard seed 41267 unapplied_running (GL-004356): observed -164, expected 0; E8308
- D01/hard seed 41276 unapplied_running (GL-004211): observed -32, expected 0; CUST98146
- D01/hard seed 41278 ar_running (GL-000895): observed -1, expected 0; SI-2025-730616
- D01/hard seed 41279 ar_running (L01297): observed -1, expected 0; F0674420
- D01/hard seed 41279 unapplied_running (L01357): observed -154, expected 0; C-1009
- D01/hard seed 41282 ar_running (R4406): observed -1, expected 0; F0128741
- D01/hard seed 41284 unapplied_running (R3587): observed -108, expected 0; C-7663
- D01/hard seed 41286 unapplied_running (GL-002193): observed -40, expected 0; C-7586
- D01/hard seed 41287 unapplied_running (GL-003483): observed -259, expected 0; CUST73028
- D01/hard seed 41288 unapplied_running (L02451): observed -14938, expected 0; E7606
- D01/hard seed 41289 unapplied_running (L03602): observed -1092, expected 0; CUST97015
- D01/hard seed 41289 unapplied_running (L03815): observed -251, expected 0; CUST84414
- D01/hard seed 41290 ar_running (R5259): observed -1, expected 0; F0617458
- D01/hard seed 41291 ar_running (R5756): observed -1, expected 0; 2604-148765
- D01/hard seed 41291 unapplied_running (R5269): observed -78791, expected 0; E8132
- D01/hard seed 41292 ar_running (GL-005681): observed -1, expected 0; INV-315947
- D01/hard seed 41292 unapplied_running (GL-005406): observed -13, expected 0; E5289
- D01/hard seed 41295 ar_running (R3380): observed -1, expected 0; F0203109
- D01/hard seed 41298 unapplied_running (R3356): observed -4, expected 0; C-7601
- D01/hard seed 41299 ar_running (R3080): observed -1, expected 0; SI-2025-343694
- D01/hard seed 41299 unapplied_running (R2644): observed -27, expected 0; E7083
- D02/default seed 41005 unapplied_running (GL-005178): observed -923, expected 0; CUST99859
- D02/default seed 41006 unapplied_running (GL-001878): observed -500336, expected 0; E0342
- D02/default seed 41007 ar_running (R2705): observed -1, expected 0; F0057818
- D02/default seed 41011 unapplied_running (L00316): observed -15, expected 0; C-5874
- D02/default seed 41012 unapplied_running (GL-005228): observed -87, expected 0; CUST57663
- D02/default seed 41013 unapplied_running (R3768): observed -168, expected 0; E6981
- D02/default seed 41014 unapplied_running (L03913): observed -2, expected 0; C-5080
- D02/default seed 41019 ar_running (GL-000793): observed -1, expected 0; INV-355747
- D02/default seed 41020 unapplied_running (L02377): observed -5, expected 0; E7129
- D02/default seed 41021 unapplied_running (R1433): observed -214, expected 0; E1968
- D02/default seed 41028 ar_running (L02016): observed -1, expected 0; F0606872
- D02/default seed 41028 unapplied_running (L02007): observed -56, expected 0; C-7863
- D02/default seed 41029 unapplied_running (R384): observed -128, expected 0; CUST43875
- D02/default seed 41032 unapplied_running (L00595): observed -86531, expected 0; C-2404
- D02/default seed 41034 ar_running (R229): observed -1, expected 0; 2503-857257
- D02/default seed 41039 ar_running (R988): observed -1, expected 0; SI-2025-984723
- D02/default seed 41043 unapplied_running (R3711): observed -667, expected 0; C-8659
- D02/default seed 41043 unapplied_running (R3858): observed -186, expected 0; C-7120
- D02/default seed 41044 unapplied_running (R4057): observed -32683, expected 0; E4613
- D02/default seed 41044 unapplied_running (R4054): observed -55854, expected 0; E9712
- D02/default seed 41045 ar_running (R4175): observed -1, expected 0; F0254951
- D02/default seed 41058 unapplied_running (L01321): observed -12, expected 0; C-0392
- D02/default seed 41059 unapplied_running (R2679): observed -41, expected 0; C-8026
- D02/default seed 41061 unapplied_running (R2190): observed -661, expected 0; CUST70335
- D02/default seed 41064 unapplied_running (R987): observed -47522, expected 0; CUST98460
- D02/default seed 41064 unapplied_running (R1036): observed -2977, expected 0; CUST42293
- D02/default seed 41066 unapplied_running (L04325): observed -555, expected 0; CUST55531
- D02/default seed 41068 unapplied_running (R1521): observed -64, expected 0; CUST07021
- D02/default seed 41071 unapplied_running (GL-000910): observed -132, expected 0; C-5747
- D02/default seed 41074 ar_running (GL-003948): observed -1, expected 0; 2601-593279
- D02/default seed 41080 unapplied_running (GL-004509): observed -14, expected 0; E9009
- D02/default seed 41081 unapplied_running (R4233): observed -225, expected 0; C-7364
- D02/default seed 41082 ar_running (GL-005049): observed -1, expected 0; F0880818
- D02/default seed 41084 unapplied_running (GL-001329): observed -91, expected 0; CUST52532
- D02/default seed 41084 unapplied_running (GL-001504): observed -16, expected 0; CUST14537
- D02/default seed 41086 unapplied_running (L03721): observed -214, expected 0; C-6213
- D02/default seed 41091 unapplied_running (R2905): observed -9, expected 0; C-1116
- D02/default seed 41094 ar_running (R3306): observed -1, expected 0; INV-357622
- D02/default seed 41100 ar_running (R1817): observed -1, expected 0; 2510-112034
- D02/default seed 41102 unapplied_running (L00536): observed -2, expected 0; CUST61593
- D02/default seed 41105 unapplied_running (GL-002236): observed -34, expected 0; CUST43566
- D02/default seed 41105 unapplied_running (GL-002244): observed -184, expected 0; CUST81946
- D02/default seed 41106 unapplied_running (GL-003529): observed -74, expected 0; C-0932
- D02/default seed 41113 unapplied_running (GL-004473): observed -115, expected 0; CUST50826
- D02/default seed 41115 unapplied_running (L04189): observed -224685, expected 0; E1486
- D02/default seed 41115 unapplied_running (L04274): observed -37185, expected 0; E5780
- D02/default seed 41116 unapplied_running (GL-002108): observed -73, expected 0; C-2466
- D02/default seed 41117 unapplied_running (GL-002803): observed -1, expected 0; E1961
- D02/default seed 41119 unapplied_running (GL-000964): observed -3, expected 0; E2473
- D02/default seed 41124 unapplied_running (GL-002245): observed -205, expected 0; C-6104
- D02/default seed 41125 unapplied_running (L00377): observed -1181, expected 0; CUST50140
- D02/default seed 41127 ar_running (GL-002840): observed -1, expected 0; F0686931
- D02/default seed 41128 unapplied_running (GL-002910): observed -97, expected 0; C-9525
- D02/default seed 41131 unapplied_running (L04366): observed -67, expected 0; C-2139
- D02/default seed 41131 unapplied_running (L04354): observed -353, expected 0; C-6052
- D02/default seed 41132 unapplied_running (R644): observed -46, expected 0; C-9933
- D02/default seed 41137 ar_running (GL-001286): observed -1, expected 0; 2501-410390
- D02/default seed 41140 unapplied_running (L01432): observed -446, expected 0; E0345
- D02/default seed 41141 ar_running (R3610): observed -1, expected 0; INV-054288
- D02/default seed 41142 unapplied_running (L03781): observed -10874, expected 0; CUST89097
- D02/default seed 41144 unapplied_running (L03241): observed -291, expected 0; E6937
- D02/default seed 41147 unapplied_running (L03708): observed -85, expected 0; E5990
- D02/default seed 41149 unapplied_running (R708): observed -60771, expected 0; C-9138
- D02/default seed 41150 unapplied_running (L01764): observed -742, expected 0; C-4875
- D02/default seed 41157 unapplied_running (L04564): observed -20455, expected 0; CUST09866
- D02/default seed 41158 unapplied_running (GL-000362): observed -1214, expected 0; E5459
- D02/default seed 41166 ar_running (GL-004004): observed -1, expected 0; 2506-422686
- D02/default seed 41170 unapplied_running (L01112): observed -27, expected 0; C-4024
- D02/default seed 41171 unapplied_running (L02781): observed -314, expected 0; C-5870
- D02/default seed 41173 unapplied_running (GL-001084): observed -132, expected 0; C-4096
- D02/default seed 41174 ar_running (GL-000390): observed -1, expected 0; SI-2025-590188
- D02/default seed 41174 unapplied_running (GL-000426): observed -286, expected 0; C-4736
- D02/default seed 41178 unapplied_running (L03744): observed -118378, expected 0; E8203
- D02/default seed 41182 ar_running (GL-000759): observed -1, expected 0; SI-2026-721173
- D02/default seed 41183 unapplied_running (L02610): observed -7, expected 0; CUST45617
- D02/default seed 41190 unapplied_running (GL-003022): observed -314, expected 0; C-6621
- D02/default seed 41192 ar_running (GL-004482): observed -1, expected 0; 2611-659303
- D02/default seed 41193 unapplied_running (GL-002517): observed -78, expected 0; CUST47530
- D02/default seed 41194 unapplied_running (L00725): observed -46, expected 0; E1812
- D02/default seed 41194 unapplied_running (L00782): observed -384, expected 0; E1022
- D02/default seed 41195 ar_running (GL-003793): observed -1, expected 0; F0615449
- D02/default seed 41196 unapplied_running (GL-003493): observed -44, expected 0; E4315
- D02/default seed 41197 unapplied_running (L02821): observed -3071, expected 0; CUST82232
- D02/default seed 41198 unapplied_running (L03718): observed -47, expected 0; CUST24584
- D02/default seed 41199 ar_running (R2679): observed -1, expected 0; F0107215
- D02/default seed 41203 unapplied_running (GL-002257): observed -220, expected 0; CUST44083
- D02/default seed 41205 unapplied_running (R4514): observed -12, expected 0; E5788
- D02/default seed 41208 unapplied_running (L02934): observed -49953, expected 0; CUST80841
- D02/default seed 41209 unapplied_running (GL-004432): observed -74, expected 0; C-3115
- D02/default seed 41212 ar_running (L01373): observed -1, expected 0; SI-2025-273988
- D02/default seed 41214 unapplied_running (R2379): observed -367, expected 0; E9465
- D02/default seed 41216 unapplied_running (R5038): observed -74, expected 0; C-8256
- D02/default seed 41220 unapplied_running (GL-002466): observed -26938, expected 0; E5508
- D02/default seed 41222 ar_running (GL-002092): observed -1, expected 0; INV-911729
- D02/default seed 41224 unapplied_running (L02932): observed -402, expected 0; E4306
- D02/default seed 41225 ar_running (R4393): observed -1, expected 0; INV-763469
- D02/default seed 41225 ar_running (R4435): observed -1, expected 0; INV-981731
- D02/default seed 41229 unapplied_running (GL-004718): observed -115, expected 0; C-5574
- D02/default seed 41234 unapplied_running (R2145): observed -46, expected 0; CUST28806
- D02/default seed 41234 unapplied_running (R2201): observed -21, expected 0; CUST09400
- D02/default seed 41236 unapplied_running (L02890): observed -55, expected 0; CUST67673
- D02/default seed 41239 ar_running (R1295): observed -1, expected 0; 2611-562598
- D02/default seed 41242 unapplied_running (R736): observed -119, expected 0; E9730
- D02/default seed 41243 ar_running (GL-005203): observed -1, expected 0; F0481630
- D02/default seed 41243 unapplied_running (GL-005212): observed -32, expected 0; CUST32225
- D02/default seed 41244 unapplied_running (L03904): observed -24475, expected 0; CUST93203
- D02/default seed 41244 unapplied_running (L04056): observed -49167, expected 0; CUST54052
- D02/default seed 41244 unapplied_running (L04053): observed -42070, expected 0; CUST05049
- D02/default seed 41245 ar_running (R2719): observed -1, expected 0; INV-988106
- D02/default seed 41247 unapplied_running (L01470): observed -3, expected 0; CUST42949
- D02/default seed 41248 ar_running (L00513): observed -1, expected 0; F0370420
- D02/default seed 41248 unapplied_running (L00432): observed -552, expected 0; E8174
- D02/default seed 41256 unapplied_running (GL-001834): observed -173, expected 0; C-4466
- D02/default seed 41257 unapplied_running (L00782): observed -34, expected 0; E4551
- D02/default seed 41258 ar_running (R1433): observed -1, expected 0; SI-2026-923475
- D02/default seed 41258 unapplied_running (R1238): observed -227031, expected 0; CUST78127
- D02/default seed 41262 ar_running (GL-001158): observed -1, expected 0; F0515687
- D02/default seed 41263 unapplied_running (R5022): observed -91, expected 0; CUST88062
- D02/default seed 41264 unapplied_running (R3651): observed -83, expected 0; C-1145
- D02/default seed 41265 unapplied_running (GL-001966): observed -170, expected 0; C-5923
- D02/default seed 41266 unapplied_running (L00492): observed -2186, expected 0; E7360
- D02/default seed 41267 unapplied_running (L03551): observed -1362, expected 0; E8408
- D02/default seed 41268 unapplied_running (R3548): observed -31589, expected 0; C-4687
- D02/default seed 41270 ar_running (GL-000401): observed -1, expected 0; INV-215118
- D02/default seed 41270 unapplied_running (GL-000443): observed -23, expected 0; CUST74275
- D02/default seed 41277 unapplied_running (L01581): observed -40, expected 0; E3442
- D02/default seed 41277 unapplied_running (L01680): observed -63, expected 0; E3442
- D02/default seed 41277 unapplied_running (L01733): observed -88, expected 0; E3442
- D02/default seed 41282 unapplied_running (GL-003747): observed -56670, expected 0; E8942
- D02/default seed 41283 unapplied_running (L04036): observed -57, expected 0; CUST56709
- D02/default seed 41287 unapplied_running (GL-004422): observed -33477, expected 0; C-5782
- D02/default seed 41287 unapplied_running (GL-004529): observed -16030, expected 0; C-6240
- D02/default seed 41289 unapplied_running (R446): observed -195, expected 0; CUST97557
- D02/default seed 41292 ar_running (L02096): observed -1, expected 0; INV-931351
- D02/default seed 41293 ar_running (GL-003102): observed -1, expected 0; 2503-365156
- D02/default seed 41293 ar_running (GL-003276): observed -1, expected 0; 2503-133260
- D02/default seed 41296 unapplied_running (L03801): observed -60, expected 0; C-9163
- D02/hard seed 41005 ar_running (GL-005749): observed -1, expected 0; INV-064884
- D02/hard seed 41008 unapplied_running (GL-003144): observed -51, expected 0; C-9667
- D02/hard seed 41011 unapplied_running (R3945): observed -229, expected 0; C-9377
- D02/hard seed 41013 ar_running (R2646): observed -1, expected 0; INV-859119
- D02/hard seed 41013 unapplied_running (R2930): observed -28, expected 0; CUST95480
- D02/hard seed 41015 unapplied_running (L05401): observed -98, expected 0; CUST95106
- D02/hard seed 41017 ar_running (L03233): observed -1, expected 0; INV-758326
- D02/hard seed 41018 unapplied_running (L03230): observed -23, expected 0; C-8778
- D02/hard seed 41020 unapplied_running (L01033): observed -303, expected 0; C-0028
- D02/hard seed 41020 unapplied_running (L01160): observed -5, expected 0; C-8284
- D02/hard seed 41024 unapplied_running (R3553): observed -143101, expected 0; E1698
- D02/hard seed 41024 unapplied_running (R3860): observed -188319, expected 0; E1698
- D02/hard seed 41025 unapplied_running (L02152): observed -10190, expected 0; C-6454
- D02/hard seed 41029 unapplied_running (R2704): observed -271, expected 0; CUST08113
- D02/hard seed 41029 unapplied_running (R2832): observed -19, expected 0; CUST09291
- D02/hard seed 41037 ar_running (L03201): observed -1, expected 0; 2611-778760
- D02/hard seed 41037 ar_running (L03244): observed -1, expected 0; 2611-453884
- D02/hard seed 41038 unapplied_running (GL-005437): observed -279331, expected 0; C-0425
- D02/hard seed 41040 ar_running (R5101): observed -1, expected 0; 2609-004130
- D02/hard seed 41045 unapplied_running (R3505): observed -103, expected 0; E2744
- D02/hard seed 41046 unapplied_running (L01489): observed -130, expected 0; E5006
- D02/hard seed 41049 unapplied_running (R3890): observed -315, expected 0; E7530
- D02/hard seed 41050 unapplied_running (L02856): observed -686, expected 0; CUST88801
- D02/hard seed 41052 ar_running (R1027): observed -1, expected 0; SI-2026-798836
- D02/hard seed 41053 unapplied_running (R2367): observed -63, expected 0; C-4903
- D02/hard seed 41061 unapplied_running (L02053): observed -26452, expected 0; CUST15073
- D02/hard seed 41063 ar_running (L01469): observed -1, expected 0; 2609-768605
- D02/hard seed 41065 ar_running (R4601): observed -1, expected 0; F0032065
- D02/hard seed 41073 unapplied_running (GL-001842): observed -420, expected 0; C-0848
- D02/hard seed 41078 unapplied_running (L01768): observed -170902, expected 0; E7114
- D02/hard seed 41079 unapplied_running (L05733): observed -20, expected 0; E5939
- D02/hard seed 41080 unapplied_running (R5253): observed -83, expected 0; C-3829
- D02/hard seed 41088 unapplied_running (GL-001810): observed -246, expected 0; C-6699
- D02/hard seed 41088 unapplied_running (GL-002196): observed -256, expected 0; C-6699
- D02/hard seed 41088 unapplied_running (GL-001984): observed -1, expected 0; C-3111
- D02/hard seed 41091 unapplied_running (GL-003949): observed -57, expected 0; E5263
- D02/hard seed 41092 unapplied_running (L03271): observed -4, expected 0; C-1933
- D02/hard seed 41093 unapplied_running (L02066): observed -2, expected 0; CUST65465
- D02/hard seed 41094 unapplied_running (R5650): observed -4, expected 0; E9227
- D02/hard seed 41096 ar_running (R648): observed -1, expected 0; SI-2026-466918
- D02/hard seed 41097 unapplied_running (R4467): observed -10407, expected 0; CUST02501
- D02/hard seed 41098 ar_running (L04227): observed -1, expected 0; 2612-160441
- D02/hard seed 41098 unapplied_running (L04443): observed -23291, expected 0; C-1225
- D02/hard seed 41099 unapplied_running (L02896): observed -26, expected 0; C-9785
- D02/hard seed 41099 unapplied_running (L03397): observed -9, expected 0; C-3675
- D02/hard seed 41100 ar_running (GL-005821): observed -1, expected 0; 2612-882562
- D02/hard seed 41103 ar_running (R2401): observed -1, expected 0; F0054592
- D02/hard seed 41106 ar_running (L03291): observed -1, expected 0; 2507-119107
- D02/hard seed 41108 unapplied_running (GL-003547): observed -174, expected 0; C-6620
- D02/hard seed 41112 ar_running (R4842): observed -1, expected 0; 2508-594384
- D02/hard seed 41115 ar_running (L03813): observed -1, expected 0; 2507-425960
- D02/hard seed 41118 ar_running (GL-004927): observed -1, expected 0; INV-114883
- D02/hard seed 41118 unapplied_running (GL-005060): observed -34, expected 0; CUST19568
- D02/hard seed 41123 ar_running (R4880): observed -1, expected 0; INV-019033
- D02/hard seed 41124 unapplied_running (L00585): observed -1, expected 0; CUST35077
- D02/hard seed 41128 ar_running (GL-001786): observed -1, expected 0; SI-2026-305268
- D02/hard seed 41134 unapplied_running (GL-005307): observed -201, expected 0; CUST34155
- D02/hard seed 41137 ar_running (R1542): observed -1, expected 0; F0267943
- D02/hard seed 41142 unapplied_running (GL-002585): observed -250, expected 0; C-5710
- D02/hard seed 41150 unapplied_running (L05035): observed -85, expected 0; CUST48458
- D02/hard seed 41151 ar_running (L00532): observed -1, expected 0; INV-263286
- D02/hard seed 41156 ar_running (R5500): observed -1, expected 0; 2508-592873
- D02/hard seed 41164 ar_running (R3355): observed -1, expected 0; 2504-064452
- D02/hard seed 41165 unapplied_running (R3538): observed -228, expected 0; CUST82075
- D02/hard seed 41170 ar_running (R3853): observed -1, expected 0; INV-886051
- D02/hard seed 41170 ar_running (R3783): observed -1, expected 0; INV-044439
- D02/hard seed 41172 unapplied_running (L02902): observed -136, expected 0; E2316
- D02/hard seed 41173 unapplied_running (L05206): observed -69, expected 0; E8466
- D02/hard seed 41174 ar_running (R1947): observed -1, expected 0; 2501-044446
- D02/hard seed 41174 unapplied_running (R1343): observed -104023, expected 0; C-2817
- D02/hard seed 41175 unapplied_running (L05070): observed -213, expected 0; C-7166
- D02/hard seed 41176 unapplied_running (GL-005340): observed -579, expected 0; E1431
- D02/hard seed 41179 ar_running (R5285): observed -1, expected 0; 2502-263509
- D02/hard seed 41185 ar_running (L05076): observed -1, expected 0; SI-2026-814573
- D02/hard seed 41194 ar_running (L05631): observed -1, expected 0; INV-589999
- D02/hard seed 41197 unapplied_running (L04940): observed -5371, expected 0; E9990
- D02/hard seed 41199 unapplied_running (GL-000525): observed -9, expected 0; CUST88252
- D02/hard seed 41200 unapplied_running (R3852): observed -10, expected 0; E9348
- D02/hard seed 41200 unapplied_running (R3947): observed -54, expected 0; E3676
- D02/hard seed 41201 unapplied_running (GL-004366): observed -14, expected 0; E0747
- D02/hard seed 41202 unapplied_running (R731): observed -67, expected 0; E8053
- D02/hard seed 41204 ar_running (R3490): observed -1, expected 0; INV-929188
- D02/hard seed 41204 unapplied_running (R3004): observed -33679, expected 0; C-2446
- D02/hard seed 41208 unapplied_running (R1128): observed -13, expected 0; C-8157
- D02/hard seed 41208 unapplied_running (R1712): observed -7, expected 0; C-8157
- D02/hard seed 41210 unapplied_running (R1520): observed -1, expected 0; E8676
- D02/hard seed 41211 unapplied_running (R1389): observed -1150, expected 0; E7884
- D02/hard seed 41212 ar_running (GL-003946): observed -1, expected 0; 2603-669849
- D02/hard seed 41216 ar_running (R2147): observed -1, expected 0; SI-2025-019680
- D02/hard seed 41216 ar_running (R2145): observed -1, expected 0; SI-2025-363180
- D02/hard seed 41216 unapplied_running (R2104): observed -66, expected 0; E3666
- D02/hard seed 41218 unapplied_running (R2840): observed -84, expected 0; C-6028
- D02/hard seed 41224 unapplied_running (GL-001578): observed -143, expected 0; E2277
- D02/hard seed 41232 unapplied_running (R5419): observed -198, expected 0; E5211
- D02/hard seed 41233 unapplied_running (GL-004739): observed -82, expected 0; C-3362
- D02/hard seed 41234 ar_running (GL-002416): observed -1, expected 0; SI-2025-000350
- D02/hard seed 41235 unapplied_running (GL-002070): observed -17333, expected 0; CUST16801
- D02/hard seed 41236 unapplied_running (GL-003576): observed -216, expected 0; CUST89445
- D02/hard seed 41240 ar_running (GL-002596): observed -1, expected 0; F0438164
- D02/hard seed 41243 unapplied_running (R2468): observed -38, expected 0; E7080
- D02/hard seed 41244 unapplied_running (L01940): observed -194678, expected 0; E7439
- D02/hard seed 41249 ar_running (R4435): observed -1, expected 0; SI-2026-018892
- D02/hard seed 41249 unapplied_running (R4476): observed -16, expected 0; E0639
- D02/hard seed 41251 ar_running (GL-004129): observed -1, expected 0; 2602-317250
- D02/hard seed 41253 ar_running (L01044): observed -1, expected 0; 2502-305985
- D02/hard seed 41253 ar_running (L00832): observed -1, expected 0; 2502-633501
- D02/hard seed 41262 ar_running (GL-003336): observed -1, expected 0; INV-882581
- D02/hard seed 41266 ar_running (GL-002148): observed -1, expected 0; F0818242
- D02/hard seed 41266 ar_running (GL-001994): observed -1, expected 0; F0254037
- D02/hard seed 41267 unapplied_running (GL-004356): observed -164, expected 0; E8308
- D02/hard seed 41276 unapplied_running (GL-004211): observed -32, expected 0; CUST98146
- D02/hard seed 41278 ar_running (GL-000895): observed -1, expected 0; SI-2025-730616
- D02/hard seed 41279 ar_running (L01297): observed -1, expected 0; F0674420
- D02/hard seed 41279 unapplied_running (L01357): observed -154, expected 0; C-1009
- D02/hard seed 41282 ar_running (R4406): observed -1, expected 0; F0128741
- D02/hard seed 41284 unapplied_running (R3587): observed -108, expected 0; C-7663
- D02/hard seed 41286 unapplied_running (GL-002193): observed -40, expected 0; C-7586
- D02/hard seed 41287 unapplied_running (GL-003483): observed -259, expected 0; CUST73028
- D02/hard seed 41288 unapplied_running (L02451): observed -14938, expected 0; E7606
- D02/hard seed 41289 unapplied_running (L03602): observed -1092, expected 0; CUST97015
- D02/hard seed 41289 unapplied_running (L03815): observed -251, expected 0; CUST84414
- D02/hard seed 41290 ar_running (R5259): observed -1, expected 0; F0617458
- D02/hard seed 41291 ar_running (R5756): observed -1, expected 0; 2604-148765
- D02/hard seed 41291 unapplied_running (R5269): observed -78791, expected 0; E8132
- D02/hard seed 41292 ar_running (GL-005681): observed -1, expected 0; INV-315947
- D02/hard seed 41292 unapplied_running (GL-005406): observed -13, expected 0; E5289
- D02/hard seed 41295 ar_running (R3380): observed -1, expected 0; F0203109
- D02/hard seed 41298 unapplied_running (R3356): observed -4, expected 0; C-7601
- D02/hard seed 41299 ar_running (R3080): observed -1, expected 0; SI-2025-343694
- D02/hard seed 41299 unapplied_running (R2644): observed -27, expected 0; E7083
- D03/default seed 41005 unapplied_running (GL-005178): observed -923, expected 0; CUST99859
- D03/default seed 41006 unapplied_running (GL-001878): observed -500336, expected 0; E0342
- D03/default seed 41007 ar_running (R2705): observed -1, expected 0; F0057818
- D03/default seed 41011 unapplied_running (L00316): observed -15, expected 0; C-5874
- D03/default seed 41012 unapplied_running (GL-005228): observed -87, expected 0; CUST57663
- D03/default seed 41013 unapplied_running (R3768): observed -168, expected 0; E6981
- D03/default seed 41014 unapplied_running (L03913): observed -2, expected 0; C-5080
- D03/default seed 41019 ar_running (GL-000793): observed -1, expected 0; INV-355747
- D03/default seed 41020 unapplied_running (L02377): observed -5, expected 0; E7129
- D03/default seed 41021 unapplied_running (R1433): observed -214, expected 0; E1968
- D03/default seed 41028 ar_running (L02016): observed -1, expected 0; F0606872
- D03/default seed 41028 unapplied_running (L02007): observed -56, expected 0; C-7863
- D03/default seed 41029 unapplied_running (R384): observed -128, expected 0; CUST43875
- D03/default seed 41032 unapplied_running (L00595): observed -86531, expected 0; C-2404
- D03/default seed 41034 ar_running (R229): observed -1, expected 0; 2503-857257
- D03/default seed 41039 ar_running (R988): observed -1, expected 0; SI-2025-984723
- D03/default seed 41043 unapplied_running (R3711): observed -667, expected 0; C-8659
- D03/default seed 41043 unapplied_running (R3858): observed -186, expected 0; C-7120
- D03/default seed 41044 unapplied_running (R4057): observed -32683, expected 0; E4613
- D03/default seed 41044 unapplied_running (R4054): observed -55854, expected 0; E9712
- D03/default seed 41045 ar_running (R4175): observed -1, expected 0; F0254951
- D03/default seed 41058 unapplied_running (L01321): observed -12, expected 0; C-0392
- D03/default seed 41059 unapplied_running (R2679): observed -41, expected 0; C-8026
- D03/default seed 41061 unapplied_running (R2190): observed -661, expected 0; CUST70335
- D03/default seed 41064 unapplied_running (R987): observed -47522, expected 0; CUST98460
- D03/default seed 41064 unapplied_running (R1036): observed -2977, expected 0; CUST42293
- D03/default seed 41066 unapplied_running (L04325): observed -555, expected 0; CUST55531
- D03/default seed 41068 unapplied_running (R1521): observed -64, expected 0; CUST07021
- D03/default seed 41071 unapplied_running (GL-000910): observed -132, expected 0; C-5747
- D03/default seed 41074 ar_running (GL-003948): observed -1, expected 0; 2601-593279
- D03/default seed 41080 unapplied_running (GL-004509): observed -14, expected 0; E9009
- D03/default seed 41081 unapplied_running (R4233): observed -225, expected 0; C-7364
- D03/default seed 41082 ar_running (GL-005049): observed -1, expected 0; F0880818
- D03/default seed 41084 unapplied_running (GL-001329): observed -91, expected 0; CUST52532
- D03/default seed 41084 unapplied_running (GL-001504): observed -16, expected 0; CUST14537
- D03/default seed 41086 unapplied_running (L03721): observed -214, expected 0; C-6213
- D03/default seed 41091 unapplied_running (R2905): observed -9, expected 0; C-1116
- D03/default seed 41094 ar_running (R3306): observed -1, expected 0; INV-357622
- D03/default seed 41100 ar_running (R1817): observed -1, expected 0; 2510-112034
- D03/default seed 41102 unapplied_running (L00536): observed -2, expected 0; CUST61593
- D03/default seed 41105 unapplied_running (GL-002236): observed -34, expected 0; CUST43566
- D03/default seed 41105 unapplied_running (GL-002244): observed -184, expected 0; CUST81946
- D03/default seed 41106 unapplied_running (GL-003529): observed -74, expected 0; C-0932
- D03/default seed 41113 unapplied_running (GL-004473): observed -115, expected 0; CUST50826
- D03/default seed 41115 unapplied_running (L04189): observed -224685, expected 0; E1486
- D03/default seed 41115 unapplied_running (L04274): observed -37185, expected 0; E5780
- D03/default seed 41116 unapplied_running (GL-002108): observed -73, expected 0; C-2466
- D03/default seed 41117 unapplied_running (GL-002803): observed -1, expected 0; E1961
- D03/default seed 41119 unapplied_running (GL-000964): observed -3, expected 0; E2473
- D03/default seed 41124 unapplied_running (GL-002245): observed -205, expected 0; C-6104
- D03/default seed 41125 unapplied_running (L00377): observed -1181, expected 0; CUST50140
- D03/default seed 41127 ar_running (GL-002840): observed -1, expected 0; F0686931
- D03/default seed 41128 unapplied_running (GL-002910): observed -97, expected 0; C-9525
- D03/default seed 41131 unapplied_running (L04366): observed -67, expected 0; C-2139
- D03/default seed 41131 unapplied_running (L04354): observed -353, expected 0; C-6052
- D03/default seed 41132 unapplied_running (R644): observed -46, expected 0; C-9933
- D03/default seed 41137 ar_running (GL-001286): observed -1, expected 0; 2501-410390
- D03/default seed 41140 unapplied_running (L01432): observed -446, expected 0; E0345
- D03/default seed 41141 ar_running (R3610): observed -1, expected 0; INV-054288
- D03/default seed 41142 unapplied_running (L03781): observed -10874, expected 0; CUST89097
- D03/default seed 41144 unapplied_running (L03241): observed -291, expected 0; E6937
- D03/default seed 41147 unapplied_running (L03708): observed -85, expected 0; E5990
- D03/default seed 41149 unapplied_running (R708): observed -60771, expected 0; C-9138
- D03/default seed 41150 unapplied_running (L01764): observed -742, expected 0; C-4875
- D03/default seed 41157 unapplied_running (L04564): observed -20455, expected 0; CUST09866
- D03/default seed 41158 unapplied_running (GL-000362): observed -1214, expected 0; E5459
- D03/default seed 41166 ar_running (GL-004004): observed -1, expected 0; 2506-422686
- D03/default seed 41170 unapplied_running (L01112): observed -27, expected 0; C-4024
- D03/default seed 41171 unapplied_running (L02781): observed -314, expected 0; C-5870
- D03/default seed 41173 unapplied_running (GL-001084): observed -132, expected 0; C-4096
- D03/default seed 41174 ar_running (GL-000390): observed -1, expected 0; SI-2025-590188
- D03/default seed 41174 unapplied_running (GL-000426): observed -286, expected 0; C-4736
- D03/default seed 41178 unapplied_running (L03744): observed -118378, expected 0; E8203
- D03/default seed 41182 ar_running (GL-000759): observed -1, expected 0; SI-2026-721173
- D03/default seed 41183 unapplied_running (L02610): observed -7, expected 0; CUST45617
- D03/default seed 41190 unapplied_running (GL-003022): observed -314, expected 0; C-6621
- D03/default seed 41192 ar_running (GL-004482): observed -1, expected 0; 2611-659303
- D03/default seed 41193 unapplied_running (GL-002517): observed -78, expected 0; CUST47530
- D03/default seed 41194 unapplied_running (L00725): observed -46, expected 0; E1812
- D03/default seed 41194 unapplied_running (L00782): observed -384, expected 0; E1022
- D03/default seed 41195 ar_running (GL-003793): observed -1, expected 0; F0615449
- D03/default seed 41196 unapplied_running (GL-003493): observed -44, expected 0; E4315
- D03/default seed 41197 unapplied_running (L02821): observed -3071, expected 0; CUST82232
- D03/default seed 41198 unapplied_running (L03718): observed -47, expected 0; CUST24584
- D03/default seed 41199 ar_running (R2679): observed -1, expected 0; F0107215
- D03/default seed 41203 unapplied_running (GL-002257): observed -220, expected 0; CUST44083
- D03/default seed 41205 unapplied_running (R4514): observed -12, expected 0; E5788
- D03/default seed 41208 unapplied_running (L02934): observed -49953, expected 0; CUST80841
- D03/default seed 41209 unapplied_running (GL-004432): observed -74, expected 0; C-3115
- D03/default seed 41212 ar_running (L01373): observed -1, expected 0; SI-2025-273988
- D03/default seed 41214 unapplied_running (R2379): observed -367, expected 0; E9465
- D03/default seed 41216 unapplied_running (R5038): observed -74, expected 0; C-8256
- D03/default seed 41220 unapplied_running (GL-002466): observed -26938, expected 0; E5508
- D03/default seed 41222 ar_running (GL-002092): observed -1, expected 0; INV-911729
- D03/default seed 41224 unapplied_running (L02932): observed -402, expected 0; E4306
- D03/default seed 41225 ar_running (R4393): observed -1, expected 0; INV-763469
- D03/default seed 41225 ar_running (R4435): observed -1, expected 0; INV-981731
- D03/default seed 41229 unapplied_running (GL-004718): observed -115, expected 0; C-5574
- D03/default seed 41234 unapplied_running (R2145): observed -46, expected 0; CUST28806
- D03/default seed 41234 unapplied_running (R2201): observed -21, expected 0; CUST09400
- D03/default seed 41236 unapplied_running (L02890): observed -55, expected 0; CUST67673
- D03/default seed 41239 ar_running (R1295): observed -1, expected 0; 2611-562598
- D03/default seed 41242 unapplied_running (R736): observed -119, expected 0; E9730
- D03/default seed 41243 ar_running (GL-005203): observed -1, expected 0; F0481630
- D03/default seed 41243 unapplied_running (GL-005212): observed -32, expected 0; CUST32225
- D03/default seed 41244 unapplied_running (L03904): observed -24475, expected 0; CUST93203
- D03/default seed 41244 unapplied_running (L04056): observed -49167, expected 0; CUST54052
- D03/default seed 41244 unapplied_running (L04053): observed -42070, expected 0; CUST05049
- D03/default seed 41245 ar_running (R2719): observed -1, expected 0; INV-988106
- D03/default seed 41247 unapplied_running (L01470): observed -3, expected 0; CUST42949
- D03/default seed 41248 ar_running (L00513): observed -1, expected 0; F0370420
- D03/default seed 41248 unapplied_running (L00432): observed -552, expected 0; E8174
- D03/default seed 41256 unapplied_running (GL-001834): observed -173, expected 0; C-4466
- D03/default seed 41257 unapplied_running (L00782): observed -34, expected 0; E4551
- D03/default seed 41258 ar_running (R1433): observed -1, expected 0; SI-2026-923475
- D03/default seed 41258 unapplied_running (R1238): observed -227031, expected 0; CUST78127
- D03/default seed 41262 ar_running (GL-001158): observed -1, expected 0; F0515687
- D03/default seed 41263 unapplied_running (R5022): observed -91, expected 0; CUST88062
- D03/default seed 41264 unapplied_running (R3651): observed -83, expected 0; C-1145
- D03/default seed 41265 unapplied_running (GL-001966): observed -170, expected 0; C-5923
- D03/default seed 41266 unapplied_running (L00492): observed -2186, expected 0; E7360
- D03/default seed 41267 unapplied_running (L03551): observed -1362, expected 0; E8408
- D03/default seed 41268 unapplied_running (R3548): observed -31589, expected 0; C-4687
- D03/default seed 41270 ar_running (GL-000401): observed -1, expected 0; INV-215118
- D03/default seed 41270 unapplied_running (GL-000443): observed -23, expected 0; CUST74275
- D03/default seed 41277 unapplied_running (L01581): observed -40, expected 0; E3442
- D03/default seed 41277 unapplied_running (L01680): observed -63, expected 0; E3442
- D03/default seed 41277 unapplied_running (L01733): observed -88, expected 0; E3442
- D03/default seed 41282 unapplied_running (GL-003747): observed -56670, expected 0; E8942
- D03/default seed 41283 unapplied_running (L04036): observed -57, expected 0; CUST56709
- D03/default seed 41287 unapplied_running (GL-004422): observed -33477, expected 0; C-5782
- D03/default seed 41287 unapplied_running (GL-004529): observed -16030, expected 0; C-6240
- D03/default seed 41289 unapplied_running (R446): observed -195, expected 0; CUST97557
- D03/default seed 41292 ar_running (L02096): observed -1, expected 0; INV-931351
- D03/default seed 41293 ar_running (GL-003102): observed -1, expected 0; 2503-365156
- D03/default seed 41293 ar_running (GL-003276): observed -1, expected 0; 2503-133260
- D03/default seed 41296 unapplied_running (L03801): observed -60, expected 0; C-9163
- D03/hard seed 41005 ar_running (GL-005749): observed -1, expected 0; INV-064884
- D03/hard seed 41008 unapplied_running (GL-003144): observed -51, expected 0; C-9667
- D03/hard seed 41011 unapplied_running (R3945): observed -229, expected 0; C-9377
- D03/hard seed 41013 ar_running (R2646): observed -1, expected 0; INV-859119
- D03/hard seed 41013 unapplied_running (R2930): observed -28, expected 0; CUST95480
- D03/hard seed 41015 unapplied_running (L05401): observed -98, expected 0; CUST95106
- D03/hard seed 41017 ar_running (L03233): observed -1, expected 0; INV-758326
- D03/hard seed 41018 unapplied_running (L03230): observed -23, expected 0; C-8778
- D03/hard seed 41020 unapplied_running (L01033): observed -303, expected 0; C-0028
- D03/hard seed 41020 unapplied_running (L01160): observed -5, expected 0; C-8284
- D03/hard seed 41024 unapplied_running (R3553): observed -143101, expected 0; E1698
- D03/hard seed 41024 unapplied_running (R3860): observed -188319, expected 0; E1698
- D03/hard seed 41025 unapplied_running (L02152): observed -10190, expected 0; C-6454
- D03/hard seed 41029 unapplied_running (R2704): observed -271, expected 0; CUST08113
- D03/hard seed 41029 unapplied_running (R2832): observed -19, expected 0; CUST09291
- D03/hard seed 41037 ar_running (L03201): observed -1, expected 0; 2611-778760
- D03/hard seed 41037 ar_running (L03244): observed -1, expected 0; 2611-453884
- D03/hard seed 41038 unapplied_running (GL-005437): observed -279331, expected 0; C-0425
- D03/hard seed 41040 ar_running (R5101): observed -1, expected 0; 2609-004130
- D03/hard seed 41045 unapplied_running (R3505): observed -103, expected 0; E2744
- D03/hard seed 41046 unapplied_running (L01489): observed -130, expected 0; E5006
- D03/hard seed 41049 unapplied_running (R3890): observed -315, expected 0; E7530
- D03/hard seed 41050 unapplied_running (L02856): observed -686, expected 0; CUST88801
- D03/hard seed 41052 ar_running (R1027): observed -1, expected 0; SI-2026-798836
- D03/hard seed 41053 unapplied_running (R2367): observed -63, expected 0; C-4903
- D03/hard seed 41061 unapplied_running (L02053): observed -26452, expected 0; CUST15073
- D03/hard seed 41063 ar_running (L01469): observed -1, expected 0; 2609-768605
- D03/hard seed 41065 ar_running (R4601): observed -1, expected 0; F0032065
- D03/hard seed 41073 unapplied_running (GL-001842): observed -420, expected 0; C-0848
- D03/hard seed 41078 unapplied_running (L01768): observed -170902, expected 0; E7114
- D03/hard seed 41079 unapplied_running (L05733): observed -20, expected 0; E5939
- D03/hard seed 41080 unapplied_running (R5253): observed -83, expected 0; C-3829
- D03/hard seed 41088 unapplied_running (GL-001810): observed -246, expected 0; C-6699
- D03/hard seed 41088 unapplied_running (GL-002196): observed -256, expected 0; C-6699
- D03/hard seed 41088 unapplied_running (GL-001984): observed -1, expected 0; C-3111
- D03/hard seed 41091 unapplied_running (GL-003949): observed -57, expected 0; E5263
- D03/hard seed 41092 unapplied_running (L03271): observed -4, expected 0; C-1933
- D03/hard seed 41093 unapplied_running (L02066): observed -2, expected 0; CUST65465
- D03/hard seed 41094 unapplied_running (R5650): observed -4, expected 0; E9227
- D03/hard seed 41096 ar_running (R648): observed -1, expected 0; SI-2026-466918
- D03/hard seed 41097 unapplied_running (R4467): observed -10407, expected 0; CUST02501
- D03/hard seed 41098 ar_running (L04227): observed -1, expected 0; 2612-160441
- D03/hard seed 41098 unapplied_running (L04443): observed -23291, expected 0; C-1225
- D03/hard seed 41099 unapplied_running (L02896): observed -26, expected 0; C-9785
- D03/hard seed 41099 unapplied_running (L03397): observed -9, expected 0; C-3675
- D03/hard seed 41100 ar_running (GL-005821): observed -1, expected 0; 2612-882562
- D03/hard seed 41103 ar_running (R2401): observed -1, expected 0; F0054592
- D03/hard seed 41106 ar_running (L03291): observed -1, expected 0; 2507-119107
- D03/hard seed 41108 unapplied_running (GL-003547): observed -174, expected 0; C-6620
- D03/hard seed 41112 ar_running (R4842): observed -1, expected 0; 2508-594384
- D03/hard seed 41115 ar_running (L03813): observed -1, expected 0; 2507-425960
- D03/hard seed 41118 ar_running (GL-004927): observed -1, expected 0; INV-114883
- D03/hard seed 41118 unapplied_running (GL-005060): observed -34, expected 0; CUST19568
- D03/hard seed 41123 ar_running (R4880): observed -1, expected 0; INV-019033
- D03/hard seed 41124 unapplied_running (L00585): observed -1, expected 0; CUST35077
- D03/hard seed 41128 ar_running (GL-001786): observed -1, expected 0; SI-2026-305268
- D03/hard seed 41134 unapplied_running (GL-005307): observed -201, expected 0; CUST34155
- D03/hard seed 41137 ar_running (R1542): observed -1, expected 0; F0267943
- D03/hard seed 41142 unapplied_running (GL-002585): observed -250, expected 0; C-5710
- D03/hard seed 41150 unapplied_running (L05035): observed -85, expected 0; CUST48458
- D03/hard seed 41151 ar_running (L00532): observed -1, expected 0; INV-263286
- D03/hard seed 41156 ar_running (R5500): observed -1, expected 0; 2508-592873
- D03/hard seed 41164 ar_running (R3355): observed -1, expected 0; 2504-064452
- D03/hard seed 41165 unapplied_running (R3538): observed -228, expected 0; CUST82075
- D03/hard seed 41170 ar_running (R3853): observed -1, expected 0; INV-886051
- D03/hard seed 41170 ar_running (R3783): observed -1, expected 0; INV-044439
- D03/hard seed 41172 unapplied_running (L02902): observed -136, expected 0; E2316
- D03/hard seed 41173 unapplied_running (L05206): observed -69, expected 0; E8466
- D03/hard seed 41174 ar_running (R1947): observed -1, expected 0; 2501-044446
- D03/hard seed 41174 unapplied_running (R1343): observed -104023, expected 0; C-2817
- D03/hard seed 41175 unapplied_running (L05070): observed -213, expected 0; C-7166
- D03/hard seed 41176 unapplied_running (GL-005340): observed -579, expected 0; E1431
- D03/hard seed 41179 ar_running (R5285): observed -1, expected 0; 2502-263509
- D03/hard seed 41185 ar_running (L05076): observed -1, expected 0; SI-2026-814573
- D03/hard seed 41194 ar_running (L05631): observed -1, expected 0; INV-589999
- D03/hard seed 41197 unapplied_running (L04940): observed -5371, expected 0; E9990
- D03/hard seed 41199 unapplied_running (GL-000525): observed -9, expected 0; CUST88252
- D03/hard seed 41200 unapplied_running (R3852): observed -10, expected 0; E9348
- D03/hard seed 41200 unapplied_running (R3947): observed -54, expected 0; E3676
- D03/hard seed 41201 unapplied_running (GL-004366): observed -14, expected 0; E0747
- D03/hard seed 41202 unapplied_running (R731): observed -67, expected 0; E8053
- D03/hard seed 41204 ar_running (R3490): observed -1, expected 0; INV-929188
- D03/hard seed 41204 unapplied_running (R3004): observed -33679, expected 0; C-2446
- D03/hard seed 41208 unapplied_running (R1128): observed -13, expected 0; C-8157
- D03/hard seed 41208 unapplied_running (R1712): observed -7, expected 0; C-8157
- D03/hard seed 41210 unapplied_running (R1520): observed -1, expected 0; E8676
- D03/hard seed 41211 unapplied_running (R1389): observed -1150, expected 0; E7884
- D03/hard seed 41212 ar_running (GL-003946): observed -1, expected 0; 2603-669849
- D03/hard seed 41216 ar_running (R2147): observed -1, expected 0; SI-2025-019680
- D03/hard seed 41216 ar_running (R2145): observed -1, expected 0; SI-2025-363180
- D03/hard seed 41216 unapplied_running (R2104): observed -66, expected 0; E3666
- D03/hard seed 41218 unapplied_running (R2840): observed -84, expected 0; C-6028
- D03/hard seed 41224 unapplied_running (GL-001578): observed -143, expected 0; E2277
- D03/hard seed 41232 unapplied_running (R5419): observed -198, expected 0; E5211
- D03/hard seed 41233 unapplied_running (GL-004739): observed -82, expected 0; C-3362
- D03/hard seed 41234 ar_running (GL-002416): observed -1, expected 0; SI-2025-000350
- D03/hard seed 41235 unapplied_running (GL-002070): observed -17333, expected 0; CUST16801
- D03/hard seed 41236 unapplied_running (GL-003576): observed -216, expected 0; CUST89445
- D03/hard seed 41240 ar_running (GL-002596): observed -1, expected 0; F0438164
- D03/hard seed 41243 unapplied_running (R2468): observed -38, expected 0; E7080
- D03/hard seed 41244 unapplied_running (L01940): observed -194678, expected 0; E7439
- D03/hard seed 41249 ar_running (R4435): observed -1, expected 0; SI-2026-018892
- D03/hard seed 41249 unapplied_running (R4476): observed -16, expected 0; E0639
- D03/hard seed 41251 ar_running (GL-004129): observed -1, expected 0; 2602-317250
- D03/hard seed 41253 ar_running (L01044): observed -1, expected 0; 2502-305985
- D03/hard seed 41253 ar_running (L00832): observed -1, expected 0; 2502-633501
- D03/hard seed 41262 ar_running (GL-003336): observed -1, expected 0; INV-882581
- D03/hard seed 41266 ar_running (GL-002148): observed -1, expected 0; F0818242
- D03/hard seed 41266 ar_running (GL-001994): observed -1, expected 0; F0254037
- D03/hard seed 41267 unapplied_running (GL-004356): observed -164, expected 0; E8308
- D03/hard seed 41276 unapplied_running (GL-004211): observed -32, expected 0; CUST98146
- D03/hard seed 41278 ar_running (GL-000895): observed -1, expected 0; SI-2025-730616
- D03/hard seed 41279 ar_running (L01297): observed -1, expected 0; F0674420
- D03/hard seed 41279 unapplied_running (L01357): observed -154, expected 0; C-1009
- D03/hard seed 41282 ar_running (R4406): observed -1, expected 0; F0128741
- D03/hard seed 41284 unapplied_running (R3587): observed -108, expected 0; C-7663
- D03/hard seed 41286 unapplied_running (GL-002193): observed -40, expected 0; C-7586
- D03/hard seed 41287 unapplied_running (GL-003483): observed -259, expected 0; CUST73028
- D03/hard seed 41288 unapplied_running (L02451): observed -14938, expected 0; E7606
- D03/hard seed 41289 unapplied_running (L03602): observed -1092, expected 0; CUST97015
- D03/hard seed 41289 unapplied_running (L03815): observed -251, expected 0; CUST84414
- D03/hard seed 41290 ar_running (R5259): observed -1, expected 0; F0617458
- D03/hard seed 41291 ar_running (R5756): observed -1, expected 0; 2604-148765
- D03/hard seed 41291 unapplied_running (R5269): observed -78791, expected 0; E8132
- D03/hard seed 41292 ar_running (GL-005681): observed -1, expected 0; INV-315947
- D03/hard seed 41292 unapplied_running (GL-005406): observed -13, expected 0; E5289
- D03/hard seed 41295 ar_running (R3380): observed -1, expected 0; F0203109
- D03/hard seed 41298 unapplied_running (R3356): observed -4, expected 0; C-7601
- D03/hard seed 41299 ar_running (R3080): observed -1, expected 0; SI-2025-343694
- D03/hard seed 41299 unapplied_running (R2644): observed -27, expected 0; E7083
- D04/default seed 41005 unapplied_running (GL-005178): observed -923, expected 0; CUST99859
- D04/default seed 41006 unapplied_running (GL-001878): observed -500336, expected 0; E0342
- D04/default seed 41007 ar_running (R2705): observed -1, expected 0; F0057818
- D04/default seed 41011 unapplied_running (L00316): observed -15, expected 0; C-5874
- D04/default seed 41012 unapplied_running (GL-005228): observed -87, expected 0; CUST57663
- D04/default seed 41013 unapplied_running (R3768): observed -168, expected 0; E6981
- D04/default seed 41014 unapplied_running (L03913): observed -2, expected 0; C-5080
- D04/default seed 41019 ar_running (GL-000793): observed -1, expected 0; INV-355747
- D04/default seed 41020 unapplied_running (L02377): observed -5, expected 0; E7129
- D04/default seed 41021 unapplied_running (R1433): observed -214, expected 0; E1968
- D04/default seed 41028 ar_running (L02016): observed -1, expected 0; F0606872
- D04/default seed 41028 unapplied_running (L02007): observed -56, expected 0; C-7863
- D04/default seed 41029 unapplied_running (R384): observed -128, expected 0; CUST43875
- D04/default seed 41032 unapplied_running (L00595): observed -86531, expected 0; C-2404
- D04/default seed 41034 ar_running (R229): observed -1, expected 0; 2503-857257
- D04/default seed 41039 ar_running (R988): observed -1, expected 0; SI-2025-984723
- D04/default seed 41043 unapplied_running (R3711): observed -667, expected 0; C-8659
- D04/default seed 41043 unapplied_running (R3858): observed -186, expected 0; C-7120
- D04/default seed 41044 unapplied_running (R4057): observed -32683, expected 0; E4613
- D04/default seed 41044 unapplied_running (R4054): observed -55854, expected 0; E9712
- D04/default seed 41045 ar_running (R4175): observed -1, expected 0; F0254951
- D04/default seed 41058 unapplied_running (L01321): observed -12, expected 0; C-0392
- D04/default seed 41059 unapplied_running (R2679): observed -41, expected 0; C-8026
- D04/default seed 41061 unapplied_running (R2190): observed -661, expected 0; CUST70335
- D04/default seed 41064 unapplied_running (R987): observed -47522, expected 0; CUST98460
- D04/default seed 41064 unapplied_running (R1036): observed -2977, expected 0; CUST42293
- D04/default seed 41066 unapplied_running (L04325): observed -555, expected 0; CUST55531
- D04/default seed 41068 unapplied_running (R1521): observed -64, expected 0; CUST07021
- D04/default seed 41071 unapplied_running (GL-000910): observed -132, expected 0; C-5747
- D04/default seed 41074 ar_running (GL-003948): observed -1, expected 0; 2601-593279
- D04/default seed 41080 unapplied_running (GL-004509): observed -14, expected 0; E9009
- D04/default seed 41081 unapplied_running (R4233): observed -225, expected 0; C-7364
- D04/default seed 41082 ar_running (GL-005049): observed -1, expected 0; F0880818
- D04/default seed 41084 unapplied_running (GL-001329): observed -91, expected 0; CUST52532
- D04/default seed 41084 unapplied_running (GL-001504): observed -16, expected 0; CUST14537
- D04/default seed 41086 unapplied_running (L03721): observed -214, expected 0; C-6213
- D04/default seed 41091 unapplied_running (R2905): observed -9, expected 0; C-1116
- D04/default seed 41094 ar_running (R3306): observed -1, expected 0; INV-357622
- D04/default seed 41100 ar_running (R1817): observed -1, expected 0; 2510-112034
- D04/default seed 41102 unapplied_running (L00536): observed -2, expected 0; CUST61593
- D04/default seed 41105 unapplied_running (GL-002236): observed -34, expected 0; CUST43566
- D04/default seed 41105 unapplied_running (GL-002244): observed -184, expected 0; CUST81946
- D04/default seed 41106 unapplied_running (GL-003529): observed -74, expected 0; C-0932
- D04/default seed 41113 unapplied_running (GL-004473): observed -115, expected 0; CUST50826
- D04/default seed 41115 unapplied_running (L04189): observed -224685, expected 0; E1486
- D04/default seed 41115 unapplied_running (L04274): observed -37185, expected 0; E5780
- D04/default seed 41116 unapplied_running (GL-002108): observed -73, expected 0; C-2466
- D04/default seed 41117 unapplied_running (GL-002803): observed -1, expected 0; E1961
- D04/default seed 41119 unapplied_running (GL-000964): observed -3, expected 0; E2473
- D04/default seed 41124 unapplied_running (GL-002245): observed -205, expected 0; C-6104
- D04/default seed 41125 unapplied_running (L00377): observed -1181, expected 0; CUST50140
- D04/default seed 41127 ar_running (GL-002840): observed -1, expected 0; F0686931
- D04/default seed 41128 unapplied_running (GL-002910): observed -97, expected 0; C-9525
- D04/default seed 41131 unapplied_running (L04366): observed -67, expected 0; C-2139
- D04/default seed 41131 unapplied_running (L04354): observed -353, expected 0; C-6052
- D04/default seed 41132 unapplied_running (R644): observed -46, expected 0; C-9933
- D04/default seed 41137 ar_running (GL-001286): observed -1, expected 0; 2501-410390
- D04/default seed 41140 unapplied_running (L01432): observed -446, expected 0; E0345
- D04/default seed 41141 ar_running (R3610): observed -1, expected 0; INV-054288
- D04/default seed 41142 unapplied_running (L03781): observed -10874, expected 0; CUST89097
- D04/default seed 41144 unapplied_running (L03241): observed -291, expected 0; E6937
- D04/default seed 41147 unapplied_running (L03708): observed -85, expected 0; E5990
- D04/default seed 41149 unapplied_running (R708): observed -60771, expected 0; C-9138
- D04/default seed 41150 unapplied_running (L01764): observed -742, expected 0; C-4875
- D04/default seed 41157 unapplied_running (L04564): observed -20455, expected 0; CUST09866
- D04/default seed 41158 unapplied_running (GL-000362): observed -1214, expected 0; E5459
- D04/default seed 41166 ar_running (GL-004004): observed -1, expected 0; 2506-422686
- D04/default seed 41170 unapplied_running (L01112): observed -27, expected 0; C-4024
- D04/default seed 41171 unapplied_running (L02781): observed -314, expected 0; C-5870
- D04/default seed 41173 unapplied_running (GL-001084): observed -132, expected 0; C-4096
- D04/default seed 41174 ar_running (GL-000390): observed -1, expected 0; SI-2025-590188
- D04/default seed 41174 unapplied_running (GL-000426): observed -286, expected 0; C-4736
- D04/default seed 41178 unapplied_running (L03744): observed -118378, expected 0; E8203
- D04/default seed 41182 ar_running (GL-000759): observed -1, expected 0; SI-2026-721173
- D04/default seed 41183 unapplied_running (L02610): observed -7, expected 0; CUST45617
- D04/default seed 41190 unapplied_running (GL-003022): observed -314, expected 0; C-6621
- D04/default seed 41192 ar_running (GL-004482): observed -1, expected 0; 2611-659303
- D04/default seed 41193 unapplied_running (GL-002517): observed -78, expected 0; CUST47530
- D04/default seed 41194 unapplied_running (L00725): observed -46, expected 0; E1812
- D04/default seed 41194 unapplied_running (L00782): observed -384, expected 0; E1022
- D04/default seed 41195 ar_running (GL-003793): observed -1, expected 0; F0615449
- D04/default seed 41196 unapplied_running (GL-003493): observed -44, expected 0; E4315
- D04/default seed 41197 unapplied_running (L02821): observed -3071, expected 0; CUST82232
- D04/default seed 41198 unapplied_running (L03718): observed -47, expected 0; CUST24584
- D04/default seed 41199 ar_running (R2679): observed -1, expected 0; F0107215
- D04/default seed 41203 unapplied_running (GL-002257): observed -220, expected 0; CUST44083
- D04/default seed 41205 unapplied_running (R4514): observed -12, expected 0; E5788
- D04/default seed 41208 unapplied_running (L02934): observed -49953, expected 0; CUST80841
- D04/default seed 41209 unapplied_running (GL-004432): observed -74, expected 0; C-3115
- D04/default seed 41212 ar_running (L01373): observed -1, expected 0; SI-2025-273988
- D04/default seed 41214 unapplied_running (R2379): observed -367, expected 0; E9465
- D04/default seed 41216 unapplied_running (R5038): observed -74, expected 0; C-8256
- D04/default seed 41220 unapplied_running (GL-002466): observed -26938, expected 0; E5508
- D04/default seed 41222 ar_running (GL-002092): observed -1, expected 0; INV-911729
- D04/default seed 41224 unapplied_running (L02932): observed -402, expected 0; E4306
- D04/default seed 41225 ar_running (R4393): observed -1, expected 0; INV-763469
- D04/default seed 41225 ar_running (R4435): observed -1, expected 0; INV-981731
- D04/default seed 41229 unapplied_running (GL-004718): observed -115, expected 0; C-5574
- D04/default seed 41234 unapplied_running (R2145): observed -46, expected 0; CUST28806
- D04/default seed 41234 unapplied_running (R2201): observed -21, expected 0; CUST09400
- D04/default seed 41236 unapplied_running (L02890): observed -55, expected 0; CUST67673
- D04/default seed 41239 ar_running (R1295): observed -1, expected 0; 2611-562598
- D04/default seed 41242 unapplied_running (R736): observed -119, expected 0; E9730
- D04/default seed 41243 ar_running (GL-005203): observed -1, expected 0; F0481630
- D04/default seed 41243 unapplied_running (GL-005212): observed -32, expected 0; CUST32225
- D04/default seed 41244 unapplied_running (L03904): observed -24475, expected 0; CUST93203
- D04/default seed 41244 unapplied_running (L04056): observed -49167, expected 0; CUST54052
- D04/default seed 41244 unapplied_running (L04053): observed -42070, expected 0; CUST05049
- D04/default seed 41245 ar_running (R2719): observed -1, expected 0; INV-988106
- D04/default seed 41247 unapplied_running (L01470): observed -3, expected 0; CUST42949
- D04/default seed 41248 ar_running (L00513): observed -1, expected 0; F0370420
- D04/default seed 41248 unapplied_running (L00432): observed -552, expected 0; E8174
- D04/default seed 41256 unapplied_running (GL-001834): observed -173, expected 0; C-4466
- D04/default seed 41257 unapplied_running (L00782): observed -34, expected 0; E4551
- D04/default seed 41258 ar_running (R1433): observed -1, expected 0; SI-2026-923475
- D04/default seed 41258 unapplied_running (R1238): observed -227031, expected 0; CUST78127
- D04/default seed 41262 ar_running (GL-001158): observed -1, expected 0; F0515687
- D04/default seed 41263 unapplied_running (R5022): observed -91, expected 0; CUST88062
- D04/default seed 41264 unapplied_running (R3651): observed -83, expected 0; C-1145
- D04/default seed 41265 unapplied_running (GL-001966): observed -170, expected 0; C-5923
- D04/default seed 41266 unapplied_running (L00492): observed -2186, expected 0; E7360
- D04/default seed 41267 unapplied_running (L03551): observed -1362, expected 0; E8408
- D04/default seed 41268 unapplied_running (R3548): observed -31589, expected 0; C-4687
- D04/default seed 41270 ar_running (GL-000401): observed -1, expected 0; INV-215118
- D04/default seed 41270 unapplied_running (GL-000443): observed -23, expected 0; CUST74275
- D04/default seed 41277 unapplied_running (L01581): observed -40, expected 0; E3442
- D04/default seed 41277 unapplied_running (L01680): observed -63, expected 0; E3442
- D04/default seed 41277 unapplied_running (L01733): observed -88, expected 0; E3442
- D04/default seed 41282 unapplied_running (GL-003747): observed -56670, expected 0; E8942
- D04/default seed 41283 unapplied_running (L04036): observed -57, expected 0; CUST56709
- D04/default seed 41287 unapplied_running (GL-004422): observed -33477, expected 0; C-5782
- D04/default seed 41287 unapplied_running (GL-004529): observed -16030, expected 0; C-6240
- D04/default seed 41289 unapplied_running (R446): observed -195, expected 0; CUST97557
- D04/default seed 41292 ar_running (L02096): observed -1, expected 0; INV-931351
- D04/default seed 41293 ar_running (GL-003102): observed -1, expected 0; 2503-365156
- D04/default seed 41293 ar_running (GL-003276): observed -1, expected 0; 2503-133260
- D04/default seed 41296 unapplied_running (L03801): observed -60, expected 0; C-9163
- D04/hard seed 41005 ar_running (GL-005749): observed -1, expected 0; INV-064884
- D04/hard seed 41008 unapplied_running (GL-003144): observed -51, expected 0; C-9667
- D04/hard seed 41011 unapplied_running (R3945): observed -229, expected 0; C-9377
- D04/hard seed 41013 ar_running (R2646): observed -1, expected 0; INV-859119
- D04/hard seed 41013 unapplied_running (R2930): observed -28, expected 0; CUST95480
- D04/hard seed 41015 unapplied_running (L05401): observed -98, expected 0; CUST95106
- D04/hard seed 41017 ar_running (L03233): observed -1, expected 0; INV-758326
- D04/hard seed 41018 unapplied_running (L03230): observed -23, expected 0; C-8778
- D04/hard seed 41020 unapplied_running (L01033): observed -303, expected 0; C-0028
- D04/hard seed 41020 unapplied_running (L01160): observed -5, expected 0; C-8284
- D04/hard seed 41024 unapplied_running (R3553): observed -143101, expected 0; E1698
- D04/hard seed 41024 unapplied_running (R3860): observed -188319, expected 0; E1698
- D04/hard seed 41025 unapplied_running (L02152): observed -10190, expected 0; C-6454
- D04/hard seed 41029 unapplied_running (R2704): observed -271, expected 0; CUST08113
- D04/hard seed 41029 unapplied_running (R2832): observed -19, expected 0; CUST09291
- D04/hard seed 41037 ar_running (L03201): observed -1, expected 0; 2611-778760
- D04/hard seed 41037 ar_running (L03244): observed -1, expected 0; 2611-453884
- D04/hard seed 41038 unapplied_running (GL-005437): observed -279331, expected 0; C-0425
- D04/hard seed 41040 ar_running (R5101): observed -1, expected 0; 2609-004130
- D04/hard seed 41045 unapplied_running (R3505): observed -103, expected 0; E2744
- D04/hard seed 41046 unapplied_running (L01489): observed -130, expected 0; E5006
- D04/hard seed 41049 unapplied_running (R3890): observed -315, expected 0; E7530
- D04/hard seed 41050 unapplied_running (L02856): observed -686, expected 0; CUST88801
- D04/hard seed 41052 ar_running (R1027): observed -1, expected 0; SI-2026-798836
- D04/hard seed 41053 unapplied_running (R2367): observed -63, expected 0; C-4903
- D04/hard seed 41061 unapplied_running (L02053): observed -26452, expected 0; CUST15073
- D04/hard seed 41063 ar_running (L01469): observed -1, expected 0; 2609-768605
- D04/hard seed 41065 ar_running (R4601): observed -1, expected 0; F0032065
- D04/hard seed 41073 unapplied_running (GL-001842): observed -420, expected 0; C-0848
- D04/hard seed 41078 unapplied_running (L01768): observed -170902, expected 0; E7114
- D04/hard seed 41079 unapplied_running (L05733): observed -20, expected 0; E5939
- D04/hard seed 41080 unapplied_running (R5253): observed -83, expected 0; C-3829
- D04/hard seed 41088 unapplied_running (GL-001810): observed -246, expected 0; C-6699
- D04/hard seed 41088 unapplied_running (GL-002196): observed -256, expected 0; C-6699
- D04/hard seed 41088 unapplied_running (GL-001984): observed -1, expected 0; C-3111
- D04/hard seed 41091 unapplied_running (GL-003949): observed -57, expected 0; E5263
- D04/hard seed 41092 unapplied_running (L03271): observed -4, expected 0; C-1933
- D04/hard seed 41093 unapplied_running (L02066): observed -2, expected 0; CUST65465
- D04/hard seed 41094 unapplied_running (R5650): observed -4, expected 0; E9227
- D04/hard seed 41096 ar_running (R648): observed -1, expected 0; SI-2026-466918
- D04/hard seed 41097 unapplied_running (R4467): observed -10407, expected 0; CUST02501
- D04/hard seed 41098 ar_running (L04227): observed -1, expected 0; 2612-160441
- D04/hard seed 41098 unapplied_running (L04443): observed -23291, expected 0; C-1225
- D04/hard seed 41099 unapplied_running (L02896): observed -26, expected 0; C-9785
- D04/hard seed 41099 unapplied_running (L03397): observed -9, expected 0; C-3675
- D04/hard seed 41100 ar_running (GL-005821): observed -1, expected 0; 2612-882562
- D04/hard seed 41103 ar_running (R2401): observed -1, expected 0; F0054592
- D04/hard seed 41106 ar_running (L03291): observed -1, expected 0; 2507-119107
- D04/hard seed 41108 unapplied_running (GL-003547): observed -174, expected 0; C-6620
- D04/hard seed 41112 ar_running (R4842): observed -1, expected 0; 2508-594384
- D04/hard seed 41115 ar_running (L03813): observed -1, expected 0; 2507-425960
- D04/hard seed 41118 ar_running (GL-004927): observed -1, expected 0; INV-114883
- D04/hard seed 41118 unapplied_running (GL-005060): observed -34, expected 0; CUST19568
- D04/hard seed 41123 ar_running (R4880): observed -1, expected 0; INV-019033
- D04/hard seed 41124 unapplied_running (L00585): observed -1, expected 0; CUST35077
- D04/hard seed 41128 ar_running (GL-001786): observed -1, expected 0; SI-2026-305268
- D04/hard seed 41134 unapplied_running (GL-005307): observed -201, expected 0; CUST34155
- D04/hard seed 41137 ar_running (R1542): observed -1, expected 0; F0267943
- D04/hard seed 41142 unapplied_running (GL-002585): observed -250, expected 0; C-5710
- D04/hard seed 41150 unapplied_running (L05035): observed -85, expected 0; CUST48458
- D04/hard seed 41151 ar_running (L00532): observed -1, expected 0; INV-263286
- D04/hard seed 41156 ar_running (R5500): observed -1, expected 0; 2508-592873
- D04/hard seed 41164 ar_running (R3355): observed -1, expected 0; 2504-064452
- D04/hard seed 41165 unapplied_running (R3538): observed -228, expected 0; CUST82075
- D04/hard seed 41170 ar_running (R3853): observed -1, expected 0; INV-886051
- D04/hard seed 41170 ar_running (R3783): observed -1, expected 0; INV-044439
- D04/hard seed 41172 unapplied_running (L02902): observed -136, expected 0; E2316
- D04/hard seed 41173 unapplied_running (L05206): observed -69, expected 0; E8466
- D04/hard seed 41174 ar_running (R1947): observed -1, expected 0; 2501-044446
- D04/hard seed 41174 unapplied_running (R1343): observed -104023, expected 0; C-2817
- D04/hard seed 41175 unapplied_running (L05070): observed -213, expected 0; C-7166
- D04/hard seed 41176 unapplied_running (GL-005340): observed -579, expected 0; E1431
- D04/hard seed 41179 ar_running (R5285): observed -1, expected 0; 2502-263509
- D04/hard seed 41185 ar_running (L05076): observed -1, expected 0; SI-2026-814573
- D04/hard seed 41194 ar_running (L05631): observed -1, expected 0; INV-589999
- D04/hard seed 41197 unapplied_running (L04940): observed -5371, expected 0; E9990
- D04/hard seed 41199 unapplied_running (GL-000525): observed -9, expected 0; CUST88252
- D04/hard seed 41200 unapplied_running (R3852): observed -10, expected 0; E9348
- D04/hard seed 41200 unapplied_running (R3947): observed -54, expected 0; E3676
- D04/hard seed 41201 unapplied_running (GL-004366): observed -14, expected 0; E0747
- D04/hard seed 41202 unapplied_running (R731): observed -67, expected 0; E8053
- D04/hard seed 41204 ar_running (R3490): observed -1, expected 0; INV-929188
- D04/hard seed 41204 unapplied_running (R3004): observed -33679, expected 0; C-2446
- D04/hard seed 41208 unapplied_running (R1128): observed -13, expected 0; C-8157
- D04/hard seed 41208 unapplied_running (R1712): observed -7, expected 0; C-8157
- D04/hard seed 41210 unapplied_running (R1520): observed -1, expected 0; E8676
- D04/hard seed 41211 unapplied_running (R1389): observed -1150, expected 0; E7884
- D04/hard seed 41212 ar_running (GL-003946): observed -1, expected 0; 2603-669849
- D04/hard seed 41216 ar_running (R2147): observed -1, expected 0; SI-2025-019680
- D04/hard seed 41216 ar_running (R2145): observed -1, expected 0; SI-2025-363180
- D04/hard seed 41216 unapplied_running (R2104): observed -66, expected 0; E3666
- D04/hard seed 41218 unapplied_running (R2840): observed -84, expected 0; C-6028
- D04/hard seed 41224 unapplied_running (GL-001578): observed -143, expected 0; E2277
- D04/hard seed 41232 unapplied_running (R5419): observed -198, expected 0; E5211
- D04/hard seed 41233 unapplied_running (GL-004739): observed -82, expected 0; C-3362
- D04/hard seed 41234 ar_running (GL-002416): observed -1, expected 0; SI-2025-000350
- D04/hard seed 41235 unapplied_running (GL-002070): observed -17333, expected 0; CUST16801
- D04/hard seed 41236 unapplied_running (GL-003576): observed -216, expected 0; CUST89445
- D04/hard seed 41240 ar_running (GL-002596): observed -1, expected 0; F0438164
- D04/hard seed 41243 unapplied_running (R2468): observed -38, expected 0; E7080
- D04/hard seed 41244 unapplied_running (L01940): observed -194678, expected 0; E7439
- D04/hard seed 41249 ar_running (R4435): observed -1, expected 0; SI-2026-018892
- D04/hard seed 41249 unapplied_running (R4476): observed -16, expected 0; E0639
- D04/hard seed 41251 ar_running (GL-004129): observed -1, expected 0; 2602-317250
- D04/hard seed 41253 ar_running (L01044): observed -1, expected 0; 2502-305985
- D04/hard seed 41253 ar_running (L00832): observed -1, expected 0; 2502-633501
- D04/hard seed 41262 ar_running (GL-003336): observed -1, expected 0; INV-882581
- D04/hard seed 41266 ar_running (GL-002148): observed -1, expected 0; F0818242
- D04/hard seed 41266 ar_running (GL-001994): observed -1, expected 0; F0254037
- D04/hard seed 41267 unapplied_running (GL-004356): observed -164, expected 0; E8308
- D04/hard seed 41276 unapplied_running (GL-004211): observed -32, expected 0; CUST98146
- D04/hard seed 41278 ar_running (GL-000895): observed -1, expected 0; SI-2025-730616
- D04/hard seed 41279 ar_running (L01297): observed -1, expected 0; F0674420
- D04/hard seed 41279 unapplied_running (L01357): observed -154, expected 0; C-1009
- D04/hard seed 41282 ar_running (R4406): observed -1, expected 0; F0128741
- D04/hard seed 41284 unapplied_running (R3587): observed -108, expected 0; C-7663
- D04/hard seed 41286 unapplied_running (GL-002193): observed -40, expected 0; C-7586
- D04/hard seed 41287 unapplied_running (GL-003483): observed -259, expected 0; CUST73028
- D04/hard seed 41288 unapplied_running (L02451): observed -14938, expected 0; E7606
- D04/hard seed 41289 unapplied_running (L03602): observed -1092, expected 0; CUST97015
- D04/hard seed 41289 unapplied_running (L03815): observed -251, expected 0; CUST84414
- D04/hard seed 41290 ar_running (R5259): observed -1, expected 0; F0617458
- D04/hard seed 41291 ar_running (R5756): observed -1, expected 0; 2604-148765
- D04/hard seed 41291 unapplied_running (R5269): observed -78791, expected 0; E8132
- D04/hard seed 41292 ar_running (GL-005681): observed -1, expected 0; INV-315947
- D04/hard seed 41292 unapplied_running (GL-005406): observed -13, expected 0; E5289
- D04/hard seed 41295 ar_running (R3380): observed -1, expected 0; F0203109
- D04/hard seed 41298 unapplied_running (R3356): observed -4, expected 0; C-7601
- D04/hard seed 41299 ar_running (R3080): observed -1, expected 0; SI-2025-343694
- D04/hard seed 41299 unapplied_running (R2644): observed -27, expected 0; E7083
- D05/default seed 41005 unapplied_running (GL-005178): observed -923, expected 0; CUST99859
- D05/default seed 41006 unapplied_running (GL-001878): observed -500336, expected 0; E0342
- D05/default seed 41007 ar_running (R2705): observed -1, expected 0; F0057818
- D05/default seed 41011 unapplied_running (L00316): observed -15, expected 0; C-5874
- D05/default seed 41012 unapplied_running (GL-005228): observed -87, expected 0; CUST57663
- D05/default seed 41013 unapplied_running (R3768): observed -168, expected 0; E6981
- D05/default seed 41014 unapplied_running (L03913): observed -2, expected 0; C-5080
- D05/default seed 41019 ar_running (GL-000793): observed -1, expected 0; INV-355747
- D05/default seed 41020 unapplied_running (L02377): observed -5, expected 0; E7129
- D05/default seed 41021 unapplied_running (R1433): observed -214, expected 0; E1968
- D05/default seed 41028 ar_running (L02016): observed -1, expected 0; F0606872
- D05/default seed 41028 unapplied_running (L02007): observed -56, expected 0; C-7863
- D05/default seed 41029 unapplied_running (R384): observed -128, expected 0; CUST43875
- D05/default seed 41032 unapplied_running (L00595): observed -86531, expected 0; C-2404
- D05/default seed 41034 ar_running (R229): observed -1, expected 0; 2503-857257
- D05/default seed 41039 ar_running (R988): observed -1, expected 0; SI-2025-984723
- D05/default seed 41043 unapplied_running (R3711): observed -667, expected 0; C-8659
- D05/default seed 41043 unapplied_running (R3858): observed -186, expected 0; C-7120
- D05/default seed 41044 unapplied_running (R4057): observed -32683, expected 0; E4613
- D05/default seed 41044 unapplied_running (R4054): observed -55854, expected 0; E9712
- D05/default seed 41045 ar_running (R4175): observed -1, expected 0; F0254951
- D05/default seed 41058 unapplied_running (L01321): observed -12, expected 0; C-0392
- D05/default seed 41059 unapplied_running (R2679): observed -41, expected 0; C-8026
- D05/default seed 41061 unapplied_running (R2190): observed -661, expected 0; CUST70335
- D05/default seed 41064 unapplied_running (R987): observed -47522, expected 0; CUST98460
- D05/default seed 41064 unapplied_running (R1036): observed -2977, expected 0; CUST42293
- D05/default seed 41066 unapplied_running (L04325): observed -555, expected 0; CUST55531
- D05/default seed 41068 unapplied_running (R1521): observed -64, expected 0; CUST07021
- D05/default seed 41071 unapplied_running (GL-000910): observed -132, expected 0; C-5747
- D05/default seed 41074 ar_running (GL-003948): observed -1, expected 0; 2601-593279
- D05/default seed 41080 unapplied_running (GL-004509): observed -14, expected 0; E9009
- D05/default seed 41081 unapplied_running (R4233): observed -225, expected 0; C-7364
- D05/default seed 41082 ar_running (GL-005049): observed -1, expected 0; F0880818
- D05/default seed 41084 unapplied_running (GL-001329): observed -91, expected 0; CUST52532
- D05/default seed 41084 unapplied_running (GL-001504): observed -16, expected 0; CUST14537
- D05/default seed 41086 unapplied_running (L03721): observed -214, expected 0; C-6213
- D05/default seed 41091 unapplied_running (R2905): observed -9, expected 0; C-1116
- D05/default seed 41094 ar_running (R3306): observed -1, expected 0; INV-357622
- D05/default seed 41100 ar_running (R1817): observed -1, expected 0; 2510-112034
- D05/default seed 41102 unapplied_running (L00536): observed -2, expected 0; CUST61593
- D05/default seed 41105 unapplied_running (GL-002236): observed -34, expected 0; CUST43566
- D05/default seed 41105 unapplied_running (GL-002244): observed -184, expected 0; CUST81946
- D05/default seed 41106 unapplied_running (GL-003529): observed -74, expected 0; C-0932
- D05/default seed 41113 unapplied_running (GL-004473): observed -115, expected 0; CUST50826
- D05/default seed 41115 unapplied_running (L04189): observed -224685, expected 0; E1486
- D05/default seed 41115 unapplied_running (L04274): observed -37185, expected 0; E5780
- D05/default seed 41116 unapplied_running (GL-002108): observed -73, expected 0; C-2466
- D05/default seed 41117 unapplied_running (GL-002803): observed -1, expected 0; E1961
- D05/default seed 41119 unapplied_running (GL-000964): observed -3, expected 0; E2473
- D05/default seed 41124 unapplied_running (GL-002245): observed -205, expected 0; C-6104
- D05/default seed 41125 unapplied_running (L00377): observed -1181, expected 0; CUST50140
- D05/default seed 41127 ar_running (GL-002840): observed -1, expected 0; F0686931
- D05/default seed 41128 unapplied_running (GL-002910): observed -97, expected 0; C-9525
- D05/default seed 41131 unapplied_running (L04366): observed -67, expected 0; C-2139
- D05/default seed 41131 unapplied_running (L04354): observed -353, expected 0; C-6052
- D05/default seed 41132 unapplied_running (R644): observed -46, expected 0; C-9933
- D05/default seed 41137 ar_running (GL-001286): observed -1, expected 0; 2501-410390
- D05/default seed 41140 unapplied_running (L01432): observed -446, expected 0; E0345
- D05/default seed 41141 ar_running (R3610): observed -1, expected 0; INV-054288
- D05/default seed 41142 unapplied_running (L03781): observed -10874, expected 0; CUST89097
- D05/default seed 41144 unapplied_running (L03241): observed -291, expected 0; E6937
- D05/default seed 41147 unapplied_running (L03708): observed -85, expected 0; E5990
- D05/default seed 41149 unapplied_running (R708): observed -60771, expected 0; C-9138
- D05/default seed 41150 unapplied_running (L01764): observed -742, expected 0; C-4875
- D05/default seed 41157 unapplied_running (L04564): observed -20455, expected 0; CUST09866
- D05/default seed 41158 unapplied_running (GL-000362): observed -1214, expected 0; E5459
- D05/default seed 41166 ar_running (GL-004004): observed -1, expected 0; 2506-422686
- D05/default seed 41170 unapplied_running (L01112): observed -27, expected 0; C-4024
- D05/default seed 41171 unapplied_running (L02781): observed -314, expected 0; C-5870
- D05/default seed 41173 unapplied_running (GL-001084): observed -132, expected 0; C-4096
- D05/default seed 41174 ar_running (GL-000390): observed -1, expected 0; SI-2025-590188
- D05/default seed 41174 unapplied_running (GL-000426): observed -286, expected 0; C-4736
- D05/default seed 41178 unapplied_running (L03744): observed -118378, expected 0; E8203
- D05/default seed 41182 ar_running (GL-000759): observed -1, expected 0; SI-2026-721173
- D05/default seed 41183 unapplied_running (L02610): observed -7, expected 0; CUST45617
- D05/default seed 41190 unapplied_running (GL-003022): observed -314, expected 0; C-6621
- D05/default seed 41192 ar_running (GL-004482): observed -1, expected 0; 2611-659303
- D05/default seed 41193 unapplied_running (GL-002517): observed -78, expected 0; CUST47530
- D05/default seed 41194 unapplied_running (L00725): observed -46, expected 0; E1812
- D05/default seed 41194 unapplied_running (L00782): observed -384, expected 0; E1022
- D05/default seed 41195 ar_running (GL-003793): observed -1, expected 0; F0615449
- D05/default seed 41196 unapplied_running (GL-003493): observed -44, expected 0; E4315
- D05/default seed 41197 unapplied_running (L02821): observed -3071, expected 0; CUST82232
- D05/default seed 41198 unapplied_running (L03718): observed -47, expected 0; CUST24584
- D05/default seed 41199 ar_running (R2679): observed -1, expected 0; F0107215
- D05/default seed 41203 unapplied_running (GL-002257): observed -220, expected 0; CUST44083
- D05/default seed 41205 unapplied_running (R4514): observed -12, expected 0; E5788
- D05/default seed 41208 unapplied_running (L02934): observed -49953, expected 0; CUST80841
- D05/default seed 41209 unapplied_running (GL-004432): observed -74, expected 0; C-3115
- D05/default seed 41212 ar_running (L01373): observed -1, expected 0; SI-2025-273988
- D05/default seed 41214 unapplied_running (R2379): observed -367, expected 0; E9465
- D05/default seed 41216 unapplied_running (R5038): observed -74, expected 0; C-8256
- D05/default seed 41220 unapplied_running (GL-002466): observed -26938, expected 0; E5508
- D05/default seed 41222 ar_running (GL-002092): observed -1, expected 0; INV-911729
- D05/default seed 41224 unapplied_running (L02932): observed -402, expected 0; E4306
- D05/default seed 41225 ar_running (R4393): observed -1, expected 0; INV-763469
- D05/default seed 41225 ar_running (R4435): observed -1, expected 0; INV-981731
- D05/default seed 41229 unapplied_running (GL-004718): observed -115, expected 0; C-5574
- D05/default seed 41234 unapplied_running (R2145): observed -46, expected 0; CUST28806
- D05/default seed 41234 unapplied_running (R2201): observed -21, expected 0; CUST09400
- D05/default seed 41236 unapplied_running (L02890): observed -55, expected 0; CUST67673
- D05/default seed 41239 ar_running (R1295): observed -1, expected 0; 2611-562598
- D05/default seed 41242 unapplied_running (R736): observed -119, expected 0; E9730
- D05/default seed 41243 ar_running (GL-005203): observed -1, expected 0; F0481630
- D05/default seed 41243 unapplied_running (GL-005212): observed -32, expected 0; CUST32225
- D05/default seed 41244 unapplied_running (L03904): observed -24475, expected 0; CUST93203
- D05/default seed 41244 unapplied_running (L04056): observed -49167, expected 0; CUST54052
- D05/default seed 41244 unapplied_running (L04053): observed -42070, expected 0; CUST05049
- D05/default seed 41245 ar_running (R2719): observed -1, expected 0; INV-988106
- D05/default seed 41247 unapplied_running (L01470): observed -3, expected 0; CUST42949
- D05/default seed 41248 ar_running (L00513): observed -1, expected 0; F0370420
- D05/default seed 41248 unapplied_running (L00432): observed -552, expected 0; E8174
- D05/default seed 41256 unapplied_running (GL-001834): observed -173, expected 0; C-4466
- D05/default seed 41257 unapplied_running (L00782): observed -34, expected 0; E4551
- D05/default seed 41258 ar_running (R1433): observed -1, expected 0; SI-2026-923475
- D05/default seed 41258 unapplied_running (R1238): observed -227031, expected 0; CUST78127
- D05/default seed 41262 ar_running (GL-001158): observed -1, expected 0; F0515687
- D05/default seed 41263 unapplied_running (R5022): observed -91, expected 0; CUST88062
- D05/default seed 41264 unapplied_running (R3651): observed -83, expected 0; C-1145
- D05/default seed 41265 unapplied_running (GL-001966): observed -170, expected 0; C-5923
- D05/default seed 41266 unapplied_running (L00492): observed -2186, expected 0; E7360
- D05/default seed 41267 unapplied_running (L03551): observed -1362, expected 0; E8408
- D05/default seed 41268 unapplied_running (R3548): observed -31589, expected 0; C-4687
- D05/default seed 41270 ar_running (GL-000401): observed -1, expected 0; INV-215118
- D05/default seed 41270 unapplied_running (GL-000443): observed -23, expected 0; CUST74275
- D05/default seed 41277 unapplied_running (L01581): observed -40, expected 0; E3442
- D05/default seed 41277 unapplied_running (L01680): observed -63, expected 0; E3442
- D05/default seed 41277 unapplied_running (L01733): observed -88, expected 0; E3442
- D05/default seed 41282 unapplied_running (GL-003747): observed -56670, expected 0; E8942
- D05/default seed 41283 unapplied_running (L04036): observed -57, expected 0; CUST56709
- D05/default seed 41287 unapplied_running (GL-004422): observed -33477, expected 0; C-5782
- D05/default seed 41287 unapplied_running (GL-004529): observed -16030, expected 0; C-6240
- D05/default seed 41289 unapplied_running (R446): observed -195, expected 0; CUST97557
- D05/default seed 41292 ar_running (L02096): observed -1, expected 0; INV-931351
- D05/default seed 41293 ar_running (GL-003102): observed -1, expected 0; 2503-365156
- D05/default seed 41293 ar_running (GL-003276): observed -1, expected 0; 2503-133260
- D05/default seed 41296 unapplied_running (L03801): observed -60, expected 0; C-9163
- D05/hard seed 41005 ar_running (GL-005749): observed -1, expected 0; INV-064884
- D05/hard seed 41008 unapplied_running (GL-003144): observed -51, expected 0; C-9667
- D05/hard seed 41011 unapplied_running (R3945): observed -229, expected 0; C-9377
- D05/hard seed 41013 ar_running (R2646): observed -1, expected 0; INV-859119
- D05/hard seed 41013 unapplied_running (R2930): observed -28, expected 0; CUST95480
- D05/hard seed 41015 unapplied_running (L05401): observed -98, expected 0; CUST95106
- D05/hard seed 41017 ar_running (L03233): observed -1, expected 0; INV-758326
- D05/hard seed 41018 unapplied_running (L03230): observed -23, expected 0; C-8778
- D05/hard seed 41020 unapplied_running (L01033): observed -303, expected 0; C-0028
- D05/hard seed 41020 unapplied_running (L01160): observed -5, expected 0; C-8284
- D05/hard seed 41024 unapplied_running (R3553): observed -143101, expected 0; E1698
- D05/hard seed 41024 unapplied_running (R3860): observed -188319, expected 0; E1698
- D05/hard seed 41025 unapplied_running (L02152): observed -10190, expected 0; C-6454
- D05/hard seed 41029 unapplied_running (R2704): observed -271, expected 0; CUST08113
- D05/hard seed 41029 unapplied_running (R2832): observed -19, expected 0; CUST09291
- D05/hard seed 41037 ar_running (L03201): observed -1, expected 0; 2611-778760
- D05/hard seed 41037 ar_running (L03244): observed -1, expected 0; 2611-453884
- D05/hard seed 41038 unapplied_running (GL-005437): observed -279331, expected 0; C-0425
- D05/hard seed 41040 ar_running (R5101): observed -1, expected 0; 2609-004130
- D05/hard seed 41045 unapplied_running (R3505): observed -103, expected 0; E2744
- D05/hard seed 41046 unapplied_running (L01489): observed -130, expected 0; E5006
- D05/hard seed 41049 unapplied_running (R3890): observed -315, expected 0; E7530
- D05/hard seed 41050 unapplied_running (L02856): observed -686, expected 0; CUST88801
- D05/hard seed 41052 ar_running (R1027): observed -1, expected 0; SI-2026-798836
- D05/hard seed 41053 unapplied_running (R2367): observed -63, expected 0; C-4903
- D05/hard seed 41061 unapplied_running (L02053): observed -26452, expected 0; CUST15073
- D05/hard seed 41063 ar_running (L01469): observed -1, expected 0; 2609-768605
- D05/hard seed 41065 ar_running (R4601): observed -1, expected 0; F0032065
- D05/hard seed 41073 unapplied_running (GL-001842): observed -420, expected 0; C-0848
- D05/hard seed 41078 unapplied_running (L01768): observed -170902, expected 0; E7114
- D05/hard seed 41079 unapplied_running (L05733): observed -20, expected 0; E5939
- D05/hard seed 41080 unapplied_running (R5253): observed -83, expected 0; C-3829
- D05/hard seed 41088 unapplied_running (GL-001810): observed -246, expected 0; C-6699
- D05/hard seed 41088 unapplied_running (GL-002196): observed -256, expected 0; C-6699
- D05/hard seed 41088 unapplied_running (GL-001984): observed -1, expected 0; C-3111
- D05/hard seed 41091 unapplied_running (GL-003949): observed -57, expected 0; E5263
- D05/hard seed 41092 unapplied_running (L03271): observed -4, expected 0; C-1933
- D05/hard seed 41093 unapplied_running (L02066): observed -2, expected 0; CUST65465
- D05/hard seed 41094 unapplied_running (R5650): observed -4, expected 0; E9227
- D05/hard seed 41096 ar_running (R648): observed -1, expected 0; SI-2026-466918
- D05/hard seed 41097 unapplied_running (R4467): observed -10407, expected 0; CUST02501
- D05/hard seed 41098 ar_running (L04227): observed -1, expected 0; 2612-160441
- D05/hard seed 41098 unapplied_running (L04443): observed -23291, expected 0; C-1225
- D05/hard seed 41099 unapplied_running (L02896): observed -26, expected 0; C-9785
- D05/hard seed 41099 unapplied_running (L03397): observed -9, expected 0; C-3675
- D05/hard seed 41100 ar_running (GL-005821): observed -1, expected 0; 2612-882562
- D05/hard seed 41103 ar_running (R2401): observed -1, expected 0; F0054592
- D05/hard seed 41106 ar_running (L03291): observed -1, expected 0; 2507-119107
- D05/hard seed 41108 unapplied_running (GL-003547): observed -174, expected 0; C-6620
- D05/hard seed 41112 ar_running (R4842): observed -1, expected 0; 2508-594384
- D05/hard seed 41115 ar_running (L03813): observed -1, expected 0; 2507-425960
- D05/hard seed 41118 ar_running (GL-004927): observed -1, expected 0; INV-114883
- D05/hard seed 41118 unapplied_running (GL-005060): observed -34, expected 0; CUST19568
- D05/hard seed 41123 ar_running (R4880): observed -1, expected 0; INV-019033
- D05/hard seed 41124 unapplied_running (L00585): observed -1, expected 0; CUST35077
- D05/hard seed 41128 ar_running (GL-001786): observed -1, expected 0; SI-2026-305268
- D05/hard seed 41134 unapplied_running (GL-005307): observed -201, expected 0; CUST34155
- D05/hard seed 41137 ar_running (R1542): observed -1, expected 0; F0267943
- D05/hard seed 41142 unapplied_running (GL-002585): observed -250, expected 0; C-5710
- D05/hard seed 41150 unapplied_running (L05035): observed -85, expected 0; CUST48458
- D05/hard seed 41151 ar_running (L00532): observed -1, expected 0; INV-263286
- D05/hard seed 41156 ar_running (R5500): observed -1, expected 0; 2508-592873
- D05/hard seed 41164 ar_running (R3355): observed -1, expected 0; 2504-064452
- D05/hard seed 41165 unapplied_running (R3538): observed -228, expected 0; CUST82075
- D05/hard seed 41170 ar_running (R3853): observed -1, expected 0; INV-886051
- D05/hard seed 41170 ar_running (R3783): observed -1, expected 0; INV-044439
- D05/hard seed 41172 unapplied_running (L02902): observed -136, expected 0; E2316
- D05/hard seed 41173 unapplied_running (L05206): observed -69, expected 0; E8466
- D05/hard seed 41174 ar_running (R1947): observed -1, expected 0; 2501-044446
- D05/hard seed 41174 unapplied_running (R1343): observed -104023, expected 0; C-2817
- D05/hard seed 41175 unapplied_running (L05070): observed -213, expected 0; C-7166
- D05/hard seed 41176 unapplied_running (GL-005340): observed -579, expected 0; E1431
- D05/hard seed 41179 ar_running (R5285): observed -1, expected 0; 2502-263509
- D05/hard seed 41185 ar_running (L05076): observed -1, expected 0; SI-2026-814573
- D05/hard seed 41194 ar_running (L05631): observed -1, expected 0; INV-589999
- D05/hard seed 41197 unapplied_running (L04940): observed -5371, expected 0; E9990
- D05/hard seed 41199 unapplied_running (GL-000525): observed -9, expected 0; CUST88252
- D05/hard seed 41200 unapplied_running (R3852): observed -10, expected 0; E9348
- D05/hard seed 41200 unapplied_running (R3947): observed -54, expected 0; E3676
- D05/hard seed 41201 unapplied_running (GL-004366): observed -14, expected 0; E0747
- D05/hard seed 41202 unapplied_running (R731): observed -67, expected 0; E8053
- D05/hard seed 41204 ar_running (R3490): observed -1, expected 0; INV-929188
- D05/hard seed 41204 unapplied_running (R3004): observed -33679, expected 0; C-2446
- D05/hard seed 41208 unapplied_running (R1128): observed -13, expected 0; C-8157
- D05/hard seed 41208 unapplied_running (R1712): observed -7, expected 0; C-8157
- D05/hard seed 41210 unapplied_running (R1520): observed -1, expected 0; E8676
- D05/hard seed 41211 unapplied_running (R1389): observed -1150, expected 0; E7884
- D05/hard seed 41212 ar_running (GL-003946): observed -1, expected 0; 2603-669849
- D05/hard seed 41216 ar_running (R2147): observed -1, expected 0; SI-2025-019680
- D05/hard seed 41216 ar_running (R2145): observed -1, expected 0; SI-2025-363180
- D05/hard seed 41216 unapplied_running (R2104): observed -66, expected 0; E3666
- D05/hard seed 41218 unapplied_running (R2840): observed -84, expected 0; C-6028
- D05/hard seed 41224 unapplied_running (GL-001578): observed -143, expected 0; E2277
- D05/hard seed 41232 unapplied_running (R5419): observed -198, expected 0; E5211
- D05/hard seed 41233 unapplied_running (GL-004739): observed -82, expected 0; C-3362
- D05/hard seed 41234 ar_running (GL-002416): observed -1, expected 0; SI-2025-000350
- D05/hard seed 41235 unapplied_running (GL-002070): observed -17333, expected 0; CUST16801
- D05/hard seed 41236 unapplied_running (GL-003576): observed -216, expected 0; CUST89445
- D05/hard seed 41240 ar_running (GL-002596): observed -1, expected 0; F0438164
- D05/hard seed 41243 unapplied_running (R2468): observed -38, expected 0; E7080
- D05/hard seed 41244 unapplied_running (L01940): observed -194678, expected 0; E7439
- D05/hard seed 41249 ar_running (R4435): observed -1, expected 0; SI-2026-018892
- D05/hard seed 41249 unapplied_running (R4476): observed -16, expected 0; E0639
- D05/hard seed 41251 ar_running (GL-004129): observed -1, expected 0; 2602-317250
- D05/hard seed 41253 ar_running (L01044): observed -1, expected 0; 2502-305985
- D05/hard seed 41253 ar_running (L00832): observed -1, expected 0; 2502-633501
- D05/hard seed 41262 ar_running (GL-003336): observed -1, expected 0; INV-882581
- D05/hard seed 41266 ar_running (GL-002148): observed -1, expected 0; F0818242
- D05/hard seed 41266 ar_running (GL-001994): observed -1, expected 0; F0254037
- D05/hard seed 41267 unapplied_running (GL-004356): observed -164, expected 0; E8308
- D05/hard seed 41276 unapplied_running (GL-004211): observed -32, expected 0; CUST98146
- D05/hard seed 41278 ar_running (GL-000895): observed -1, expected 0; SI-2025-730616
- D05/hard seed 41279 ar_running (L01297): observed -1, expected 0; F0674420
- D05/hard seed 41279 unapplied_running (L01357): observed -154, expected 0; C-1009
- D05/hard seed 41282 ar_running (R4406): observed -1, expected 0; F0128741
- D05/hard seed 41284 unapplied_running (R3587): observed -108, expected 0; C-7663
- D05/hard seed 41286 unapplied_running (GL-002193): observed -40, expected 0; C-7586
- D05/hard seed 41287 unapplied_running (GL-003483): observed -259, expected 0; CUST73028
- D05/hard seed 41288 unapplied_running (L02451): observed -14938, expected 0; E7606
- D05/hard seed 41289 unapplied_running (L03602): observed -1092, expected 0; CUST97015
- D05/hard seed 41289 unapplied_running (L03815): observed -251, expected 0; CUST84414
- D05/hard seed 41290 ar_running (R5259): observed -1, expected 0; F0617458
- D05/hard seed 41291 ar_running (R5756): observed -1, expected 0; 2604-148765
- D05/hard seed 41291 unapplied_running (R5269): observed -78791, expected 0; E8132
- D05/hard seed 41292 ar_running (GL-005681): observed -1, expected 0; INV-315947
- D05/hard seed 41292 unapplied_running (GL-005406): observed -13, expected 0; E5289
- D05/hard seed 41295 ar_running (R3380): observed -1, expected 0; F0203109
- D05/hard seed 41298 unapplied_running (R3356): observed -4, expected 0; C-7601
- D05/hard seed 41299 ar_running (R3080): observed -1, expected 0; SI-2025-343694
- D05/hard seed 41299 unapplied_running (R2644): observed -27, expected 0; E7083

First unexplained violation of each check outside clean scenarios:
- baseline/default seed 41005 ar_running (L02591): observed -1, expected 0; 2610-365414
- baseline/default seed 41012 unapplied_running (L01019): observed -73138, expected 0; CUST92808
- baseline/hard seed 41003 unapplied_running (R1333): observed -94142, expected 0; C-9211
- baseline/hard seed 41012 ar_running (L04872): observed -1, expected 0; F0023605
- D06/default seed 41001 ar_running (R2582): observed -1, expected 0; F0305356
- D06/default seed 41001 unapplied_running (R2778): observed -103426, expected 0; C-5947
- D06/hard seed 41003 unapplied_running (L05977): observed -21074, expected 0; CUST06473
- D06/hard seed 41045 ar_running (GL-005132): observed -1, expected 0; SI-2026-846198
- D07/default seed 41001 ar_running (R2582): observed -1, expected 0; F0305356
- D07/default seed 41001 unapplied_running (R2778): observed -103426, expected 0; C-5947
- D07/hard seed 41003 unapplied_running (L05977): observed -21074, expected 0; CUST06473
- D07/hard seed 41045 ar_running (GL-005132): observed -1, expected 0; SI-2026-846198
- D08/default seed 41001 ar_running (R2582): observed -1, expected 0; F0305356
- D08/default seed 41001 unapplied_running (R2778): observed -103426, expected 0; C-5947
- D08/hard seed 41003 unapplied_running (L05977): observed -21074, expected 0; CUST06473
- D08/hard seed 41045 ar_running (GL-005132): observed -1, expected 0; SI-2026-846198
- D09/default seed 41010 ar_running (GL-004502): observed -1, expected 0; INV-463338
- D09/default seed 41010 unapplied_running (GL-004469): observed -862, expected 0; C-1748
- D09/hard seed 41000 unapplied_running (L04377): observed -7, expected 0; CUST00285
- D09/hard seed 41005 ar_running (L05113): observed -1, expected 0; SI-2026-837760
- D10/default seed 41000 unapplied_running (L04767): observed -2, expected 0; E3927
- D10/default seed 41023 ar_running (R748): observed -1, expected 0; INV-743893
- D10/hard seed 41001 unapplied_running (R766): observed -54, expected 0; E7663
- D10/hard seed 41004 ar_running (GL-002153): observed -1, expected 0; 2611-127037
- D11/default seed 41000 ar_running (L01797): observed -1, expected 0; 2609-934689
- D11/default seed 41002 unapplied_running (GL-000951): observed -139083, expected 0; CUST19275
- D11/hard seed 41000 unapplied_running (L05309): observed -124, expected 0; CUST69014
- D11/hard seed 41005 ar_running (R3913): observed -1, expected 0; 2507-597948
- D12/default seed 41000 unapplied_running (R2538): observed -142, expected 0; CUST35030
- D12/default seed 41005 ar_running (R768): observed -1, expected 0; SI-2025-376606
- D12/hard seed 41000 unapplied_running (GL-000987): observed -35, expected 0; E7690
- D12/hard seed 41034 ar_running (GL-002580): observed -1, expected 0; SI-2026-071363
- D13/default seed 41000 unapplied_running (R2538): observed -142, expected 0; CUST35030
- D13/default seed 41005 ar_running (R768): observed -1, expected 0; SI-2025-376606
- D13/hard seed 41000 unapplied_running (GL-000987): observed -35, expected 0; E7690
- D13/hard seed 41034 ar_running (GL-002580): observed -1, expected 0; SI-2026-071363
- D14/default seed 41001 unapplied_running (GL-003565): observed -328, expected 0; C-7484
- D14/default seed 41020 ar_running (GL-003239): observed -1, expected 0; F0121313
- D14/hard seed 41000 unapplied_running (L04702): observed -4, expected 0; E6613
- D14/hard seed 41002 ar_running (R2696): observed -1, expected 0; INV-526580
- D15/default seed 41001 unapplied_running (GL-003565): observed -328, expected 0; C-7484
- D15/default seed 41020 ar_running (GL-003239): observed -1, expected 0; F0121313
- D15/hard seed 41000 unapplied_running (L04702): observed -4, expected 0; E6613
- D15/hard seed 41002 ar_running (R2696): observed -1, expected 0; INV-526580
- D16/default seed 41001 unapplied_running (GL-003068): observed -5493, expected 0; C-9026
- D16/default seed 41002 ar_running (R3716): observed -1, expected 0; INV-447954
- D16/hard seed 41001 ar_running (L03959): observed -1, expected 0; F0896281
- D16/hard seed 41022 unapplied_running (GL-004514): observed -39, expected 0; CUST71742
- D17/default seed 41001 unapplied_running (GL-003068): observed -5493, expected 0; C-9026
- D17/default seed 41002 ar_running (R3716): observed -1, expected 0; INV-447954
- D17/hard seed 41001 ar_running (L03959): observed -1, expected 0; F0896281
- D17/hard seed 41022 unapplied_running (GL-004514): observed -39, expected 0; CUST71742
- D18/default seed 41001 unapplied_running (GL-003068): observed -5493, expected 0; C-9026
- D18/default seed 41002 ar_running (R3716): observed -1, expected 0; INV-447954
- D18/hard seed 41001 ar_running (L03959): observed -1, expected 0; F0896281
- D18/hard seed 41022 unapplied_running (GL-004514): observed -39, expected 0; CUST71742
- D19/default seed 41001 unapplied_running (GL-000925): observed -23, expected 0; E3462
- D19/default seed 41012 ar_running (L02181): observed -1, expected 0; 2602-726143
- D19/hard seed 41000 unapplied_running (R3497): observed -355, expected 0; CUST75627
- D19/hard seed 41020 ar_running (GL-002714): observed -1, expected 0; SI-2025-056047
- D20/default seed 41001 unapplied_running (GL-000925): observed -23, expected 0; E3462
- D20/default seed 41012 ar_running (L02181): observed -1, expected 0; 2602-726143
- D20/hard seed 41000 unapplied_running (R3497): observed -355, expected 0; CUST75627
- D20/hard seed 41020 ar_running (GL-002714): observed -1, expected 0; SI-2025-056047

2026-11-22 03:55 codex1 — X3 extreme configurations. `env -u AUDITENV_SECRET uv run python -m night.r21.extreme_configs` → exit 0, 19.223 s.

Assumptions: three fresh seeds 44000–44002, mixed counts distributed as evenly as possible across the four issue types, two findings per interacting scenario, documented maximum 12 for every type, and permutation seed 37 versus null. The factorial uses one allocation error so all three allocation settings are exercised. All 300 accepted episodes verified and returned exactly the requested count. All 72 rejected configurations reported `ValueError: at most 12 issues per episode`. No silent count mismatch, unexpected exception, or action-budget overrun. Max 72 actions. Both reconciliation and empty submissions were replayed in closed mode and scored independently. Per-config results follow.

- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 0}, "n_invoices": 10} — valid: 0 issues; 18 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "default", "errors": {"payment_allocation": 0}, "n_invoices": 10} — valid: 0 issues; 18 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "default", "errors": {"fx_error": 0}, "n_invoices": 10} — valid: 0 issues; 18 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "default", "errors": {"period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 18 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 0, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 18 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 1}, "n_invoices": 10} — valid: 1 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"payment_allocation": 1}, "n_invoices": 10} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"fx_error": 1}, "n_invoices": 10} — valid: 1 issues; 17 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"period_cutoff": 1}, "n_invoices": 10} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 1, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 1 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 12}, "n_invoices": 10} — valid: 12 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"payment_allocation": 12}, "n_invoices": 10} — valid: 12 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"fx_error": 12}, "n_invoices": 10} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"period_cutoff": 12}, "n_invoices": 10} — valid: 12 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 10} — valid: 12 issues; 25 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"payment_allocation": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"fx_error": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"period_cutoff": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 5, "fx_error": 5, "payment_allocation": 5, "period_cutoff": 5}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"payment_allocation": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"fx_error": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"period_cutoff": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 13, "fx_error": 12, "payment_allocation": 13, "period_cutoff": 12}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "interacting": {"I1": 1, "I2": 0}, "n_invoices": 10} — valid: 2 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "interacting": {"I1": 0, "I2": 1}, "n_invoices": 10} — valid: 2 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "interacting": {"I1": 1, "I2": 1}, "n_invoices": 10} — valid: 4 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "interacting": {"I1": 6, "I2": 0}, "n_invoices": 10} — valid: 12 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "interacting": {"I1": 0, "I2": 6}, "n_invoices": 10} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "interacting": {"I1": 3, "I2": 3}, "n_invoices": 10} — valid: 12 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "interacting": {"I1": 7, "I2": 0}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "interacting": {"I1": 0, "I2": 7}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 100} — valid: 12 issues; 28 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"duplicate_invoice": 12}, "n_invoices": 100} — valid: 12 issues; 47 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"payment_allocation": 12}, "n_invoices": 100} — valid: 12 issues; 23 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"fx_error": 12}, "n_invoices": 100} — valid: 12 issues; 24 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "default", "errors": {"period_cutoff": 12}, "n_invoices": 100} — valid: 12 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 0}, "n_invoices": 10} — valid: 0 issues; 43 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "hard", "errors": {"payment_allocation": 0}, "n_invoices": 10} — valid: 0 issues; 43 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "hard", "errors": {"fx_error": 0}, "n_invoices": 10} — valid: 0 issues; 43 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "hard", "errors": {"period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 43 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 0, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 43 actions; reconcile F1=1.0; empty F1=1.0
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 1}, "n_invoices": 10} — valid: 1 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"payment_allocation": 1}, "n_invoices": 10} — valid: 1 issues; 46 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"fx_error": 1}, "n_invoices": 10} — valid: 1 issues; 35 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"period_cutoff": 1}, "n_invoices": 10} — valid: 1 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 1, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 1 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 12}, "n_invoices": 10} — valid: 12 issues; 61 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"payment_allocation": 12}, "n_invoices": 10} — valid: 12 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"fx_error": 12}, "n_invoices": 10} — valid: 12 issues; 44 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"period_cutoff": 12}, "n_invoices": 10} — valid: 12 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 10} — valid: 12 issues; 48 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"payment_allocation": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"fx_error": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"period_cutoff": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 5, "fx_error": 5, "payment_allocation": 5, "period_cutoff": 5}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"payment_allocation": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"fx_error": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"period_cutoff": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 13, "fx_error": 12, "payment_allocation": 13, "period_cutoff": 12}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "interacting": {"I1": 1, "I2": 0}, "n_invoices": 10} — valid: 2 issues; 46 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 1}, "n_invoices": 10} — valid: 2 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "interacting": {"I1": 1, "I2": 1}, "n_invoices": 10} — valid: 4 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "interacting": {"I1": 6, "I2": 0}, "n_invoices": 10} — valid: 12 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 6}, "n_invoices": 10} — valid: 12 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "interacting": {"I1": 3, "I2": 3}, "n_invoices": 10} — valid: 12 issues; 41 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "interacting": {"I1": 7, "I2": 0}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 7}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 100} — valid: 12 issues; 54 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"duplicate_invoice": 12}, "n_invoices": 100} — valid: 12 issues; 63 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"payment_allocation": 12}, "n_invoices": 100} — valid: 12 issues; 44 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"fx_error": 12}, "n_invoices": 100} — valid: 12 issues; 44 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"difficulty": "hard", "errors": {"period_cutoff": 12}, "n_invoices": 100} — valid: 12 issues; 48 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 46 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 46 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 17 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 17 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 17 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 17 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 35 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 35 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 44 actions; reconcile F1=1.0; empty F1=0.0
- seed 44000 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 44 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 0}, "n_invoices": 10} — valid: 0 issues; 19 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "default", "errors": {"payment_allocation": 0}, "n_invoices": 10} — valid: 0 issues; 19 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "default", "errors": {"fx_error": 0}, "n_invoices": 10} — valid: 0 issues; 19 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "default", "errors": {"period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 19 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 0, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 19 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 1}, "n_invoices": 10} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"payment_allocation": 1}, "n_invoices": 10} — valid: 1 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"fx_error": 1}, "n_invoices": 10} — valid: 1 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"period_cutoff": 1}, "n_invoices": 10} — valid: 1 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 1, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 12}, "n_invoices": 10} — valid: 12 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"payment_allocation": 12}, "n_invoices": 10} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"fx_error": 12}, "n_invoices": 10} — valid: 12 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"period_cutoff": 12}, "n_invoices": 10} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 10} — valid: 12 issues; 24 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"payment_allocation": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"fx_error": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"period_cutoff": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 5, "fx_error": 5, "payment_allocation": 5, "period_cutoff": 5}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"payment_allocation": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"fx_error": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"period_cutoff": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 13, "fx_error": 12, "payment_allocation": 13, "period_cutoff": 12}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "interacting": {"I1": 1, "I2": 0}, "n_invoices": 10} — valid: 2 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "interacting": {"I1": 0, "I2": 1}, "n_invoices": 10} — valid: 2 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "interacting": {"I1": 1, "I2": 1}, "n_invoices": 10} — valid: 4 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "interacting": {"I1": 6, "I2": 0}, "n_invoices": 10} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "interacting": {"I1": 0, "I2": 6}, "n_invoices": 10} — valid: 12 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "interacting": {"I1": 3, "I2": 3}, "n_invoices": 10} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "interacting": {"I1": 7, "I2": 0}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "interacting": {"I1": 0, "I2": 7}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 100} — valid: 12 issues; 27 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"duplicate_invoice": 12}, "n_invoices": 100} — valid: 12 issues; 46 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"payment_allocation": 12}, "n_invoices": 100} — valid: 12 issues; 24 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"fx_error": 12}, "n_invoices": 100} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "default", "errors": {"period_cutoff": 12}, "n_invoices": 100} — valid: 12 issues; 23 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 0}, "n_invoices": 10} — valid: 0 issues; 40 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "hard", "errors": {"payment_allocation": 0}, "n_invoices": 10} — valid: 0 issues; 40 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "hard", "errors": {"fx_error": 0}, "n_invoices": 10} — valid: 0 issues; 40 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "hard", "errors": {"period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 40 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 0, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 40 actions; reconcile F1=1.0; empty F1=1.0
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 1}, "n_invoices": 10} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"payment_allocation": 1}, "n_invoices": 10} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"fx_error": 1}, "n_invoices": 10} — valid: 1 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"period_cutoff": 1}, "n_invoices": 10} — valid: 1 issues; 36 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 1, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 12}, "n_invoices": 10} — valid: 12 issues; 68 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"payment_allocation": 12}, "n_invoices": 10} — valid: 12 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"fx_error": 12}, "n_invoices": 10} — valid: 12 issues; 36 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"period_cutoff": 12}, "n_invoices": 10} — valid: 12 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 10} — valid: 12 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"payment_allocation": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"fx_error": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"period_cutoff": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 5, "fx_error": 5, "payment_allocation": 5, "period_cutoff": 5}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"payment_allocation": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"fx_error": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"period_cutoff": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 13, "fx_error": 12, "payment_allocation": 13, "period_cutoff": 12}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "interacting": {"I1": 1, "I2": 0}, "n_invoices": 10} — valid: 2 issues; 41 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 1}, "n_invoices": 10} — valid: 2 issues; 44 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "interacting": {"I1": 1, "I2": 1}, "n_invoices": 10} — valid: 4 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "interacting": {"I1": 6, "I2": 0}, "n_invoices": 10} — valid: 12 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 6}, "n_invoices": 10} — valid: 12 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "interacting": {"I1": 3, "I2": 3}, "n_invoices": 10} — valid: 12 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "interacting": {"I1": 7, "I2": 0}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 7}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 100} — valid: 12 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"duplicate_invoice": 12}, "n_invoices": 100} — valid: 12 issues; 72 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"payment_allocation": 12}, "n_invoices": 100} — valid: 12 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"fx_error": 12}, "n_invoices": 100} — valid: 12 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"difficulty": "hard", "errors": {"period_cutoff": 12}, "n_invoices": 100} — valid: 12 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 34 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 34 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 33 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 33 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 45 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44001 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 0}, "n_invoices": 10} — valid: 0 issues; 23 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "default", "errors": {"payment_allocation": 0}, "n_invoices": 10} — valid: 0 issues; 23 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "default", "errors": {"fx_error": 0}, "n_invoices": 10} — valid: 0 issues; 23 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "default", "errors": {"period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 23 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 0, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 23 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 1}, "n_invoices": 10} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"payment_allocation": 1}, "n_invoices": 10} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"fx_error": 1}, "n_invoices": 10} — valid: 1 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"period_cutoff": 1}, "n_invoices": 10} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 1, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 12}, "n_invoices": 10} — valid: 12 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"payment_allocation": 12}, "n_invoices": 10} — valid: 12 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"fx_error": 12}, "n_invoices": 10} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"period_cutoff": 12}, "n_invoices": 10} — valid: 12 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 10} — valid: 12 issues; 26 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"payment_allocation": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"fx_error": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"period_cutoff": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 5, "fx_error": 5, "payment_allocation": 5, "period_cutoff": 5}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"payment_allocation": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"fx_error": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"period_cutoff": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 13, "fx_error": 12, "payment_allocation": 13, "period_cutoff": 12}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "interacting": {"I1": 1, "I2": 0}, "n_invoices": 10} — valid: 2 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "interacting": {"I1": 0, "I2": 1}, "n_invoices": 10} — valid: 2 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "interacting": {"I1": 1, "I2": 1}, "n_invoices": 10} — valid: 4 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "interacting": {"I1": 6, "I2": 0}, "n_invoices": 10} — valid: 12 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "interacting": {"I1": 0, "I2": 6}, "n_invoices": 10} — valid: 12 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "interacting": {"I1": 3, "I2": 3}, "n_invoices": 10} — valid: 12 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "interacting": {"I1": 7, "I2": 0}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "interacting": {"I1": 0, "I2": 7}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 100} — valid: 12 issues; 28 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"duplicate_invoice": 12}, "n_invoices": 100} — valid: 12 issues; 49 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"payment_allocation": 12}, "n_invoices": 100} — valid: 12 issues; 22 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"fx_error": 12}, "n_invoices": 100} — valid: 12 issues; 27 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "default", "errors": {"period_cutoff": 12}, "n_invoices": 100} — valid: 12 issues; 26 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 0}, "n_invoices": 10} — valid: 0 issues; 41 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "hard", "errors": {"payment_allocation": 0}, "n_invoices": 10} — valid: 0 issues; 41 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "hard", "errors": {"fx_error": 0}, "n_invoices": 10} — valid: 0 issues; 41 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "hard", "errors": {"period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 41 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 0, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 0 issues; 41 actions; reconcile F1=1.0; empty F1=1.0
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 1}, "n_invoices": 10} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"payment_allocation": 1}, "n_invoices": 10} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"fx_error": 1}, "n_invoices": 10} — valid: 1 issues; 44 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"period_cutoff": 1}, "n_invoices": 10} — valid: 1 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 1, "fx_error": 0, "payment_allocation": 0, "period_cutoff": 0}, "n_invoices": 10} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 12}, "n_invoices": 10} — valid: 12 issues; 58 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"payment_allocation": 12}, "n_invoices": 10} — valid: 12 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"fx_error": 12}, "n_invoices": 10} — valid: 12 issues; 43 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"period_cutoff": 12}, "n_invoices": 10} — valid: 12 issues; 41 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 10} — valid: 12 issues; 50 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"payment_allocation": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"fx_error": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"period_cutoff": 20}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 5, "fx_error": 5, "payment_allocation": 5, "period_cutoff": 5}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"payment_allocation": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"fx_error": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"period_cutoff": 50}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 13, "fx_error": 12, "payment_allocation": 13, "period_cutoff": 12}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "interacting": {"I1": 1, "I2": 0}, "n_invoices": 10} — valid: 2 issues; 44 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 1}, "n_invoices": 10} — valid: 2 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "interacting": {"I1": 1, "I2": 1}, "n_invoices": 10} — valid: 4 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "interacting": {"I1": 6, "I2": 0}, "n_invoices": 10} — valid: 12 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 6}, "n_invoices": 10} — valid: 12 issues; 36 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "interacting": {"I1": 3, "I2": 3}, "n_invoices": 10} — valid: 12 issues; 41 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "interacting": {"I1": 7, "I2": 0}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "interacting": {"I1": 0, "I2": 7}, "n_invoices": 10} — rejected: ValueError: at most 12 issues per episode
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 3, "fx_error": 3, "payment_allocation": 3, "period_cutoff": 3}, "n_invoices": 100} — valid: 12 issues; 47 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"duplicate_invoice": 12}, "n_invoices": 100} — valid: 12 issues; 69 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"payment_allocation": 12}, "n_invoices": 100} — valid: 12 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"fx_error": 12}, "n_invoices": 100} — valid: 12 issues; 48 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"difficulty": "hard", "errors": {"period_cutoff": 12}, "n_invoices": 100} — valid: 12 issues; 51 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 14 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 34 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 34 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 21 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 37 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 35 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 35 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 46 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": null, "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 46 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 16 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 38 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 36 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 36 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "missing", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 18 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 40 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 19 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": false, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 39 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 15 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "default", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 15 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 34 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "hard", "distractors": false, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 34 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "default", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 20 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": null} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0
- seed 44002 {"allocation": "partial", "difficulty": "hard", "distractors": true, "ensure_distractors": true, "errors": {"payment_allocation": 1}, "n_invoices": 10, "transform_seed": 37} — valid: 1 issues; 42 actions; reconcile F1=1.0; empty F1=0.0

Outcomes: {'valid': 300, 'rejected': 72, 'failure': 0}. Total: 372.

`env -u AUDITENV_SECRET uv run python -m auditenv.check` → exit 0, 71.45 s wall time, ALL CHECKS PASSED in 71.4 s
2026-11-22 03:55 codex2 — Y3: README first-read review at 7444579. `git clone /Users/caliskan/Projects/genesis /tmp/r21-codex2/clone` and `git -C /tmp/r21-codex2/clone checkout --detach origin/night/2026-11-22-r21` both exited 0 (2.0 s together).

Read README.md lines 1–466 top to bottom: introduction, Quick start, Container, Isolated baseline run, For the jury, Errors, Reward, Results, What the check does, Using the environment and all subsections, Other commands, Repository layout, Honest limitations, License, and Contributing. Assumption for the ten-minute review: prioritize the jury's runnable route and validate maintenance examples selectively. Docker was absent locally, so those commands were checked against Dockerfile and CI. The clone used local repository access as assigned.

From the fresh clone, `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r21-codex2/readme/auditenv-metrics.json` exited 0 in 92.72 s: `[PASS] unit tests — 563 tests, 0 failures, 0 errors` and `ALL CHECKS PASSED in 92.5 s`. The four jury modules exited 0 in 4.53 s (73 tests, OK), `uv run python -m auditenv.jury_run` exited 0 in 2.99 s (20 scenarios; reconcile F1 1.000), and `uv run python -m auditenv.demo` exited 0 in 0.21 s (closed reward 0.958, four TPs). All three Python examples, both trial policy commands, the hard-train export, the 674-line trajectory regeneration and byte comparison, the out-of-process smoke, generated and disk verifiers, doc sync, analysis, golden hashes, chart, and Make preview passed. Outputs generated during the review went to worker scratch or the scratch clone.

1. **Lines 12 and 29–46, offline prerequisites.** A reader can see “Без сети” before learning that cloning, first-time Python installation and an uncached Docker build may need a network. The pinned image is a build input, and `--network none` applies to the run. Proposed text: “Once this checkout and Python 3.11 are available, the check runs without network access or third-party Python dependencies. A first `uv` run may download Python. The Docker build may pull its pinned base image; the built image runs the check offline with `--network none`.”
2. **Lines 59–72, jury path placement.** The first two optional Docker flows precede the jury entry point, while a Docker-free full run took 92.72 s and the standalone demo 0.21 s. Proposed lead sentence in Quick start: “For the shortest review, run `uv run python -m auditenv.demo`, then the full check below. To connect the official harness, start at [For the jury](#for-the-jury). Docker is optional.”
3. **Lines 30, 113–124 and 378–403, public reproducibility.** The check strips `AUDITENV_SECRET` only for its unit test gate, and a previously exported key changes other runs and generated files. Proposed text: “For the published metrics and byte-identical public exports, start these commands with `AUDITENV_SECRET` unset (for example, `env -u AUDITENV_SECRET uv run python -m auditenv.check`). Set a custom key only in the grader process.”
4. **Lines 81, 147–150 and 332–333, policy process and adapter location.** These read as though all four baselines run through worker processes. `auditenv.jury_run.play` runs the oracle in the grader, and `JuryPolicy` is defined in `auditenv.policy_worker`. Proposed text: “The jury runner exercises four baselines. It launches random explorer, reconcile and flag-all as separate policy processes using `auditenv.policy_worker.JuryPolicy`; the oracle runs in the grader.”
5. **Lines 108–111, 173 and 272, reward visibility.** The early reward summary describes the grading rule before distinguishing the closed return. Proposed text: “The grader uses this score on the terminal step. Train mode returns the terminal score; closed mode returns 0.0 to the policy on every step and keeps the actual score in the grader log.”
6. **Lines 124 and 127–150, which command backs the sweep.** “Seed sweep over 3 000 episodes” appears before the full-check gates, whose data verifier covers 200 episodes and is a different workload. Proposed text: “Separate from the full check, `uv run python -m auditenv.fuzz --seeds 0-999` checked 3,000 companies with zero problems. See DESIGN §9.”
7. **Lines 173–177 and 307–321, config discovery.** The first list of keys leaves out the two jury options used later. Proposed text after `difficulty`: “`allocation` (`partial`, `missing` or null) selects the allocation-injection variant. `ensure_distractors` (bool) adds split payments and refunded overpayments when suitable receipts exist. See CONTRACT §4 for defaults.”
8. **Lines 197–205 and 397–399, copy-paste side effects.** The first regeneration command writes the tracked root trajectory and the later three export commands replace committed split directories. For a read-only comparison, the fresh clone reproduced all 674 trajectory lines byte for byte in scratch. Proposed text: “To verify without changing the checkout, regenerate the trajectory to a temporary path and compare it with `cmp trajectories.jsonl <temporary path>`. The export commands below replace the specified split directories; use temporary output paths for a reproduction check.”
9. **Lines 272–274, reset and step tuple shapes.** The first observation is listed in the `step` row. Proposed replacement: “`reset` returns `(first_observation, info)`, where `first_observation` has `task`, `manifest`, `policy` and `remaining_steps`. `step` returns `(observation, reward, terminated, truncated, info)`; the step observation has `result`, `error` and `remaining_steps`.”
10. **Lines 93 and 299, cutoff amount.** Line 299 says “AR debit posted out of period”, whereas the posted debit is in the current period and the invoice issue date is outside it. Proposed table cell: “AR debit posted inside the audited period for an invoice issued outside it.”
11. **Line 311, clean scenario denominators and evidence.** Reading the last `199/200` as applying to both difficulties is easy. A public-record D01 probe on each difficulty at seeds 0–199 reproduced 200/200 split, refund, equal-total and unidentified-receipt cases in each difficulty, and foreign documents in 199/200 default and 200/200 hard. The Block 2 unit suite checks the scenario properties on seeds 900–903. Proposed text: “D01–D05 share these settings. Reproduce the clean scenario assertions with `uv run python -m unittest tests.test_judge_scenarios.JudgeScenariosTest.test_clean_scenarios_hold_the_legitimate_lookalikes`. In a separate public sweep on seeds 0–199, foreign-currency documents appeared in 199/200 default and 200/200 hard companies.”
12. **Lines 346–347, timing claim.** The fresh-clone run alongside the full check reported reconcile at max 0.051 s, and the combined-load Y2 run observed a maximum of 54.050 s. The fixed “under 0.05 s” is workload-dependent. Proposed text: “The jury runner prints mean and maximum wall time per policy, including process startup. The official check requires all episodes in this replay to finish within the 60-second limit.”
13. **Lines 355–365, closed server quick start.** With `GRADER_KEY` absent, the exact assignment in line 357 aborts in Bash with `/bin/bash: GRADER_KEY: Set GRADER_KEY in the organiser shell` before the new default-key server can run. Proposed first command: `uv run python -m auditenv.server --episodes hidden.json --grader-log grader.jsonl`. Follow it with: “The server creates or uses the grader-only key file by default. For a custom key, set `AUDITENV_SECRET` in the organiser's environment. To reproduce a deliberately public queue, unset `AUDITENV_SECRET` and add `--public`.”
14. **Lines 390–391 and 405, chart input dependency.** The chart command looks self-contained and reads whatever is at `/tmp/auditenv-metrics.json`. It succeeded here with an older file already present (00:08 local); on a machine without the earlier command's output the input is missing. Proposed text: “After the `auditenv.check --json` command above, pass its output explicitly: `uv run python scripts/chart.py --json /tmp/auditenv-metrics.json`.”
2026-11-22 03:53 gemini1a — G2 complete: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 69000` (exit 0, wall time 177.8 s / 2:57.86): config sweep, cases 69000-71999: 3000 random configs (1254 hard) in 177.8 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 56; FUZZ PASSED. Max steps: 56. Next: G3. Assumptions: none.

2026-11-22 03:54 gemini1a — G3 complete: `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 3000-3999` (exit 0, wall time 29.9 s): 3000/3000 episodes valid; episodes with problems: 0. All assigned tasks (G1, G2, G3) complete. Next: check for any new tasks or idle. Assumptions: none.
2026-11-22 03:54 gemini1b — G6 config sweep on cases 72000-74999: 3000 random configs (1155 hard) in 148.9 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 57; FUZZ PASSED (wall time 148.9 s). Tasks G4, G5, G6 all complete.
2026-11-22 03:46 gemini2a — G7: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 37000-37299` exited 0 (wall time 199s, 12,600 episodes checked across 42 configs).
  totals: a_pay_before_inv=0, a_ref_unknown=0, a_due_before_issue=0, b_cn_before_booking=0, b_cn_orphan=0, b_cn_not_full=0, b_reissue_before_orig=0, c_neg_credit=0, d_ledger_out_period=0, d_cutoff_item=3044, e_fx_missing=0, f_inv_booked_before_issue=2553, f_pay_posted_before_doc=0, f_ar_before_booking=25, f_inv_not_booked=0, f_pay_not_posted=0, f_overallocated=0, f_pay_entity=0, f_fx_posted=5023, c_tie=3
  unexplained violations: 25 (0 in clean configs)
  Next: G8.
2026-11-22 03:51 gemini2a — G8: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 37300-37599` exited 0 (wall time 233s, 12,600 episodes checked across 42 configs).
  totals: a_pay_before_inv=0, a_ref_unknown=0, a_due_before_issue=0, b_cn_before_booking=0, b_cn_orphan=0, b_cn_not_full=0, b_reissue_before_orig=0, c_neg_credit=0, d_ledger_out_period=0, d_cutoff_item=3100, e_fx_missing=0, f_inv_booked_before_issue=2625, f_pay_posted_before_doc=0, f_ar_before_booking=16, f_inv_not_booked=0, f_pay_not_posted=0, f_overallocated=0, f_pay_entity=0, f_fx_posted=5069, c_tie=0
  unexplained violations: 16 (0 in clean configs)
  Next: G9.
2026-11-22 03:53 gemini2a — G9: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/policy_text.py --seeds 38000-38199` exited 0 (wall time 99s).
  Audited 8400 episodes across 42 configurations; 33113438 checks, 0 unexpected failures.
  All gemini2a tasks (G7, G8, G9) complete.
2026-11-22 03:55 gemini2b — G12 complete: ran `scripts/shortcut_miner.py --seeds 5000-5999 --report-only` (default, 32.7s, exit 0) and with `--hard` (42.1s, exit 0).
Default mode: 16 flagged values (precision > 0.5):
## Max precision per issue type (default)
| type | affected max P | evidence max P | flagged (aff/ev) |
|---|---|---|---|
| duplicate_invoice | 0.997 | 0.997 | 2/2 |
| payment_allocation | 0.981 | 0.981 | 8/1 |
| fx_error | 0.714 | 0.320 | 3/0 |
| period_cutoff | 0.460 | 0.460 | 0/0 |
All 16 flagged values are consistent with docs/DESIGN.md §10 (e.g., duplicate count=2 at 0.997, 2900 amount_count>=4 at 0.981, 2900 end-0 at 0.804, 7900 end-0 at 0.577, fx_error end-0 at 0.714).

Hard mode: 13 flagged values (precision > 0.5):
## Max precision per issue type (hard)
| type | affected max P | evidence max P | flagged (aff/ev) |
|---|---|---|---|
| duplicate_invoice | 0.404 | 0.404 | 0/0 |
| payment_allocation | 1.000 | 0.840 | 9/2 |
| fx_error | 0.668 | 0.303 | 2/0 |
| period_cutoff | 0.454 | 0.454 | 0/0 |
Values with precision > 0.5 called out:
- `ledger | amount_digits@acct2900 | 10`: precision 1.000 (support 32, pos 32) for affected and 0.812 (support 32, pos 26) for evidence. This discrete 10-digit bucket (amounts >= $10,000,000 minor units) has support 32 on seeds 5000-5999, which exceeds the miner support threshold (>= 30). docs/DESIGN.md §10 noted "11 in hard mode" on seeds 0-999 (where this 10-digit bucket fell below 30 support) and noted "a large 2900 amount at payment_allocation (0.75-0.77)".
All other 11 values match the documented hard-mode cues in DESIGN §10 (2900 amount_count>=4 at 0.840, 2900 end-0 at 0.765, 2900 9-digits at 0.730, 2900 6-digits at 0.562, fx_error 2900 end-0 at 0.668, fx_error 7900 end-0 at 0.551).
All tasks for gemini2b in Round 21 finished.
2026-11-22 03:46 gemini3b — G18 complete: ran `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r21-gemini3b/c.json` (exit 0, ALL CHECKS PASSED in 137.7 s; 563 unit tests, 200/200 verifier, 20/20 paired, 50/50 hard verifier, 20/20 hard paired) then `uv run python scripts/sync_docs.py --check --json /tmp/r21-gemini3b/c.json` (exit 0, verbatim output: "All documentation tables match measured data.", zero drift). All gemini3b tasks (G16, G17, G18) completed.
2026-11-22 03:53 rb — Z2 done. scenarios_adapter has no seed flag (argparse absent; --help is ignored and it runs), so per task
  copied night/r20/scenarios_adapter.py → night/r21/scenarios_adapter_43000.py. Edits beyond the seed constant
  (assumptions, minimal): SEEDS range(32000,32005)→range(43000,43005); SCRATCH /tmp/r20-rb→/tmp/r21-rb (round rule:
  scratch only under /tmp/r21-rb/); the printed header's seed-range label 32000-32004→43000-43004 so the evidence
  is not mislabeled. No other logic changed (diff is 3 lines).
  Command: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r21/scenarios_adapter_43000.py` → exit 0, wall 12 s.
  Header: `Z1: 20 scenarios x 2 difficulties x 5 seeds (43000-43004) x 2 policies = 400 closed runs through judge_adapter, 12.2 s total`
  FLAGS (0): none — every reconcile/reconcile_hard episode F1 = 1.000, every flag_all return = -1.000, no invalid
  submissions, no episode ≥ 60 s (max 0.040 s). Table (reconcile = reconcile on default / reconcile_hard on hard;
  steps = max adapter steps of reconcile; full 80-row output at /tmp/r21-rb/z2_scenarios.out, JSON /tmp/r21-rb/z1.json):
  | scenario | difficulty | reconcile mean return | mean F1 | min F1 | flag_all mean return | max steps |
  |---|---|---|---|---|---|---|
  | D01 | default | 0.961 | 1.000 | 1.000 | -1.000 | 23 |
  | D01 | hard | 0.916 | 1.000 | 1.000 | -1.000 | 47 |
  | D02 | default | 0.961 | 1.000 | 1.000 | -1.000 | 23 |
  | D02 | hard | 0.916 | 1.000 | 1.000 | -1.000 | 47 |
  | D03 | default | 0.961 | 1.000 | 1.000 | -1.000 | 23 |
  | D03 | hard | 0.916 | 1.000 | 1.000 | -1.000 | 47 |
  | D04 | default | 0.961 | 1.000 | 1.000 | -1.000 | 23 |
  | D04 | hard | 0.916 | 1.000 | 1.000 | -1.000 | 47 |
  | D05 | default | 0.961 | 1.000 | 1.000 | -1.000 | 23 |
  | D05 | hard | 0.916 | 1.000 | 1.000 | -1.000 | 47 |
  | D06 | default | 0.959 | 1.000 | 1.000 | -1.000 | 23 |
  | D06 | hard | 0.918 | 1.000 | 1.000 | -1.000 | 45 |
  | D07 | default | 0.959 | 1.000 | 1.000 | -1.000 | 23 |
  | D07 | hard | 0.918 | 1.000 | 1.000 | -1.000 | 45 |
  | D08 | default | 0.959 | 1.000 | 1.000 | -1.000 | 23 |
  | D08 | hard | 0.918 | 1.000 | 1.000 | -1.000 | 45 |
  | D09 | default | 0.962 | 1.000 | 1.000 | -1.000 | 22 |
  | D09 | hard | 0.915 | 1.000 | 1.000 | -1.000 | 46 |
  | D10 | default | 0.960 | 1.000 | 1.000 | -1.000 | 22 |
  | D10 | hard | 0.922 | 1.000 | 1.000 | -1.000 | 44 |
  | D11 | default | 0.963 | 1.000 | 1.000 | -1.000 | 23 |
  | D11 | hard | 0.912 | 1.000 | 1.000 | -1.000 | 48 |
  | D12 | default | 0.962 | 1.000 | 1.000 | -1.000 | 22 |
  | D12 | hard | 0.920 | 1.000 | 1.000 | -1.000 | 45 |
  | D13 | default | 0.962 | 1.000 | 1.000 | -1.000 | 22 |
  | D13 | hard | 0.920 | 1.000 | 1.000 | -1.000 | 45 |
  | D14 | default | 0.960 | 1.000 | 1.000 | -1.000 | 23 |
  | D14 | hard | 0.920 | 1.000 | 1.000 | -1.000 | 44 |
  | D15 | default | 0.960 | 1.000 | 1.000 | -1.000 | 23 |
  | D15 | hard | 0.920 | 1.000 | 1.000 | -1.000 | 44 |
  | D16 | default | 0.960 | 1.000 | 1.000 | -1.000 | 23 |
  | D16 | hard | 0.918 | 1.000 | 1.000 | -1.000 | 45 |
  | D17 | default | 0.960 | 1.000 | 1.000 | -1.000 | 23 |
  | D17 | hard | 0.918 | 1.000 | 1.000 | -1.000 | 45 |
  | D18 | default | 0.960 | 1.000 | 1.000 | -1.000 | 23 |
  | D18 | hard | 0.918 | 1.000 | 1.000 | -1.000 | 45 |
  | D19 | default | 0.959 | 1.000 | 1.000 | -1.000 | 23 |
  | D19 | hard | 0.921 | 1.000 | 1.000 | -1.000 | 45 |
  | D20 | default | 0.959 | 1.000 | 1.000 | -1.000 | 23 |
  | D20 | hard | 0.921 | 1.000 | 1.000 | -1.000 | 45 |
  Called out per accept: no reconcile F1 < 1 and no flag_all > 0. NOTES (22): all hard reconcile_hard per-scenario
  mean returns 0.912–0.922 and D19/D20 default 0.959 are below the README jury_run mean 0.959 — expected: README's
  number is a 20-scenario default-difficulty mean on seeds 3001-3020; hard uses ~2x inspection steps at 0.002/step.
  Same pattern as round 20 (archive r20-LOG Z1); not a defect. Next: Z3 (jury_run on seed bases 24000-27000).
2026-11-22 03:55 rb — Z3 done. `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base <B> --json /tmp/r21-rb/j<B>.json`
  for B in 24000, 25000, 26000, 27000: all exit 0; wall 3 s, 2 s, 2 s, 3 s. Policy tables verbatim:
  --- B=24000 (seeds 24001-24020) ---
  20 jury scenarios D01-D20 (seeds 24001-24020) through judge_adapter, closed mode, policies in their own process (oracle grader-side)
  policy                P      R     F1   return   steps   max   time s   max s
  random_explorer   0.000  0.000  0.000   -1.000    33.0    33    0.032   0.033
  reconcile         1.000  1.000  1.000    0.961    20.4    23    0.033   0.035
  flag_all          0.000  0.000  0.000   -1.000     3.5     4    0.029   0.031
  oracle            1.000  1.000  1.000    1.000     1.0     1    0.005   0.006
  --- B=25000 (seeds 25001-25020) ---
  20 jury scenarios D01-D20 (seeds 25001-25020) through judge_adapter, closed mode, policies in their own process (oracle grader-side)
  policy                P      R     F1   return   steps   max   time s   max s
  random_explorer   0.000  0.000  0.000   -1.000    33.0    33    0.038   0.045
  reconcile         1.000  1.000  1.000    0.960    21.1    23    0.033   0.038
  flag_all          0.000  0.000  0.000   -1.000     3.5     4    0.030   0.031
  oracle            1.000  1.000  1.000    1.000     1.0     1    0.005   0.006
  --- B=26000 (seeds 26001-26020) ---
  20 jury scenarios D01-D20 (seeds 26001-26020) through judge_adapter, closed mode, policies in their own process (oracle grader-side)
  policy                P      R     F1   return   steps   max   time s   max s
  random_explorer   0.000  0.000  0.000   -0.903    33.0    33    0.033   0.034
  reconcile         1.000  1.000  1.000    0.961    20.7    24    0.034   0.037
  flag_all          0.000  0.000  0.000   -1.000     3.5     4    0.030   0.031
  oracle            1.000  1.000  1.000    1.000     1.0     1    0.005   0.006
  --- B=27000 (seeds 27001-27020) ---
  20 jury scenarios D01-D20 (seeds 27001-27020) through judge_adapter, closed mode, policies in their own process (oracle grader-side)
  policy                P      R     F1   return   steps   max   time s   max s
  random_explorer   0.000  0.000  0.000   -0.903    33.0    33    0.033   0.036
  reconcile         1.000  1.000  1.000    0.960    21.1    25    0.034   0.036
  flag_all          0.000  0.000  0.000   -1.000     3.5     4    0.030   0.034
  oracle            1.000  1.000  1.000    1.000     1.0     1    0.005   0.006
  Accept check: oracle F1 = 1.000 and reconcile F1 = 1.000 in all four runs; random_explorer returns -1.000/-1.000/
  -0.903/-0.903 and flag_all -1.000 everywhere — none > -0.5, nothing to call out. Note: random_explorer -0.903 on
  B=26000/27000 comes from fewer false positives (fp=38 vs flag_all's 600 across 20 episodes), so the FP penalty is
  smaller; P/R/F1 still 0.000. Not a defect. JSON at /tmp/r21-rb/j{24000,25000,26000,27000}.json.
  All rb tasks (Z1, Z2, Z3) done and pushed; no unchecked (rb) tasks remain — going IDLE.
2026-11-22 04:06 lead — Merged all worker branches (G1–G18, X1–X3, Y1–Y3, Z1–Z3 done). X1 text-only auditor F1 1.000 on 4,200 episodes, 0 disagreements. X3: 300 extreme configs valid with exact counts, >12 issues rejected with ValueError. X2: 1,335 clean-config violations; lead inspected the largest (D01 seed 41006, E0342, −500,336 KZT minor): a full refund debited to 2900 at the refund-date rate after the receipt credited it at the receipt-date rate. This follows the documented CONTRACT rule (refund Dr 2900 / Cr 1000 at payment-date rate); the document-currency credit is exactly 0 (chronology c_neg_credit = 0). Decision: no posting-rule change 13 h before freeze (would change policy text, every export and golden hashes); measure (X4) and document as a limitation in DESIGN §10 / README. Y3: README fixes by lead next (incl. real defect #13: closed-server command aborts in bash when GRADER_KEY is unset). Top-up 1 queued.
2026-11-22 04:08 lead — README: first-read fixes (Y3 items 1–4, 6, 7, 9, 10, 12–14). #13 was a real defect: the closed-server command `AUDITENV_SECRET="${GRADER_KEY:?...}"` aborted in bash without GRADER_KEY although the server keys hidden episodes by default since round 19; now the plain command (verified: starts, warns about the key file, exit 0). Skipped #5 (mode key text already says eval hides the reward), #8 (export commands are labelled as re-export after a generator change), #11 (the README 199/200 sentence is per difficulty in its own table). check exit 0 50.7 s; sync_docs no drift.
2026-11-22 04:08 lead — Correction to the previous entry: Y3 #11 was valid (README D01–D05 row gave 199/200 without saying it is the default count); now '199/200 default and 200/200 hard' per codex2's probe.
