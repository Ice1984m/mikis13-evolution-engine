#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys

ROOT = (
    Path.home()
    / "mikis13-evolution-engine"
)

FILE = (
    ROOT
    / "state/failure-memory/memory.json"
)

FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

def now():
    return datetime.now(
        timezone.utc
    ).isoformat()

def normalize(text):
    text = text.lower()
    text = re.sub(
        r"[^a-z0-9_-]+",
        "-",
        text
    )
    return text.strip("-")[:80]

def load():
    try:
        return json.loads(
            FILE.read_text()
        )
    except Exception:
        return {
            "version": 2,
            "signatures": {}
        }

def save(data):
    FILE.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ) + "\n"
    )

def main():

    if len(sys.argv) < 3:

        print(
            "Gebruik:"
            "\n failure_memory_v2.py"
            " success <signature> [fix]"
            "\n failure_memory_v2.py"
            " failure <signature> [fix]"
        )

        raise SystemExit(1)

    outcome = sys.argv[1]

    signature = normalize(
        sys.argv[2]
    )

    fix = (
        sys.argv[3]
        if len(sys.argv) > 3
        else ""
    )

    data = load()

    record = (
        data["signatures"]
        .setdefault(
            signature,
            {
                "signature":
                    signature,
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "successful_fixes": [],
                "last_seen": None
            }
        )
    )

    record["attempts"] += 1

    if outcome == "success":

        record["successes"] += 1

        if (
            fix
            and fix
            not in record[
                "successful_fixes"
            ]
        ):
            record[
                "successful_fixes"
            ].append(fix)

    else:

        record["failures"] += 1

    record["last_seen"] = now()

    save(data)

    print(
        json.dumps(
            record,
            indent=2,
            ensure_ascii=False
        )
    )

if __name__ == "__main__":
    main()
