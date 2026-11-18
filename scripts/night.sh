#!/bin/bash
# Overnight watchdog for Claude Code. See NIGHT.md.
# Re-prompts one headless session until night/DONE, night/STOP or the deadline.
# On usage-limit errors waits LIMIT_SLEEP (default 1h) and tries again.
set -u

ROLE=lead
UNTIL=07:00
while [ $# -gt 0 ]; do
  case "$1" in
    --role)  ROLE="$2"; shift 2 ;;
    --until) UNTIL="$2"; shift 2 ;;
    *) echo "usage: $0 [--role lead|worker] [--until HH:MM]"; exit 2 ;;
  esac
done

CLAUDE_BIN="${CLAUDE_BIN:-claude}"        # overridable for testing
LIMIT_SLEEP="${LIMIT_SLEEP:-3600}"        # wait after a usage limit
ERROR_SLEEP="${ERROR_SLEEP:-300}"         # wait after other errors
IDLE_SLEEP="${IDLE_SLEEP:-600}"           # worker with nothing to do
NEXT_SLEEP="${NEXT_SLEEP:-15}"            # pause between normal runs

cd "$(dirname "$0")/.." || exit 1
mkdir -p .night-logs night

# Keep the Mac awake for as long as this script runs.
caffeinate -dimsu -w $$ &

now() { date +%s; }
DEADLINE=$(date -j -f "%Y-%m-%d %H:%M" "$(date +%F) $UNTIL" +%s) || exit 1
[ "$DEADLINE" -le "$(now)" ] && DEADLINE=$((DEADLINE + 86400))
DEADLINE_HUMAN=$(date -r "$DEADLINE" "+%Y-%m-%d %H:%M")
log() { echo "[$(date '+%H:%M:%S')] [$ROLE] $*"; }

# Sleep, but never past the deadline and wake early on DONE/STOP.
nap() {
  local end=$(( $(now) + $1 ))
  [ "$end" -gt "$DEADLINE" ] && end=$DEADLINE
  while [ "$(now)" -lt "$end" ] && [ ! -e night/DONE ] && [ ! -e night/STOP ]; do sleep "${NAP_POLL:-20}"; done
}

SESSION_FILE=".night-logs/session-$ROLE"
FIRST_PROMPT="Read NIGHT.md and follow it exactly as role=$ROLE. The deadline is $DEADLINE_HUMAN. Work autonomously, use subagents, commit and push after every finished task."
NEXT_PROMPT="Continue the night run per NIGHT.md as role=$ROLE (deadline $DEADLINE_HUMAN). Re-read night/TASKS.md and the end of night/LOG.md, then pick up where you left off."

log "started, deadline $DEADLINE_HUMAN"
i=0
while [ "$(now)" -lt "$DEADLINE" ]; do
  [ -e night/DONE ] && { log "night/DONE found — finished"; break; }
  [ -e night/STOP ] && { log "night/STOP found — stopping"; break; }
  i=$((i + 1))
  out=".night-logs/$ROLE-run-$i.json"

  if [ -s "$SESSION_FILE" ]; then
    args=(--resume "$(cat "$SESSION_FILE")"); prompt="$NEXT_PROMPT"
  else
    sid=$(uuidgen | tr 'A-Z' 'a-z'); echo "$sid" > "$SESSION_FILE"
    args=(--session-id "$sid"); prompt="$FIRST_PROMPT"
  fi

  log "run $i (${args[0]})"
  "$CLAUDE_BIN" -p "$prompt" "${args[@]}" --dangerously-skip-permissions \
    --output-format json > "$out" 2>&1 &
  pid=$!
  # Hard stop at the deadline.
  ( sleep $(( DEADLINE - $(now) )); kill -TERM "$pid" 2>/dev/null ) &
  killer=$!
  wait "$pid"; rc=$?
  kill "$killer" 2>/dev/null; wait "$killer" 2>/dev/null

  failed=0
  { [ "$rc" -ne 0 ] || grep -q '"is_error": *true' "$out"; } && failed=1

  if [ "$failed" -eq 1 ] && grep -qiE 'usage limit|hit your limit|limit reached|rate.?limit|429|overloaded|resets' "$out"; then
    log "usage limit (rc=$rc) — sleeping ${LIMIT_SLEEP}s"; nap "$LIMIT_SLEEP"
  elif [ "$failed" -eq 1 ]; then
    if grep -qiE 'no conversation found|session.*not found' "$out"; then
      log "session lost — starting a fresh one"; rm -f "$SESSION_FILE"
    fi
    log "error rc=$rc (see $out) — sleeping ${ERROR_SLEEP}s"; nap "$ERROR_SLEEP"
  elif grep -q '"result": *"IDLE"' "$out"; then
    log "idle — sleeping ${IDLE_SLEEP}s"; nap "$IDLE_SLEEP"
  else
    nap "$NEXT_SLEEP"
  fi
done
log "exit"
