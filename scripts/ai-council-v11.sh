#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/mikis13-evolution-engine"

STAMP="$(date +%Y%m%d-%H%M%S)"

REPORT="$ROOT/reports/council/council-$STAMP.md"
LOG="$ROOT/logs/ai/council-$STAMP.log"

MASTER="$(
  cat "$ROOT/config/autonomous-life-master-prompt-v11.txt"
)"

CONTEXT=""

if [ -f "$ROOT/reports/city-v9-status.json" ]; then
    CONTEXT="$CONTEXT

CITY STATUS:
$(cat "$ROOT/reports/city-v9-status.json")
"
fi

if [ -f "$ROOT/reports/tgpt-council-latest.md" ]; then
    CONTEXT="$CONTEXT

PREVIOUS COUNCIL:
$(tail -n 80 "$ROOT/reports/tgpt-council-latest.md")
"
fi

PROMPT="$MASTER

CURRENT CONTEXT:

$CONTEXT

Determine the single highest-value next improvement for the current
Mikis13 system.

Do not execute it.
Return the council decision."

echo "AI Council started $(date -Iseconds)" \
  >> "$LOG"

if OUTPUT="$(
      mikis-ai "$PROMPT" \
      2>>"$LOG"
   )"
then
    printf '%s\n' "$OUTPUT" \
      > "$REPORT"
else
    {
        echo "# Council fallback"
        echo
        echo "AI provider unavailable."
        echo
        echo "The deterministic City Governor remains active."
        echo
        echo "Next action: diagnose tgpt providers."
    } > "$REPORT"
fi

ln -sf \
  "$REPORT" \
  "$ROOT/reports/council/latest.md"

echo "Council report: $REPORT"
