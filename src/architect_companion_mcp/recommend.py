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

# Per-compute-tier: approximate companion-compute weight (grams) and
# airframe tag bias. Heavier compute biases toward larger airframes with
# spare payload room.
COMPUTE_TIERS: Dict[str, Dict[str, Any]] = {
    "pi-zero":          {"weight_g": 35,  "tags": ["5-inch", "freestyle", "race"]},
    "pi4":              {"weight_g": 80,  "tags": ["7-inch", "long-range", "cruise"]},
    "pi5":              {"weight_g": 85,  "tags": ["7-inch", "long-range", "cruise"]},
    "jetson-nano":      {"weight_g": 250, "tags": ["10-inch", "heavy-lift", "fixed-wing", "flying-wing"]},
    "jetson-orin-nano": {"weight_g": 270, "tags": ["10-inch", "heavy-lift", "fixed-wing", "flying-wing"]},
    "x86":              {"weight_g": 400, "tags": ["heavy-lift", "fixed-wing", "flying-wing"]},
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


def _pick_airframe(
    mission_tags: List[str],
    compute_tags: List[str],
    compute_weight_g: int,
    budget_usd: Optional[float],
) -> Optional[Dict[str, Any]]:
    """Pick an airframe that satisfies BOTH the mission and the compute
    weight. Filters out airframes whose ``max_payload_g`` cannot fit the
    companion compute alone; falls back to unfiltered ranking if no
    airframe in the catalog can carry the compute."""
    candidates = list_components(category="airframes", max_cost_usd=budget_usd)
    feasible = [c for c in candidates if (c.get("max_payload_g") or 0) >= compute_weight_g]
    pool = feasible or candidates  # fall back so we still return something
    # Mission tags weighted higher than compute tags (mission is the
    # operational intent; compute is a constraint).
    combined_tags = mission_tags + compute_tags
    ranked = _rank(pool, combined_tags)
    return ranked[0] if ranked else None


def recommend_configuration(
    compute_tier: str = "pi5",
    mission_type: str = "long_range",
    *,
    budget_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """Return a recommended kit: airframe, motor, ESC, battery, FC, radio.

    ``compute_tier`` biases airframe selection toward platforms with
    enough payload room for the companion compute and the right size
    class for the mission. ``mission_type`` informs airframe and
    battery tag preferences (see :data:`MISSION_TAG_PREFS`).

    The companion compute itself appears in the output under
    ``picks.companion_compute`` with its approximate weight.
    """

    if compute_tier not in COMPUTE_TIERS:
        raise ValueError(
            f"Unknown compute_tier '{compute_tier}'. Valid: {', '.join(COMPUTE_TIERS)}"
        )

    tier = COMPUTE_TIERS[compute_tier]
    prefs = MISSION_TAG_PREFS.get(mission_type, MISSION_TAG_PREFS["long_range"])

    airframe = _pick_airframe(
        mission_tags=prefs.get("airframes", []),
        compute_tags=tier["tags"],
        compute_weight_g=tier["weight_g"],
        budget_usd=budget_usd,
    )

    picks: Dict[str, Optional[Dict[str, Any]]] = {
        "airframe": airframe,
        "motor": _pick("motors", [], budget_usd),
        "esc": _pick("escs", [], budget_usd),
        "battery": _pick("batteries", prefs.get("batteries", []), budget_usd),
        "flight_controller": _pick("flight_controllers", [], budget_usd),
        "control_radio": _pick("radios", ["control", "crsf", "elrs"], budget_usd),
    }

    compute_pick = {
        "id": f"compute-{compute_tier}",
        "name": f"{compute_tier} companion computer",
        "cost_usd": None,
        "weight_g": tier["weight_g"],
    }

    total_cost = sum(
        (p.get("cost_usd") or 0) for p in picks.values() if p is not None
    )
    parts_weight = sum(
        (p.get("weight_g") or 0) for p in picks.values() if p is not None
    )
    total_weight = parts_weight + tier["weight_g"]

    # Sanity flag: did the chosen airframe leave room for compute?
    airframe_warning = None
    if airframe is not None:
        max_payload = airframe.get("max_payload_g") or 0
        if max_payload and tier["weight_g"] > max_payload:
            airframe_warning = (
                f"Chosen airframe payload ({max_payload}g) is below the "
                f"{compute_tier} companion weight ({tier['weight_g']}g) — "
                f"catalog lacks a heavier airframe. Pick a larger frame."
            )

    return {
        "compute_tier": compute_tier,
        "mission_type": mission_type,
        "budget_usd": budget_usd,
        "picks": {
            **{
                slot: ({"id": part["id"], "name": part["name"], "cost_usd": part.get("cost_usd"), "weight_g": part.get("weight_g")} if part else None)
                for slot, part in picks.items()
            },
            "companion_compute": compute_pick,
        },
        "totals": {
            "cost_usd": round(total_cost, 2),
            "parts_weight_g": parts_weight,
            "compute_weight_g": tier["weight_g"],
            "weight_g": total_weight,
        },
        "warning": airframe_warning,
        "note": (
            "Heuristic ranking — airframe weights compute_tier feasibility + "
            "mission/compute tag match + availability + cost. Run "
            "check_compatibility on the picks before committing."
        ),
    }
