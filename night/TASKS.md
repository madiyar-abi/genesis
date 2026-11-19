# TASKS — round 2 (polish run, night/2026-11-19-r2)

Goals: `night/ROUND2.md`. Ideas: `HANDOFF.md` → "Ideas to improve".
Format: `- [ ] ID (owner) task — files: <paths> — accept: <check>`. `[x]` only after the check passed.
Every task also requires: `uv run python -m auditenv.check` exit 0 (workers may run the unit tests
`uv run python -m unittest discover -s tests -t .` instead if check is slow). Never change the reset/step
contract, actions, findings format or the shared reward (`matcher.py`, `metrics.py` logic). Stdlib only.
Workers: touch ONLY the files listed for your task.

## Block 1 — reward / contract / isolation
- [ ] R2 (codex) Mutation testing of the reward: new `scripts/mutate_reward.py` applies ~15 single-line source
  mutations, one at a time, to an in-memory copy of `auditenv/matcher.py` and `auditenv/metrics.py` (e.g. flip
  `<=`/`<`, change tolerance constant, drop a check in `_checks`, swap precision/recall, remove dedup, change step
  cost), writes the mutated module to a temp dir copy of the package (never edit the real files), runs
  `python -m unittest tests.test_matcher tests.test_reward_attacks tests.test_jury tests.test_metrics` against it,
  and prints a table mutant → killed/survived; exit 1 if any mutant survives. If a mutant survives, add a test that
  kills it to `tests/test_reward_attacks.py` (the test must pass on the real code) — files: scripts/mutate_reward.py,
  tests/test_reward_attacks.py, tests/test_mutate_reward.py (smoke test: the script's mutant list is non-empty and
  every mutation pattern matches the source exactly once) — accept: `uv run python scripts/mutate_reward.py` exit 0,
  all mutants killed; `uv run python -m unittest tests.test_mutate_reward tests.test_reward_attacks` green
- [ ] C3 (codex) Injectable clock for the 60 s limit: `AuditEnv(clock=time.monotonic)` — optional constructor
  argument, default unchanged; replace the three `time.monotonic()` calls in `auditenv/env.py` with `self._clock()`.
  New `tests/test_clock.py` with a fake clock: (a) a step at elapsed 59.9 s works, (b) the first step after 60.0+ s
  returns error code `time_limit`, truncated=True, terminated=False, empty-answer grade in train mode, (c) the step
  after that returns `episode_over`, (d) a custom `time_limit_s` in config is honoured, (e) eval mode: no reward/info
  leak on time limit (info == {} and reward == 0.0). No sleeping in tests — files: auditenv/env.py, tests/test_clock.py
  — accept: `uv run python -m unittest tests.test_clock tests.test_env` green; `uv run python -m auditenv.check` exit 0
- [ ] C2 (gemini) Bound request size and bad bytes in `auditenv/server.py`: read stdin as bytes (`sys.stdin.buffer`),
  reject any request line longer than 1 MiB (constant `MAX_LINE = 1 << 20`) with `{"error": "request too large"}`
  without parsing it, decode UTF-8 strictly and answer `{"error": "invalid utf-8"}` on failure; the server keeps
  serving after either error (next valid request works). Keep the JSON-lines protocol and all existing responses
  unchanged; `serve()` must still accept text streams used by existing tests (accept both bytes and str lines).
  Tests in `tests/test_server.py` (in-process `serve()` with io.BytesIO/StringIO, plus one subprocess test sending a
  10 MB line and invalid UTF-8 then a valid reset) — files: auditenv/server.py, tests/test_server.py — accept:
  `uv run python -m unittest tests.test_server` green; `uv run python -m auditenv.check` exit 0 (remote gate passes)

## Block 2 — reproducibility / data
- [ ] P1 (gemini) Golden hashes: new `scripts/golden.py` computes sha256 of `json.dumps(generate(seed, config),
  sort_keys=True, separators=(",", ":"))` for seeds 0–19 × configs [default `{}`, `{"errors": {}}`,
  `{"difficulty": "hard"}`, `{"transform_seed": 7}`] (80 hashes) and writes `tests/golden_hashes.json`
  (`{"<config-json>|<seed>": "<hex>"}`); `--check` mode compares and exits 1 on drift. New `tests/test_golden.py`
  recomputes all 80 and asserts equality, with a message telling to run `scripts/golden.py` after an intended
  generator change (and to re-export episodes). Use `from auditenv.generator import generate` — files:
  scripts/golden.py, tests/golden_hashes.json, tests/test_golden.py — accept: `uv run python -m unittest
  tests.test_golden` green and < 20 s; `uv run python scripts/golden.py --check` exit 0
