2026-11-22 00:21 lead — Round 20 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/r19 archive. Wrote TASKS.md: independent defect hunts (codex1 chronology/policy-text/adapter reality, codex2 fresh-clone + claims audits, rb scenario adapter runs), evidence sweeps on unseen seeds for gemini workers. Baseline check running. Assumption: generator fixes stay with lead (one re-export owner) to avoid conflicting exports.
2026-11-22 00:23 lead — D: demo --seed 2003 reproduces every DEMO.md number (326 rows, 69 invoices, 21 inspections, 0.958, 286 / 351331 minor units, 0.333, 22 actions). P: sync_docs tables match, but prose on slide 7 and DESIGN §9 was stale since 20 Nov: analyze --config configs/eval_hard.json gives reconcile 20 FP (not 22), duplicate recall 2/8 (not 3/8, six missed, not five), mean 43 actions (not 43.2). Fixed PITCH.md and DESIGN.md; sync_docs does not cover prose numbers.
2026-11-22 00:27 gemini2b — G10: Re-exported splits to scratch dirs and diffed against committed exports. Commands and results:
  - `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/dev.json --out /tmp/r20-gemini2b/dev` (exit 0, wall 0.078s, "Exported 10 episodes to /tmp/r20-gemini2b/dev"). `diff -r episodes/dev /tmp/r20-gemini2b/dev` exit 0 (0 differing files).
  - `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/train.json --out /tmp/r20-gemini2b/train` (exit 0, wall 0.074s, "Exported 10 episodes to /tmp/r20-gemini2b/train"). `diff -r episodes/train /tmp/r20-gemini2b/train` exit 0 (0 differing files).
  - `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/eval_hard.json --out /tmp/r20-gemini2b/hard` (exit 0, wall 0.253s, "Exported 20 episodes to /tmp/r20-gemini2b/hard"). `diff -r episodes/hard /tmp/r20-gemini2b/hard` exit 0 (0 differing files).
  - `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/train_hard.json --out /tmp/r20-gemini2b/train_hard` (exit 0, wall 0.147s, "Exported 10 episodes to /tmp/r20-gemini2b/train_hard"). Committed `episodes/train_hard` does not exist (as documented in README line 195: hard train episodes are generated on demand into /tmp; `episodes/hard` holds eval_hard); verified exported directory with `env -u AUDITENV_SECRET uv run python -m auditenv.verify --dir /tmp/r20-gemini2b/train_hard` (exit 0: "10/10 episodes valid; episodes with problems: 0").
  All committed exports match byte for byte with fresh exports.
2026-11-22 00:31 gemini2b — G11: Checked golden hashes and ran reward mutation tests. Commands and results:
  - `uv run python scripts/golden.py --check` (exit 0, wall 0.650s): "All 80 golden hashes match /Users/caliskan/Projects/genesis-gemini2b/tests/golden_hashes.json."
  - `uv run python scripts/mutate_reward.py` (exit 0, wall 3:40.49 total / 219.12s user): "22/22 mutants killed."
  All 80 golden hashes match; all 22 reward/matcher/schema/metrics mutants successfully killed.
2026-11-22 00:33 gemini2b — G12: Ran `uv run python scripts/shortcut_miner.py` (seeds 0-999, configs random_mix/heavy, 2000 episodes, wall 22.4s, exit 1 due to flagged values without --report-only).
Max precision per issue type:
| type | affected max P | evidence max P | flagged (aff/ev) |
|---|---|---|---|
| duplicate_invoice | 0.996 | 0.996 | 2/2 |
| payment_allocation | 0.964 | 0.964 | 8/1 |
| fx_error | 0.704 | 0.308 | 3/0 |
| period_cutoff | 0.452 | 0.452 | 0/0 |

Total flagged values: 16 (precision > 0.5):
- affected duplicate_invoice (2): `invoices same_entity_currency_total_count == 2` (P=0.996), `invoices total_count_in_table == 2` (P=0.972).
- affected payment_allocation (8): `ledger amount_count_in_table@acct2900 == 4+` (P=0.964), `ledger day_rel_period@acct2900 == end-0` (P=0.789), `ledger amount_digits@acct2900 == 9` (P=0.750), `ledger position_decile@acct2900 == 9` (P=0.671), `ledger amount_count_in_table@acct2900 == 1` (P=0.622), `ledger day_rel_period@acct7900 == end-0` (P=0.568), `ledger amount_digits@acct2900 == 6` (P=0.566), `ledger payment_journal_size@acct2900 == 4+` (P=0.557).
- affected fx_error (3): `ledger day_rel_period@acct2900 == end-0` (P=0.704), `ledger position_decile@acct2900 == 9` (P=0.549), `ledger day_rel_period@acct7900 == end-0` (P=0.548).
- evidence duplicate_invoice (2): `invoices same_entity_currency_total_count == 2` (P=0.996), `invoices total_count_in_table == 2` (P=0.972).
- evidence payment_allocation (1): `ledger amount_count_in_table@acct2900 == 4+` (P=0.964).

Comparison with `docs/DESIGN.md` §10: Exactly 16 flagged values in default mode, precisely matching the 16 flagged values documented in DESIGN §10 (duplicate definitions at P=0.996, last-day 2900/7900 fx_error cues at P=0.70, 2900 payment_allocation hints at P=0.75-0.78 and repeated amount at P=0.964). 0 unlisted columns/features with precision > 0.5.
