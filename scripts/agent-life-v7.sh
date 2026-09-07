#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

cd "$ROOT"

echo
echo "==============================================="
echo " MIKIS13 AGENT LIFE V7"
echo "==============================================="

echo
echo "1/4 POLICY TEST"
python tests/test_agent_life_v7.py

echo
echo "2/4 AGENT LIFE"
python engine/agent_life_v7.py

echo
echo "3/4 SECURITY GATE"
if [ -x scripts/security-gate-v6.sh ]; then
  scripts/security-gate-v6.sh
fi

echo
echo "4/4 REPORT"
cat reports/agent-life-v7-latest.md

echo
echo "✅ AGENT LIFE V7 CYCLE COMPLETE"
