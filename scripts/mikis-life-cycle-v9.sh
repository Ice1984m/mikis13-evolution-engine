#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

cd "$ROOT"

LOCK="$ROOT/state/ai-life/cycle.lock"

mkdir -p \
    "$(dirname "$LOCK")" \
    logs/ai-life

exec 9>"$LOCK"

if ! flock -n 9; then
    echo "ℹ️ Andere Mikis Life cycle draait reeds."
    exit 0
fi

STAMP="$(date +%Y%m%d-%H%M%S)"

LOG="$ROOT/logs/ai-life/life-$STAMP.log"

exec >>"$LOG" 2>&1

echo
echo "=============================================="
echo " MIKIS13 LIFE CYCLE"
echo " $(date -Is)"
echo "=============================================="

# 1. Bestaande lokale leer/evolution lagen.

if [ -f engine/learn_v4.py ]; then
    python engine/learn_v4.py || true
fi

if [ -f engine/evolve.py ]; then
    python engine/evolve.py || true
fi

# 2. Bot factory.

if [ -f engine/bot_factory.py ]; then
    python engine/bot_factory.py || true
fi

# 3. Agent Life.

if [ -f engine/agent_life_v7.py ]; then
    python engine/agent_life_v7.py || true
fi

# 4. Population / Governor.

if [ -f engine/population_v9.py ]; then
    python engine/population_v9.py || true
fi

if [ -f engine/governor_v9.py ]; then
    python engine/governor_v9.py || true
fi

# 5. Safety validation BEFORE AI council.

if [ -f tests/test_city_v9.py ]; then
    python tests/test_city_v9.py
fi

if [ -x scripts/security-gate-v6.sh ]; then
    scripts/security-gate-v6.sh
fi

# 6. AI overleg.
#
# AI schrijft alleen een voorstel.

scripts/github-ai-council-v9.sh || true

# 7. Health.

if [ -x scripts/healthcheck-v6.sh ]; then
    scripts/healthcheck-v6.sh || true
fi

# 8. Governor opnieuw om grenzen te handhaven.

if [ -f engine/governor_v9.py ]; then
    python engine/governor_v9.py || true
fi

echo
echo "✅ Life cycle finished $(date -Is)"
