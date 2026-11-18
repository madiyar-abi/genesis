# HANDOFF.md — start here

> Current state of the project for the next person (human or agent).
> Read this first after `git pull`. Keep it short and true.
> Updated after every finished task (by the night agent or by you).

**Last updated:** 2026-11-18 · by: Claude (setup) · branch: `chore/night-mode`

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
