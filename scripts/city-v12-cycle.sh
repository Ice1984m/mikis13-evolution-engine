#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

cd "$ROOT"

mkdir -p reports/v12

LOG="reports/v12/cycle-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG") 2>&1

echo "=============================================="
echo " MIKIS13 CITY V12"
echo " $(date -Iseconds)"
echo "=============================================="

echo
echo "[1] POPULATION"

[ -f engine/population_v9.py ] &&
    python engine/population_v9.py

echo
echo "[2] COMPETENCY GRAPH"

python engine/competency_v12.py

echo
echo "[3] REPUTATION / PROMOTION"

python engine/reputation_v12.py

echo
echo "[4] GOVERNOR"

[ -f engine/governor_v9.py ] &&
    python engine/governor_v9.py

echo
echo "[5] POLICY TESTS"

[ -f tests/test_city_v9.py ] &&
    python tests/test_city_v9.py

echo
echo "[6] SECURITY"

[ -x scripts/security-gate-v6.sh ] &&
    scripts/security-gate-v6.sh

echo
echo "[7] HEALTH"

[ -x scripts/healthcheck-v6.sh ] &&
    scripts/healthcheck-v6.sh || true

echo
echo "✅ V12 cycle complete"
