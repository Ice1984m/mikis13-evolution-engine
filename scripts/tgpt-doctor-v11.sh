#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/mikis13-evolution-engine"

STAMP="$(date +%Y%m%d-%H%M%S)"

LOG="$ROOT/logs/providers/tgpt-doctor-$STAMP.log"
REPORT="$ROOT/reports/providers/tgpt-doctor-latest.txt"

mkdir -p \
  "$(dirname "$LOG")" \
  "$(dirname "$REPORT")"

{
    echo "Mikis13 TGPT Doctor"
    echo "Date: $(date -Iseconds)"
    echo

    echo "===== BINARY ====="
    command -v tgpt || true
    tgpt --version 2>&1 || true

    echo
    echo "===== HELP ====="
    tgpt --help 2>&1 || true

    echo
    echo "===== NETWORK ====="

    curl \
      -L \
      --connect-timeout 10 \
      --max-time 20 \
      -I \
      https://github.com \
      2>&1 |
    head -n 20 || true

    echo
    echo "===== PROXY ENV ====="

    env |
    grep -Ei \
      '^(http|https|all)_proxy=' \
      || echo "Geen proxy environment"

    echo
    echo "===== DEFAULT TGPT TEST ====="

    timeout 90 \
      tgpt \
      "Reply only with MIKIS13_TGPT_OK" \
      2>&1 || true

} | tee "$LOG" > "$REPORT"

echo
echo "Doctor opgeslagen:"
echo "$REPORT"
