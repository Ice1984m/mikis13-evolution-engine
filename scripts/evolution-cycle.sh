#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

OWNER="${OWNER:-Ice1984m}"
ROOT="$HOME/mikis13-evolution-engine"

LOG="$ROOT/logs/cycle-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG") 2>&1

echo
echo "=================================================="
echo " MIKIS13 EVOLUTION CYCLE"
echo " $(date -Iseconds)"
echo "=================================================="

cd "$ROOT"

echo
echo "1/6 PHONE + GITHUB DISCOVERY"

python engine/evolve.py

echo
echo "2/6 BLUEPRINT INCUBATION"

if [ "${AUTO_CREATE_PROTOTYPE_REPO:-1}" = "1" ]; then
  ./scripts/incubate.sh
fi

echo
echo "3/6 WEBSITE LAB"

if [ "${AUTO_WEBSITE_PR:-1}" = "1" ]; then
  ./scripts/website-lab-pr.sh || true
fi

echo
echo "4/6 DOCTOR"

./scripts/doctor.sh

echo
echo "5/6 ENGINE HISTORY COMMIT"

git add \
  config \
  engine \
  scripts \
  reports \
  state

# Full local absolute paths remain only in SQLite,
# which we do NOT commit.

git reset state/evolution.db 2>/dev/null || true

if ! git diff --cached --quiet; then

  BRANCH="bot/evolution-$(date -u +%Y%m%d-%H%M%S)"

  # Main eerst schoon synchroniseren voordat de bot-branch wordt gemaakt.
  git reset

  git checkout main

  git pull --ff-only origin main

  git checkout -b "$BRANCH"

  git add \
    config \
    engine \
    scripts \
    reports \
    state

  git reset state/evolution.db 2>/dev/null || true

  git commit \
    -m "Evolution cycle $(date -u +%Y-%m-%dT%H:%MZ)"

  git push \
    -u origin \
    "$BRANCH"

  gh pr create \
    --repo "$OWNER/mikis13-evolution-engine" \
    --base main \
    --head "$BRANCH" \
    --title "Evolution cycle $(date +%Y-%m-%d)" \
    --body \
"Automated Mikis13 evolution report, knowledge update and blueprint generation.

Safety:
- raw phone source not uploaded
- no direct website main push
- no blind merge
- prototype status remains LAB"

  git checkout main

fi

echo
echo "6/6 FINAL REPORT"

cat reports/latest.md

echo
echo "=================================================="
echo " ✅ EVOLUTION CYCLE COMPLETE"
echo "=================================================="
