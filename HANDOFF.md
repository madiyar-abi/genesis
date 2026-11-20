# HANDOFF.md — start here

> Current state of the project for the next person (human or agent).
> Read this first after `git pull`. Keep it short and true.
> Updated after every finished task (by the night agent or by you).

**Current state (20 November 2026):** `main` has rounds 1–15 merged. Round 16 is complete on
`night/2026-11-20-r16` and goes to `main` through the marathon PR. The marathon (`scripts/marathon.sh`) opens one round
after another until the feature freeze on **2026-11-22 18:00**. Each round merges through a PR after CI passes.
`uv run python -m auditenv.check` passes (385 tests, all gates, about 40 s). After the freeze, only the human
submission steps listed below remain.

## Round 17 in progress

The seed-2003 demo script matches a fresh run (four matches, return 0.958). Worker assignments and outstanding verification are in `night/TASKS.md`.

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

## Round 16 complete · 20 November 2026

Branch `night/2026-11-20-r16`. Run `env -u AUDITENV_SECRET uv run python -m auditenv.check`. The check passes with
385 tests, and `scripts/sync_docs.py --check` finds no drift. Three red-team subagent passes (reward/contract,
data/verifier, check-gate false passes) found six defects, all fixed test-first; reproductions are in `REVIEW.md` → "Round 16".

- T7. A submission claiming 0 and `10**400` made the experimental reward raise `OverflowError`, so the episode ended
  ungraded with reward 0 and no grader-log line. Anyone below 0 could take that 0 instead, and in eval it hid an
  episode. It is now graded (−1) and logged.
- T8. The JSON-lines server abandoned the open episode before validating a new reset's config, so a typo scored the
  episode −1. A rejected reset now leaves the episode open, as it does in process (CONTRACT §4).
- T9. Exported `public/` files lacked the task text, the only place the duplicate definition and the hard-mode
  re-typing rule are stated. Every export now has `public/task.txt`, and the loader round-trips the full episode.
- T10–T12. The checks now byte-compare all three committed export splits with a fresh export (before, only hard;
  a truth copy planted in `public/` passed). They regenerate the seven trajectory files and compare bytes (before,
  swapping two files passed). The unit-test gate fails on zero discovered tests.
- T5, T6. DESIGN no longer hard-codes a stale test count. The README's "Honest limitations" now lists the measured
  limitations (simplified books, rule-script solvability, the 0.996 default duplicate cue, no trained model).
- Evidence on new seeds, no code change: 44,000 attack mutations with step cost on seeds 4000–4019 found 0 violations.
  The 6000–6999 fuzz sweep found 0 problems in 6,000 episodes. Stress runs on 4000–4299 gave 0 imperfect episodes out
  of 2,400 (max 33 / 57 steps). A fresh clone ran all 29 README `uv run` commands with exit 0. The deepseek worker still has no API key, so
  the lead ran its task. DEMO numbers are unchanged; PITCH slide 8 now mentions the byte-for-byte regeneration.

## Round 15 complete · 20 November 2026

Branch `night/2026-11-20-r15`. Run `env -u AUDITENV_SECRET uv run python -m auditenv.check`. The check passes with
380 tests, and `scripts/sync_docs.py --check` finds no drift.

- T1. The JSON-lines server answered a non-object request with an internal `AttributeError` name and accepted
  `NaN` / `Infinity`. Non-object requests now get `request must be a JSON object`. Malformed JSON, non-standard
  constants and over-deep nesting get `invalid json`, and the server keeps serving (`tests/test_server.py`).
- T6. The top of this file now gives the current state, and the repo's private visibility is flagged.
- T7, T8. The demo script and the slide outline were re-checked against fresh demo and check output, and every
  number matched.
- T2–T5 (evidence on new seeds, no code change): fuzz on 5000–5999 found 0 problems in 6,000 default and hard
  episodes. Attack on 3000–3019 found 0 violations in 11,000 mutations. Stress on 3000–3299 gave 0 imperfect
  episodes out of 2,400, with at most 58 of 100 steps used. All 11 "How to run" commands exit 0.
- The deepseek worker fails with `set DEEPSEEK_API_KEY or supply --api-key`. A human has to provide the key in the
  environment; never put it in a file. The lead did T5.

## Round 14 complete · 20 November 2026

Branch `night/2026-11-20-r14`. Run `env -u AUDITENV_SECRET uv run python -m auditenv.check`. All eight tasks passed: 379 tests, both 20-pair gates and the out-of-process run. `scripts/sync_docs.py --check` found no drift. The marathon handles CI and PR integration. Human submission steps remain in the checklist above.

