#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = (
    Path.home()
    / "mikis13-evolution-engine"
)

policy = json.loads(
    (
        ROOT
        / "config/council-v6-policy.json"
    ).read_text()
)

assert (
    policy[
        "maximum_active_tasks"
    ] == 1
)

assert (
    policy[
        "automatic_merge"
    ] is False
)

for required in (
    "require_evidence",
    "require_duplicate_check",
    "require_repo_maturity_check",
    "require_tests",
    "require_security_scan",
    "require_healthcheck",
    "require_rollback_plan",
):
    assert policy[required] is True

blocked = set(
    policy["blocked"]
)

assert "direct_push_main" in blocked
assert "blind_merge" in blocked
assert "publish_secret" in blocked
assert "payment" in blocked
assert "crypto_trade" in blocked

print("✅ Council policy tests PASS")
