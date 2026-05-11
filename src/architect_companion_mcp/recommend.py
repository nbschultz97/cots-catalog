"""Configuration recommender — picks parts for a compute tier + mission.

Operates over the bundled parts library only. The picks are
deterministic given the same catalog; ranking is heuristic, not
optimization — the LLM should iterate using the other tools.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .catalog import list_components

# Ranked tag preferences per mission_type → category
MISSION_TAG_PREFS: Dict[str, Dict[str, List[str]]] = {
    "long_range": {
        "airframes": ["long-range", "long-endurance", "7-inch", "fixed-wing", "flying-wing", "cruise"],
        "batteries": ["li-ion", "long-range", "endurance"],
    },
    "endurance_survey": {
        "airframes": ["fixed-wing", "flying-wing", "long-endurance", "heavy-lift", "cargo", "10-inch"],
        "batteries": ["li-ion", "endurance"],
    },
    "freestyle": {
        "airframes": ["5-inch", "freestyle", "true-x"],
        "batteries": ["6s", "high-discharge"],
    },
    "racing": {
        "airframes": ["5-inch", "race", "true-x"],
        "batteries": ["6s", "high-discharge"],
    },
    "cinematic": {
        "airframes": ["5-inch", "7-inch", "long-range", "cruise"],
        "batteries": ["6s", "li-ion"],
    },
    "cold_weather": {
        "airframes": ["7-inch", "long-range", "cruise"],
        "batteries": ["li-ion"],
    },
}

COMPUTE_TIER_TAGS: Dict[str, List[str]] = {
    "pi-zero": ["pi", "lightweight"],
    "pi4": ["pi", "rpi4"],
    "pi5": ["pi", "rpi5"],
    "jetson-nano": ["jetson", "gpu"],
    "jetson-orin-nano": ["jetson", "orin", "gpu"],
    "x86": ["x86", "laptop"],
}


def _rank(parts: List[Dict[str, Any]], preferred_tags: List[str]) -> List[Dict[str, Any]]:
    def score(part: Dict[str, Any]) -> tuple:
        tags = set(part.get("tags") or [])
        hits = sum(1 for tag in preferred_tags if tag in tags)
        # in-stock first, then more tag hits, then cheaper
        availability_score = 0 if part.get("availability") == "in-stock" else 1
        cost = part.get("cost_usd") or 1e9
        return (availability_score, -hits, cost)

    return sorted(parts, key=score)


def _pick(category: str, preferred_tags: List[str], budget_usd: Optional[float]) -> Optional[Dict[str, Any]]:
    candidates = list_components(category=category, max_cost_usd=budget_usd)
    ranked = _rank(candidates, preferred_tags)
    return ranked[0] if ranked else None


def recommend_configuration(
    compute_tier: str = "pi5",
    mission_type: str = "long_range",
    *,
    budget_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """Return a recommended kit: airframe, motor, ESC, battery, FC, radio.

    ``compute_tier`` informs the radio/sensor picks (heavier compute
    accepts heavier video radios). ``mission_type`` informs airframe
    and battery preferences (see :data:`MISSION_TAG_PREFS`).
    """

    if compute_tier not in COMPUTE_TIER_TAGS:
        raise ValueError(
            f"Unknown compute_tier '{compute_tier}'. Valid: {', '.join(COMPUTE_TIER_TAGS)}"
        )

    prefs = MISSION_TAG_PREFS.get(mission_type, MISSION_TAG_PREFS["long_range"])
    picks: Dict[str, Optional[Dict[str, Any]]] = {
        "airframe": _pick("airframes", prefs.get("airframes", []), budget_usd),
        "motor": _pick("motors", [], budget_usd),
        "esc": _pick("escs", [], budget_usd),
        "battery": _pick("batteries", prefs.get("batteries", []), budget_usd),
        "flight_controller": _pick("flight_controllers", [], budget_usd),
        "control_radio": _pick("radios", ["control", "crsf", "elrs"], budget_usd),
    }

    total_cost = sum(
        (p.get("cost_usd") or 0) for p in picks.values() if p is not None
    )
    total_weight = sum(
        (p.get("weight_g") or 0) for p in picks.values() if p is not None
    )

    return {
        "compute_tier": compute_tier,
        "mission_type": mission_type,
        "budget_usd": budget_usd,
        "picks": {
            slot: ({"id": part["id"], "name": part["name"], "cost_usd": part.get("cost_usd"), "weight_g": part.get("weight_g")} if part else None)
            for slot, part in picks.items()
        },
        "totals": {
            "cost_usd": round(total_cost, 2),
            "weight_g": total_weight,
        },
        "note": (
            "Heuristic ranking — sort by availability, mission-tag match, then cost. "
            "Run check_compatibility on the picks before committing."
        ),
    }
