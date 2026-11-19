#!/bin/bash
# Continuous improvement until the freeze time: round after round of
#   new branch from origin/main → lead (rotating engines) + gemini worker (scripts/night.sh)
#   → night/DONE → merge origin/main + check → PR → CI green → merge into main → next round.
# A failed merge/check/CI starts a fix round on the same branch. A round with no
# product change makes the marathon back off. See NIGHT.md → "Continuous mode".
# Stop: touch .night-logs/STOP   (git-ignored; the current round ends at its next turn)
set -u

FREEZE="${1:-2026-11-22 18:00}"                 # stop starting work here (humans submit after)
C1=$HOME/.codex-acc1; C2=$HOME/.codex-acc2
LEAD_SLOTS="${LEAD_SLOTS:-claude|default|;codex|$C2|gpt-6.2-astra;codex|$C2|gpt-6.2-sol;codex|$C1|gpt-6.2-astra;codex|$C1|gpt-6.2-sol}"
GEM_ACCOUNTS="${GEM_ACCOUNTS:-default,$HOME/.agy-acc2,$HOME/.agy-acc3}"
GEM_MODEL="${GEM_MODEL:-Gemini 3.8 Flash (High)}"
GEM_DIR="${GEM_DIR-../genesis-gemini}"         # worker worktree (created if missing); "" = no worker
CHECK_CMD="${CHECK_CMD:-uv run python -m auditenv.check}"
PR="${PR:-1}"                                   # 0 = push only, no PR/merge (testing)
EMPTY_SLEEP="${EMPTY_SLEEP:-7200}"              # after a round with no product change
NIGHT_SH="${NIGHT_SH:-scripts/night.sh}"

cd "$(dirname "$0")/.." || exit 1
mkdir -p .night-logs
caffeinate -dimsu -w $$ &
now() { date +%s; }
END=$(date -j -f "%Y-%m-%d %H:%M:%S" "$FREEZE:00" +%s) || exit 1
log() { echo "[$(date '+%m-%d %H:%M:%S')] [marathon] $*"; }
stopped() { [ -e .night-logs/STOP ] || [ "$(now)" -ge "$END" ]; }
nap() { local e=$(( $(now) + $1 )); while [ "$(now)" -lt "$e" ] && ! stopped; do sleep 20; done; }

ROUND_FILE=.night-logs/marathon-round
round=$(cat "$ROUND_FILE" 2>/dev/null || echo 3)

# Commit whatever the agents left uncommitted, so no work is lost when branches change.
save_leftovers() {
  if [ -n "$(git status --porcelain)" ]; then
    git add -A && git commit -qm "marathon: commit leftover changes from round $round" && git push -q 2>/dev/null
    log "committed leftover changes"
  fi
}

