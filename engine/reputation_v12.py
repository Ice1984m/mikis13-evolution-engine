#!/usr/bin/env python3

from pathlib import Path
import json

ROOT = Path.home() / "mikis13-evolution-engine"

AGENTS = ROOT / "state/agents"
POLICY = ROOT / "config/city-v12-policy.json"


def promotion(agent, policy):
    reputation = int(
        agent.get("reputation", 50)
    )

    successes = int(
        agent.get("successful_tasks", 0)
    )

    rules = policy["promotion"]

    if (
        reputation >= rules["mentor_min_reputation"]
        and
        successes >= rules["mentor_min_successes"]
    ):
        return "MENTOR"

    if (
        reputation >= rules["specialist_min_reputation"]
        and
        successes >= rules["specialist_min_successes"]
    ):
        return "SPECIALIST"

    if successes > 0:
        return "ACTIVE"

    return agent.get(
        "rank",
        "TRAINEE"
    )


def main():
    policy = json.loads(
        POLICY.read_text()
    )

    result = {
        "TRAINEE": 0,
        "ACTIVE": 0,
        "SPECIALIST": 0,
        "MENTOR": 0
    }

    for path in AGENTS.glob("*.json"):
        try:
            agent = json.loads(
                path.read_text()
            )
        except Exception:
            continue

        rank = promotion(
            agent,
            policy
        )

        agent["rank"] = rank

        path.write_text(
            json.dumps(
                agent,
                indent=2
            ) + "\n"
        )

        result[rank] = (
            result.get(rank, 0) + 1
        )

    print(
        json.dumps(
            result,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
