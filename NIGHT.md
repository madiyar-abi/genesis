# NIGHT.md — autonomous overnight run

Protocol for unattended agent runs started by `scripts/night.sh`.
Nobody is awake to answer questions. You are re-prompted with "continue" after
every stop, usage-limit pause or crash until `night/DONE` exists or the deadline
(default 07:00) passes — so keep all state in files, not only in your context.
The prompt names the night branch (`night/<date>`) and the worker branch
(`night/<date>-worker`); use exactly those names.

## Team
- **lead** — Claude Code (`--engine claude`), main checkout. Plans, does the hard
  and cross-cutting work, reviews and merges the worker's commits.
- **worker** (optional) — Gemini via Antigravity CLI (`--engine agy`) in its own
  git worktree `../genesis-worker`, or a teammate's own account on their machine.
  Separate usage quota, so it keeps going while the lead waits out a limit.

## Files (all tracked in git)
- `night/SPEC.md` — the task spec. Source of truth. Never edit it.
- `night/TASKS.md` — task list: `- [ ] T1 (lead) <task> — files: <paths> — accept: <check>`.
  Mark `[x]` only after the check passed. Owner is `lead` or `worker`.
- `night/LOG.md` — append-only: timestamp, who (lead/worker), what you did,
  what's next, every assumption you made instead of asking.
- `HANDOFF.md` (repo root) — human-readable state for the next person: Status,
  Done, In progress, Left to do, Decisions, How to run, Last updated. Must be
  true at any moment — the run can be killed at the deadline mid-task.
- `night/DONE` — create only when every acceptance criterion in SPEC.md is met
  and verified. Creating it ends the night run for everyone.

## Role: lead
1. First run: read `night/SPEC.md`. Write `night/TASKS.md`: small tasks (≤ ~1h
   each), each with the files it touches and a concrete acceptance check.
   If the prompt says a worker is running, tag as `(worker)` the tasks that are
   small, self-contained, touch files no lead task touches, and have a
   mechanical check (a test, a command). Everything else is `(lead)`.
   Commit + push TASKS.md first — the worker starts from it.
2. Work on the night branch (create from current HEAD if missing).
   Never commit to or push `main`. Never force-push.
3. Execute with subagents (superpowers `subagent-driven-development` /
   `dispatching-parallel-agents`): one subagent per task, independent tasks in
   parallel (max 3 at once — they share the usage limit), then review each
   result yourself before marking it done.
4. Test-first where the code is testable. Run the tests/build before every commit.
5. After each finished task: update TASKS.md + LOG.md + HANDOFF.md, commit, `git push`.
6. Every ~30 min: `git fetch`, merge `origin/<worker branch>` if it exists,
   review the worker's diff, re-run tests, fix or revert what's broken, push.
   A `(worker)` task with no progress on the worker branch for > 1h → retag it
   `(lead)` and do it yourself.
7. All tasks done → re-read SPEC.md line by line, verify each requirement,
   fix gaps, update README run instructions and HANDOFF.md (incl. "How to run"
   and what a teammate should do next). Then create `night/DONE`, commit, push.

## Role: worker
1. `git fetch`. Work only on the worker branch: the first time
   `git checkout -B <worker branch> origin/<night branch>`. Never check out the
   lead's branch itself — it is open in another worktree.
   Before each task: `git fetch && git merge origin/<night branch>`.
2. Take only unchecked `(worker)` tasks from `night/TASKS.md`, one at a time.
   If there are none (or TASKS.md doesn't exist yet), reply with exactly `IDLE`
   and stop — the script retries in 10 min.
3. Touch only the files listed for your task. Test, mark `[x]`, append to
   LOG.md, commit, `git push -u origin <worker branch>` after every task.
   Don't edit HANDOFF.md — the lead owns it. Never touch `main`.

## Hard rules
- Never ask the user a question — choose the simplest reasonable option and log
  the assumption in LOG.md.
- Don't stop early: if you think you're done, verify against SPEC.md again.
- Stay inside this repo. No secrets in files. No destructive git (reset --hard
  on shared branches, force-push, branch deletion).
- Stuck on one task > 3 attempts → log why, mark it `[!]`, move to the next.

## How to launch (done by the human or by Claude when the spec arrives)
```bash
# 1. put the spec into night/SPEC.md, commit it on the night branch, push
B=night/$(date +%F)
# 2. lead — detached, survives closing the terminal; Mac on the charger, lid open
mkdir -p .night-logs && nohup scripts/night.sh --role lead --branch $B --with-worker \
  --until 07:00 > .night-logs/lead.out 2>&1 &
# 3. worker (Gemini) in its own worktree
git worktree add --detach ../genesis-worker origin/$B && mkdir -p ../genesis-worker/.night-logs
nohup ../genesis-worker/scripts/night.sh --role worker --engine agy --branch $B \
  --until 07:00 > ../genesis-worker/.night-logs/worker.out 2>&1 &
# watch:  tail -f .night-logs/lead.out ../genesis-worker/.night-logs/worker.out
# stop:   touch night/STOP ../genesis-worker/night/STOP
```
