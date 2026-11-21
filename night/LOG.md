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
