# NIGHT.md — autonomous overnight run

Protocol for unattended agent runs started by `scripts/night.sh`.
Nobody is awake to answer questions. You are re-prompted with "continue" after
every stop, usage-limit pause or crash until `night/DONE` exists or the deadline
(default 07:00) passes — so keep all state in files, not only in your context.
The prompt names the night branch (`night/<date>`) and, for a worker, its name
and branch (`night/<date>-<name>`); use exactly those names.

## Team
- **lead** — main checkout. Plans, does the hard and cross-cutting work, reviews
  and merges the workers' commits. The lead *engine rotates* (`--slots`): Codex
  (GPT-6.2 Astra → Sol, 2 ChatGPT accounts) first, Claude Code as fallback; on a
  usage limit the watchdog hands the lead role to the next free slot and goes
  back to Codex when its limit resets. A lead that starts after another engine
  continues from `night/TASKS.md`, the end of `night/LOG.md` and `git status`
  (finish or cleanly revert the previous lead's uncommitted change first).
- Workers (optional, each in its own git worktree, own quota — they keep going
  while the lead waits out a limit; weaker than the lead: give them
  well-specified tasks):
  - **gemini1, gemini2, gemini3** — 3 parallel Antigravity CLI workers (`--engine agy`), each pinned to its own Google account (`default`, `~/.agy-acc2`, `~/.agy-acc3`), running `Gemini 3.8 Flash (High)`.
    Worktrees: `../genesis-gemini1`, `../genesis-gemini2`, `../genesis-gemini3`.
  - **deepseek** — DeepSeek API worker (`--engine deepseek`), model `deepseek-v4.1-flash`
    via ReformBoss API (`https://api.reformboss.com/v1`). Worktree `../genesis-deepseek`.
  - **codex** — Codex CLI (`--engine codex`), 2 ChatGPT Plus accounts
    (`~/.codex-acc1`, `~/.codex-acc2`), `gpt-6.2-astra` → `gpt-6.2-sol`.
    Worktree `../genesis-codex`. Don't run it while Codex is in the lead
    slots — they share the same quota.

## Files (all tracked in git)
- `night/SPEC.md` — the task spec. Source of truth. Never edit it.
- `night/TASKS.md` — task list: `- [ ] T1 (lead) <task> — files: <paths> — accept: <check>`.
  Mark `[x]` only after the check passed. Owner is `lead` or a worker name.
- `night/LOG.md` — append-only: timestamp (from `date '+%F %H:%M'`, never
  estimated), who (lead or worker name), what you did,
  what's next, every assumption you made instead of asking.
- `HANDOFF.md` (repo root) — human-readable state for the next person: Status,
  Done, In progress, Left to do, Decisions, How to run, Last updated. Must be
  true at any moment — the run can be killed at the deadline mid-task.
- `night/DONE` — create only when every acceptance criterion in SPEC.md is met
  and verified. Creating it ends the night run for everyone.

## Role: lead
1. First run: read `night/SPEC.md`. Write `night/TASKS.md`: small tasks (≤ ~1h
   each), each with the files it touches and a concrete acceptance check.
   If the prompt lists running workers, tag with a worker's name (e.g.
   `(gemini1)`, `(gemini2)`, `(gemini3)`, `(deepseek)`, `(codex)`) the tasks that are small, self-contained, touch files
   no other owner's task touches, and have a mechanical check (a test, a
   command). Give each worker its own area of files. Everything else is `(lead)`.
   Always end TASKS.md with two `(lead)` tasks for the jury materials (humans
   record the video and make the slides from them):
   - `docs/DEMO.md` — demo-video script: 2–3 min, numbered steps, exact clicks/
     commands and inputs, what to say at each step, which result to show.
   - `docs/PITCH.md` — slide outline, one heading per slide: problem → solution
     → live demo → how it works (architecture, stack) → results/metrics →
     what's next → team. Max ~4 bullets per slide, facts only from the code.
   Commit + push TASKS.md first — the workers start from it.
2. Work on the night branch (create from current HEAD if missing).
   Never commit to or push `main`. Never force-push.
3. If your tool has subagents (Claude Code: superpowers
   `subagent-driven-development` / `dispatching-parallel-agents`), use one per
   task, independent tasks in parallel (max 3 at once — they share the usage
   limit), then review each result yourself before marking it done. Without
   subagents, do the tasks one by one yourself. Grunt work (docs sweeps,
   repetitive tests, data re-export checks) goes to the parallel workers (`gemini1`, `gemini2`, `gemini3`, `deepseek`).
4. Test-first where the code is testable. Run the tests/build before every commit.
5. After each finished task: update TASKS.md + LOG.md + HANDOFF.md, commit, `git push`.
6. Every ~30 min: `git fetch`, merge each `origin/<night branch>-<worker name>`
   that exists, review the worker's diff, re-run tests, fix or revert what's
   broken, push. A worker task with no progress on its branch for > 1h → retag
   it `(lead)` and do it yourself.
7. All tasks done → re-read SPEC.md line by line, verify each requirement,
   fix gaps, update README run instructions, `docs/DEMO.md`, `docs/PITCH.md`
   and HANDOFF.md (incl. "How to run" and what a teammate should do next) so
   they match what actually works. Then create `night/DONE`, commit, push.

## Role: worker
Your name and branch are in the prompt (e.g. name `codex`, branch `night/<date>-codex`).
1. `git fetch`. Work only on your branch: the first time
   `git checkout -B <your branch> origin/<night branch>`. Never check out the
   lead's or another worker's branch — they are open in other worktrees.
   Before each task: `git fetch && git merge origin/<night branch>`.
