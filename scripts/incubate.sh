#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

OWNER="${OWNER:-Ice1984m}"
ROOT="$HOME/mikis13-evolution-engine"

RESULT="$ROOT/state/latest-result.json"

[ -s "$RESULT" ] || {
  echo "❌ Geen evolution-resultaat."
  exit 1
}

SCORE="$(
  jq -r '.best_idea.score // 0' \
    "$RESULT"
)"

TITLE="$(
  jq -r '.best_idea.title // empty' \
    "$RESULT"
)"

SLUG="$(
  jq -r '.best_idea.slug // empty' \
    "$RESULT"
)"

PROBLEM="$(
  jq -r '.best_idea.problem // empty' \
    "$RESULT"
)"

SOLUTION="$(
  jq -r '.best_idea.solution // empty' \
    "$RESULT"
)"

if [ -z "$SLUG" ]; then
  echo "ℹ️ Geen kandidaat."
  exit 0
fi

if [ "$SCORE" -lt 85 ]; then
  echo "ℹ️ Score $SCORE < 85."
  echo "Geen nieuwe repo."
  exit 0
fi

REPO="mikis13-lab-$SLUG"
FULL="$OWNER/$REPO"

# Max één repo-aanmaak per cyclus.
if gh repo view "$FULL" >/dev/null 2>&1; then

  echo "✅ Prototype repo bestaat al: $FULL"

else

  echo "🚀 Prototype repository maken:"
  echo "$FULL"

  gh repo create "$FULL" \
    --public \
    --description "$TITLE — experimental Mikis13 LAB prototype"

fi

TMP="$HOME/.mikis13-evolution/prototype"

rm -rf "$TMP"

gh repo clone \
  "$FULL" \
  "$TMP"

cd "$TMP"

cat > README.md <<EOF
# $TITLE

**Status: LAB / experimental**

Score tijdens incubatie: **$SCORE/100**

## Probleem

$PROBLEM

## Hypothese

$SOLUTION

## Status

Dit is automatisch aangemaakt als experimentele
Mikis13-prototypeomgeving.

Het is **geen afgewerkt product**.

## Development gates

- [ ] MVP
- [ ] automated test
- [ ] secret scan
- [ ] security review
- [ ] useful real-world validation
- [ ] health check
- [ ] documentation
- [ ] beta decision

## Principle

Build the smallest measurable experiment first.
EOF

mkdir -p blueprint tests src

cp \
 "$ROOT/state/blueprints/$SLUG/BLUEPRINT.json" \
 blueprint/BLUEPRINT.json

cat > src/README.md <<EOF
# Prototype source

Implementation intentionally starts empty.

The blueprint must first prove what minimum
function is actually required.
EOF

cat > tests/validate.sh <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

test -s README.md
test -s blueprint/BLUEPRINT.json

jq empty blueprint/BLUEPRINT.json

grep -q "LAB" README.md

echo "✅ Prototype validation PASS"
EOF

chmod +x tests/validate.sh

mkdir -p .github/workflows

cat > .github/workflows/validate.yml <<'EOF'
name: Validate LAB Prototype

on:
  workflow_dispatch:
  push:
    branches:
      - main
  pull_request:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Validate
        run: |
          chmod +x tests/validate.sh
          tests/validate.sh
EOF

./tests/validate.sh

git add .

if ! git diff --cached --quiet; then

  git commit \
    -m "Initialize validated LAB blueprint"

  git push origin main

fi

jq --arg repo "$FULL" \
   '.prototype_repo=$repo' \
   "$ROOT/state/latest-result.json" \
   > "$ROOT/state/latest-result.tmp"

mv \
 "$ROOT/state/latest-result.tmp" \
 "$ROOT/state/latest-result.json"

echo "✅ Prototype: https://github.com/$FULL"
