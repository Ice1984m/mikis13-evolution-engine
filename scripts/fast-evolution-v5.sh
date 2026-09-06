#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

LOG="$ROOT/logs/fast-v5-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG") 2>&1

echo
echo "=================================================="
echo " MIKIS13 FAST EVOLUTION V5"
echo "=================================================="

cd "$ROOT"

echo
echo "1/5 LEARN"

if [ -f engine/learn_v4.py ]; then
    python engine/learn_v4.py || true
fi

echo
echo "2/5 EVOLVE"

if [ -f engine/evolve.py ]; then
    python engine/evolve.py || true
fi

echo
echo "3/5 CREATE WORKERS"

python engine/bot_factory.py

echo
echo "4/5 RUN WORKERS"

workers/run-workers.sh

echo

echo
echo "5/5 BOT COUNCIL"

workers/council-cycle.sh

echo
echo "✅ FAST EVOLUTION COMPLETE"

