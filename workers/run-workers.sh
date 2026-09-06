#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

JOBS="$ROOT/state/workers/latest.json"

[ -s "$JOBS" ] || {
  echo "ℹ️ Geen workers klaar"
  exit 0
}

echo
echo "=================================================="
echo " MIKIS13 WORKER POOL"
echo "=================================================="

COUNT="$(jq '.worker_count // 0' "$JOBS")"

echo "Workers: $COUNT"

jq -c '.workers[]' "$JOBS" |
while read -r WORKER
do
    ID="$(jq -r '.id' <<<"$WORKER")"
    ROLE="$(jq -r '.role' <<<"$WORKER")"
    MISSION="$(jq -r '.mission' <<<"$WORKER")"

    echo
    echo "------------------------------------------"
    echo "🤖 $ROLE"
    echo "ID: $ID"
    echo "Mission: $MISSION"
    echo "------------------------------------------"

    case "$ROLE" in

      "Repair Worker")
        echo "→ repair/failure data onderzoeken"
        ;;

      "Monitor Worker")
        echo "→ repositories/workflows controleren"
        ;;

      "Security Review Worker")
        echo "→ veilige statische controles voorbereiden"
        ;;

      "Website Worker")
        echo "→ website-integratie voorbereiden"
        ;;

      "Hosting Worker")
        echo "→ hosting/health status analyseren"
        ;;

      "Test Worker")
        echo "→ testplan genereren"
        ;;

      "GitHub Worker")
        echo "→ repo/PR status onderzoeken"
        ;;

      "Automation Worker")
        echo "→ herhaalbaar proces zoeken"
        ;;

      *)
        echo "→ research + blueprint"
        ;;
    esac

done

echo
echo "✅ Worker pool cycle klaar"
