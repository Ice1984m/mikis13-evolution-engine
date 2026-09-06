#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import subprocess
import hashlib
import json
import os
import re

HOME = Path.home()
ROOT = HOME / "mikis13-evolution-engine"

STATE = ROOT / "state"
REPORTS = ROOT / "reports"

COUNCIL = STATE / "council"
COORD = STATE / "coordinator"
TASKS = STATE / "tasks"
LOCKS = STATE / "locks"
FAILURES = STATE / "failure-memory"
MATURITY = STATE / "maturity"

POLICY_FILE = ROOT / "config/council-v6-policy.json"

OWNER = os.getenv("OWNER", "Ice1984m")

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def ensure_dirs():
    for p in (
        COUNCIL,
        COUNCIL / "history",
        COORD,
        COORD / "history",
        TASKS,
        LOCKS,
        FAILURES,
        MATURITY,
        REPORTS,
    ):
        p.mkdir(parents=True, exist_ok=True)

def read_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ) + "\n"
    )

def run(cmd):
    p = subprocess.run(
        cmd,
        text=True,
        capture_output=True
    )
    return (
        p.returncode,
        p.stdout.strip(),
        p.stderr.strip()
    )

def policy():
    return read_json(
        POLICY_FILE,
        {}
    )

def normalize(text):
    text = (text or "").lower()
    text = re.sub(
        r"https?://\S+",
        "",
        text
    )
    text = re.sub(
        r"[^a-z0-9à-ÿ]+",
        " ",
        text
    )
    return " ".join(text.split())

def fingerprint(text):
    return hashlib.sha256(
        normalize(text).encode()
    ).hexdigest()[:20]

# ============================================================
# GITHUB INVENTORY
# ============================================================

def repositories():
    code, out, _ = run([
        "gh",
        "repo",
        "list",
        OWNER,
        "--limit",
        "200",
        "--json",
        (
            "name,description,isArchived,"
            "isFork,updatedAt,url,"
            "primaryLanguage"
        )
    ])

    if code:
        return []

    try:
        return json.loads(out)
    except Exception:
        return []

def open_prs():
    code, out, _ = run([
        "gh",
        "search",
        "prs",
        "--owner",
        OWNER,
        "--state",
        "open",
        "--limit",
        "200",
        "--json",
        (
            "number,title,repository,"
            "url,updatedAt"
        )
    ])

    if code:
        return []

    try:
        return json.loads(out)
    except Exception:
        return []

# ============================================================
# MATURITY
# ============================================================

def maturity_score(repo):

    score = 0
    reasons = []

    if repo.get("isArchived"):
        return {
            "score": 0,
            "reasons": ["archived"]
        }

    if repo.get("description"):
        score += 10
        reasons.append("description")

    if repo.get("primaryLanguage"):
        score += 15
        reasons.append("source-code")

    name = repo.get("name", "")

    code, out, _ = run([
        "gh",
        "api",
        f"repos/{OWNER}/{name}/contents",
        "--jq",
        ".[].name"
    ])

    files = set(
        out.splitlines()
        if code == 0
        else []
    )

    if "README.md" in files:
        score += 10
        reasons.append("readme")

    if (
        "package.json" in files
        or "pyproject.toml" in files
        or "requirements.txt" in files
        or "Cargo.toml" in files
        or "go.mod" in files
    ):
        score += 15
        reasons.append("dependency-manifest")

    if (
        "tests" in files
        or "test" in files
    ):
        score += 15
        reasons.append("tests")

    if ".github" in files:
        score += 15
        reasons.append("automation")

    if (
        "Dockerfile" in files
        or "docker-compose.yml" in files
    ):
        score += 10
        reasons.append("runtime")

    if (
        "index.html" in files
        or "public" in files
        or "src" in files
    ):
        score += 10
        reasons.append("product-content")

    return {
        "score": min(100, score),
        "reasons": reasons
    }

def build_maturity_inventory(repos):

    result = []

    for repo in repos:

        m = maturity_score(repo)

        result.append({
            "repo": repo["name"],
            "url": repo["url"],
            "score": m["score"],
            "reasons": m["reasons"]
        })

    result.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    write_json(
        MATURITY / "latest.json",
        {
            "generated": utcnow(),
            "repositories": result
        }
    )

    return result

