# Round 21

Open improvement round (freeze 2026-11-22 18:00). Rounds 18–20 each found an *ordinary-use* data defect with an
independent checker that read only public data (refund before receipt; cash applied before the invoice was booked).
This round continues that line with checkers no round has written yet: an independent auditor written only from the
task text, an independent double-entry/balance re-derivation, and extreme config combinations — plus fresh evidence
on unseen seeds.

Rules for workers: run from the repo root, prefix every module with `env -u AUDITENV_SECRET uv run python -m ...`.
`git fetch && git merge origin/night/2026-11-22-r21` before each task. Touch only your listed files plus
night/TASKS.md (your own `[x]`) and night/LOG.md (append, `date '+%F %H:%M'` timestamp). Never edit README.md,
HANDOFF.md, REVIEW.md, docs/, auditenv/, episodes/, trajectories/ unless your task lists them. Scratch files only
under /tmp/r21-<your name>/. Evidence tasks: record exact command, exit code, wall time and the summary line(s);
quote any failure verbatim. If something fails, do NOT fix product code — log it with a reproduction; the lead fixes.
Audit scripts go under `night/r21/` (one file per task, named in the task). Scripts that "read only public data" may
import `auditenv.generator` (to generate), `auditenv.jury` (config list), `judge_adapter` and `auditenv.money`, and
must never read truth/provenance, `verify.py`, `inject.py` or `auditenv/policies/`.

## codex1 — independent defect hunts (strong)
- [x] X1 (codex1) Independent text-only auditor. Write `night/r21/text_auditor.py`: an audit policy implemented ONLY
  from `public/task.txt` + `policy.json` + the public tables (do not open auditenv/policies/, inject.py, verify.py,
  matcher.py). It derives findings for every issue type the task text defines. Run it through `judge_adapter`
  (`generate_episode` to a temp dir, then `score_episode` on its findings) on seeds 40000–40099 × default, hard and
  every D01–D20 config of `auditenv/jury.py` in both difficulties. — files: night/r21/text_auditor.py, night/LOG.md —
  accept: LOG table config × difficulty → mean F1 / precision / recall; then, for every episode where F1 < 1, the
  lead-readable classification of each missed or extra finding: (a) auditor bug, (b) the text does not state the rule
  needed (quote the missing rule), or (c) truth label looks wrong (seed, config, record ids, why). Exit 0 always;
  this is evidence, not a gate.
- [x] X2 (codex1) Independent double-entry and balance re-derivation. Write `night/r21/ledger_identity.py` (public
  data only): per journal (group rows by `timestamp` + entity for journals without ids, see CLAUDE.md gotchas) Dr =
  Cr; per invoice the AR (1200) balance in time order never below 0 and at period end equals total − applied cash −
  credit notes (at the documented rates); per customer the 2900 balance in time order never below 0; every 7900 row
  equals the FX difference the policy text defines; the trial balance sums to 0. Seeds 41000–41299 × default, hard
  and D01–D20 both difficulties. — files: night/r21/ledger_identity.py, night/LOG.md — accept: per check × config the
  count and violations; violations in clean configs (D01–D05) quoted with seed and row ids; exit 0 iff none
  unexplained (explained = the config injects an error type that produces it, as in night/r20/chronology.py).
- [x] X3 (codex1) Extreme config combinations through `judge_adapter.generate_episode` + `reset` + `score_episode`
  (oracle-from-records policy `reconcile`/`reconcile_hard` and empty findings): n_invoices 10 with 0, 1, 12, 20, 50
  errors of one type and of mixed types; every issue type alone at its max; `interacting` only; `allocation` ×
  `ensure_distractors` × `distractors` × `difficulty` × `transform_seed` full product; n_invoices 100 with 12 issues.
  Write `night/r21/extreme_configs.py`. — files: night/r21/extreme_configs.py, night/LOG.md — accept: per config:
  either a valid episode (`uv run python -m auditenv.verify` logic via `auditenv.verify` on the written dir is
  allowed here, it is a check not a solver) whose truth count equals the requested count, or a `ValueError` with a
  clear message; LOG lists every other exception, silent count mismatch, or step-budget overrun with a reproduction.

## codex2 — jury-run realism (strong)
- [x] Y1 (codex2) Jury copy robustness beyond the published paired transform: take 10 exported episodes (5 default,
  5 hard; `episodes/dev`, `episodes/hard`) and write variants a jury tool could plausibly produce when it re-writes
  files: CSV column order shuffled, CRLF line endings, UTF-8 BOM on CSV/JSON, trailing newline missing, JSON pretty-
  printed vs compact, JSONL with keys reordered. For each variant: `judge_adapter` reset on `episode_dir` + replay of
  the reference answer + `score_episode`. Script `night/r21/jury_copy.py`. — files: night/r21/jury_copy.py,
  night/LOG.md — accept: table variant → accepted / rejected (error text) / score equal to the original; every
  rejection of a semantically identical file called out (the lead decides whether to accept it).
