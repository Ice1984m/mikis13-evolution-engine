#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

cd "$ROOT"

echo "🩺 COUNCIL V6 HEALTHCHECK"

test -s \
 config/council-v6-policy.json

jq empty \
 config/council-v6-policy.json

python -m py_compile \
 engine/coordinator_v6.py \
 engine/failure_memory_v2.py

if [ -s state/coordinator/latest.json ]; then
  jq empty state/coordinator/latest.json
fi

if [ -s state/tasks/latest.json ]; then

  jq -e \
    '.rollback_plan != null' \
    state/tasks/latest.json \
    >/dev/null

fi

echo "✅ Local Council health PASS"

# Publieke site indien bereikbaar.
for URL in \
  "https://mikis13.nl/" \
  "https://www.mikis13.nl/"
do

  CODE="$(
    curl \
      --location \
      --silent \
      --output /dev/null \
      --connect-timeout 8 \
      --max-time 15 \
      --write-out '%{http_code}' \
      "$URL" \
      || echo 000
  )"

  echo "$URL → HTTP $CODE"

done
