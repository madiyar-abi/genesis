# Round 17 log

2026-11-20 09:02 lead — Started round 17 (open improvement round, Claude Code lead). Wrote night/TASKS.md: T1–T4 worker evidence tasks on angles no earlier round covered (clone path with spaces/non-ASCII, timezone independence of exports, C-locale/ascii output encoding, config sweep on a new range). Next: three read-only red-team subagents (SPEC §04–§06 conformance of reward/contract; data ambiguity/solvability; observation-side leakage), findings → REVIEW.md Round 17 and tasks T5+. Assumption: deepseek still lacks an API key (r13–r16); lead takes T4 over after 1 h.
2026-11-20 09:08 lead — T98 rehearsed seed 2003. Four matches, 21 inspections, 0.958 return, closed policy saw [0.0]. Fresh reconcile micro-F1 1.000 dev and 0.752 hard. Script matches. Next: verify standalone exported task validation (T5).
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
