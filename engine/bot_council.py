#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

HOME = Path.home()
ROOT = HOME / "mikis13-evolution-engine"

STATE = ROOT / "state"
COUNCIL = STATE / "council"
REPORTS = ROOT / "reports"

WORKERS_FILE = STATE / "workers/latest.json"
LATEST = COUNCIL / "latest.json"
MESSAGES = COUNCIL / "messages.jsonl"

ROLE_WEIGHT = {
    "Security Review Worker": 1.30,
    "Test Worker": 1.25,
    "Repair Worker": 1.20,
    "Hosting Worker": 1.15,
    "GitHub Worker": 1.10,
    "Website Worker": 1.00,
    "Monitor Worker": 1.00,
    "Automation Worker": 0.95,
    "Research Worker": 0.90,
    "AI Blueprint Worker": 0.90,
    "Release Worker": 1.15,
}

BLOCKING_ROLES = {
    "Security Review Worker",
    "Test Worker",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def ensure():
    COUNCIL.mkdir(parents=True, exist_ok=True)
    (COUNCIL / "history").mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

def load_workers():
    if not WORKERS_FILE.exists():
        return []
    try:
        return json.loads(
            WORKERS_FILE.read_text()
        ).get("workers", [])
    except Exception:
        return []

def msg_id(worker_id, topic, text):
    raw = f"{worker_id}|{topic}|{text}|{now()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:14]

def append_message(worker, topic, text, kind="observation",
                   confidence=50, risk="medium", recommendation="review"):

    record = {
        "id": msg_id(worker["id"], topic, text),
        "timestamp": now(),
        "worker_id": worker["id"],
        "worker_role": worker["role"],
        "topic": topic,
        "kind": kind,
        "message": text,
        "confidence": max(0, min(100, int(confidence))),
        "risk": risk,
        "recommendation": recommendation
    }

    with MESSAGES.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(record, ensure_ascii=False)
            + "\n"
        )

    return record

def read_messages():
    if not MESSAGES.exists():
        return []

    result = []

    for line in MESSAGES.read_text(
        encoding="utf-8"
    ).splitlines():
        try:
            result.append(json.loads(line))
        except Exception:
            pass

    return result[-500:]

def seed_worker_views(workers):
    existing = read_messages()

    existing_ids = {
        (m.get("worker_id"), m.get("topic"))
        for m in existing
    }

    for w in workers:

        role = w["role"]
        mission = w["mission"]

        key = (w["id"], mission)

        if key in existing_ids:
            continue

        if role == "Security Review Worker":
            append_message(
                w,
                mission,
                "Geen merge zonder secret scan en security-check.",
                kind="constraint",
                confidence=95,
                risk="high",
                recommendation="require-security"
            )

        elif role == "Test Worker":
            append_message(
                w,
                mission,
                "Geen merge zonder reproduceerbare tests op gewijzigde code.",
                kind="constraint",
                confidence=95,
                risk="high",
                recommendation="require-tests"
            )

        elif role == "Repair Worker":
            append_message(
                w,
                mission,
                "Controleer eerst bestaand incident en bestaande open repair-PR.",
                confidence=85,
                risk="medium",
                recommendation="reuse-existing-fix"
            )

        elif role == "GitHub Worker":
            append_message(
                w,
                mission,
                "Controleer open PR's en duplicate branches voordat nieuwe code wordt gemaakt.",
                confidence=90,
                risk="medium",
                recommendation="deduplicate"
            )

        elif role == "Hosting Worker":
            append_message(
                w,
                mission,
                "Publieke domein-health moet apart van lokale localhost-health worden bewezen.",
                confidence=90,
                risk="high",
                recommendation="require-healthcheck"
            )

        elif role == "Website Worker":
            append_message(
                w,
                mission,
                "Alleen werkende of duidelijk als LAB gemarkeerde functies publiceren.",
                confidence=90,
                risk="medium",
                recommendation="truthful-publication"
            )

        else:
            append_message(
                w,
                mission,
                "Analyseer kleinste veilige actie met aantoonbare impact.",
                confidence=75,
                risk="medium",
                recommendation="smallest-action"
            )

