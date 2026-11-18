# HANDOFF.md — start here

> Current state of the project for the next person (human or agent).
> Read this first after `git pull`. Keep it short and true.
> Updated after every finished task (by the night agent or by you).

**Last updated:** 2026-11-18 · by: Claude (setup) · branch: `chore/night-mode`

## Deadline & submission
**Final deadline: 2026-11-22** (time of day: TBD — check the hackathon page).
Case arrives ~00:00 on 2026-11-19 → 3 days to build.

Submission form (`submit.exe`, opens together with the case): project name +
link to **one Google Drive folder** containing everything. Any teammate can
submit; the link can be changed until the deadline.

- [ ] Working end-to-end demo flow
- [ ] `README.md`: what it is, how to run — the jury opens the repo
- [ ] GitHub repo reachable by the jury — **it's private now**: make it public
      (or otherwise give access) before submitting
- [ ] Demo video — script: `docs/DEMO.md` (written by the night agent)
- [ ] Presentation — outline: `docs/PITCH.md` (written by the night agent)
- [ ] Drive folder with: demo video + GitHub link (file or text) + presentation,
      sharing set to **"Anyone with the link"** (otherwise the jury can't open it)
- [ ] Form submitted: project name + Drive folder link

## Status
Setup is done, no product code yet. Waiting for the task spec (track) —
it goes into `night/SPEC.md` and the overnight run starts from there.

## Done
- Repo connected to https://github.com/madiyar-abi/genesis, `.gitignore` for
  personal/editor files, `README.md`, `CLAUDE.md` (agent rules).
- Overnight autonomous run: `NIGHT.md` (protocol) + `scripts/night.sh`
  (watchdog: retries hourly on usage limits, stops at 07:00) — PR #1.
- Team for the night: lead = Claude Code, worker = Gemini via Antigravity CLI
  (`agy`: Opus 4.6 → Gemini Flash fallback, own quota, own worktree
  `../genesis-worker`). Tested end-to-end.

## In progress
- PR #1 `chore/night-mode` → `main` (open, needs merge).

## Left to do
- Full task list with acceptance checks: `night/TASKS.md` (created when the spec arrives).
- Fill the `[TODO]` sections in `CLAUDE.md` once the stack is chosen.

## Decisions & assumptions
- Work goes through branches + PRs into `main`; nobody pushes to `main` directly.
- Night agent never asks questions; every assumption it makes is logged in `night/LOG.md`.

## How to run
- [TODO: install / dev / test commands — mirror of CLAUDE.md once known.]

## How to continue (process for the next person)
1. `git pull` → read this file → open `night/TASKS.md`.
2. Take the first unchecked task `- [ ]` (or a `[!]` one that got stuck — see
   `night/LOG.md` for why). Put your name next to it so nobody doubles up.
3. Branch from the latest work: `git checkout -b <your-name>/<task-id> origin/<branch above>`.
4. Do the task, check its acceptance criterion, mark it `[x]`.
5. Update this file (Status / Done / Left / Last updated), commit, push,
   open a PR into the branch above (or into `main` if the night branch is merged).
