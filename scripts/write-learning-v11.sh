#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/mikis13-evolution-engine"

STAMP="$(date +%Y%m%d-%H%M%S)"

OUT="$ROOT/reports/learning/learning-$STAMP.md"

{
    echo "# Mikis13 Learning Cycle"
    echo
    echo "Timestamp: $(date -Iseconds)"
    echo

    echo "## Environment"
    echo
    uname -a
    echo

    echo "## City"
    echo

    [ -f "$ROOT/reports/city-v9-status.json" ] &&
      cat "$ROOT/reports/city-v9-status.json"

    echo
    echo "## AI provider"
    echo

    [ -f "$ROOT/state/ai/last-provider.json" ] &&
      cat "$ROOT/state/ai/last-provider.json"

    echo
    echo "## Council"
    echo

    [ -f "$ROOT/reports/council/latest.md" ] &&
      tail -n 120 \
        "$ROOT/reports/council/latest.md"

    echo
    echo "## Recent Git state"
    echo

    cd "$ROOT"

    git status --short 2>/dev/null || true

    echo
    echo "## Recent commits"

    git log \
      --oneline \
      -n 10 \
      2>/dev/null || true

    echo
    echo "## GitHub workflow state"

    gh run list \
      --repo Ice1984m/mikis13-evolution-engine \
      --limit 10 \
      2>/dev/null || true

} > "$OUT"

ln -sf \
  "$OUT" \
  "$ROOT/reports/learning/latest.md"

echo "$OUT"
