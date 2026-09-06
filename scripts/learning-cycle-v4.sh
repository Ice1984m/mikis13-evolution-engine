#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

OWNER="${OWNER:-Ice1984m}"
ROOT="$HOME/mikis13-evolution-engine"

mkdir -p \
 "$ROOT/logs" \
 "$ROOT/state/history" \
 "$ROOT/state/learning" \
 "$ROOT/state/knowledge" \
 "$ROOT/state/blueprints" \
 "$ROOT/state/project-graph"

LOG="$ROOT/logs/learning-v4-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG") 2>&1

echo
echo "=================================================="
echo " MIKIS13 LEARNING V4"
echo " $(date -Iseconds)"
echo "=================================================="

cd "$ROOT"

# Eerst bestaande Evolution Engine gebruiken indien werkend.
if [ -f engine/evolve.py ]; then

  echo
  echo "1/4 EVOLUTION SCAN"

  python engine/evolve.py || {
    echo "⚠️ V3 scan had een fout; V4 learning gaat verder."
  }

fi

echo
echo "2/4 NOTE / MEMORY LEARNING"

python engine/learn_v4.py

echo
echo "3/4 VALIDATION"

python -m py_compile \
 engine/evolve.py \
 engine/learn_v4.py

jq empty \
 state/project-graph/latest.json

jq empty \
 state/learning/latest.json

echo "✅ Learning validation PASS"

echo
echo "4/4 REPORT"

cat reports/learning-v4-latest.md

echo
echo "=================================================="
echo " ✅ LEARNING CYCLE COMPLETE"
echo "=================================================="