# ============================================================
# CANDIDATES
# ============================================================

def candidate_sources():

    candidates = []

    evolution = read_json(
        STATE / "latest-result.json",
        {}
    ) or {}

    learning = read_json(
        STATE / "learning/latest.json",
        {}
    ) or {}

    council = read_json(
        COUNCIL / "latest.json",
        {}
    ) or {}

    if evolution.get("best_idea"):

        item = evolution["best_idea"]

        candidates.append({
            "source": "evolution",
            "title": (
                item.get("title")
                or "Evolution candidate"
            ),
            "description": json.dumps(
                item,
                ensure_ascii=False
            ),
            "base_score": int(
                item.get("score", 60)
                if isinstance(item, dict)
                else 60
            )
        })

    if learning.get("top_concept"):

        item = learning["top_concept"]

        candidates.append({
            "source": "learning",
            "title": (
                item.get("title")
                or "Learning candidate"
            ),
            "description": (
                item.get("normalized")
                or json.dumps(
                    item,
                    ensure_ascii=False
                )
            ),
            "base_score": int(
                item.get("score", 60)
            )
        })

    decision = council.get(
        "decision",
        {}
    )

    if council.get("topic"):

        candidates.append({
            "source": "council",
            "title": council["topic"],
            "description": (
                decision.get("action")
                or council["topic"]
            ),
            "base_score": min(
                100,
                int(
                    decision.get(
                        "score",
                        60
                    )
                )
            )
        })

    unique = {}

    for c in candidates:

        fp = fingerprint(
            c["title"]
            + " "
            + c["description"]
        )

        if (
            fp not in unique
            or c["base_score"]
            > unique[fp]["base_score"]
        ):
            c["fingerprint"] = fp
            unique[fp] = c

    return list(
        unique.values()
    )

# ============================================================
# DUPLICATE DETECTOR
# ============================================================

def words(text):
    return {
        x for x in normalize(text).split()
        if len(x) >= 4
    }

def similarity(a, b):

    aw = words(a)
    bw = words(b)

    if not aw or not bw:
        return 0

    return int(
        100
        * len(aw & bw)
        / len(aw | bw)
    )

def duplicate_check(candidate, prs):

    best = None

    source_text = (
        candidate["title"]
        + " "
        + candidate["description"]
    )

    for pr in prs:

        repo = pr.get(
            "repository",
            {}
        )

        if isinstance(repo, dict):
            repo_name = repo.get(
                "nameWithOwner",
                ""
            )
        else:
            repo_name = str(repo)

        pr_text = (
            str(pr.get("title", ""))
            + " "
            + repo_name
        )

        sim = similarity(
            source_text,
            pr_text
        )

        if (
            best is None
            or sim > best["similarity"]
        ):
            best = {
                "similarity": sim,
                "title": pr.get("title"),
                "number": pr.get("number"),
                "repository": repo_name,
                "url": pr.get("url")
            }

    if (
        best
        and best["similarity"] >= 45
    ):
        return {
            "duplicate": True,
            "match": best
        }

    return {
        "duplicate": False,
        "match": best
    }

# ============================================================
# FAILURE MEMORY
# ============================================================

def failure_memory():

    file = FAILURES / "memory.json"

    memory = read_json(
        file,
        {
            "version": 2,
            "signatures": {}
        }
    )

    return memory

def save_failure_memory(memory):
    write_json(
        FAILURES / "memory.json",
        memory
    )

def failure_penalty(candidate, memory):

    text = normalize(
        candidate["title"]
        + " "
        + candidate["description"]
    )

    penalty = 0
    previous = []

    for sig, record in memory[
        "signatures"
    ].items():

        if sig in text:

            attempts = int(
                record.get(
                    "attempts",
                    0
                )
            )

            success = int(
                record.get(
                    "successes",
                    0
                )
            )

            previous.append(record)

            if (
                attempts >= 2
                and success == 0
            ):
                penalty += 25

    return min(
        50,
        penalty
    ), previous

# ============================================================
# EVIDENCE GATE
# ============================================================

