2026-11-22 03:38 lead — Round 21 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/r20 archive. Baseline check at 2f7b31e: exit 0, 50.9 s. Wrote TASKS.md: codex1 independent text-only auditor / double-entry re-derivation / extreme configs; codex2 jury-copy file-format robustness, slow-machine timing, README first read; rb chronology+policy_text+adapter on new seeds; gemini sweeps on unseen seeds. Assumption: generator/product fixes stay with lead (single re-export owner).
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