- T2. Gemini1 changed `docs/CHECKS.md` to describe the out-of-process gate as a two-episode public smoke test (seeds 7001–7002, `flag_all`), separate from the withheld cohorts. The lead checked both values against `run_remote`.

- T3. Gemini2 added the server's JSON-lines commands and the standalone smoke command to the README. The lead checked the command names against `server.py` and confirmed the smoke command exits 0.

- T4. Gemini3 found no drift between the measured JSON and the README, DESIGN and PITCH tables. The lead reran `sync_docs --check` on fresh check output and got the same result.

- T1. The official check now reports a failing assertion and restores the grader key after a discovery exception. Both regressions failed before the fix; the integrated suite passed 378 tests.

- T5. DeepSeek reported a missing API key, so the lead checked all 80 golden hashes and verified all 10 train, 10 dev and 20 hard exports.

- T6. Rehearsed the five video prompts on seed 2003. PAY-136430 shows 286 and 351331 USD minor units. The policy saw zero rewards across 22 steps and the grader matched all four findings for 0.958.

- T7. Slide 9 now quantifies the duplicate cue: 4902/4920 flagged invoices on default and 4886/13660 on hard. The ten slides, measured tables and SPEC sections 1–13 were reviewed; the submitter owns team credits, recording, deck export and access.

- T8. Dropping or adding an evidence alternative used to pass the paired gate. Both mutations now fail, reordering passes, and the integrated check passed 379 tests plus both 20-pair gates.

## Round 13 complete · 20 November 2026

Branch `night/2026-11-20-r13`. Run `env -u AUDITENV_SECRET uv run python -m auditenv.check`. All eight tasks passed. The marathon handles CI and PR integration. Human submission steps remain in the checklist above.

- T6. Rehearsed all five Enter prompts. PAY-136430 showed 286 and 351331 USD minor units. The closed grader recorded four matches after 21 inspections for a return of 0.958.

- T1. Added the public 20-company default comparison to console and JSON. The regression failed before implementation and the integrated offline run passed all 376 tests and both 20-pair gates.

- T8. Runner and server tests cover malformed seed and config values, both list formats, duplicates and ordering. All 18 focused tests and the integrated offline suite passed.

- T5. DeepSeek exited with a missing API key. The lead verified sync_docs --check with the three-split JSON and reproduced the committed chart byte for byte.

- T7. Rechecked SPEC sections 1–13, pitch metrics and README run instructions. Both 3,000-company sweeps passed, 11,000 answer mutations gave zero violations, 15/15 reward mutants were caught and all 80 golden hashes matched. The default miner still flags the documented surface cues. The submitter owns the recording, team credits, deck export and jury access.

- T4. Independently reproduced the worker’s public default results. Mean returns rounded to three decimals were 1.000 for oracle, 0.959 for reconcile, and −1.000 for both random and flag_all.

- T2. Verified the jury check map against the official console and JSON outputs and updated its reset-test count to twelve invalid requests.

- T3. Confirmed the official verifier checks 50 seeds under four configurations. The separate 200-seed command verified all 600 companies. DESIGN now gives the measured workloads and 376-test count.

## Round 12 complete · 20 November 2026

Branch `night/2026-11-20-r12`. Run `env -u AUDITENV_SECRET uv run python -m auditenv.check` from the repository root. All 374 tests and both 20-pair gates passed. The seed sweep verified 3,000 companies. The marathon handles PR integration and CI.

- T1. The verifier previously accepted 3-1 after checking zero episodes. Five command entry points now reject reversed ranges. Ordered and repeated seeds still work. The focused tests and official check passed.

- T8. A failed reset now preserves the active episode’s evaluation mode and budget. The regression failed on the old code and all 33 environment tests passed after the fix.

- T6. The rehearsed demo labels each amount in USD minor units. PAY-136430 shows $2.86 and $3,513.31. Four findings matched after 21 inspections and the closed return was 0.958.

- T5. The DeepSeek launcher exited with a configuration error, so the lead ran auditenv.verify --dir for each committed split. All 10 train, 10 dev and 20 hard companies passed.

- T7. The paired gate now compares complete translated public rows. A due-date mutation that previously passed is caught on both clean and dirty episodes. Both 20-pair suites passed and all three documentation tables matched current metrics. The submitter still needs the recording, credits, slide export and jury access.

