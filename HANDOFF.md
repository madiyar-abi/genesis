# HANDOFF.md — start here

> Current state of the project for the next person (human or agent).
> Read this first after `git pull`. Keep it short and true.
> Updated after every finished task (by the night agent or by you).

**Last updated:** 2026-11-19 13:40 · by: Claude (setup) · branch: `night/2026-11-19`

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
Case received (FinTech: RL environment for AI financial audit) → `night/SPEC.md`
(PDF: `night/case.pdf`). Agent run started on `night/2026-11-19`; no product
code yet. Note: the PDF's deadline is 2026-11-22 23:59 Astana, the organizer
chat said 22:00 — we plan for 22:00.

## Done
- Repo connected to https://github.com/madiyar-abi/genesis, `.gitignore` for
  personal/editor files, `README.md`, `CLAUDE.md` (agent rules).
- Overnight autonomous run: `NIGHT.md` (protocol) + `scripts/night.sh`
  (watchdog: retries hourly on usage limits, stops at 07:00) — merged via PR #1.
- Team for the night: lead = Claude Code; workers = `gemini` (Antigravity CLI,
  3 Google accounts, Opus 4.6 → Gemini Flash) and `codex` (Codex CLI, 2 ChatGPT
  Plus accounts), each in its own worktree and branch. Rehearsed end-to-end.

## In progress
- Agent run (lead Claude + workers gemini, codex) planning `night/TASKS.md` from the spec.

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
