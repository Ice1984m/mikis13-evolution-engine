#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import json

from agent_identity_v7 import (
    load_or_create,
    save
)

from memory_graph_v7 import (
    add_memory,
    read_memories
)

from affect_state_v7 import (
    update_state
)

from reflection_v7 import (
    reflect
)

from autonomy_budget_v7 import (
    reset
)

ROOT = Path.home() / "mikis13-evolution-engine"

WORKERS = (
    ROOT
    / "state/workers/latest.json"
)

REPORT = (
    ROOT
    / "reports/agent-life-v7-latest.md"
)


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    if not WORKERS.exists():
        print(
            "ℹ️ Geen workers gevonden"
        )
        return

    data = json.loads(
        WORKERS.read_text()
    )

    workers = data.get(
        "workers",
        []
    )[:4]

    agents = []

    for worker in workers:
        agent = load_or_create(
            worker
        )

        memories = read_memories(
            agent["id"]
        )

        if not memories:
            add_memory(
                agent["id"],
                "identity",
                "creation",
                (
                    "Agent identity created from "
                    "Bot Factory worker profile."
                ),
                confidence=100,
                outcome="success"
            )

        event = {
            "result": "success",
            "risk": "low",
            "source": "agent-life-cycle",
            "message": (
                "Identity and memory state loaded."
            )
        }

        update_state(
            agent,
            event
        )

        memories = read_memories(
            agent["id"]
        )

        reflection = reflect(
            agent,
            event,
            memories
        )

        lesson = reflection["lesson"]

        if lesson not in agent["lessons"]:
            agent["lessons"].append(
                lesson
            )

        agent["lessons"] = (
            agent["lessons"][-25:]
        )

        agent["memory_count"] = len(
            memories
        )

        agent["reflection_count"] = (
            int(
                agent.get(
                    "reflection_count",
                    0
                )
            )
            + 1
        )

        reset(
            agent["id"]
        )

        save(agent)

        agents.append(agent)

    # relation awareness
    for agent in agents:

        relationships = agent.get(
            "relationships",
            {}
        )

        for peer in agents:

            if peer["id"] == agent["id"]:
                continue

            current = relationships.get(
                peer["id"],
                {
                    "name": peer["name"],
                    "role": peer["role"],
                    "interactions": 0,
                    "trust": 50
                }
            )

            current["interactions"] += 1

            relationships[
                peer["id"]
            ] = current

        agent[
            "relationships"
        ] = relationships

        save(agent)

    lines = [
        "# Mikis13 Agent Life V7",
        "",
        f"Generated: {now()}",
        "",
        (
            "Affect values are simulated "
            "decision-state variables; "
            "they are not evidence of consciousness."
        ),
        "",
        f"Persistent agents: **{len(agents)}**",
        ""
    ]

    for agent in agents:
        lines += [
            f"## {agent['name']}",
            "",
            f"- ID: `{agent['id']}`",
            f"- Role: {agent['role']}",
            f"- Mission: {agent['mission']}",
            (
                "- Confidence: "
                f"{agent['state']['confidence']}"
            ),
            (
                "- Uncertainty: "
                f"{agent['state']['uncertainty']}"
            ),
            (
                "- Curiosity: "
                f"{agent['state']['curiosity']}"
            ),
            (
                "- Satisfaction: "
                f"{agent['state']['satisfaction']}"
            ),
            (
                "- Memories: "
                f"{agent['memory_count']}"
            ),
            (
                "- Reflections: "
                f"{agent['reflection_count']}"
            ),
            ""
        ]

    REPORT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "version": 7,
                "agents": len(agents),
                "report": str(REPORT),
                "status": "OK"
            },
            indent=2
        )
    )


if __name__ == "__main__":
    main()
