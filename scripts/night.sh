#!/bin/bash
# Overnight watchdog for Claude Code / Antigravity CLI (agy). See NIGHT.md.
# Re-prompts one headless session until night/DONE, night/STOP or the deadline.
# On usage-limit errors waits LIMIT_SLEEP (default 1h) and tries again.
set -u

ROLE=lead
UNTIL=07:00
ENGINE=claude
WITH_WORKER=0
BRANCH="night/$(date +%F)"
usage() { echo "usage: $0 [--role lead|worker] [--engine claude|agy] [--until HH:MM] [--branch night/YYYY-MM-DD] [--with-worker]"; exit 2; }
while [ $# -gt 0 ]; do
  case "$1" in
    --role)        ROLE="$2"; shift 2 ;;
    --until)       UNTIL="$2"; shift 2 ;;
    --engine)      ENGINE="$2"; shift 2 ;;
    --with-worker) WITH_WORKER=1; shift ;;
    --branch)      BRANCH="$2"; shift 2 ;;
    *) usage ;;
  esac
done
case "$ENGINE" in claude|agy) ;; *) usage ;; esac

CLAUDE_BIN="${CLAUDE_BIN:-claude}"              # overridable for testing
AGY_BIN="${AGY_BIN:-$HOME/.gemini/bin/agy}"     # full path: nohup shells may lack PATH
LIMIT_SLEEP="${LIMIT_SLEEP:-3600}"              # wait after a usage limit
ERROR_SLEEP="${ERROR_SLEEP:-300}"               # wait after other errors
IDLE_SLEEP="${IDLE_SLEEP:-600}"                 # worker with nothing to do
NEXT_SLEEP="${NEXT_SLEEP:-15}"                  # pause between normal runs

cd "$(dirname "$0")/.." || exit 1
mkdir -p .night-logs night

# Keep the Mac awake for as long as this script runs.
caffeinate -dimsu -w $$ &

now() { date +%s; }
DEADLINE=$(date -j -f "%Y-%m-%d %H:%M" "$(date +%F) $UNTIL" +%s) || exit 1
[ "$DEADLINE" -le "$(now)" ] && DEADLINE=$((DEADLINE + 86400))
DEADLINE_HUMAN=$(date -r "$DEADLINE" "+%Y-%m-%d %H:%M")
log() { echo "[$(date '+%H:%M:%S')] [$ROLE/$ENGINE] $*"; }

# Sleep, but never past the deadline and wake early on DONE/STOP.
nap() {
  local end=$(( $(now) + $1 ))
  [ "$end" -gt "$DEADLINE" ] && end=$DEADLINE
  while [ "$(now)" -lt "$end" ] && [ ! -e night/DONE ] && [ ! -e night/STOP ]; do sleep "${NAP_POLL:-20}"; done
}

SESSION_FILE=".night-logs/session-$ROLE-$ENGINE"
TEAM_NOTE=""
[ "$ROLE" = lead ] && [ "$WITH_WORKER" -eq 1 ] && TEAM_NOTE=" A worker (Gemini via agy) is running in parallel: tag small self-contained tasks (worker) as NIGHT.md describes."
FIRST_PROMPT="Read CLAUDE.md, HANDOFF.md and NIGHT.md, then follow NIGHT.md exactly as role=$ROLE. Night branch: $BRANCH (worker branch: $BRANCH-worker). The deadline is $DEADLINE_HUMAN. Work autonomously, use subagents if you have them, commit and push after every finished task.$TEAM_NOTE"
NEXT_PROMPT="Continue the night run per NIGHT.md as role=$ROLE (night branch $BRANCH, deadline $DEADLINE_HUMAN). Re-read night/TASKS.md and the end of night/LOG.md, then pick up where you left off.$TEAM_NOTE"

# Runs one turn in the background, sets $pid. Output (JSON) goes to $out.
start_run() {
  local sid=""
  [ -s "$SESSION_FILE" ] && sid=$(cat "$SESSION_FILE")
  local prompt="$FIRST_PROMPT"; [ -n "$sid" ] && prompt="$NEXT_PROMPT"
  if [ "$ENGINE" = claude ]; then
    if [ -n "$sid" ]; then set -- --resume "$sid"
    else sid=$(uuidgen | tr 'A-Z' 'a-z'); echo "$sid" > "$SESSION_FILE"; set -- --session-id "$sid"; fi
    "$CLAUDE_BIN" -p "$prompt" "$@" --dangerously-skip-permissions --output-format json > "$out" 2>&1 &
  else
    # agy: no fixed ids; resume by conversation id, saved from each run's JSON.
    if [ -n "$sid" ]; then set -- --conversation "$sid"; else set --; fi
    "$AGY_BIN" -p "$prompt" "$@" --dangerously-skip-permissions --output-format json > "$out" 2>&1 &
  fi
  pid=$!
  log "run $i (${sid:-new session})"
}

log "started, branch $BRANCH, deadline $DEADLINE_HUMAN"
i=0
while [ "$(now)" -lt "$DEADLINE" ]; do
  [ -e night/DONE ] && { log "night/DONE found — finished"; break; }
  [ -e night/STOP ] && { log "night/STOP found — stopping"; break; }
  i=$((i + 1))
  out=".night-logs/$ROLE-$ENGINE-run-$i.json"

  start_run
  # Hard stop at the deadline.
  ( sleep $(( DEADLINE - $(now) )); kill -TERM "$pid" 2>/dev/null ) &
  killer=$!
  wait "$pid"; rc=$?
  kill "$killer" 2>/dev/null; wait "$killer" 2>/dev/null

  failed=0
  if [ "$ENGINE" = claude ]; then
    { [ "$rc" -ne 0 ] || grep -q '"is_error": *true' "$out"; } && failed=1
  else
    cid=$(grep -oE '"conversation_id": *"[^"]+"' "$out" | head -1 | sed -E 's/.*"([^"]+)"$/\1/')
    [ -n "$cid" ] && echo "$cid" > "$SESSION_FILE"
    { [ "$rc" -ne 0 ] || ! grep -q '"status": *"SUCCESS"' "$out"; } && failed=1
  fi

  if [ "$failed" -eq 1 ] && grep -qiE 'usage limit|hit your limit|limit reached|rate.?limit|429|overloaded|quota|resource.?exhausted|resets' "$out"; then
    log "usage limit (rc=$rc) — sleeping ${LIMIT_SLEEP}s"; nap "$LIMIT_SLEEP"
  elif [ "$failed" -eq 1 ]; then
    if grep -qiE 'no conversation found|session.*not found' "$out"; then
      log "session lost — starting a fresh one"; rm -f "$SESSION_FILE"
    fi
    log "error rc=$rc (see $out) — sleeping ${ERROR_SLEEP}s"; nap "$ERROR_SLEEP"
  elif grep -qE '"(result|response)": *"IDLE' "$out"; then
    log "idle — sleeping ${IDLE_SLEEP}s"; nap "$IDLE_SLEEP"
  else
    nap "$NEXT_SLEEP"
  fi
done
log "exit"
