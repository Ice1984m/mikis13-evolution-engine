#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path.home() / "mikis13-evolution-engine"
MEMORY = ROOT / "state/agent-memory"
POLICY = ROOT / "config/agent-life-v7-policy.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def policy():
    return json.loads(POLICY.read_text())


def memory_file(agent_id):
    MEMORY.mkdir(parents=True, exist_ok=True)
    return MEMORY / f"{agent_id}.jsonl"


def add_memory(
    agent_id,
    kind,
    subject,
    content,
    confidence=50,
    outcome=None
):
    record = {
        "id": hashlib.sha256(
            (
                agent_id
                + subject
                + content
                + now()
            ).encode()
        ).hexdigest()[:16],

        "timestamp": now(),
        "kind": kind,
        "subject": subject,
        "content": content,
        "confidence": max(
            0,
            min(100, int(confidence))
        ),
        "outcome": outcome
    }

    path = memory_file(agent_id)

    memories = read_memories(agent_id)

    memories.append(record)

    limit = int(
        policy().get(
            "maximum_memories_per_agent",
            200
        )
    )

    memories = memories[-limit:]

    path.write_text(
        "\n".join(
            json.dumps(
                x,
                ensure_ascii=False
            )
            for x in memories
        ) + "\n"
    )

    return record


def read_memories(agent_id):
    path = memory_file(agent_id)

    if not path.exists():
        return []

    result = []

    for line in path.read_text().splitlines():
        try:
            result.append(json.loads(line))
        except Exception:
            continue

    return result


def relevant_memories(agent_id, text, limit=8):
    target = set(
        str(text).lower().split()
    )

    scored = []

    for memory in read_memories(agent_id):

        words = set(
            (
                memory.get("subject", "")
                + " "
                + memory.get("content", "")
            ).lower().split()
        )

        score = len(
            target & words
        )

        scored.append(
            (
                score,
                memory
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        item
        for score, item in scored[:limit]
        if score > 0
    ]
