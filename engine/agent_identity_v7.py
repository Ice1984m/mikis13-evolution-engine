#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path.home() / "mikis13-evolution-engine"
AGENTS = ROOT / "state/agents"
POLICY = ROOT / "config/agent-life-v7-policy.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def load_policy():
    return json.loads(POLICY.read_text())


def agent_id(worker):
    raw = (
        str(worker.get("id", ""))
        + "|"
        + str(worker.get("role", "unknown"))
        + "|"
        + str(worker.get("name", "unknown"))
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def default_profile(worker):
    policy = load_policy()

    return {
        "version": 7,
        "id": agent_id(worker),
        "name": worker.get("name", "Unnamed Agent"),
        "role": worker.get("role", "Research Worker"),
        "mission": worker.get("mission", "Safe research"),
        "created": now(),
        "updated": now(),

        "identity": {
            "purpose": worker.get(
                "mission",
                "Find the smallest safe useful action"
            ),
            "values": policy["core_values"],
            "strengths": [],
            "weaknesses": [],
            "specialization": worker.get(
                "role",
                "Research Worker"
            )
        },

        "state": {
            "confidence": 50,
            "uncertainty": 50,
            "curiosity": 60,
            "urgency": 20,
            "satisfaction": 50,
            "frustration": 0
        },

        "goals": [
            {
                "goal": worker.get(
                    "mission",
                    "Safe useful progress"
                ),
                "priority": 80,
                "status": "ACTIVE"
            }
        ],

        "lessons": [],
        "relationships": {},
        "memory_count": 0,
        "reflection_count": 0,

        "safety": {
            "self_modification": "PROPOSAL_ONLY",
            "direct_main_push": False,
            "blind_merge": False,
            "payments": False,
            "crypto_trading": False,
            "paid_advertising": False,
            "secret_publication": False
        }
    }


def load_or_create(worker):
    AGENTS.mkdir(parents=True, exist_ok=True)

    aid = agent_id(worker)
    path = AGENTS / f"{aid}.json"

    if path.exists():
        profile = json.loads(path.read_text())
        profile["updated"] = now()

        profile["role"] = worker.get(
            "role",
            profile.get("role")
        )

        profile["mission"] = worker.get(
            "mission",
            profile.get("mission")
        )

    else:
        profile = default_profile(worker)

    path.write_text(
        json.dumps(
            profile,
            indent=2,
            ensure_ascii=False
        ) + "\n"
    )

    return profile


def save(profile):
    AGENTS.mkdir(parents=True, exist_ok=True)

    profile["updated"] = now()

    (
        AGENTS
        / f"{profile['id']}.json"
    ).write_text(
        json.dumps(
            profile,
            indent=2,
            ensure_ascii=False
        ) + "\n"
    )
