# Round 9 log

2026-11-20 03:16 lead (Claude) — Started round 9 as first lead (no TASKS.md). Read SPEC §10, HANDOFF, REVIEW (rounds 1–8), archive r8. Official check in the main checkout: ALL CHECKS PASSED (32.8 s). Rounds 1–8 hardened the data verifier heavily, so this round targets what the jury touches first: README snippets and commands run as written (T3 gemini1, T5 gemini3), hash-randomisation independence (T4 gemini2), a long hard sweep (T6 deepseek), and an independent read-only red-team pass on contract/isolation/reward/reproducibility (T2 lead, subagent running). Assumption: workers gemini1–3 and deepseek are running per the prompt; deepseek's worktree exists at ../genesis-deepseek.
2026-11-20 03:16 lead — T1 done: fresh clone of night/2026-11-20-r9 into /tmp/r9-clone, `env -u AUDITENV_SECRET uv run python -m auditenv.check` → "ALL CHECKS PASSED in 32.5 s", exit 0. Nothing in the check depends on untracked or ignored local files.
2026-11-20 03:26 gemini3 — T5 done: README "Other commands" sweep (19 commands run from repo root with env -u AUDITENV_SECRET, 0 failures, 0 files modified):
- `uv run python -m unittest discover -s tests -t .` — exit 0, 26.6 s — All documentation tables match measured data.
- `uv run python -m unittest tests.test_env` — exit 0, 0.2 s — OK
- `uv run python -m auditenv.verify --seeds 0-199` — exit 0, 3.5 s — 600/600 episodes valid; episodes with problems: 0
- `uv run python -m auditenv.verify --dir episodes/train` — exit 0, 0.1 s — 10/10 episodes valid; episodes with problems: 0
- `uv run python -m auditenv.verify --dir episodes/dev` — exit 0, 0.1 s — 10/10 episodes valid; episodes with problems: 0
- `uv run python -m auditenv.verify --dir episodes/hard` — exit 0, 0.2 s — 20/20 episodes valid; episodes with problems: 0
- `uv run python -m auditenv.attack` — exit 0, 0.3 s — Elapsed time: 0.243 s
- `uv run python -m tests.test_fuzz` — exit 0, 0.9 s — Python 3.11.14, 20312 episode actions, 20517 total step calls in 0.836 s
- `uv run python -m auditenv.check --json /tmp/auditenv-metrics.json` — exit 0, 33.4 s — ALL CHECKS PASSED in 33.4 s
- `uv run python scripts/sync_docs.py --check --json /tmp/auditenv-metrics.json` — exit 0, 0.0 s — All documentation tables match measured data.
- `uv run python -m auditenv.fuzz --seeds 0-999` — exit 0, 49.4 s — FUZZ PASSED
- `uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299` — exit 0, 6.2 s — reconcile on 1200 default episodes (seeds 0-299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 33, truncated 0 (6.2 s)
- `uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json` — exit 0, 0.1 s — | Total | 103 |
- `uv run python -m auditenv.demo` — exit 0, 0.1 s — Done. Full check: uv run python -m auditenv.check
- `uv run python scripts/mutate_reward.py` — exit 0, 88.1 s — 15/15 mutants killed.
- `uv run python scripts/sensitivity.py` — exit 0, 1.5 s — (re-grade with default parameters reproduced every env reward exactly; tolerance '0 (exact)' = 0 minor units, '1 %' = max(1, expected // 100); 1.5 s)
- `uv run python scripts/shortcut_miner.py --report-only` — exit 0, 16.1 s — | ledger | entity_id | E9977 | 47 |
- `uv run python scripts/golden.py --check` — exit 0, 0.5 s — All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini3/tests/golden_hashes.json.
- `uv run python scripts/bench.py` — exit 0, 8.6 s — | flag_all | hard | 7.20 | 4 | -1.000 | 0.000 |
