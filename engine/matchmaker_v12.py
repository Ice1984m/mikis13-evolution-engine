#!/usr/bin/env python3

from pathlib import Path
import json
import sys

ROOT = Path.home() / "mikis13-evolution-engine"

AGENTS = ROOT / "state/agents"
SKILLS = ROOT / "state/competencies"

KEYWORDS = {
    "workflow": ["ci", "github", "automation"],
    "github": ["github", "git"],
    "security": ["security", "testing"],
    "website": ["html", "javascript", "css"],
    "hosting": ["hosting", "dns", "reliability"],
    "python": ["python"],
    "javascript": ["javascript"],
    "test": ["testing"],
    "failure": ["debugging", "analysis"],
    "repair": ["debugging", "testing"],
    "ai": ["ai", "research"]
}


def required_skills(text):
    text = text.lower()

    result = set()

    for word, skills in KEYWORDS.items():
        if word in text:
            result.update(skills)

    if not result:
        result.update(
            ["analysis", "research"]
        )

    return sorted(result)


def main():
    task = " ".join(sys.argv[1:]).strip()

    if not task:
        print("Geef een taak.")
        raise SystemExit(2)

    wanted = required_skills(task)

    candidates = []

    for path in AGENTS.glob("*.json"):
        try:
            agent = json.loads(
                path.read_text()
            )

            cp = SKILLS / f"{agent['id']}.json"

            skills = (
                json.loads(cp.read_text())["skills"]
                if cp.exists()
                else {}
            )

        except Exception:
            continue

        skill_score = sum(
            skills.get(skill, 0)
            for skill in wanted
        )

        reputation = int(
            agent.get("reputation", 50)
        )

        experience = int(
            agent.get("successful_tasks", 0)
        )

        score = (
            skill_score
            + reputation
            + min(experience, 25)
        )

        candidates.append(
            {
                "agent_id": agent["id"],
                "name": agent.get("name"),
                "role": agent.get("role"),
                "rank": agent.get(
                    "rank",
                    "TRAINEE"
                ),
                "status": agent.get("status"),
                "score": score,
                "matching_skills": {
                    skill: skills.get(skill, 0)
                    for skill in wanted
                }
            }
        )

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    print(
        json.dumps(
            {
                "task": task,
                "required_skills": wanted,
                "selected": candidates[:3]
            },
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
