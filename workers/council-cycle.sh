#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

cd "$ROOT"

echo
echo "=============================================="
echo " MIKIS13 BOT COUNCIL"
echo "=============================================="

python engine/bot_council.py

echo
echo "=== COUNCIL DECISION ==="

jq '.decision' \
  state/council/latest.json

echo
echo "=== BLOCKERS ==="

jq '.blockers' \
  state/council/latest.json

echo
echo "=== OVERLEGLOG ==="

cat reports/bot-council-latest.md
