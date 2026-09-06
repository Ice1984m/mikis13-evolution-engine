#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import subprocess
import json
import os
import re
import hashlib

HOME = Path.home()
ROOT = HOME / "mikis13-evolution-engine"

STATE = ROOT / "state"
WORKERS = ROOT / "workers"
REPORTS = ROOT / "reports"

OWNER = os.getenv("OWNER", "Ice1984m")

ROLE_MAP = {
    "repair": "Repair Worker",
    "monitor": "Monitor Worker",
    "security": "Security Review Worker",
    "website": "Website Worker",
    "hosting": "Hosting Worker",
    "test": "Test Worker",
    "github": "GitHub Worker",
    "automation": "Automation Worker",
    "ai": "AI Blueprint Worker",
    "release": "Release Worker",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def slug(text):
    return re.sub(
        r"[^a-z0-9]+",
        "-",
        text.lower()
    ).strip("-")[:50]

def run(cmd):
    p = subprocess.run(
        cmd,
        text=True,
        capture_output=True
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def latest_learning():
    p = STATE / "learning/latest.json"

    if not p.exists():
        return None

    try:
        return json.loads(p.read_text())
    except Exception:
        return None

def latest_evolution():
    p = STATE / "latest-result.json"

    if not p.exists():
        return None

    try:
        return json.loads(p.read_text())
    except Exception:
        return None

def infer_roles(text):

    text = text.lower()

    roles = []

    for key, role in ROLE_MAP.items():
        if key in text:
            roles.append(role)

    if not roles:
        roles = [
            "Research Worker",
            "Test Worker"
        ]

    return list(dict.fromkeys(roles))[:4]

def worker_definition(name, role, mission):

    wid = hashlib.sha256(
        f"{name}|{role}|{mission}".encode()
    ).hexdigest()[:12]

    return {
        "id": wid,
        "name": name,
        "role": role,
        "mission": mission,
        "status": "READY",
        "created": now(),
        "permissions": [
            "read repositories",
            "analyze files",
            "generate blueprint",
            "run tests",
            "create bot branch",
            "open pull request"
        ],
        "blocked": [
            "force push main",
            "blind merge",
            "publish secrets",
            "payments",
            "crypto trading",
            "paid advertising",
            "delete production data"
        ]
    }

def main():

    WORKERS.mkdir(
        parents=True,
        exist_ok=True
    )

    (STATE / "workers").mkdir(
        parents=True,
        exist_ok=True
    )

    learning = latest_learning()
    evolution = latest_evolution()

    source = ""

    if learning and learning.get("top_concept"):
        source += json.dumps(
            learning["top_concept"]
        )

    if evolution and evolution.get("best_idea"):
        source += " " + json.dumps(
            evolution["best_idea"]
        )

    if not source:
        print("ℹ️ Nog geen learning/evolution kandidaat")
        return

    roles = infer_roles(source)

    title = "Evolution Candidate"

    if learning and learning.get("top_concept"):
        title = (
            learning["top_concept"].get(
                "title"
            )
            or title
        )

    elif evolution and evolution.get("best_idea"):
        title = (
            evolution["best_idea"].get(
                "title"
            )
            or title
        )

    workers = []

    for role in roles:

        name = (
            "Mikis13 "
            + role
            + " / "
            + title[:35]
        )

        workers.append(
            worker_definition(
                name,
                role,
                title
            )
        )

    result = {
        "generated": now(),
        "source_candidate": title,
        "worker_count": len(workers),
        "workers": workers
    }

    out = STATE / "workers/latest.json"

    out.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
        + "\n"
    )

    report = REPORTS / "bot-factory-latest.md"

    lines = [
        "# Mikis13 Bot Factory V5",
        "",
        f"Generated: {now()}",
        "",
        f"Candidate: **{title}**",
        "",
        f"Workers generated: **{len(workers)}**",
        ""
    ]

    for w in workers:
        lines += [
            f"## {w['role']}",
            "",
            f"ID: `{w['id']}`",
            "",
            f"Mission: {w['mission']}",
            "",
            "Status: READY",
            ""
        ]

    report.write_text(
        "\n".join(lines)
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )

if __name__ == "__main__":
    main()
