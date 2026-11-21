2026-11-22 03:38 lead — Round 21 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/r20 archive. Baseline check at 2f7b31e: exit 0, 50.9 s. Wrote TASKS.md: codex1 independent text-only auditor / double-entry re-derivation / extreme configs; codex2 jury-copy file-format robustness, slow-machine timing, README first read; rb chronology+policy_text+adapter on new seeds; gemini sweeps on unseen seeds. Assumption: generator/product fixes stay with lead (single re-export owner).

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