def evidence(candidate, duplicate, maturity):

    score = candidate["base_score"]

    evidence = []

    if candidate["source"] == "council":
        score += 10
        evidence.append(
            "council-consensus"
        )

    if candidate["source"] == "learning":
        score += 5
        evidence.append(
            "learning-memory"
        )

    if candidate["source"] == "evolution":
        score += 5
        evidence.append(
            "evolution-analysis"
        )

    if duplicate.get("duplicate"):
        score += 10
        evidence.append(
            "existing-pr"
        )

    related = []

    cwords = words(
        candidate["title"]
        + " "
        + candidate["description"]
    )

    for repo in maturity:

        rwords = words(
            repo["repo"]
        )

        overlap = len(
            cwords & rwords
        )

        if overlap:

            related.append({
                "repo": repo["repo"],
                "maturity": repo["score"],
                "overlap": overlap
            })

    related.sort(
        key=lambda x: (
            x["overlap"],
            x["maturity"]
        ),
        reverse=True
    )

    if related:
        score += min(
            15,
            related[0]["maturity"] // 10
        )
        evidence.append(
            "existing-repository"
        )

    return {
        "score": min(100, score),
        "evidence": evidence,
        "related_repositories": related[:5]
    }

# ============================================================
# TASK LOCK
# ============================================================

def active_lock():

    path = LOCKS / "active.json"

    lock = read_json(
        path
    )

    if not lock:
        return None

    if lock.get("status") in (
        "ACTIVE",
        "WAITING_CHECKS"
    ):
        return lock

    return None

def create_lock(task):

    lock = {
        "id": task["id"],
        "status": "ACTIVE",
        "created": utcnow(),
        "title": task["title"],
        "selected_action":
            task["selected_action"]
    }

    write_json(
        LOCKS / "active.json",
        lock
    )

    return lock

# ============================================================
# TASK SELECTION
# ============================================================

def choose_task(
    candidates,
    prs,
    maturity,
    memory,
    pol
):

    ranked = []

    for candidate in candidates:

        duplicate = duplicate_check(
            candidate,
            prs
        )

        ev = evidence(
            candidate,
            duplicate,
            maturity
        )

        penalty, previous = (
            failure_penalty(
                candidate,
                memory
            )
        )

        score = (
            ev["score"]
            - penalty
        )

        if duplicate["duplicate"]:

            action = (
                "UPDATE_EXISTING_PR"
            )

        elif (
            ev[
                "related_repositories"
            ]
        ):

            action = (
                "IMPROVE_EXISTING_REPO"
            )

        else:

            action = (
                "RESEARCH_ONLY"
            )

        ranked.append({
            **candidate,
            "evidence_score": score,
            "evidence": ev["evidence"],
            "related_repositories":
                ev[
                    "related_repositories"
                ],
            "duplicate":
                duplicate,
            "failure_penalty":
                penalty,
            "previous_failures":
                previous,
            "selected_action":
                action
        })

    ranked.sort(
        key=lambda x:
            x["evidence_score"],
        reverse=True
    )

    minimum = int(
        pol.get(
            "minimum_evidence_score",
            60
        )
    )

    eligible = [
        x for x in ranked
        if x["evidence_score"] >= minimum
    ]

    if not eligible:
        return None, ranked

    return eligible[0], ranked

# ============================================================
# ROLLBACK PLAN
# ============================================================

def rollback_plan(task):

    return {
        "before_change": [
            "record current branch SHA",
            "record current workflow status",
            "record current healthcheck result"
        ],

        "rollback": [
            "do not merge failing PR",
            "close bot PR when invalid",
            "delete bot branch only after review",
            "restore previous tested commit if already deployed"
        ],

        "required_after_change": [
            "tests green",
            "security scan green",
            "healthcheck green"
        ]
    }

# ============================================================
# REPORT
# ============================================================

