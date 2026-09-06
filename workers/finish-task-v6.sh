#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

LOCK="$ROOT/state/locks/active.json"
TASK="$ROOT/state/tasks/latest.json"

[ -s "$LOCK" ] || {
  echo "ℹ️ Geen actieve taak"
  exit 0
}

RESULT="${1:-}"

if [ "$RESULT" != "success" ] &&
   [ "$RESULT" != "failure" ]
then
  echo "Gebruik:"
  echo "  mikis-task-finish success"
  echo "  mikis-task-finish failure"
  exit 1
fi

TITLE="$(
  jq -r '.title' "$TASK"
)"

SIGNATURE="$(
  printf '%s' "$TITLE" |
  tr '[:upper:]' '[:lower:]' |
  sed 's/[^a-z0-9]/-/g' |
  sed 's/--*/-/g'
)"

python \
 "$ROOT/engine/failure_memory_v2.py" \
 "$RESULT" \
 "$SIGNATURE" \
 "Council V6 task result"

TMP="$LOCK.tmp"

jq \
 --arg result "$RESULT" \
 --arg finished "$(date -Iseconds)" \
 '.status="FINISHED"
  | .result=$result
  | .finished=$finished' \
 "$LOCK" > "$TMP"

mv "$TMP" "$LOCK"

cp \
 "$LOCK" \
 "$ROOT/state/locks/last.json"

rm -f "$LOCK"

echo "✅ Task afgesloten: $RESULT"
