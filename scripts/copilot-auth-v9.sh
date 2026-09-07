#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

TOKEN="$(gh auth token 2>/dev/null || true)"

if [ -z "$TOKEN" ]; then
    echo "❌ Geen bruikbare GitHub-authenticatie."
    echo
    echo "Probeer eenmalig:"
    echo "  copilot login --device-code"
    exit 1
fi

export GH_TOKEN="$TOKEN"

exec "$@"
