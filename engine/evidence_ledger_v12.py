#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path.home() / "mikis13-evolution-engine"

LEDGER = (
    ROOT
    / "state/evidence/ledger.jsonl"
)


def now():
    return datetime.now(timezone.utc).isoformat()


def record(
    agent,
    proposal,
    evidence,
    risk,
    confidence,
    expected_impact,
    decision
):
    raw = (
        agent
        + proposal
        + now()
    )

    entry = {
        "id": hashlib.sha256(
            raw.encode()
        ).hexdigest()[:16],

        "timestamp": now(),
        "agent": agent,
        "proposal": proposal,
        "evidence": evidence,
        "risk": risk,
        "confidence": confidence,
        "expected_impact": expected_impact,
        "actual_impact": None,
        "decision": decision
    }

    LEDGER.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with LEDGER.open(
        "a",
        encoding="utf-8"
    ) as fh:
        fh.write(
            json.dumps(
                entry,
                ensure_ascii=False
            ) + "\n"
        )

    return entry


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: evidence_ledger_v12.py "
            "AGENT PROPOSAL EVIDENCE"
        )
        raise SystemExit(2)

    entry = record(
        sys.argv[1],
        sys.argv[2],
        [sys.argv[3]],
        20,
        50,
        50,
        "EXPERIMENT"
    )

    print(json.dumps(entry, indent=2))


if __name__ == "__main__":
    main()
