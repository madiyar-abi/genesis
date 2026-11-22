2026-11-22 06:21 lead — Round 23 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/CASE_UPDATES/REVIEW r20–r22/r22 archive. No known defect left from r22. Plan: clean-room checkers for what is not independently covered yet — Block 2 condition 1 rebuilt from provenance.json as README documents it (codex2 Y1), Block 1 C01–C20 from the published text with a separate policy process (codex1 X1), matcher differential from the published conventions (codex1 X2), engineering anchors self-score (codex2 Y2); rb re-runs r20–r22 checkers on unseen seeds + fresh-clone README walk; gemini sweeps on unseen seeds. Lead: baseline check, three red-team subagents, merge/fix, DEMO/PITCH. Assumption: unseen seed ranges 62000–72099 for checkers, 19000–20999 fuzz, 87000/90000 configs, 10000–11999 verify, 14000 stress, 34000–36000 jury_run (none used in r18–r22 logs).
2026-11-22 06:22 lead — L1 done: baseline `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r23-lead-check.json` exit 0, 565 tests, all gates, 55.7 s; sync_docs --check: no drift. L2 started: three read-only red-team subagents (contract/reward vs CASE_UPDATES, data ambiguity/evidence on seeds 73000+, jury-facing doc claims).
2026-11-22 06:22 lead — L4 done: `yes '' | uv run python -m auditenv.demo` exit 0; PAY-136430 286 and 351331 USD minor units, 21 inspections, terminal 0.958, grader TP 4 FP 0 FN 0, comparison table (oracle 1.000 … clean reconcile 0.958) — every number in docs/DEMO.md matches.

2026-11-22 06:30 codex1 — X1 done.
Command: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r23.c_matrix` → exit 0, real 65.57 s.
Seeds 70000–70004 × default/hard. C and L both use the clean generator config and are generated into distinct
directories. L is accepted only if its ledger has at least 101 rows. E has one duplicate invoice. U is selected
against the full public ID inventory. The separate JSON-pipe policy uses macOS sandbox-exec to deny reads of
the repo, fixtures and grader key directory, and denies network. The isolated train process is used for
C15/C17/C18 to check final grading. C18 sleeps 60.1 s inside that process after one inspection. The jury inserts
oracle findings after reading the policy's action from the pipe.

| Check | Result | Check | Result |
|---|---|---|---|
| C01 | pass 10/10 | C11 | pass 10/10 |
| C02 | pass 10/10 | C12 | pass 10/10 |
| C03 | pass 10/10 | C13 | pass 10/10 |
| C04 | pass 10/10 | C14 | pass 10/10 |
| C05 | pass 10/10 | C15 | pass 10/10 |
| C06 | pass 10/10 | C16 | pass 10/10 |
| C07 | pass 10/10 | C17 | pass 10/10 |
| C08 | pass 10/10 | C18 | pass 10/10 |
| C09 | pass 10/10 | C19 | pass 10/10 |
| C10 | pass 10/10 | C20 | pass 10/10 |

No failures on the final run. C20 checks public responses against the fixture records and uses ordinary invalid
requests. It covers the pipe and policy sandbox in this harness. Jury-runner deployment and product code review
are outside this black-box check. Next: X2.
