#!/bin/bash
# Overnight watchdog for Claude Code / Antigravity CLI (agy) / Codex CLI. See NIGHT.md.
# Re-prompts one headless session until night/DONE, night/STOP or the deadline.
# Slots = (engine, account, model) tried in order; the first slot that is not
# rate-limited is always used. A limited slot waits until its reported reset
# time (or LIMIT_SLEEP if none); when every slot is limited, sleep until the
# earliest reset.
set -u

ROLE=lead
NAME=""
UNTIL=07:00
ENGINE=claude
WORKERS=""
BRANCH="night/$(date +%F)"
MODELS=""
ACCOUNTS="default"
SLOTS=""
usage() {
  echo "usage: $0 [--role lead|worker] [--name NAME] [--engine claude|agy|codex|deepseek] [--until HH:MM|\"YYYY-MM-DD HH:MM\"]"
  echo "          [--branch night/YYYY-MM-DD] [--model \"A,B\"] [--accounts \"default,DIR\"] [--workers \"gemini,codex\"]"
  echo "          [--slots \"engine|account|model;engine|account|model\"]   (overrides --engine/--model/--accounts)"
  exit 2
}
while [ $# -gt 0 ]; do
  case "$1" in
    --role)        ROLE="$2"; shift 2 ;;
    --name)        NAME="$2"; shift 2 ;;      # worker name = its task tag and branch suffix
    --until)       UNTIL="$2"; shift 2 ;;
    --engine)      ENGINE="$2"; shift 2 ;;
    --workers)     WORKERS="$2"; shift 2 ;;   # lead only: names of workers running in parallel
    --with-worker) WORKERS="worker"; shift ;; # old flag: one worker named "worker"
    --branch)      BRANCH="$2"; shift 2 ;;
    --model)       MODELS="$2"; shift 2 ;;    # comma list: next one is used on a usage limit
    --accounts)    ACCOUNTS="$2"; shift 2 ;;  # agy: HOME dirs, codex: CODEX_HOME dirs; "default" = own login
    --slots)       SLOTS="$2"; shift 2 ;;     # mixed engines, e.g. codex first, claude as fallback
    *) usage ;;
  esac
done
case "$ROLE" in lead|worker) ;; *) usage ;; esac
[ -z "$NAME" ] && NAME="$ROLE"

# Build SLOTS from --engine/--accounts/--model when --slots is not given.
if [ -z "$SLOTS" ]; then
  case "$ENGINE" in claude|agy|codex|deepseek) ;; *) usage ;; esac
  # agy default: strongest model first, fallback with its own quota second.
  [ "$ENGINE" = agy ] && [ -z "$MODELS" ] && MODELS="Claude Opus 4.6 (Thinking),Gemini 3.8 Flash (High)"
  [ "$ENGINE" = claude ] && ACCOUNTS="default"
  for a in $(echo "$ACCOUNTS" | tr ',' ' '); do
    if [ -z "$MODELS" ]; then SLOTS="$SLOTS;$ENGINE|$a|"
    else
      n=$(echo "$MODELS" | awk -F, '{print NF}')
      for k in $(seq 1 "$n"); do SLOTS="$SLOTS;$ENGINE|$a|$(echo "$MODELS" | cut -d, -f"$k")"; done
    fi
  done
  SLOTS="${SLOTS#;}"
fi
N_SLOTS=$(echo "$SLOTS" | awk -F';' '{print NF}')
slot_spec()  { echo "$SLOTS" | cut -d';' -f"$1"; }
slot_field() { slot_spec "$1" | cut -d'|' -f"$2"; }
for k in $(seq 1 "$N_SLOTS"); do
  case "$(slot_field "$k" 1)" in claude|agy|codex|deepseek) ;; *) echo "bad slot: $(slot_spec "$k")"; usage ;; esac
done

slot=1
cur_engine() { slot_field "$slot" 1; }
cur_acc()    { local a; a=$(slot_field "$slot" 2); echo "${a:-default}"; }
cur_home()   { local a; a=$(cur_acc); [ "$a" = default ] || echo "$a"; }
cur_model()  { slot_field "$slot" 3; }
# Conversations belong to (engine, account); switching models keeps the conversation.
# agy ignores --model when resuming a conversation, so it gets one conversation per model.
session_file() {
  local k; k="$(cur_engine)-$(cur_acc)"; [ "$(cur_engine)" = agy ] && k="$k-$(cur_model)"
  echo ".night-logs/session-$NAME-$(echo "$k" | tr -c 'A-Za-z0-9\n-' '_')"
}