- T3. Gemini2 regenerated the chart. The lead independently compared docs/baselines.svg byte for byte with scripts/chart.py output from the integrated check metrics.

- T2. Gemini1 and the lead independently counted generated truth. Each 20-company evaluation config contains five clean companies and five with interacting errors.

- T4. All seven trajectory files have the required fields across 2,258 records, including 70 resets. All 70 episodes terminated and none truncated.

## Round 11 complete · 20 November 2026

Work is on `night/2026-11-20-r11`. See `night/TASKS.md` for ownership and
`night/LOG.md` for verification. Run `env -u AUDITENV_SECRET uv run python -m auditenv.check`
from the repository root. This round addresses duplicate seeds in failure reports
and verifies the actions recorded in the seven published training trajectories.

- T1. Failure reports now retain each configuration sharing a seed. The full and filtered report regressions failed before the fix and pass after it. Explicit seed ordering and missing-seed errors are preserved.

- T6. The five Enter prompts in the 2:40 demo script reproduced the two PAY-136430 discrepancies, 21 inspections, four matches and a closed-run return of 0.958.

- T5. The DeepSeek launcher reported a missing API key, so the lead reassigned its export check. For split/config pairs train/train, dev/dev and hard/eval_hard, ran env -u AUDITENV_SECRET uv run python -m auditenv.export --config "configs/$cfg.json" --out "$tmpdir/$split" and diff -qr "episodes/$split" "$tmpdir/$split". All 81 train, 81 dev and 161 hard files matched.

- T3. Reviewed the hard split across both policies. Default reconciliation missed five duplicates and returned 22 unmatched false positives. The hard rules matched all 46 issues. Both averaged 43.2 actions.

- T4. Verified split-wide mean action counts against the official metrics. The timing audit identified an outdated whole-suite runtime and an unsupported per-episode upper bound. The updated timing table uses the benchmark’s actual first-company workload.

- T8. Snapshotting actions and observations fixed 40 stored invoice-list responses across three files. All 2,258 records now replay exactly. All seven files were regenerated; actions, rewards, IDs, step numbers and termination flags matched their earlier values. The mutating-policy regression and official check passed.

- T2. The official suite now replays the seven published trajectory files against the train and hard-train configs and checks every reset and transition.

- T7. Verified the pitch against measured results, including the archived 20,000-config sweep. The offline check passed 369 unit tests and both 20-pair replay suites. The README, pitch and design tables matched the official metrics.

Next, record the demo and add the confirmed team credits before exporting the slides. The marathon handles CI and PR integration.

## Round 10 complete · 20 November 2026

All eleven tasks passed on `night/2026-11-20-r10`. Run `env -u AUDITENV_SECRET uv run python -m auditenv.check` from the repository root. All 366 tests passed, along with 20 default and 20 hard paired checks.

- The new sweep sampled 20,000 configurations (8,037 hard). The independent verifier accepted every episode. The oracle and the reconciliation policy for each difficulty reached F1 1.000 within 59 actions. Replay any case N with `uv run python -m auditenv.fuzz --configs 1 --start N`.
- Reset rejects malformed config objects and counts filed under the wrong group. A subprocess test sends eight invalid requests, then successfully opens an episode on the same connection.
- Both policies solved their 4,000 stress episodes without truncation. Maximum action counts were 33 on default and 58 on hard. A separate hard sweep over seeds 1000–1999 found zero problems across 3,000 episodes.
- All 40 exported episodes and seven trajectories reproduced byte for byte. All 80 golden hashes matched. The reward suite caught 15/15 mutants and found zero violations across 11,000 answer mutations.
- The documentation now describes hard-mode sizing, credit-note eligibility and allocation evidence. The seed-2003 demo reproduced four matched findings after 21 inspections for a return of 0.958.

The marathon handles PR integration and CI. Record the walkthrough in `docs/DEMO.md`, add confirmed team names and contributions to `docs/PITCH.md`, export the deck, and complete the access and submission checklist above.

## Round 9 · 20 November 2026

Branch `night/2026-11-20-r9`, tasks in `night/TASKS.md`. A read-only red-team pass on contract, isolation, reward and reproducibility found nothing that leaks truth or beats the oracle, and three smaller defects, now fixed test-first (`REVIEW.md` → "Round 9"):
- A huge integer `time_limit_s` passed `reset` and made every `step` raise. `reset` now rejects it.
- Closing the server session logged only the open hidden episode. Every hidden episode never reset is now logged as abandoned, so stopping early cannot shrink the grader log.
- Zero-amount false positives cost nothing in the experimental materiality-weighted reward. A false positive now weighs at least the mean expected amount. The shared reward is unchanged.