write_round() {   # $1 = kind (improve|fix), $2 = details
  cat > night/ROUND.md <<EOF
# ROUND $round — $1 (branch $B, freeze $FREEZE)

$( if [ "$1" = fix ]; then echo "**Fix round.** $2
Merge \`origin/main\` into this branch if needed (keep both sides' intent), make
\`$CHECK_CMD\` green, then create \`night/DONE\`. Nothing else."
else echo "**Open improvement round** — follow NIGHT.md → \"Continuous mode\": review, pick
the highest-value improvements for the jury (SPEC §10), implement, verify, DONE.
$2"; fi )
EOF
}

start_round() {   # new branch from origin/main
  git fetch -q origin
  B="night/$(date +%F)-r$round"
  while git ls-remote --exit-code --heads origin "$B" >/dev/null 2>&1; do   # never reuse a branch
    round=$((round + 1)); B="night/$(date +%F)-r$round"
  done
  save_leftovers
  git checkout -q -B "$B" origin/main || { log "cannot create $B"; return 1; }
  mkdir -p night/archive
  local prev=$((round - 1))
  for f in TASKS LOG ROUND; do
    [ -f "night/$f.md" ] && git mv -f "night/$f.md" "night/archive/r$prev-$f.md"
  done
  git rm -q --ignore-unmatch night/DONE
  write_round improve "Previous rounds: night/archive/ (don't repeat what they did or rejected)."
  git add -A night && git commit -qm "Round $round: open improvement round (marathon)" && git push -qu origin "$B" 2>/dev/null
  log "round $round started on $B"
}

fix_round() {     # same branch, new goal
  log "fix round on $B: $1"
  git rm -q --ignore-unmatch night/DONE
  write_round fix "$1"
  git add -A night && git commit -qm "Round $round: fix — $1" && git push -q 2>/dev/null
}

run_team() {
  if [ -n "$GEM_DIR" ]; then
    [ -d "$GEM_DIR" ] || git worktree add -q --detach "$GEM_DIR" "origin/$B"
    ( cd "$GEM_DIR" && git stash -q -u 2>/dev/null; git fetch -q && git checkout -q --detach "origin/$B" \
      && rm -f night/STOP .night-logs/session-* && mkdir -p .night-logs \
      && exec "$NIGHT_SH" --role worker --name gemini --engine agy --branch "$B" --model "$GEM_MODEL" \
           --accounts "$GEM_ACCOUNTS" --until "$FREEZE" >> .night-logs/worker.out 2>&1 ) &
    gpid=$!
  fi
  rm -f .night-logs/session-lead-*            # fresh lead conversation each round
  "$NIGHT_SH" --role lead --branch "$B" ${GEM_DIR:+--workers gemini} --until "$FREEZE" --slots "$LEAD_SLOTS" \
    >> .night-logs/lead.out 2>&1
  if [ -n "$GEM_DIR" ]; then
    touch "$GEM_DIR/night/STOP"; wait "$gpid" 2>/dev/null; rm -f "$GEM_DIR/night/STOP"
  fi
}

# Merge main, check, PR, CI, merge. Returns 0 = merged, 1 = needs a fix round (reason in FIX), 2 = nothing to merge.
integrate() {
  FIX=""
  save_leftovers
  git fetch -q origin
  if ! git merge -q --no-edit origin/main 2>/dev/null; then
    git merge --abort 2>/dev/null; FIX="merge conflict with origin/main"; return 1
  fi
  if ! $CHECK_CMD > ".night-logs/check-r$round.txt" 2>&1; then
    FIX="'$CHECK_CMD' fails after merging main (output: .night-logs/check-r$round.txt, rerun it)"; return 1
  fi
  git push -q 2>/dev/null
  if git diff --quiet origin/main...HEAD -- . ':!night' ':!HANDOFF.md'; then return 2; fi
  [ "$PR" = 1 ] || return 0
  local url n
  url=$(gh pr list --head "$B" --state open --json url --jq '.[0].url' 2>/dev/null)
  [ -z "$url" ] && url=$(gh pr create --base main --head "$B" --title "Round $round: autonomous improvements ($B)" \
    --body "Autonomous improvement round $round (\`scripts/marathon.sh\`). What was done and why: \`night/TASKS.md\`, \`night/LOG.md\`, \`REVIEW.md\`. \`$CHECK_CMD\` passed on the merged tree.

🤖 Generated with [Claude Code](https://claude.com/claude-code)" 2>/dev/null)
  [ -z "$url" ] && { FIX="could not open a PR (gh)"; return 1; }
  log "PR $url — waiting for CI"
  sleep 30
  if ! gh pr checks "$url" --watch --interval 60 > ".night-logs/ci-r$round.txt" 2>&1; then
    grep -qE '\bfail' ".night-logs/ci-r$round.txt" && { FIX="CI failed on $url (gh pr checks $url)"; return 1; }
  fi
  for n in 1 2 3; do gh pr merge "$url" --merge >/dev/null 2>&1 && { log "merged $url"; return 0; }; sleep 60; done
  FIX="PR $url could not be merged (main moved?) — merge origin/main again"; return 1
}

log "marathon until $FREEZE, starting at round $round"
while ! stopped; do
  start_round || { nap 600; continue; }
  tries=0
  while :; do
    run_team
    if stopped; then integrate; log "freeze/stop reached (integrate rc=$?)"; break; fi
    integrate; rc=$?
    [ "$rc" -eq 0 ] && break
    [ "$rc" -eq 2 ] && { log "round $round changed no product files — backing off ${EMPTY_SLEEP}s"; nap "$EMPTY_SLEEP"; break; }
    tries=$((tries + 1))
    [ "$tries" -gt 3 ] && { log "round $round: 3 fix rounds failed ($FIX) — leaving $B for humans"; break; }
    fix_round "$FIX"
  done
  round=$((round + 1)); echo "$round" > "$ROUND_FILE"
done
log "exit"
