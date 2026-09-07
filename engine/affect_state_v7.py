#!/usr/bin/env python3


def clamp(value):
    return max(
        0,
        min(100, int(value))
    )


def update_state(profile, event):
    state = profile["state"]

    result = event.get(
        "result",
        "unknown"
    )

    risk = event.get(
        "risk",
        "medium"
    )

    if result == "success":
        state["confidence"] = clamp(
            state["confidence"] + 5
        )
        state["satisfaction"] = clamp(
            state["satisfaction"] + 10
        )
        state["frustration"] = clamp(
            state["frustration"] - 8
        )

    elif result == "failure":
        state["confidence"] = clamp(
            state["confidence"] - 5
        )
        state["uncertainty"] = clamp(
            state["uncertainty"] + 10
        )
        state["frustration"] = clamp(
            state["frustration"] + 10
        )

    elif result == "blocked":
        state["uncertainty"] = clamp(
            state["uncertainty"] + 5
        )

    if risk == "high":
        state["urgency"] = clamp(
            state["urgency"] + 10
        )

    elif risk == "critical":
        state["urgency"] = clamp(
            state["urgency"] + 20
        )

    state["curiosity"] = clamp(
        state["curiosity"]
    )

    return profile