A hard-mode sweep over seeds 0–999 (3,000 episodes) found 0 problems. New tests: the README Python snippets run in the suite, and episodes plus a trajectory are identical under three `PYTHONHASHSEED` values. A fresh clone passes the official check, and all 19 README "Other commands" exit 0. `docs/CONTRACT.md` now lists `generator_version` and describes cursors as `table:offset`. Episodes, trajectories and the demo numbers are unchanged.

Run `uv run python -m auditenv.check` from the repository root: 359 unit tests pass and all gates pass.

## Round 8 · 20 November 2026

Branch `night/2026-11-20-r8`, tasks in `night/TASKS.md`. The verifier now enforces the published posting policy in both the reconstructed and the published books. It checks accounts per journal type, entities, the unapplied-cash remainder of every payment and the dates against documents. It also rejects invalid invoice refs, credit notes outside the hard-mode policy and inverted invoice journals. It selects evidence rows by role and requires the policy to agree with the manifest and the contract. A seed-0 probe and an independent red-team pass found these accepted tampers (`REVIEW.md` → "Round 8"). `tests/test_ledger_policy.py` and `tests/test_verify_redteam.py` cover them. Generator-side sweeps (`tests/test_ledger_accounts.py`, `tests/test_ledger_timestamps.py`) confirm the new invariants on 200 heavy episodes. Generated data is unchanged.

Run `uv run python -m auditenv.check` from the repository root. All 355 unit tests pass, `verify --seeds 0-199` finds 600/600 valid, and the 0–4999 nightly sweep found 0 problems in 15,000 episodes. The 40 exported episodes verify, and the seed-2003 demo in `docs/DEMO.md` still matches.

## Round 7 complete · 20 November 2026

All seven tasks passed on `night/2026-11-20-r7`. The verifier now checks the signed unapplied-cash posting (account 2900) for an unidentified receipt or refund; on clean seed 7, moving such a receipt to revenue used to pass. A new test confirms every payment receivables posting names the customer of the invoice it settles: 0 mismatches across 200 heavy episodes (5,148 postings).

Run `uv run python -m auditenv.check` from the repository root. All 322 unit tests and both sets of 20 paired checks passed, and `auditenv.verify --seeds 0-199` found 600/600 episodes valid. The seed-2003 demo rehearsal passed, and both recording tabs use public companies even on a machine holding a private grading key. The published chart reproduced byte for byte. The README covers offline Python, the container check and verification of all exported splits. The jury map in `docs/CHECKS.md` resolves every referenced test.

## Round 6 complete · 20 November 2026

All seven tasks passed on `night/2026-11-20-r6`. The verifier rejects out-of-period postings in the public and reconstructed ledgers, duplicate dated FX rates, and FX evidence identifiers that disagree with the date or currency pair. The independent sweep checked 52,901 FX rows across 200 heavy episodes.

Run `uv run python -m auditenv.check` from the repository root. All 316 unit tests and both sets of 20 paired checks passed. The seed sweeps found zero problems across 3,000 default and 600 hard episodes. All 40 exported episodes verified. The miner flagged 16 default and 11 hard feature values, as documented in the design limitations.

The contract, README and pitch describe the earlier FX date that can occur on a backdated invoice. Follow `docs/DEMO.md` to record the verified seed-2003 walkthrough. The grader matched all four findings and returned 0.958. Use `docs/PITCH.md` for the deck. The marathon handles branch integration and CI. The credential owner must revoke the previously exposed DeepSeek key before sharing the repository.

## Round 5 complete · 20 November 2026

Before sharing the repository, the credential owner must revoke the DeepSeek API key exposed in Git history. The launcher now requires an explicit key.

The verifier rejects ledger postings that cite a missing payment or invoice, including balanced orphan journals. It also checks the truth episode ID and requires distinct issue IDs. Allocation evidence that cites a receivables posting must identify the payment and invoice on a positive credit.

The jury evidence map lists the checks for each scoring criterion in `docs/CHECKS.md`.

Paired checks now compare the public identifiers and row order in all four tables and reject untranslated dirty findings.

Independent verification passed for all 200 transformed heavy episodes, covering 100 seeds in each difficulty. The reproduction command is in `night/LOG.md`.

