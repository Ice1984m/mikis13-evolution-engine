#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

cd "$ROOT"

echo "🔐 SECURITY GATE"

PATTERN='(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})'

if git grep -En "$PATTERN" -- \
  ':!state/' \
  ':!reports/' \
  ':!logs/' \
  >/tmp/mikis-secret-hits 2>/dev/null
then

  echo "❌ Mogelijk geheim gevonden:"
  sed -E \
    's/[A-Za-z0-9_-]{12,}/[REDACTED]/g' \
    /tmp/mikis-secret-hits

  exit 1
fi

echo "✅ Secret scan PASS"

python -m py_compile \
  engine/*.py

echo "✅ Python compile PASS"

for FILE in \
 scripts/*.sh \
 workers/*.sh
do
  [ -e "$FILE" ] || continue
  bash -n "$FILE"
done

echo "✅ Shell syntax PASS"