CLAUDE_BIN="${CLAUDE_BIN:-claude}"                       # overridable for testing
AGY_BIN="${AGY_BIN:-$HOME/.gemini/bin/agy}"              # full paths: nohup shells may lack PATH
CODEX_BIN="${CODEX_BIN:-$(command -v codex || echo codex)}"
LIMIT_SLEEP="${LIMIT_SLEEP:-3600}"                       # limited slot with no reset time in the message
ERROR_SLEEP="${ERROR_SLEEP:-300}"                        # wait after other errors
IDLE_SLEEP="${IDLE_SLEEP:-300}"                          # worker with nothing to do (doubles while idle)
IDLE_MAX="${IDLE_MAX:-1200}"                             # cap for the idle back-off
NEXT_SLEEP="${NEXT_SLEEP:-15}"                           # pause between normal runs
AGY_TURN_TIMEOUT="${AGY_TURN_TIMEOUT:-7200s}"            # agy turn cap (e.g. stuck waiting for a login)

# Work in the git worktree of the current directory (the marathon starts workers from
# their own worktrees with one shared script path); fall back to the script's repo.
ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || ROOT="$(dirname "$0")/.."
cd "$ROOT" || exit 1
mkdir -p .night-logs night

# Keep the Mac awake for as long as this script runs.
caffeinate -dimsu -w $$ &

now() { date +%s; }
case "$UNTIL" in
  *-*) DEADLINE=$(date -j -f "%Y-%m-%d %H:%M:%S" "$UNTIL:00" +%s) || exit 1 ;;   # full "YYYY-MM-DD HH:MM"
  *)   DEADLINE=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%F) $UNTIL:00" +%s) || exit 1
       [ "$DEADLINE" -le "$(now)" ] && DEADLINE=$((DEADLINE + 86400)) ;;
esac
DEADLINE_HUMAN=$(date -r "$DEADLINE" "+%Y-%m-%d %H:%M")
log() { echo "[$(date '+%H:%M:%S')] [$NAME/$(cur_engine)] $*"; }

# Sleep, but never past the deadline and wake early on DONE/STOP.
nap() {
  local end=$(( $(now) + $1 ))
  [ "$end" -gt "$DEADLINE" ] && end=$DEADLINE
  while [ "$(now)" -lt "$end" ] && [ ! -e night/DONE ] && [ ! -e night/STOP ]; do sleep "${NAP_POLL:-20}"; done
}

# Epoch when a limited slot is usable again, parsed from the engine's message; empty if unknown.
#   claude: "resets 9:30pm (Asia/...)"  codex: "try again at 11:29 PM"  agy: "Resets in 151h35m20s"
reset_epoch() {
  local f="$1" t h m ap s
  t=$(grep -oiE 'resets in [0-9]+h([0-9]+m)?' "$f" | head -1)
  if [ -n "$t" ]; then
    h=$(echo "$t" | sed -E 's/.* ([0-9]+)h.*/\1/'); m=$(echo "$t" | sed -nE 's/.*h([0-9]+)m.*/\1/p')
    echo $(( $(now) + h * 3600 + ${m:-0} * 60 + 60 )); return
  fi
  t=$(grep -oiE '(resets|try again at) [0-9]{1,2}(:[0-9]{2})? ?(am|pm)' "$f" | head -1)
  [ -z "$t" ] && return
  h=$(echo "$t" | sed -E 's/.* ([0-9]{1,2})(:[0-9]{2})? ?([aApP][mM])$/\1/')
  m=$(echo "$t" | sed -nE 's/.*:([0-9]{2}) ?[aApP][mM]$/\1/p')
  ap=$(echo "$t" | grep -oiE '(am|pm)$' | tr 'a-z' 'A-Z')
  s=$(date -j -f "%Y-%m-%d %I:%M %p" "$(date +%F) $h:${m:-00} $ap" +%s 2>/dev/null) || return
  [ "$s" -le "$(now)" ] && s=$((s + 86400))
  echo $((s + 60))
}

# Per-slot "usable again at" epochs, space separated (bash 3.2: no associative arrays).
# Machine-local last-resort lead slots (git-ignored), e.g. Gemini Flash so the lead never
# stands still while every other slot waits for its reset:
#   echo "agy|default|Gemini 3.8 Flash (High);agy|$HOME/.agy-acc2|Gemini 3.8 Flash (High)" > .night-logs/lead-extra-slots
if [ "$ROLE" = lead ] && [ -s .night-logs/lead-extra-slots ]; then
  SLOTS="$SLOTS;$(tr -d '\n' < .night-logs/lead-extra-slots)"
  N_SLOTS=$(echo "$SLOTS" | awk -F';' '{print NF}')
fi
AVAIL=""; for k in $(seq 1 "$N_SLOTS"); do AVAIL="$AVAIL 0"; done
avail_get() { echo $AVAIL | cut -d' ' -f"$1"; }
avail_set() { AVAIL=$(echo $AVAIL | awk -v i="$1" -v v="$2" '{$i=v; print}'); }
# First slot (in order) that is usable now; 0 if none.
first_free() {
  local k t=$(now)
  for k in $(seq 1 "$N_SLOTS"); do [ "$(avail_get "$k")" -le "$t" ] && { echo "$k"; return; }; done
  echo 0
}
earliest_reset() { echo $AVAIL | tr ' ' '\n' | sort -n | head -1; }