The ten-slide outline matches the integrated metrics and both interacting scenarios. The rehearsed demo in `docs/DEMO.md` identifies the two amounts on the same payment for the recording.

All nine tasks on `night/2026-11-20-r5` passed. Run `uv run python -m auditenv.check` at the repository root. All 309 tests and both sets of 20 paired checks passed. The seed sweeps found zero problems across 3,000 default and 600 hard episodes. All 80 golden hashes matched, 15/15 reward mutants were caught, and 11,000 reward mutations produced zero violations. The miner still flags 16 default and 11 hard feature values. The marathon handles PR integration and CI. Engineering freeze is 22 November at 18:00 Astana.

## Round 4 complete · 19 November 2026

All eight tasks on `night/2026-11-19-r4` passed. The verifier now compares invoice lines with quantity times unit price, counts documents directly from the public tables, and rejects empty, unreadable or incomplete indexed exports. The demo and pitch reproduce the same public company even on a machine configured with a private grader key.

Run `uv run python -m auditenv.check` from the repository root. All 295 tests passed. All 323 exported files and all 2,258 recorded trajectory steps reproduced byte for byte. Seed sweeps passed on 3,000 default and 600 hard episodes. All 80 golden hashes matched, reward tests caught all 15 mutants, and the 11,000 reward mutations produced zero violations. The shortcut miner still flags 16 default and 11 hard feature values. See the limitations in `docs/DESIGN.md` §10. [Python and offline Docker CI on the verified implementation](https://github.com/madiyar-abi/genesis/actions/runs/44591400232)

The marathon handles branch integration. The team records the demo, supplies team names, exports the deck, arranges jury access and submits the three-link Google Doc. Engineering freeze is **22 November at 18:00 Astana**.

## Round 3 complete · 19 November 2026

Demo rehearsal complete. Follow `docs/DEMO.md` for the 2:40 video. The ten-slide outline in `docs/PITCH.md` is verified against the same demo and the measured results.

Branch `night/2026-11-19-r3`. The round freeze is 22 November at 18:00 local time. Round 2 is in main. The verifier now rejects a truth amount denominated in the wrong currency. Run `uv run python -m unittest tests.test_verify` for all six verifier tests. Gemini’s jury map in `docs/CHECKS.md` matches the merged suite. The official check passed all 285 tests. All 40 exported episodes verified and both seed sweeps passed (3,000 default and 600 hard episodes). Record the demo, finish the team slide, and complete the access and submission checklist above.

## Status
Everything SPEC §07 requires is implemented and passes the official check. The current round is described at the
top of this file, and earlier rounds are archived in `night/archive/` and summarised below. Round 2's evidence is
kept here for reference.

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
- Check: `uv run python -m auditenv.check` → 283 tests, all gates PASS (≈ 24 s); fuzz 0–999 → 3 000 episodes, 0 problems.

GitHub Actions built the Docker image and passed the offline container check on the implementation commit. The manual run also exercises the two pinned Python patch versions. [Extended matrix and job results](https://github.com/madiyar-abi/genesis/actions/runs/44551717103)

## Six handoff improvements

Run these commands from the repository root with Python 3.11 (`uv run python`).

| Item | Implementation and local acceptance |
|---|---|
| R1 | `-m auditenv.attack` graded 11,000 mutations, including 5 clean seeds among 20, with 0 violations. Failures save replay inputs in `attack_failures.json`. |
| C1 | `-m tests.test_fuzz` validated 20,312 episode actions plus 205 post-terminal responses (20,314 before the round-2 strict-input fix) against the schema and strict JSON. Python 3.11.18, 10.898 s. |
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

- **Engineering:** the marathon merges each round into `main` through a PR with CI and stops at the 2026-11-22 18:00
  freeze. Before submitting, check that `main` is green (CI badge in README) and that no PR is left open.
- **Demo and slides:** record the walkthrough from `docs/DEMO.md` and build the deck from `docs/PITCH.md` (chart: `docs/baselines.svg`), including the Team slide.
- **Access and submission:** the repository is **private** (checked 2026-11-20), so the owner must make it public or
  otherwise give the jury access. The team checks the repo, video and presentation links, adds them to the Google
  Doc, and submits the Doc through the hackathon account by the internal deadline of **22 November, 22:00 Astana**.

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
uv run python scripts/mutate_reward.py                # 15/15 reward mutants caught
uv run python scripts/golden.py --check               # generator drift detector (80 hashes)
make -n fuzz stress attack miner sensitivity bench chart  # preview available targets
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
