#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timezone
import subprocess
import sqlite3
import hashlib
import json
import os
import re
import itertools

HOME = Path.home()
ROOT = HOME / "mikis13-evolution-engine"

STATE = ROOT / "state"
REPORTS = ROOT / "reports"
DB = STATE / "evolution.db"

OWNER = os.getenv("OWNER", "Ice1984m")

REPO_THRESHOLD = int(
    os.getenv("NEW_REPO_THRESHOLD", "85")
)

SCAN_ROOTS = [
    HOME / "storage" / "downloads",
    HOME / "storage" / "documents",
    HOME / "storage" / "shared",
    HOME
]

BLOCK_DIR = {
    ".git",
    ".ssh",
    ".gnupg",
    ".cache",
    ".npm",
    "node_modules",
    "__pycache__",
    "Android",
    "DCIM",
    "Pictures",
    "Movies",
    "Music",
    "WhatsApp",
    "Telegram",
    "Signal",
    "wallet",
    "wallets",
    "secrets"
}

SENSITIVE = (
    ".env",
    "password",
    "passwd",
    "privatekey",
    "private-key",
    "secret",
    "wallet",
    "mnemonic",
    "seedphrase",
    "credential",
    "cookie",
    "session",
    "apikey",
    "api-key"
)

BLOCK_EXT = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".kdbx"
}

CODE_EXT = {
    ".sh",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".php",
    ".java",
    ".kt",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".txt"
}

MARKERS = {
    "package.json": "node",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "Dockerfile": "container",
    "docker-compose.yml": "container",
    "index.html": "website",
    "composer.json": "php",
    "Cargo.toml": "rust",
    "go.mod": "go"
}

TODO_RE = re.compile(
    r"\b(TODO|FIXME|ROADMAP|UNFINISHED|HACK|LATER)\b",
    re.I
)


def now():
    return datetime.now(timezone.utc).isoformat()


def run(args, cwd=None):

    p = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    return p.returncode, p.stdout.strip(), p.stderr.strip()


def gh_json(args):

    code, out, _ = run(["gh", *args])

    if code:
        return None

    try:
        return json.loads(out)
    except Exception:
        return None


def slugify(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text
    )

    return text.strip("-")[:48]


def blocked(path):

    if set(path.parts).intersection(BLOCK_DIR):
        return True

    name = path.name.lower()

    if any(x in name for x in SENSITIVE):
        return True

    if path.suffix.lower() in BLOCK_EXT:
        return True

    return False


def db():

    STATE.mkdir(
        parents=True,
        exist_ok=True
    )

    con = sqlite3.connect(DB)

    con.executescript("""
    CREATE TABLE IF NOT EXISTS discoveries(
      path TEXT PRIMARY KEY,
      kind TEXT,
      score INTEGER,
      todos INTEGER,
      last_seen TEXT
    );

    CREATE TABLE IF NOT EXISTS ideas(
      signature TEXT PRIMARY KEY,
      title TEXT,
      source TEXT,
      score INTEGER,
      problem TEXT,
      solution TEXT,
      status TEXT,
      repo TEXT,
      first_seen TEXT,
      last_seen TEXT
    );

    CREATE TABLE IF NOT EXISTS cycles(
      cycle_id TEXT PRIMARY KEY,
      started TEXT,
      files INTEGER,
      projects INTEGER,
      repos INTEGER,
      ideas INTEGER,
      best_score INTEGER
    );
    """)

    con.commit()

    return con


