# HANDOFF.md — start here

> Current state of the project for the next person (human or agent).
> Read this first after `git pull`. Keep it short and true.
> Updated after every finished task (by the night agent or by you).

**Last updated:** 2026-11-19 · by: Claude (night lead) · branch: `night/2026-11-19`

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

- [ ] Working end-to-end demo flow
- [ ] `README.md`: what it is, how to run — the jury opens the repo
- [ ] GitHub repo viewable by the jury — **it's private now**: make it public
      (or otherwise give access) before submitting
- [ ] Demo video: short demo + explanation of the solution — script: `docs/DEMO.md`
- [ ] Presentation — outline: `docs/PITCH.md` (written by the night agent)
- [ ] Google Doc with the 3 links (repo, video, presentation); the Doc and all
      three materials shared as **"Anyone with the link — Viewer"**
- [ ] Doc link submitted in the personal account on the site

## Status
Core environment works end-to-end and passes the single check command
(`uv run python -m auditenv.check` → ALL CHECKS PASSED, ~6 s). Night run (lead Claude +
workers gemini, codex) continues on `night/2026-11-19`; task list: `night/TASKS.md`.

## Done
- Generator (`auditenv/generator.py`, `inject.py`): hidden company history → correct double-entry
  ledger → 4 error types (duplicate_invoice, payment_allocation, fx_error, period_cutoff) +
  2 interacting scenarios (I1, I2) + clean companies + distractors; truth + provenance.
- Env (`auditenv/env.py`): JSON `reset/step`, 5 tools, 50-row pages, 100-step limit, 60 s limit,
  train/eval modes. Matcher + reward (`matcher.py`, `metrics.py`, `schema.py`, `calculator.py`).
- Independent verifier (`verify.py`), benign transform for paired checks (`transform.py`),
  out-of-process server/client (`server.py`, `client.py`), runner + trajectories (`run.py`),
  baselines random / flag-all / oracle (`policies/`), check command (`check.py`), Dockerfile.
- 154 unit tests (`tests/`), incl. all SPEC §05 attack properties.

## In progress
- gemini: T12 reconcile baseline, T16 episode export + configs. codex: T23 failure analysis.
- lead: design note, README, demo script, pitch outline (T19–T22).

## Left to do
- See `night/TASKS.md` (unchecked items).
- Fill the `[TODO]` sections in `CLAUDE.md` (stack now chosen: Python 3.11 stdlib, unittest, uv).

## Decisions & assumptions
- Work goes through branches + PRs into `main`; nobody pushes to `main` directly.
- Night agent never asks questions; every assumption it makes is logged in `night/LOG.md`.
- Interfaces are fixed in `docs/CONTRACT.md` (ledger in base currency only; truth amounts are
  ledger misstatements in base currency; evidence ids = doc_id / row_id).
- Stdlib only, zero runtime dependencies; tests use `unittest`.

## How to run
```bash
uv run python -m auditenv.check                       # everything (tests, verifier, baselines, paired, remote)
uv run python -m unittest discover -s tests -t .      # unit tests only
uv run python -m auditenv.verify --seeds 0-199        # data/truth verifier
uv run python -m auditenv.run --policy oracle --seeds 2000-2009 --out /tmp/traj.jsonl
```

## How to continue (process for the next person)
1. `git pull` → read this file → open `night/TASKS.md`.
2. Take the first unchecked task `- [ ]` (or a `[!]` one that got stuck — see
   `night/LOG.md` for why). Put your name next to it so nobody doubles up.
3. Branch from the latest work: `git checkout -b <your-name>/<task-id> origin/<branch above>`.
4. Do the task, check its acceptance criterion, mark it `[x]`.
5. Update this file (Status / Done / Left / Last updated), commit, push,
   open a PR into the branch above (or into `main` if the night branch is merged).
