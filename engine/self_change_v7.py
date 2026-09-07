#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path.home() / "mikis13-evolution-engine"

PROPOSALS = (
    ROOT
    / "state/agent-proposals"
)


def now():
    return datetime.now(timezone.utc).isoformat()


def propose(agent, title, reason, change):
    PROPOSALS.mkdir(
        parents=True,
        exist_ok=True
    )

    pid = hashlib.sha256(
        (
            agent["id"]
            + title
            + reason
            + now()
        ).encode()
    ).hexdigest()[:16]

    proposal = {
        "id": pid,
        "agent_id": agent["id"],
        "created": now(),
        "title": title,
        "reason": reason,
        "proposed_change": change,
        "status": "REVIEW_REQUIRED",
        "automatic_apply": False
    }

    (
        PROPOSALS
        / f"{pid}.json"
    ).write_text(
        json.dumps(
            proposal,
            indent=2,
            ensure_ascii=False
        ) + "\n"
    )

    return proposal