2. Take only unchecked tasks tagged with your name, one at a time.
   If there are none (or TASKS.md doesn't exist yet), stop and make `IDLE` the
   last line of your reply — the script then retries in 5 min.
3. Touch only the files listed for your task. Test, mark `[x]`, append to
   LOG.md, commit, `git push -u origin <your branch>` after every task.
   Don't edit HANDOFF.md — the lead owns it. Never touch `main`.

## Continuous mode (`scripts/marathon.sh`)
The marathon runs rounds back to back until the freeze time: each round is a
new branch `night/<date>-r<N>` from `origin/main`; after `night/DONE` it merges
`main`, runs the check, opens a PR, waits for CI and merges it, then starts the
next round. The round's goal is in `night/ROUND.md` (read it first).
- **Open improvement round** (lead): there is no fixed spec beyond SPEC.md, so
  find the work yourself:
  1. Read `night/archive/` (previous rounds' TASKS/LOG/ROUND), `REVIEW.md`,
     `docs/CHECKS.md`, HANDOFF "Ideas". Don't repeat done or rejected work.
  2. Review the repo against SPEC §10 (jury criteria, points) like a strict
     jury member: run `auditenv.check`, `auditenv.fuzz`, `auditenv.attack`,
     the shortcut miner; read the code and docs for wrong claims. Record
     findings with evidence in `REVIEW.md` → "Round N".
  3. Write `night/TASKS.md`: 3–8 tasks with the highest jury value per hour
     (real defects first, then evidence/tests, then docs accuracy). Small,
     safe, each with a mechanical check. Grunt work → `(gemini1)`, `(gemini2)`, `(gemini3)`, `(deepseek)`.
  4. Do them, keep `auditenv.check` green after every commit, sync doc numbers
     (`scripts/sync_docs.py`), update HANDOFF, then `night/DONE`.
  5. Nothing with real jury value left? Log "no valuable improvement found"
     with what you checked, and create `night/DONE` without code changes —
     the marathon then pauses for 2 h instead of burning quota.
- **Fix round**: do exactly what `night/ROUND.md` says (merge conflict, red
  check or red CI), nothing else, then `night/DONE`.
- All "Rules first" in HANDOFF.md still apply (fixed contract and reward,
  stdlib only, byte-identical default episodes unless a data fix needs a re-export).
- Humans start/stop it: `nohup scripts/marathon.sh "2026-11-22 18:00" >> .night-logs/marathon.out 2>&1 &`
  · stop: `touch .night-logs/STOP` · watch: `tail -f .night-logs/marathon.out .night-logs/lead.out`

## Priorities (hackathon, final deadline 2026-11-22 22:00)
A run ends at its `--until` time (default 07:00); the whole project has ~3.5 days. Order tasks so that a
working end-to-end demo exists as early as possible and stays working after
every merge; features and polish come after. Keep README run steps true.

## Hard rules
- Never ask the user a question — choose the simplest reasonable option and log
  the assumption in LOG.md.
- Don't stop early: if you think you're done, verify against SPEC.md again.
- Stay inside this repo. No secrets in files. No destructive git (reset --hard
  on shared branches, force-push, branch deletion).
- Stuck on one task > 3 attempts → log why, mark it `[!]`, move to the next.
- Merge conflicts in `night/TASKS.md` / `night/LOG.md` are expected (everyone
  edits them): keep both sides — every task line, `[x]` beats `[ ]`, all log
  entries in time order. Never resolve by dropping the other side.

## How to launch (done by the human or by Claude when the spec arrives)
```bash
# 1. put the spec into night/SPEC.md, commit it on the night branch, push
B=night/$(date +%F)
# 2. lead — detached, survives closing the terminal; Mac on the charger, lid open.
#    Slots "engine|account|model" in preference order: Codex Astra/Sol on both accounts, Claude last.
C1=$HOME/.codex-acc1; C2=$HOME/.codex-acc2
mkdir -p .night-logs && nohup scripts/night.sh --role lead --branch $B --workers "gemini" --until 07:00 \
  --slots "codex|$C1|gpt-6.2-astra;codex|$C1|gpt-6.2-sol;codex|$C2|gpt-6.2-astra;codex|$C2|gpt-6.2-sol;claude|default|" \
  > .night-logs/lead.out 2>&1 &
# 3. worker for grunt work, in its own worktree
git worktree add --detach ../genesis-gemini origin/$B && mkdir -p ../genesis-gemini/.night-logs
(cd ../genesis-gemini && nohup scripts/night.sh --role worker --name gemini --engine agy --branch $B \
  --model "Gemini 3.8 Flash (High)" --accounts "default,$HOME/.agy-acc2,$HOME/.agy-acc3" --until 07:00 \
  > .night-logs/worker.out 2>&1 &)
# optional (only if Codex is NOT in the lead slots): codex worker in ../genesis-codex
#   (cd ../genesis-codex && scripts/night.sh --role worker --name codex --engine codex --branch $B \
#     --model "gpt-6.2-astra,gpt-6.2-sol" --accounts "$C1,$C2" --until 07:00)
# night.sh always works in the git worktree of the current directory — cd there first.
# logins (one-time): agy: HOME=$HOME/.agy-accN ~/.gemini/bin/agy · codex: CODEX_HOME=$HOME/.codex-accN codex login --device-auth
# watch:  tail -f .night-logs/lead.out ../genesis-*/.night-logs/worker.out
# stop:   touch night/STOP ../genesis-*/night/STOP
```
