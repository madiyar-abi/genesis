# NIGHT.md — autonomous overnight run

Protocol for unattended Claude Code runs started by `scripts/night.sh`.
Nobody is awake to answer questions. You are re-prompted with "continue" after
every stop, usage-limit pause or crash until `night/DONE` exists or the deadline
(default 07:00) passes — so keep all state in files, not only in your context.

## Files (all tracked in git)
- `night/SPEC.md` — the task spec. Source of truth. Never edit it.
- `night/TASKS.md` — task list you maintain: `- [ ] T1 (lead) <task> — accept: <check>`.
  Mark `[x]` only after the check passed. Owner is `lead` or `worker`.
- `night/LOG.md` — append-only: timestamp, what you did, what's next, every
  assumption you made instead of asking.
- `night/DONE` — create only when every acceptance criterion in SPEC.md is met
  and verified. Creating it ends the night run.

## Role: lead (default)
1. First run: read `night/SPEC.md`. Write `night/TASKS.md`: small tasks (≤ ~1h
   each), each with a concrete acceptance check. Tag tasks that are independent
   of the rest and touch separate files as `(worker)` if a worker is running,
   else everything is `(lead)`.
2. Branch: work on `night/<YYYY-MM-DD>` (create from current HEAD if missing).
   Never commit to or push `main`. Never force-push.
3. Execute with subagents (superpowers `subagent-driven-development` /
   `dispatching-parallel-agents`): one subagent per task, independent tasks in
   parallel (max 3 at once — they share the usage limit), then review each
   result yourself before marking it done.
4. Test-first where the code is testable. Run the tests/build before every commit.
5. After each finished task: update TASKS.md + LOG.md, commit, `git push`.
6. Every ~30 min: `git fetch` and merge `origin/night/<date>-worker` if it exists;
   resolve conflicts, re-run tests, push.
7. All tasks done → re-read SPEC.md line by line, verify each requirement,
   fix gaps, update README run instructions. Then create `night/DONE`, commit, push.

## Role: worker (second account, separate worktree or machine)
1. `git fetch`; work on `night/<date>-worker`, created from `origin/night/<date>`
   (`git checkout -B night/<date>-worker origin/night/<date>` the first time).
   Never check out the lead's branch itself — it may be open in another worktree.
   Re-merge `origin/night/<date>` before each task.
2. Take only unchecked `(worker)` tasks from `night/TASKS.md`. If there are
   none, reply with exactly `IDLE` and stop — the script retries in 10 min.
3. Same rules: test, mark `[x]`, log to LOG.md, commit, push your branch after
   every task. Never touch `main` or the lead's branch directly.

## Hard rules
- Never ask the user a question — choose the simplest reasonable option and log
  the assumption in LOG.md.
- Don't stop early: if you think you're done, verify against SPEC.md again.
- Stay inside this repo. No secrets in files. No destructive git (reset --hard
  on shared branches, force-push, branch deletion).
- Stuck on one task > 3 attempts → log why, mark it `[!]`, move to the next.

## How to launch (done by the human or by Claude when the spec arrives)
```bash
# 1. put the spec into night/SPEC.md, commit it
# 2. start detached, survives closing the terminal; Mac must stay on the charger, lid open
mkdir -p .night-logs && nohup scripts/night.sh --role lead --until 07:00 > .night-logs/lead.out 2>&1 &
# worker = second account on the same Mac: own config dir + own worktree
#   one-time: CLAUDE_CONFIG_DIR=~/.claude-acc2 claude auth login
#             git worktree add --detach ../genesis-worker
cd ../genesis-worker && git fetch && git checkout --detach origin/night/<date> && mkdir -p .night-logs
CLAUDE_CONFIG_DIR=~/.claude-acc2 nohup scripts/night.sh --role worker --until 07:00 > .night-logs/worker.out 2>&1 &
# watch:   tail -f .night-logs/lead.out      stop:   touch night/STOP
```
