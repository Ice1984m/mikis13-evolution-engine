#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

mkdir -p "$ROOT/logs"

LOG="$ROOT/logs/council-v6-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG") 2>&1

cd "$ROOT"

echo
echo "============================================================"
echo " MIKIS13 AUTONOMOUS COUNCIL V6"
echo " $(date -Iseconds)"
echo "============================================================"

echo
echo "1/8 LEARNING"

if [ -f engine/learn_v4.py ]; then
  python engine/learn_v4.py || {
    echo "⚠️ Learning had waarschuwing"
  }
fi

echo
echo "2/8 EVOLUTION"

if [ -f engine/evolve.py ]; then
  python engine/evolve.py || {
    echo "⚠️ Evolution had waarschuwing"
  }
fi

echo
echo "3/8 BOT FACTORY"

if [ -f engine/bot_factory.py ]; then
  python engine/bot_factory.py
fi

echo
echo "4/8 WORKERS"

if [ -x workers/run-workers.sh ]; then
  workers/run-workers.sh
fi

echo
echo "5/8 BOT COUNCIL"

if [ -f engine/bot_council.py ]; then
  python engine/bot_council.py
fi

echo
echo "6/8 COORDINATOR"

python engine/coordinator_v6.py

echo
echo "7/8 SECURITY"

scripts/security-gate-v6.sh

echo
echo "8/8 HEALTHCHECK"

scripts/healthcheck-v6.sh

echo
echo "============================================================"
echo " ✅ COUNCIL V6 CYCLE COMPLETE"
echo "============================================================"

echo
echo "Coordinator:"
cat reports/coordinator-v6-latest.md 2>/dev/null || true