- [x] P2 (lead) Paired checks for hard mode inside `auditenv.check` (seed replay + transform keeps oracle reward,
  hard config); confirm transform shuffles FX (it does) — files: auditenv/check.py, tests/ — accept: check prints the
  hard paired gate and exits 0
- [ ] D4 (lead) Shortcut miner: new `scripts/shortcut_miner.py` — for each truth issue type, single-column predictors
  (hour, weekday, id format/suffix, amount pattern, row position, description tokens) on 1 000 seeds; report max
  precision; fix any leak > 0.5 in the generator (re-export) — files: scripts/shortcut_miner.py, generator/inject
  if needed — accept: miner reports no column > 0.5 (or documented why acceptable)
- [ ] D2 (lead) Decide/document "nothing allocated" evidence for payment_allocation (DESIGN §7) — files:
  docs/DESIGN.md (+ inject/verify if changed) — accept: verify 0 problems, decision in DESIGN

## Block 3 — measured design / engineering
- [ ] E2 (gemini) Timing benchmark: new `scripts/bench.py` measures wall time (time.perf_counter, median of 3) of
  (a) `generate()` for seeds 0–99 default and hard, (b) one full episode per policy (`auditenv.run` APIs) on
  `configs/dev.json` and `configs/eval_hard.json`, (c) `auditenv.verify` over seeds 0–99; prints a markdown table
  and with `--json PATH` writes the numbers; prints Python version and `platform.platform()`. Do NOT edit docs — the
  lead pastes the table into DESIGN — files: scripts/bench.py, tests/test_bench.py (smoke test running a tiny
  subset via a function call, < 10 s) — accept: `uv run python scripts/bench.py` prints the table, exit 0;
  `uv run python -m unittest tests.test_bench` green
- [ ] E3a (codex) Makefile targets `fuzz` (`uv run python -m auditenv.fuzz --seeds 0-999`), `stress`
  (`uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299` and the hard variant `--hard --stress
  reconcile_hard --seeds 0-299` if `--hard` supports it — check `auditenv/fuzz.py`), `attack`
  (`uv run python -m auditenv.attack`), `golden` (`uv run python scripts/golden.py --check`), `mutate`
  (`uv run python scripts/mutate_reward.py`), `.PHONY` updated — files: Makefile — accept: `make -n fuzz stress attack`
  prints the commands; `make fuzz` exit 0
- [ ] R3 (lead) Sensitivity table: baseline ranking under step cost 0.001/0.002/0.005 and tolerance 0/0.1 %/1 %
  (grader-side param in analysis only, shared reward unchanged) — files: auditenv/analyze.py or scripts/, DESIGN §6 —
  accept: table in DESIGN, ranking stated
- [ ] H2 (lead) Step-budget margin with 100 invoices + 12 issues (+ hard) via `fuzz --stress`; keep max ≤ 80 —
  files: DESIGN — accept: numbers in DESIGN from the stress output
- [ ] E3b (lead) Hard-mode trajectories `trajectories/train_hard_*.jsonl`, CI badge in README — files: README.md,
  trajectories/, tests — accept: test_trajectory_files green
- [ ] E4 (lead) Stdlib SVG chart of baseline returns (dev vs hard) for the pitch: `scripts/chart.py` →
  `docs/baselines.svg` from `check --json` — files: scripts/chart.py, docs/baselines.svg, docs/PITCH.md — accept:
  SVG renders, numbers match check

## Block 4 — optional (only if 1–3 done)
- [ ] H1 (lead) "expert" difficulty (opt-in) — accept: new check gates, default episodes byte-identical
- [ ] E5 (lead) Rule-search baseline — last, skip if short on time

## Jury materials (last)
- [ ] J1 (lead) `docs/DEMO.md` — demo-video script: 2–3 min, numbered steps, exact commands, what to say, which
  result to show; refresh for round-2 features — files: docs/DEMO.md — accept: every command runs
- [ ] J2 (lead) `docs/PITCH.md` — slide outline: problem → solution → live demo → how it works → results/metrics →
  what's next → team; ≤ 4 bullets per slide, facts from the code; refresh numbers — files: docs/PITCH.md — accept:
  numbers match check output (`scripts/sync_docs.py --check`)