def find_projects():

    candidates = {}
    seen_realpaths = set()

    def canonical(path):
        try:
            return str(path.resolve())
        except Exception:
            return str(path)

    def looks_like_project_root(path, files):
        markers = [
            marker for marker in MARKERS
            if marker in files
        ]

        if (path / ".git").exists():
            markers.append(".git")

        return markers

    for base in SCAN_ROOTS:

        if not base.exists():
            continue

        for root, dirs, files in os.walk(base):

            p = Path(root)

            dirs[:] = [
                d for d in dirs
                if d not in BLOCK_DIR
                and not blocked(p / d)
            ]

            real = canonical(p)

            if real in seen_realpaths:
                dirs[:] = []
                continue

            seen_realpaths.add(real)

            markers = looks_like_project_root(
                p,
                files
            )

            if not markers:
                continue

            # -------------------------------------------------
            # Nested project suppressie:
            # als een parent binnen 3 niveaus reeds een duidelijke
            # project-root is, behandel deze map niet opnieuw als
            # zelfstandig project tenzij hij zelf .git bevat.
            # -------------------------------------------------

            nested_parent = None

            current = p.parent

            for _ in range(3):

                parent_real = canonical(current)

                if parent_real in candidates:
                    nested_parent = parent_real
                    break

                if current == current.parent:
                    break

                current = current.parent

            has_git = (
                p / ".git"
            ).exists()

            if nested_parent and not has_git:
                continue

            marker_types = []

            for marker in markers:

                if marker == ".git":
                    marker_types.append("git")
                else:
                    marker_types.append(
                        MARKERS.get(
                            marker,
                            "unknown"
                        )
                    )

            todos = 0
            codefiles = 0

            for filename in files:

                f = p / filename

                if blocked(f):
                    continue

                if f.suffix.lower() not in CODE_EXT:
                    continue

                try:

                    if f.stat().st_size > 1_500_000:
                        continue

                    body = f.read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )

                    todos += len(
                        TODO_RE.findall(body)
                    )

                    codefiles += 1

                except Exception:
                    pass

            score = 25

            score += min(
                25,
                len(set(marker_types)) * 7
            )

            score += min(
                20,
                codefiles // 5
            )

            score += min(
                15,
                todos * 2
            )

            if has_git:
                score += 10

            # Backup/archive-namen krijgen lagere waarde.
            name_lower = p.name.lower()

            if any(
                x in name_lower
                for x in (
                    "backup",
                    "old",
                    "copy",
                    "archive",
                    "tmp"
                )
            ):
                score -= 15

            score = max(
                0,
                min(
                    100,
                    score
                )
            )

            candidates[real] = {
                "path": real,
                "types": sorted(
                    set(marker_types)
                ),
                "todos": todos,
                "codefiles": codefiles,
                "score": score
            }

    # ---------------------------------------------
    # Conceptuele duplicaten groeperen.
    # ---------------------------------------------

    by_name = {}

    for project in candidates.values():

        name = Path(
            project["path"]
        ).name.lower()

        clean_name = re.sub(
            r"[-_](backup|old|copy|archive)[-_0-9]*$",
            "",
            name
        )

        by_name.setdefault(
            clean_name,
            []
        ).append(
            project
        )

    results = []

    for _, group in by_name.items():

        group.sort(
            key=lambda x: (
                "git" in x["types"],
                x["score"],
                x["codefiles"]
            ),
            reverse=True
        )

        primary = group[0]

        primary[
            "duplicate_candidates"
        ] = [
            x["path"]
            for x in group[1:]
        ]

        primary[
            "duplicate_count"
        ] = max(
            0,
            len(group) - 1
        )

        results.append(
            primary
        )

    return sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )

def github_repos():

    data = gh_json([
        "repo",
        "list",
        OWNER,
        "--limit",
        "200",
        "--json",
        "name,description,isArchived,pushedAt,url"
    ])

    return data or []


def tags_from_project(project):

    tags = set(project["types"])

    name = Path(
        project["path"]
    ).name.lower()

    mapping = {
        "repair": "repair",
        "bot": "automation",
        "monitor": "monitoring",
        "control": "control-plane",
        "site": "website",
        "web": "website",
        "security": "security",
        "scan": "security",
        "api": "api",
        "shop": "commerce",
        "ai": "ai",
        "game": "gaming",
        "host": "hosting"
    }

    for key, tag in mapping.items():

        if key in name:
            tags.add(tag)

    return tags


