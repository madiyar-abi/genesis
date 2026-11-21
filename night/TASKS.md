# Round 20

Open improvement round (freeze 2026-11-22 18:00). Rounds 1–19 hardened contract, data, reward, the jury adapter and
docs (night/archive/, REVIEW.md). Round 19 showed that green sweeps can still miss *ordinary-use* defects (a refund
dated before its receipt; hidden server queues keyed publicly) — so this round hunts for such defects with
independent checkers, plus fresh evidence on unseen seeds.

Rules for workers: run from the repo root, prefix every module with `env -u AUDITENV_SECRET uv run python -m ...`.
`git fetch && git merge origin/night/2026-11-22-r20` before each task. Touch only your listed files plus
night/TASKS.md (your own `[x]`) and night/LOG.md (append, `date '+%F %H:%M'` timestamp). Never edit README.md,
HANDOFF.md, REVIEW.md, docs/, auditenv/, episodes/, trajectories/ unless your task lists them. Scratch files only
under /tmp/r20-<your name>/. Evidence tasks: record exact command, exit code, wall time and the summary line(s);
quote any failure verbatim. If something fails, do NOT fix product code — log it with a reproduction; the lead fixes.
Audit scripts go under `night/r20/` (one file per task, named in the task) and must only read the *public* episode
files (task.txt, policy.json, CSV/JSONL tables) — never truth, verify.py, inject.py or policies.

## codex1 — independent defect hunts (strong)
- [ ] X1 (codex1) Chronology and causality audit. Write `night/r20/chronology.py`: generate episodes in memory via
  `auditenv.generator` (public tables only) for default, `--hard` and every D01–D20 config in `auditenv/jury.py`
  (both difficulties), seeds 30000–30299. Check from the public tables only: every payment / credit note / refund /
  reversal is dated on or after the document it references; a reversal follows its original posting; every
  refund ≤ the customer's running credit in the payment currency at that time; every ledger posting timestamp is
  within the period or is explicitly a cutoff/period error the policy text describes; an FX rate exists for every
  (date, currency) the policy says to use. — files: night/r20/chronology.py, night/LOG.md — accept: script exits 0
  when no violation; LOG lists counts per check × config and every violation with config, seed and record ids.
- [ ] X2 (codex1) Policy text vs data audit. Read task.txt and policy.json of 5 default + 5 hard + 10 scenario
  episodes. For every sentence that states a rule or a fact (terms, tolerance, currency, period, which rate to use,
  what counts as an issue), write a check in `night/r20/policy_text.py` that tests the statement against the public
  data on seeds 31000–31199 of each config. — files: night/r20/policy_text.py, night/LOG.md — accept: LOG lists every
  sentence checked, the check and its count; any statement the data contradicts (or that is unstated but needed to
  find a truth issue) quoted with seed and record ids.
- [ ] X3 (codex1) Jury-machine reality check of `judge_adapter.py`: (a) fresh `HOME` with no `~/.auditenv`, (b) read-only
  `HOME`, (c) 8 processes calling `judge_adapter.generate_episode` + `reset` at the same moment on an empty key dir
  (race on `grader.key` creation — do all 8 agree on one key, does any crash or write a partial key?), (d) `episode_dir`
  given as a relative path, a path with spaces and non-ASCII, and a symlinked directory. Scripts in
  `night/r20/adapter_reality.py`. — files: night/r20/adapter_reality.py, night/LOG.md — accept: each case's result in
  LOG; any crash, disagreement or leak of a path/key into an observation quoted with a reproduction.

## codex2 — docs claims and fresh-clone runs (strong)
- [ ] Y1 (codex2) Fresh-clone sweep: `git clone /Users/caliskan/Projects/genesis /tmp/r20-codex2/clone` at
  origin/night/2026-11-22-r20, then run every shell command in fenced blocks of README.md, docs/DEMO.md and
  docs/CONTRACT.md (skip docker, git clone of GitHub, asciinema, the organiser server and commands needing
  `AUDITENV_SECRET` unless they say how to set it) — files: night/LOG.md — accept: LOG table: command, exit code,
  wall time; every non-zero exit or output that differs from what the doc says it prints quoted verbatim.
- [ ] Y2 (codex2) Claims audit of README.md sections "For the jury" and "Jury adapter" and docs/CONTRACT.md: for every
  factual claim (a number, a behaviour, an error code, a key name, a default) find the code line or run the command
  that proves it. — files: night/LOG.md — accept: LOG lists each wrong or unprovable claim with the file:line of the
  doc, the evidence (code file:line or command output) and the correct text; "0 wrong claims" is a valid result
  only with the number of claims checked.
- [ ] Y3 (codex2) Same as Y2 for docs/DESIGN.md and docs/PITCH.md (numbers must come from
  `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r20-codex2/c.json`, `auditenv.analyze`,
  `auditenv.fuzz`). — files: night/LOG.md — accept: as Y2.

## rb — adapter-level evidence (medium)
- [ ] Z1 (rb) Play every D01–D20 scenario through `judge_adapter` (closed mode, `generate_episode` with seeds
  32000–32004 each, both difficulties) with the oracle-from-records policy `reconcile` / `reconcile_hard` and with
  `flag_all`; write `night/r20/scenarios_adapter.py`. — files: night/r20/scenarios_adapter.py, night/LOG.md — accept:
  table in LOG: scenario × difficulty → mean grader score of each policy; call out any scenario where reconcile
  scores < the documented value in README or flag_all scores > 0.
- [ ] Z2 (rb) `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base <B> --json /tmp/r20-rb/j<B>.json`
  for B in 20000, 21000, 22000, 23000 — files: night/LOG.md — accept: per run the policy table in LOG; call out any run
  where oracle F1 < 1, reconcile F1 < 1, or random/flag_all return > -0.5.