def make_report(
    selected,
    ranked,
    maturity,
    lock
):

    lines = [
        "# Mikis13 Autonomous Council V6",
        "",
        f"Generated: {utcnow()}",
        "",
        "## Coordinator",
        ""
    ]

    if selected:

        lines += [
            f"Selected: **{selected['title']}**",
            "",
            (
                "Action: "
                f"`{selected['selected_action']}`"
            ),
            "",
            (
                "Evidence score: "
                f"**{selected['evidence_score']}/100**"
            ),
            "",
            (
                "Task lock: "
                f"`{lock['id']}`"
            ),
            ""
        ]

        duplicate = selected[
            "duplicate"
        ]

        if duplicate.get(
            "duplicate"
        ):

            m = duplicate["match"]

            lines += [
                "### Existing work detected",
                "",
                (
                    f"- PR #{m['number']} "
                    f"{m['title']}"
                ),
                (
                    f"- Similarity: "
                    f"{m['similarity']}%"
                ),
                "",
                (
                    "**Decision:** update/review "
                    "existing work instead of "
                    "creating duplicate work."
                ),
                ""
            ]

    else:

        lines += [
            "No task passed Evidence Gate.",
            "",
            (
                "Result: research only; "
                "no implementation task started."
            ),
            ""
        ]

    lines += [
        "## Candidate ranking",
        ""
    ]

    for item in ranked[:10]:

        lines.append(
            "- "
            f"**{item['evidence_score']}/100** "
            f"{item['title']} → "
            f"`{item['selected_action']}`"
        )

    lines += [
        "",
        "## Highest maturity repositories",
        ""
    ]

    for repo in maturity[:15]:

        lines.append(
            f"- **{repo['score']}/100** "
            f"`{repo['repo']}`"
        )

    lines += [
        "",
        "## Mandatory execution gate",
        "",
        "- exactly one active task",
        "- duplicate check before implementation",
        "- existing repository reuse first",
        "- bot branch only",
        "- syntax/unit tests required",
        "- security scan required",
        "- healthcheck required",
        "- rollback plan required",
        "- no blind merge",
        ""
    ]

    path = (
        REPORTS
        / "coordinator-v6-latest.md"
    )

    path.write_text(
        "\n".join(lines)
    )

    return path

# ============================================================
# MAIN
# ============================================================

def main():

    ensure_dirs()

    pol = policy()

    existing_lock = (
        active_lock()
    )

    if existing_lock:

        print(
            "🔒 Bestaande actieve taak:"
        )

        print(
            json.dumps(
                existing_lock,
                indent=2,
                ensure_ascii=False
            )
        )

        print(
            "\nGeen tweede taak gestart."
        )

        return

    print(
        "🐙 GitHub repositories analyseren..."
    )

    repos = repositories()

    print(
        f"✅ {len(repos)} repositories"
    )

    print(
        "📊 Repo maturity berekenen..."
    )

    maturity = (
        build_maturity_inventory(
            repos
        )
    )

    print(
        "🔎 Open PR's controleren..."
    )

    prs = open_prs()

    print(
        f"✅ {len(prs)} open PR's"
    )

    candidates = (
        candidate_sources()
    )

    print(
        f"💡 {len(candidates)} kandidaten"
    )

    memory = failure_memory()

    selected, ranked = choose_task(
        candidates,
        prs,
        maturity,
        memory,
        pol
    )

    lock = None

    if selected:

        task_id = fingerprint(
            selected["title"]
            + utcnow()
        )

        selected["id"] = task_id

        selected["created"] = (
            utcnow()
        )

        selected["rollback_plan"] = (
            rollback_plan(
                selected
            )
        )

        write_json(
            TASKS / "latest.json",
            selected
        )

        write_json(
            TASKS
            / f"{task_id}.json",
            selected
        )

        lock = create_lock(
            selected
        )

    report = make_report(
        selected,
        ranked,
        maturity,
        lock or {
            "id": "none"
        }
    )

    result = {
        "generated": utcnow(),
        "selected_task": selected,
        "candidate_count":
            len(candidates),
        "open_pr_count":
            len(prs),
        "repository_count":
            len(repos),
        "report":
            str(report)
    }

    write_json(
        COORD / "latest.json",
        result
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    write_json(
        COORD
        / "history"
        / f"{stamp}.json",
        result
    )

    print()

    if selected:

        print(
            "🎯 GESELECTEERDE TAAK"
        )

        print(
            json.dumps(
                selected,
                indent=2,
                ensure_ascii=False
            )
        )

    else:

        print(
            "ℹ️ Geen kandidaat door "
            "Evidence Gate."
        )

if __name__ == "__main__":
    main()