def generate_ideas(projects, repos):

    tag_sources = {}

    for project in projects:

        for tag in tags_from_project(project):

            tag_sources.setdefault(
                tag,
                []
            ).append(
                Path(project["path"]).name
            )

    repo_names = " ".join(
        r["name"].lower()
        for r in repos
    )

    templates = [
        (
            {"monitoring", "repair"},
            "Autonomous Recovery Monitor",
            "Websites and services fail repeatedly and require manual diagnosis.",
            "Combine monitoring with remembered repair playbooks to detect, diagnose and prepare recovery automatically.",
            91
        ),
        (
            {"hosting", "repair"},
            "Hosting Self-Healing Assistant",
            "Hosting and deployment failures cost time and are often repetitive.",
            "Detect known hosting failure patterns and produce tested repair PRs plus health verification.",
            90
        ),
        (
            {"control-plane", "monitoring"},
            "Mikis13 Operations Intelligence",
            "Repository and deployment state is fragmented across projects.",
            "Create one evidence-driven operational overview with repository health and highest-impact next actions.",
            88
        ),
        (
            {"security", "monitoring"},
            "Continuous Defensive Audit",
            "Security drift can remain unnoticed between manual reviews.",
            "Combine safe configuration scanning, repository checks and history to highlight meaningful defensive changes.",
            86
        ),
        (
            {"website", "automation"},
            "Website Release Publisher",
            "Project releases and website information can become inconsistent.",
            "Generate truthful LAB/BETA/STABLE website updates from verified repository state.",
            85
        ),
        (
            {"ai", "automation"},
            "Development Blueprint Incubator",
            "Old ideas and experiments are easy to forget and repeatedly rebuild.",
            "Transform historical project signals into ranked reusable blueprints and minimal experiments.",
            92
        )
    ]

    ideas = []

    available = set(
        tag_sources.keys()
    )

    for required, title, problem, solution, base in templates:

        overlap = len(
            required.intersection(
                available
            )
        )

        if not overlap:
            continue

        score = base

        if required.issubset(
            available
        ):
            score += 4

        slug = slugify(title)

        # Reduce score slightly if a very similar repo exists.
        words = [
            w for w in slug.split("-")
            if len(w) > 4
        ]

        if any(
            word in repo_names
            for word in words
        ):
            score -= 5

        source_tags = sorted(
            required.intersection(
                available
            )
        )

        ideas.append({
            "title": title,
            "slug": slug,
            "problem": problem,
            "solution": solution,
            "score": min(
                100,
                score
            ),
            "source_tags": source_tags
        })

    # Generic revival candidate.
    if projects:

        best_project = max(
            projects,
            key=lambda x: x["score"]
        )

        ideas.append({
            "title":
                "Forgotten Project Revival Lab",

            "slug":
                "forgotten-project-revival-lab",

            "problem":
                "Useful unfinished work can disappear in phone storage and later be rebuilt from scratch.",

            "solution":
                "Rank old project structures, extract reusable concepts and turn only promising candidates into new experiments.",

            "score":
                min(
                    89,
                    60 + best_project["score"] // 3
                ),

            "source_tags":
                best_project["types"]
        })

    return sorted(
        ideas,
        key=lambda x: x["score"],
        reverse=True
    )


def save_blueprint(idea):

    signature = hashlib.sha256(
        json.dumps(
            idea,
            sort_keys=True
        ).encode()
    ).hexdigest()[:16]

    blueprint = {
        "signature": signature,
        "created": now(),
        "status": "LAB",
        "title": idea["title"],
        "score": idea["score"],
        "problem": idea["problem"],
        "target_user":
            "Developer or small technical operation with recurring development and maintenance work.",
        "evidence_source":
            idea["source_tags"],
        "solution": idea["solution"],
        "reuse_check":
            "Reuse existing Mikis13 repositories and modules before creating duplicated implementation.",
        "mvp": [
            "one narrow working function",
            "automated test",
            "clear README",
            "failure handling",
            "measurable success condition"
        ],
        "success_metric":
            "A real recurring task is completed or diagnosed with less manual work.",
        "stop_condition":
            "Pause if there is no measurable usefulness, excessive maintenance, or duplication with an existing project.",
        "security":
            "No credentials or raw phone-storage source may be automatically published.",
        "business_hypothesis":
            "Could become a tool or technical service only after demand is validated.",
        "next_action":
            "Create the smallest reversible prototype."
    }

    folder = (
        STATE
        / "blueprints"
        / idea["slug"]
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        folder
        / "BLUEPRINT.json"
    )

    path.write_text(
        json.dumps(
            blueprint,
            indent=2,
            ensure_ascii=False
        )
        + "\n"
    )

    return signature, path, blueprint


