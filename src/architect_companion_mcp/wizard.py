"""Build wizard + suggest-alternatives helpers.

``build_wizard`` is a one-shot tool that:

1. Filters build templates by (mission, budget, skill).
2. Runs ``check_compatibility`` on each candidate's catalog parts.
3. Ranks by validation (compatible first), then by closeness to budget.
4. Returns the top picks with their validation report attached.

``suggest_alternatives`` is the swap helper: given a build that failed
compatibility, return candidate replacement parts for the problematic
category.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .catalog import list_components, part_by_id
from .compatibility import check_compatibility
from .templates import (
    get_build_template,
    list_build_templates,
    template_part_ids,
)


def build_wizard(
    mission_type: Optional[str] = None,
    airframe_class: Optional[str] = None,
    skill_level: Optional[str] = None,
    budget_usd: Optional[float] = None,
    top_n: int = 3,
) -> Dict[str, Any]:
    """Find the top-N canonical templates matching the filters, run
    compatibility on each, and return them with their validation status."""

    candidates = list_build_templates(
        mission_type=mission_type,
        airframe_class=airframe_class,
        skill_level=skill_level,
        max_budget_usd=budget_usd,
    )

    scored: List[Dict[str, Any]] = []
    for summary in candidates:
        template = get_build_template(summary["id"])
        part_ids = template_part_ids(template)
        # Only the catalog-resolvable parts go to check_compatibility.
        valid_ids = [pid for pid in part_ids if part_by_id(pid) is not None]
        report = check_compatibility(valid_ids) if valid_ids else {
            "compatible": True, "issues": [], "parts": [],
            "total_weight_g": 0, "budget": None,
        }

        total_cost = 0.0
        for pid in valid_ids:
            part = part_by_id(pid)
            if part:
                total_cost += float(part.get("cost_usd") or 0)

        budget_delta = (
            abs(total_cost - budget_usd) if budget_usd is not None else 0.0
        )

        scored.append({
            "template_id": template["id"],
            "name": template["name"],
            "description": template.get("description"),
            "mission_type": template.get("mission_type"),
            "airframe_class": template.get("airframe_class"),
            "skill_level": template.get("skill_level"),
            "budget_estimate_usd": template.get("budget_estimate_usd"),
            "computed_cost_usd": round(total_cost, 2),
            "budget_delta_usd": round(budget_delta, 2),
            "parts": template.get("parts", {}),
            "validation": {
                "compatible": report.get("compatible", True),
                "issues": report.get("issues", []),
            },
            "notes": template.get("notes", ""),
        })

    # Compatible first, then closest to budget, then within budget
    scored.sort(key=lambda s: (
        0 if s["validation"]["compatible"] else 1,
        s["budget_delta_usd"],
    ))

    return {
        "filters": {
            "mission_type": mission_type,
            "airframe_class": airframe_class,
            "skill_level": skill_level,
            "budget_usd": budget_usd,
        },
        "n_candidates": len(scored),
        "top_picks": scored[:top_n],
        "note": (
            "Templates are curated canonical kits. Run check_compatibility on "
            "the chosen template's parts after any swap to keep it engineering-clean."
        ),
    }


# ---- Suggest alternatives for a failing build ----

# Which category an issue typically points at, so we can suggest swaps
# in the right slot. Conservative mapping; multi-cause issues default
# to the airframe.
_ISSUE_TO_CATEGORY = [
    ("battery", "batteries"),
    ("ESC", "escs"),
    ("motor", "motors"),
    ("airframe", "airframes"),
    ("radio", "radios"),
    ("antenna", "accessories"),
    ("ecosystem", "sensors"),
    ("VTX", "sensors"),
    ("goggle", "sensors"),
    ("flight controller", "flight_controllers"),
]


def _issue_target_category(issue: str) -> Optional[str]:
    lowered = issue.lower()
    for keyword, category in _ISSUE_TO_CATEGORY:
        if keyword.lower() in lowered:
            return category
    return None


def suggest_alternatives(
    failing_part_ids: List[str],
    issue: str,
    top_n: int = 3,
) -> Dict[str, Any]:
    """For a build that failed compatibility, return up to N candidate
    swap parts in the category the issue most likely points at, ranked
    by cost (cheapest first)."""

    target_category = _issue_target_category(issue) or "airframes"
    # Find the existing part in the build for that category so we can
    # report its name and exclude it from suggestions.
    existing_in_category: List[Dict[str, Any]] = []
    for pid in failing_part_ids:
        part = part_by_id(pid)
        if part and part["_category"] == target_category:
            existing_in_category.append(part)

    # Pull all parts in that category and rank by cost.
    candidates = list_components(category=target_category)
    existing_ids = {p["id"] for p in existing_in_category}
    candidates = [c for c in candidates if c["id"] not in existing_ids]
    candidates.sort(key=lambda c: (
        0 if c.get("availability") == "in-stock" else 1,
        c.get("cost_usd") or 1e9,
    ))

    return {
        "issue": issue,
        "target_category": target_category,
        "swap_out": [
            {"id": p["id"], "name": p["name"], "cost_usd": p.get("cost_usd"), "weight_g": p.get("weight_g")}
            for p in existing_in_category
        ],
        "swap_in_candidates": [
            {
                "id": c["id"],
                "name": c["name"],
                "cost_usd": c.get("cost_usd"),
                "weight_g": c.get("weight_g"),
                "tags": c.get("tags", []),
            }
            for c in candidates[:top_n]
        ],
        "note": (
            "Run check_compatibility again with the new part swapped in to "
            "confirm the issue resolves and no new ones surface."
        ),
    }
