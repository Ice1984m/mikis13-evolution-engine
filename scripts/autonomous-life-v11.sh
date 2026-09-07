#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/mikis13-evolution-engine"

INTERVAL="${MIKIS_LIFE_INTERVAL:-1800}"

mkdir -p \
  "$ROOT/state/locks" \
  "$ROOT/logs/life"

LOCK="$ROOT/state/locks/autonomous-life-v11.lock"

exec 9>"$LOCK"

if ! flock -n 9; then
    echo "ℹ️ Autonomous Life draait reeds."
    exit 0
fi

echo "Mikis13 Autonomous Life V11"
echo "Interval: ${INTERVAL}s"

while true
do
    STAMP="$(date +%Y%m%d-%H%M%S)"
    LOG="$ROOT/logs/life/cycle-$STAMP.log"

    {
        echo "=============================================="
        echo "MIKIS13 LIFE CYCLE"
        echo "$(date -Iseconds)"
        echo "=============================================="

        cd "$ROOT" || exit 1

        # ----------------------------------------
        # 1. Environment / population
        # ----------------------------------------

        if [ -f engine/population_v9.py ]; then
            python engine/population_v9.py || true
        fi

        if [ -f engine/governor_v9.py ]; then
            python engine/governor_v9.py || true
        fi

        # ----------------------------------------
        # 2. Existing learning
        # ----------------------------------------

        if [ -f engine/learn_v4.py ]; then
            python engine/learn_v4.py || true
        fi

        if [ -f engine/evolve.py ]; then
            python engine/evolve.py || true
        fi

        # ----------------------------------------
        # 3. Bot factory
        # ----------------------------------------

        if [ -f engine/bot_factory.py ]; then
            python engine/bot_factory.py || true
        fi

        # ----------------------------------------
        # 4. Persistent Agent Life
        # ----------------------------------------

        if [ -f engine/agent_life_v7.py ]; then
            python engine/agent_life_v7.py || true
        fi

        # ----------------------------------------
        # 5. AI Council via TGPT
        # ----------------------------------------

        scripts/ai-council-v11.sh || true

        # ----------------------------------------
        # 6. Existing Council
        # ----------------------------------------

        if [ -f engine/city_council_v9.py ]; then
            python engine/city_council_v9.py || true
        fi

        # ----------------------------------------
        # 7. Policy tests
        # ----------------------------------------

        if [ -f tests/test_city_v9.py ]; then
            python tests/test_city_v9.py || true
        fi

        # ----------------------------------------
        # 8. Security
        # ----------------------------------------

        if [ -x scripts/security-gate-v6.sh ]; then
            scripts/security-gate-v6.sh || true
        fi

        # ----------------------------------------
        # 9. Health
        # ----------------------------------------

        if [ -x scripts/healthcheck-v6.sh ]; then
            scripts/healthcheck-v6.sh || true
        fi

        # ----------------------------------------
        # 10. Governor closes cycle
        # ----------------------------------------

        if [ -f engine/governor_v9.py ]; then
            python engine/governor_v9.py || true
        fi

        # ----------------------------------------
        # 11. Learning journal
        # ----------------------------------------

        scripts/write-learning-v11.sh || true

        echo
        echo "✅ Cycle complete $(date -Iseconds)"

    } >> "$LOG" 2>&1

    sleep "$INTERVAL"
done
