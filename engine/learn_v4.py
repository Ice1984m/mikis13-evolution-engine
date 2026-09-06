#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import sqlite3
import subprocess
import hashlib
import json
import os
import re

HOME = Path.home()
ROOT = HOME / "mikis13-evolution-engine"

STATE = ROOT / "state"
REPORTS = ROOT / "reports"

LEARNING = STATE / "learning"
KNOWLEDGE = STATE / "knowledge"
BLUEPRINTS = STATE / "blueprints"
GRAPH = STATE / "project-graph"
HISTORY = STATE / "history"

DB = LEARNING / "learning.db"

OWNER = os.getenv(
    "OWNER",
    "Ice1984m"
)

INBOXES = [
    HOME / "storage/shared/Download/Mikis13-Inbox",
    HOME / "storage/documents/Mikis13-Inbox",
    HOME / "storage/downloads/Mikis13-Inbox",
]

SAFE_EXT = {
    ".txt",
    ".md",
    ".json",
    ".ipynb",
    ".sh",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".yml",
    ".yaml",
}

SENSITIVE_NAME = re.compile(
    r"(password|passwd|credential|secret|token|"
    r"api[-_ ]?key|private[-_ ]?key|wallet|"
    r"mnemonic|seed|cookie|session)",
    re.I,
)

SECRET_PATTERNS = [
    re.compile(
        r"sk-[A-Za-z0-9_-]{20,}"
    ),
    re.compile(
        r"gh[pousr]_[A-Za-z0-9]{20,}"
    ),
    re.compile(
        r"AIza[A-Za-z0-9_-]{20,}"
    ),
    re.compile(
        r"AKIA[A-Z0-9]{16}"
    ),
    re.compile(
        r"(?i)(api[_ -]?key|token|secret)"
        r"\s*[:=]\s*['\"]?[A-Za-z0-9._-]{12,}"
    ),
]

IDEA_WORDS = {
    "idee",
    "idea",
    "bouwen",
    "bouw",
    "maken",
    "maak",
    "app",
    "website",
    "bot",
    "repair",
    "monitor",
    "automatisch",
    "automation",
    "tool",
    "programma",
    "project",
    "verbeter",
    "ontwikkel",
    "ontwikkeling",
    "security",
    "hosting",
    "ai",
    "dashboard",
    "service",
    "business",
    "inkomsten",
    "mvp",
    "prototype",
    "todo",
}

STOP = {
    "de","het","een","en","van","voor","met","naar","op",
    "in","is","dat","dit","die","te","om","ik","je","kan",
    "kunnen","the","a","an","and","to","for","with","of",
    "on","it","this","that","be","as"
}


def utcnow():
    return datetime.now(
        timezone.utc
    ).isoformat()


def ensure_dirs():
    for p in (
        STATE,
        REPORTS,
        LEARNING,
        KNOWLEDGE,
        BLUEPRINTS,
        GRAPH,
        HISTORY,
        STATE / "ideas",
        STATE / "experiments",
    ):
        p.mkdir(
            parents=True,
            exist_ok=True
        )


def run(cmd):
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    return (
        p.returncode,
        p.stdout.strip()
    )


def repo_inventory():
    code, output = run([
        "gh",
        "repo",
        "list",
        OWNER,
        "--limit",
        "200",
        "--json",
        "name,description,url,isArchived"
    ])

    if code:
        return []

    try:
        return json.loads(output)
    except Exception:
        return []


def database():
    con = sqlite3.connect(DB)

    con.executescript("""
    CREATE TABLE IF NOT EXISTS documents(
      fingerprint TEXT PRIMARY KEY,
      basename TEXT,
      extension TEXT,
      size INTEGER,
      modified REAL,
      last_seen TEXT
    );

    CREATE TABLE IF NOT EXISTS concepts(
      fingerprint TEXT PRIMARY KEY,
      normalized TEXT,
      title TEXT,
      occurrences INTEGER DEFAULT 1,
      first_seen TEXT,
      last_seen TEXT,
      score INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS sources(
      concept_fingerprint TEXT,
      document_fingerprint TEXT,
      source_name TEXT,
      UNIQUE(
        concept_fingerprint,
        document_fingerprint
      )
    );

    CREATE TABLE IF NOT EXISTS repo_links(
      concept_fingerprint TEXT,
      repo TEXT,
      strength INTEGER,
      UNIQUE(
        concept_fingerprint,
        repo
      )
    );

    CREATE TABLE IF NOT EXISTS cycles(
      id TEXT PRIMARY KEY,
      generated TEXT,
      documents INTEGER,
      concepts INTEGER,
      top_score INTEGER
    );
    """)

    con.commit()
    return con


