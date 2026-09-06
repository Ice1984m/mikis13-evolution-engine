#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

FAIL=0

REPORT="$ROOT/reports/doctor.md"

{
echo "# Mikis13 Evolution V3 Doctor"
echo
echo "Generated: $(date -Iseconds)"
echo
} > "$REPORT"

check() {

  NAME="$1"
  shift

  if "$@" >/dev/null 2>&1; then

    echo "✅ $NAME"

    echo "- ✅ $NAME" \
      >> "$REPORT"

  else

    echo "❌ $NAME"

    echo "- ❌ $NAME" \
      >> "$REPORT"

    FAIL=1

  fi
}

check git git --version
check gh gh --version
check python python --version
check sqlite sqlite3 --version
check jq jq --version
check curl curl --version
check github-auth gh auth status

check python-syntax \
  python -m py_compile \
  "$ROOT/engine/evolve.py"

check policy \
  jq empty \
  "$ROOT/config/policy.json"

check prompt \
  test -s \
  "$ROOT/config/MASTER-PROMPT-V3.md"

check evolution-result \
  test -s \
  "$ROOT/state/latest-result.json"

echo >> "$REPORT"

if [ "$FAIL" -eq 0 ]; then

  echo "## RESULT: PASS" \
    >> "$REPORT"

  echo
  echo "✅ DOCTOR PASS"

else

  echo "## RESULT: FAIL" \
    >> "$REPORT"

  echo
  echo "❌ DOCTOR FAIL"

fi

echo
echo "Verslag:"
echo "$REPORT"

exit "$FAIL"
