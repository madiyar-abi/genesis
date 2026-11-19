# HANDOFF.md — start here

> Current state of the project for the next person (human or agent).
> Read this first after `git pull`. Keep it short and true.
> Updated after every finished task (by the night agent or by you).

**Last updated:** 2026-11-19 · by: Chingiz (hinabaina) + Claude · branch: `hinabaina/T19-T22` → PR into `night/2026-11-19`

## Deadline & submission
Genesis Hackathon, online stage. **Cases are published on the hackathon site on
2026-11-19 at 12:00.** **Final deadline: 2026-11-22, 22:00.**
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
- [ ] Presentation — outline: `docs/PITCH.md` (written by the night agent)
- [ ] Google Doc with the 3 links (repo, video, presentation); the Doc and all
      three materials shared as **"Anyone with the link — Viewer"**
- [ ] Doc link submitted in the personal account on the site

## Status
Environment is feature-complete for the case and passes the single check command
(`uv run python -m auditenv.check` → ALL CHECKS PASSED, ~8 s, 187 tests). Jury materials are written and re-checked against the check output
(`docs/DESIGN.md`, `docs/DEMO.md`, `docs/PITCH.md`). Night run continues on `night/2026-11-19`
with hardening (review, fuzzing, on-disk episode verification); task list: `night/TASKS.md`.

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
- Data: `configs/{train,dev,eval_example}.json`, `episodes/{train,dev}` (10+10 exported),
  `trajectories/train_*.jsonl`.
- Docs: `README.md`, `docs/CONTRACT.md`, `docs/DESIGN.md` (with measured results), `docs/DEMO.md`, `docs/PITCH.md`.

## In progress
- Nothing. T19–T22 re-verified: every command in README/DEMO runs, numbers in DESIGN/PITCH match
  `auditenv.check` and `auditenv.analyze`. `auditenv.analyze` now reports micro P/R/F1 like the check
  (before, the per-episode mean scored silence on clean books as P = R = 0: reconcile showed 0.8/0.8/1.0).
  All of `night/TASKS.md` is [x].

## Left to do (humans)
- Record the demo video following `docs/DEMO.md` (`uv run python -m auditenv.demo --pause`).
- Build slides from `docs/PITCH.md`; fill in the Team slide.
- Merge `night/2026-11-19` into `main` via PR; make the repo public (or share) before submitting.
- Submission checklist above ("Deadline & submission").

## Decisions & assumptions
- Hidden evaluation: set `AUDITENV_SECRET` in the grader process only (keys generator RNG + HMAC episode_id).
- After ANY generator change: re-export `episodes/` and regenerate `trajectories/` (tests/test_load.py fails otherwise).
- Work goes through branches + PRs into `main`; nobody pushes to `main` directly.
- Night agent never asks questions; every assumption it makes is logged in `night/LOG.md`.
- Interfaces are fixed in `docs/CONTRACT.md` (ledger in base currency only; truth amounts are
  ledger misstatements in base currency; evidence ids = doc_id / row_id).
- Stdlib only, zero runtime dependencies; tests use `unittest`.

## How to run
```bash
uv run python -m auditenv.check                       # everything: tests, verifier, baselines, paired, remote
uv run python -m auditenv.demo --pause                # narrated demo for the video
uv run python -m unittest discover -s tests -t .      # unit tests only
uv run python -m auditenv.verify --seeds 0-199        # data/truth verifier
uv run python -m auditenv.run --policy reconcile --config configs/dev.json --out /tmp/traj.jsonl
uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json
```
No `uv`: `python3.11 -m auditenv.check` from the repo root. Docker: `docker build -t auditenv . && docker run --rm auditenv`.

## How to continue (process for the next person)
1. `git pull` → read this file → open `night/TASKS.md`.
2. Take the first unchecked task `- [ ]` (or a `[!]` one that got stuck — see
   `night/LOG.md` for why). Put your name next to it so nobody doubles up.
3. Branch from the latest work: `git checkout -b <your-name>/<task-id> origin/<branch above>`.
4. Do the task, check its acceptance criterion, mark it `[x]`.
5. Update this file (Status / Done / Left / Last updated), commit, push,
   open a PR into the branch above (or into `main` if the night branch is merged).
