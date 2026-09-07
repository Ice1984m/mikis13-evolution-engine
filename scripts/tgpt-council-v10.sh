#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="$ROOT/reports/tgpt-council-$STAMP.md"

STATUS="Geen statusrapport."

if [ -s "$ROOT/reports/city-v9-status.json" ]; then
    STATUS="$(cat "$ROOT/reports/city-v9-status.json")"
fi

PROMPT="
You are a member of Mikis13 Engineering Council.

CURRENT CITY:
$STATUS

Analyseer alleen.

Zoek:
- bestaande problemen
- falende workflows
- duplicaten
- verbeteringen
- tests
- security
- betrouwbaarheid
- mogelijke nieuwe worker-specialisaties

Regels:
- geen direct push naar main
- geen force push
- geen blind merge
- geen secrets
- geen betalingen
- geen aankopen
- geen crypto trading/withdrawals
- geen paid advertising
- geen mass PR/issues/comments
- geen externe repo wijzigen zonder opt-in
- bestaande agents hergebruiken voordat nieuwe worden gemaakt
- geef voorkeur aan kleine omkeerbare wijzigingen

Geef:
HYPOTHESIS
EVIDENCE_NEEDED
PROPOSED_ACTION
WORKER_ROLE
RISK
EXPECTED_IMPACT
"

{
    echo "# Mikis13 TGPT Council"
    echo
    echo "Generated: $(date -Iseconds)"
    echo

    for ROLE in \
        "architect" \
        "repair engineer" \
        "security reviewer" \
        "test engineer" \
        "evolution researcher"
    do
        echo "## $ROLE"
        echo

        mikis-ai \
            "Je bent de $ROLE. $PROMPT" \
            || echo "AI provider tijdelijk niet beschikbaar."

        echo
    done
} > "$REPORT"

ln -sf "$REPORT" \
    "$ROOT/reports/tgpt-council-latest.md"

echo "✅ Council: $REPORT"
