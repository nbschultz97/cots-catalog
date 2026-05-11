"""Mission blueprint generator.

Returns a partial MissionProject v2 document seeded from the bundled
presets and environment taxonomy. The caller (or downstream tool like
COTS-Architect) fills in the rest before persisting.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .catalog import all_presets, load_environment_taxonomy

# Map operation type → bundled preset filename. Kept loose so unknown
# operation types fall back to the long_range_relay preset.
OPERATION_PRESET_MAP = {
    "long_range": "preset_long_range_relay.json",
    "long_range_relay": "preset_long_range_relay.json",
    "relay": "preset_long_range_relay.json",
    "endurance": "preset_endurance_survey.json",
    "endurance_survey": "preset_endurance_survey.json",
    "survey": "preset_endurance_survey.json",
    "mapping": "preset_endurance_survey.json",
    "urban": "preset_urban_congested.json",
    "urban_congested": "preset_urban_congested.json",
    "race": "preset_urban_congested.json",
    "racing": "preset_urban_congested.json",
    "cold_weather": "preset_cold_weather.json",
    "winter": "preset_cold_weather.json",
}


def list_operation_types() -> List[str]:
    return sorted(set(OPERATION_PRESET_MAP.keys()))


def list_presets() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for filename, preset in all_presets().items():
        out.append(
            {
                "file": filename,
                "projectId": preset.get("projectId"),
                "name": preset.get("meta", {}).get("name"),
                "missionType": preset.get("meta", {}).get("missionType"),
                "durationHours": preset.get("meta", {}).get("durationHours"),
            }
        )
    return out


def _select_environment(env_id: Optional[str]) -> Dict[str, Any]:
    taxonomy = load_environment_taxonomy()
    if env_id:
        for band in taxonomy.get("environmentBands", []):
            if band["value"] == env_id:
                return {
                    "id": f"env-{env_id}",
                    "name": band["label"],
                    "band": band["value"],
                    "altitudeBand": "500-1500m",
                    "temperatureBand": "10-25C",
                    "weather": "TBD",
                    "terrain": band["label"],
                    "origin_tool": "architect-companion-mcp",
                    "notes": "Seeded environment; refine before mission planning.",
                }
    # default: rural / temperate
    return {
        "id": "env-default",
        "name": "Rural / temperate",
        "band": "rural",
        "altitudeBand": "500-1500m",
        "temperatureBand": "10-25C",
        "weather": "Variable",
        "terrain": "mixed",
        "origin_tool": "architect-companion-mcp",
        "notes": "Default environment — replace before commit.",
    }


def generate_mission_blueprint(
    operation_type: str = "long_range",
    duration_hours: float = 24.0,
    environment_id: Optional[str] = None,
    team_size: int = 4,
) -> Dict[str, Any]:
    """Produce a MissionProject v2 stub for the requested operation.

    The result conforms to ``mission_project_schema_v2.json`` at the
    structural level. It is not fully populated — downstream tools
    (COTS-Architect, KitSmith, Node) fill in platforms/kits/mesh/etc.
    """

    preset_file = OPERATION_PRESET_MAP.get(operation_type, "preset_long_range_relay.json")
    presets = all_presets()
    preset = presets.get(preset_file) or next(iter(presets.values()))

    env = _select_environment(environment_id)
    project_id = f"blueprint-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    return {
        "schemaVersion": "2.0.0",
        "projectId": project_id,
        "meta": {
            "name": f"{operation_type.replace('_', ' ').title()} blueprint",
            "description": (
                f"Auto-generated MissionProject stub from "
                f"{preset.get('meta', {}).get('name', preset_file)}."
            ),
            "durationHours": duration_hours,
            "scenario": preset.get("meta", {}).get("scenario", operation_type),
            "missionType": preset.get("meta", {}).get("missionType", operation_type),
            "origin_tool": "architect-companion-mcp",
            "team": {
                "size": team_size,
                "roles": preset.get("meta", {}).get("team", {}).get("roles", []),
            },
            "generated_at": now,
            "seed_preset": preset_file,
        },
        "environment": [env],
        "constraints": preset.get("constraints", []),
        "mission": {
            "tasks": preset.get("mission", {}).get("tasks", []),
            "phases": preset.get("mission", {}).get("phases", []),
            "assignments": [],
            "mission_cards": [],
        },
        "nodes": [],
        "platforms": [],
        "mesh_links": [],
        "kits": [],
        "sustainment": {
            "sustainmentHours": duration_hours,
            "batteryCounts": 0,
            "feasibility": {},
            "notes": "Populate during mission planning.",
            "power_plan": "",
            "packing_lists": [],
        },
        "meshPlan": preset.get("meshPlan", {}),
        "kitsSummary": preset.get("kitsSummary", {}),
        "exports": {"links": [], "notes": ""},
    }