- [x] Y2 (codex2) Hidden-run timing on a slow machine: run the four jury modules and `auditenv.jury_run` under
  `taskpolicy -c background` (macOS low-QoS, slower cores) and with 6 parallel copies of
  `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 0-999 --hard` as background load. — files:
  night/LOG.md — accept: per run exit code + wall time + any timing-related failure quoted verbatim (60 s limit,
  timeouts in tests).
- [x] Y3 (codex2) README first-read review as a jury member who has 10 minutes: follow README top to bottom on a
  fresh clone (`git clone /Users/caliskan/Projects/genesis /tmp/r21-codex2/clone`, branch origin/night/2026-11-22-r21);
  list every place where a reader would get stuck, read a claim that is not backed by a command, or find two
  sections saying different things. — files: night/LOG.md — accept: numbered list with README line numbers and a
  proposed replacement text for each item; "nothing found" only with the list of sections read.

## rb — independent checkers on fresh seeds (medium)
- [x] Z1 (rb) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 42000-42299` and
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/policy_text.py --seeds 42000-42199` — files:
  night/LOG.md — accept: exit codes, totals and "unexplained" lines verbatim, wall times.
- [x] Z2 (rb) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py` with seeds changed
  to 43000–43004 (read its `--help`; if it has no seed flag, copy it to `night/r21/scenarios_adapter_43000.py` and
  change only the seed constant) — files: night/r21/scenarios_adapter_43000.py (if needed), night/LOG.md — accept:
  scenario × difficulty table of mean scores; any reconcile score below README's documented value or flag_all > 0
  called out.
- [x] Z3 (rb) `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base <B> --json /tmp/r21-rb/j<B>.json`
  for B in 24000, 25000, 26000, 27000 — files: night/LOG.md — accept: per run the policy table; call out any run
  where oracle F1 < 1, reconcile F1 < 1, or random/flag_all return > -0.5.

## gemini1a — seed sweeps (evidence only, files: night/LOG.md)
- [x] G1 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 13000-13999` and the same with
  `--hard` — accept: both summaries + wall times in LOG; any problem line verbatim.
- [x] G2 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 69000` — accept:
  summary + wall time + max steps.
- [x] G3 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 3000-3999` — accept: last line.

## gemini1b — stress solvability (evidence only, files: night/LOG.md)
- [x] G4 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 10000-10299` and
  `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 10000-10299` —
  accept: per command the summary line + wall time.
- [x] G5 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 14000-14999` and the same with
  `--hard` — accept: both summaries + wall times; any problem line verbatim.
- [x] G6 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 72000` — accept:
  summary + wall time + max steps.

## gemini2a — chronology on new seeds (evidence only, files: night/LOG.md)
- [x] G7 (gemini2a) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 37000-37299` —
  accept: exit code, totals line and "unexplained violations" line verbatim, wall time.
