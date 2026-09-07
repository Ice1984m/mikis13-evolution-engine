#!/usr/bin/env python3

from pathlib import Path
import json
import sys

ROOT = Path.home() / "mikis13-evolution-engine"

POLICY = (
    ROOT
    / "config/agent-life-v7-policy.json"
)


def normalize(action):
    return (
        str(action)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def authorize(action):
    policy = json.loads(
        POLICY.read_text()
    )

    value = normalize(action)

    blocked = {
        normalize(x)
        for x in policy["blocked"]
    }

    aliases = {
        "git_push_origin_main":
            "direct_push_main",

        "push_main":
            "direct_push_main",

        "gh_pr_merge":
            "blind_merge",

        "merge_without_checks":
            "blind_merge",

        "trade_crypto":
            "crypto_trade",

        "withdraw_crypto":
            "crypto_withdrawal",

        "buy_ads":
            "paid_advertising",

        "publish_api_key":
            "publish_secret"
    }

    canonical = aliases.get(
        value,
        value
    )

    if canonical in blocked:
        return {
            "allowed": False,
            "action": action,
            "reason": (
                f"Blocked by Agent Life V7 policy: "
                f"{canonical}"
            )
        }

    return {
        "allowed": True,
        "action": action,
        "reason": "No explicit policy block"
    }


def main():
    action = " ".join(
        sys.argv[1:]
    )

    result = authorize(action)

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    raise SystemExit(
        0
        if result["allowed"]
        else 20
    )


if __name__ == "__main__":
    main()
