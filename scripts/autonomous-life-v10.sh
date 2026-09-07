#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/mikis13-evolution-engine"

mkdir -p "$ROOT/logs"

LOCK="$ROOT/state/tgpt/life.lock"

exec 9>"$LOCK"

if ! flock -n 9; then
    echo "Life engine draait al."
    exit 0
fi

echo "Mikis13 Autonomous Life gestart."

while true
do
    LOG="$ROOT/logs/life-$(date +%Y%m%d).log"

    {
        echo
        echo "======================================"
        echo "$(date -Iseconds)"
        echo "======================================"

        cd "$ROOT" || exit 1

        # ----------------------------------------
        # Population / governor
        # ----------------------------------------

        if [ -f engine/population_v9.py ]; then
            python engine/population_v9.py || true
        fi

        if [ -f engine/governor_v9.py ]; then
            python engine/governor_v9.py || true
        fi

        # ----------------------------------------
        # Existing Agent Life
        # ----------------------------------------

        if [ -f engine/agent_life_v7.py ]; then
            python engine/agent_life_v7.py || true
        fi

        # ----------------------------------------
        # AI Council
        # ----------------------------------------

        scripts/tgpt-council-v10.sh || true

        # ----------------------------------------
        # Existing council
        # ----------------------------------------

        if [ -f engine/city_council_v9.py ]; then
            python engine/city_council_v9.py || true
        fi

        # ----------------------------------------
        # Security gate
        # ----------------------------------------

        if [ -x scripts/security-gate-v6.sh ]; then
            scripts/security-gate-v6.sh || true
        fi

        # ----------------------------------------
        # Health
        # ----------------------------------------

        if [ -x scripts/healthcheck-v6.sh ]; then
            scripts/healthcheck-v6.sh || true
        fi

        echo "Cycle klaar."

    } >> "$LOG" 2>&1

    # 30 minuten rust.
    # Geen eindeloze API-loop/spam.
    sleep 1800
done