def redact(text):
    result = text

    for pattern in SECRET_PATTERNS:
        result = pattern.sub(
            "[REDACTED_SECRET]",
            result
        )

    return result


def safe_file(path):

    if path.suffix.lower() not in SAFE_EXT:
        return False

    if SENSITIVE_NAME.search(
        path.name
    ):
        return False

    try:
        size = path.stat().st_size
    except Exception:
        return False

    return (
        0 < size <= 2_000_000
    )


def fingerprint(data):
    return hashlib.sha256(
        data.encode(
            "utf-8",
            errors="ignore"
        )
    ).hexdigest()


def normalize(sentence):

    sentence = sentence.lower()

    sentence = re.sub(
        r"https?://\S+",
        "",
        sentence
    )

    sentence = re.sub(
        r"[^a-z0-9à-ÿ _-]+",
        " ",
        sentence
    )

    words = [
        x for x in sentence.split()
        if x not in STOP
        and len(x) > 2
    ]

    return " ".join(words[:40])


def title_for(normalized):

    words = normalized.split()

    if not words:
        return "Unnamed concept"

    return " ".join(
        words[:8]
    ).title()


def extract_sentences(text):

    text = redact(text)

    # Notebook blijft lokale bron.
    # Alleen platte tekstsignalen worden gebruikt.
    text = text.replace(
        "\\n",
        "\n"
    )

    parts = re.split(
        r"[\n.!?]+",
        text
    )

    results = []

    for part in parts:

        line = " ".join(
            part.split()
        ).strip()

        if len(line) < 20:
            continue

        if len(line) > 500:
            line = line[:500]

        low = line.lower()

        hits = sum(
            1 for word in IDEA_WORDS
            if word in low
        )

        if hits == 0:
            continue

        normalized = normalize(
            line
        )

        if len(
            normalized.split()
        ) < 3:
            continue

        results.append(
            (
                line,
                normalized,
                hits
            )
        )

    return results


def scan_documents(con):

    discovered = []

    seen_paths = set()

    for inbox in INBOXES:

        if not inbox.exists():
            continue

        for p in inbox.rglob("*"):

            if not p.is_file():
                continue

            try:
                real = str(
                    p.resolve()
                )
            except Exception:
                continue

            if real in seen_paths:
                continue

            seen_paths.add(real)

            if not safe_file(p):
                continue

            try:
                text = p.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )
            except Exception:
                continue

            stat = p.stat()

            doc_fp = fingerprint(
                f"{p.name}|{stat.st_size}|{text[:5000]}"
            )

            con.execute("""
            INSERT INTO documents(
              fingerprint,
              basename,
              extension,
              size,
              modified,
              last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint)
            DO UPDATE SET
              last_seen=excluded.last_seen
            """, (
                doc_fp,
                p.name,
                p.suffix.lower(),
                stat.st_size,
                stat.st_mtime,
                utcnow()
            ))

            ideas = extract_sentences(
                text
            )

            discovered.append({
                "name": p.name,
                "fingerprint": doc_fp,
                "ideas": ideas
            })

    con.commit()
    return discovered


def update_concepts(
    con,
    docs
):

    current = {}

    for doc in docs:

        for original, normalized, hits in doc["ideas"]:

            cfp = fingerprint(
                normalized
            )[:24]

            row = con.execute(
                """
                SELECT occurrences
                FROM concepts
                WHERE fingerprint=?
                """,
                (cfp,)
            ).fetchone()

            if row:

                con.execute("""
                UPDATE concepts
                SET
                  occurrences=occurrences+1,
                  last_seen=?
                WHERE fingerprint=?
                """, (
                    utcnow(),
                    cfp
                ))

            else:

                con.execute("""
                INSERT INTO concepts(
                  fingerprint,
                  normalized,
                  title,
                  occurrences,
                  first_seen,
                  last_seen
                )
                VALUES (?, ?, ?, 1, ?, ?)
                """, (
                    cfp,
                    normalized,
                    title_for(
                        normalized
                    ),
                    utcnow(),
                    utcnow()
                ))

            con.execute("""
            INSERT OR IGNORE INTO sources(
              concept_fingerprint,
              document_fingerprint,
              source_name
            )
            VALUES (?, ?, ?)
            """, (
                cfp,
                doc["fingerprint"],
                doc["name"]
            ))

            current[cfp] = {
                "original": original,
                "hits": hits
            }

    con.commit()
    return current


def concept_words(text):
    return {
        x for x in text.lower().split()
        if len(x) >= 4
        and x not in STOP
    }


