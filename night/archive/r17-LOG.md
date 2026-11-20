# Round 17 log

2026-11-20 09:02 lead — Started round 17 (open improvement round, Claude Code lead). Wrote night/TASKS.md: T1–T4 worker evidence tasks on angles no earlier round covered (clone path with spaces/non-ASCII, timezone independence of exports, C-locale/ascii output encoding, config sweep on a new range). Next: three read-only red-team subagents (SPEC §04–§06 conformance of reward/contract; data ambiguity/solvability; observation-side leakage), findings → REVIEW.md Round 17 and tasks T5+. Assumption: deepseek still lacks an API key (r13–r16); lead takes T4 over after 1 h.

2026-11-20 09:08 lead — T98 rehearsed seed 2003. Four matches, 21 inspections, 0.958 return, closed policy saw [0.0]. Fresh reconcile micro-F1 1.000 dev and 0.752 hard. Script matches. Next: verify standalone exported task validation (T5).

2026-11-20 09:08 gemini1 — Completed T1 (Jury-environment robustness in non-ASCII / spaced path). Cloned branch night/2026-11-20-r17 into '/tmp/r17 жюри clone'. Ran all 3 commands with env -u AUDITENV_SECRET:
1. `env -u AUDITENV_SECRET uv run python -m auditenv.check`: exit 0, wall time 47.98s, last line: "ALL CHECKS PASSED in 47.9 s"
2. `env -u AUDITENV_SECRET uv run python -m auditenv.demo`: exit 0, wall time 0.15s, last line: "Done. Full check: uv run python -m auditenv.check"
3. `env -u AUDITENV_SECRET uv run python -m auditenv.verify --dir episodes/dev`: exit 0, wall time 0.09s, last line: "10/10 episodes valid; episodes with problems: 0"
Zero non-zero exits and zero tracebacks; all 385 tests and verifiers passed without issues in non-ASCII path with spaces. Removed clone directory. Next: check for further unchecked tasks tagged (gemini1).

2026-11-20 09:08 gemini2 — T2. Timezone independence evidence across UTC, Asia/Almaty, America/Los_Angeles, Pacific/Kiritimati.
For each timezone, ran `TZ=<tz> env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/dev.json --out /tmp/r17-tz-<name>/dev` (where name has `/` replaced by `_`), `diff -r episodes/dev /tmp/r17-tz-<name>/dev`, and `TZ=<tz> env -u AUDITENV_SECRET uv run python scripts/golden.py --check`.
Results per TZ:
1. `TZ=UTC` (name=UTC):
   - diff: empty (byte-for-byte identical to episodes/dev)
   - golden.py last line: "All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2/tests/golden_hashes.json." (exit code 0)
2. `TZ=Asia/Almaty` (name=Asia_Almaty):
   - diff: empty (byte-for-byte identical to episodes/dev)
   - golden.py last line: "All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2/tests/golden_hashes.json." (exit code 0)
3. `TZ=America/Los_Angeles` (name=America_Los_Angeles):
   - diff: empty (byte-for-byte identical to episodes/dev)
   - golden.py last line: "All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2/tests/golden_hashes.json." (exit code 0)
4. `TZ=Pacific/Kiritimati` (name=Pacific_Kiritimati):
   - diff: empty (byte-for-byte identical to episodes/dev)
   - golden.py last line: "All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2/tests/golden_hashes.json." (exit code 0)
Export outputs and golden hashes are completely timezone-independent. Removed temporary export directories in /tmp.
Assumption: none; evidence-only task. Next: check TASKS.md for remaining (gemini2) tasks, else IDLE.

2026-11-20 09:08 gemini3 — T3. Locale / output-encoding robustness, evidence only (9 runs):
1. `env -u AUDITENV_SECRET LC_ALL=C LANG=C uv run python -m auditenv.demo`: exit code 0, last line: `Done. Full check: uv run python -m auditenv.check`
2. `env -u AUDITENV_SECRET PYTHONIOENCODING=ascii uv run python -m auditenv.demo`: exit code 0, last line: `Done. Full check: uv run python -m auditenv.check`
3. `env -u AUDITENV_SECRET PYTHONUTF8=0 LC_ALL=C uv run python -m auditenv.demo`: exit code 0, last line: `Done. Full check: uv run python -m auditenv.check`
4. `env -u AUDITENV_SECRET LC_ALL=C LANG=C uv run python -m auditenv.verify --seeds 0-9`: exit code 0, last line: `30/30 episodes valid; episodes with problems: 0`
5. `env -u AUDITENV_SECRET PYTHONIOENCODING=ascii uv run python -m auditenv.verify --seeds 0-9`: exit code 0, last line: `30/30 episodes valid; episodes with problems: 0`
6. `env -u AUDITENV_SECRET PYTHONUTF8=0 LC_ALL=C uv run python -m auditenv.verify --seeds 0-9`: exit code 0, last line: `30/30 episodes valid; episodes with problems: 0`
7. `env -u AUDITENV_SECRET LC_ALL=C LANG=C uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json`: exit code 0, last line: `| Total | 103 |`
8. `env -u AUDITENV_SECRET PYTHONIOENCODING=ascii uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json`: exit code 0, last line: `| Total | 103 |`
9. `env -u AUDITENV_SECRET PYTHONUTF8=0 LC_ALL=C uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json`: exit code 0, last line: `| Total | 103 |`
No UnicodeEncodeError or traceback occurred across any run. All 9 runs completed with exit code 0. Assumption: evidence only, no code changes required. What's next: check for remaining (gemini3) tasks, else IDLE.

2026-11-20 09:09 lead — T5. The verifier now rejects blank public/task.txt. Both empty and whitespace-only instructions previously passed standalone directory verification. The directory regressions pass, and all ten dev exports verify.

2026-11-20 09:10 lead — T6. The verifier checks integer exponents for every currency used in public records. Two mutations previously passed: a missing JPY exponent and JSON false in place of zero. Both now fail, and valid dev exports pass.

2026-11-20 09:10 lead — T1. Reviewed the fresh clone run in a path containing Cyrillic and spaces. The official check, demo and verifier all exited zero.

2026-11-20 09:10 lead — T2. Reviewed four timezone runs. Dev exports matched byte for byte and all 80 golden hashes matched in each timezone.

2026-11-20 09:10 lead — T3. Reviewed all nine command and encoding combinations. The demo, verifier and analysis CLI exited zero under each setting.

2026-11-20 09:10 lead — T99. The ten-slide outline matches the demo and the official metrics. The default reconciliation policy on hard episodes scored 41 TP, 22 FP and 5 FN. The hard policy scored 46 TP with no FP or FN. Both averaged 43.2 actions. Documentation tables match the fresh report.

2026-11-20 09:11 lead — T4. DeepSeek exited with the missing-key error before starting. The lead independently verified its acceptance command during integration. `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 30000` exited 0 in 99.94 s wall time.
config sweep, cases 30000-32999: 3000 random configs (1195 hard) in 99.9 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 58
FUZZ PASSED

2026-11-20 09:12 lead — Rechecked SPEC §§01–13, README, demo and pitch. The final offline check passed all 387 tests, both 20-pair suites, data, reward and remote gates in 37.5 s. All 40 exports verify and sync_docs --check passes. Fuzz 0–999 verified 3,000 episodes, attack checked 11,000 mutations with zero violations and the miner confirmed the default duplicate cue (4,902/4,920). The marathon owns PR/CI integration. Human submission checklist remains open.
