#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path.home() / "mikis13-evolution-engine"

REFLECTIONS = (
    ROOT
    / "state/agent-reflections"
)


def now():
    return datetime.now(timezone.utc).isoformat()


def reflect(profile, event, memories):
    result = event.get(
        "result",
        "unknown"
    )

    lesson = None

    if result == "success":
        lesson = (
            "Successful action: preserve the evidence "
            "and reproduce the same validation next time."
        )

    elif result == "failure":
        lesson = (
            "Failure observed: reduce confidence, inspect "
            "evidence and avoid repeating the same approach blindly."
        )

    elif result == "blocked":
        lesson = (
            "Safety boundary activated: find a lower-impact "
            "alternative instead of bypassing policy."
        )

    else:
        lesson = (
            "Outcome uncertain: gather more evidence before "
            "increasing autonomy."
        )

    record = {
        "timestamp": now(),
        "agent_id": profile["id"],
        "event": event,
        "memory_context": memories[-5:],
        "lesson": lesson,
        "next_rule": (
            "Prefer the smallest reversible action "
            "with measurable evidence."
        )
    }

    REFLECTIONS.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        REFLECTIONS
        / f"{profile['id']}.jsonl"
    )

    with path.open(
        "a",
        encoding="utf-8"
    ) as fh:
        fh.write(
            json.dumps(
                record,
                ensure_ascii=False
            )
            + "\n"
        )

    return record