- [x] G8 (gemini2a) Same as G7 with `--seeds 37300-37599`.
- [x] G9 (gemini2a) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/policy_text.py --seeds 38000-38199` —
  accept: exit code and the final "Audited ... unexpected failures" line verbatim, wall time.

## gemini2b — reproducibility (evidence only, files: night/LOG.md)
- [x] G10 (gemini2b) Re-export into scratch dirs and diff against the committed exports:
  `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/dev.json --out /tmp/r21-gemini2b/dev` then
  `diff -r episodes/dev /tmp/r21-gemini2b/dev`; same for every split under episodes/ (config names in configs/) —
  accept: per split the diff exit code; any differing file named.
- [x] G11 (gemini2b) `uv run python scripts/golden.py --check` and `uv run python scripts/mutate_reward.py` —
  accept: both summary lines and exit codes.
- [x] G12 (gemini2b) `uv run python scripts/shortcut_miner.py --seeds 5000-5999 --report-only` and the same with
  `--hard` — accept: printed tables; any value with precision > 0.5 that is NOT listed in docs/DESIGN.md §10 called out.

## gemini3a — repeatability (evidence only, files: night/LOG.md)
- [x] G13 (gemini3a) Four jury modules 5 times: `env -u AUDITENV_SECRET uv run python -m unittest
  tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired` — accept: per
  run `Ran N tests` + result.
- [x] G14 (gemini3a) `env -u AUDITENV_SECRET uv run python -m auditenv.attack` and `uv run python scripts/sensitivity.py`
  — accept: summaries + exit codes.
- [x] G15 (gemini3a) Full suite under `PYTHONHASHSEED=7 TZ=America/St_Johns env -u AUDITENV_SECRET uv run python -m
  unittest discover -s tests -t .` and `PYTHONHASHSEED=99 TZ=Pacific/Chatham ...` — accept: `Ran N tests`,
  OK/FAILED, wall time; failures verbatim.

## gemini3b — exports, demo, docs drift (evidence only, files: night/LOG.md)
- [x] G16 (gemini3b) `uv run python -m auditenv.verify --dir episodes/<split>` for every directory under episodes/ —
  accept: per split the `N/N episodes valid` line.
- [x] G17 (gemini3b) `yes '' | uv run python -m auditenv.demo` — accept: exit code, the final reward/score lines
  quoted; compare them with the numbers in docs/DEMO.md and call out any difference.
- [x] G18 (gemini3b) `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r21-gemini3b/c.json` then
  `uv run python scripts/sync_docs.py --check --json /tmp/r21-gemini3b/c.json` — accept: both exit codes; drift lines
  verbatim.

## lead
- [x] L0 (lead) Baseline on round start `2f7b31e`: `env -u AUDITENV_SECRET uv run python -m auditenv.check` → exit 0,
  50.9 s.
- [ ] L1 (lead) Review worker findings, fix every real defect test-first, re-export if the generator changes — files:
  as needed — accept: `env -u AUDITENV_SECRET uv run python -m auditenv.check` exit 0.
- [ ] L2 (lead) Record Round 21 findings with evidence in REVIEW.md, sync doc numbers (`scripts/sync_docs.py`),
  update HANDOFF.md — files: REVIEW.md, HANDOFF.md, README.md, docs/ — accept: sync_docs --check no drift.
- [ ] D (lead) `docs/DEMO.md` — re-verify the numbered 2–3 min recording script against the actual demo output —
  accept: every number in it reproduced.
- [ ] P (lead) `docs/PITCH.md` — re-verify slide outline facts and numbers against the current check output — accept:
  every number matches.

## Top-up 1 (04:30) — same rules as above
- [ ] X4 (codex1) Classify every clean-config (D01–D05, both difficulties) violation of `night/r21/ledger_identity.py`
  on seeds 41000–41299: add a `--classify` flag that sorts each into (a) `unapplied_running` caused only by a refund
  debited at the refund-date rate while its receipt credited 2900 at the receipt-date rate (same customer, same
  document currency, document-currency credit never negative), (b) `ar_running`/`ar_close` off by at most the number
  of cash applications to that invoice (per-application ROUND_HALF_UP residue), (c) other. — files:
  night/r21/ledger_identity.py, night/LOG.md — accept: LOG counts per class × config, max |residue| for (a) in base
  minor units and as % of the refund, and every class (c) item quoted with seed and row ids ("0 other" is the hoped
  result, only with the totals).
- [ ] X5 (codex1) `env -u AUDITENV_SECRET uv run python -m night.r21.text_auditor` on seeds 45000–45099 (add a
  `--seeds` flag if missing) — files: night/r21/text_auditor.py, night/LOG.md — accept: the table + discrepancy count.
- [ ] Y4 (codex2) After the lead's README commit "README: first-read fixes (Y3)" lands (merge first; if it is not
  there yet, do Y5 first): fresh clone at origin/night/2026-11-22-r21, run every command in the README sections the
  commit touched — files: night/LOG.md — accept: table command → exit code → wall time; any mismatch with the text.
- [ ] Y5 (codex2) Re-run Y2's combined condition (low QoS + 6 parallel hard fuzz sweeps) on `auditenv.jury_run` only,
  3 times, and record per policy the max wall time; then the same with `--seed-base 5000` — files: night/LOG.md —
  accept: table run → policy → max s; note whether the 54 s outlier repeats and what part is process startup (time
  `uv run python -c pass` under the same load).
- [ ] Z4 (rb) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.extreme_configs` and
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.jury_copy` — files: night/LOG.md — accept: exit codes
  + summary lines (reproduction of codex1/codex2 results by another worker).
- [ ] G19 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 15000-15999` and the same with
  `--hard` — files: night/LOG.md — accept: both summaries + wall times.
- [x] G20 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 75000` — files:
  night/LOG.md — accept: summary + wall time + max steps.
- [ ] G21 (gemini2a) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 39000-39299`
  — files: night/LOG.md — accept: exit code, totals and "unexplained violations" lines verbatim.
- [ ] G22 (gemini2b) `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 4000-5999` — files:
  night/LOG.md — accept: last line + wall time.
- [ ] G23 (gemini3a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 11000-11299`
  and `... --hard --stress reconcile_hard --seeds 11000-11299` — files: night/LOG.md — accept: summaries + wall times.
- [ ] G24 (gemini3b) After the lead's README commit lands: `env -u AUDITENV_SECRET uv run python -m auditenv.check
  --json /tmp/r21-gemini3b/c2.json` then `uv run python scripts/sync_docs.py --check --json /tmp/r21-gemini3b/c2.json`
  — files: night/LOG.md — accept: both exit codes and last lines.
