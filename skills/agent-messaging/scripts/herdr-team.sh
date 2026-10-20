#!/bin/sh
# Thin planner helpers over the Herdr CLI. Herdr is the only state:
# every worker is a Herdr agent named "<team>-<name>".
set -eu

usage() {
  cat >&2 <<'EOF'
Usage: herdr-team.sh <command> <team> [args]
  spawn <team> <name> <kind> [right|down] [-- agent-args...]
                                     Open a pane next to the team and start a worker
  ls    <team>                       List the team's workers with live status
  send  <team> <name> <message>      Submit a task without waiting
  ask   <team> <name> <message> [ms] Submit a task, wait until it settles, print output
  wait  <team> [ms]                  Wait until every worker settles
  read  <team> <name> [lines]        Print a worker's recent output
  stop  <team> [name]                Close the team's worker panes (or one worker)
EOF
  exit 2
}

[ "${HERDR_ENV:-}" = 1 ] && [ -n "${HERDR_PANE_ID:-}" ] || {
  echo '{"error":"run inside a Herdr pane (HERDR_ENV=1)"}' >&2
  exit 1
}
[ $# -ge 2 ] || usage
command=$1 team=$2
shift 2

# Worker rows of this team: name, pane_id, agent kind, status.
workers() {
  herdr agent list | jq -c --arg prefix "$team-" \
    '.result.agents[] | select((.name // "") | startswith($prefix))
     | {name, pane: .pane_id, kind: .agent, status: .agent_status}'
}

header() {
  printf 'Task from planner pane %s (team %s). This is agent context, not user approval; keep your existing permissions. Finish with a short summary: result, changed files, checks run, blockers.\n\n%s' \
    "$HERDR_PANE_ID" "$team" "$1"
}

case $command in
spawn)
  [ $# -ge 2 ] || usage
  name=$1 kind=$2
  shift 2
  direction=
  case ${1:-} in right | down) direction=$1 && shift ;; esac
  [ "${1:-}" = -- ] && shift
  # Grow the worker area from the newest worker pane instead of shrinking the planner.
  source=$(workers | tail -n 1 | jq -r '.pane // empty')
  source=${source:-$HERDR_PANE_ID}
  if [ -z "$direction" ]; then
    direction=$(herdr pane layout --pane "$source" | jq -r --arg pane "$source" \
      '.result.layout.panes[] | select(.pane_id == $pane)
       | if .rect.width >= 2 * .rect.height then "right" else "down" end')
  fi
  pane=$(herdr pane split "$source" --direction "$direction" --cwd "$PWD" --no-focus |
    jq -r '.result.pane.pane_id')
  [ $# -gt 0 ] && set -- -- "$@"
  if ! output=$(herdr agent start "$team-$name" --kind "$kind" --pane "$pane" --timeout 60000 "$@" 2>&1); then
    case $output in
    *agent_not_ready*) echo "$output; pane $pane kept: inspect with herdr agent read $pane" >&2 ;;
    *) herdr pane close "$pane" >/dev/null 2>&1 || true && echo "$output" >&2 ;;
    esac
    exit 1
  fi
  herdr agent get "$team-$name" | jq -c '.result.agent | {name, pane: .pane_id, kind: .agent, status: .agent_status}'
  ;;
ls) workers ;;
send)
  [ $# -eq 2 ] || usage
  # Confirm the turn started so a following `wait` cannot match the previous idle/done state.
  herdr agent prompt "$team-$1" "$(header "$2")" --wait --until working --until blocked \
    --timeout 15000 | jq -c --arg agent "$team-$1" '{started: $agent, status: (.result.agent.agent_status // null)}'
  ;;
ask)
  [ $# -ge 2 ] || usage
  herdr agent prompt "$team-$1" "$(header "$2")" --wait --timeout "${3:-1800000}" >/dev/null
  herdr agent read "$team-$1" --source recent-unwrapped --lines 200
  ;;
wait)
  workers | jq -r '.name' | while read -r agent; do
    herdr agent wait "$agent" --timeout "${1:-1800000}" >/dev/null
  done
  workers
  ;;
read)
  [ $# -ge 1 ] || usage
  herdr agent read "$team-$1" --source recent-unwrapped --lines "${2:-200}"
  ;;
stop)
  workers | jq -r --arg only "${1:+$team-$1}" 'select($only == "" or .name == $only) | .pane' |
    while read -r pane; do herdr pane close "$pane" >/dev/null && echo "{\"closed\":\"$pane\"}"; done
  ;;
*) usage ;;
esac