if [ "$ROLE" = lead ]; then
  TEAM_NOTE=""
  if [ -n "$WORKERS" ]; then
    list=""; for w in $(echo "$WORKERS" | tr ',' ' '); do list="$list $w (branch $BRANCH-$w),"; done
    TEAM_NOTE=" Workers running in parallel:${list%,}. Assign tasks to them by tagging with the worker name, as NIGHT.md describes."
  fi
  FIRST_PROMPT="Read CLAUDE.md, HANDOFF.md and NIGHT.md, then follow NIGHT.md exactly as role=lead. Night branch: $BRANCH. The deadline is $DEADLINE_HUMAN. Work autonomously, use subagents if your tool has them, commit and push after every finished task. If night/TASKS.md already exists, another lead engine worked before you: continue from TASKS.md and the end of night/LOG.md (check git status for its unfinished changes).$TEAM_NOTE"
  NEXT_PROMPT="Continue the night run per NIGHT.md as role=lead (night branch $BRANCH, deadline $DEADLINE_HUMAN). Re-read night/TASKS.md and the end of night/LOG.md (another lead engine may have worked meanwhile), then pick up where you left off.$TEAM_NOTE"
else
  ME="role=worker, worker name=$NAME: take only tasks tagged ($NAME); your branch is $BRANCH-$NAME (created from origin/$BRANCH); night branch $BRANCH"
  FIRST_PROMPT="Read CLAUDE.md, HANDOFF.md and NIGHT.md, then follow NIGHT.md exactly as $ME. The deadline is $DEADLINE_HUMAN. Work autonomously, commit and push after every finished task."
  NEXT_PROMPT="Continue the night run per NIGHT.md as $ME (deadline $DEADLINE_HUMAN). Fetch, re-read night/TASKS.md, then pick up where you left off."
fi

# One turn of the current slot's engine. $1 = prompt, $2 = session id (may be empty).
run_engine() {
  local prompt="$1" sid="$2" home model
  home=$(cur_home); model=$(cur_model)
  case "$(cur_engine)" in
    claude)
      if [ -n "$sid" ]; then set -- --resume "$sid"; else set -- --session-id "$NEW_SID"; fi
      [ -n "$model" ] && set -- "$@" --model "$model"
      if [ -n "$home" ]; then CLAUDE_CONFIG_DIR="$home" "$CLAUDE_BIN" -p "$prompt" "$@" --dangerously-skip-permissions --output-format json
      else "$CLAUDE_BIN" -p "$prompt" "$@" --dangerously-skip-permissions --output-format json; fi ;;
    agy)
      if [ -n "$sid" ]; then set -- --conversation "$sid"; else set --; fi
      [ -n "$model" ] && set -- "$@" --model "$model"
      set -- -p "$prompt" "$@" --dangerously-skip-permissions --output-format json --print-timeout "$AGY_TURN_TIMEOUT"
      if [ -n "$home" ]; then HOME="$home" "$AGY_BIN" "$@"; else "$AGY_BIN" "$@"; fi ;;
    codex)
      if [ -n "$sid" ]; then set -- exec resume; else set -- exec; fi
      set -- "$@" --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json
      [ -n "$model" ] && set -- "$@" -m "$model"
      [ -n "$sid" ] && set -- "$@" "$sid"
      set -- "$@" "$prompt"
      if [ -n "$home" ]; then CODEX_HOME="$home" "$CODEX_BIN" "$@"; else "$CODEX_BIN" "$@"; fi ;;
    deepseek)
      DEEPSEEK_BIN="${DEEPSEEK_BIN:-$(dirname "$0")/deepseek_worker.py}"
      [ -n "$model" ] && set -- --model "$model"
      python3 "$DEEPSEEK_BIN" -p "$prompt" "$@" --output-format json ;;
  esac
}