def match_repositories(
    con,
    repos
):

    rows = con.execute("""
    SELECT
      fingerprint,
      normalized
    FROM concepts
    """).fetchall()

    for fp, normalized in rows:

        cwords = concept_words(
            normalized
        )

        for repo in repos:

            repo_text = (
                repo.get(
                    "name",
                    ""
                )
                + " "
                + (
                    repo.get(
                        "description"
                    ) or ""
                )
            ).lower()

            rwords = concept_words(
                repo_text.replace(
                    "-",
                    " "
                )
            )

            overlap = len(
                cwords.intersection(
                    rwords
                )
            )

            if overlap == 0:
                continue

            strength = min(
                100,
                overlap * 20
            )

            con.execute("""
            INSERT INTO repo_links(
              concept_fingerprint,
              repo,
              strength
            )
            VALUES (?, ?, ?)
            ON CONFLICT(
              concept_fingerprint,
              repo
            )
            DO UPDATE SET
              strength=excluded.strength
            """, (
                fp,
                repo["name"],
                strength
            ))

    con.commit()


def score_concepts(con):

    rows = con.execute("""
    SELECT
      fingerprint,
      normalized,
      title,
      occurrences
    FROM concepts
    """).fetchall()

    scored = []

    for fp, normalized, title, occurrences in rows:

        source_count = con.execute("""
        SELECT COUNT(*)
        FROM sources
        WHERE concept_fingerprint=?
        """, (
            fp,
        )).fetchone()[0]

        links = con.execute("""
        SELECT
          repo,
          strength
        FROM repo_links
        WHERE concept_fingerprint=?
        ORDER BY strength DESC
        """, (
            fp,
        )).fetchall()

        score = 35

        score += min(
            20,
            occurrences * 3
        )

        score += min(
            15,
            source_count * 4
        )

        if links:
            score += 15

        low = normalized.lower()

        if any(
            x in low
            for x in (
                "automation",
                "automatisch",
                "repair",
                "monitor",
                "security",
                "hosting",
                "dashboard",
                "ai"
            )
        ):
            score += 10

        if any(
            x in low
            for x in (
                "business",
                "klant",
                "service",
                "website"
            )
        ):
            score += 5

        score = min(
            100,
            score
        )

        con.execute("""
        UPDATE concepts
        SET score=?
        WHERE fingerprint=?
        """, (
            score,
            fp
        ))

        scored.append({
            "fingerprint": fp,
            "title": title,
            "normalized": normalized,
            "occurrences": occurrences,
            "sources": source_count,
            "score": score,
            "repo_links": [
                {
                    "repo": repo,
                    "strength": strength
                }
                for repo, strength in links
            ]
        })

    con.commit()

    return sorted(
        scored,
        key=lambda x: (
            x["score"],
            x["occurrences"],
            x["sources"]
        ),
        reverse=True
    )


def build_graph(
    concepts,
    repos
):

    nodes = []
    edges = []

    used_repos = set()

    for concept in concepts[:50]:

        cid = (
            "concept:"
            + concept["fingerprint"]
        )

        nodes.append({
            "id": cid,
            "type": "concept",
            "label": concept["title"],
            "score": concept["score"]
        })

        for link in concept["repo_links"]:

            repo = link["repo"]

            rid = (
                "repo:"
                + repo
            )

            if repo not in used_repos:

                used_repos.add(
                    repo
                )

                nodes.append({
                    "id": rid,
                    "type": "repository",
                    "label": repo
                })

            edges.append({
                "from": cid,
                "to": rid,
                "type": "reuse_candidate",
                "strength":
                    link["strength"]
            })

    graph = {
        "generated": utcnow(),
        "nodes": nodes,
        "edges": edges
    }

    path = (
        GRAPH
        / "latest.json"
    )

    path.write_text(
        json.dumps(
            graph,
            ensure_ascii=False,
            indent=2
        )
        + "\n"
    )

    return path


