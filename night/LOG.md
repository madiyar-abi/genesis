# Round 10 log

2026-11-20 03:44 lead (Claude) — Started round 10 as first lead (no TASKS.md). Read NIGHT, HANDOFF, SPEC, REVIEW rounds 1–9, archive r9. Official check: ALL CHECKS PASSED (33.0 s, exit 0). Probes in /tmp/r10-probe: (a) 3,300 random config combinations (0–12 issues incl. I1/I2, n_invoices 10–100, distractors, transform_seed, both difficulties) → verifier 0 problems, oracle and reconcile/reconcile_hard F1 1.0 everywhere, max 56 steps; edge configs (12 of one type on 10 invoices, 6×I1, 6×I2, hard, no distractors) all valid and solved — the shipped sweeps only use 3 fixed configs, so T1 publishes this as `fuzz --configs`. (b) `reset(1, {"errors": "x"})` raises AttributeError, `{"errors": 0 | false | []}` silently gives a clean company → T2. Assumption: workers gemini1–3 and deepseek are running per the prompt; T4 depends on T1 and says IDLE until it lands.
2026-11-20 03:45 lead — T2 done: test_reset_rejects_config_of_the_wrong_shape red (AttributeError / no raise) → green. gen_config raises ValueError unless errors/interacting are dicts; env.reset requires config dict or None. CONTRACT config paragraph states it. Golden 80/80, test_load + trajectory files unchanged; auditenv.check ALL CHECKS PASSED (33.3 s, 360 tests). Assumption: `errors: null` (previously = clean company, undocumented, used nowhere in configs/ or code) is now rejected like any non-object — the contract only documents `{type: count}`.
2026-11-20 03:48 gemini2 — T5 done: Solvability stress sweeps completed (0 non-zero exits).
- Command 1: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 0-999`
  Wall time: 23.34s
  Summary: reconcile on 4000 default episodes (seeds 0-999 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 33, truncated 0 (23.3 s)
- Command 2: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile_hard --seeds 0-999 --hard`
  Wall time: 60.31s
  Summary: reconcile_hard on 4000 hard episodes (seeds 0-999 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 58, truncated 0 (60.3 s)
2026-11-20 03:51 lead — T3: Reproduced ledger and credit-note edge cases on seeds 3 and 4, corrected config, evidence, lifecycle and Make examples. Official check passed in 63.0 s; measured tables matched.
2026-11-20 03:51 lead — T1: env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000: 3,000 cases (1,186 hard), 132.9 s, 0 problems, max 56 steps. Six focused tests passed, full check green.
