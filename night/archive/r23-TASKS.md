# Round 23

Open improvement round (freeze 2026-11-22 18:00). Round 22 left no known defect. This round adds the one
independent checker the jury's Block 2 condition 1 implies and nobody has written yet — rebuild the books *before*
the error from `grader/provenance.json` exactly as README documents it, and prove the declared discrepancy from the
before/after states without our matcher or verifier — plus a clean-room C01–C20 run and a clean-room matcher
differential. Workers re-run the existing independent checkers and sweeps on unseen seeds. The lead runs red-team
passes and keeps the jury materials true.

Rules for workers: run from the repo root, prefix every module with `env -u AUDITENV_SECRET uv run python -m ...`
(scripts under night/: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.rNN.<name> ...`).
`git fetch && git merge origin/night/2026-11-22-r23` before each task. Touch only your listed files plus
night/TASKS.md (your own `[x]`) and night/LOG.md (append, `date '+%F %H:%M'` timestamp, never estimated).
Never edit README.md, HANDOFF.md, REVIEW.md, docs/, auditenv/, judge_adapter.py, episodes/, trajectories/,
tests/ unless your task lists them. Scratch files only under /tmp/r23-<your name>/. Evidence tasks: record the exact
command, exit code, wall time and the summary line(s); quote any failure verbatim. If something fails, do NOT fix
product code — log it with a reproduction (seed, config, ids); the lead fixes. Clean-room scripts must not read or
import `auditenv/verify.py`, `auditenv/inject.py`, `auditenv/matcher.py`, `auditenv/policies/`, `auditenv/transform.py`
or the tests; they may import `judge_adapter`, `auditenv.jury` (for `SCENARIOS`) and `auditenv.money`, and generate
episodes only through `judge_adapter.generate_episode`.

**FIX COMMIT `e23958c`** (lead, `generator: nothing-allocated evidence cites the payment's whole journal…`): with
nothing allocated, a payment_allocation evidence set now holds every ledger row of the payment (cash, 2900, other AR
credits, 7900) instead of only the 2900 row; policy.json evidence/duplicate wording and the hard task text changed;
episodes/trajectories/golden re-exported. Tasks marked *after FIX* run on a head that contains it
(`git fetch && git merge origin/night/2026-11-22-r23` first; `git log --oneline | grep e23958c`).

## codex1 (strong)
- [x] X1 (codex1) Clean-room Block 1 run, written only from night/CASE_UPDATES.md lines 31–98 (adapter interface,
  boundary rules, fixtures C/E/L/U, C01–C20) and README "Jury adapter": `night/r23/c_matrix.py`. Build fixtures with
  `judge_adapter.generate_episode` (C = clean config, E = one declared error, L = a table with ≥ 101 rows, U = an id
  chosen after reading the fixture's public files), then drive `judge_adapter.make_env()` from a *separate policy
  process* that only sees what `reset`/`step` return (subprocess + JSON over a pipe; the jury side keeps paths, truth
  and `score_episode`). Implement each of C01–C20 as one pass/fail with all its sub-assertions (C18: a reproducible
  over-60-s scenario — use the documented clock injection or a policy that sleeps; say which). Run on fixture seeds
  70000–70004 × default and hard. — files: night/r23/c_matrix.py, night/LOG.md — accept: LOG table C01–C20 → pass N/10;
  every fail quoted (stimulus → observed) with a one-command reproduction; script exits 1 on any fail.
- [x] X2 (codex1) Clean-room matcher differential, written only from night/CASE_UPDATES.md lines 120–211 (Block 3,
  "Точные соглашения matcher", M01–M12): `night/r23/matcher_diff.py` with your own implementation (structure limits
  first, sets, exact ids/currency, τ from `policy.json` `findings.tolerance_minor`, maximum-cardinality matching with
  the published tie rule, the reward formula). For 40 generated episodes (seeds 71000–71019 × default/hard, plus
  D06–D20 through `auditenv.jury.SCENARIOS`) build ≥ 100,000 submissions by mutating the truth answer (drop/duplicate
  findings, swap types, add/remove affected ids, ±1 amounts, currency case/space, evidence subsets/supersets/unknown
  ids, 10/11 evidence ids, 30/31 findings, 1000/1001-char explanations, bool/str/float amounts, missing/extra keys)
  and compare tp/fp/fn/precision/recall/f1/return with `judge_adapter.score_episode` (abs diff ≤ 1e-9; null fields
  on invalid). — files: night/r23/matcher_diff.py, night/LOG.md — accept: LOG: submissions compared, disagreements 0
  (or each disagreement quoted with the submission and both results, and which reading of the text is right).
- [x] X3 (codex1, after FIX) Update `night/r21/text_auditor.py` to the new published evidence rule (policy.json
  `findings.evidence`: with nothing allocated cite every ledger row of the payment) — change only that, say so in
  LOG — then `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.text_auditor --seeds 63000-63099` and
  `--seeds 75000-75099` — files: night/r21/text_auditor.py, night/LOG.md — accept: F1 1.000, 0 discrepancies on both.
- [x] X4 (codex1, after FIX) Extend `night/r23/c_matrix.py` with the two boundary cases fixed in `5700626`: C02 on a
  fixture copy without `public/task.txt` (task must be a non-empty str) and a closed-mode submit with 31 findings /
  non-object findings (policy sees only `{"accepted": true}` or a bounded structure error — never "accepted" for an
  invalid structure; reward 0; grader return -1). Run seeds 76000–76004 × default/hard. Keep LOG short: table +
  failures only (no full payload dumps; put long output in /tmp/r23-codex1/). — files: night/r23/c_matrix.py,
  night/LOG.md — accept: all rows pass 10/10, script exit 0.

## codex2 (strong)
- [x] Y1 (codex2) Clean-room Block 2 "before/after" check, written only from night/CASE_UPDATES.md lines 111–119
  (conditions of a passed episode), README "Jury adapter" (the `grader/provenance.json` paragraph) and
  docs/CONTRACT.md §2 (posting rules) / `public/policy.json`: `night/r23/provenance_rebuild.py`. For each episode:
  (1) rebuild the books before the error by replacing every provenance `changes[].after` journal with its `before`
  (null = journal absent) and dropping `documents_added`; check every journal and the trial balance sum to 0, AR per
  invoice equals the booked total minus applied cash, 2900 per customer ≥ 0 in base currency, nothing booked out of
  period, each in-period invoice booked once at the policy rate — i.e. zero discrepancies by the published rules;
  (2) on the published (after) books, recompute each declared issue from the before/after difference and the public
  documents alone: payment → actual allocation vs remittance, FX → amount under the policy date/rate vs booked,
  period → date vs period boundary in the manifest timezone, duplicate → the same obligation booked twice; the truth
  `type`, `affected_ids` (as a set), `expected_amount_minor` and currency must equal what you derive; (3) at least one
  evidence set per issue contains only public ids from which you can recompute the amount. Seeds 72000–72099 ×
  default, hard and D01–D20 both difficulties (4,200 episodes). — files: night/r23/provenance_rebuild.py,
  night/LOG.md — accept: LOG table scenario × condition → holds N/M; every failure quoted with seed, difficulty,
  issue and ids; script exits 1 on any failure. If a condition cannot be checked from the documented provenance
  format, say exactly which fact is missing (that is a finding too).
- [x] Y2 (codex2) Engineering anchors as a strict jury member (CASE_UPDATES lines 168–175): for each of the five
  criteria give 0/1/2 with evidence (file:line, command + its output). Specifically check: the single README command
  on a fresh clone in /tmp/r23-codex2/clone (no undocumented step); `trajectories.jsonl` at the repo root has
  episode_id, step, action, observation, reward, terminated, truncated on every line and no truth value in any
  observation (scan for every truth `affected_ids` element that is not a public id, every `expected_amount_minor`
  string, `issue_id`, `ISS-`, `seed`, `provenance`, `evidence_sets`); config versions (configs/*.json,
  generator_version, uv.lock, Python pin) suffice to regenerate `episodes/` byte for byte; the measured failure
  analysis names a failure, its cause and a re-check. — files: night/LOG.md (scripts under /tmp/r23-codex2/) —
  accept: LOG table criterion → score → evidence; anything below 2 with the exact fix proposed (text or command).
- [x] Y3 (codex2, after FIX) Re-run `night/r23/provenance_rebuild.py` on seeds 72000–72099 and 74000–74099 (all
  scenarios, both difficulties). Do not loosen the evidence check; if it needs the new published rule text, read it
  from policy.json. — files: night/r23/provenance_rebuild.py, night/LOG.md — accept: evidence N/N in every row
  (expected 4,200/4,200 per range); any failure quoted with seed/issue/ids.
- [x] Y4 (codex2, after FIX) Strict review of the FIX COMMIT diff: can a reader of the new set alone (two docs, the
  payment's journal rows, the invoice-date rate) derive expected − posted for every nothing-allocated issue, incl.
  merged receipts, foreign payments and I1 cases? Count on seeds 0–999 × default/hard/D09/D11: sets > 10 ids
  (expected 0), sets whose rows do not balance (expected 0), sets with an AR credit to the invoice (expected 0).
  — files: night/LOG.md (script under /tmp/r23-codex2/) — accept: three counts + verdict; any wording fix as exact
  replacement text.

## rb (medium)
- [x] Z1 (rb) Re-run the existing independent checkers on unseen seeds:
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.ledger_identity --classify --seeds 62000-62299`,
  (text_auditor moved to codex1 X3 — it needs the new evidence rule first)
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r22.d_matrix --seeds 65000-65199` — files: night/LOG.md
  — accept: exit codes, summary lines verbatim; clean violations 0, F1 1.000 with 0 discrepancies, 0 failed checks;
  anything else quoted with seed/config/ids.
- [x] Z2 (rb) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/policy_text.py --seeds 64000-64199`,
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py --seeds 64000-64299`,
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r22.paired_cleanroom --seeds 66000-66009` — files:
  night/LOG.md — accept: as Z1 (0 unexpected failures, 0 unexplained clean violations, all pairs equal).
- [x] Z3 (rb) Fresh-clone README walk: `git clone` this repo's branch into /tmp/r23-rb/clone (use
  `git clone --branch night/2026-11-22-r23 <local repo path>`), then run every command in README.md that starts with
  `uv run` / `make` / `env` (skip docker, network and anything needing a key you don't have; say which you skipped)
  from the clone root. — files: night/LOG.md — accept: LOG table command → exit code → wall time; every non-zero exit
  quoted with its last 10 lines.
- [x] Z4 (rb, after FIX) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py`,
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.extreme_configs`,
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.jury_copy`,
  `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 37000` — files: night/LOG.md — accept: exit
  codes + summaries; reconcile F1 < 1 or flag_all > −0.5 called out.

## gemini1a (evidence only, files: night/LOG.md)
- [x] G1 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 19000-19999` and the same with
  `--hard` — accept: both summary lines + wall times; any problem line verbatim.
- [x] G2 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 87000` — accept:
  summary + wall time + max steps.
- [x] G14 (gemini1a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 21000-21999` and the
  same with `--hard` — accept: both summaries + wall times.

## gemini1b (evidence only, files: night/LOG.md)
- [x] G3 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 14000-14299` and
  `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 14000-14299` —
  accept: per command the summary line + wall time.
- [x] G4 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 20000-20999` and the same with
  `--hard` — accept: both summaries + wall times.
- [x] G15 (gemini1b, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds
  15000-15299`, the same with `--hard --stress reconcile_hard`, and `env -u AUDITENV_SECRET uv run python -m
  auditenv.fuzz --configs 3000 --start 93000` — accept: summaries + wall times + max steps.

## gemini2a (evidence only, files: night/LOG.md)
- [x] G5 (gemini2a) `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 10000-11999` — accept: last line +
  wall time.
- [x] G6 (gemini2a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 90000` — accept:
  summary + wall time + max steps.
- [x] G16 (gemini2a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 12000-13999` —
  accept: last line + wall time.

## gemini2b (evidence only, files: night/LOG.md)
- [x] G7 (gemini2b) Re-export into scratch dirs and diff against the committed exports: for each split
  (dev → configs/dev.json, train → configs/train.json, hard → configs/eval_hard.json)
  `env -u AUDITENV_SECRET uv run python -m auditenv.export --config <cfg> --out /tmp/r23-gemini2b/<split>` then
  `diff -r episodes/<split> /tmp/r23-gemini2b/<split>` — accept: per split the diff exit code (expected 0).
- [x] G8 (gemini2b) `uv run python scripts/golden.py --check`, `uv run python scripts/mutate_reward.py`,
  `uv run python scripts/shortcut_miner.py --seeds 6000-6999 --report-only` and the same with `--hard` — accept:
  summary lines + exit codes; any miner value with precision > 0.5 that is NOT in docs/DESIGN.md §10 called out.
- [x] G17 (gemini2b, after FIX) Repeat G7 (re-export diff, all three splits) and G8 (golden, mutate_reward, miner
  seeds 7000–7999 default and `--hard`) on the FIX head — accept: as G7/G8.

## gemini3a (evidence only, files: night/LOG.md)
- [x] G9 (gemini3a) Four jury modules under three hash seeds: for H in 0 1 12345:
  `PYTHONHASHSEED=$H env -u AUDITENV_SECRET uv run python -m unittest tests.test_judge_contract tests.test_judge_reward
  tests.test_judge_scenarios tests.test_judge_paired` — accept: per run `Ran N tests` + result.
- [x] G10 (gemini3a) `env -u AUDITENV_SECRET uv run python -m auditenv.attack` and `uv run python scripts/sensitivity.py`
  — accept: summaries + exit codes; sensitivity values compared with the docs/DESIGN.md §6 table, differences called out.
- [x] G18 (gemini3a, after FIX) Four jury modules once, `env -u AUDITENV_SECRET uv run python -m auditenv.attack`,
  `uv run python scripts/sensitivity.py` (compare with docs/DESIGN.md §6: naive dev −0.516/−0.529/−0.569, naive hard
  −0.704/−0.725/−0.786) — accept: summaries + exit codes, differences called out.

## gemini3b (evidence only, files: night/LOG.md)
- [x] G11 (gemini3b) `uv run python -m auditenv.verify --dir episodes/<split>` for every directory under episodes/ —
  accept: per split the `N/N episodes valid` line.
- [x] G12 (gemini3b) `yes '' | uv run python -m auditenv.demo` — accept: exit code, final reward/score lines quoted;
  compare with the numbers in docs/DEMO.md and call out any difference.
- [x] G13 (gemini3b) `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 34000` and the same for
  35000, 36000 — accept: per run the policy table; call out oracle F1 < 1, reconcile F1 < 1, or random/flag_all
  return > -0.5.
- [x] G19 (gemini3b, after FIX) G11 + G12 again, then `env -u AUDITENV_SECRET uv run python -m auditenv.check --json
  /tmp/r23-gemini3b/c.json` and `uv run python scripts/sync_docs.py --check --json /tmp/r23-gemini3b/c.json` —
  accept: N/N per split, demo numbers equal docs/DEMO.md, check exit 0, no drift.

## lead
- [x] L1 (lead) Baseline: `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r23-lead-check.json` and
  `scripts/sync_docs.py --check` — accept: exit 0, no drift.
- [x] L2 (lead) Red-team passes (subagents, read-only first): (a) judge_adapter + env against CASE_UPDATES Block 1/3
  boundary rules; (b) data: contradictory/unresolvable public data and evidence sufficiency on D01–D20; (c) jury-facing
  docs claims (README "For the jury", "Jury adapter", "Honest limitations", DESIGN §9–10) against the code. Fix
  every confirmed defect test-first — files: as found, REVIEW.md — accept: REVIEW.md "Round 23" with evidence;
  `auditenv.check` exit 0.
- [x] L3 (lead) Merge worker branches, review, fix what the clean-room checkers find (test-first) — accept: check
  exit 0 after each merge.
- [x] L4 (lead) `docs/DEMO.md` re-verified against a fresh demo run — accept: every number matches.
- [x] L5 (lead) `docs/PITCH.md` re-verified against check/analyze/fuzz output; REVIEW "Round 23", HANDOFF, night/DONE —
  accept: `sync_docs --check` no drift, check exit 0.
