2026-11-22 03:38 lead — Round 21 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/r20 archive. Baseline check at 2f7b31e: exit 0, 50.9 s. Wrote TASKS.md: codex1 independent text-only auditor / double-entry re-derivation / extreme configs; codex2 jury-copy file-format robustness, slow-machine timing, README first read; rb chronology+policy_text+adapter on new seeds; gemini sweeps on unseen seeds. Assumption: generator/product fixes stay with lead (single re-export owner).
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

2026-11-22 03:42 gemini1b — G4 stress solvability on seeds 10000-10299: reconcile default 1200 episodes imperfect 0, max steps 33, truncated 0 (wall time 7.7 s); reconcile_hard 1200 hard episodes imperfect 0, max steps 57, truncated 0 (wall time 21.4 s). Next: G5.
2026-11-22 03:42 gemini3a — G13: Four jury modules 5 times (tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired). All 5 runs passed 73/73 tests cleanly.
  Run 1: Ran 73 tests in 2.094s, OK, exit 0, wall time 2s
  Run 2: Ran 73 tests in 2.083s, OK, exit 0, wall time 2s
  Run 3: Ran 73 tests in 2.225s, OK, exit 0, wall time 3s
  Run 4: Ran 73 tests in 2.249s, OK, exit 0, wall time 2s
  Run 5: Ran 73 tests in 2.528s, OK, exit 0, wall time 3s
  Total: 365 tests, 0 failures. Next: G14.
2026-11-22 03:42 gemini3b — G16 complete: verified all splits under episodes/ (dev: 10/10 valid, exit 0, 0.13s; hard: 20/20 valid, exit 0, 0.35s; train: 10/10 valid, exit 0, 0.11s). Next: G17.
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
2026-11-22 03:43 gemini2b — G10 complete. Re-exported dev, train, and hard splits into /tmp/r21-gemini2b/ and diffed against committed episodes/:
- dev: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/dev.json --out /tmp/r21-gemini2b/dev` (exit 0, wall time 0.119s, "Exported 10 episodes to /tmp/r21-gemini2b/dev") && `diff -r episodes/dev /tmp/r21-gemini2b/dev` (exit 0, 0 files differ).
- train: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/train.json --out /tmp/r21-gemini2b/train` (exit 0, wall time 0.120s, "Exported 10 episodes to /tmp/r21-gemini2b/train") && `diff -r episodes/train /tmp/r21-gemini2b/train` (exit 0, 0 files differ).
- hard: `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/eval_hard.json --out /tmp/r21-gemini2b/hard` (exit 0, wall time 0.374s, "Exported 20 episodes to /tmp/r21-gemini2b/hard") && `diff -r episodes/hard /tmp/r21-gemini2b/hard` (exit 0, 0 files differ).
All 40 exported episodes across all three splits are byte-for-byte identical to the committed exports (0 differing files). Next: G11.
2026-11-22 03:42 gemini3a — G14: Ran attack search and sensitivity analysis. Both passed cleanly (exit 0).
  - auditenv.attack: PASSED, 20 seeds evaluated (5 clean, 15 dirty), 11,000 mutations tested across 10 families, 0 violations detected, elapsed 0.360 s, exit 0, wall time 0s.
  - scripts/sensitivity.py: PASSED, evaluated dev (10 episodes) and hard (20 episodes) across varied step cost (0.001, 0.002, 0.005) and amount tolerance (0, 1, 100 units). Ranking unchanged across all settings: dev (oracle > reconcile > naive_reconcile > random > flag_all), hard (oracle > reconcile_hard > reconcile > naive_reconcile > random > flag_all). Re-grade with default parameters reproduced every env reward exactly in 2.1 s, exit 0, wall time 3s. Next: G15.
2026-11-22 03:42 gemini3b — G17 complete: ran `yes '' | env -u AUDITENV_SECRET uv run python -m auditenv.demo` (exit 0, wall time 0.13s). Quoted final score lines: `terminal reward 0.958 = clip(2*F1 - 1 - 0.002*21 steps)   P=1.00 R=1.00 F1=1.00`; section 4 rewards: oracle 1.000, reconcile 0.958, silence -1.000, repeated twice 0.333, clean silence 1.000, clean reconcile 0.958; section 5 closed run: `policy side: 22 steps, rewards seen = [0.0], final info = {}`, `grader log : reward 0.958, F1 1.00, TP 4 FP 0 FN 0`. Compared with docs/DEMO.md: all numbers match exactly (326 ledger rows, 69 invoices, 100 budget steps; 21 inspect + 1 submit step; return 0.958; FX error 286 cents / $2.86, allocation error 351,331 cents / $3,513.31; oracle 1, repeated 0.333, silence -1; 22 actions, empty info, TP 4 FP 0 FN 0, return 0.958). Zero differences found. Next: G18.
