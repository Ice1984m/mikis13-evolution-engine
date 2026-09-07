#!/usr/bin/env python3

from pathlib import Path
import json

ROOT = Path.home() / "mikis13-evolution-engine"

POLICY = (
    ROOT
    / "config/agent-life-v7-policy.json"
)

BUDGET = (
    ROOT
    / "state/agent-budget"
)


def load_policy():
    return json.loads(
        POLICY.read_text()
    )


def reset(agent_id):
    BUDGET.mkdir(
        parents=True,
        exist_ok=True
    )

    limit = int(
        load_policy().get(
            "maximum_actions_per_cycle",
            3
        )
    )

    state = {
        "agent_id": agent_id,
        "limit": limit,
        "used": 0,
        "remaining": limit
    }

    (
        BUDGET
        / f"{agent_id}.json"
    ).write_text(
        json.dumps(
            state,
            indent=2
        ) + "\n"
    )

    return state


def consume(agent_id, amount=1):
    path = (
        BUDGET
        / f"{agent_id}.json"
    )

    if not path.exists():
        state = reset(agent_id)
    else:
        state = json.loads(
            path.read_text()
        )

    if (
        state["used"] + amount
        > state["limit"]
    ):
        return False, state

    state["used"] += amount

    state["remaining"] = (
        state["limit"]
        - state["used"]
    )

    path.write_text(
        json.dumps(
            state,
            indent=2
        ) + "\n"
    )

    return True, state