log "started ($ROLE), branch $BRANCH, deadline $DEADLINE_HUMAN, slots: $N_SLOTS"
i=0; idle_n=0
while [ "$(now)" -lt "$DEADLINE" ]; do
  [ -e night/DONE ] && { log "night/DONE found — finished"; break; }
  [ -e night/STOP ] && { log "night/STOP found — stopping"; break; }
  # The lead may have finished in another worktree: check the pushed branch too.
  git fetch -q origin 2>/dev/null
  git cat-file -e "origin/$BRANCH:night/DONE" 2>/dev/null && { log "night/DONE on origin/$BRANCH — finished"; break; }

  free=$(first_free)
  if [ "$free" -eq 0 ]; then
    wake=$(earliest_reset); log "every slot is rate-limited — sleeping until $(date -r "$wake" '+%m-%d %H:%M')"
    nap $(( wake - $(now) > 60 ? wake - $(now) : 60 )); continue
  fi
  [ "$free" -ne "$slot" ] && { slot=$free; log "using slot $slot: $(cur_engine) $(cur_model) (account $(cur_acc))"; }

  i=$((i + 1))
  ENG=$(cur_engine)
  out=".night-logs/$NAME-$ENG-run-$i.json"
  SESSION_FILE=$(session_file)
  sid=""; [ -s "$SESSION_FILE" ] && sid=$(cat "$SESSION_FILE")
  prompt="$FIRST_PROMPT"; [ -n "$sid" ] && prompt="$NEXT_PROMPT"
  if [ "$ENG" = claude ] && [ -z "$sid" ]; then NEW_SID=$(uuidgen | tr 'A-Z' 'a-z'); echo "$NEW_SID" > "$SESSION_FILE"; fi

  run_engine "$prompt" "$sid" < /dev/null > "$out" 2>&1 &
  pid=$!
  log "run $i (${sid:-new session}) slot $slot: model ${ENG}/$(cur_model) account $(cur_acc)"

  # Wait for the run; hard stop at the deadline.
  while kill -0 "$pid" 2>/dev/null; do
    [ "$(now)" -ge "$DEADLINE" ] && { log "deadline — stopping the run"; kill -TERM "$pid" 2>/dev/null; }
    sleep "${RUN_POLL:-5}"
  done
  wait "$pid"; rc=$?

  failed=0
  case "$ENG" in
    claude)
      { [ "$rc" -ne 0 ] || grep -q '"is_error": *true' "$out"; } && failed=1 ;;
    agy)
      cid=$(grep -oE '"conversation_id": *"[^"]+"' "$out" | head -1 | sed -E 's/.*"([^"]+)"$/\1/')
      [ -n "$cid" ] && echo "$cid" > "$SESSION_FILE"
      { [ "$rc" -ne 0 ] || ! grep -q '"status": *"SUCCESS"' "$out"; } && failed=1 ;;
    codex)
      cid=$(grep -oE '"thread_id": *"[^"]+"' "$out" | head -1 | sed -E 's/.*"([^"]+)"$/\1/')
      [ -n "$cid" ] && echo "$cid" > "$SESSION_FILE"
      # "type":"error" alone can be a warning (e.g. resumed with another model): the turn must complete.
      { [ "$rc" -ne 0 ] || grep -q '"type": *"turn\.failed"' "$out" || ! grep -q '"type": *"turn\.completed"' "$out"; } && failed=1 ;;
    deepseek)
      { [ "$rc" -ne 0 ] || ! grep -q '"status": *"SUCCESS"' "$out"; } && failed=1 ;;
  esac

  if [ "$failed" -eq 1 ] && grep -qiE 'usage limit|hit your limit|limit reached|rate.?limit|429|overloaded|quota|resource.?exhausted|resets|try again at|authentication required|not logged in' "$out"; then
    # Push unfinished work right away, so the next engine/round continues from it.
    if [ -n "$(git status --porcelain)" ]; then
      git add -A && git commit -qm "WIP: $NAME ($ENG) hit its usage limit — unfinished work, continue it" \
        && git push -q origin HEAD 2>/dev/null && log "pushed unfinished work before the limit pause"
    fi
    r=$(reset_epoch "$out"); [ -z "$r" ] && r=$(( $(now) + LIMIT_SLEEP ))
    avail_set "$slot" "$r"
    log "usage limit on slot $slot until $(date -r "$r" '+%m-%d %H:%M')"; nap "$NEXT_SLEEP"
  elif [ "$failed" -eq 1 ]; then
    if grep -qiE 'no conversation found|session.*not found|thread.*not found' "$out"; then
      log "session lost — starting a fresh one"; rm -f "$SESSION_FILE"
    fi
    log "error rc=$rc (see $out) — sleeping ${ERROR_SLEEP}s"; nap "$ERROR_SLEEP"
  elif grep -qE '("|\\n)[*_` ]*IDLE[*_`. ]*(\\n)*"' "$out"; then   # IDLE as the reply's last line
    idle_n=$((idle_n + 1)); s=$IDLE_SLEEP; k=1
    while [ "$k" -lt "$idle_n" ] && [ "$s" -lt "$IDLE_MAX" ]; do s=$((s * 2)); k=$((k + 1)); done
    [ "$s" -gt "$IDLE_MAX" ] && s=$IDLE_MAX
    log "idle — sleeping ${s}s"; nap "$s"
  else
    idle_n=0; nap "$NEXT_SLEEP"
  fi
done
log "exit"