def update_db(con, projects, ideas):

    for p in projects:

        con.execute("""
        INSERT INTO discoveries(
          path,
          kind,
          score,
          todos,
          last_seen
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
          kind=excluded.kind,
          score=excluded.score,
          todos=excluded.todos,
          last_seen=excluded.last_seen
        """, (
            p["path"],
            ",".join(
                p["types"]
            ),
            p["score"],
            p["todos"],
            now()
        ))

    for idea in ideas:

        signature = hashlib.sha256(
            json.dumps(
                idea,
                sort_keys=True
            ).encode()
        ).hexdigest()[:16]

        con.execute("""
        INSERT INTO ideas(
          signature,
          title,
          source,
          score,
          problem,
          solution,
          status,
          first_seen,
          last_seen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(signature) DO UPDATE SET
          score=excluded.score,
          last_seen=excluded.last_seen
        """, (
            signature,
            idea["title"],
            ",".join(
                idea["source_tags"]
            ),
            idea["score"],
            idea["problem"],
            idea["solution"],
            "BLUEPRINT",
            now(),
            now()
        ))

    con.commit()


def report(projects, repos, ideas, blueprint_path):

    report = REPORTS / "latest.md"

    best = ideas[0] if ideas else None

    lines = [
        "# Mikis13 Evolution V3 Report",
        "",
        f"Generated: {now()}",
        "",
        "## Scan",
        "",
        f"- Local project structures found: **{len(projects)}**",
        f"- GitHub repositories visible: **{len(repos)}**",
        f"- Innovation candidates: **{len(ideas)}**",
        "",
        "## Best phone-memory candidates",
        ""
    ]

    for p in sorted(
        projects,
        key=lambda x: x["score"],
        reverse=True
    )[:10]:

        # Only basename in report intended for GitHub.
        # Full local path remains in local SQLite database.
        duplicate_count = p.get(
            "duplicate_count",
            0
        )

        duplicate_note = (
            f" — {duplicate_count} related duplicate(s)"
            if duplicate_count
            else ""
        )

        lines.append(
            f"- **{p['score']}/100** "
            f"{Path(p['path']).name} — "
            f"{','.join(p['types'])} — "
            f"{p['todos']} unfinished marker(s)"
            f"{duplicate_note}"
        )

    lines.extend([
        "",
        "## Top innovation candidate",
        ""
    ])

    if best:

        lines.extend([
            f"### {best['title']}",
            "",
            f"Score: **{best['score']}/100**",
            "",
            f"Problem: {best['problem']}",
            "",
            f"Proposed solution: {best['solution']}",
            "",
            f"Evidence tags: {', '.join(best['source_tags'])}",
            ""
        ])

    lines.extend([
        "## Blueprint",
        "",
        f"`{blueprint_path.relative_to(ROOT) if blueprint_path else 'none'}`",
        "",
        "## Privacy",
        "",
        "Raw phone-storage source files were not uploaded.",
        "",
        "## Governance",
        "",
        "New repositories are prototypes, not finished products. Website promotion uses LAB status until verified."
    ])

    report.write_text(
        "\n".join(lines) + "\n"
    )

    return report


def main():

    REPORTS.mkdir(
        parents=True,
        exist_ok=True
    )

    con = db()

    print(
        "🔎 Phone-memory project discovery..."
    )

    projects = find_projects()

    print(
        f"✅ {len(projects)} project structures found"
    )

    print(
        "🔎 GitHub repository inventory..."
    )

    repos = github_repos()

    print(
        f"✅ {len(repos)} GitHub repositories visible"
    )

    ideas = generate_ideas(
        projects,
        repos
    )

    print(
        f"💡 {len(ideas)} innovation candidates"
    )

    update_db(
        con,
        projects,
        ideas
    )

    blueprint_path = None
    blueprint = None

    if ideas:

        _, blueprint_path, blueprint = save_blueprint(
            ideas[0]
        )

    report_path = report(
        projects,
        repos,
        ideas,
        blueprint_path
    )

    result = {
        "generated": now(),
        "projects": len(projects),
        "repos": len(repos),
        "ideas": len(ideas),
        "best_idea":
            ideas[0] if ideas else None,
        "blueprint":
            str(blueprint_path)
            if blueprint_path else None,
        "report":
            str(report_path)
    }

    (
        STATE / "latest-result.json"
    ).write_text(
        json.dumps(
            result,
            indent=2
        ) + "\n"
    )

    history = (
        STATE
        / "history"
        / (
            datetime.now().strftime(
                "%Y%m%d-%H%M%S"
            )
            + ".json"
        )
    )

    history.write_text(
        json.dumps(
            result,
            indent=2
        ) + "\n"
    )

    print()
    print("========== RESULT ==========")
    print(json.dumps(
        result,
        indent=2
    ))


if __name__ == "__main__":
    main()
