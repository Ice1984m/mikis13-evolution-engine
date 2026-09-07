#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

INTERVAL="${MIKIS_LIFE_INTERVAL:-1800}"

mkdir -p \
    "$ROOT/state/ai-life" \
    "$ROOT/logs/ai-life"

PIDFILE="$ROOT/state/ai-life/daemon.pid"

echo "$$" > "$PIDFILE"

trap '
  rm -f "$PIDFILE"
  exit 0
' INT TERM EXIT

echo "Mikis13 Life daemon started"
echo "Interval: ${INTERVAL}s"

while true
do

    "$ROOT/scripts/mikis-life-cycle-v9.sh" || true

    sleep "$INTERVAL"

done