## gemini1a — seed sweeps (evidence only, files: night/LOG.md)
- [x] G1 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 10000-10999` and the same with
  `--hard` — files: night/LOG.md — accept: both summaries + wall times in LOG; any problem line verbatim.
- [x] G2 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 60000` — files:
  night/LOG.md — accept: summary + wall time + max steps in LOG.
- [x] G3 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 2000-2999` — files: night/LOG.md —
  accept: last line (`N/N episodes valid`) in LOG.

## gemini1b — stress solvability (evidence only, files: night/LOG.md)
- [x] G4 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 8000-8299` and
  `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 8000-8299` — files:
  night/LOG.md — accept: per command the summary line + wall time in LOG.
- [x] G5 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 11000-11999` and the same with
  `--hard` — files: night/LOG.md — accept: both summaries + wall times; any problem line verbatim.
- [x] G6 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 63000` — files:
  night/LOG.md — accept: summary + wall time + max steps in LOG.

## gemini2a — determinism (evidence only, files: night/LOG.md)
- [ ] G7 (gemini2a) Full unit suite three times: `PYTHONHASHSEED=1 TZ=UTC env -u AUDITENV_SECRET uv run python -m
  unittest discover -s tests -t .`, then `PYTHONHASHSEED=4242 TZ=Asia/Almaty ...`, then `PYTHONHASHSEED=random
  TZ=Pacific/Kiritimati ...` — files: night/LOG.md — accept: per run `Ran N tests`, OK/FAILED, wall time; failures
  verbatim.
- [ ] G8 (gemini2a) `env -u AUDITENV_SECRET uv run python -m auditenv.check` twice while
  `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 0-999 --hard` runs in the background — files:
  night/LOG.md — accept: both exit codes, last lines, wall times; any timing failure verbatim.
- [ ] G9 (gemini2a) `LC_ALL=C LANG=C env -u AUDITENV_SECRET uv run python -m auditenv.check` and
  `LC_ALL=tr_TR.UTF-8 env -u AUDITENV_SECRET uv run python -m auditenv.check` — files: night/LOG.md — accept: both
  exit codes, last lines, wall times.

## gemini2b — golden and export reproducibility (evidence only, files: night/LOG.md)
- [ ] G10 (gemini2b) Re-export into scratch dirs and diff against the committed exports:
  `env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/dev.json --out /tmp/r20-gemini2b/dev`
  then `diff -r episodes/dev /tmp/r20-gemini2b/dev`; same for train, train_hard and eval_hard (use the `--out` dirs
  and the committed dir names from README) — files: night/LOG.md — accept: per split the diff exit code; any
  differing file named.
- [ ] G11 (gemini2b) `uv run python scripts/golden.py --check` and `uv run python scripts/mutate_reward.py` — files:
  night/LOG.md — accept: both summary lines and exit codes in LOG.
- [ ] G12 (gemini2b) `uv run python scripts/shortcut_miner.py` (see its `--help`) — files: night/LOG.md — accept:
  printed table in LOG; any column with precision > 0.5 that is NOT listed in docs/DESIGN.md §10 called out.

## gemini3a — jury modules repeat (evidence only, files: night/LOG.md)
- [ ] G13 (gemini3a) Four jury modules 5 times in a row: `env -u AUDITENV_SECRET uv run python -m unittest
  tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired` — files:
  night/LOG.md — accept: per run `Ran N tests` + result; any differing run verbatim.
- [ ] G14 (gemini3a) `env -u AUDITENV_SECRET uv run python -m auditenv.attack` and
  `uv run python scripts/sensitivity.py` — files: night/LOG.md — accept: summaries + exit codes.
- [ ] G15 (gemini3a) Red-team modules 10 times: `env -u AUDITENV_SECRET uv run python -m unittest
  tests.test_load_redteam tests.test_server_redteam tests.test_jury_run` in a `for i in $(seq 10)` loop — files:
  night/LOG.md — accept: per run `Ran N tests` + OK/FAILED + wall time.

## gemini3b — verify on exports and demo (evidence only, files: night/LOG.md)
- [ ] G16 (gemini3b) `uv run python -m auditenv.verify --dir episodes/<split>` for every directory under episodes/
  — files: night/LOG.md — accept: per split the `N/N episodes valid` line.
- [ ] G17 (gemini3b) `uv run python -m auditenv.demo` piped with enough newlines (`yes '' | ...`), and
  `uv run python -m auditenv.demo --help` — files: night/LOG.md — accept: exit code, the final reward/score lines
  quoted; compare them with the numbers in docs/DEMO.md and call out any difference.
- [ ] G18 (gemini3b) `uv run python scripts/sync_docs.py --check --json /tmp/r20-gemini3b/c.json` after
  `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r20-gemini3b/c.json` — files: night/LOG.md —
  accept: both exit codes; any drift line verbatim.

## lead
- [ ] L1 (lead) Baseline: full check on the round start; review worker findings, fix every real defect test-first,
  re-export if the generator changes — files: as needed — accept: `env -u AUDITENV_SECRET uv run python -m auditenv.check` exit 0.
- [ ] L2 (lead) Record Round 20 findings with evidence in REVIEW.md, sync doc numbers (`scripts/sync_docs.py`),
  update HANDOFF.md — files: REVIEW.md, HANDOFF.md, README.md, docs/ — accept: sync_docs --check no drift.
- [x] D (lead) `docs/DEMO.md` — re-verify the numbered 2–3 min recording script against the actual demo output — accept:
  every number in it reproduced.
- [x] P (lead) `docs/PITCH.md` — re-verify slide outline facts and numbers against the current check output — accept:
  every number matches.
