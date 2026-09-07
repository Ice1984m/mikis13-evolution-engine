#!/usr/bin/env python3

from pathlib import Path
import json

ROOT = Path.home() / "mikis13-evolution-engine"
AGENTS = ROOT / "state/agents"
SKILLS = ROOT / "state/competencies"

ROLE_SKILLS = {
    "github": ["github", "git", "automation"],
    "ci/cd": ["github", "ci", "automation"],
    "repair": ["debugging", "testing", "python"],
    "monitoring": ["monitoring", "reliability", "python"],
    "security": ["security", "testing", "git"],
    "website": ["html", "css", "javascript"],
    "hosting": ["hosting", "dns", "reliability"],
    "documentation": ["documentation", "research"],
    "release": ["git", "github", "ci"],
    "healthcheck": ["testing", "monitoring", "reliability"],

    "research": ["research", "analysis", "python"],
    "architecture": ["architecture", "analysis", "design"],
    "testing": ["testing", "python", "automation"],
    "failure analysis": ["debugging", "analysis", "testing"],
    "optimization": ["performance", "analysis", "python"],
    "automation design": ["automation", "python", "shell"],
    "ai design": ["ai", "python", "research"],
    "security research": ["security", "research", "testing"],
    "repository reuse": ["git", "github", "architecture"],
    "experimental": ["research", "testing", "design"]
}


def load_agent(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def default_skills(agent):
    role = str(agent.get("role", "")).lower()

    skills = {}

    for skill in ROLE_SKILLS.get(
        role,
        ["analysis", "research"]
    ):
        skills[skill] = 50

    return skills


def ensure_profile(agent):
    SKILLS.mkdir(parents=True, exist_ok=True)

    path = SKILLS / f"{agent['id']}.json"

    if path.exists():
        return json.loads(path.read_text())

    profile = {
        "agent_id": agent["id"],
        "skills": default_skills(agent),
        "tasks_measured": 0
    }

    path.write_text(
        json.dumps(profile, indent=2) + "\n"
    )

    return profile


def update(agent_id, skills, success):
    path = SKILLS / f"{agent_id}.json"

    if not path.exists():
        raise RuntimeError("competency profile missing")

    profile = json.loads(path.read_text())

    delta = 2 if success else -1

    for skill in skills:
        current = profile["skills"].get(skill, 25)

        profile["skills"][skill] = max(
            0,
            min(100, current + delta)
        )

    profile["tasks_measured"] += 1

    path.write_text(
        json.dumps(profile, indent=2) + "\n"
    )

    return profile


def main():
    count = 0

    for path in AGENTS.glob("*.json"):
        agent = load_agent(path)

        if not agent:
            continue

        ensure_profile(agent)
        count += 1

    print(f"✅ Competency profiles: {count}")


if __name__ == "__main__":
    main()