def score_messages(messages):
    scored = []

    for m in messages:

        weight = ROLE_WEIGHT.get(
            m["worker_role"],
            1.0
        )

        confidence = m.get(
            "confidence",
            50
        )

        risk_factor = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.25,
            "critical": 1.5,
        }.get(
            m.get("risk", "medium"),
            1.0
        )

        score = round(
            confidence
            * weight
            * risk_factor,
            2
        )

        item = dict(m)
        item["weighted_score"] = score

        scored.append(item)

    return sorted(
        scored,
        key=lambda x: x["weighted_score"],
        reverse=True
    )

def detect_blockers(messages):

    blockers = []

    for m in messages:

        if (
            m["worker_role"] in BLOCKING_ROLES
            and m["kind"] == "constraint"
        ):
            blockers.append({
                "role": m["worker_role"],
                "requirement": m["recommendation"],
                "message": m["message"]
            })

    return blockers

def choose_action(messages):

    recommendations = {}

    for m in messages:

        rec = m.get("recommendation")

        if not rec:
            continue

        recommendations.setdefault(
            rec,
            {
                "score": 0,
                "votes": 0
            }
        )

        recommendations[rec]["score"] += (
            m.get("weighted_score", 0)
        )

        recommendations[rec]["votes"] += 1

    if not recommendations:
        return {
            "action": "review",
            "reason": "No usable worker recommendations."
        }

    best = max(
        recommendations.items(),
        key=lambda kv: (
            kv[1]["score"],
            kv[1]["votes"]
        )
    )

    return {
        "action": best[0],
        "votes": best[1]["votes"],
        "score": round(
            best[1]["score"],
            2
        )
    }

def main():

    ensure()

    workers = load_workers()

    if not workers:
        print("ℹ️ Geen workers beschikbaar")
        return

    seed_worker_views(workers)

    messages = read_messages()

    candidate = workers[0].get(
        "mission",
        "unknown"
    )

    relevant = [
        m for m in messages
        if m.get("topic") == candidate
    ]

    scored = score_messages(
        relevant
    )

    blockers = detect_blockers(
        scored
    )

    decision = choose_action(
        scored
    )

    result = {
        "generated": now(),
        "topic": candidate,
        "worker_count": len(workers),
        "messages": scored,
        "blockers": blockers,
        "decision": decision,
        "merge_policy": {
            "bot_branch_only": True,
            "tests_required": True,
            "security_required": True,
            "healthcheck_required": True,
            "blind_merge": False
        }
    }

    LATEST.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    (
        COUNCIL
        / "history"
        / f"council-{stamp}.json"
    ).write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )

    report = [
        "# Mikis13 Bot Council",
        "",
        f"Generated: {result['generated']}",
        "",
        f"Topic: **{candidate}**",
        "",
        f"Workers: **{len(workers)}**",
        "",
        "## Overleg",
        ""
    ]

    for m in scored:
        report += [
            f"### {m['worker_role']}",
            "",
            m["message"],
            "",
            f"- confidence: {m['confidence']}%",
            f"- risk: {m['risk']}",
            f"- recommendation: `{m['recommendation']}`",
            f"- weighted score: {m['weighted_score']}",
            ""
        ]

    report += [
        "## Council decision",
        "",
        f"**{decision['action']}**",
        "",
        f"Votes: {decision.get('votes', 0)}",
        "",
        f"Score: {decision.get('score', 0)}",
        "",
        "## Blocking requirements",
        ""
    ]

    for b in blockers:
        report.append(
            f"- {b['role']}: {b['message']}"
        )

    report += [
        "",
        "## Merge gate",
        "",
        "- bot branch required",
        "- tests required",
        "- security scan required",
        "- healthcheck required",
        "- never blind merge",
        ""
    ]

    (
        REPORTS
        / "bot-council-latest.md"
    ).write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print(
        json.dumps(
            result["decision"],
            indent=2,
            ensure_ascii=False
        )
    )

if __name__ == "__main__":
    main()
