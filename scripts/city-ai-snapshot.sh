#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/mikis13-evolution-engine"
OUT="$ROOT/state/ai-life/context.txt"

cd "$ROOT"

{
    echo "MIKIS13 CITY CURRENT STATE"
    echo "Generated: $(date -Is)"
    echo

    echo "===== CITY STATUS ====="

    if [ -x scripts/mikis-city-status ]; then
        scripts/mikis-city-status 2>&1 || true
    elif [ -f engine/governor_v9.py ]; then
        python engine/governor_v9.py 2>&1 || true
    fi

    echo
    echo "===== OPEN JOBS ====="

    find state/jobs \
        -type f \
        -name '*.json' \
        -print0 2>/dev/null |
    xargs -0 -r jq -c \
        'select(.status != "FINISHED") |
        {
          id,
          title,
          repository,
          priority,
          status,
          assigned_agents
        }' \
        2>/dev/null |
    tail -n 20 || true

    echo
    echo "===== AGENT SAMPLE ====="

    find state/agents \
        -type f \
        -name '*.json' \
        -print0 2>/dev/null |
    xargs -0 -r jq -c \
        '{
          id,
          name,
          role,
          division,
          status,
          reputation,
          successful_tasks,
          failed_tasks
        }' \
        2>/dev/null |
    head -n 30 || true

    echo
    echo "===== RECENT GITHUB RUNS ====="

    if gh repo view Ice1984m/mikis13-evolution-engine \
        >/dev/null 2>&1
    then
        gh run list \
            --repo Ice1984m/mikis13-evolution-engine \
            --limit 10 \
            --json \
name,status,conclusion,workflowName,headBranch,createdAt,url \
            2>/dev/null || true
    fi

    echo
    echo "===== OPEN PRS ====="

    gh pr list \
        --repo Ice1984m/mikis13-evolution-engine \
        --state open \
        --limit 20 \
        --json \
number,title,headRefName,baseRefName,isDraft,mergeStateStatus,url \
        2>/dev/null || true

    echo
    echo "===== SAFETY POLICY ====="

    if [ -f config/city-v9-policy.json ]; then
        cat config/city-v9-policy.json
    fi

} > "$OUT"

echo "$OUT"
