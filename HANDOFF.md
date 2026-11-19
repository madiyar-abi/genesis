# HANDOFF.md — start here

> Current state of the project for the next person (human or agent).
> Read this first after `git pull`. Keep it short and true.
> Updated after every finished task (by the night agent or by you).

**19 November 2026 · Khasuetolog** implemented R1, C1, D1, D3, P3 and E1 in commit `66a3504` on `audit/handoff-validation`. The six results and reproduction commands are below. [PR #11 into main](https://github.com/madiyar-abi/genesis/pull/11)

## Deadline & submission
Genesis Hackathon, online stage. **Cases are published on the hackathon site on
2026-11-19 at 12:00.** **Final deadline: 2026-11-22, 22:00 (Astana; the PDF says 23:59, we plan for 22:00).**
Results: 7 teams per case (14 finalists) go to the offline final in Astana,
planned for 2026-11-28/29 (exact dates and venue TBA).

Submit via the personal account on the hackathon site: a link to **one Google
Docs document** with three links in it — GitHub repo, demo video, presentation.
Every material must be viewable by anyone with the link. (The earlier
`submit.exe` form asked for a Google Drive folder; the organizers' latest
message says a Google Doc — follow the latest, re-check the form before submitting.)

- [x] Working end-to-end demo flow (`uv run python -m auditenv.demo`)
- [x] `README.md`: what it is, how to run — the jury opens the repo
- [ ] GitHub repo viewable by the jury — **it's private now**: make it public
      (or otherwise give access) before submitting
- [ ] Demo video: short demo + explanation of the solution — script: `docs/DEMO.md`
- [ ] Presentation — 10-slide outline with numbers: `docs/PITCH.md` (fill in the Team slide)
- [ ] Google Doc with the 3 links (repo, video, presentation); the Doc and all
      three materials shared as **"Anyone with the link — Viewer"**
- [ ] Doc link submitted in the personal account on the site

## Status
**Round 2 (agent polish run) on `night/2026-11-19-r2` — all planned ideas done except the optional H1/E5
(skipped on purpose, see `night/LOG.md`).** Goals: `night/ROUND2.md`; tasks: `night/TASKS.md`.
Humans open the PR from `night/2026-11-19-r2` into `main` (the night run never touches `main`).

Round-2 results (each with its command; numbers from the current code):
- Reward: R2 `scripts/mutate_reward.py` — 15/15 one-line mutants of matcher/reward caught; R3
  `scripts/sensitivity.py` — baseline ranking unchanged for step cost 0.001–0.005 and tolerance 0–1 % (DESIGN §6).
- Contract: C3 injectable clock (`AuditEnv(clock=...)`, `tests/test_clock.py`, no sleeping); C2 server rejects
  lines > 1 MiB (read in bounded chunks) and invalid UTF-8, keeps serving (`tests/test_server.py`).
- Data: D4 `scripts/shortcut_miner.py` found a hard-mode leak (re-typed text marked duplicate copies, precision
  1.000) — fixed (0.467); hard episodes/trajectories/golden hashes regenerated, default data byte-identical; the
  residual default-mode signals are listed in DESIGN §10. D2 nothing-allocated evidence decision in DESIGN §7.
- Reproducibility: P2 check runs 20 paired checks on hard episodes too; P1 80 golden hashes
  (`scripts/golden.py --check`, `tests/test_golden.py`).
- Engineering: H2 step-budget table (max 57/100), E2 timing (`scripts/bench.py`, DESIGN §9), E3 hard trajectories
  (`configs/train_hard.json`, `trajectories/train_hard_*`), make targets, CI badge, E4 chart `docs/baselines.svg`.
- Check: `uv run python -m auditenv.check` → 276 tests, all gates PASS (≈ 24 s); fuzz 0–999 → 3 000 episodes, 0 problems.

GitHub Actions built the Docker image and passed the offline container check on the implementation commit. The manual run also exercises the two pinned Python patch versions. [Extended matrix and job results](https://github.com/madiyar-abi/genesis/actions/runs/44551717103)

## Six handoff improvements

Run these commands from the repository root with Python 3.11 (`uv run python`).

| Item | Implementation and local acceptance |
|---|---|
| R1 | `-m auditenv.attack` graded 11,000 mutations, including 5 clean seeds among 20, with 0 violations. Failures save replay inputs in `attack_failures.json`. |
| C1 | `-m tests.test_fuzz` validated 20,314 episode actions plus 205 post-terminal responses against the schema and strict JSON. Python 3.11.18, 10.898 s. |
| D1 | `-m unittest tests.test_hardening.DuplicateEvidenceTest` checks both modes and four booking-row combinations. Seed 7, four inspections, the original incomplete answer fell from TP=1 / 0.992 to TP=0 / −1. Verifier: 600/600. |
| D3 | `-m auditenv.verify --dir episodes/hard` verified 20/20. A fresh export from `configs/eval_hard.json` matched all 161 files. |
| P3 | `.github/workflows/check.yml` schedules the 0–4999 sweep at 02:00 UTC on Python 3.11.17 and 3.11.18. The same matrix runs via workflow_dispatch. |
| E1 | `-m auditenv.check --json /tmp/auditenv-metrics.json` then `scripts/sync_docs.py --check --json /tmp/auditenv-metrics.json` checks all three documents. Omit --check to refresh their tables. |

## Done
- Generator (`auditenv/generator.py`, `inject.py`): hidden company history → correct double-entry
  ledger → 4 error types + 2 interacting scenarios + clean companies + distractors; truth + provenance.
- Env (`auditenv/env.py`): JSON `reset/step`, 5 tools, 50-row pages, 100-step + 60 s limits,
  train/eval modes. Matcher + reward (`matcher.py`, `metrics.py`, `schema.py`, `calculator.py`);
  experimental materiality-weighted reward reported separately (`experimental.py`).
- Independent verifier (`verify.py`), benign transform (`transform.py`), out-of-process
  server/client (`server.py`, `client.py`), runner (`run.py`), failure analysis (`analyze.py`),
  narrated demo (`demo.py`), exporter (`export.py`), check command (`check.py`), Dockerfile, JSON schemas (`schemas/`).
- Baselines (`policies/`): random explorer, naive reconcile, reconcile, flag-all, oracle.
- Data: `configs/{train,dev,eval_example}.json`, `episodes/{train,dev,hard}` (10+10+20 exported),
  `trajectories/train_*.jsonl`.
- Docs: `README.md`, `docs/CONTRACT.md`, `docs/DESIGN.md` (with measured results), `docs/DEMO.md`, `docs/PITCH.md`.
- Hard mode (`difficulty: "hard"`, `configs/eval_hard.json`, `reconcile_hard`): reconcile F1 1.0 → 0.752, oracle 1.0.
- Jury review (`REVIEW.md`): self-sufficient `payment_allocation` evidence (episodes re-exported), `tests/test_jury.py`
  (jury checklist as 33 tests), `auditenv.fuzz` (seed sweep + `--stress`), CI with Docker, verify totals, docs pass.

## Remaining work before submission

- **Engineering:** open and merge the PR `night/2026-11-19-r2` → `main` after CI passes (PR #11 is already merged). The first scheduled nightly CI run can be checked after merge.
- **Demo and slides:** record the walkthrough from `docs/DEMO.md` and build the deck from `docs/PITCH.md` (chart: `docs/baselines.svg`), including the Team slide.
- **Access and submission:** the repository owner arranges jury access. The team checks the repo, video and presentation links, adds them to the Google Doc, and submits the Doc through the hackathon account by the internal deadline of **22 November, 22:00 Astana**.

## Decisions & assumptions
- Hidden evaluation: set `AUDITENV_SECRET` in the grader process only (keys generator RNG + HMAC episode_id).
- After ANY generator change: re-export `episodes/` and regenerate `trajectories/` (tests/test_load.py fails otherwise).
- Work goes through branches + PRs into `main`; nobody pushes to `main` directly.
- Night agent never asks questions; every assumption it makes is logged in `night/LOG.md`.
- Interfaces are fixed in `docs/CONTRACT.md` (ledger in base currency only; truth amounts are
  ledger misstatements in base currency; evidence ids = doc_id / row_id).
- Stdlib only, zero runtime dependencies; tests use `unittest`.

## Ideas to improve (for the next agent) / Идеи для улучшения

### Rules first (do not break what scores today)
- Interfaces in `docs/CONTRACT.md` are fixed: do not change the reset/step contract, actions, findings
  format or reward formula. New behaviour only behind new optional config keys (as `difficulty`).
- Default-mode episodes stay byte-identical (`tests/test_load.py` compares the committed `episodes/`).
  After any generator change: re-export `episodes/` and regenerate `trajectories/` (commands in CLAUDE.md).
- Stdlib only, Python 3.11, tests with `unittest`. No network, GPU, paid APIs, no weight training.
- Never edit `night/SPEC.md` or `night/case.pdf`.
- Run `uv run python -m auditenv.check` after every change; keep `python -m auditenv.fuzz --seeds 0-999` green.
- Every number in README/DESIGN/PITCH/DEMO must be copied from the current output of `check`, `analyze`
  or `fuzz` — re-run them after the change and update the docs in the same PR.
- Branch + PR into `main` only; never push to `main`. Deadline **2026-11-22 22:00 Astana** — stop feature
  work by the 22nd morning, leave the rest for the video and slides.
- Don't ask questions: decide, and log the decision and its reason in `night/LOG.md`; record defects in `REVIEW.md`.
- Treat each idea below as a hypothesis: reproduce or measure the problem before changing code.

### Ideas, ordered by jury weight

Columns: what to do · why (jury criterion) · start in · how to check · risk.

**Reward reliability (25)**
| # | what | why | start in | check | risk |
|---|---|---|---|---|---|
| R1 ✓ | Automatic attack search: mutate the oracle answer and silence (ids, amounts at/over tolerance, evidence padded to 10 ids, wrong types/currency, duplicates, order) and search for any submission that beats the honest answer or scores > 0 on clean books | proves "атакующие ответы" beyond the 12 hand-written attacks | new `auditenv/attack.py`, `matcher.py` | new test: 10 000 mutations on 20 seeds, 0 hits; add any hit to `tests/test_reward_attacks.py` | low — read-only search |
| R2 ✓ | Mutation testing of the reward: break `matcher._checks`, `tolerance`, `prf1` one line at a time and confirm a test fails each time | shows the reward tests actually bite | `matcher.py`, `metrics.py` | small script that patches and runs `tests.test_matcher tests.test_reward_attacks tests.test_jury` | low |
| R3 ✓ | Sensitivity table: baseline ranking under step cost 0.001/0.002/0.005 and tolerance 0/0.1 %/1 % | the design choice is measured, not asserted | `analyze.py` (grader-side param), DESIGN §6 | ranking unchanged or documented | low; do not change the shared reward |

**Contract and isolation (25)**
| # | what | why | start in | check | risk |
|---|---|---|---|---|---|
| C1 ✓ | Property-based action fuzz (stdlib `random`): generate actions from the action schema plus mutations, assert every observation matches `schemas/observation.schema.json` and `json.dumps(obs, allow_nan=False)` works | covers the 20 contract checks more broadly than the previous 3 000-action fuzz | `tests/test_fuzz.py`, `tests/test_schemas.py::_matches` | ≥ 20 000 actions, < 20 s | low |
| C2 ✓ | Bound request/response size in `server.py`; test a 10 MB line and invalid UTF-8 → bounded error, server keeps serving | isolation of the closed run | `server.py`, `tests/test_server.py` | new tests | medium — do not change the JSON-lines protocol |
| C3 ✓ | Injectable clock in `AuditEnv` to test the 60 s limit without sleeping, in-process and via the server | "лимит времени" tested deterministically | `env.py` (keep default `time.monotonic`) | new tests | low |

**Data and truth (25)**
| # | what | why | start in | check | risk |
|---|---|---|---|---|---|
| D1 ✓ | Duplicate evidence includes a booking row for each invoice (the previous version only proved the later copy was booked); check it in `verify._sufficient` | "независимая достаточность доказательств" | `inject.duplicate_invoice`, `verify._sufficient` | verify 600/600, fuzz green; re-export | medium — changes truth files → re-export, re-run docs numbers |
| D2 ✓ | "Nothing allocated" allocation proven only by the 2900 row: decide whether evidence must show more, document the decision | same criterion | `inject.payment_allocation`, DESIGN §7 | as D1 | medium |
| D3 ✓ | Export the hard split to `episodes/hard` and verify it with `verify --dir` | 20 more closed episodes for the jury | `export.py`, `configs/eval_hard.json` | `verify --dir episodes/hard` 20/20 | low |
| D4 ✓ | Shortcut miner: for each truth issue type, find any single column (hour, weekday, id format, amount pattern, row order) with precision > 0.5 on 1 000 seeds | each hit is a data leak (three were already removed, see LOG) | new script, `generator.py`/`inject.py` | miner reports no column > 0.5 | medium — a fix changes the generator |

**Difficulty (part of data quality)**
| # | what | why | start in | check | risk |
|---|---|---|---|---|---|
| H1 | Harder level so that even `reconcile_hard` is < 1.0 but an oracle-from-records still reaches 1.0: legitimate near-duplicates with changed quantities, weekend FX gaps with a "last available rate" rule in `policy.json`, more distractors | a jury may still call a script-solvable env easy | `generator.py` (`difficulty: "expert"`), `policies/reconcile.py` | new check gates like hard mode; stress test with an updated rule policy = 0 imperfect | high — keep it opt-in, keep the default untouched |
| H2 ✓ | Step-budget margin: hard max is 58/100 steps; measure with 100 invoices + 12 issues + expert mode and keep max ≤ 80 | solvability within the budget | `fuzz.py --stress` | stress output | low |

**Reproducibility (15)**
| # | what | why | start in | check | risk |
|---|---|---|---|---|---|
| P1 ✓ | Golden hashes: sha256 of `generate(seed, config)` for ~50 seeds/configs in a committed file + test | catches any unintended generator drift | `tests/` | test fails on drift | low |
| P2 ✓ | Paired checks for hard mode inside `auditenv.check`; transform also shuffles the FX table | "перестановка ID сохраняет ответ" for every mode | `check.run_paired`, `transform.py` | check gate | low |
| P3 ✓ | CI matrix: two Python 3.11 patch versions, more seeds (`fuzz --seeds 0-4999`) on a nightly schedule | reproducibility evidence | `.github/workflows/check.yml` | green CI | low (Actions minutes of the repo owner) |

**Engineering and explanation (10)**
| # | what | why | start in | check | risk |
|---|---|---|---|---|---|
| E1 ✓ | Docs from data: `check --json` → script rewrites the tables in README/DESIGN/PITCH; a test fails when docs drift | numbers always match | `check.py`, new `scripts/sync_docs.py` | test | low |
| E2 ✓ | Timing benchmark (`check`, `fuzz`, one episode per policy) recorded in DESIGN | "измеренный разбор" | `fuzz.py` | numbers in DESIGN | low |
| E3 ✓ | Hard-mode trajectories (`trajectories/train_hard_*.jsonl`), `make fuzz`/`make stress`, CI badge, Docker image pinned by digest | engineering polish | `run.py`, `Makefile`, README, `Dockerfile` | CI green | low |
| E4 ✓ | Demo and pitch: asciinema/GIF of `auditenv.demo`, one chart of baseline returns (dev vs hard) for slide 7 | the video and slides score with humans | `docs/DEMO.md`, `docs/PITCH.md` | renders | low |
| E5 | A learnable baseline without weights: a search over simple rule programs scored by the reward on train, reported on dev/hard (learning curve by iterations) — shows the env is learnable, not only scriptable. Skip if it looks like "training a model" to the jury | explanation | new `policies/rule_search.py` | dev/hard table | medium — time sink; do it last |

## How to run
```bash
uv run python -m auditenv.check                       # everything: tests, verifier, baselines, paired, remote
uv run python -m auditenv.demo --pause                # narrated demo for the video
uv run python -m unittest discover -s tests -t .      # unit tests only
uv run python -m auditenv.verify --seeds 0-199        # data/truth verifier
uv run python -m auditenv.run --policy reconcile --config configs/dev.json --out /tmp/traj.jsonl
uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json
uv run python -m auditenv.fuzz --seeds 0-999          # seed sweep (3 000 episodes, ~45 s)
uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299
```
No `uv`: `python3.11 -m auditenv.check` from the repo root. Docker: `docker build -t auditenv . && docker run --rm --network none auditenv`
(verified in CI; Docker is not installed on the dev Mac).

## How to continue (process for the next person)
1. `git pull` → read this file → open `night/TASKS.md`.
2. Take the first unchecked task `- [ ]` (or a `[!]` one that got stuck — see
   `night/LOG.md` for why). Put your name next to it so nobody doubles up.
3. Branch from the latest work: `git checkout -b <your-name>/<task-id> origin/<branch above>`.
4. Do the task, check its acceptance criterion, mark it `[x]`.
5. Update this file (Status / Done / Left / Last updated), commit, push,
   open a PR into the branch above (or into `main` if the night branch is merged).