def make_blueprint(
    best
):

    existing = [
        x["repo"]
        for x in best[
            "repo_links"
        ][:5]
    ]

    blueprint = {
        "version": 4,
        "created": utcnow(),
        "status": "RESEARCH",
        "concept_fingerprint":
            best["fingerprint"],
        "title":
            best["title"],
        "evidence": {
            "score":
                best["score"],
            "occurrences":
                best["occurrences"],
            "independent_sources":
                best["sources"]
        },
        "reuse_candidates":
            existing,
        "principle":
            "Reuse before creating another repository.",
        "problem_hypothesis":
            best["normalized"],
        "development_loop": [
            "inspect existing repositories",
            "identify reusable components",
            "define one measurable problem",
            "create smallest experiment",
            "write automated test",
            "run security check",
            "measure outcome",
            "keep improve merge pause or delete"
        ],
        "automatic_actions_allowed": [
            "research",
            "local analysis",
            "blueprint generation",
            "project graph updates",
            "test generation",
            "bot branch",
            "pull request"
        ],
        "automatic_actions_blocked": [
            "publish secrets",
            "upload raw notes",
            "paid advertising",
            "purchases",
            "payments",
            "crypto trading",
            "blind main merge"
        ],
        "next_action":
            (
                "Inspect reuse candidates before "
                "creating implementation."
                if existing
                else
                "Create a minimal local experiment first."
            )
    }

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        best["title"].lower()
    ).strip("-")[:60]

    folder = (
        BLUEPRINTS
        / f"v4-{slug}"
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    json_path = (
        folder
        / "BLUEPRINT.json"
    )

    json_path.write_text(
        json.dumps(
            blueprint,
            ensure_ascii=False,
            indent=2
        )
        + "\n"
    )

    md = [
        f"# {best['title']}",
        "",
        "**Status: RESEARCH**",
        "",
        f"Evidence score: **{best['score']}/100**",
        "",
        f"Occurrences: **{best['occurrences']}**",
        "",
        f"Independent sources: **{best['sources']}**",
        "",
        "## Existing repositories to inspect",
        ""
    ]

    if existing:
        md.extend(
            f"- `{x}`"
            for x in existing
        )
    else:
        md.append(
            "- none detected"
        )

    md.extend([
        "",
        "## Hypothesis",
        "",
        best["normalized"],
        "",
        "## Next step",
        "",
        blueprint["next_action"],
        ""
    ])

    (
        folder
        / "BLUEPRINT.md"
    ).write_text(
        "\n".join(md)
    )

    return json_path


def report(
    documents,
    concepts,
    graph,
    blueprint
):

    path = (
        REPORTS
        / "learning-v4-latest.md"
    )

    lines = [
        "# Mikis13 Learning V4",
        "",
        f"Generated: {utcnow()}",
        "",
        "## Result",
        "",
        f"- Inbox documents processed: **{len(documents)}**",
        f"- Learned concepts stored: **{len(concepts)}**",
        "",
        "## Top learned concepts",
        ""
    ]

    for c in concepts[:10]:

        repos = ", ".join(
            x["repo"]
            for x in c[
                "repo_links"
            ][:3]
        )

        if not repos:
            repos = "none"

        lines.append(
            f"- **{c['score']}/100** "
            f"{c['title']} — "
            f"{c['occurrences']} occurrence(s) — "
            f"reuse: {repos}"
        )

    lines.extend([
        "",
        "## Project graph",
        "",
        f"`{graph.relative_to(ROOT)}`",
        "",
        "## Best blueprint",
        "",
        (
            f"`{blueprint.relative_to(ROOT)}`"
            if blueprint
            else "No blueprint yet."
        ),
        "",
        "## Privacy",
        "",
        "Raw notes are not committed or uploaded.",
        "",
        "Detected credential-like strings are redacted before analysis.",
        "",
        "The learning database remains local.",
        ""
    ])

    path.write_text(
        "\n".join(lines)
    )

    return path


def main():

    ensure_dirs()

    con = database()

    print(
        "🧠 Mikis13 Learning V4"
    )

    docs = scan_documents(
        con
    )

    print(
        f"📓 {len(docs)} veilige documenten gelezen"
    )

    current = update_concepts(
        con,
        docs
    )

    repos = repo_inventory()

    print(
        f"🐙 {len(repos)} GitHub repositories vergeleken"
    )

    match_repositories(
        con,
        repos
    )

    concepts = score_concepts(
        con
    )

    graph = build_graph(
        concepts,
        repos
    )

    blueprint = None

    if concepts:
        blueprint = make_blueprint(
            concepts[0]
        )

    report_path = report(
        docs,
        concepts,
        graph,
        blueprint
    )

    result = {
        "generated": utcnow(),
        "documents_processed":
            len(docs),
        "concepts":
            len(concepts),
        "top_concept":
            concepts[0]
            if concepts else None,
        "graph":
            str(graph),
        "blueprint":
            str(blueprint)
            if blueprint else None,
        "report":
            str(report_path)
    }

    (
        LEARNING
        / "latest.json"
    ).write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
        + "\n"
    )

    history = (
        HISTORY
        / (
            "learning-v4-"
            + datetime.now().strftime(
                "%Y%m%d-%H%M%S"
            )
            + ".json"
        )
    )

    history.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
        + "\n"
    )

    print()
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
