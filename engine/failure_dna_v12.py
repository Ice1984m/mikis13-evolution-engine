#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import sys

ROOT = Path.home() / "mikis13-evolution-engine"

DNA = ROOT / "state/failure-dna"


def normalize(text):
    text = text.lower()

    text = re.sub(
        r"[0-9a-f]{7,40}",
        "<sha>",
        text
    )

    text = re.sub(
        r"\d+",
        "<n>",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def fingerprint(text):
    clean = normalize(text)

    return hashlib.sha256(
        clean.encode()
    ).hexdigest()[:20]


def remember(text, solution=None):
    DNA.mkdir(parents=True, exist_ok=True)

    fp = fingerprint(text)

    path = DNA / f"{fp}.json"

    if path.exists():
        data = json.loads(path.read_text())
        data["occurrences"] += 1
    else:
        data = {
            "fingerprint": fp,
            "normalized_failure": normalize(text),
            "occurrences": 1,
            "solutions": []
        }

    if solution and solution not in data["solutions"]:
        data["solutions"].append(solution)

    data["last_seen"] = (
        datetime.now(timezone.utc).isoformat()
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ) + "\n"
    )

    return data


def main():
    text = " ".join(sys.argv[1:]).strip()

    if not text:
        print("Geef fouttekst.")
        raise SystemExit(2)

    print(
        json.dumps(
            remember(text),
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
