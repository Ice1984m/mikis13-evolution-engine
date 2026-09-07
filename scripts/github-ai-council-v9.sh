#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"

cd "$ROOT"

mkdir -p \
    logs/ai-life \
    reports/ai-life \
    state/ai-life

STAMP="$(date +%Y%m%d-%H%M%S)"

CONTEXT="$(
    scripts/city-ai-snapshot.sh
)"

REPORT="$ROOT/reports/ai-life/council-$STAMP.md"
LATEST="$ROOT/reports/ai-life/latest.md"
LOG="$ROOT/logs/ai-life/council-$STAMP.log"

PROMPT_FILE="$ROOT/state/ai-life/prompt.txt"

cat > "$PROMPT_FILE" <<EOF
You are Mikis13 City Council.

You coordinate a persistent engineering society consisting of:
- 50 evolution agents
- 50 operations agents
- dormant agents
- mentors
- workers
- testing agents
- repair agents
- GitHub agents
- security agents
- research agents

Your purpose is to decide the safest and most useful next work.

IMPORTANT:

You are currently an ADVISORY COUNCIL.

DO NOT modify files.
DO NOT execute commands.
DO NOT push code.
DO NOT merge pull requests.
DO NOT publish secrets.
DO NOT initiate purchases.
DO NOT initiate payments.
DO NOT perform cryptocurrency trading.
DO NOT perform cryptocurrency withdrawals.
DO NOT initiate paid advertisements.
DO NOT contact external repositories unless explicitly opted in.
DO NOT weaken safety policies.

Always prefer:

1. use an existing agent
2. reactivate a dormant suitable agent
3. reassign an existing agent
4. only then propose creation of a new agent

Before proposing a new repository:
- inspect existing repositories
- inspect existing workers
- inspect existing pull requests
- inspect previous failures
- inspect reusable components

Maximum active workers should remain bounded.

Evaluate the current city state below.

Return a concise council report using these sections:

# Council Decision

## Situation

## Highest Impact Task

## Assigned Roles
Select at most 3 roles.

## Evidence

## Proposed Actions
Only reversible, bounded proposals.

## Risks

## Tests Required

## Security Required

## Healthcheck Required

## Rollback

## Learning

## Population Decision
Choose exactly one:
REUSE_EXISTING
REACTIVATE_DORMANT
REASSIGN
SPAWN_PROPOSAL
NO_CHANGE

## Final Decision
Choose exactly one:
IMPLEMENT_PROPOSAL
EXPERIMENT
IMPROVE_EXISTING
RESEARCH
PAUSE
REJECT

Do not claim any command was executed.

CURRENT CITY STATE:

$(cat "$CONTEXT")
EOF

echo "🤖 GitHub Copilot Council draait..."

set +e

OUTPUT="$(
    scripts/copilot-auth-v9.sh \
    copilot \
      -sp "$(cat "$PROMPT_FILE")" \
      --model auto \
      --no-ask-user \
      --no-remote \
      --no-remote-export \
      --disable-builtin-mcps \
      --deny-tool='shell' \
      --deny-tool='write' \
      --deny-tool='task' \
      --deny-tool='web_fetch' \
      2>"$LOG"
)"

RC=$?

set -e

if [ "$RC" -ne 0 ]; then

    {
        echo "# Copilot Council failed"
        echo
        echo "Exit code: $RC"
        echo
        echo "Log:"
        echo
        tail -n 50 "$LOG"
    } > "$REPORT"

    cp "$REPORT" "$LATEST"

    echo "⚠️ Council kon niet antwoorden."
    exit "$RC"
fi

printf '%s\n' "$OUTPUT" > "$REPORT"

cp "$REPORT" "$LATEST"

echo "✅ Council rapport:"
echo "$REPORT"
